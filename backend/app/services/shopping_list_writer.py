import json
from pathlib import Path
from typing import List
from app.config import settings
from app.models.ingredient import IngredientInput


def write_shopping_list(items: List[IngredientInput]) -> bool:
    """
    Write shopping_list.json to current_code/ directory.
    Format matches what main.py driver expects.
    
    Expected schema:
    {
      "items": [
        { "name": "tomato", "quantity": 3, "unit": "pcs" }
      ]
    }
    """
    try:
        output_path = settings.shopping_list_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert Pydantic models to dict
        data = {
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit or ""
                }
                for item in items
            ]
        }
        
        # Atomic write: write to temp, then rename
        temp_path = output_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        temp_path.replace(output_path)
        return True
    
    except Exception as e:
        print(f"[ERROR] write_shopping_list: {e}")
        return False

