# tests/test_phase4.py
"""
Test Phase 4: Knot API Integration

Deliverables:
- Knot API configuration with merchant IDs
- Knot API client with sync_transactions method
- Mock data generator for demo purposes
- Test script for transaction sync
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_knot_imports():
    """Test Knot API imports"""
    print("Testing Knot API imports...")
    
    try:
        from knot_api.config import KNOT_CLIENT_ID, MERCHANT_IDS, KNOT_SYNC_ENDPOINT
        from knot_api.client import KnotAPIClient, get_knot_client
        from knot_api.mock_data import generate_mock_transactions
        
        print("[PASS] All Knot API modules imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Import error: {e}")
        return False

def test_knot_config():
    """Test Knot API configuration"""
    print("\nTesting Knot API configuration...")
    
    from knot_api.config import MERCHANT_IDS
    
    required_merchants = ["instacart", "ubereats", "doordash"]
    
    for merchant in required_merchants:
        if merchant not in MERCHANT_IDS:
            print(f"[FAIL] Merchant {merchant} not in config")
            return False
        
        if not isinstance(MERCHANT_IDS[merchant], int):
            print(f"[FAIL] Merchant ID for {merchant} is not an integer")
            return False
    
    print(f"[PASS] All {len(MERCHANT_IDS)} merchants configured correctly")
    return True

def test_mock_data_generation():
    """Test mock transaction data generation"""
    print("\nTesting mock data generation...")
    
    from knot_api.mock_data import generate_mock_transactions
    
    # Generate mock data
    data = generate_mock_transactions(merchant_id=40, limit=3)
    
    # Verify structure
    if "transactions" not in data:
        print("[FAIL] Mock data missing 'transactions' key")
        return False
    
    if len(data["transactions"]) != 3:
        print(f"[FAIL] Expected 3 transactions, got {len(data['transactions'])}")
        return False
    
    # Verify transaction structure
    txn = data["transactions"][0]
    required_keys = ["id", "merchant_id", "amount", "date", "status", "items"]
    
    for key in required_keys:
        if key not in txn:
            print(f"[FAIL] Transaction missing key: {key}")
            return False
    
    # Verify items have SKUs
    if not txn["items"]:
        print("[FAIL] Transaction has no items")
        return False
    
    item = txn["items"][0]
    required_item_keys = ["sku", "name", "quantity", "price"]
    
    for key in required_item_keys:
        if key not in item:
            print(f"[FAIL] Item missing key: {key}")
            return False
    
    print("[PASS] Mock data generation works correctly")
    print(f"  Sample SKU: {item['sku']}")
    print(f"  Sample item: {item['name']}")
    return True

def test_knot_client():
    """Test Knot API client"""
    print("\nTesting Knot API client...")
    
    from knot_api.client import KnotAPIClient, get_knot_client
    
    # Test client creation
    client = KnotAPIClient()
    
    if not hasattr(client, 'sync_transactions'):
        print("[FAIL] Client missing sync_transactions method")
        return False
    
    # Test singleton
    client1 = get_knot_client()
    client2 = get_knot_client()
    
    if client1 is not client2:
        print("[FAIL] Singleton pattern not working")
        return False
    
    # Test sync (will use mock data since API may not be accessible)
    try:
        result = client.sync_transactions(
            merchant_id=40,
            external_user_id="test_user",
            limit=1
        )
        
        if "transactions" not in result:
            print("[FAIL] sync_transactions returned invalid format")
            return False
        
        print("[PASS] Knot API client works correctly")
        print(f"  Retrieved: {len(result['transactions'])} transaction(s)")
        print(f"  Mock: {result.get('mock', False)}")
        return True
        
    except Exception as e:
        print(f"[FAIL] Client test error: {e}")
        return False

def test_merchant_id_mapping():
    """Test merchant ID mapping to platforms"""
    print("\nTesting merchant ID mapping...")
    
    from knot_api.config import MERCHANT_IDS
    from config.platforms import PLATFORM_CONFIGS
    
    # Verify all configured platforms have merchant IDs
    for platform in ["instacart", "ubereats", "doordash"]:
        if platform not in MERCHANT_IDS:
            print(f"[FAIL] Platform {platform} missing from MERCHANT_IDS")
            return False
        
        if platform not in PLATFORM_CONFIGS:
            print(f"[FAIL] Platform {platform} missing from PLATFORM_CONFIGS")
            return False
        
        # Check merchant_id matches
        if PLATFORM_CONFIGS[platform]["merchant_id"] != MERCHANT_IDS[platform]:
            print(f"[FAIL] Merchant ID mismatch for {platform}")
            return False
    
    print("[PASS] Merchant ID mapping correct across configs")
    return True

def main():
    """Run all Phase 4 tests"""
    print("=" * 70)
    print("PHASE 4 DELIVERABLE TESTS")
    print("=" * 70)
    
    tests = [
        ("Knot API Imports", test_knot_imports),
        ("Knot Config", test_knot_config),
        ("Mock Data Generation", test_mock_data_generation),
        ("Knot API Client", test_knot_client),
        ("Merchant ID Mapping", test_merchant_id_mapping),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            results.append(test_func())
        except Exception as e:
            print(f"[FAIL] {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 70)
    print("PHASE 4 TEST RESULTS")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] ALL PHASE 4 TESTS PASSED - Ready for git commit")
        return True
    else:
        print("[FAILURE] SOME TESTS FAILED - Fix before committing")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

