import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional
import os
import uuid
import random


def _money(x: Any) -> float:
    """Parse price fields like '$4.99', '4.99', or float."""
    if x is None:
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).replace("$", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def summarize_cart(
    cart_path: str,
    *,
    merchant_name: Optional[str] = None,
    order_total_override: Optional[float] = None
) -> str:
    """
    Summarize a cart file if it exists.
    If the file is missing, return an empty string instead of printing anything.
    """

    if not os.path.exists(cart_path):
        return ""  # ← quietly skip missing files

    try:
        with open(cart_path, "r", encoding="utf-8") as f:
            cart_data = json.load(f)
    except Exception:
        return ""  # skip corrupted/malformed files silently

    # Infer merchant name from filename if not provided
    if merchant_name is None:
        file_name = os.path.basename(cart_path).lower()
        if "instacart" in file_name:
            merchant_name = "Instacart"
        elif "uber" in file_name:
            merchant_name = "Uber Eats"
        elif "doordash" in file_name:
            merchant_name = "DoorDash"
        else:
            merchant_name = "Your Store"

    items: List[Dict[str, Any]] = cart_data.get("cart_items", [])
    subtotal = _money(cart_data.get("subtotal"))
    if subtotal == 0:
        subtotal = sum(_money(i.get("price")) * int(i.get("quantity", 1)) for i in items)

    total = order_total_override if order_total_override else subtotal
    today = date.today().strftime("%B %d, %Y")

    item_lines = "\n".join([f"- {i['name']}" for i in items]) or "- (No items found)"

    # Optional payment line
    payment = cart_data.get("payment", {})
    brand = payment.get("brand")
    last_four = payment.get("last_four")

    payment_line = ""
    if brand:
        payment_line = f"This order was paid using your {brand} card"
        if last_four:
            payment_line += f" ending in {last_four}"
        payment_line += "."

    summary = (
        f"Your last {merchant_name} order was placed on {today} for a total of ${total:.2f}. "
        f"You ordered:\n\n{item_lines}\n"
    )

    if payment_line:
        summary += "\n" + payment_line

    return summary


def build_knot_like_from_cart(
    cart_path: str,
    *,
    merchant_name: Optional[str] = None,
    rng_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Build a Knot-style JSON object using the template's structure.
    - Preserves input cart details: product names, quantities, unit prices, computed totals, and subtotal.
    - Fills all other fields with random but valid values/classes consistent with the template.
    Returns {} if file missing or unreadable.
    """
    if rng_seed is not None:
        random.seed(rng_seed)

    if not os.path.exists(cart_path):
        return {}

    try:
        with open(cart_path, "r", encoding="utf-8") as f:
            cart_data = json.load(f)
    except Exception:
        return {}

    # Infer merchant name from filename if not provided
    if merchant_name is None:
        file_name = os.path.basename(cart_path).lower()
        if "instacart" in file_name:
            merchant_name = "Instacart"
        elif "uber" in file_name:
            merchant_name = "Uber Eats"
        elif "doordash" in file_name:
            merchant_name = "DoorDash"
        else:
            merchant_name = "Your Store"

    items: List[Dict[str, Any]] = cart_data.get("cart_items", [])
    subtotal = _money(cart_data.get("subtotal"))
    if subtotal == 0:
        subtotal = sum(_money(i.get("price")) * int(i.get("quantity", 1)) for i in items)

    # Randomized fields consistent with template classes
    order_status_options = ["ORDERED", "COMPLETED", "CANCELLED", "PICKED_UP", "BILLED"]
    payment_type_options = ["CARD", "PAYPAL", "EBTSNAP"]
    card_brand_options = ["VISA", "MASTERCARD", "AMEX", "DISCOVER"]

    # Random tax and totals
    tax_rate = random.choice([0.0, 0.05, 0.065, 0.0725, 0.08])
    tax_amt = round(subtotal * tax_rate, 2)
    adjustments: List[Dict[str, Any]] = []
    if tax_amt > 0:
        adjustments.append({
            "type": "TAX",
            "label": "Sales Tax",
            "amount": f"{tax_amt:.2f}"
        })
    total = round(subtotal + tax_amt, 2)

    # Build products preserving details
    products: List[Dict[str, Any]] = []
    for idx, i in enumerate(items, start=1):
        qty = int(i.get("quantity", 1))
        unit_price = _money(i.get("price"))
        prod_total = round(unit_price * qty, 2)
        products.append({
            "external_id": str(1200000 + idx),
            "name": i.get("name", f"Item {idx}"),
            "url": "",
            "quantity": qty,
            "price": {
                "sub_total": f"{prod_total:.2f}",
                "total": f"{prod_total:.2f}",
                "unit_price": f"{unit_price:.2f}"
            },
            "eligibility": []
        })

    # Payment methods (randomized)
    payment_methods: List[Dict[str, Any]] = []
    chosen_type = random.choice(payment_type_options)
    if chosen_type == "CARD":
        brand = random.choice(card_brand_options)
        last_four = f"{random.randint(0, 9999):04d}"
        payment_methods.append({
            "external_id": str(uuid.uuid4()),
            "type": "CARD",
            "brand": brand,
            "last_four": last_four,
            "transaction_amount": f"{total:.2f}"
        })
    elif chosen_type == "PAYPAL":
        payment_methods.append({
            "external_id": str(uuid.uuid4()),
            "type": "PAYPAL",
            "transaction_amount": f"{total:.2f}"
        })
    else:  # EBTSNAP
        last_four = f"{random.randint(0, 9999):04d}"
        payment_methods.append({
            "external_id": str(uuid.uuid4()),
            "type": "EBTSNAP",
            "last_four": last_four,
            "transaction_amount": f"{total:.2f}"
        })

    # Prefer input payment details if present (preserve)
    payment = cart_data.get("payment", {})
    if payment.get("brand"):
        if payment_methods:
            pm0 = payment_methods[0]
            pm0["type"] = "CARD"
            pm0["brand"] = str(payment.get("brand")).upper()
            if payment.get("last_four"):
                pm0["last_four"] = str(payment["last_four"])
            pm0["transaction_amount"] = f"{total:.2f}"

    # Transaction ID/URL
    tx_id = str(uuid.uuid4())
    if merchant_name == "Instacart":
        order_url = f"https://www.instacart.com/store/orders/{tx_id}"
    elif merchant_name == "Uber Eats":
        order_url = f"https://www.ubereats.com/order/{tx_id}"
    elif merchant_name == "DoorDash":
        order_url = f"https://www.doordash.com/order/{tx_id}"
    else:
        order_url = ""

    result: Dict[str, Any] = {
        "merchant": {
            "id": random.randint(1, 9999),
            "name": merchant_name
        },
        "transactions": [
            {
                "id": tx_id,
                "external_id": tx_id,
                "datetime": datetime.utcnow().isoformat(),
                "url": order_url,
                "order_status": random.choice(order_status_options),
                "payment_methods": payment_methods,
                "price": {
                    "sub_total": f"{subtotal:.2f}",
                    "adjustments": adjustments,
                    "total": f"{total:.2f}",
                    "currency": "USD"
                },
                "products": products
            }
        ],
        "next_cursor": "",
        "limit": 1
    }

    return result