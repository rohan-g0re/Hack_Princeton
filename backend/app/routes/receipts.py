"""
Receipts API Routes
Endpoints for generating receipt images
"""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from app.security.jwt import get_current_user_id
from app.services.gemini_receipts import process_receipt_for_order
from app.services.supabase_service import supabase_service
from app.models.phase3 import ReceiptGenerateResponse

router = APIRouter(prefix="/api/receipts", tags=["Receipts"])


@router.post("/generate/{order_id}", response_model=ReceiptGenerateResponse)
async def generate_receipt(
    order_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)
):
    """
    Trigger receipt generation for an order.
    
    Generates a photorealistic receipt image using Gemini Nano Banana
    and uploads it to Supabase Storage.
    
    The operation runs in the background. Check order.receipt_status
    for completion status.
    
    Returns immediately with confirmation.
    """
    try:
        order = supabase_service.get_order(order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Verify ownership
        if order["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        # Enqueue background task
        background_tasks.add_task(process_receipt_for_order, order_id, user_id)
        
        return ReceiptGenerateResponse(
            message="Receipt generation started",
            order_id=order_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger receipt generation: {str(e)}"
        )

