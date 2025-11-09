# agents/search_order_agent_nova.py
"""
Amazon Nova Auto implementation for search and order
Uses NovaAct with natural language instructions and persistent sessions
"""

from nova_act import NovaAct
from config.platforms import PLATFORM_CONFIGS
from models.cart_models import CartItem, PlatformCart, ItemStatus
import logging
import os
from dotenv import load_dotenv
from typing import List
import re

logger = logging.getLogger(__name__)
load_dotenv()

# Configure Nova Act API key (load from .env instead of requiring export)
nova_key = os.getenv("NOVA_ACT_API_KEY")
if not nova_key:
    raise ValueError("NOVA_ACT_API_KEY environment variable not set")
os.environ["NOVA_ACT_API_KEY"] = nova_key

# Browser debugging port
os.environ["NOVA_ACT_BROWSER_ARGS"] = "--remote-debugging-port=9222"

class SearchOrderAgentNova:
    """
    Search for ingredients and add them to cart using Amazon Nova Auto
    
    Uses natural language instructions - much simpler than DOM selectors!
    Based on proven instacart_nova_auto.py and uber_nova_auto.py patterns
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.config = PLATFORM_CONFIGS[platform_name]
        self.nova = None
    
    def _get_platform_url(self):
        """
        Get the base URL for this platform
        EXACTLY as used in working reference implementations
        """
        # FROM instacart_nova_auto.py line 328 and uber_nova_auto.py line 329
        if "instacart" in self.platform_name:
            return "https://www.instacart.com"  # PROVEN TO WORK
        elif "ubereats" in self.platform_name:
            return "https://www.ubereats.com"  # PROVEN TO WORK
        else:
            raise ValueError(f"Unsupported platform: {self.platform_name}. Only 'instacart' and 'ubereats' are supported.")
    
    def _normalize_item_name(self, name: str) -> str:
        """
        Clean up item name for better search results
        EXACTLY FROM reference implementations lines 158-179 (PROVEN TO WORK)
        """
        DESCRIPTORS = {"medium", "large", "small", "melted", "ripe", "unsalted"}
        
        # if there are alternatives like "unsalted butter or vegetable oil" → pick the first option
        if " or " in name.lower():
            name = re.split(r"\s+or\s+", name, flags=re.IGNORECASE)[0]
        
        # drop common descriptors at word boundaries
        words = []
        for w in re.split(r"\s+", name.strip()):
            w_clean = re.sub(r"[^\w\-]", "", w).lower()
            if w_clean not in DESCRIPTORS:
                words.append(w)
        cleaned = " ".join(words).strip()
        
        # some slight tweaks: "Medium ripe bananas" → "bananas"
        cleaned = re.sub(r"\brip[e]?\b", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return cleaned
    
    
    def _build_instruction_for_items(self, items: List[str], is_first_batch=True) -> str:
        """
        Build natural language instruction for Nova Auto - platform-specific logic
        Based on proven working patterns from instacart_nova_auto.py and uber_nova_auto.py
        """
        instruction = ""
        
        if is_first_batch:
            # Platform-specific initialization (EXACTLY as in working reference files)
            if "instacart" in self.platform_name:
                # FROM instacart_nova_auto.py lines 253-259 (PROVEN TO WORK)
                instruction += (
                    "If a sign-up popup appears, close it. "
                    "If a CAPTCHA appears, complete the verification. "
                    "If any popup appears, close it. "
                    "Search for 'Stop & shop' and click on the store. "
                    "If any popup appears, close it. "
                )
            
            elif "ubereats" in self.platform_name:
                # FROM uber_nova_auto.py lines 253-260 (PROVEN TO WORK)
                instruction += (
                    "If a sign-up popup appears, close it. "
                    "Put addess to deliver as 89 Northampton St, Boston, MA 02118. "
                    "If a CAPTCHA appears, complete the verification. "
                    "If any popup appears, close it. "
                    "Search for '{Target_Element_To_be_bought}' and click on the store. "
                    "If any popup appears, close it. "
                )
            
            else:
                # Unsupported platform (DoorDash removed)
                raise ValueError(f"Unsupported platform: {self.platform_name}. Only 'instacart' and 'ubereats' are supported.")
        
        else:
            # Subsequent batches - FROM reference implementations lines 262-266
            instruction += (
                "If any popup appears, close it. "
                "Go to the store page if not already there. "
            )
        
        # Add each item - simple mode: just add 1 of each
        # FROM reference implementations lines 268-300
        for item in items:
            normalized_item = self._normalize_item_name(item)
            # Using simplified approach (countable items only for now)
            instruction += f"Search for '{normalized_item}' and add 1 to cart. "
        
        instruction += "Return the total items in cart."
        return instruction
    
    def start_session(self):
        """Start a persistent Nova Act session (call once before operations)"""
        if self.nova is None:
            logger.info(f"[{self.platform_name}] Starting persistent Nova Act session...")
            
            # Convert relative path to absolute path for Windows compatibility
            user_data_path = os.path.abspath(self.config["user_data_dir"])
            
            # Create directory if it doesn't exist
            os.makedirs(user_data_path, exist_ok=True)
            logger.info(f"[{self.platform_name}] User data directory: {user_data_path}")
            
            self.nova = NovaAct(
                starting_page=self._get_platform_url(),
                user_data_dir=user_data_path
            )
            self.nova.start()
            logger.info(f"[{self.platform_name}] Session started successfully")
    
    def stop_session(self):
        """Stop the persistent Nova Act session (call once when done)"""
        if self.nova:
            logger.info(f"[{self.platform_name}] Stopping persistent Nova Act session...")
            self.nova.stop()
            self.nova = None
            logger.info(f"[{self.platform_name}] Session stopped")
    
    async def search_and_add_all(self, ingredients: List[str]) -> PlatformCart:
        """
        Public async API expected by orchestrators.
        Runs the synchronous NovaAct flow in a background thread to avoid
        'Playwright Sync API inside the asyncio loop' errors.
        """
        import asyncio
        return await asyncio.to_thread(self._search_and_add_all_sync, ingredients)

    # --------- Internal synchronous implementation (safe for NovaAct) ---------
    def _search_and_add_all_sync(self, ingredients: List[str]) -> PlatformCart:
        """
        Synchronous implementation of the NovaAct batching flow with persistent session.
        This must NOT run inside the main asyncio event loop thread.
        """
        cart = PlatformCart(
            platform_name=self.platform_name,
            platform_id=self.config["merchant_id"]
        )

        ITEMS_PER_BATCH = 7  # FROM reference implementations line 306 (PROVEN TO WORK)
        total_items = len(ingredients)
        num_batches = (total_items + ITEMS_PER_BATCH - 1) // ITEMS_PER_BATCH

        logger.info(f"[{self.platform_name}] Processing {total_items} items in {num_batches} batches")

        # Start persistent session (only once)
        self.start_session()

        try:
            for batch_idx in range(num_batches):
                start_idx = batch_idx * ITEMS_PER_BATCH
                end_idx = min(start_idx + ITEMS_PER_BATCH, total_items)
                batch_items = ingredients[start_idx:end_idx]

                logger.info(f"[{self.platform_name}] Batch {batch_idx + 1}/{num_batches}: items {start_idx + 1}-{end_idx}")

                # Build instruction
                is_first = (batch_idx == 0)
                instruction = self._build_instruction_for_items(batch_items, is_first_batch=is_first)

                try:
                    # Use the persistent session (no need to start/stop each time)
                    result = self.nova.act(instruction, max_steps=99)
                    logger.info(f"[{self.platform_name}] Batch {batch_idx + 1} completed: {result}")

                    # Add items to cart (mark as ADDED)
                    for item in batch_items:
                        cart.add_item(CartItem(
                            ingredient_requested=item,
                            product_name=f"{item} (added via Nova)",
                            product_url="",
                            price=0.0,
                            status=ItemStatus.ADDED
                        ))

                except Exception as e:
                    logger.error(f"[{self.platform_name}] Batch {batch_idx + 1} error: {e}")
                    for item in batch_items:
                        cart.add_item(CartItem(
                            ingredient_requested=item,
                            product_name="Failed",
                            product_url="",
                            price=0.0,
                            status=ItemStatus.FAILED
                        ))

            logger.info(f"[{self.platform_name}] All batches completed!")
        
        finally:
            # Stop session when all batches are done (or on error)
            self.stop_session()

        return cart

