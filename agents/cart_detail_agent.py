# agents/cart_detail_agent.py

from agents.base_agent import AgentUtils
from config.platforms import PLATFORM_CONFIGS
from models.cart_models import CartItem, PlatformCart, ItemStatus
from utils.popup_handler import dismiss_popups
from utils.retry_decorator import async_retry
import logging
from typing import List

logger = logging.getLogger(__name__)

class CartDetailAgent:
    """
    Extract detailed cart information from platform
    
    Reads actual cart state from the platform's cart page.
    More reliable than trying to track state from agent actions.
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
        
        if not await AgentUtils.check_session_valid(self.page, self.platform_name):
            raise ValueError(f"Not logged in to {self.platform_name}")
    
    async def cleanup(self):
        """Cleanup browser resources"""
        if self.playwright and self.context:
            await AgentUtils.cleanup_browser(self.playwright, self.context)
    
    @async_retry(max_attempts=3)
    async def extract_cart_details(self) -> PlatformCart:
        """
        Extract complete cart details from platform
        
        Returns:
            PlatformCart with all items and totals
        """
        logger.info(f"[{self.platform_name}] Extracting cart details")
        
        await self.initialize()
        
        try:
            # Navigate to cart
            await self.page.goto(self.config["cart_url"], wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)  # Let cart load
            await dismiss_popups(self.page)
            
            # Extract items
            items = await self._extract_cart_items()
            
            # Extract totals
            subtotal, delivery_fee, service_fee, tax, total = await self._extract_totals()
            
            cart = PlatformCart(
                platform_name=self.platform_name,
                platform_id=self.config["merchant_id"],
                items=items,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                service_fee=service_fee,
                tax=tax,
                total=total
            )
            
            logger.info(f"[{self.platform_name}] Extracted {len(items)} items, total: ${total}")
            
            return cart
            
        finally:
            await self.cleanup()
    
    async def _extract_cart_items(self) -> List[CartItem]:
        """
        Extract all items from cart page
        
        Platform-specific selectors may need adjustment
        """
        items = []
        
        try:
            # Generic cart item selectors (adjust per platform)
            cart_item_selectors = [
                "[data-testid*='cart-item']",
                "[class*='CartItem']",
                "[class*='cart-item']",
                ".cart-item"
            ]
            
            cart_items_elements = []
            for selector in cart_item_selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    cart_items_elements = elements
                    break
            
            if not cart_items_elements:
                logger.warning("No cart items found")
                return items
            
            for elem in cart_items_elements:
                try:
                    # Extract name
                    name_selectors = ["[class*='name']", "[class*='title']", "h3", "h4", "[data-testid*='name']"]
                    name = "Unknown Product"
                    for sel in name_selectors:
                        name_elem = await elem.query_selector(sel)
                        if name_elem:
                            name = (await name_elem.inner_text()).strip()
                            break
                    
                    # Extract price
                    price_selectors = ["[class*='price']", "[data-testid*='price']", "[class*='cost']"]
                    price = 0.0
                    for sel in price_selectors:
                        price_elem = await elem.query_selector(sel)
                        if price_elem:
                            price_text = await price_elem.inner_text()
                            # Remove $ and commas, convert to float
                            price_text = price_text.replace("$", "").replace(",", "").strip()
                            try:
                                price = float(price_text)
                                break
                            except ValueError:
                                continue
                    
                    # Extract quantity
                    qty_selectors = ["[class*='quantity']", "input[type='number']", "select"]
                    quantity = 1
                    for sel in qty_selectors:
                        qty_elem = await elem.query_selector(sel)
                        if qty_elem:
                            qty_text = await qty_elem.get_attribute("value") or await qty_elem.inner_text()
                            try:
                                quantity = int(qty_text)
                                break
                            except ValueError:
                                continue
                    
                    # Create CartItem
                    item = CartItem(
                        ingredient_requested=name,  # We don't know original request here
                        product_name=name,
                        product_url=self.page.url,
                        price=price,
                        quantity=quantity,
                        status=ItemStatus.ADDED
                    )
                    
                    items.append(item)
                    
                except Exception as e:
                    logger.warning(f"Failed to extract cart item: {e}")
                    continue
            
            return items
            
        except Exception as e:
            logger.error(f"Failed to extract cart items: {e}")
            return items
    
    async def _extract_totals(self):
        """
        Extract subtotal, fees, tax, and total
        
        Returns:
            Tuple of (subtotal, delivery_fee, service_fee, tax, total)
        """
        try:
            # Generic total selectors
            total_selectors = [
                "[data-testid*='total']",
                "[class*='total']",
                "[class*='Total']"
            ]
            
            subtotal = 0.0
            delivery_fee = 0.0
            service_fee = 0.0
            tax = 0.0
            total = 0.0
            
            # Try to find total
            for selector in total_selectors:
                total_elem = await self.page.query_selector(selector)
                if total_elem:
                    total_text = await total_elem.inner_text()
                    total_text = total_text.replace("$", "").replace(",", "").strip()
                    try:
                        total = float(total_text)
                        break
                    except ValueError:
                        continue
            
            # If we found total, use it. Otherwise, calculate from items.
            # For MVP, we can estimate fees as 0 if not extractable
            
            return (subtotal, delivery_fee, service_fee, tax, total)
            
        except Exception as e:
            logger.error(f"Failed to extract totals: {e}")
            return (0.0, 0.0, 0.0, 0.0, 0.0)

