import sys
import json
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models.ingredient import Ingredient

# Import from app/services/gemini_recipe
try:
    from app.services.gemini_recipe import recipe_to_shopping_list, ingredients_to_shopping_list
except ImportError as e:
    raise RuntimeError(f"Cannot import from app/services/gemini_recipe.py: {e}")


def fetch_ingredients_for_recipe(recipe_name: str) -> list[Ingredient]:
    """
    Adapter to call app/services/gemini_recipe.py and normalize to Ingredient models.
    Returns empty list on failure.
    """
    try:
        # Call Gemini via existing code
        if "," in recipe_name:
            result = ingredients_to_shopping_list(recipe_name)
        else:
            result = recipe_to_shopping_list(recipe_name)
        
        if not result or "shopping_list" not in result:
            return []
        
        items = result["shopping_list"]
        return [Ingredient.from_gemini_item(item) for item in items]
    
    except Exception as e:
        # Log error but don't crash
        print(f"[ERROR] fetch_ingredients_for_recipe: {e}")
        return []

