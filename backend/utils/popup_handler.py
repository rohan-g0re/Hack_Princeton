# utils/popup_handler.py

from playwright.async_api import Page

CLOSE_SELECTORS = [
    "[aria-label='Close']",
    "[aria-label*='close']",
    "button:has-text('Close')",
    "button:has-text('Got it')",
    "button:has-text('Dismiss')",
    "button:has-text('Not now')",
    "button:has-text('Accept')",
    "button:has-text('Continue')",
    "[data-testid*='close']",
    "[data-test*='close']",
    "[class*='close']",
    "[role='button'][aria-label*='Close']",
    "button[aria-label*='Dismiss']",
    "button :text('×')",
]

async def dismiss_popups(page: Page, attempts: int = 6) -> None:
    """
    Aggressively dismiss popups, modals, and dialogs
    
    Strategy:
    1. Press Escape key (works for many modals)
    2. Find and click visible close buttons
    3. Handle dialogs specifically
    
    Args:
        page: Playwright page object
        attempts: Number of dismissal cycles
    """
    for _ in range(attempts):
        try:
            # Escape key first
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(150)
            
            # Try all close button selectors
            for sel in CLOSE_SELECTORS:
                loc = page.locator(sel).filter(has_not=page.locator("[aria-hidden='true']")).first
                if await loc.is_visible():
                    try:
                        await loc.click(timeout=700)
                        await page.wait_for_timeout(200)
                    except Exception:
                        pass
            
            # Handle dialog elements specifically
            dialogs = page.get_by_role("dialog")
            count = await dialogs.count()
            for i in range(count):
                dlg = dialogs.nth(i)
                if await dlg.is_visible():
                    inner_close = dlg.locator(", ".join(CLOSE_SELECTORS)).first
                    if await inner_close.is_visible():
                        try:
                            await inner_close.click(timeout=700)
                            await page.wait_for_timeout(200)
                        except Exception:
                            pass
        except Exception:
            pass

