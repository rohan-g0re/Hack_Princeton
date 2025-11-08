import asyncio
from urllib.parse import quote_plus
from playwright.async_api import async_playwright, TimeoutError as PwTimeout

INGREDIENT = "milk"  # change as needed

DUCK_URL = "https://duckduckgo.com/?q={}"
INSTA_SEARCH_URL = "https://www.instacart.com/store/search?q={}"

QUERY_INSTACART_SUFFIX = True  # always search "<ingredient> instacart"

async def first_href_containing(page, substring: str) -> str | None:
    hrefs = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    for h in hrefs:
        if substring in h:
            return h
    return None

async def add_first_item_to_cart(page) -> bool:
    """Try several patterns that Instacart uses for the Add button."""
    selector_candidates = [
        # text-based
        "button:has-text('Add')",
        "button:has-text('ADD')",
        # aria / test ids
        "button[aria-label*='Add']",
        "[data-testid*='Add']",
        "[data-testid*='add']",
        "[data-test*='add']",
        # sometimes plus icon wrapped in a button/div with role
        "[role='button'][aria-label*='Add']",
    ]
    # ensure product cards are visible before hunting buttons
    card_hints = [
        "[data-testid*='item-card']",
        "[data-test*='item-card']",
        "[class*='ItemCard']",
        "[class*='Product']",
        "button:has-text('Add')",
    ]
    for hint in card_hints:
        try:
            await page.locator(hint).first.wait_for(state="visible", timeout=5000)
            break
        except PwTimeout:
            continue

    # small progressive scroll to bring early items into view
    for _ in range(4):
        try:
            await page.mouse.wheel(0, 350)
            await page.wait_for_timeout(400)
        except Exception:
            pass

    for sel in selector_candidates:
        try:
            btn = page.locator(sel).first
            await btn.wait_for(state="visible", timeout=2500)
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
            user_data_dir="./user_data",  # keeps you logged in
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = await ctx.new_page()

        # ---------- 1) Search engine step: "<ingredient> instacart" ----------
        query = INGREDIENT + (" instacart" if QUERY_INSTACART_SUFFIX else "")
        duck_url = DUCK_URL.format(quote_plus(query))
        try:
            await page.goto(duck_url, wait_until="domcontentloaded")
            href = await first_href_containing(page, "instacart.com")
            if not href:
                # fallback to direct instacart search
                href = INSTA_SEARCH_URL.format(quote_plus(INGREDIENT))
            await page.goto(href, wait_until="domcontentloaded")
        except Exception:
            # hard fallback
            await page.goto(INSTA_SEARCH_URL.format(quote_plus(INGREDIENT)), wait_until="domcontentloaded")

        # ---------- 2) If not already on a search results page, search on Instacart ----------
        try:
            search_selectors = [
                "input[placeholder*='Search']",
                "input[type='search']",
                "form[role='search'] input",
                "input[name='search']",
                "input[name='searchTerm']",
            ]
            filled = False
            for sel in search_selectors:
                loc = page.locator(sel).first
                try:
                    await loc.wait_for(state="visible", timeout=2500)
                    await loc.click()
                    await loc.fill(INGREDIENT)
                    await page.keyboard.press("Enter")
                    filled = True
                    break
                except PwTimeout:
                    continue
                except Exception:
                    continue
            # give results time to render
            if filled:
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(2500)
        except Exception:
            pass

        # ---------- 3) Try to add the first item ----------
        added = await add_first_item_to_cart(page)
        if added:
            print(f"✅ Added '{INGREDIENT}' to cart.")
        else:
            print("❌ Could not find an 'Add' button. Ensure you're logged in, address/store is set, and items are available.")

        await page.wait_for_timeout(2000)
        await ctx.close()

if __name__ == "__main__":
    asyncio.run(run())
