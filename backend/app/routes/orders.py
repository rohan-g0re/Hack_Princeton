"""
Orders API Routes
Endpoints for managing orders and importing Knot JSONs
"""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from typing import List
from app.security.jwt import get_current_user_id
from app.services.supabase_service import supabase_service
from app.services.knot_importer import import_knot_jsons
from app.services.gemini_receipts import process_receipt_for_order
from app.services.gemini_profiling import update_user_preferences
from app.models.phase3 import (
    OrderSummary,
    OrderDetailResponse,
    OrderDetail,
    OrderItem,
    ImportKnotResponse
)

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.post("/import-knot", response_model=ImportKnotResponse)
async def import_knot(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)
):
    """
    Import Knot JSONs from current_code/knot_api_jsons/.
    
    Triggers background tasks for:
    - Receipt generation (Gemini)
    - User profiling (preference keywords)
    
    Returns list of created order IDs.
    """
    try:
        order_ids = import_knot_jsons(user_id)
        
        # Enqueue background tasks for each order
        for order_id in order_ids:
            background_tasks.add_task(process_receipt_for_order, order_id, user_id)
            background_tasks.add_task(update_user_preferences, user_id, order_id)
        
        return ImportKnotResponse(
            created_order_ids=order_ids,
            count=len(order_ids),
            message=f"Successfully imported {len(order_ids)} order(s)"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/", response_model=List[OrderSummary])
async def list_orders(
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id)
):
    """
    List user's orders with thumbnail URLs.
    
    Query params:
    - limit: Max results per page (default: 50)
    - offset: Pagination offset (default: 0)
    
    Returns orders newest first.
    """
    try:
        orders = supabase_service.list_orders(user_id, limit, offset)
        
        # Generate signed URLs for thumbnails
        for order in orders:
            if order.get("receipt_thumbnail_path"):
                order["receipt_thumbnail_url"] = supabase_service.get_signed_url(
                    order["receipt_thumbnail_path"], expires_in=3600
                )
            else:
                order["receipt_thumbnail_url"] = None
        
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order_detail(
    order_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get order details with items and receipt URL.
    
    Returns:
    - Order metadata
    - All order items
    - Signed URL for full receipt image (1-hour expiry)
    """
    try:
        order = supabase_service.get_order(order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Verify ownership
        if order["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        # Get items
        items = supabase_service.get_order_items(order_id)
        
        # Generate signed URL for full receipt
        receipt_url = None
        if order.get("receipt_image_path"):
            receipt_url = supabase_service.get_signed_url(
                order["receipt_image_path"], expires_in=3600
            )
        
        return OrderDetailResponse(
            order=OrderDetail(
                id=order["id"],
                store_name=order.get("store_name"),
                subtotal=order["subtotal"],
                tax=order["tax"],
                total=order["total"],
                currency=order["currency"],
                receipt_image_url=receipt_url,
                created_at=order["created_at"]
            ),
            items=[OrderItem(**item) for item in items]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch order: {str(e)}")

