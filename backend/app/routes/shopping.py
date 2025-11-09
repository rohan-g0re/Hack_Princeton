from fastapi import APIRouter, HTTPException
from app.models.ingredient import ShoppingListRequest, ShoppingListResponse
from app.services.shopping_list_writer import write_shopping_list

router = APIRouter(prefix="/shopping-list", tags=["shopping"])


@router.post("", response_model=ShoppingListResponse)
async def save_shopping_list(request: ShoppingListRequest):
    """
    Save finalized shopping list to current_code/shopping_list.json
    """
    success = write_shopping_list(request.items)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to write shopping list to disk"
        )
    
    return ShoppingListResponse(saved=True, count=len(request.items))

