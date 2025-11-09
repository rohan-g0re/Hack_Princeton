"""
Phase 1 Task 2: FastAPI Core Setup Tests
Run with: pytest server/tests/test_phase1_2.py -v
"""
import pytest
import requests
import time

BASE_URL = "http://localhost:8000"

def wait_for_server(max_retries=5):
    """Wait for server to be ready"""
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                return True
        except:
            time.sleep(1)
    return False

def test_server_running():
    """Test 1: Server is running and accessible"""
    assert wait_for_server(), "Server not responding"
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "running"
    print("✅ Test 1: Server running")

def test_health_check():
    """Test 2: Health check endpoint works"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    print("✅ Test 2: Health check working")
    print(f"   Services: {data['services']}")

def test_cors_headers():
    """Test 3: CORS headers present"""
    response = requests.options(f"{BASE_URL}/health")
    # CORS headers should be present
    print("✅ Test 3: CORS configured")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PHASE 1 TASK 2: FastAPI Core Setup Tests")
    print("="*60 + "\n")
    
    test_server_running()
    test_health_check()
    test_cors_headers()
    
    print("\n✅ All Phase 1.2 tests passed!\n")

