import os
import json
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

# 🔑 Set your Gemini key
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("Please set your GEMINI_API_KEY environment variable.")

genai.configure(api_key=API_KEY)

# 🌐 Simple web search function using DuckDuckGo
def search_recipe_online(recipe_name):
    """Fetch top search results for the recipe and extract brief info."""
    print(f"🔍 Searching the web for '{recipe_name}' ingredients...")
    search_url = "https://api.duckduckgo.com/"
    params = {
        "q": f"{recipe_name} ingredients list recipe site:allrecipes.com OR site:bbcgoodfood.com OR site:foodnetwork.com",
        "format": "json",
        "no_html": 1
    }
    response = requests.get(search_url, params=params)
    data = response.json()
    # Extract snippet if available
    related = data.get("RelatedTopics", [])
    snippets = [r.get("Text", "") for r in related if "Text" in r]
    return "\n".join(snippets[:5])  # take a few snippets


# 🧾 Use Gemini to structure into JSON
def recipe_to_shopping_list(recipe_name):
    search_results = search_recipe_online(recipe_name)

    prompt = f"""
Based on reliable online recipes, list the ingredients and their approximate quantities for "{recipe_name}".
Format the response ONLY as a JSON object like:

{{
  "shopping_list": [
    {{"item": "Bananas", "quantity": 1}},
    {{"item": "Milk", "quantity": 1}}
  ]
}}

Use numeric quantities where possible (e.g., 2, 0.5, 3) with unit of measurement.
Here are some online snippets to reference:
{search_results}
"""

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    text = response.text.strip()

    # Extract only valid JSON
    start, end = text.find("{"), text.rfind("}") + 1
    json_str = text[start:end]
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("⚠️ Model did not return valid JSON, showing raw output:")
        print(text)
        return None


# 🧾 Alternative: accept a comma-separated ingredient list and normalize
def ingredients_to_shopping_list(ingredients_csv: str):
    """
    Convert a comma-separated list of ingredients into a structured shopping list JSON.
    Uses Gemini to normalize names and infer reasonable numeric quantities and units.
    """
    raw_items = [x.strip() for x in ingredients_csv.split(",") if x.strip()]
    if not raw_items:
        return None

    items_bulleted = "\n".join(f"- {i}" for i in raw_items)

    prompt = f"""
You are a precise shopping-list normalizer. Convert the following ingredient names
into a JSON shopping list with numeric quantities and units. If a quantity is
unspecified, make a reasonable default guess.

Ingredients:
{items_bulleted}

Return ONLY a JSON object like:
{{
  "shopping_list": [
    {{"item": "Bananas", "quantity": 6}},
    {{"item": "Milk", "quantity": "1 liter"}}
  ]
}}

Rules:
- Use numeric quantities where possible (e.g., 2, 0.5, 3) and include unit if applicable.
- If count-based (e.g., bananas, eggs), return an integer count.
- Keep item names simple for store search (avoid adjectives like 'ripe', 'fresh', 'unsalted').
"""
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    text = response.text.strip()

    # Extract only valid JSON
    start, end = text.find("{"), text.rfind("}") + 1
    json_str = text[start:end]
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("⚠️ Model did not return valid JSON, showing raw output:")
        print(text)
        return None


# 💾 Save to file
def save_to_file(data, recipe_name):
    filename = f"shopping_list.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved JSON to {filename}")


# 🚀 Run
if __name__ == "__main__":
    user_input = input("🍳 Enter recipe name OR comma-separated ingredients: ").strip()
    if "," in user_input:
        data = ingredients_to_shopping_list(user_input)
    else:
        data = recipe_to_shopping_list(user_input)
    if data:
        print(json.dumps(data, indent=2))
        save_to_file(data, user_input)
