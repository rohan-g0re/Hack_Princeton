"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# Recipe & Ingredients Models
class RecipeRequest(BaseModel):
    query: str = Field(..., description="Recipe query like 'caesar salad'")


class IngredientItem(BaseModel):
    name: str
    quantity: str
    category: Optional[str] = None


class RecipeResponse(BaseModel):
    recipe_name: str
    ingredients: List[IngredientItem]
    session_id: UUID


# Agent Models
class StartAgentsRequest(BaseModel):
    session_id: UUID
    ingredients: List[IngredientItem]
    platforms: List[str] = Field(..., description="List of platforms like ['instacart', 'ubereats']")


class AgentProgressUpdate(BaseModel):
    platform: str
    status: str  # 'starting', 'running', 'completed', 'failed'
    message: str
    progress_percent: Optional[int] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    platforms: Dict[str, Any]


# Cart Models
class CartItem(BaseModel):
    name: str
    quantity: int
    price: float
    size: Optional[str] = None
    image_url: Optional[str] = None


class PlatformCart(BaseModel):
    platform: str
    items: List[CartItem]
    subtotal: float
    item_count: int
    updated_at: datetime


class CartStatusResponse(BaseModel):
    session_id: UUID
    carts: List[PlatformCart]
    total_items: int
    total_amount: float


# Cart Diff Models
class CartDiffItem(BaseModel):
    action: str = Field(..., description="'add' or 'remove'")
    item: CartItem


class SaveCartDiffsRequest(BaseModel):
    session_id: UUID
    platform: str
    diffs: List[CartDiffItem]


class ApplyDiffsRequest(BaseModel):
    session_id: UUID


# Checkout Models
class CheckoutRequest(BaseModel):
    session_id: UUID


class PlatformTotal(BaseModel):
    platform: str
    subtotal: float
    items_count: int


class CheckoutResponse(BaseModel):
    transaction_id: UUID
    total_amount: float
    platforms: List[PlatformTotal]
    knot_transaction_id: Optional[str] = None
    created_at: datetime


# Auth Models (proxy for Supabase)
class SignUpRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class SignInRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: Dict[str, Any]

