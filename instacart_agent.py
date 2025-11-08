import asyncio
import random
from urllib.parse import quote_plus
from playwright.async_api import async_playwright, TimeoutError as PwTimeout

# ---------- Edit your shopping list here ----------
INGREDIENTS = ["milk", "eggs", "{}metalxx", "paneer"]

DUCK_URL = "https://duckduckgo.com/?q={}"
INSTA_SEARCH_URL = "https://www.instacart.com/store/search?q={}"

def human_delay(min_ms=300, max_ms=800):
    return random.randint(min_ms, max_ms)

async def first_href_containing(page, substring: str) -> str | None:
    hrefs = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    for h in hrefs:
        if substring in h:
            return h
    return None

async def dismiss_popups(page, attempts: int = 6) -> None:
    close_selectors = [
        "[aria-label='Close']",
        "[aria-label*='close']",
        "button:has-text('Close')",
        "button:has-text('Got it')",
        "button:has-text('Dismiss')",
        "button:has-text('Not now')",
        "[data-testid*='close']",
        "[data-test*='close']",
        "[class*='close']",
        "[role='button'][aria-label*='Close']",
        "button[aria-label*='Dismiss']",
        "button :text('×')",
    ]
    for _ in range(attempts):
        try:
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(150)
            for sel in close_selectors:
                loc = page.locator(sel).filter(has_not=page.locator("[aria-hidden='true']")).first
                if await loc.is_visible():
                    try:
                        await loc.click(timeout=700)
                        await page.wait_for_timeout(200)
                    except Exception:
                        pass
            dialogs = page.get_by_role("dialog")
            count = await dialogs.count()
            for i in range(count):
                dlg = dialogs.nth(i)
                if await dlg.is_visible():
                    inner_close = dlg.locator(", ".join(close_selectors)).first
                    if await inner_close.is_visible():
                        try:
                            await inner_close.click(timeout=700)
                            await page.wait_for_timeout(200)
                        except Exception:
                            pass
        except Exception:
            pass

async def ensure_on_instacart_results(page, ingredient: str):
    """Land on an Instacart results page for the ingredient, using DDG or direct URL, then clear popups."""
    query = f"{ingredient} instacart"
    duck_url = DUCK_URL.format(quote_plus(query))
    try:
        await page.goto(duck_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(human_delay())
        href = await first_href_containing(page, "instacart.com")
        if not href:
            href = INSTA_SEARCH_URL.format(quote_plus(ingredient))
        await page.goto(href, wait_until="domcontentloaded")
    except Exception:
        await page.goto(INSTA_SEARCH_URL.format(quote_plus(ingredient)), wait_until="domcontentloaded")

    await dismiss_popups(page)

    # If not already on a results page, try the site search box
    search_selectors = [
        "input[placeholder*='Search']",
        "input[type='search']",
        "form[role='search'] input",
        "input[name='search']",
        "input[name='searchTerm']",
    ]
    for sel in search_selectors:
        loc = page.locator(sel).first
        try:
            await loc.wait_for(state="visible", timeout=1800)
            await loc.click()
            await loc.fill(ingredient)
            await page.keyboard.press("Enter")
            break
        except Exception:
            continue

    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_timeout(900)
    await dismiss_popups(page)

async def count_product_cards(page) -> int:
    """Return a count of visible product tiles/cards (multi-selector union)."""
    selectors = [
        "[data-testid*='item-card']",
        "[data-test*='item-card']",
        "[class*='ItemCard']",
        "[class*='product']",
        "[class*='Product']",
        "button:has-text('Add')",  # sometimes only Add buttons are reliable
    ]
    total = 0
    for sel in selectors:
        try:
            total = max(total, await page.locator(sel).count())
        except Exception:
            pass
    return total

async def page_indicates_no_results(page) -> bool:
    """Heuristics for explicit 'no results' banners/messages."""
    texts = [
        "No results", "no results", "0 results",
        "We couldn’t find any results", "We couldn't find any results",
        "Try a different search", "No items found", "did not match any products",
    ]
    for t in texts:
        if await page.get_by_text(t, exact=False).first.is_visible():
            return True
    # common data-testid containers for empty states (best-effort)
    empty_selectors = [
        "[data-testid*='no-results']",
        "[data-test*='no-results']",
        "[data-testid*='empty']",
        "[class*='EmptyState']",
    ]
    for sel in empty_selectors:
        if await page.locator(sel).first.is_visible():
            return True
    return False

async def thorough_results_check(page) -> bool:
    """
    Decide if this query has results WITHOUT relying on timeouts:
    - look for explicit 'no results'
    - progressive scroll + recount product cards
    """
    # 1) explicit 'no results' signals
    if await page_indicates_no_results(page):
        return False

    # 2) count product cards, then scroll a bit and recount
    cards_before = await count_product_cards(page)
    # Progressive scroll to trigger lazy loading (fixed number of steps)
    for _ in range(6):
        try:
            await page.mouse.wheel(0, 500)
            await page.wait_for_timeout(200)
        except Exception:
            pass
    cards_after = await count_product_cards(page)

    return max(cards_before, cards_after) > 0

async def add_first_item_to_cart(page) -> bool:
    """Find an 'Add' button and click it. If blocked, dismiss popups and retry."""
    candidates = [
        "button:has-text('Add')",
        "button:has-text('ADD')",
        "button[aria-label*='Add']",
        "[data-testid*='Add']",
        "[data-testid*='add']",
        "[data-test*='add']",
        "[role='button'][aria-label*='Add']",
    ]

    # small pre-scroll to bring items into view
    for _ in range(4):
        try:
            await page.mouse.wheel(0, 350)
            await page.wait_for_timeout(180)
        except Exception:
            pass

    # try twice with popup dismissal between attempts
    for _ in range(2):
        for sel in candidates:
            btn = page.locator(sel).first
            try:
                if await btn.is_visible():
                    await btn.click()
                    return True
            except Exception:
                continue
        await dismiss_popups(page)
        await page.wait_for_timeout(250)
    return False

async def run():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir="./user_data",   # keeps your Instacart login + store
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = await ctx.new_page()

        success, failed, not_found = [], [], []

        for ingredient in INGREDIENTS:
            print(f"\n—> Processing: {ingredient}")
            await ensure_on_instacart_results(page, ingredient)

            # ===== thorough no-results check (DOM-based, not timeout-based) =====
            has_results = await thorough_results_check(page)
            if not has_results:
                print(f"⏭️  No results for '{ingredient}' — moving on.")
                not_found.append(ingredient)
                await page.wait_for_timeout(human_delay(600, 1100))
                continue

            # ===== try to add first available item =====
            added = await add_first_item_to_cart(page)
            if added:
                print(f"✅ Added '{ingredient}' to cart.")
                success.append(ingredient)
            else:
                print(f"❌ Could not add '{ingredient}'. (Store/address or UI may block.)")
                failed.append(ingredient)

            await page.wait_for_timeout(human_delay(650, 1200))

        print("\nSummary:")
        print("  Added     :", success or "—")
        print("  Not found :", not_found or "—")
        print("  Failed    :", failed or "—")

        await page.wait_for_timeout(900)
        await ctx.close()

if __name__ == "__main__":
    asyncio.run(run())
