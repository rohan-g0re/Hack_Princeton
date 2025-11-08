# agents/edit_cart_agent.py

from browser_use import Agent
from agents.base_agent import AgentUtils
from config.platforms import PLATFORM_CONFIGS
from models.cart_models import CartDiff
from utils.popup_handler import dismiss_popups
from utils.retry_decorator import async_retry
import logging
import os
from typing import List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

from langchain.chat_models import init_chat_model

load_dotenv()

def get_llm():
    """Get configured LLM for BrowserUse - using Gemini with proper provider interface"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    # Use init_chat_model for proper provider interface that BrowserUse expects
    return init_chat_model(
        "gemini-1.5-flash",
        model_provider="google_genai",
        api_key=api_key,
        temperature=0.1
    )

class EditCartAgent:
    """
    Apply cart modifications (diffs) to actual platform cart
    
    Handles:
    - Removing items from cart
    - Adding new items to cart
    - Updating quantities
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
        
        # Don't check session - would navigate to cart page prematurely
        # Persistent context already has the session
    
    async def cleanup(self):
        """Cleanup browser resources"""
        if self.playwright and self.context:
            await AgentUtils.cleanup_browser(self.playwright, self.context)
    
    @async_retry(max_attempts=3)
    async def apply_diff(self, diff: CartDiff) -> bool:
        """
        Apply a single cart diff
        
        Args:
            diff: CartDiff object describing the change
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"[{self.platform_name}] Applying diff: {diff.action} - {diff.item.product_name}")
        
        # Navigate to cart
        await self.page.goto(self.config["cart_url"], wait_until="domcontentloaded")
        await dismiss_popups(self.page)
        
        if diff.action == "remove":
            return await self._remove_item(diff.item.product_name)
        elif diff.action == "add":
            return await self._add_item(diff.item.ingredient_requested)
        elif diff.action == "update_quantity":
            return await self._update_quantity(diff.item.product_name, diff.item.quantity)
        else:
            logger.error(f"Unknown diff action: {diff.action}")
            return False
    
    async def _remove_item(self, product_name: str) -> bool:
        """Remove item from cart by product name"""
        task = f"""
        Remove the product '{product_name}' from the shopping cart.
        
        Instructions:
        1. Find the cart item with name '{product_name}'
        2. Click the "Remove" or "Delete" button for this item
        3. Confirm if a confirmation dialog appears
        4. Verify the item is no longer in the cart
        """
        
        agent = Agent(task=task, llm=self.llm)
        result = await agent.run(self.page)
        
        logger.info(f"Remove result: {result}")
        return True  # BrowserUse handles verification
    
    async def _add_item(self, ingredient: str) -> bool:
        """Add new item to cart (same as SearchOrderAgent logic)"""
        task = f"""
        Search for '{ingredient}' and add it to the cart.
        
        Instructions:
        1. Navigate to the search page or use search box
        2. Search for '{ingredient}'
        3. Add the first available product to cart
        4. Handle any popups
        """
        
        agent = Agent(task=task, llm=self.llm)
        result = await agent.run(self.page)
        
        logger.info(f"Add result: {result}")
        return True
    
    async def _update_quantity(self, product_name: str, new_quantity: int) -> bool:
        """Update quantity of item in cart"""
        task = f"""
        Update the quantity of '{product_name}' to {new_quantity}.
        
        Instructions:
        1. Find the cart item '{product_name}'
        2. Locate the quantity selector (dropdown or input)
        3. Change the quantity to {new_quantity}
        4. Confirm the change
        """
        
        agent = Agent(task=task, llm=self.llm)
        result = await agent.run(self.page)
        
        logger.info(f"Update quantity result: {result}")
        return True
    
    async def apply_all_diffs(self, diffs: List[CartDiff]) -> int:
        """
        Apply all diffs for this platform
        
        Args:
            diffs: List of CartDiff objects
        
        Returns:
            Number of successfully applied diffs
        """
        await self.initialize()
        
        success_count = 0
        
        try:
            for diff in diffs:
                try:
                    if await self.apply_diff(diff):
                        success_count += 1
                        diff.applied = True
                except Exception as e:
                    logger.error(f"Failed to apply diff: {e}")
            
            return success_count
            
        finally:
            await self.cleanup()

