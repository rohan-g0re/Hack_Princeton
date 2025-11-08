# agents/base_agent.py

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from config.platforms import PLATFORM_CONFIGS, BROWSER_ARGS, HEADLESS
import logging

logger = logging.getLogger(__name__)

class AgentUtils:
    """
    Shared utilities for all agents
    
    NOT a base class - agents don't inherit from this.
    Use these functions directly.
    """
    
    @staticmethod
    async def create_browser_context(platform_name: str):
        """
        Create persistent browser context for a platform
        
        Uses Playwright persistent context to maintain login sessions
        across agent runs. Session data stored in user_data_dir.
        
        Args:
            platform_name: Platform identifier (e.g., "instacart")
        
        Returns:
            Tuple of (playwright_instance, browser_context, page)
        
        Usage:
            p, ctx, page = await AgentUtils.create_browser_context("instacart")
            # ... do work ...
            await ctx.close()
            await p.stop()
        """
        config = PLATFORM_CONFIGS[platform_name]
        
        playwright = await async_playwright().start()
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=config["user_data_dir"],
            headless=HEADLESS,
            args=BROWSER_ARGS,
        )
        
        page = await context.new_page()
        logger.info(f"Created browser context for {platform_name}")
        
        return playwright, context, page
    
    @staticmethod
    async def cleanup_browser(playwright, context):
        """
        Cleanup browser resources
        
        Args:
            playwright: Playwright instance from create_browser_context
            context: Browser context from create_browser_context
        """
        try:
            await context.close()
            await playwright.stop()
            logger.info("Browser context cleaned up")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    @staticmethod
    async def check_session_valid(page: Page, platform_name: str) -> bool:
        """
        Check if user is still logged in
        
        Strategy: Navigate to account/cart page, check if redirected to login
        
        Args:
            page: Playwright page
            platform_name: Platform identifier
        
        Returns:
            True if logged in, False if login required
        """
        config = PLATFORM_CONFIGS[platform_name]
        
        try:
            await page.goto(config["cart_url"], wait_until="domcontentloaded", timeout=10000)
            await page.wait_for_timeout(1000)
            
            # If URL contains "login" or "signin", session expired
            current_url = page.url.lower()
            if "login" in current_url or "signin" in current_url or "sign-in" in current_url:
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Session check failed for {platform_name}: {e}")
            return False

