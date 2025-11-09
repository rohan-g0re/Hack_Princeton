"""
Phase 3 Pydantic Models
Models for orders, receipts, and profiling APIs
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ==================== ORDER MODELS ====================

class OrderSummary(BaseModel):
    """Summary view of an order (for list display)"""
    id: str
    store_name: Optional[str]
    total: float
    currency: str
    receipt_thumbnail_url: Optional[str]
    created_at: str


class OrderDetail(BaseModel):
    """Detailed view of an order"""
    id: str
    store_name: Optional[str]
    subtotal: float
    tax: float
    total: float
    currency: str
    receipt_image_url: Optional[str]
    created_at: str


class OrderItem(BaseModel):
    """Individual item within an order"""
    platform: Optional[str]
    item_name: str
    quantity: Optional[float]
    unit: Optional[str]
    unit_price: Optional[float]
    total: Optional[float]


class OrderDetailResponse(BaseModel):
    """Response containing order details and items"""
    order: OrderDetail
    items: List[OrderItem]


# ==================== IMPORT MODELS ====================

class ImportKnotResponse(BaseModel):
    """Response from Knot JSON import"""
    created_order_ids: List[str]
    count: int
    message: str = "Orders imported successfully"


# ==================== RECEIPT MODELS ====================

class ReceiptGenerateResponse(BaseModel):
    """Response from receipt generation trigger"""
    message: str
    order_id: str


# ==================== PROFILING MODELS ====================

class ProfilingRefreshResponse(BaseModel):
    """Response from profiling refresh"""
    message: str


class PreferencesResponse(BaseModel):
    """User preferences response"""
    preferences: List[str]

