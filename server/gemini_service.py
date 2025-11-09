"""
Gemini API service for recipe to ingredients conversion
"""
import google.generativeai as genai
import json
from typing import List, Dict, Optional
from server.models import IngredientItem


class GeminiService:
    """Service for interacting with Gemini API"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    async def get_recipe_ingredients(self, recipe_query: str) -> Dict:
        """
        Convert recipe query to structured ingredient list
        
        Args:
            recipe_query: User's recipe request like "caesar salad"
            
        Returns:
            Dict with recipe_name and ingredients list
        """
        prompt = f"""
You are a professional chef and recipe expert. Given a recipe name or query, provide a complete list of ingredients needed.

Recipe Query: {recipe_query}

Provide your response as a JSON object with this exact format:
{{
    "recipe_name": "Name of the Recipe",
    "ingredients": [
        {{
            "name": "ingredient name",
            "quantity": "amount with unit (e.g., 2 cups, 1 tbsp, 3 items)",
            "category": "produce/dairy/meat/pantry/etc"
        }}
    ]
}}

Rules:
- Be specific and realistic with quantities for 2-4 servings
- Use standard cooking measurements (cups, tbsp, tsp, oz, lb, etc.)
- Include all essential ingredients
- Categorize ingredients appropriately
- Keep ingredient names simple (e.g., "Romaine Lettuce" not "Fresh Organic Romaine Lettuce")

Example for "Caesar Salad":
{{
    "recipe_name": "Caesar Salad",
    "ingredients": [
        {{"name": "Romaine Lettuce", "quantity": "1 large head", "category": "produce"}},
        {{"name": "Parmesan Cheese", "quantity": "1/2 cup", "category": "dairy"}},
        {{"name": "Caesar Dressing", "quantity": "1/2 cup", "category": "pantry"}},
        {{"name": "Croutons", "quantity": "1 cup", "category": "pantry"}},
        {{"name": "Lemon", "quantity": "1 item", "category": "produce"}}
    ]
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
            # Validate structure
            if "recipe_name" not in result or "ingredients" not in result:
                raise ValueError("Invalid response structure from Gemini")
            
            return result
            
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            # Fallback to a simple response
            return {
                "recipe_name": recipe_query.title(),
                "ingredients": [
                    {"name": "Error fetching ingredients", "quantity": "N/A", "category": "error"}
                ]
            }
    
    async def estimate_weight_from_quantity(self, item_name: str, quantity: str) -> Optional[Dict]:
        """
        Estimate weight in grams for a given quantity (for agent instructions)
        Reused from existing instacart.py logic
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
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
            if result.get("weight_grams") and result["weight_grams"] > 0:
                return result
            return None
            
        except Exception as e:
            print(f"Error estimating weight for {item_name}: {e}")
            return None

