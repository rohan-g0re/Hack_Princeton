import json
from datetime import date
from typing import Any, Dict, List, Optional
import os


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


def payment_line_only(cart_path: str) -> str:
    """Return only the payment line (if file exists and payment data found)."""
    if not os.path.exists(cart_path):
        return ""
    try:
        with open(cart_path, "r", encoding="utf-8") as f:
            cart_data = json.load(f)
    except Exception:
        return ""

    payment = cart_data.get("payment", {})
    brand = payment.get("brand")
    last_four = payment.get("last_four")
    if not brand:
        return ""
    return (
        f"This order was paid using your {brand} card"
        + (f" ending in {last_four}" if last_four else "")
        + "."
    )
