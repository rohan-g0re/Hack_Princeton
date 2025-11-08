import json
import re
from nova_act import NovaAct
import os

# Browser args enables browser debugging on port 9222.
os.environ["NOVA_ACT_BROWSER_ARGS"] = "--remote-debugging-port=9222"

def load_shopping_list(path="shopping_list.json"):
    with open(path, "r") as f:
        return json.load(f)["shopping_list"]

# remove descriptors that don't help store search
DESCRIPTORS = {
    "medium", "large", "small", "melted", "ripe", "unsalted"
}

def normalize_item_name(name: str) -> str:
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

    # some slight tweaks: “Medium ripe bananas” → “bananas”
    cleaned = re.sub(r"\brip[e]?\b", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned

def is_count_quantity(q):
    # countable if a plain int/float, or a numeric string with no unit words
    if isinstance(q, (int, float)):
        return True
    if isinstance(q, str):
        # if string has any letters, assume it's unit-based (cups, tbsp, tsp, etc.)
        if re.search(r"[A-Za-z]", q):
            return False
        # numeric-only string -> treat as count
        return bool(re.fullmatch(r"\d+(\.\d+)?", q.strip()))
    return False

shopping_list = load_shopping_list()

# Base instruction (kept your Whole Foods flow)
instruction = (
    "If a sign-up popup appears, close it. "
    "If a CAPTCHA appears, complete the verification. "
    "If a any popup appears, close it. "
    # "Enter the delivery address '89 Northampton St, Boston MA'. "
    # "If a any popup appears, close it. "
    "Search for 'Stop & shop' and click on the store. "
    "If a any popup appears, close it. "

)

for entry in shopping_list:
    raw_item = entry.get("item", "").strip()
    qty = entry.get("quantity", 1)
    item = normalize_item_name(raw_item)

    if is_count_quantity(qty):
        # Countable: add exactly that many (e.g., 2 bananas)
        qty_int = int(float(qty))  # robust cast for "2" or 2.0
        instruction += (
            f"Search for '{item}' and add {qty_int} to cart. "
        )
    else:
        # Unit-based or descriptive: get the smallest-size pack/container available
        # (don’t try to match cups/tbsp precisely)
        instruction += (
            f"Search for '{item}'. "
            f"In product list, prefer the smallest-size pack/container available. "
            f"Add 1 to cart. "
        )

instruction += "Return the total items in cart."

# Use it:
nova = NovaAct(starting_page="https://www.instacart.com")

nova.start()
nova.act(instruction)
