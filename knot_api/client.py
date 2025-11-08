# knot_api/client.py

import requests
from typing import Dict, List, Optional
import logging
from .config import KNOT_BASE_URL, KNOT_BASIC_AUTH, KNOT_SYNC_ENDPOINT, MERCHANT_IDS

logger = logging.getLogger(__name__)

class KnotAPIClient:
    """
    Client for Knot API transaction sync
    
    Purpose: Retrieve sample transaction data to demonstrate
    what real order data looks like with SKU-level details.
    
    NOT used for actual payment processing.
    """
    
    def __init__(self, base_url: str = KNOT_BASE_URL, auth: str = KNOT_BASIC_AUTH):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json"
        })
    
    def sync_transactions(
        self,
        merchant_id: int,
        external_user_id: str,
        limit: int = 5,
        cursor: Optional[str] = None
    ) -> Dict:
        """
        Sync transactions from a merchant
        
        Args:
            merchant_id: Knot merchant ID (e.g., 40 for Instacart)
            external_user_id: Unique user identifier in your system
            limit: Number of transactions to retrieve
            cursor: Pagination cursor
        
        Returns:
            Dict containing transaction data with SKU details
        
        Example Response:
        {
            "transactions": [
                {
                    "id": "txn_123",
                    "amount": 45.67,
                    "date": "2024-11-08T10:30:00Z",
                    "items": [
                        {"sku": "MILK-001", "name": "Organic Milk", "quantity": 1, "price": 5.99}
                    ]
                }
            ],
            "cursor": "next_page_token"
        }
        """
        url = f"{self.base_url}{KNOT_SYNC_ENDPOINT}"
        payload = {
            "merchant_id": merchant_id,
            "external_user_id": external_user_id,
            "limit": limit
        }
        
        if cursor:
            payload["cursor"] = cursor
        
        try:
            logger.info(f"Syncing transactions for merchant_id={merchant_id}")
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Retrieved {len(data.get('transactions', []))} transactions")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Knot API request failed: {e}")
            # Fallback to mock data
            from .mock_data import generate_mock_transactions
            return generate_mock_transactions(merchant_id, limit)

# Singleton instance
_client = None

def get_knot_client() -> KnotAPIClient:
    """Get or create singleton Knot API client"""
    global _client
    if _client is None:
        _client = KnotAPIClient()
    return _client

