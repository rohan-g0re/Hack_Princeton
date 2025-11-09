from pydantic import BaseModel
from typing import Optional


class ItemSummary(BaseModel):
    """Summary of a single cart item"""
    name: str
    quantity: int
    unit_price: float
    total_price: float


class PlatformSummary(BaseModel):
    """Summary for a single platform (Instacart, Uber Eats, etc.)"""
    name: str
    logo: str  # "instacart" | "ubereats" | "doordash"
    items: list[ItemSummary]
    subtotal: float
    tax: float
    total: float
    date: str  # ISO format or display format
    best_deal: bool = False


class ComparisonResponse(BaseModel):
    """Comparison across all platforms"""
    job_id: str
    platforms: list[PlatformSummary]

