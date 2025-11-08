# knot_api/examples/test_sync.py

import sys
sys.path.append('../..')

from knot_api.client import get_knot_client
from knot_api.config import MERCHANT_IDS
import json

def test_transaction_sync():
    """Test syncing transactions from multiple merchants"""
    
    print("\n" + "=" * 70)
    print("KNOT API TRANSACTION SYNC TEST")
    print("=" * 70)
    
    client = get_knot_client()
    
    platforms_to_test = ["instacart", "ubereats", "doordash"]
    
    for platform in platforms_to_test:
        merchant_id = MERCHANT_IDS.get(platform)
        if not merchant_id:
            continue
        
        print(f"\n{'=' * 70}")
        print(f"Platform: {platform.upper()} (Merchant ID: {merchant_id})")
        print("=" * 70)
        
        result = client.sync_transactions(
            merchant_id=merchant_id,
            external_user_id="test_user_123",
            limit=2
        )
        
        print(f"\nRetrieved: {len(result.get('transactions', []))} transactions")
        print(f"Mock Data: {result.get('mock', False)}")
        
        for txn in result.get("transactions", []):
            print(f"\n  Transaction ID: {txn.get('id')}")
            print(f"  Amount: ${txn.get('amount'):.2f}")
            print(f"  Date: {txn.get('date')}")
            print(f"  Items: {len(txn.get('items', []))}")
            
            for item in txn.get("items", []):
                print(f"    - {item.get('name')} (SKU: {item.get('sku')})")
                print(f"      Qty: {item.get('quantity')}, Price: ${item.get('price'):.2f}")

if __name__ == "__main__":
    test_transaction_sync()

