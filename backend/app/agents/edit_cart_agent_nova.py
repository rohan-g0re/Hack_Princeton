# agents/edit_cart_agent_nova.py
"""
Edit Cart agent using Amazon Nova Act
Applies user edits (diffs) to platform carts
"""

from nova_act import NovaAct
from config.platforms import PLATFORM_CONFIGS
from models.cart_models import CartDiff, PlatformCart
import logging
import os
from dotenv import load_dotenv
from typing import List

logger = logging.getLogger(__name__)
load_dotenv()

# Configure Nova Act API key
nova_key = os.getenv("NOVA_ACT_API_KEY")
if not nova_key:
    raise ValueError("NOVA_ACT_API_KEY environment variable not set")
os.environ["NOVA_ACT_API_KEY"] = nova_key

# Browser debugging port
os.environ["NOVA_ACT_BROWSER_ARGS"] = "--remote-debugging-port=9222"


class EditCartAgentNova:
    """
    Apply user edits to platform carts using Nova Act
    
    Processes CartDiff objects and applies changes to actual carts
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.config = PLATFORM_CONFIGS[platform_name]
        self.nova = None
    
    def start_session(self):
        """Start a persistent Nova Act session"""
        if self.nova is None:
            logger.info(f"[{self.platform_name}] Starting edit cart session...")
            
            # Convert relative path to absolute path for Windows compatibility
            user_data_path = os.path.abspath(self.config["user_data_dir"])
            
            # Create directory if it doesn't exist
            os.makedirs(user_data_path, exist_ok=True)
            logger.info(f"[{self.platform_name}] User data directory: {user_data_path}")
            
            self.nova = NovaAct(
                starting_page=self.config["cart_url"],
                user_data_dir=user_data_path
            )
            self.nova.start()
            logger.info(f"[{self.platform_name}] Session started")
    
    def stop_session(self):
        """Stop the persistent Nova Act session"""
        if self.nova:
            logger.info(f"[{self.platform_name}] Stopping edit cart session...")
            self.nova.stop()
            self.nova = None
    
    async def apply_diffs(self, diffs: List[CartDiff]) -> bool:
        """
        Public async API expected by orchestrators.
        Runs synchronous NovaAct in a background thread.
        
        Args:
            diffs: List of CartDiff objects to apply
        
        Returns:
            True if all diffs applied successfully
        """
        import asyncio
        return await asyncio.to_thread(self._apply_diffs_sync, diffs)
    
    def _apply_diffs_sync(self, diffs: List[CartDiff]) -> bool:
        """
        Synchronous implementation of diff application
        """
        if not diffs:
            logger.info(f"[{self.platform_name}] No diffs to apply")
            return True
        
        logger.info(f"[{self.platform_name}] Applying {len(diffs)} cart edits...")
        
        # Start session
        self.start_session()
        
        success_count = 0
        
        try:
            for idx, diff in enumerate(diffs):
                logger.info(f"[{self.platform_name}] Applying diff {idx + 1}/{len(diffs)}: {diff.action} - {diff.item.product_name}")
                
                try:
                    # Build instruction based on action
                    if diff.action == "remove":
                        instruction = self._build_remove_instruction(diff)
                    elif diff.action == "add":
                        instruction = self._build_add_instruction(diff)
                    else:
                        logger.warning(f"[{self.platform_name}] Unknown action: {diff.action}")
                        continue
                    
                    # Execute the instruction
                    result = self.nova.act(instruction, max_steps=50)
                    logger.info(f"[{self.platform_name}] Diff applied: {result}")
                    
                    # Mark diff as applied
                    diff.applied = True
                    success_count += 1
                
                except Exception as e:
                    logger.error(f"[{self.platform_name}] Error applying diff {idx + 1}: {e}")
                    # Continue with next diff even if this one fails
                    continue
            
            logger.info(f"[{self.platform_name}] Applied {success_count}/{len(diffs)} diffs successfully")
        
        finally:
            self.stop_session()
        
        return success_count == len(diffs)
    
    def _build_remove_instruction(self, diff: CartDiff) -> str:
        """Build instruction to remove an item from cart"""
        item_name = diff.item.product_name
        
        instruction = (
            "Go to the cart page. "
            f"Find the item named '{item_name}'. "
            "Remove it from the cart. "
            "Confirm the removal if prompted. "
            "Return the updated cart total."
        )
        
        return instruction
    
    def _build_add_instruction(self, diff: CartDiff) -> str:
        """Build instruction to add an item to cart"""
        item_name = diff.item.product_name
        quantity = diff.item.quantity
        
        instruction = (
            f"Search for '{item_name}'. "
            f"Add {quantity} to cart. "
            "Return the updated cart total."
        )
        
        return instruction


def main():
    """
    CLI entry point for testing edit cart
    
    Usage:
        python -m agents.edit_cart_agent_nova instacart
    """
    import sys
    import asyncio
    from models.cart_models import CartItem, ItemStatus
    
    if len(sys.argv) < 2:
        print("Usage: python -m agents.edit_cart_agent_nova <platform_name>")
        print("Available platforms: instacart, ubereats, doordash")
        sys.exit(1)
    
    platform_name = sys.argv[1].lower()
    
    if platform_name not in PLATFORM_CONFIGS:
        print(f"Error: Unknown platform '{platform_name}'")
        sys.exit(1)
    
    agent = EditCartAgentNova(platform_name)
    
    # Create a test diff (remove operation)
    test_item = CartItem(
        ingredient_requested="milk",
        product_name="Organic Whole Milk",
        product_url="",
        price=5.99,
        status=ItemStatus.ADDED
    )
    
    test_diff = CartDiff(
        platform=platform_name,
        action="remove",
        item=test_item,
        timestamp=None
    )
    
    print(f"\nApplying test diff to {platform_name}...")
    print(f"Action: {test_diff.action}")
    print(f"Item: {test_diff.item.product_name}\n")
    
    success = asyncio.run(agent.apply_diffs([test_diff]))
    
    if success:
        print(f"\n✓ Diff applied successfully!")
    else:
        print(f"\n✗ Diff application failed")


if __name__ == "__main__":
    main()

