"""
Supabase client and authentication utilities
"""
import os
from supabase import create_client, Client
from typing import Optional, Dict, Any
from jose import jwt, JWTError
import httpx


class SupabaseClient:
    """Singleton Supabase client for backend operations"""
    
    _instance: Optional[Client] = None
    _url: str = ""
    _service_role_key: str = ""
    
    @classmethod
    def initialize(cls, url: str, service_role_key: str):
        """Initialize the Supabase client with credentials"""
        cls._url = url
        cls._service_role_key = service_role_key
        cls._instance = create_client(url, service_role_key)
    
    @classmethod
    def get_client(cls) -> Client:
        """Get the Supabase client instance"""
        if cls._instance is None:
            raise RuntimeError("SupabaseClient not initialized. Call initialize() first.")
        return cls._instance
    
    @classmethod
    def get_url(cls) -> str:
        """Get the Supabase URL"""
        return cls._url


async def verify_supabase_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Supabase JWT token and return user payload
    
    For prototype: simplified verification
    In production: fetch JWKS and verify signature properly
    """
    try:
        # Decode without verification for prototype (NOT FOR PRODUCTION)
        # In production, fetch JWKS from: {SUPABASE_URL}/auth/v1/jwks
        payload = jwt.decode(
            token,
            options={"verify_signature": False},  # For prototype only!
        )
        
        # Basic validation
        if "sub" not in payload:
            return None
            
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
        }
    except JWTError as e:
        print(f"JWT decode error: {e}")
        return None


async def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Get user information from JWT token
    """
    payload = await verify_supabase_token(token)
    if not payload:
        return None
    
    # Optionally fetch full user details from Supabase
    try:
        client = SupabaseClient.get_client()
        response = client.auth.get_user(token)
        return response.user.model_dump() if response.user else None
    except Exception as e:
        print(f"Error fetching user: {e}")
        # Return basic info from token
        return payload

