"""
Gemini Profiling Service
Extracts preference keywords from order items using Gemini
"""
import google.generativeai as genai
from typing import List
import random
from app.config import settings
from app.services.supabase_service import supabase_service

genai.configure(api_key=settings.gemini_api_key)


def extract_keywords_from_items(items: List[str]) -> List[str]:
    """
    Use Gemini to suggest 5 preference keywords from grocery item names.
    
    Args:
        items: List of item names
    
    Returns:
        List of up to 5 keyword strings
    """
    items_text = "\n".join([f"- {item}" for item in items[:50]])  # Limit to 50 items
    
    prompt = f"""You are a grocery preference analyzer. Given the following list of grocery items, suggest exactly 5 concise preference keywords that capture the user's food/lifestyle interests.

Items:
{items_text}

Requirements:
- Return exactly 5 keywords
- Each keyword should be 1-2 words max
- Focus on categories (e.g., "Organic", "Snacks", "Health", "Baby Care", "Personal Care", "Beverages")
- Return ONLY the keywords, one per line, no numbering or extra text

Keywords:"""
    
    model = genai.GenerativeModel(settings.gemini_model_text)
    response = model.generate_content(prompt)
    
    # Parse response - extract lines
    keywords = [
        line.strip() 
        for line in response.text.strip().split("\n") 
        if line.strip() and not line.strip().startswith(("#", "-", "*"))
    ]
    
    return keywords[:5]  # Ensure max 5


def update_user_preferences(user_id: str, order_id: str):
    """
    Refresh user preferences based on latest order.
    This function is designed to run as a background task.
    
    Process:
    1. Get items from the specified order
    2. Generate 5 keywords via Gemini
    3. Merge with existing preferences (dedupe)
    4. Randomly select 5 final preferences
    5. Update profile
    6. Log to profiling_history
    
    Args:
        user_id: User to update
        order_id: Order to base preferences on
    """
    try:
        # Update status
        supabase_service.update_order_profiling_status(order_id, "processing")
        
        # Get items from the order
        items = supabase_service.get_order_items(order_id)
        if not items:
            print(f"No items found for order {order_id}, skipping profiling")
            supabase_service.update_order_profiling_status(order_id, "skipped")
            return
        
        # Extract unique item names
        item_names = list(set([item["item_name"] for item in items if item.get("item_name")]))
        
        if not item_names:
            print(f"No valid item names for order {order_id}, skipping profiling")
            supabase_service.update_order_profiling_status(order_id, "skipped")
            return
        
        # Generate keywords via Gemini
        generated_keywords = extract_keywords_from_items(item_names)
        
        # Get current preferences
        profile = supabase_service.get_profile(user_id)
        existing_prefs = profile.get("preferences", []) if profile else []
        
        # Merge: existing + new, dedupe (case-insensitive)
        all_keywords_lower = {kw.lower(): kw for kw in (existing_prefs + generated_keywords)}
        all_keywords = list(all_keywords_lower.values())
        
        # Randomly select 5
        if len(all_keywords) > 5:
            final_prefs = random.sample(all_keywords, 5)
        else:
            final_prefs = all_keywords[:5]
        
        # Ensure we have a profile first
        if not profile:
            supabase_service.upsert_profile(user_id, {
                "preferences": final_prefs
            })
        else:
            # Update DB
            supabase_service.update_preferences(user_id, final_prefs)
        
        # Log history
        supabase_service.log_profiling(user_id, order_id, generated_keywords, final_prefs)
        
        # Update order profiling status
        supabase_service.update_order_profiling_status(order_id, "completed")
        
        print(f"✓ Profiling updated for user {user_id}, order {order_id}: {final_prefs}")
    
    except Exception as e:
        print(f"✗ Profiling failed for user {user_id}, order {order_id}: {e}")
        supabase_service.update_order_profiling_status(order_id, "failed")
        raise e

