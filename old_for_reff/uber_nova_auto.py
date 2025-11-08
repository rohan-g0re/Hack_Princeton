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
# genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))  # Set your API key
# model = genai.GenerativeModel('gemini-2.0-flash-exp')

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")

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

def build_instruction_for_items(items_subset, is_first_batch=True):
    """Build instruction string for a subset of items"""
    instruction = ""
    
    if is_first_batch:
        instruction += (
            "If a sign-up popup appears, close it. "
            "Put addess to deliver as 89 Northampton St, Boston, MA 02118. "
            "If a CAPTCHA appears, complete the verification. "
            "If any popup appears, close it. "
            "Search for '{Target_Element_To_be_bought}' and click on the store. "
            "If any popup appears, close it. "
        )
    else:
        # For subsequent batches, just handle popups and navigate to store
        instruction += (
            "If any popup appears, close it. "
            "Go to the store page if not already there. "
        )
    
    for entry in items_subset:
        raw_item = entry.get("item", "").strip()
        qty = entry.get("quantity", 1)
        item = normalize_item_name(raw_item)

        if is_count_quantity(qty):
            # Countable items - add exact count
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
                instruction += (
                    f"Search for '{item}'. "
                    f"Look at available package sizes in grams. "
                    f"Target weight needed: {target_weight}g. "
                    f"If packages are smaller than {target_weight}g, calculate how many packages are needed to meet or exceed {target_weight}g and add that many to cart. "
                    f"If a package is larger than or equal to {target_weight}g, add 1 to cart. "
                    f"Prefer the option closest to {target_weight}g without going significantly over. "
                )
            else:
                # Fallback to smallest pack if weight estimation fails
                instruction += (
                    f"Search for '{item}'. "
                    f"In product list, prefer the smallest-size pack/container available. "
                    f"Add 1 to cart. "
                )
    
    instruction += "Return the total items in cart."
    return instruction

# Configuration
ITEMS_PER_BATCH = 7
shopping_list = load_shopping_list()

# Process items in batches
total_items = len(shopping_list)
num_batches = (total_items + ITEMS_PER_BATCH - 1) // ITEMS_PER_BATCH  # ceiling division

print(f"Processing {total_items} items in {num_batches} batches...")

for batch_idx in range(num_batches):
    start_idx = batch_idx * ITEMS_PER_BATCH
    end_idx = min(start_idx + ITEMS_PER_BATCH, total_items)
    batch_items = shopping_list[start_idx:end_idx]
    
    print(f"\n{'='*50}")
    print(f"Batch {batch_idx + 1}/{num_batches}: Processing items {start_idx + 1}-{end_idx}")
    print(f"{'='*50}")
    
    # Build instruction for this batch
    is_first = (batch_idx == 0)
    instruction = build_instruction_for_items(batch_items, is_first_batch=is_first)
    
    # Create new NovaAct instance for each batch
    nova = NovaAct(starting_page="https://www.ubereats.com")
    nova.start()
    
    try:
        result = nova.act(instruction, max_steps=99)
        print(f"Batch {batch_idx + 1} completed. Result: {result}")
    except Exception as e:
        print(f"Error in batch {batch_idx + 1}: {e}")
    finally:
        # Clean up the session
        nova.stop()  # assuming there's a stop/close method
    
    print(f"Batch {batch_idx + 1} session closed.\n")

print("\n" + "="*50)
print("All batches completed!")
print("="*50)