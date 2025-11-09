import json
import re
from nova_act import NovaAct
import os
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
# load_dotenv()

# Browser args enables browser debugging on port 9222.
os.environ["NOVA_ACT_BROWSER_ARGS"] = "--remote-debugging-port=9222"

# # Configure Gemini
# api_key = os.getenv("GEMINI_API_KEY")
# if not api_key:
#     raise ValueError("GEMINI_API_KEY not found in .env file. Get your key from: https://aistudio.google.com/app/apikey")

# genai.configure(api_key=api_key)
# model = genai.GenerativeModel('gemini-2.0-flash-exp')

load_dotenv()
GROK_API_KEY = os.getenv("GROK_API_KEY")
if not GROK_API_KEY:
    raise ValueError("GROK_API_KEY not found in .env file. Please get your key from xAI API console.")

# Base endpoint (example — check docs for current URL)
GROK_API_URL = "https://api.x.ai/v1/chat/completions"


def call_grok(prompt: str, model: str="grok-4-fast-reasoning", max_tokens: int=512, temperature: float=0.0):
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise cooking measurement converter."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    resp = requests.post(GROK_API_URL, headers=headers, json=body)
    resp.raise_for_status()
    data = resp.json()
    # The structure of response depends on version; assume something like:
    return data["choices"][0]["message"]["content"]


def estimate_weight_with_grok(item_name: str, quantity: str) -> dict:
    prompt = f"""
Convert the following ingredient quantity to grams.
Ingredient: {item_name}
Quantity: {quantity}
Provide ONLY a JSON response in this exact format:
{{
    "weight_grams": <number_or_null>,
    "unit": "g",
    "confidence": "high/medium/low"
}}
Make your best estimate.

Rules:
- Be as accurate as possible using standard cooking conversions
- For liquids, use density (water = 1g/ml, oil = 0.92g/ml, milk = 1.03g/ml, etc.)
- For dry ingredients, use standard conversions (1 cup flour = 120g, 1 tbsp sugar = 12.5g, etc.)
- Round to nearest gram
- If you cannot determine, set weight_grams to null

Example conversions:
- 2 tbsp sugar → 25g
- 1 cup flour → 120g
- 1/2 cup milk → 120g
- 1 tsp salt → 6g
"""
    try:
        response_text = call_grok(prompt)
        # Clean up markdown/codeblock if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)
        if result.get("weight_grams") and result["weight_grams"] > 0:
            print(f"  ✓ Estimated {quantity} {item_name} = {result['weight_grams']}g (confidence: {result.get('confidence','unknown')})")
            return result
        else:
            print(f"  ⚠ Could not estimate weight for {quantity} {item_name}")
            return None
    except Exception as e:
        print(f"  ✗ Error estimating weight for {item_name}: {e}")
        return None

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

    # some slight tweaks: "Medium ripe bananas" → "bananas"
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

def estimate_weight_with_gemini(item_name: str, quantity: str) -> dict:
    """
    Use Gemini to estimate the weight needed for a given quantity.
    Returns dict with 'weight_grams' and 'unit' or None if can't estimate.
    """
    prompt = f"""
You are a precise cooking measurement converter. Convert the following ingredient quantity to grams.

Ingredient: {item_name}
Quantity: {quantity}

Provide ONLY a JSON response in this exact format:
{{
    "weight_grams": <number>,
    "unit": "g",
    "confidence": "high/medium/low"
}}

Rules:
- Be as accurate as possible using standard cooking conversions
- For liquids, use density (water = 1g/ml, oil = 0.92g/ml, milk = 1.03g/ml, etc.)
- For dry ingredients, use standard conversions (1 cup flour = 120g, 1 tbsp sugar = 12.5g, etc.)
- Round to nearest gram
- If you cannot determine, set weight_grams to null

Example conversions:
- 2 tbsp sugar → 25g
- 1 cup flour → 120g
- 1/2 cup milk → 120g
- 1 tsp salt → 6g
"""
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        
        if result.get("weight_grams") and result["weight_grams"] > 0:
            print(f"  ✓ Estimated {quantity} {item_name} = {result['weight_grams']}g (confidence: {result.get('confidence', 'unknown')})")
            return result
        else:
            print(f"  ⚠ Could not estimate weight for {quantity} {item_name}")
            return None
            
    except Exception as e:
        print(f"  ✗ Error estimating weight for {item_name}: {e}")
        return None

shopping_list = load_shopping_list()

# Base instruction
instruction = (
    "If a sign-up popup appears, close it. "
    "add addess to deliver as 89 Northampton St, Boston, MA 02118. "
    "If a CAPTCHA appears, complete the verification. "
    "If any popup appears, close it. "
    "Search for 'Target' and click on the store. "
    "If any popup appears, close it. "
)

