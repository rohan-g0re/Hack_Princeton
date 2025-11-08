# agents/search_order_agent.py

from browser_use import Agent
from playwright.async_api import Page
from agents.base_agent import AgentUtils
from config.platforms import PLATFORM_CONFIGS
from models.cart_models import CartItem, PlatformCart, ItemStatus
from utils.popup_handler import dismiss_popups
from utils.retry_decorator import async_retry
import logging
import os
from typing import List

logger = logging.getLogger(__name__)

# BrowserUse LLM setup with Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    """Get configured LLM for BrowserUse - using Gemini"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",  # Fast and cost-effective
        google_api_key=api_key,
        temperature=0.1  # Low temperature for consistent results
    )

class SearchOrderAgent:
    """
    Search for ingredients and add them to cart
    
    Uses BrowserUse for AI-powered browser automation.
    Handles search, result validation, and cart addition.
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.config = PLATFORM_CONFIGS[platform_name]
        self.llm = get_llm()
        self.playwright = None
        self.context = None
        self.page = None
    
    async def initialize(self):
        """Initialize browser context"""
        self.playwright, self.context, self.page = await AgentUtils.create_browser_context(self.platform_name)
        
        # Verify session valid
        if not await AgentUtils.check_session_valid(self.page, self.platform_name):
            raise ValueError(f"Not logged in to {self.platform_name}. Run SignIn agent first.")
    
    async def cleanup(self):
        """Cleanup browser resources"""
        if self.playwright and self.context:
            await AgentUtils.cleanup_browser(self.playwright, self.context)
    
    @async_retry(max_attempts=3, backoff_base=2.0)
    async def search_and_add_item(self, ingredient: str) -> CartItem:
        """
        Search for ONE ingredient and add first available result to cart
        
        Args:
            ingredient: Ingredient name (e.g., "milk")
        
        Returns:
            CartItem with result status
        
        Raises:
            Exception if all retries fail
        """
        logger.info(f"[{self.platform_name}] Searching for: {ingredient}")
        
        # Dismiss any existing popups
        await dismiss_popups(self.page)
        
        # BrowserUse task description
        task = f"""
        Search for '{ingredient}' on this grocery delivery website.
        
        Instructions:
        1. Find the search box and enter '{ingredient}'
        2. Wait for search results to load
        3. If NO results found, report "NO_RESULTS"
        4. If results found, click the "Add" button on the FIRST available product
        5. Handle any popups or dialogs that appear
        6. Report the product name and price that was added
        
        Important:
        - Choose the FIRST available product only
        - If a popup blocks the action, dismiss it and retry
        - If product is out of stock, report "OUT_OF_STOCK"
        """
        
        # Run BrowserUse agent
        agent = Agent(task=task, llm=self.llm)
        result = await agent.run(self.page)
        
        # Parse result
        result_text = str(result).lower()
        
        if "no_results" in result_text or "no results" in result_text:
            logger.warning(f"[{self.platform_name}] No results for: {ingredient}")
            return CartItem(
                ingredient_requested=ingredient,
                product_name="Not Found",
                product_url="",
                price=0.0,
                status=ItemStatus.NOT_FOUND
            )
        
        if "out_of_stock" in result_text:
            logger.warning(f"[{self.platform_name}] Out of stock: {ingredient}")
            return CartItem(
                ingredient_requested=ingredient,
                product_name="Out of Stock",
                product_url="",
                price=0.0,
                status=ItemStatus.OUT_OF_STOCK
            )
        
        # Extract product details from page
        # BrowserUse should have added to cart, now we extract details
        product_name, price, url = await self._extract_last_added_item()
        
        logger.info(f"[{self.platform_name}] Added: {product_name} (${price})")
        
        return CartItem(
            ingredient_requested=ingredient,
            product_name=product_name,
            product_url=url,
            price=price,
            status=ItemStatus.ADDED
        )
    
    async def _extract_last_added_item(self):
        """
        Extract details of last item added to cart
        
        Strategy: Navigate to cart and extract last item details
        
        Returns:
            Tuple of (product_name, price, url)
        """
        try:
            await self.page.goto(self.config["cart_url"], wait_until="domcontentloaded")
            await dismiss_popups(self.page)
            
            # Platform-specific selectors (customize per platform)
            # This is a generic approach - may need refinement
            
            # Try to extract last cart item
            cart_items = await self.page.query_selector_all("[data-testid*='cart-item'], .cart-item, [class*='CartItem']")
            
            if not cart_items:
                return ("Unknown Product", 0.0, "")
            
            last_item = cart_items[-1]
            
            # Extract name
            name_elem = await last_item.query_selector("[class*='name'], [class*='title'], h3, h4")
            product_name = await name_elem.inner_text() if name_elem else "Unknown Product"
            
            # Extract price
            price_elem = await last_item.query_selector("[class*='price'], [data-testid*='price']")
            price_text = await price_elem.inner_text() if price_elem else "$0.00"
            price = float(price_text.replace("$", "").replace(",", "").strip())
            
            # Get current URL as product URL (cart page)
            url = self.page.url
            
            return (product_name.strip(), price, url)
            
        except Exception as e:
            logger.warning(f"Failed to extract cart item details: {e}")
            return ("Unknown Product", 0.0, "")
    
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
                except Exception as e:
                    logger.error(f"Failed to add {ingredient}: {e}")
                    # Add failed item
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

