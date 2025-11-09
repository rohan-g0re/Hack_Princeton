from fastapi import APIRouter, HTTPException
from app.models.ingredient import RecipeIngredientsRequest, RecipeIngredientsResponse
from app.services.gemini_recipe_adapter import fetch_ingredients_for_recipe

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.post("/ingredients", response_model=RecipeIngredientsResponse)
async def get_recipe_ingredients(request: RecipeIngredientsRequest):
    """
    Fetch ingredients for a given recipe name using Gemini API.
    Returns normalized ingredient list with IDs.
    """
    ingredients = fetch_ingredients_for_recipe(request.recipe_name)
    
    if not ingredients:
        raise HTTPException(
            status_code=422,
            detail="Unable to fetch ingredients for this recipe. Please try again."
        )
    
    return RecipeIngredientsResponse(ingredients=ingredients)