for entry in shopping_list:
    raw_item = entry.get("item", "").strip()
    qty = entry.get("quantity", 1)
    item = normalize_item_name(raw_item)

    if is_count_quantity(qty):
        # Countable: add exactly that many (e.g., 2 bananas)
        qty_int = int(float(qty))
        instruction += (
            f"Search for '{item}' and add {qty_int} to cart. "
        )
    else:
        # Unit-based measurements - use Gemini to estimate weight
        print(f"Converting measurement for: {item} - {qty}")
        weight_info = estimate_weight_with_grok(item, qty)
        
        if weight_info and weight_info.get("weight_grams"):
            target_weight = weight_info["weight_grams"]
            # Convert grams to ounces for easier comparison (1 oz = 28.35g)
            target_oz = round(target_weight / 28.35, 1)
            
            # SIMPLIFIED INSTRUCTION
            instruction += (
                f"Search for '{item}'. "
                f"look for item in the list"
                # f"You need approximately {target_weight}g (about {target_oz} oz). "
                # f"Find the package that contains at least this amount. "
                f"Add ONLY 1 package to cart. "
                f"Do not add multiple packages. "

                # f"Search for '{item}'. "
                # f"Look for {item} and available package sizes in grams or ounces. "
                # f"Target weight needed: {target_weight}g (about {target_oz} oz). "
                # f"If packages are smaller than {target_weight}g, calculate how many packages are needed to meet or exceed {target_weight}g and add that many to cart. "
                # f"For example, if target is {target_weight}g and packages are 3g each, add {(target_weight + 2) // 3} packages. "
                # f"If a package is larger than or equal to {target_weight}g, add 1 to cart. "
                # f"Prefer the option closest to {target_weight}g without going significantly over. Do not add multiple packages if not needed. "
            )
        else:
            # Fallback to smallest pack if weight estimation fails
            instruction += (
                f"Search for '{item}'. "
                f"Add 1 of the smallest available package to cart. "
            )

instruction += "Return the total number of items in cart."

# Use it:
nova = NovaAct(starting_page="https://www.ubereats.com")

nova.start()
result = nova.act(instruction, max_steps=99)

print("\n" + "="*50)
print("STEP 1: Shopping completed!")
print(f"Result: {result}")
print("="*50)

# Extract item count
try:
    if hasattr(result, 'response'):
        item_count = str(result.response).strip()
    else:
        item_count = str(result).strip()
    
    print(f"\n✓ Added {item_count} items to cart")
except Exception as e:
    print(f"⚠ Could not extract item count: {e}")
    item_count = "unknown"

# STEP 2: Extract cart details in a separate call
print("\n" + "="*50)
print("STEP 2: Extracting cart details...")
print("="*50)

cart_extraction_instruction = (
    "You are on the Ubereats page and on cart section. "
    "Look at all items already added in the cart by you earlier and scroll if necessary and extract the following information for each item: "
    "product name, quantity, price per unit, total price, and package size. "
    "Format your response as a simple list like this:\n"
    "Item 1: [name] | Qty: [number] | Price: $[amount] | Size: [size]\n"
    "Item 2: [name] | Qty: [number] | Price: $[amount] | Size: [size]\n"
    "...\n"
    "Total items: [count]\n"
    "Subtotal: $[amount]"
)

try:
    cart_result = nova.act(cart_extraction_instruction, max_steps=20)
    
    if hasattr(cart_result, 'response'):
        cart_text = str(cart_result.response)
    else:
        cart_text = str(cart_result)
    
    print("\n" + "="*50)
    print("CART CONTENTS:")
    print("="*50)
    print(cart_text)
    print("="*50)
    
    # Save to text file
    # with open("uber_cart_details.txt", "w") as f:
    #     f.write("INSTACART CART DETAILS\n")
    #     f.write("="*50 + "\n\n")
    #     f.write(cart_text)
    #     f.write("\n\n" + "="*50 + "\n")
    #     f.write(f"Extraction Date: {os.popen('date').read().strip()}\n")
    
    # print("\n✓ Cart details saved to uber_cart_details.txt")
    
    # Try to parse into structured format using regex
    cart_items = []
    lines = cart_text.split('\n')
    
    for line in lines:
        # Try to extract item info using regex
        match = re.search(r'(.+?)\s*\|\s*Qty:\s*(\d+)\s*\|\s*Price:\s*\$?([\d.]+)\s*\|\s*Size:\s*(.+)', line, re.IGNORECASE)
        if match:
            cart_items.append({
                "name": match.group(1).strip(),
                "quantity": int(match.group(2)),
                "price": match.group(3),
                "size": match.group(4).strip()
            })
    
    # Extract totals
    subtotal_match = re.search(r'Subtotal:\s*\$?([\d.]+)', cart_text, re.IGNORECASE)
    count_match = re.search(r'Total items:\s*(\d+)', cart_text, re.IGNORECASE)
    
    # Create structured JSON
    cart_data = {
        "item_count": int(count_match.group(1)) if count_match else len(cart_items),
        "subtotal": subtotal_match.group(1) if subtotal_match else "N/A",
        "cart_items": cart_items,
        "extraction_successful": len(cart_items) > 0
    }
    # Output path relative to working directory (backend/data/)
    output_path = Path("cart_jsons") / "uber_cart_details.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
    # with open("../../cart_json/uber_cart_details.json", "w") as f:
        json.dump(cart_data, f, indent=2)
    
    print("✓ Structured data saved to uber_cart_details.json")
    
    if cart_items:
        print(f"\nParsed {len(cart_items)} items:")
        for item in cart_items:
            print(f"  - {item['name']} (Qty: {item['quantity']}, Size: {item['size']}) = ${item['price']}")
    
except Exception as e:
    print(f"\n⚠ Error extracting cart details: {e}")
    print("Cart details could not be extracted automatically.")

print("\n" + "="*50)
print("COMPLETE!")
print("="*50)