# agents/signin_agent.py

from playwright.async_api import async_playwright
from config.platforms import PLATFORM_CONFIGS
from utils.popup_handler import dismiss_popups
import logging

logger = logging.getLogger(__name__)

class SignInAgent:
    """
    Handles user authentication for delivery platforms
    
    Opens a persistent browser for the user to manually log in.
    Session is saved in user_data_dir and reused by other agents.
    
    Based on proven instacart_agent.py pattern.
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.config = PLATFORM_CONFIGS[platform_name]
    
    async def run(self) -> bool:
        """
        Execute sign-in flow
        
        Opens browser and waits for user to log in manually.
        Session persists in user_data_dir for future use.
        
        Returns:
            True if sign-in successful, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"SIGN IN TO {self.platform_name.upper()}")
        print("="*70)
        print(f"\nOpening browser for {self.config['name']}...")
        print("Please log in manually in the browser window.")
        print("The session will be saved for future runs.")
        print("\nPress ENTER after you've successfully logged in...")
        print("="*70)
        
        async with async_playwright() as p:
            # Use persistent context - same pattern as instacart_agent.py
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=self.config["user_data_dir"],
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )
            
            page = await ctx.new_page()
            
            try:
                # Navigate to login page
                await page.goto(self.config["login_url"], wait_until="domcontentloaded")
                await page.wait_for_timeout(1000)
                await dismiss_popups(page)
                
                # Wait for user confirmation
                input()  # Wait for user to press ENTER
                
                # Verify login by checking cart page
                print("\nVerifying login...")
                await page.goto(self.config["cart_url"], wait_until="domcontentloaded", timeout=10000)
                await page.wait_for_timeout(2000)
                
                # Check if we're still on login page (login failed)
                current_url = page.url.lower()
                if "login" in current_url or "signin" in current_url or "sign-in" in current_url:
                    print(f"\n[FAILURE] Still on login page. Please try again.")
                    await ctx.close()
                    return False
                
                print(f"\n[SUCCESS] Successfully logged in to {self.config['name']}!")
                print(f"Session saved to: {self.config['user_data_dir']}")
                print("You can now run the main workflow.\n")
                
                await page.wait_for_timeout(1000)
                await ctx.close()
                return True
                
            except Exception as e:
                print(f"\n[ERROR] Sign-in failed: {e}")
                await ctx.close()
                return False

# CLI entry point
async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m agents.signin_agent <platform>")
        print("Platforms: instacart, ubereats, doordash")
        return
    
    platform = sys.argv[1]
    
    if platform not in PLATFORM_CONFIGS:
        print(f"Unknown platform: {platform}")
        print(f"Available: {', '.join(PLATFORM_CONFIGS.keys())}")
        return
    
    agent = SignInAgent(platform)
    await agent.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

