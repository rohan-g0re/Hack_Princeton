"""
Gemini Receipt Generation
Uses Gemini Nano Banana to generate photorealistic receipt images
"""
import google.generativeai as genai
from PIL import Image
from io import BytesIO
from typing import Dict, Tuple, Optional
from app.config import settings
from app.services.supabase_service import supabase_service
import time

genai.configure(api_key=settings.gemini_api_key)


def build_receipt_prompt(order: Dict) -> str:
    """
    Construct comprehensive prompt for Gemini Nano Banana to generate receipt.
    """
    knot_payload = order.get("knot_payload", {})
    store_name = order.get("store_name", "Store")
    order_date = order.get("created_at", "")
    
    # Extract first transaction for simplicity (or aggregate)
    tx = knot_payload.get("transactions", [{}])[0]
    products = tx.get("products", [])
    price_info = tx.get("price", {})
    
    subtotal = price_info.get("sub_total", "0.00")
    total = price_info.get("total", "0.00")
    
    # Calculate tax
    tax = "0.00"
    for adj in price_info.get("adjustments", []):
        if adj.get("type") == "TAX":
            tax = adj.get("amount", "0.00")
            break
    
    # Build items list
    items_text = ""
    for idx, product in enumerate(products, start=1):
        name = product.get("name", f"Item {idx}")
        qty = product.get("quantity", 1)
        unit_price = product.get("price", {}).get("unit_price", "0.00")
        line_total = product.get("price", {}).get("total", "0.00")
        items_text += f"{idx}. {name} (Qty: {qty}) @ ${unit_price} ea = ${line_total}\n"
    
    prompt = f"""Generate a photorealistic grocery store receipt image with the following specifications:

**Store**: {store_name}
**Date**: {order_date}

**Items**:
{items_text}

**Financial Summary**:
- Subtotal: ${subtotal}
- Tax: ${tax}
- Total: ${total}

**Image Requirements**:
- Dimensions: 1024x1792 pixels (portrait orientation)
- Style: Matte white thermal paper with slight texture
- Font: Monospaced, similar to receipt printers (Courier or similar)
- Layout: Center-aligned store name at top, items in tabular format, totals at bottom
- Realism: Include faint creases, subtle yellowing, realistic alignment
- Accuracy: DO NOT add or remove items; match quantities and prices EXACTLY
- Watermark: Subtle "AI Generated" or similar in footer (optional)

Make it look like a real receipt you'd get from {store_name}. Focus on authenticity and readability."""
    
    return prompt


def generate_receipt_image(order_id: str, max_retries: int = None) -> Tuple[bytes, bytes]:
    """
    Generate receipt image + thumbnail using Gemini Nano Banana.
    
    Args:
        order_id: Order to generate receipt for
        max_retries: Max retry attempts (defaults to settings)
    
    Returns:
        Tuple of (full_image_bytes, thumbnail_bytes)
    
    Raises:
        ValueError: If order not found
        RuntimeError: If generation fails after retries
    """
    if max_retries is None:
        max_retries = settings.max_receipt_retries
    
    order = supabase_service.get_order(order_id)
    if not order:
        raise ValueError(f"Order {order_id} not found")
    
    prompt = build_receipt_prompt(order)
    
    model = genai.GenerativeModel(settings.gemini_model_image)
    
    for attempt in range(max_retries):
        try:
            # Call Gemini image generation
            # Note: Actual API may differ; adjust based on Gemini docs
            response = model.generate_content([
                prompt,
                {"mime_type": "image/png"}
            ])
            
            # Extract image bytes
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_bytes = part.inline_data.data
                        
                        # Create thumbnail (320x568)
                        img = Image.open(BytesIO(image_bytes))
                        img.thumbnail((320, 568), Image.Resampling.LANCZOS)
                        thumb_buffer = BytesIO()
                        img.save(thumb_buffer, format="JPEG", quality=85)
                        thumb_bytes = thumb_buffer.getvalue()
                        
                        return image_bytes, thumb_bytes
            
            raise ValueError("No image in Gemini response")
        
        except Exception as e:
            if attempt < max_retries - 1:
                delay = settings.receipt_retry_delay_seconds * (attempt + 1)
                print(f"Receipt generation attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                raise e
    
    raise RuntimeError(f"Failed to generate receipt after {max_retries} retries")


def process_receipt_for_order(order_id: str, user_id: str):
    """
    Generate receipt and upload to Storage; update order.
    This function is designed to run as a background task.
    
    Args:
        order_id: Order to process
        user_id: User who owns the order
    """
    try:
        # Update status to generating
        supabase_service.update_order_receipt(order_id, None, None, status="generating")
        
        # Generate images
        image_bytes, thumb_bytes = generate_receipt_image(order_id)
        
        # Upload to Supabase Storage
        image_path = supabase_service.upload_receipt(user_id, order_id, image_bytes, is_thumbnail=False)
        thumb_path = supabase_service.upload_receipt(user_id, order_id, thumb_bytes, is_thumbnail=True)
        
        # Update order with paths
        supabase_service.update_order_receipt(order_id, image_path, thumb_path, status="completed")
        
        print(f"✓ Receipt generated for order {order_id}")
    
    except Exception as e:
        print(f"✗ Receipt generation failed for order {order_id}: {e}")
        supabase_service.update_order_receipt(order_id, None, None, status="failed")
        raise e

