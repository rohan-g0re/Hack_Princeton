from pathlib import Path
from app.config import settings


def count_cart_artifacts() -> int:
    """Count JSON files in cart_jsons/"""
    cart_dir = settings.cart_jsons_dir
    if not cart_dir.exists():
        return 0
    return len(list(cart_dir.glob("*.json")))


def count_knot_api_artifacts() -> int:
    """Count JSON files in knot_api_jsons/"""
    knot_dir = settings.knot_api_jsons_dir
    if not knot_dir.exists():
        return 0
    return len(list(knot_dir.glob("*.json")))


def get_artifact_counts() -> dict:
    """Get counts for both directories"""
    return {
        "cart_count": count_cart_artifacts(),
        "knot_api_count": count_knot_api_artifacts()
    }

