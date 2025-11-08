# tests/test_phase6.py
"""
Test Phase 6: Main Entry Point

Deliverables:
- main.py with complete workflow orchestration
- CLI argument parsing for ingredients
- Logging configuration
- Step-by-step workflow execution
- Knot API integration for mock payment demo
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_main_file_exists():
    """Test main.py file exists"""
    print("Testing main.py file existence...")
    
    if os.path.exists("main.py"):
        print("[PASS] main.py file exists")
        return True
    else:
        print("[FAIL] main.py file missing")
        return False

def test_main_structure():
    """Test main.py has correct structure"""
    print("\nTesting main.py structure...")
    
    if not os.path.exists("main.py"):
        print("[FAIL] main.py file missing")
        return False
    
    with open("main.py", 'r') as f:
        content = f.read()
    
    required_elements = [
        "async def main()",
        "asyncio.run(main())",
        "ParallelOrchestrator",
        "run_search_and_order_all_platforms",
        "extract_cart_details_all_platforms",
        "apply_diffs_all_platforms",
        "get_knot_client",
        "logging.basicConfig"
    ]
    
    missing = []
    for element in required_elements:
        if element not in content:
            missing.append(element)
    
    if missing:
        print(f"[FAIL] Missing elements: {missing}")
        return False
    
    print(f"[PASS] All {len(required_elements)} required elements present")
    return True

def test_workflow_steps():
    """Test main.py implements all workflow steps"""
    print("\nTesting workflow steps...")
    
    with open("main.py", 'r') as f:
        content = f.read()
    
    # Check for 6 main steps
    steps = [
        "STEP 1",  # Get ingredients
        "STEP 2",  # Search & Order
        "STEP 3",  # Extract cart details
        "STEP 4",  # Simulate edits
        "STEP 5",  # Apply diffs (conditional)
        "STEP 6",  # Mock payment
    ]
    
    found_steps = []
    for i, step in enumerate(steps, 1):
        if step in content:
            found_steps.append(i)
    
    if len(found_steps) >= 5:  # At least 5 steps should be clearly marked
        print(f"[PASS] Workflow implements {len(found_steps)} steps")
        return True
    else:
        print(f"[FAIL] Only {len(found_steps)} steps found, expected at least 5")
        return False

def test_cli_argument_handling():
    """Test main.py handles CLI arguments"""
    print("\nTesting CLI argument handling...")
    
    with open("main.py", 'r') as f:
        content = f.read()
    
    if "sys.argv" in content:
        print("[PASS] CLI argument handling implemented")
        return True
    else:
        print("[FAIL] No CLI argument handling found")
        return False

def test_logging_configuration():
    """Test logging is configured"""
    print("\nTesting logging configuration...")
    
    with open("main.py", 'r') as f:
        content = f.read()
    
    if "logging.basicConfig" in content and "logger = logging.getLogger" in content:
        print("[PASS] Logging configured correctly")
        return True
    else:
        print("[FAIL] Logging not properly configured")
        return False

def test_orchestrator_integration():
    """Test main.py integrates with orchestrator"""
    print("\nTesting orchestrator integration...")
    
    with open("main.py", 'r') as f:
        content = f.read()
    
    orchestrator_calls = [
        "ParallelOrchestrator",
        "run_search_and_order_all_platforms",
        "extract_cart_details_all_platforms",
        "apply_diffs_all_platforms"
    ]
    
    missing = [call for call in orchestrator_calls if call not in content]
    
    if not missing:
        print(f"[PASS] All orchestrator methods called")
        return True
    else:
        print(f"[FAIL] Missing orchestrator calls: {missing}")
        return False

def test_knot_api_integration():
    """Test main.py integrates with Knot API"""
    print("\nTesting Knot API integration...")
    
    with open("main.py", 'r') as f:
        content = f.read()
    
    if "get_knot_client" in content and "sync_transactions" in content:
        print("[PASS] Knot API integration present")
        return True
    else:
        print("[FAIL] Knot API not integrated")
        return False

def test_cart_state_display():
    """Test main.py displays cart state"""
    print("\nTesting cart state display...")
    
    with open("main.py", 'r') as f:
        content = f.read()
    
    display_elements = [
        "INITIAL CART STATE",
        "FINAL CART STATE",
        "TOTAL ACROSS ALL PLATFORMS"
    ]
    
    found = [elem for elem in display_elements if elem in content]
    
    if len(found) >= 2:
        print(f"[PASS] Cart state display implemented ({len(found)}/3 sections)")
        return True
    else:
        print(f"[FAIL] Insufficient cart display sections ({len(found)}/3)")
        return False

def main():
    """Run all Phase 6 tests"""
    print("=" * 70)
    print("PHASE 6 DELIVERABLE TESTS")
    print("=" * 70)
    
    tests = [
        ("Main File Exists", test_main_file_exists),
        ("Main Structure", test_main_structure),
        ("Workflow Steps", test_workflow_steps),
        ("CLI Arguments", test_cli_argument_handling),
        ("Logging Configuration", test_logging_configuration),
        ("Orchestrator Integration", test_orchestrator_integration),
        ("Knot API Integration", test_knot_api_integration),
        ("Cart State Display", test_cart_state_display),
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
    print("PHASE 6 TEST RESULTS")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    print("\n[NOTE] Full workflow execution requires:")
    print("  - All dependencies installed (playwright, browser-use)")
    print("  - Platform sessions established")
    print("  - GEMINI_API_KEY in .env")
    print("  - Integration testing in Phase 7")
    
    if passed == total:
        print("\n[SUCCESS] ALL PHASE 6 TESTS PASSED - Ready for git commit")
        return True
    else:
        print("\n[FAILURE] SOME TESTS FAILED - Fix before committing")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

