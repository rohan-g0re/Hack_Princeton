import json
from pathlib import Path
from typing import List
from app.config import settings
from app.models.comparison import PlatformSummary, ItemSummary


def parse_knot_api_jsons() -> List[PlatformSummary]:
    """
    Parse all knot_api_jsons/*.json files and return platform summaries.
    Each file represents one platform's order.
    """
    knot_dir = settings.knot_api_jsons_dir
    if not knot_dir.exists():
        return []
    
    platforms = []
    
    for json_file in knot_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Extract merchant name
            merchant_name = data.get("merchant", {}).get("name", "Unknown")
            logo_map = {
                "Instacart": "instacart",
                "Uber Eats": "ubereats",
                "DoorDash": "doordash"
            }
            logo = logo_map.get(merchant_name, "store")
            
            # Extract transaction (assume first transaction)
            transactions = data.get("transactions", [])
            if not transactions:
                continue
            
            tx = transactions[0]
            
            # Extract items
            products = tx.get("products", [])
            items = []
            subtotal_calculated = 0.0
            
            for prod in products:
                price_data = prod.get("price", {})
                unit_price_str = str(price_data.get("unit_price", "0")).replace("$", "").strip()
                total_price_str = str(price_data.get("total", "0")).replace("$", "").strip()
                
                unit_price = float(unit_price_str) if unit_price_str else 0.0
                total_price = float(total_price_str) if total_price_str else 0.0
                
                items.append(ItemSummary(
                    name=prod.get("name", "Unknown"),
                    quantity=prod.get("quantity", 1),
                    unit_price=unit_price,
                    total_price=total_price
                ))
                subtotal_calculated += total_price
            
            # Extract tax from transaction price
            price = tx.get("price", {})
            adjustments = price.get("adjustments", [])
            tax = 0.0
            for adj in adjustments:
                if adj.get("type") == "TAX":
                    tax_str = str(adj.get("amount", "0")).replace("$", "").strip()
                    tax += float(tax_str) if tax_str else 0.0
            
            # Calculate total (sum of items + tax)
            subtotal = subtotal_calculated
            total = subtotal + tax
            
            # Date
            date_str = tx.get("datetime", "")[:10]  # ISO date
            
            platforms.append(PlatformSummary(
                name=merchant_name,
                logo=logo,
                items=items,
                subtotal=subtotal,
                tax=tax,
                total=total,
                date=date_str,
                best_deal=False
            ))
        
        except Exception as e:
            print(f"[WARN] Error parsing {json_file.name}: {e}")
            continue
    
    # Mark best deal (lowest total)
    if platforms:
        best = min(platforms, key=lambda p: p.total)
        best.best_deal = True
    
    return platforms

