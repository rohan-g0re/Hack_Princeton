# knot_api/mock_data.py

from datetime import datetime, timedelta
import random
import uuid
from typing import Dict, List

def generate_mock_transactions(merchant_id: int, limit: int = 5) -> Dict:
    """
    Generate mock transaction data
    
    Used when Knot API is unavailable or for demo purposes
    """
    transactions = []
    
    # Sample grocery items
    sample_items_pool = [
        {"name": "Organic Whole Milk", "base_price": 5.99, "sku_prefix": "MILK"},
        {"name": "Large Eggs (Dozen)", "base_price": 4.49, "sku_prefix": "EGGS"},
        {"name": "Fresh Paneer", "base_price": 6.99, "sku_prefix": "PANE"},
        {"name": "Romaine Lettuce", "base_price": 3.99, "sku_prefix": "LETT"},
        {"name": "Cherry Tomatoes", "base_price": 2.99, "sku_prefix": "TOMA"},
        {"name": "Extra Virgin Olive Oil", "base_price": 8.99, "sku_prefix": "OLIV"},
        {"name": "Caesar Dressing", "base_price": 4.49, "sku_prefix": "DRES"},
        {"name": "Parmesan Cheese", "base_price": 7.99, "sku_prefix": "CHES"},
    ]
    
    for i in range(limit):
        # Random number of items per transaction
        num_items = random.randint(2, 6)
        selected_items = random.sample(sample_items_pool, num_items)
        
        items = []
        transaction_total = 0.0
        
        for item_template in selected_items:
            quantity = random.randint(1, 3)
            price = round(item_template["base_price"] * random.uniform(0.9, 1.1), 2)
            
            item = {
                "sku": f"{item_template['sku_prefix']}-{random.randint(100, 999)}",
                "name": item_template["name"],
                "quantity": quantity,
                "price": price
            }
            items.append(item)
            transaction_total += price * quantity
        
        transaction = {
            "id": f"mock_txn_{uuid.uuid4().hex[:8]}",
            "merchant_id": merchant_id,
            "amount": round(transaction_total, 2),
            "date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "status": "completed",
            "items": items
        }
        
        transactions.append(transaction)
    
    return {
        "transactions": transactions,
        "cursor": None,
        "total_count": limit,
        "mock": True  # Indicate this is mock data
    }

