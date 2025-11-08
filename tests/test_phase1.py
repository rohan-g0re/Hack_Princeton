# tests/test_phase1.py
"""
Test Phase 1: Project Structure & Core Utilities

Deliverables:
- Directory structure created
- Configuration file with platform details
- Popup handler utility
- Retry decorator utility
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from config.platforms import PLATFORM_CONFIGS, BROWSER_ARGS, HEADLESS, MAX_RETRIES
        print("[PASS] Config imports successful")
        
        # Note: popup_handler needs playwright, but we're testing structure only in Phase 1
        try:
            from utils.popup_handler import CLOSE_SELECTORS
            print("[PASS] Popup handler imports successful")
        except ImportError:
            print("[NOTE] Popup handler needs playwright (install dependencies later)")
        
        from utils.retry_decorator import async_retry
        print("[PASS] Retry decorator imports successful")
        
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False

def test_config_structure():
    """Test configuration structure"""
    print("\nTesting configuration structure...")
    
    from config.platforms import PLATFORM_CONFIGS
    
    required_platforms = ["instacart", "ubereats", "doordash"]
    required_keys = ["name", "merchant_id", "search_url", "cart_url", "login_url", "user_data_dir"]
    
    for platform in required_platforms:
        if platform not in PLATFORM_CONFIGS:
            print(f"[FAIL] Platform {platform} not in config")
            return False
        
        for key in required_keys:
            if key not in PLATFORM_CONFIGS[platform]:
                print(f"[FAIL] Key {key} missing from {platform} config")
                return False
    
    print(f"[PASS] All {len(required_platforms)} platforms properly configured")
    print(f"   Platforms: {list(PLATFORM_CONFIGS.keys())}")
    return True

def test_popup_selectors():
    """Test popup handler has selectors"""
    print("\nTesting popup handler...")
    
    try:
        from utils.popup_handler import CLOSE_SELECTORS
        
        if len(CLOSE_SELECTORS) == 0:
            print("[FAIL] No close selectors defined")
            return False
        
        print(f"[PASS] Popup handler has {len(CLOSE_SELECTORS)} close selectors")
        return True
    except ImportError:
        print("[NOTE] Playwright not installed yet - skipping (will install in Phase 7)")
        return True  # Don't fail Phase 1 for missing dependencies

def test_retry_decorator():
    """Test retry decorator basic functionality"""
    print("\nTesting retry decorator...")
    
    import asyncio
    from utils.retry_decorator import async_retry
    
    # Test successful function
    @async_retry(max_attempts=2)
    async def success_func():
        return "success"
    
    # Test with failure then success
    call_count = {"value": 0}
    
    @async_retry(max_attempts=3, backoff_base=0.1)
    async def retry_func():
        call_count["value"] += 1
        if call_count["value"] < 2:
            raise ValueError("Test error")
        return "success"
    
    try:
        result1 = asyncio.run(success_func())
        if result1 != "success":
            print("[FAIL] Retry decorator changed return value")
            return False
        
        result2 = asyncio.run(retry_func())
        if result2 != "success" or call_count["value"] != 2:
            print(f"[FAIL] Retry decorator didn't retry correctly (calls: {call_count['value']})")
            return False
        
        print("[PASS] Retry decorator works correctly")
        return True
    except Exception as e:
        print(f"[FAIL] Retry decorator test failed: {e}")
        return False

def main():
    """Run all Phase 1 tests"""
    print("=" * 70)
    print("PHASE 1 DELIVERABLE TESTS")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration Structure", test_config_structure),
        ("Popup Selectors", test_popup_selectors),
        ("Retry Decorator", test_retry_decorator),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            results.append(test_func())
        except Exception as e:
            print(f"[FAIL] {test_name} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("PHASE 1 TEST RESULTS")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] ALL PHASE 1 TESTS PASSED - Ready for git commit")
        return True
    else:
        print("[FAILURE] SOME TESTS FAILED - Fix before committing")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

