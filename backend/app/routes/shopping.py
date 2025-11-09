from fastapi import APIRouter, HTTPException
from app.models.ingredient import ShoppingListRequest, ShoppingListResponse
from app.services.shopping_list_writer import write_shopping_list
import logging

router = APIRouter(prefix="/shopping-list", tags=["shopping"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ShoppingListResponse)
async def save_shopping_list(request: ShoppingListRequest):
    """
    Save finalized shopping list to current_code/shopping_list.json
    """
    logger.info(f"[SHOPPING LIST] Saving shopping list with {len(request.items)} items")
    
    success = write_shopping_list(request.items)
    
    if not success:
        logger.error(f"[SHOPPING LIST] Failed to write shopping list to disk")
        raise HTTPException(
            status_code=500,
            detail="Failed to write shopping list to disk"
        )
    
    logger.info(f"[SHOPPING LIST] Successfully saved shopping list with {len(request.items)} items")
    return ShoppingListResponse(saved=True, count=len(request.items))

