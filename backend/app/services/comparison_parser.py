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
            for prod in products:
                items.append(ItemSummary(
                    name=prod.get("name", "Unknown"),
                    quantity=prod.get("quantity", 1),
                    unit_price=float(prod.get("price", {}).get("unit_price", "0").replace("$", "")),
                    total_price=float(prod.get("price", {}).get("total", "0").replace("$", ""))
                ))
            
            # Extract price
            price = tx.get("price", {})
            subtotal = float(price.get("sub_total", "0").replace("$", ""))
            total = float(price.get("total", "0").replace("$", ""))
            tax = total - subtotal
            
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

