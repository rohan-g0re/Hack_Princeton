"""
Supabase Service
Centralized operations for Supabase database and storage
"""
from supabase import create_client, Client
from typing import List, Dict, Any, Optional
from app.config import settings
import hashlib
import json


class SupabaseService:
    """Wrapper for Supabase operations with convenience methods"""
    
    def __init__(self):
        """Initialize Supabase client with service role key (admin access)"""
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
    
    # ==================== PROFILES ====================
    
    def get_profile(self, user_id: str) -> Optional[Dict]:
        """Fetch user profile by ID"""
        response = self.client.table("profiles").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None
    
    def upsert_profile(self, user_id: str, data: Dict) -> Dict:
        """Create or update user profile"""
        data["id"] = user_id
        response = self.client.table("profiles").upsert(data).execute()
        return response.data[0]
    
    def update_preferences(self, user_id: str, preferences: List[str]) -> Dict:
        """Update user preferences (max 5 keywords)"""
        response = self.client.table("profiles").update({
            "preferences": preferences[:5]  # Ensure max 5
        }).eq("id", user_id).execute()
        return response.data[0] if response.data else {}
    
    # ==================== ORDERS ====================
    
    def create_order(self, user_id: str, order_data: Dict, knot_payload: Dict) -> str:
        """
        Create order with idempotency via payload_hash.
        Returns order_id (existing or newly created).
        """
        # Compute hash for idempotency
        payload_hash = hashlib.sha256(
            json.dumps(knot_payload, sort_keys=True).encode()
        ).hexdigest()
        
        # Check if already imported
        existing = self.client.table("orders").select("id").eq("payload_hash", payload_hash).execute()
        if existing.data:
            return existing.data[0]["id"]
        
        # Create new order
        order = {
            "user_id": user_id,
            "store_name": order_data.get("store_name"),
            "subtotal": order_data.get("subtotal"),
            "tax": order_data.get("tax"),
            "total": order_data.get("total"),
            "currency": order_data.get("currency", "USD"),
            "platform_subtotals": order_data.get("platform_subtotals"),
            "knot_payload": knot_payload,
            "payload_hash": payload_hash,
            "receipt_status": "pending",
            "profiling_status": "pending"
        }
        
        response = self.client.table("orders").insert(order).execute()
        return response.data[0]["id"]
    
    def list_orders(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List orders for user, newest first"""
        response = self.client.table("orders").select(
            "id, store_name, total, currency, receipt_image_path, receipt_thumbnail_path, created_at"
        ).eq("user_id", user_id).order("created_at", desc=True).range(
            offset, offset + limit - 1
        ).execute()
        return response.data
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get single order with full details"""
        response = self.client.table("orders").select("*").eq("id", order_id).execute()
        return response.data[0] if response.data else None
    
    def update_order_receipt(
        self, 
        order_id: str, 
        image_path: Optional[str], 
        thumbnail_path: Optional[str] = None, 
        status: str = "completed"
    ):
        """Update receipt paths and status"""
        update_data = {
            "receipt_image_path": image_path,
            "receipt_status": status
        }
        if thumbnail_path:
            update_data["receipt_thumbnail_path"] = thumbnail_path
        
        self.client.table("orders").update(update_data).eq("id", order_id).execute()
    
    def update_order_profiling_status(self, order_id: str, status: str):
        """Update profiling status for an order"""
        self.client.table("orders").update({"profiling_status": status}).eq("id", order_id).execute()
    
    # ==================== ORDER ITEMS ====================
    
    def bulk_insert_order_items(self, order_id: str, items: List[Dict]):
        """Insert multiple order items at once"""
        for item in items:
            item["order_id"] = order_id
        if items:
            self.client.table("order_items").insert(items).execute()
    
    def get_order_items(self, order_id: str) -> List[Dict]:
        """Get all items for a specific order"""
        response = self.client.table("order_items").select("*").eq("order_id", order_id).execute()
        return response.data
    
    def get_latest_order_items(self, user_id: str) -> List[Dict]:
        """Get items from user's most recent order"""
        latest_order = self.client.table("orders").select("id").eq(
            "user_id", user_id
        ).order("created_at", desc=True).limit(1).execute()
        
        if not latest_order.data:
            return []
        
        order_id = latest_order.data[0]["id"]
        return self.get_order_items(order_id)
    
    # ==================== PROFILING HISTORY ====================
    
    def log_profiling(
        self, 
        user_id: str, 
        order_id: str, 
        generated_keywords: List[str], 
        final_preferences: List[str]
    ):
        """Record profiling update in history table"""
        self.client.table("profiling_history").insert({
            "user_id": user_id,
            "order_id": order_id,
            "generated_keywords": generated_keywords,
            "final_preferences": final_preferences
        }).execute()
    
    # ==================== STORAGE ====================
    
    def upload_receipt(
        self, 
        user_id: str, 
        order_id: str, 
        image_bytes: bytes, 
        is_thumbnail: bool = False
    ) -> str:
        """
        Upload receipt image to Supabase Storage.
        Returns the storage path.
        """
        extension = "jpg" if is_thumbnail else "png"
        suffix = "_thumb" if is_thumbnail else ""
        path = f"{user_id}/{order_id}{suffix}.{extension}"
        
        # Upload to storage bucket
        self.client.storage.from_(settings.receipts_bucket).upload(
            path,
            image_bytes,
            file_options={"content-type": f"image/{extension}"}
        )
        
        return path
    
    def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """
        Generate signed URL for private storage object.
        Default expiry: 1 hour (3600 seconds)
        """
        response = self.client.storage.from_(settings.receipts_bucket).create_signed_url(
            path, expires_in
        )
        return response.get("signedURL", "")


# Singleton instance
supabase_service = SupabaseService()

