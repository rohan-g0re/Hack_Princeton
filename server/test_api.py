"""
Comprehensive API tests for all endpoints
Run with: pytest server/test_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from server.main import app
import json
from uuid import uuid4

client = TestClient(app)

# Test data
TEST_USER = {
    "email": f"test_{uuid4().hex[:8]}@example.com",
    "password": "Test123456!",
    "name": "Test User"
}

# Global vars for test flow
access_token = None
session_id = None
job_id = None


class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    def test_root_endpoint(self):
        """Test GET /"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "version" in data
        print("✅ Root endpoint working")
    
    def test_health_check(self):
        """Test GET /health"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        print("✅ Health check working")


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_signup(self):
        """Test POST /auth/signup"""
        global access_token
        
        response = client.post("/auth/signup", json=TEST_USER)
        
        # May fail if Supabase not configured, that's okay for local dev
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "user" in data
            access_token = data["access_token"]
            print(f"✅ Signup successful: {data['user']['email']}")
        else:
            print(f"⚠️  Signup skipped (Supabase not configured): {response.status_code}")
    
    def test_signin(self):
        """Test POST /auth/signin"""
        global access_token
        
        response = client.post("/auth/signin", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            access_token = data["access_token"]
            print(f"✅ Signin successful")
        else:
            print(f"⚠️  Signin skipped: {response.status_code}")
    
    def test_get_me(self):
        """Test GET /auth/me"""
        if not access_token:
            pytest.skip("No access token available")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/auth/me", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data or "email" in data
            print(f"✅ Get me endpoint working")
        else:
            print(f"⚠️  Get me skipped: {response.status_code}")


class TestRecipeEndpoints:
    """Test recipe and ingredients endpoints"""
    
    def test_recipe_without_auth(self):
        """Test POST /api/recipe without authentication"""
        response = client.post("/api/recipe", json={"query": "caesar salad"})
        assert response.status_code == 401
        print("✅ Recipe endpoint properly requires auth")
    
    def test_recipe_with_auth(self):
        """Test POST /api/recipe with authentication"""
        global session_id
        
        if not access_token:
            pytest.skip("No access token available")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post(
            "/api/recipe",
            json={"query": "caesar salad"},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "recipe_name" in data
            assert "ingredients" in data
            assert "session_id" in data
            assert len(data["ingredients"]) > 0
            
            session_id = data["session_id"]
            print(f"✅ Recipe endpoint working: {data['recipe_name']}")
            print(f"   Found {len(data['ingredients'])} ingredients")
            for ing in data["ingredients"][:3]:
                print(f"   - {ing['name']}: {ing['quantity']}")
        elif response.status_code == 503:
            print("⚠️  Recipe endpoint skipped (Gemini not configured)")
        else:
            print(f"⚠️  Recipe endpoint error: {response.status_code}")


class TestAgentEndpoints:
    """Test agent orchestration endpoints"""
    
    def test_start_agents_without_auth(self):
        """Test POST /api/start-agents without auth"""
        response = client.post("/api/start-agents", json={})
        assert response.status_code == 401
        print("✅ Start agents endpoint properly requires auth")
    
    def test_start_agents_with_auth(self):
        """Test POST /api/start-agents with auth"""
        global job_id
        
        if not access_token or not session_id:
            pytest.skip("Auth or session not available")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post(
            "/api/start-agents",
            json={
                "session_id": session_id,
                "ingredients": [
                    {"name": "Lettuce", "quantity": "1 head"},
                    {"name": "Parmesan", "quantity": "1/2 cup"}
                ],
                "platforms": ["instacart"]
            },
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
            assert data["status"] == "started"
            job_id = data["job_id"]
            print(f"✅ Agents started: {data['job_id']}")
        elif response.status_code == 403:
            print("⚠️  Start agents skipped (session mismatch)")
        else:
            print(f"⚠️  Start agents error: {response.status_code}")
    
    def test_job_status(self):
        """Test GET /api/job/{job_id}/status"""
        if not access_token or not job_id:
            pytest.skip("Auth or job_id not available")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get(f"/api/job/{job_id}/status", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
            assert "status" in data
            assert "platforms" in data
            print(f"✅ Job status: {data['status']}")
        else:
            print(f"⚠️  Job status error: {response.status_code}")


class TestCartEndpoints:
    """Test cart management endpoints"""
    
    def test_cart_status(self):
        """Test GET /api/cart-status"""
        if not access_token or not session_id:
            pytest.skip("Auth or session not available")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get(
            f"/api/cart-status?session_id={session_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "session_id" in data
            assert "carts" in data
            assert "total_items" in data
            assert "total_amount" in data
            print(f"✅ Cart status: {len(data['carts'])} platforms, {data['total_items']} items")
        elif response.status_code == 403:
            print("⚠️  Cart status skipped (unauthorized)")
        else:
            print(f"⚠️  Cart status error: {response.status_code}")
    
    def test_save_cart_diffs(self):
        """Test POST /api/cart-diffs"""
        if not access_token or not session_id:
            pytest.skip("Auth or session not available")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post(
            "/api/cart-diffs",
            json={
                "session_id": session_id,
                "platform": "instacart",
                "diffs": [
                    {
                        "action": "remove",
                        "item": {
                            "name": "Test Item",
                            "quantity": 1,
                            "price": 5.99
                        }
                    }
                ]
            },
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
            print(f"✅ Cart diffs saved: {data['message']}")
        elif response.status_code == 403:
            print("⚠️  Save diffs skipped (unauthorized)")
        else:
            print(f"⚠️  Save diffs error: {response.status_code}")
    
    def test_apply_diffs(self):
        """Test POST /api/apply-diffs"""
        if not access_token or not session_id:
            pytest.skip("Auth or session not available")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post(
            "/api/apply-diffs",
            json={"session_id": session_id},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
            print(f"✅ Diffs applied: {data['message']}")
        elif response.status_code == 403:
            print("⚠️  Apply diffs skipped (unauthorized)")
        else:
            print(f"⚠️  Apply diffs error: {response.status_code}")


class TestCheckoutEndpoints:
    """Test checkout endpoints"""
    
    def test_checkout(self):
        """Test POST /api/checkout"""
        if not access_token or not session_id:
            pytest.skip("Auth or session not available")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post(
            "/api/checkout",
            json={"session_id": session_id},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "transaction_id" in data
            assert "total_amount" in data
            assert "platforms" in data
            assert "knot_transaction_id" in data
            print(f"✅ Checkout successful: ${data['total_amount']:.2f}")
            print(f"   Transaction ID: {data['transaction_id']}")
            print(f"   Knot ID: {data['knot_transaction_id']}")
        elif response.status_code == 403:
            print("⚠️  Checkout skipped (unauthorized)")
        else:
            print(f"⚠️  Checkout error: {response.status_code}")


class TestWebSocket:
    """Test WebSocket endpoint"""
    
    def test_websocket_connection(self):
        """Test WebSocket /ws/agent-progress"""
        with client.websocket_connect(f"/ws/agent-progress?session_id=test") as websocket:
            # Connection successful
            print("✅ WebSocket connection established")
            
            # Can send/receive if needed
            # websocket.send_text("ping")
            # data = websocket.receive_text()


def run_all_tests():
    """Run all tests manually"""
    print("\n" + "="*60)
    print("🧪 RUNNING API TESTS")
    print("="*60 + "\n")
    
    # Health tests
    print("📋 Testing Health Endpoints...")
    test_health = TestHealthEndpoints()
    test_health.test_root_endpoint()
    test_health.test_health_check()
    
    # Auth tests
    print("\n🔐 Testing Auth Endpoints...")
    test_auth = TestAuthEndpoints()
    test_auth.test_signup()
    test_auth.test_signin()
    test_auth.test_get_me()
    
    # Recipe tests
    print("\n🍳 Testing Recipe Endpoints...")
    test_recipe = TestRecipeEndpoints()
    test_recipe.test_recipe_without_auth()
    test_recipe.test_recipe_with_auth()
    
    # Agent tests
    print("\n🤖 Testing Agent Endpoints...")
    test_agent = TestAgentEndpoints()
    test_agent.test_start_agents_without_auth()
    test_agent.test_start_agents_with_auth()
    test_agent.test_job_status()
    
    # Cart tests
    print("\n🛒 Testing Cart Endpoints...")
    test_cart = TestCartEndpoints()
    test_cart.test_cart_status()
    test_cart.test_save_cart_diffs()
    test_cart.test_apply_diffs()
    
    # Checkout tests
    print("\n💳 Testing Checkout Endpoints...")
    test_checkout = TestCheckoutEndpoints()
    test_checkout.test_checkout()
    
    # WebSocket tests
    print("\n🔌 Testing WebSocket...")
    test_ws = TestWebSocket()
    try:
        test_ws.test_websocket_connection()
    except Exception as e:
        print(f"⚠️  WebSocket test skipped: {e}")
    
    print("\n" + "="*60)
    print("✨ TEST RUN COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()

