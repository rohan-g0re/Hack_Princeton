# import json
# import re
# from nova_act import NovaAct
# import os
# import google.generativeai as genai
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# # Browser args enables browser debugging on port 9222.
# os.environ["NOVA_ACT_BROWSER_ARGS"] = "--remote-debugging-port=9222"

# # Configure Gemini
# api_key = os.getenv("GEMINI_API_KEY")
# if not api_key:
#     raise ValueError("GEMINI_API_KEY not found in .env file. Get your key from: https://aistudio.google.com/app/apikey")

# genai.configure(api_key=api_key)
# model = genai.GenerativeModel('gemini-2.0-flash-exp')

# def load_shopping_list(path="shopping_list.json"):
#     with open(path, "r") as f:
#         return json.load(f)["shopping_list"]

# # remove descriptors that don't help store search
# DESCRIPTORS = {
#     "medium", "large", "small", "melted", "ripe", "unsalted"
# }

# def normalize_item_name(name: str) -> str:
#     # if there are alternatives like "unsalted butter or vegetable oil" → pick the first option
#     if " or " in name.lower():
#         name = re.split(r"\s+or\s+", name, flags=re.IGNORECASE)[0]

#     # drop common descriptors at word boundaries
#     words = []
#     for w in re.split(r"\s+", name.strip()):
#         w_clean = re.sub(r"[^\w\-]", "", w).lower()
#         if w_clean not in DESCRIPTORS:
#             words.append(w)
#     cleaned = " ".join(words).strip()

#     # some slight tweaks: "Medium ripe bananas" → "bananas"
#     cleaned = re.sub(r"\brip[e]?\b", "", cleaned, flags=re.IGNORECASE).strip()
#     cleaned = re.sub(r"\s{2,}", " ", cleaned)
#     return cleaned

# def is_count_quantity(q):
#     # countable if a plain int/float, or a numeric string with no unit words
#     if isinstance(q, (int, float)):
#         return True
#     if isinstance(q, str):
#         # if string has any letters, assume it's unit-based (cups, tbsp, tsp, etc.)
#         if re.search(r"[A-Za-z]", q):
#             return False
#         # numeric-only string -> treat as count
#         return bool(re.fullmatch(r"\d+(\.\d+)?", q.strip()))
#     return False

# def estimate_weight_with_gemini(item_name: str, quantity: str) -> dict:
#     """
#     Use Gemini to estimate the weight needed for a given quantity.
#     Returns dict with 'weight_grams' and 'unit' or None if can't estimate.
#     """
#     prompt = f"""
# You are a precise cooking measurement converter. Convert the following ingredient quantity to grams.

# Ingredient: {item_name}
# Quantity: {quantity}

# Provide ONLY a JSON response in this exact format:
# {{
#     "weight_grams": <number>,
#     "unit": "g",
#     "confidence": "high/medium/low"
# }}

# Rules:
# - Be as accurate as possible using standard cooking conversions
# - For liquids, use density (water = 1g/ml, oil = 0.92g/ml, milk = 1.03g/ml, etc.)
# - For dry ingredients, use standard conversions (1 cup flour = 120g, 1 tbsp sugar = 12.5g, etc.)
# - Round to nearest gram
# - If you cannot determine, set weight_grams to null

# Example conversions:
# - 2 tbsp sugar → 25g
# - 1 cup flour → 120g
# - 1/2 cup milk → 120g
# - 1 tsp salt → 6g
# """
    
#     try:
#         response = model.generate_content(prompt)
#         response_text = response.text.strip()
        
#         # Extract JSON from markdown code blocks if present
#         if "```json" in response_text:
#             response_text = response_text.split("```json")[1].split("```")[0].strip()
#         elif "```" in response_text:
#             response_text = response_text.split("```")[1].split("```")[0].strip()
        
#         result = json.loads(response_text)
        
#         if result.get("weight_grams") and result["weight_grams"] > 0:
#             print(f"  ✓ Estimated {quantity} {item_name} = {result['weight_grams']}g (confidence: {result.get('confidence', 'unknown')})")
#             return result
#         else:
#             print(f"  ⚠ Could not estimate weight for {quantity} {item_name}")
#             return None
            
#     except Exception as e:
#         print(f"  ✗ Error estimating weight for {item_name}: {e}")
#         return None

# shopping_list = load_shopping_list()

# # Base instruction
# instruction = (
#     "If a sign-up popup appears, close it. "
#     "If a CAPTCHA appears, complete the verification. "
#     "If any popup appears, close it. "
#     "Search for 'Stop & shop' and click on the store. "
#     "If any popup appears, close it. "
# )

# for entry in shopping_list:
#     raw_item = entry.get("item", "").strip()
#     qty = entry.get("quantity", 1)
#     item = normalize_item_name(raw_item)

#     if is_count_quantity(qty):
#         # Countable: add exactly that many (e.g., 2 bananas)
#         qty_int = int(float(qty))
#         instruction += (
#             f"Search for '{item}' and add {qty_int} to cart. "
#         )
#     else:
#         # Unit-based measurements - use Gemini to estimate weight
#         print(f"Converting measurement for: {item} - {qty}")
#         weight_info = estimate_weight_with_gemini(item, qty)
        
