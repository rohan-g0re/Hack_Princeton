# agents/signin_agent.py

from agents.base_agent import AgentUtils
from config.platforms import PLATFORM_CONFIGS
from utils.popup_handler import dismiss_popups
import logging

logger = logging.getLogger(__name__)

class SignInAgent:
    """
    Handles user authentication for delivery platforms
    
    This agent opens a browser for the user to manually log in.
    Once logged in, the session is persisted in the platform's
    user_data_dir and reused by other agents.
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.config = PLATFORM_CONFIGS[platform_name]
    
    async def run(self) -> bool:
        """
        Execute sign-in flow
        
        Returns:
            True if sign-in successful, False otherwise
        """
        logger.info(f"Starting sign-in for {self.platform_name}")
        
        playwright, context, page = await AgentUtils.create_browser_context(self.platform_name)
        
        try:
            # Check if already logged in
            if await AgentUtils.check_session_valid(page, self.platform_name):
                logger.info(f"Already logged in to {self.platform_name}")
                return True
            
            # Navigate to login page
            await page.goto(self.config["login_url"], wait_until="domcontentloaded")
            await dismiss_popups(page)
            
            logger.info(f"Waiting for user to log in to {self.platform_name}...")
            logger.info("Please log in manually in the browser window.")
            
            # Wait for successful login (cart page accessible)
            # Poll cart page until accessible (max 5 minutes)
            for _ in range(60):  # 60 attempts * 5 seconds = 5 minutes
                await page.wait_for_timeout(5000)
                
                if await AgentUtils.check_session_valid(page, self.platform_name):
                    logger.info(f"Successfully logged in to {self.platform_name}!")
                    return True
            
            logger.error(f"Login timeout for {self.platform_name}")
            return False
            
        except Exception as e:
            logger.error(f"Sign-in failed for {self.platform_name}: {e}")
            return False
            
        finally:
            await AgentUtils.cleanup_browser(playwright, context)

# CLI entry point for testing
async def main():
    import sys
    import asyncio
    platform = sys.argv[1] if len(sys.argv) > 1 else "instacart"
    
    agent = SignInAgent(platform)
    success = await agent.run()
    
    print(f"\n{'[SUCCESS]' if success else '[FAILURE]'}: {platform}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

