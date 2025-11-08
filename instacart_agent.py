import asyncio
import random
from urllib.parse import quote_plus
from playwright.async_api import async_playwright, TimeoutError as PwTimeout

# >>> Edit your shopping list here
INGREDIENTS = ["milk", "eggs", "bread"]  # add more

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

async def ensure_on_instacart_results(page, ingredient: str):
    """
    Try DuckDuckGo ('<ingredient> instacart'), then fallback to direct Instacart search.
    Leaves you on an Instacart search results page for the ingredient.
    """
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
        # hard fallback
        await page.goto(INSTA_SEARCH_URL.format(quote_plus(ingredient)), wait_until="domcontentloaded")

    # If we didn’t land on a results page, try to type into the site search box
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
            await loc.wait_for(state="visible", timeout=2000)
            await loc.click()
            await loc.fill(ingredient)
            await page.keyboard.press("Enter")
            break
        except Exception:
            continue

    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_timeout(1500)

async def add_first_item_to_cart(page) -> bool:
    """
    Try several likely 'Add' selectors, with small scrolls.
    """
    # ensure product grid is present-ish
    grid_hints = [
        "[data-testid*='item-card']",
        "[data-test*='item-card']",
        "[class*='ItemCard']",
        "[class*='Product']",
        "button:has-text('Add')",
    ]
    for hint in grid_hints:
        try:
            await page.locator(hint).first.wait_for(state="visible", timeout=4000)
            break
        except PwTimeout:
            continue

    # progressive scroll to bring top items into view
    for _ in range(5):
        try:
            await page.mouse.wheel(0, 350)
            await page.wait_for_timeout(250)
        except Exception:
            pass

    candidates = [
        "button:has-text('Add')",
        "button:has-text('ADD')",
        "button[aria-label*='Add']",
        "[data-testid*='Add']",
        "[data-testid*='add']",
        "[data-test*='add']",
        "[role='button'][aria-label*='Add']",
    ]
    for sel in candidates:
        btn = page.locator(sel).first
        try:
            await btn.wait_for(state="visible", timeout=2000)
            await btn.click()
            return True
        except PwTimeout:
            continue
        except Exception:
            continue
    return False

async def run():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir="./user_data",   # persists your Instacart login + store
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = await ctx.new_page()

        success = []
        failed = []

        for item in INGREDIENTS:
            print(f"\n—> Processing: {item}")
            await ensure_on_instacart_results(page, item)
            added = await add_first_item_to_cart(page)
            if added:
                print(f"✅ Added '{item}' to cart.")
                success.append(item)
            else:
                print(f"❌ Could not add '{item}'. Check login/store or UI changed.")
                failed.append(item)
            await page.wait_for_timeout(human_delay(600, 1200))

        print("\nSummary:")
        print("  Added :", success or "—")
        print("  Failed:", failed or "—")

        await page.wait_for_timeout(1500)
        await ctx.close()

if __name__ == "__main__":
    asyncio.run(run())
