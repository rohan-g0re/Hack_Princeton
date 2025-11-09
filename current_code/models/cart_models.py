# models/cart_models.py

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
import json

class ItemStatus(Enum):
    """Status of an item in cart"""
    ADDED = "added"
    NOT_FOUND = "not_found"
    FAILED = "failed"
    OUT_OF_STOCK = "out_of_stock"

@dataclass
class CartItem:
    """
    Single item in a platform's cart
    
    Attributes:
        ingredient_requested: What user originally asked for (e.g., "milk")
        product_name: Actual product added (e.g., "Organic Whole Milk 1 Gallon")
        product_url: Direct link to product page
        price: Item price in USD
        quantity: Number of units
        image_url: Product image URL (optional)
        sku: Product SKU for Knot API integration (optional)
        status: Current status of this item
        timestamp: When this item was added
    """
    ingredient_requested: str
    product_name: str
    product_url: str
    price: float
    quantity: int = 1
    image_url: Optional[str] = None
    sku: Optional[str] = None
    status: ItemStatus = ItemStatus.ADDED
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        data = asdict(self)
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict):
        """Reconstruct from dict"""
        data['status'] = ItemStatus(data['status'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class PlatformCart:
    """
    Complete cart state for one delivery platform
    
    Attributes:
        platform_name: Platform identifier (e.g., "instacart")
        platform_id: Knot API merchant_id for this platform
        items: List of CartItem objects
        subtotal: Sum of item prices
        delivery_fee: Platform delivery fee
        service_fee: Platform service fee
        tax: Estimated tax
        total: Final total amount
        timestamp: Last update time
        session_valid: Whether login session is still active
    """
    platform_name: str
    platform_id: int
    items: List[CartItem] = field(default_factory=list)
    subtotal: float = 0.0
    delivery_fee: float = 0.0
    service_fee: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    session_valid: bool = True
    
    def calculate_totals(self):
        """Recalculate subtotal and total from items"""
        self.subtotal = sum(item.price * item.quantity for item in self.items if item.status == ItemStatus.ADDED)
        self.total = self.subtotal + self.delivery_fee + self.service_fee + self.tax
    
    def add_item(self, item: CartItem):
        """Add item and recalculate totals"""
        self.items.append(item)
        self.calculate_totals()
    
    def remove_item(self, ingredient_requested: str):
        """Remove item by ingredient name"""
        self.items = [item for item in self.items if item.ingredient_requested != ingredient_requested]
        self.calculate_totals()
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            "platform_name": self.platform_name,
            "platform_id": self.platform_id,
            "items": [item.to_dict() for item in self.items],
            "subtotal": self.subtotal,
            "delivery_fee": self.delivery_fee,
            "service_fee": self.service_fee,
            "tax": self.tax,
            "total": self.total,
            "timestamp": self.timestamp.isoformat(),
            "session_valid": self.session_valid
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Reconstruct from dict"""
        data['items'] = [CartItem.from_dict(item) for item in data['items']]
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class CartDiff:
    """
    Record of user edit to a platform cart
    
    Used to track changes made in the UI that need to be
    applied to actual platform carts before checkout.
    
    Attributes:
        platform: Platform name this diff applies to
        action: Type of change ("add", "remove", "update_quantity")
        item: The CartItem being modified
        timestamp: When this change was made
        applied: Whether this diff has been applied to actual cart
    """
    platform: str
    action: str  # "add", "remove", "update_quantity"
    item: CartItem
    timestamp: datetime = field(default_factory=datetime.now)
    applied: bool = False
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            "platform": self.platform,
            "action": self.action,
            "item": self.item.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "applied": self.applied
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Reconstruct from dict"""
        data['item'] = CartItem.from_dict(data['item'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class CartState:
    """
    Global cart state manager
    
    Manages all platform carts and tracks diffs for user edits.
    Provides persistence to JSON file.
    
    Usage:
        state = CartState()
        state.add_platform_cart(instacart_cart)
        state.record_diff("instacart", "remove", milk_item)
        state.save_to_file()
    """
    def __init__(self):
        self.platform_carts: Dict[str, PlatformCart] = {}
        self.diffs: List[CartDiff] = []
        self.ingredients_requested: List[str] = []
    
    def add_platform_cart(self, cart: PlatformCart):
        """Add or update a platform cart"""
        self.platform_carts[cart.platform_name] = cart
    
    def get_cart(self, platform_name: str) -> Optional[PlatformCart]:
        """Get cart for specific platform"""
        return self.platform_carts.get(platform_name)
    
    def record_diff(self, platform: str, action: str, item: CartItem):
        """Record user edit as a diff"""
        diff = CartDiff(platform=platform, action=action, item=item)
        self.diffs.append(diff)
    
    def get_pending_diffs(self, platform: str) -> List[CartDiff]:
        """Get unapplied diffs for a platform"""
        return [d for d in self.diffs if d.platform == platform and not d.applied]
    
    def mark_diffs_applied(self, platform: str):
        """Mark all diffs for platform as applied"""
        for diff in self.diffs:
            if diff.platform == platform:
                diff.applied = True
    
    def get_total_across_platforms(self) -> float:
        """Calculate total cost across all platforms"""
        return sum(cart.total for cart in self.platform_carts.values())
    
    def save_to_file(self, filepath: str = "data/cart_state.json"):
        """Persist entire state to JSON file"""
        data = {
            "platform_carts": {
                name: cart.to_dict() 
                for name, cart in self.platform_carts.items()
            },
            "diffs": [diff.to_dict() for diff in self.diffs],
            "ingredients_requested": self.ingredients_requested,
            "saved_at": datetime.now().isoformat()
        }
        
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str = "data/cart_state.json"):
        """Load state from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        state = cls()
        state.ingredients_requested = data.get('ingredients_requested', [])
        
        # Reconstruct platform carts
        for name, cart_data in data.get('platform_carts', {}).items():
            state.platform_carts[name] = PlatformCart.from_dict(cart_data)
        
        # Reconstruct diffs
        for diff_data in data.get('diffs', []):
            state.diffs.append(CartDiff.from_dict(diff_data))
        
        return state

