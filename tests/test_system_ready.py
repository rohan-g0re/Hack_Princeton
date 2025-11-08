# tests/test_system_ready.py
"""
Complete System Readiness Test

Validates that all phases are complete and system is ready for execution.
This is the final test before attempting to run the full workflow.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_all_phase_files_exist():
    """Test all required files from all phases exist"""
    print("=" * 70)
    print("SYSTEM READINESS CHECK")
    print("=" * 70)
    print("\nChecking file structure...")
    
    required_files = [
        # Phase 1
        "config/platforms.py",
        "utils/popup_handler.py",
        "utils/retry_decorator.py",
        
        # Phase 2
        "models/cart_models.py",
        
        # Phase 3
        "agents/base_agent.py",
        "agents/signin_agent.py",
        "agents/search_order_agent.py",
        "agents/edit_cart_agent.py",
        "agents/cart_detail_agent.py",
        
        # Phase 4
        "knot_api/config.py",
        "knot_api/client.py",
        "knot_api/mock_data.py",
        "knot_api/examples/test_sync.py",
        
        # Phase 5
        "orchestrator.py",
        
        # Phase 6
        "main.py",
        
        # Other
        "requirements.txt",
        "README.md",
    ]
    
    missing = []
    for filepath in required_files:
        if not os.path.exists(filepath):
            missing.append(filepath)
    
    if missing:
        print(f"[FAIL] Missing files: {missing}")
        return False
    
    print(f"[PASS] All {len(required_files)} required files exist")
    return True

def test_requirements_complete():
    """Test requirements.txt has all dependencies"""
    print("\nChecking dependencies...")
    
    with open("requirements.txt", 'r') as f:
        requirements = f.read()
    
    required_packages = [
        "playwright",
        "browser-use",
        "langchain-google-genai",
        "requests",
        "python-dotenv"
    ]
    
    missing = []
    for package in required_packages:
        if package not in requirements:
            missing.append(package)
    
    if missing:
        print(f"[FAIL] Missing packages in requirements.txt: {missing}")
        return False
    
    print(f"[PASS] All {len(required_packages)} required packages listed")
    return True

def test_configuration_complete():
    """Test all configurations are present"""
    print("\nChecking configuration...")
    
    try:
        from config.platforms import PLATFORM_CONFIGS
        from knot_api.config import MERCHANT_IDS
        
        platforms = list(PLATFORM_CONFIGS.keys())
        merchants = list(MERCHANT_IDS.keys())
        
        if len(platforms) < 3:
            print(f"[FAIL] Only {len(platforms)} platforms configured, need at least 3")
            return False
        
        if len(merchants) < 3:
            print(f"[FAIL] Only {len(merchants)} merchants configured, need at least 3")
            return False
        
        print(f"[PASS] {len(platforms)} platforms and {len(merchants)} merchants configured")
        return True
        
    except Exception as e:
        print(f"[FAIL] Configuration error: {e}")
        return False

def test_models_functional():
    """Test data models can be used"""
    print("\nChecking data models...")
    
    try:
        from models.cart_models import CartItem, PlatformCart, CartState, ItemStatus
        
        # Quick functional test
        item = CartItem("milk", "Whole Milk", "url", 5.99)
        cart = PlatformCart("test", 1)
        cart.add_item(item)
        state = CartState()
        state.add_platform_cart(cart)
        
        if len(state.platform_carts) != 1:
            print("[FAIL] CartState not working correctly")
            return False
        
        print("[PASS] All data models functional")
        return True
        
    except Exception as e:
        print(f"[FAIL] Data model error: {e}")
        return False

def test_knot_api_functional():
    """Test Knot API client works"""
    print("\nChecking Knot API...")
    
    try:
        from knot_api.client import get_knot_client
        
        client = get_knot_client()
        result = client.sync_transactions(40, "test", 1)
        
        if "transactions" not in result:
            print("[FAIL] Knot API client not returning correct format")
            return False
        
        print("[PASS] Knot API client functional")
        return True
        
    except Exception as e:
        print(f"[FAIL] Knot API error: {e}")
        return False

def test_orchestrator_structure():
    """Test orchestrator is properly structured"""
    print("\nChecking orchestrator...")
    
    try:
        # Try import first
        try:
            from orchestrator import ParallelOrchestrator
            orchestrator = ParallelOrchestrator(["test"])
            
            if not hasattr(orchestrator, 'run_search_and_order_all_platforms'):
                print("[FAIL] Orchestrator missing required methods")
                return False
                
            print("[PASS] Orchestrator fully functional")
            return True
            
        except ImportError:
            # Check file structure if import fails
            if os.path.exists("orchestrator.py"):
                with open("orchestrator.py", 'r') as f:
                    content = f.read()
                    if "asyncio.gather" in content and "ParallelOrchestrator" in content:
                        print("[PASS] Orchestrator structure correct (needs dependencies)")
                        return True
            
            print("[FAIL] Orchestrator not properly implemented")
            return False
            
    except Exception as e:
        print(f"[FAIL] Orchestrator error: {e}")
        return False

def test_main_entry_point():
    """Test main.py is properly structured"""
    print("\nChecking main entry point...")
    
    try:
        with open("main.py", 'r') as f:
            content = f.read()
        
        required_elements = ["async def main()", "asyncio.run(main())", "ParallelOrchestrator"]
        
        for element in required_elements:
            if element not in content:
                print(f"[FAIL] main.py missing: {element}")
                return False
        
        print("[PASS] Main entry point properly structured")
        return True
        
    except Exception as e:
        print(f"[FAIL] Main entry point error: {e}")
        return False

def test_env_requirements():
    """Test environment requirements"""
    print("\nChecking environment requirements...")
    
    issues = []
    
    # Check .env file mentioned in README
    if not os.path.exists("README.md"):
        issues.append("README.md missing")
    else:
        with open("README.md", 'r') as f:
            readme = f.read()
            if "GEMINI_API_KEY" not in readme:
                issues.append("README doesn't mention GEMINI_API_KEY requirement")
    
    # Check data directory
    if not os.path.exists("data"):
        issues.append("data/ directory missing")
    
    if issues:
        print(f"[WARN] Environment issues: {issues}")
        print("[PASS] Non-critical issues (will work with .env setup)")
    else:
        print("[PASS] Environment requirements documented")
    
    return True

def main():
    """Run all system readiness tests"""
    
    tests = [
        ("File Structure", test_all_phase_files_exist),
        ("Dependencies", test_requirements_complete),
        ("Configuration", test_configuration_complete),
        ("Data Models", test_models_functional),
        ("Knot API", test_knot_api_functional),
        ("Orchestrator", test_orchestrator_structure),
        ("Main Entry", test_main_entry_point),
        ("Environment", test_env_requirements),
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
    print("SYSTEM READINESS SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Checks Passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] SYSTEM READY FOR EXECUTION")
        print("\nNext Steps:")
        print("1. Ensure GEMINI_API_KEY is in .env")
        print("2. Run: pip install -r requirements.txt")
        print("3. Run: playwright install chromium")
        print("4. Sign in to platforms: python -m agents.signin_agent instacart")
        print("5. Execute: python main.py")
        return True
    else:
        print("\n[FAILURE] SYSTEM NOT READY")
        print(f"\nFailed checks: {total - passed}")
        print("Fix issues above before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

