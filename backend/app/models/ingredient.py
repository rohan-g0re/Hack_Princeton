from pydantic import BaseModel, Field, field_validator
from typing import Optional
import uuid


class IngredientInput(BaseModel):
    """User input for a single ingredient"""
    name: str = Field(..., min_length=1, max_length=200)
    quantity: float = Field(..., ge=0, le=9999)
    unit: Optional[str] = Field(None, max_length=50)
    
    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v):
        return v.strip()
    
    @field_validator("unit")
    @classmethod
    def sanitize_unit(cls, v):
        return v.strip() if v else None


class Ingredient(BaseModel):
    """Ingredient with generated ID"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    quantity: float
    unit: Optional[str] = None
    
    @classmethod
    def from_gemini_item(cls, item: dict) -> "Ingredient":
        """
        Convert Gemini API response item to Ingredient.
        Gemini returns: {"item": "Bananas", "quantity": 1}
        or: {"item": "Milk", "quantity": "1 liter"}
        """
        name = item.get("item", "Unknown")
        qty = item.get("quantity", 1)
        
        # Handle quantity that might be "1 liter" vs numeric
        if isinstance(qty, str):
            parts = qty.split()
            try:
                qty_num = float(parts[0])
                unit = " ".join(parts[1:]) if len(parts) > 1 else None
            except (ValueError, IndexError):
                qty_num = 1.0
                unit = qty
        else:
            qty_num = float(qty)
            unit = None
        
        return cls(name=name, quantity=qty_num, unit=unit)


class RecipeIngredientsRequest(BaseModel):
    """Request to fetch ingredients for a recipe"""
    recipe_name: str = Field(..., min_length=1, max_length=200)
    
    @field_validator("recipe_name")
    @classmethod
    def sanitize_recipe_name(cls, v):
        return v.strip()


class RecipeIngredientsResponse(BaseModel):
    """Response containing ingredients list"""
    ingredients: list[Ingredient]


class ShoppingListRequest(BaseModel):
    """Request to save shopping list"""
    items: list[IngredientInput] = Field(..., min_length=1, max_length=100)


class ShoppingListResponse(BaseModel):
    """Response after saving shopping list"""
    saved: bool
    count: int

