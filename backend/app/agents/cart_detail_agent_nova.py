# agents/cart_detail_agent_nova.py
"""
Cart Detail agent using Amazon Nova Act
Extracts current cart contents from platforms
"""

from nova_act import NovaAct
from config.platforms import PLATFORM_CONFIGS
from models.cart_models import CartItem, PlatformCart, ItemStatus
import logging
import os
from dotenv import load_dotenv
import re
import json

logger = logging.getLogger(__name__)
load_dotenv()

# Configure Nova Act API key
nova_key = os.getenv("NOVA_ACT_API_KEY")
if not nova_key:
    raise ValueError("NOVA_ACT_API_KEY environment variable not set")
os.environ["NOVA_ACT_API_KEY"] = nova_key

# Browser debugging port
os.environ["NOVA_ACT_BROWSER_ARGS"] = "--remote-debugging-port=9222"


class CartDetailAgentNova:
    """
    Extract cart details from platforms using Nova Act
    
    Uses natural language queries to get cart contents
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.config = PLATFORM_CONFIGS[platform_name]
        self.nova = None
    
    def start_session(self):
        """Start a persistent Nova Act session"""
        if self.nova is None:
            logger.info(f"[{self.platform_name}] Starting cart detail session...")
            
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
            logger.info(f"[{self.platform_name}] Stopping cart detail session...")
            self.nova.stop()
            self.nova = None
    
    async def extract_cart_details(self) -> PlatformCart:
        """
        Public async API expected by orchestrators.
        Runs synchronous NovaAct in a background thread.
        """
        import asyncio
        return await asyncio.to_thread(self._extract_cart_details_sync)
    
    def _extract_cart_details_sync(self) -> PlatformCart:
        """
        Synchronous implementation of cart detail extraction
        """
        cart = PlatformCart(
            platform_name=self.platform_name,
            platform_id=self.config["merchant_id"]
        )
        
        logger.info(f"[{self.platform_name}] Extracting cart details...")
        
        # Start session
        self.start_session()
        
        try:
            # Build instruction to extract cart details
            instruction = (
                "Go to the cart page. "
                "List all items in the cart with their names, prices, and quantities. "
                "If the cart is empty, say 'Cart is empty'. "
                "Return the subtotal or total amount."
            )
            
            # Execute
            result = self.nova.act(instruction, max_steps=50)
            logger.info(f"[{self.platform_name}] Cart extraction result: {result}")
            
            # Parse the result
            cart = self._parse_cart_response(result)
            
            logger.info(f"[{self.platform_name}] Found {len(cart.items)} items, total: ${cart.total:.2f}")
        
        except Exception as e:
            logger.error(f"[{self.platform_name}] Cart detail extraction error: {e}")
            # Return empty cart on error
        
        finally:
            self.stop_session()
        
        return cart
    
    def _parse_cart_response(self, response: str) -> PlatformCart:
        """
        Parse Nova Act's response to extract cart items
        
        This is a best-effort parser. Nova's responses may vary.
        """
        cart = PlatformCart(
            platform_name=self.platform_name,
            platform_id=self.config["merchant_id"]
        )
        
        if not response or "empty" in response.lower():
            logger.info(f"[{self.platform_name}] Cart is empty")
            return cart
        
        # Try to parse items from the response
        # Look for patterns like:
        # - "Item Name - $X.XX"
        # - "Item Name: $X.XX"
        # - "Item Name $X.XX x 2"
        
        lines = response.split('\n')
        
        for line in lines:
            # Skip empty lines and headers
            if not line.strip() or len(line.strip()) < 5:
                continue
            
            # Try to extract item name and price
            # Pattern 1: Name - $X.XX
            match = re.search(r'(.+?)\s*[-:]\s*\$(\d+\.?\d*)', line)
            if not match:
                # Pattern 2: Name $X.XX
                match = re.search(r'(.+?)\s+\$(\d+\.?\d*)', line)
            
            if match:
                item_name = match.group(1).strip()
                price_str = match.group(2)
                
                # Skip if this looks like a total line
                if any(keyword in item_name.lower() for keyword in ['total', 'subtotal', 'tax', 'fee', 'delivery']):
                    continue
                
                try:
                    price = float(price_str)
                    
                    # Try to extract quantity
                    quantity = 1
                    qty_match = re.search(r'x\s*(\d+)', line, re.IGNORECASE)
                    if qty_match:
                        quantity = int(qty_match.group(1))
                    
                    # Create cart item
                    cart.add_item(CartItem(
                        ingredient_requested="",  # Unknown at extraction time
                        product_name=item_name,
                        product_url="",
                        price=price,
                        quantity=quantity,
                        status=ItemStatus.ADDED
                    ))
                    
                    logger.debug(f"[{self.platform_name}] Parsed item: {item_name} - ${price} x {quantity}")
                
                except ValueError:
                    logger.warning(f"[{self.platform_name}] Could not parse price from: {line}")
                    continue
        
        # Try to extract total
        total_match = re.search(r'(?:total|subtotal)[:\s]*\$(\d+\.?\d*)', response, re.IGNORECASE)
        if total_match:
            try:
                total = float(total_match.group(1))
                # Override calculated total with extracted total if available
                cart.total = total
                logger.info(f"[{self.platform_name}] Extracted total: ${total:.2f}")
            except ValueError:
                pass
        
        return cart


def main():
    """
    CLI entry point for testing cart detail extraction
    
    Usage:
        python -m agents.cart_detail_agent_nova instacart
    """
    import sys
    import asyncio
    
    if len(sys.argv) < 2:
        print("Usage: python -m agents.cart_detail_agent_nova <platform_name>")
        print("Available platforms: instacart, ubereats, doordash")
        sys.exit(1)
    
    platform_name = sys.argv[1].lower()
    
    if platform_name not in PLATFORM_CONFIGS:
        print(f"Error: Unknown platform '{platform_name}'")
        sys.exit(1)
    
    agent = CartDetailAgentNova(platform_name)
    
    print(f"\nExtracting cart details from {platform_name}...\n")
    
    cart = asyncio.run(agent.extract_cart_details())
    
    print(f"\n{'='*70}")
    print(f"CART DETAILS - {platform_name.upper()}")
    print(f"{'='*70}")
    print(f"Items: {len(cart.items)}")
    print(f"Total: ${cart.total:.2f}")
    print()
    
    for item in cart.items:
        print(f"  - {item.product_name}: ${item.price:.2f} x {item.quantity}")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()

