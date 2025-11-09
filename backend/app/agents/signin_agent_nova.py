# agents/signin_agent_nova.py
"""
Sign-in agent using Amazon Nova Act
Handles manual authentication with persistent session management
"""

from nova_act import NovaAct
from config.platforms import PLATFORM_CONFIGS
import logging
import os
from dotenv import load_dotenv
import time

logger = logging.getLogger(__name__)
load_dotenv()

# Configure Nova Act API key
nova_key = os.getenv("NOVA_ACT_API_KEY")
if not nova_key:
    raise ValueError("NOVA_ACT_API_KEY environment variable not set")
os.environ["NOVA_ACT_API_KEY"] = nova_key

# Browser debugging port
os.environ["NOVA_ACT_BROWSER_ARGS"] = "--remote-debugging-port=9222"


class SignInAgentNova:
    """
    Handle platform authentication using Nova Act
    
    Opens browser to login page and waits for user to manually sign in.
    Session is persisted via user_data_dir for future use.
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.config = PLATFORM_CONFIGS[platform_name]
        self.nova = None
    
    def signin(self, wait_time: int = 120):
        """
        Open browser to login page and wait for user to sign in manually
        
        Args:
            wait_time: How long to keep browser open for user to sign in (seconds)
        """
        logger.info(f"[{self.platform_name}] Starting sign-in process...")
        
        try:
            # Convert relative path to absolute path for Windows compatibility
            user_data_path = os.path.abspath(self.config["user_data_dir"])
            
            # Create directory if it doesn't exist
            os.makedirs(user_data_path, exist_ok=True)
            logger.info(f"[{self.platform_name}] User data directory: {user_data_path}")
            
            # Start Nova Act with persistent user data directory
            self.nova = NovaAct(
                starting_page=self.config["login_url"],
                user_data_dir=user_data_path
            )
            self.nova.start()
            
            logger.info(f"[{self.platform_name}] Browser opened at login page")
            logger.info(f"[{self.platform_name}] Please sign in manually in the browser window")
            logger.info(f"[{self.platform_name}] Waiting {wait_time} seconds for you to complete sign-in...")
            
            # Give instruction to wait at login page
            instruction = (
                "Stay on the login page. "
                "Wait for the user to manually sign in. "
                "Do not close any windows."
            )
            
            # Execute with a short step limit to just load the page
            result = self.nova.act(instruction, max_steps=5)
            logger.info(f"[{self.platform_name}] Navigation result: {result}")
            
            # Wait for user to complete sign-in
            print(f"\n{'='*70}")
            print(f"SIGN IN TO {self.platform_name.upper()}")
            print(f"{'='*70}")
            print(f"Browser is now open. Please sign in manually.")
            print(f"You have {wait_time} seconds to complete sign-in.")
            print(f"The session will be saved for future use.")
            print(f"{'='*70}\n")
            
            time.sleep(wait_time)
            
            logger.info(f"[{self.platform_name}] Sign-in wait period completed")
            logger.info(f"[{self.platform_name}] Session data saved to: {self.config['user_data_dir']}")
            
        except Exception as e:
            logger.error(f"[{self.platform_name}] Sign-in error: {e}")
            raise
        
        finally:
            if self.nova:
                self.nova.stop()
                self.nova = None
        
        print(f"\n[{self.platform_name}] Sign-in process completed!")
        print(f"Session saved. Future operations will use this authenticated session.\n")
    
    def check_session_exists(self) -> bool:
        """
        Check if a session already exists for this platform
        
        Returns:
            True if user_data_dir exists with session data
        """
        user_data_dir = self.config["user_data_dir"]
        
        # Check if the directory exists and has content
        if os.path.exists(user_data_dir):
            # Check for Default directory (Chrome profile indicator)
            default_dir = os.path.join(user_data_dir, "Default")
            if os.path.exists(default_dir):
                logger.info(f"[{self.platform_name}] Existing session found at: {user_data_dir}")
                return True
        
        logger.info(f"[{self.platform_name}] No existing session found")
        return False


def main():
    """
    CLI entry point for manual sign-in to platforms
    
    Usage:
        python -m agents.signin_agent_nova instacart
        python -m agents.signin_agent_nova ubereats
        python -m agents.signin_agent_nova doordash
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m agents.signin_agent_nova <platform_name>")
        print("Available platforms: instacart, ubereats, doordash")
        sys.exit(1)
    
    platform_name = sys.argv[1].lower()
    
    if platform_name not in PLATFORM_CONFIGS:
        print(f"Error: Unknown platform '{platform_name}'")
        print("Available platforms: instacart, ubereats, doordash")
        sys.exit(1)
    
    agent = SignInAgentNova(platform_name)
    
    # Check if session already exists
    if agent.check_session_exists():
        print(f"\n[INFO] Session already exists for {platform_name}")
        print("Do you want to sign in again? (y/n): ", end="")
        response = input().strip().lower()
        if response != 'y':
            print("Skipping sign-in. Using existing session.")
            sys.exit(0)
    
    # Perform sign-in
    agent.signin(wait_time=120)


if __name__ == "__main__":
    main()

