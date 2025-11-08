# agents/search_order_agent_playwright.py
"""
Pure Playwright implementation - based on proven instacart_agent.py pattern
No LLM, just DOM selectors and heuristics
"""

from playwright.async_api import Page
from agents.base_agent import AgentUtils
from config.platforms import PLATFORM_CONFIGS
from models.cart_models import CartItem, PlatformCart, ItemStatus
from utils.popup_handler import dismiss_popups
from utils.retry_decorator import async_retry
import logging
import random
from typing import List
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

def human_delay(min_ms=300, max_ms=800):
    """Random delay to mimic human behavior"""
    return random.randint(min_ms, max_ms)

class SearchOrderAgentPlaywright:
    """
    Search for ingredients and add them to cart using pure Playwright
    
    Based on proven instacart_agent.py pattern - no LLM dependency
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.config = PLATFORM_CONFIGS[platform_name]
        self.playwright = None
        self.context = None
        self.page = None
    
    async def initialize(self):
        """Initialize browser context"""
        self.playwright, self.context, self.page = await AgentUtils.create_browser_context(self.platform_name)
    
    async def cleanup(self):
        """Cleanup browser resources"""
        if self.playwright and self.context:
            await AgentUtils.cleanup_browser(self.playwright, self.context)
    
    async def _first_href_containing(self, substring: str) -> str:
        """Find first link containing substring"""
        hrefs = await self.page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        for h in hrefs:
            if substring in h:
                return h
        return None
    
    async def _ensure_on_results_page(self, ingredient: str):
        """Navigate to search results page via DuckDuckGo"""
        query = f"{ingredient} {self.platform_name}"
        duck_url = f"https://duckduckgo.com/?q={quote_plus(query)}"
        
        try:
            # Try DuckDuckGo first
            await self.page.goto(duck_url, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(human_delay())
            
            # Find platform link
            href = await self._first_href_containing(self.config["name"].lower())
            if not href:
                # Fallback to direct search URL
                href = self.config["search_url"].format(quote_plus(ingredient))
            
            await self.page.goto(href, wait_until="domcontentloaded")
        except Exception:
            # Direct fallback
            await self.page.goto(self.config["search_url"].format(quote_plus(ingredient)), 
                                wait_until="domcontentloaded")
        
        await dismiss_popups(self.page)
        
        # Try site search box if needed
        search_selectors = [
            "input[placeholder*='Search']",
            "input[type='search']",
            "form[role='search'] input",
            "input[name='search']",
            "input[name='searchTerm']",
        ]
        for sel in search_selectors:
            loc = self.page.locator(sel).first
            try:
                await loc.wait_for(state="visible", timeout=1800)
                await loc.click()
                await loc.fill(ingredient)
                await self.page.keyboard.press("Enter")
                break
            except Exception:
                continue
        
        await self.page.wait_for_load_state("domcontentloaded")
        await self.page.wait_for_timeout(900)
        await dismiss_popups(self.page)
    
    async def _count_product_cards(self) -> int:
        """Count visible product tiles/cards"""
        selectors = [
            "[data-testid*='item-card']",
            "[data-test*='item-card']",
            "[class*='ItemCard']",
            "[class*='product']",
            "[class*='Product']",
            "button:has-text('Add')",
        ]
        total = 0
        for sel in selectors:
            try:
                total = max(total, await self.page.locator(sel).count())
            except Exception:
                pass
        return total
    
    async def _page_indicates_no_results(self) -> bool:
        """Check for explicit 'no results' messages"""
        texts = [
            "No results", "no results", "0 results",
            "We couldn't find any results",
            "Try a different search", "No items found",
            "did not match any products",
        ]
        for t in texts:
            try:
                if await self.page.get_by_text(t, exact=False).first.is_visible():
                    return True
            except:
                pass
        
        # Check empty state selectors
        empty_selectors = [
            "[data-testid*='no-results']",
            "[data-test*='no-results']",
            "[data-testid*='empty']",
            "[class*='EmptyState']",
        ]
        for sel in empty_selectors:
            try:
                if await self.page.locator(sel).first.is_visible():
                    return True
            except:
                pass
        return False
    
    async def _thorough_results_check(self) -> bool:
        """Check if query has results"""
        # Check explicit 'no results'
        if await self._page_indicates_no_results():
            return False
        
        # Count product cards
        cards_before = await self._count_product_cards()
        
        # Progressive scroll to trigger lazy loading
        for _ in range(6):
            try:
                await self.page.mouse.wheel(0, 500)
                await self.page.wait_for_timeout(200)
            except Exception:
                pass
        
        cards_after = await self._count_product_cards()
        return max(cards_before, cards_after) > 0
    
    async def _add_first_item_to_cart(self) -> bool:
        """Find an 'Add' button and click it"""
        candidates = [
            "button:has-text('Add')",
            "button:has-text('ADD')",
            "button[aria-label*='Add']",
            "[data-testid*='Add']",
            "[data-testid*='add']",
            "[data-test*='add']",
            "[role='button'][aria-label*='Add']",
        ]
        
        # Scroll to bring items into view
        for _ in range(4):
            try:
                await self.page.mouse.wheel(0, 350)
                await self.page.wait_for_timeout(180)
            except Exception:
                pass
        
        # Try twice with popup dismissal
        for _ in range(2):
            for sel in candidates:
                btn = self.page.locator(sel).first
                try:
                    if await btn.is_visible():
                        await btn.click()
                        return True
                except Exception:
                    continue
            await dismiss_popups(self.page)
            await self.page.wait_for_timeout(250)
        
        return False
    
    @async_retry(max_attempts=3, backoff_base=2.0)
    async def search_and_add_item(self, ingredient: str) -> CartItem:
        """
        Search for ONE ingredient and add first available result to cart
        
        Args:
            ingredient: Ingredient name (e.g., "milk")
        
        Returns:
            CartItem with result status
        """
        logger.info(f"[{self.platform_name}] Searching for: {ingredient}")
        
        await self._ensure_on_results_page(ingredient)
        
        # Check if results exist
        has_results = await self._thorough_results_check()
        if not has_results:
            logger.warning(f"[{self.platform_name}] No results for: {ingredient}")
            return CartItem(
                ingredient_requested=ingredient,
                product_name="Not Found",
                product_url="",
                price=0.0,
                status=ItemStatus.NOT_FOUND
            )
        
        # Try to add item
        added = await self._add_first_item_to_cart()
        if added:
            logger.info(f"[{self.platform_name}] Added '{ingredient}' to cart")
            # Return basic item (we don't extract details in this flow)
            return CartItem(
                ingredient_requested=ingredient,
                product_name=f"{ingredient} (added)",
                product_url=self.page.url,
                price=0.0,  # Will be extracted by CartDetailAgent
                status=ItemStatus.ADDED
            )
        else:
            logger.warning(f"[{self.platform_name}] Could not add '{ingredient}'")
            return CartItem(
                ingredient_requested=ingredient,
                product_name="Failed to add",
                product_url="",
                price=0.0,
                status=ItemStatus.FAILED
            )
    
    async def search_and_add_all(self, ingredients: List[str]) -> PlatformCart:
        """
        Search and add ALL ingredients for this platform
        
        Args:
            ingredients: List of ingredient names
        
        Returns:
            PlatformCart with all items
        """
        await self.initialize()
        
        cart = PlatformCart(
            platform_name=self.platform_name,
            platform_id=self.config["merchant_id"]
        )
        
        try:
            for ingredient in ingredients:
                try:
                    item = await self.search_and_add_item(ingredient)
                    cart.add_item(item)
                    await self.page.wait_for_timeout(human_delay(650, 1200))
                except Exception as e:
                    logger.error(f"Failed to add {ingredient}: {e}")
                    cart.add_item(CartItem(
                        ingredient_requested=ingredient,
                        product_name="Failed",
                        product_url="",
                        price=0.0,
                        status=ItemStatus.FAILED
                    ))
            
            return cart
            
        finally:
            await self.cleanup()