#         if weight_info and weight_info.get("weight_grams"):
#             target_weight = weight_info["weight_grams"]
#             instruction += (
#                 f"Search for '{item}'. "
#                 f"Look at available package sizes in grams or ounces. "
#                 f"Target weight needed: {target_weight}g. "
#                 f"If packages are smaller than {target_weight}g, calculate how many packages are needed to meet or exceed {target_weight}g and add that many to cart. "
#                 f"For example, if target is {target_weight}g and packages are 3g each, add {(target_weight + 2) // 3} packages. "
#                 f"If a package is larger than or equal to {target_weight}g, add 1 to cart. "
#                 f"Prefer the option closest to {target_weight}g without going significantly over. "
#             )
#         else:
#             # Fallback to smallest pack if weight estimation fails
#             instruction += (
#                 f"Search for '{item}'. "
#                 f"In product list, prefer the smallest-size pack/container available. "
#                 f"Add 1 to cart. "
#             )

# # CHANGED: More explicit instruction to get cart details
# instruction += (
#     "Go to the cart or view cart page. "
#     "Extract detailed information for each item in the cart including: "
#     "product name, quantity added, individual price, total price for that item, and package size or weight. "
#     "Return ONLY a valid JSON object (no markdown, no code blocks) with this exact structure: "
#     '{"cart_items": [{"name": "product name", "quantity": number, "unit_price": "price", "total_price": "price", "package_info": "size/weight"}], '
#     '"subtotal": "amount", "item_count": number}'
# )

# # Use it:
# nova = NovaAct(starting_page="https://www.instacart.com")

# nova.start()
# result = nova.act(instruction, max_steps=99)  # Increased max_steps for cart extraction

# print("\n" + "="*50)
# print("Shopping completed!")
# print(f"Result: {result}")
# print("="*50)

# # Handle the result
# try:
#     # Check if result has a response attribute
#     if hasattr(result, 'response'):
#         response_data = result.response
#     else:
#         response_data = result
    
#     # Convert to string if needed
#     result_text = str(response_data).strip()
    
#     # If it's just a number, Nova didn't return JSON
#     if result_text.isdigit():
#         print(f"\n⚠ Nova returned only item count: {result_text}")
#         print("Cart details were not extracted. The cart has", result_text, "items.")
        
#         # Create a simple summary file
#         summary = {
#             "status": "incomplete",
#             "item_count": int(result_text),
#             "note": "Detailed cart information was not extracted"
#         }
#         with open("cart_summary.json", "w") as f:
#             json.dump(summary, f, indent=2)
#         print("✓ Basic summary saved to cart_summary.json")
        
#     else:
#         # Try to parse as JSON
#         if "```json" in result_text:
#             json_text = result_text.split("```json")[1].split("```")[0].strip()
#         elif "```" in result_text:
#             json_text = result_text.split("```")[1].split("```")[0].strip()
#         elif result_text.startswith("{"):
#             json_text = result_text
#         else:
#             # Try to find JSON pattern in the text
#             json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
#             json_text = json_match.group(0) if json_match else result_text
        
#         cart_data = json.loads(json_text)
        
#         # Save to file
#         with open("cart_details.json", "w") as f:
#             json.dump(cart_data, f, indent=2)
        
#         print("\n✓ Cart details saved to cart_details.json")
#         print(f"\nSummary:")
#         print(f"  Total items: {cart_data.get('item_count', 'N/A')}")
#         print(f"  Subtotal: {cart_data.get('subtotal', 'N/A')}")
#         print(f"  Items in cart:")
#         for item in cart_data.get('cart_items', []):
#             print(f"    - {item.get('name', 'Unknown')} x {item.get('quantity', 'N/A')} = {item.get('total_price', 'N/A')}")
    
# except json.JSONDecodeError as e:
#     print(f"\n⚠ Could not parse cart details as JSON: {e}")
#     print("Raw result:", result)
# except Exception as e:
#     print(f"\n⚠ Error processing cart details: {e}")
#     print("Raw result:", result)

# print("\n" + "="*50)



import json
import re
from nova_act import NovaAct
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Browser args enables browser debugging on port 9222.
os.environ["NOVA_ACT_BROWSER_ARGS"] = "--remote-debugging-port=9222"

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file. Get your key from: https://aistudio.google.com/app/apikey")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

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
    "If a CAPTCHA appears, complete the verification. "
    "If any popup appears, close it. "
    "Search for 'Stop & shop' and click on the store. "
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
        weight_info = estimate_weight_with_gemini(item, qty)
        
        if weight_info and weight_info.get("weight_grams"):
            target_weight = weight_info["weight_grams"]
            # Convert grams to ounces for easier comparison (1 oz = 28.35g)
            target_oz = round(target_weight / 28.35, 1)
            
            # SIMPLIFIED INSTRUCTION
            instruction += (
                f"Search for '{item}'. "
                f"You need approximately {target_weight}g (about {target_oz} oz). "
                f"Find the SMALLEST package size that contains at least this amount. "
                f"Add ONLY 1 package to cart. "
                f"Do not add multiple packages. "
            )
        else:
            # Fallback to smallest pack if weight estimation fails
            instruction += (
                f"Search for '{item}'. "
                f"Add 1 of the smallest available package to cart. "
            )

instruction += "Return the total number of items in cart."

# Use it:
nova = NovaAct(starting_page="https://www.instacart.com")

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
    "You are on the Instacart cart page. "
    "Look at all items in the cart and extract the following information for each item: "
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
    with open("instacart_cart_details.txt", "w") as f:
        f.write("INSTACART CART DETAILS\n")
        f.write("="*50 + "\n\n")
        f.write(cart_text)
        f.write("\n\n" + "="*50 + "\n")
        f.write(f"Extraction Date: {os.popen('date').read().strip()}\n")
    
    print("\n✓ Cart details saved to instacart_cart_details.txt")
    
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
    
    # Save JSON
    with open("instacart_cart_details.json", "w") as f:
        json.dump(cart_data, f, indent=2)
    
    print("✓ Structured data saved to instacart_cart_details.json")
    
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