"""
Profiling API Routes
Endpoints for user preference management
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from typing import List
from app.security.jwt import get_current_user_id
from app.services.gemini_profiling import update_user_preferences
from app.services.supabase_service import supabase_service
from app.models.phase3 import ProfilingRefreshResponse

router = APIRouter(prefix="/api/profiling", tags=["Profiling"])


@router.post("/refresh", response_model=ProfilingRefreshResponse)
async def refresh_profiling(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)
):
    """
    Refresh user preferences based on latest order.
    
    Process:
    1. Get user's most recent order
    2. Extract item names
    3. Generate 5 keywords via Gemini
    4. Merge with existing preferences
    5. Randomly select 5 final preferences
    6. Update profile
    
    Runs in background. Returns immediately.
    """
    # Get latest order
    orders = supabase_service.list_orders(user_id, limit=1)
    if not orders:
        return ProfilingRefreshResponse(
            message="No orders found for profiling"
        )
    
    order_id = orders[0]["id"]
    
    # Enqueue background task
    background_tasks.add_task(update_user_preferences, user_id, order_id)
    
    return ProfilingRefreshResponse(
        message="Profiling refresh started"
    )


@router.get("/preferences", response_model=List[str])
async def get_preferences(user_id: str = Depends(get_current_user_id)):
    """
    Get user's current preferences (up to 5 keywords).
    
    These keywords represent the user's food/lifestyle interests
    based on their order history.
    
    Returns empty list if user has no preferences yet.
    """
    profile = supabase_service.get_profile(user_id)
    return profile.get("preferences", []) if profile else []

