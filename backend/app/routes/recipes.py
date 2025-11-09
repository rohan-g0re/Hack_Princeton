from fastapi import APIRouter, HTTPException
from app.models.ingredient import RecipeIngredientsRequest, RecipeIngredientsResponse
from app.services.gemini_recipe_adapter import fetch_ingredients_for_recipe
import logging

router = APIRouter(prefix="/recipes", tags=["recipes"])
logger = logging.getLogger(__name__)


@router.post("/ingredients", response_model=RecipeIngredientsResponse)
async def get_recipe_ingredients(request: RecipeIngredientsRequest):
    """
    Fetch ingredients for a given recipe name using Gemini API.
    Returns normalized ingredient list with IDs.
    """
    logger.info(f"[RECIPE] Fetching ingredients for recipe: {request.recipe_name}")
    
    ingredients = fetch_ingredients_for_recipe(request.recipe_name)
    
    if not ingredients:
        logger.error(f"[RECIPE] Failed to fetch ingredients for: {request.recipe_name}")
        raise HTTPException(
            status_code=422,
            detail="Unable to fetch ingredients for this recipe. Please try again."
        )
    
    logger.info(f"[RECIPE] Successfully fetched {len(ingredients)} ingredients for: {request.recipe_name}")
    return RecipeIngredientsResponse(ingredients=ingredients)

