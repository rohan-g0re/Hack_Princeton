"""
Knot JSON Importer
Scans current_code/knot_api_jsons/ and imports orders into Supabase
"""
import os
import json
from typing import List, Dict, Any
from decimal import Decimal
from app.services.supabase_service import supabase_service
from app.config import settings


def parse_knot_json(knot_data: Dict) -> Dict:
    """
    Extract order summary and items from Knot API JSON format.
    
    Returns dict with:
        - store_name
        - subtotal, tax, total, currency
        - platform_subtotals (dict)
        - items (list of dicts)
    """
    merchant_name = knot_data.get("merchant", {}).get("name", "Unknown")
    
    # Aggregate across all transactions
    all_products = []
    platform_subtotals = {}
    total_subtotal = Decimal("0")
    total_tax = Decimal("0")
    total_total = Decimal("0")
    
    for tx in knot_data.get("transactions", []):
        price = tx.get("price", {})
        tx_subtotal = Decimal(str(price.get("sub_total", "0")))
        tx_total = Decimal(str(price.get("total", "0")))
        
        # Calculate tax from adjustments
        tx_tax = Decimal("0")
        for adj in price.get("adjustments", []):
            if adj.get("type") == "TAX":
                tx_tax += Decimal(str(adj.get("amount", "0")))
        
        total_subtotal += tx_subtotal
        total_tax += tx_tax
        total_total += tx_total
        
        platform_subtotals[merchant_name] = float(
            platform_subtotals.get(merchant_name, Decimal("0")) + tx_subtotal
        )
        
        # Extract products
        for product in tx.get("products", []):
            price_info = product.get("price", {})
            all_products.append({
                "platform": merchant_name,
                "item_name": product.get("name"),
                "external_id": product.get("external_id"),
                "quantity": product.get("quantity", 1),
                "unit": None,  # Not in Knot template
                "unit_price": float(Decimal(str(price_info.get("unit_price", "0")))),
                "subtotal": float(Decimal(str(price_info.get("sub_total", "0")))),
                "total": float(Decimal(str(price_info.get("total", "0")))),
                "eligibility": product.get("eligibility", [])
            })
    
    return {
        "store_name": merchant_name,
        "subtotal": float(total_subtotal),
        "tax": float(total_tax),
        "total": float(total_total),
        "currency": knot_data.get("transactions", [{}])[0].get("price", {}).get("currency", "USD"),
        "platform_subtotals": platform_subtotals,
        "items": all_products
    }


def import_knot_jsons(user_id: str, directory: str = None) -> List[str]:
    """
    Import all Knot JSONs from directory into Supabase.
    Returns list of created order IDs.
    
    Args:
        user_id: User who owns the orders
        directory: Path to JSON directory (defaults to settings.knot_api_jsons_dir)
    
    Returns:
        List of order IDs (UUIDs)
    
    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    if directory is None:
        directory = str(settings.knot_api_jsons_dir)
    
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    created_order_ids = []
    
    for filename in os.listdir(directory):
        if not filename.endswith(".json"):
            continue
        
        filepath = os.path.join(directory, filename)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                knot_data = json.load(f)
            
            # Parse order summary
            order_summary = parse_knot_json(knot_data)
            items = order_summary.pop("items")
            
            # Create order (idempotent via payload_hash)
            order_id = supabase_service.create_order(user_id, order_summary, knot_data)
            
            # Insert items
            if items:
                supabase_service.bulk_insert_order_items(order_id, items)
            
            created_order_ids.append(order_id)
        
        except Exception as e:
            print(f"Error importing {filename}: {e}")
            continue
    
    return created_order_ids

