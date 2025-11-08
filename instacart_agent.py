import asyncio
from playwright.async_api import async_playwright, TimeoutError as PwTimeout

INGREDIENT = "milk"   # change me

DUCK_URL = "https://duckduckgo.com/?q=site%3Ainstacart.com+{}&ia=web"
INSTA_SEARCH_URL = "https://www.instacart.com/store/search?q={}"

async def first_href_containing(page, substring: str) -> str | None:
    """Return the first anchor href on the page that contains substring."""
    hrefs = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    for h in hrefs:
        if substring in h:
            return h
    return None

async def add_first_item_to_cart(page):
    """
    Tries several reasonable selectors for an 'Add' button
    and clicks the first one found.
    """
    # common “Add” button patterns
    selector_candidates = [
        "button:has-text('Add')",
        "button:has-text('ADD')",
        "[data-test*='add']:not([disabled])",
        "[data-testid*='add']:not([disabled])",
        "button[aria-label*='Add']",
    ]
    for sel in selector_candidates:
        btn = page.locator(sel).first
        try:
            await btn.wait_for(state="visible", timeout=4000)
            await btn.click()
            return True
        except PwTimeout:
            continue
        except Exception:
            continue
    return False

async def run():
    async with async_playwright() as p:
        # Use persistent context so your Instacart login is remembered
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir="./user_data",   # keep cookies/sessions here
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],  # a tiny bit less “automated”
        )
        page = await ctx.new_page()

        # ---------- Step 1: Try DuckDuckGo (avoid Google bot-check) ----------
        try:
            await page.goto(DUCK_URL.format(INGREDIENT), wait_until="domcontentloaded")
            # pick first instacart link from results
            href = await first_href_containing(page, "instacart.com")
            if href:
                await page.goto(href, wait_until="domcontentloaded")
            else:
                # fallback to direct instacart search
                await page.goto(INSTA_SEARCH_URL.format(INGREDIENT), wait_until="domcontentloaded")
        except Exception:
            # fallback if even DDG failed
            await page.goto(INSTA_SEARCH_URL.format(INGREDIENT), wait_until="domcontentloaded")

        # ---------- Step 2: If we’re not on a search page, search on Instacart ----------
        # Try to fill any visible search box; otherwise we assume we’re already on /store/search?q=...
        try:
            # Try common search inputs
            search_selectors = [
                "input[placeholder*='Search']",
                "input[type='search']",
                "form[role='search'] input",
                "input[name='search']",
                "input[name='searchTerm']",
            ]
            found = False
            for sel in search_selectors:
                loc = page.locator(sel).first
                try:
                    await loc.wait_for(state="visible", timeout=2500)
                    await loc.click()
                    await loc.fill(INGREDIENT)
                    await page.keyboard.press("Enter")
                    found = True
                    break
                except PwTimeout:
                    continue
                except Exception:
                    continue

            if found:
                # allow results to load
                await page.wait_for_load_state("domcontentloaded")
                # give time for product grid hydration
                await page.wait_for_timeout(3000)
        except Exception:
            pass  # it’s fine—maybe we’re already on a search results page

        # ---------- Step 3: Add the first item ----------
        # scroll a bit to ensure first card’s buttons are in view
        try:
            await page.mouse.wheel(0, 400)
        except Exception:
            pass

        added = await add_first_item_to_cart(page)
        if added:
            print(f"✅ Added '{INGREDIENT}' to cart.")
        else:
            print("❌ Could not find an 'Add' button. You may need to log in or set your store/address first.")

        # brief pause so you can see the result before the window closes
        await page.wait_for_timeout(2500)
        await ctx.close()

if __name__ == "__main__":
    asyncio.run(run())
