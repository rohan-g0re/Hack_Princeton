# tests/test_phase2.py
"""
Test Phase 2: Data Models

Deliverables:
- CartItem dataclass with status tracking
- PlatformCart with item management
- CartDiff for tracking user edits
- CartState for global state management with JSON persistence
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.cart_models import CartItem, PlatformCart, CartDiff, CartState, ItemStatus

def test_cart_item():
    """Test CartItem creation and serialization"""
    print("Testing CartItem...")
    
    # Create item
    item = CartItem(
        ingredient_requested="milk",
        product_name="Organic Whole Milk",
        product_url="https://example.com/milk",
        price=5.99,
        quantity=2
    )
    
    # Test attributes
    if item.ingredient_requested != "milk":
        print("[FAIL] CartItem ingredient_requested incorrect")
        return False
    
    if item.status != ItemStatus.ADDED:
        print("[FAIL] CartItem default status incorrect")
        return False
    
    # Test serialization
    item_dict = item.to_dict()
    if item_dict['price'] != 5.99:
        print("[FAIL] CartItem to_dict() failed")
        return False
    
    # Test deserialization
    item2 = CartItem.from_dict(item_dict)
    if item2.product_name != "Organic Whole Milk":
        print("[FAIL] CartItem from_dict() failed")
        return False
    
    print("[PASS] CartItem works correctly")
    return True

def test_platform_cart():
    """Test PlatformCart with items"""
    print("\nTesting PlatformCart...")
    
    # Create cart
    cart = PlatformCart(platform_name="instacart", platform_id=40)
    
    # Add items
    item1 = CartItem("milk", "Organic Milk", "url1", 5.99)
    item2 = CartItem("eggs", "Large Eggs", "url2", 4.49)
    
    cart.add_item(item1)
    cart.add_item(item2)
    
    # Test item count
    if len(cart.items) != 2:
        print(f"[FAIL] Expected 2 items, got {len(cart.items)}")
        return False
    
    # Test totals calculation
    if cart.subtotal != 10.48:
        print(f"[FAIL] Subtotal incorrect: {cart.subtotal}")
        return False
    
    # Test remove item
    cart.remove_item("milk")
    if len(cart.items) != 1:
        print("[FAIL] Remove item failed")
        return False
    
    # Test serialization
    cart_dict = cart.to_dict()
    cart2 = PlatformCart.from_dict(cart_dict)
    
    if cart2.platform_name != "instacart":
        print("[FAIL] PlatformCart serialization failed")
        return False
    
    print("[PASS] PlatformCart works correctly")
    return True

def test_cart_diff():
    """Test CartDiff for tracking edits"""
    print("\nTesting CartDiff...")
    
    item = CartItem("milk", "Organic Milk", "url1", 5.99)
    diff = CartDiff(platform="instacart", action="remove", item=item)
    
    # Test attributes
    if diff.applied:
        print("[FAIL] CartDiff should not be applied initially")
        return False
    
    if diff.action != "remove":
        print("[FAIL] CartDiff action incorrect")
        return False
    
    # Test serialization
    diff_dict = diff.to_dict()
    diff2 = CartDiff.from_dict(diff_dict)
    
    if diff2.platform != "instacart":
        print("[FAIL] CartDiff serialization failed")
        return False
    
    print("[PASS] CartDiff works correctly")
    return True

def test_cart_state():
    """Test CartState global manager"""
    print("\nTesting CartState...")
    
    state = CartState()
    state.ingredients_requested = ["milk", "eggs"]
    
    # Create and add cart
    cart1 = PlatformCart("instacart", 40)
    item1 = CartItem("milk", "Organic Milk", "url1", 5.99)
    cart1.add_item(item1)
    
    state.add_platform_cart(cart1)
    
    # Test cart retrieval
    retrieved = state.get_cart("instacart")
    if retrieved is None:
        print("[FAIL] Could not retrieve cart from state")
        return False
    
    # Test diff recording
    state.record_diff("instacart", "remove", item1)
    pending = state.get_pending_diffs("instacart")
    
    if len(pending) != 1:
        print(f"[FAIL] Expected 1 pending diff, got {len(pending)}")
        return False
    
    # Test mark applied
    state.mark_diffs_applied("instacart")
    pending2 = state.get_pending_diffs("instacart")
    
    if len(pending2) != 0:
        print("[FAIL] Diffs not marked as applied")
        return False
    
    print("[PASS] CartState works correctly")
    return True

def test_cart_state_persistence():
    """Test CartState save/load"""
    print("\nTesting CartState persistence...")
    
    # Create state
    state = CartState()
    state.ingredients_requested = ["milk", "eggs", "bread"]
    
    cart = PlatformCart("instacart", 40)
    item = CartItem("milk", "Organic Milk", "url1", 5.99, quantity=2)
    cart.add_item(item)
    state.add_platform_cart(cart)
    
    state.record_diff("instacart", "add", item)
    
    # Save to file
    test_file = "data/test_cart_state.json"
    state.save_to_file(test_file)
    
    # Check file exists
    if not os.path.exists(test_file):
        print("[FAIL] Cart state file not created")
        return False
    
    # Load from file
    loaded_state = CartState.load_from_file(test_file)
    
    # Verify data
    if loaded_state.ingredients_requested != ["milk", "eggs", "bread"]:
        print("[FAIL] Ingredients not loaded correctly")
        return False
    
    loaded_cart = loaded_state.get_cart("instacart")
    if loaded_cart is None or len(loaded_cart.items) != 1:
        print("[FAIL] Cart items not loaded correctly")
        return False
    
    if len(loaded_state.diffs) != 1:
        print("[FAIL] Diffs not loaded correctly")
        return False
    
    # Cleanup
    os.remove(test_file)
    
    print("[PASS] CartState persistence works correctly")
    return True

def test_item_status_enum():
    """Test ItemStatus enum"""
    print("\nTesting ItemStatus enum...")
    
    # Test all statuses
    statuses = [ItemStatus.ADDED, ItemStatus.NOT_FOUND, ItemStatus.FAILED, ItemStatus.OUT_OF_STOCK]
    
    if len(statuses) != 4:
        print("[FAIL] Not all statuses defined")
        return False
    
    # Test enum values
    if ItemStatus.ADDED.value != "added":
        print("[FAIL] ItemStatus enum value incorrect")
        return False
    
    # Test enum in CartItem
    item = CartItem("milk", "Milk", "url", 5.99, status=ItemStatus.NOT_FOUND)
    if item.status != ItemStatus.NOT_FOUND:
        print("[FAIL] ItemStatus not set correctly in CartItem")
        return False
    
    print("[PASS] ItemStatus enum works correctly")
    return True

def main():
    """Run all Phase 2 tests"""
    print("=" * 70)
    print("PHASE 2 DELIVERABLE TESTS")
    print("=" * 70)
    
    tests = [
        ("CartItem", test_cart_item),
        ("PlatformCart", test_platform_cart),
        ("CartDiff", test_cart_diff),
        ("CartState", test_cart_state),
        ("CartState Persistence", test_cart_state_persistence),
        ("ItemStatus Enum", test_item_status_enum),
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
    print("PHASE 2 TEST RESULTS")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] ALL PHASE 2 TESTS PASSED - Ready for git commit")
        return True
    else:
        print("[FAILURE] SOME TESTS FAILED - Fix before committing")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

