# Grocery Super-App Implementation Plan
## Complete Phased Development with Test Deliverables

---

## 🎯 Project Overview
Build a multi-platform grocery ordering super-app with React Native Expo frontend and FastAPI backend, using Supabase for data/auth and browser automation agents for cart management.

---

## Phase 1: Backend Foundation & Infrastructure
**Goal:** Set up and test all backend services independently

### Task 1.1: Supabase Database Setup
**Deliverables:**
- [ ] Supabase project created
- [ ] Schema applied (user_sessions, cart_states, cart_diffs, transactions)
- [ ] Test user created
- [ ] RLS policies configured

**Test Suite 1.1:**
```sql
-- Test 1: Verify tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('user_sessions', 'cart_states', 'cart_diffs', 'transactions');

-- Test 2: Insert test session
INSERT INTO user_sessions (user_id, recipe_query, ingredients) 
VALUES ('test-uuid', 'test recipe', '[]'::jsonb);

-- Test 3: Verify foreign key constraints work
INSERT INTO cart_states (session_id, platform, items) 
VALUES ((SELECT id FROM user_sessions LIMIT 1), 'instacart', '[]'::jsonb);

-- Test 4: Clean up test data
DELETE FROM cart_states WHERE platform = 'instacart';
DELETE FROM user_sessions WHERE recipe_query = 'test recipe';
```

**Exit Criteria:**
✅ All 4 tables created
✅ Can insert/query test data
✅ Foreign keys working
✅ Test user can authenticate

---

### Task 1.2: FastAPI Core Setup
**Deliverables:**
- [ ] server/ folder structure created
- [ ] requirements.txt with dependencies
- [ ] .env.example file
- [ ] Main FastAPI app with CORS
- [ ] Health check endpoint working
- [ ] Supabase client initialized

**Test Suite 1.2:**
```bash
# Test 1: Install dependencies
cd server
pip install -r requirements.txt

# Test 2: Start server
python -m uvicorn server.main:app --reload --port 8000

# Test 3: Health check (in another terminal)
curl http://localhost:8000/health

# Test 4: Root endpoint
curl http://localhost:8000/

# Expected: Both return 200 OK with JSON
```

**Python Test Script:**
```python
# server/tests/test_phase1_2.py
import requests

def test_server_running():
    response = requests.get("http://localhost:8000/")
    assert response.status_code == 200
    assert "status" in response.json()

def test_health_check():
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
```

**Exit Criteria:**
✅ Server starts without errors
✅ Health endpoint returns 200
✅ Supabase connection confirmed
✅ CORS configured

---

### Task 1.3: Authentication Endpoints
**Deliverables:**
- [ ] POST /auth/signup endpoint
- [ ] POST /auth/signin endpoint
- [ ] GET /auth/me endpoint
- [ ] JWT token verification working
- [ ] Supabase auth integration

**Test Suite 1.3:**
```python
# server/tests/test_phase1_3.py
import requests
import pytest

BASE_URL = "http://localhost:8000"
test_email = f"test_{uuid4().hex[:8]}@example.com"
test_password = "Test123456!"
access_token = None

def test_signup():
    global access_token
    response = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": test_email,
        "password": test_password,
        "name": "Test User"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    access_token = data["access_token"]
    print(f"✅ Signup successful: {data['user']['email']}")

def test_signin():
    global access_token
    response = requests.post(f"{BASE_URL}/auth/signin", json={
        "email": test_email,
        "password": test_password
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    access_token = data["access_token"]
    print("✅ Signin successful")

def test_get_me():
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "email" in data or "user_id" in data
    print("✅ Get me working")

def test_invalid_token():
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert response.status_code == 401
    print("✅ Invalid token properly rejected")
```

**Exit Criteria:**
✅ Can create new user
✅ Can sign in existing user
✅ JWT token validates correctly
✅ Invalid tokens rejected

---

### Task 1.4: Gemini Recipe Service
**Deliverables:**
- [ ] GeminiService class implemented
- [ ] Recipe to ingredients conversion working
- [ ] POST /api/recipe endpoint
- [ ] Session created in DB on recipe request

**Test Suite 1.4:**
```python
# server/tests/test_phase1_4.py
import requests

BASE_URL = "http://localhost:8000"
access_token = "your_token_here"  # From previous tests

def test_recipe_endpoint():
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(
        f"{BASE_URL}/api/recipe",
        json={"query": "caesar salad"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "recipe_name" in data
    assert "ingredients" in data
    assert "session_id" in data
    assert len(data["ingredients"]) > 0
    
    print(f"✅ Recipe: {data['recipe_name']}")
    print(f"✅ Ingredients: {len(data['ingredients'])}")
    for ing in data["ingredients"][:3]:
        print(f"   - {ing['name']}: {ing['quantity']}")
    
    return data["session_id"]

def test_session_in_database(session_id):
    # Verify session was created in Supabase
    # Query via Supabase client
    from server.supabase_client import SupabaseClient
    client = SupabaseClient.get_client()
    result = client.table("user_sessions").select("*").eq("id", session_id).execute()
    assert len(result.data) == 1
    assert result.data[0]["recipe_query"] is not None
    print("✅ Session stored in database")
```

**Exit Criteria:**
✅ Gemini API responds with ingredients
✅ Recipe endpoint returns structured data
✅ Session saved to database
✅ Auth required for recipe endpoint

---

## Phase 2: Agent Integration & WebSocket
**Goal:** Connect browser automation agents and enable real-time progress

### Task 2.1: Agent Runner Implementation
**Deliverables:**
- [ ] AgentRunner class with subprocess management
- [ ] Shopping list JSON generation
- [ ] Agent output parsing
- [ ] Job status tracking

**Test Suite 2.1:**
```python
# server/tests/test_phase2_1.py
from server.agent_runner import AgentRunner
from server.models import IngredientItem
from pathlib import Path
import asyncio

async def test_agent_runner_init():
    runner = AgentRunner(Path("server"))
    assert runner.agents_dir.exists()
    print("✅ AgentRunner initialized")

async def test_job_creation():
    runner = AgentRunner(Path("server"))
    ingredients = [
        IngredientItem(name="Lettuce", quantity="1 head"),
        IngredientItem(name="Parmesan", quantity="1/2 cup")
    ]
    job_id = await runner.run_agents("test-session", ingredients, ["instacart"])
    
    assert job_id is not None
    assert job_id in runner.jobs
    print(f"✅ Job created: {job_id}")
    
    # Wait for job completion (or timeout)
    for i in range(60):
        await asyncio.sleep(1)
        status = runner.get_job_status(job_id)
        print(f"Job status: {status['status']}")
        if status["status"] in ["completed", "failed"]:
            break
    
    final_status = runner.get_job_status(job_id)
    print(f"✅ Final job status: {final_status}")
```

**Exit Criteria:**
✅ AgentRunner can spawn subprocesses
✅ Shopping list JSON created
✅ Job status tracked correctly
✅ Agent output captured

---

### Task 2.2: WebSocket Manager
**Deliverables:**
- [ ] ConnectionManager class
- [ ] WebSocket endpoint at /ws/agent-progress
- [ ] Session-based connection tracking
- [ ] Message broadcasting to sessions

**Test Suite 2.2:**
```python
# server/tests/test_phase2_2.py
import asyncio
import websockets
import json

async def test_websocket_connection():
    uri = "ws://localhost:8000/ws/agent-progress?session_id=test-session"
    
    async with websockets.connect(uri) as websocket:
        print("✅ WebSocket connected")
        
        # Wait for messages (with timeout)
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)
            print(f"✅ Received message: {data}")
        except asyncio.TimeoutError:
            print("⚠️  No message received (expected for idle connection)")

async def test_websocket_multiple_clients():
    uri = "ws://localhost:8000/ws/agent-progress?session_id=test-session-2"
    
    async with websockets.connect(uri) as ws1:
        async with websockets.connect(uri) as ws2:
            print("✅ Multiple WebSocket clients connected")
            # Both should receive broadcasts
```

**Exit Criteria:**
✅ WebSocket accepts connections
✅ Messages can be sent to specific sessions
✅ Multiple clients per session supported
✅ Connections cleaned up properly

---

### Task 2.3: Agent Orchestration Endpoints
**Deliverables:**
- [ ] POST /api/start-agents endpoint
- [ ] GET /api/job/{job_id}/status endpoint
- [ ] Agent progress sent via WebSocket
- [ ] Cart data stored in database

**Test Suite 2.3:**
```python
# server/tests/test_phase2_3.py
import requests
import websockets
import asyncio
import json

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def test_start_agents_flow():
    # 1. Get session_id from recipe endpoint
    headers = {"Authorization": f"Bearer {access_token}"}
    recipe_resp = requests.post(
        f"{BASE_URL}/api/recipe",
        json={"query": "simple salad"},
        headers=headers
    )
    session_id = recipe_resp.json()["session_id"]
    ingredients = recipe_resp.json()["ingredients"]
    
    # 2. Connect WebSocket BEFORE starting agents
    ws_uri = f"{WS_URL}/ws/agent-progress?session_id={session_id}"
    
    async with websockets.connect(ws_uri) as websocket:
        print("✅ WebSocket connected")
        
        # 3. Start agents
        agent_resp = requests.post(
            f"{BASE_URL}/api/start-agents",
            json={
                "session_id": session_id,
                "ingredients": ingredients[:2],  # First 2 items
                "platforms": ["instacart"]
            },
            headers=headers
        )
        assert agent_resp.status_code == 200
        job_id = agent_resp.json()["job_id"]
        print(f"✅ Agents started: {job_id}")
        
        # 4. Listen for WebSocket updates
        updates_received = []
        try:
            while True:
                message = await asyncio.wait_for(websocket.recv(), timeout=120.0)
                data = json.loads(message)
                updates_received.append(data)
                print(f"📡 Update: {data}")
                
                if data.get("type") == "job_completed":
                    break
        except asyncio.TimeoutError:
            print("⏱️  Timeout waiting for job completion")
        
        # 5. Verify updates received
        assert len(updates_received) > 0
        print(f"✅ Received {len(updates_received)} updates")
        
        # 6. Check final job status
        status_resp = requests.get(
            f"{BASE_URL}/api/job/{job_id}/status",
            headers=headers
        )
        assert status_resp.status_code == 200
        final_status = status_resp.json()
        print(f"✅ Final status: {final_status}")
```

**Exit Criteria:**
✅ Agents start successfully
✅ WebSocket receives progress updates
✅ Job status endpoint works
✅ Agent completion detected

---

## Phase 3: Cart Management & Diffs
**Goal:** Implement cart viewing, editing, and diff tracking

### Task 3.1: Cart Status Endpoint
**Deliverables:**
- [ ] GET /api/cart-status endpoint
- [ ] Cart data aggregation from DB
- [ ] Multi-platform cart support
- [ ] Total calculation

**Test Suite 3.1:**
```python
# server/tests/test_phase3_1.py
import requests

BASE_URL = "http://localhost:8000"

def test_cart_status_empty():
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{BASE_URL}/api/cart-status?session_id={session_id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "carts" in data
    assert "total_items" in data
    assert "total_amount" in data
    print(f"✅ Cart status: {len(data['carts'])} platforms")

def test_cart_status_with_data(session_id_with_cart):
    # After agents have run
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{BASE_URL}/api/cart-status?session_id={session_id_with_cart}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["carts"]) > 0
    assert data["total_items"] > 0
    assert data["total_amount"] > 0
    
    for cart in data["carts"]:
        print(f"✅ {cart['platform']}: {cart['item_count']} items, ${cart['subtotal']:.2f}")
```

**Exit Criteria:**
✅ Returns cart data for session
✅ Aggregates multiple platforms
✅ Calculates totals correctly
✅ Returns empty for new sessions

---

### Task 3.2: Cart Diff Tracking
**Deliverables:**
- [ ] POST /api/cart-diffs endpoint
- [ ] Diff storage in database
- [ ] Support add/remove actions
- [ ] Applied flag tracking

**Test Suite 3.2:**
```python
# server/tests/test_phase3_2.py
import requests

def test_save_cart_diffs():
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(
        f"{BASE_URL}/api/cart-diffs",
        json={
            "session_id": session_id,
            "platform": "instacart",
            "diffs": [
                {
                    "action": "remove",
                    "item": {
                        "name": "Lettuce",
                        "quantity": 1,
                        "price": 3.99
                    }
                },
                {
                    "action": "add",
                    "item": {
                        "name": "Extra Parmesan",
                        "quantity": 1,
                        "price": 5.99
                    }
                }
            ]
        },
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"✅ {data['message']}")

def test_diffs_in_database():
    from server.supabase_client import SupabaseClient
    client = SupabaseClient.get_client()
    result = client.table("cart_diffs")\
        .select("*")\
        .eq("session_id", session_id)\
        .eq("applied", False)\
        .execute()
    
    assert len(result.data) == 2
    print(f"✅ {len(result.data)} diffs stored in DB")
```

**Exit Criteria:**
✅ Can save cart diffs
✅ Diffs stored in database
✅ Multiple diffs per session supported
✅ Applied flag defaults to false

---

### Task 3.3: Apply Diffs Endpoint
**Deliverables:**
- [ ] POST /api/apply-diffs endpoint
- [ ] Mark diffs as applied
- [ ] (Future: Trigger edit cart agents)

**Test Suite 3.3:**
```python
# server/tests/test_phase3_3.py
def test_apply_diffs():
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(
        f"{BASE_URL}/api/apply-diffs",
        json={"session_id": session_id},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"✅ {data['message']}")

def test_diffs_marked_applied():
    from server.supabase_client import SupabaseClient
    client = SupabaseClient.get_client()
    result = client.table("cart_diffs")\
        .select("*")\
        .eq("session_id", session_id)\
        .eq("applied", True)\
        .execute()
    
    assert len(result.data) > 0
    print(f"✅ {len(result.data)} diffs marked as applied")
```

**Exit Criteria:**
✅ Diffs marked as applied
✅ No errors on empty diffs
✅ Returns success message

---

## Phase 4: Checkout & Transactions
**Goal:** Implement checkout flow with mock payments

### Task 4.1: Checkout Endpoint
**Deliverables:**
- [ ] POST /api/checkout endpoint
- [ ] Cart totals aggregation
- [ ] Transaction record creation
- [ ] Mock Knot API integration

**Test Suite 4.1:**
```python
# server/tests/test_phase4_1.py
def test_checkout_flow():
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(
        f"{BASE_URL}/api/checkout",
        json={"session_id": session_id},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "transaction_id" in data
    assert "total_amount" in data
    assert "platforms" in data
    assert "knot_transaction_id" in data
    assert "created_at" in data
    
    print(f"✅ Transaction ID: {data['transaction_id']}")
    print(f"✅ Total: ${data['total_amount']:.2f}")
    print(f"✅ Knot ID: {data['knot_transaction_id']}")
    
    for platform in data["platforms"]:
        print(f"   - {platform['platform']}: ${platform['subtotal']:.2f}")

def test_transaction_in_database():
    from server.supabase_client import SupabaseClient
    client = SupabaseClient.get_client()
    result = client.table("transactions")\
        .select("*")\
        .eq("session_id", session_id)\
        .execute()
    
    assert len(result.data) == 1
    transaction = result.data[0]
    assert transaction["total_amount"] > 0
    assert transaction["knot_transaction_id"] is not None
    print("✅ Transaction stored in database")
```

**Exit Criteria:**
✅ Checkout creates transaction
✅ Total calculated correctly
✅ Mock Knot ID generated
✅ Transaction saved to DB

---

## Phase 5: Mobile App Foundation
**Goal:** Set up React Native Expo app with navigation and auth

### Task 5.1: Expo App Scaffold
**Deliverables:**
- [ ] mobile/ folder created
- [ ] package.json with Beat_Fitness versions
- [ ] app.json configured
- [ ] TypeScript + Babel configured
- [ ] App runs on simulator/device

**Test Suite 5.1:**
```bash
# Test 1: Initialize project structure
cd mobile
npm install

# Test 2: Start Expo
npx expo start

# Test 3: Build check
npx expo prebuild --clean

# Test 4: Type check
npx tsc --noEmit
```

**Exit Criteria:**
✅ App starts without errors
✅ TypeScript compiles
✅ Can view on iOS/Android
✅ Hot reload works

---

### Task 5.2: Supabase Client & Auth Setup
**Deliverables:**
- [ ] Supabase client initialized
- [ ] Auth context provider
- [ ] Sign up screen
- [ ] Sign in screen
- [ ] Session persistence

**Test Suite 5.2:**
**Manual Test Checklist:**
- [ ] Open app → shows sign in screen
- [ ] Click "Sign Up" → form appears
- [ ] Enter email/password → successfully creates user
- [ ] App navigates to main screen
- [ ] Close and reopen app → still logged in
- [ ] Click logout → returns to sign in
- [ ] Sign in with same credentials → works

**Exit Criteria:**
✅ Can create new account
✅ Can sign in
✅ Session persists across restarts
✅ Can log out

---

### Task 5.3: Navigation Structure
**Deliverables:**
- [ ] React Navigation installed
- [ ] Auth stack (Sign In, Sign Up)
- [ ] App stack (Home, Recipe Input, etc.)
- [ ] Tab navigation (if needed)
- [ ] Navigation working between screens

**Test Suite 5.3:**
**Manual Test Checklist:**
- [ ] Auth screens accessible when logged out
- [ ] Main screens accessible when logged in
- [ ] Can navigate forward/back
- [ ] Deep linking works (optional)
- [ ] No navigation errors in console

**Exit Criteria:**
✅ All screens reachable
✅ Navigation smooth
✅ Auth-protected routes work
✅ Back button behaves correctly

---

## Phase 6: Mobile Core Features
**Goal:** Implement recipe input, ingredient selection, and agent progress

### Task 6.1: Recipe Input Screen
**Deliverables:**
- [ ] Text input for recipe query
- [ ] "Get Ingredients" button
- [ ] API call to /api/recipe
- [ ] Loading state
- [ ] Error handling
- [ ] Navigate to ingredients screen

**Test Suite 6.1:**
**Manual Test Checklist:**
- [ ] Enter "caesar salad" → click button
- [ ] Loading indicator appears
- [ ] Ingredients list displays
- [ ] Can see recipe name
- [ ] Navigates to ingredients screen
- [ ] Error shown if API fails
- [ ] Auth token sent correctly

**Automated Test:**
```javascript
// mobile/__tests__/RecipeInputScreen.test.tsx
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import RecipeInputScreen from '../src/screens/RecipeInputScreen';

test('submits recipe query', async () => {
  const { getByPlaceholderText, getByText } = render(<RecipeInputScreen />);
  
  const input = getByPlaceholderText('Enter recipe...');
  fireEvent.changeText(input, 'caesar salad');
  
  const button = getByText('Get Ingredients');
  fireEvent.press(button);
  
  await waitFor(() => {
    // Verify API called or navigation occurred
  });
});
```

**Exit Criteria:**
✅ Input accepts text
✅ API call successful
✅ Ingredients displayed
✅ Error handling works

---

### Task 6.2: Ingredients Selection Screen
**Deliverables:**
- [ ] List of ingredients with checkboxes
- [ ] Can add/remove ingredients
- [ ] "Start Shopping" button
- [ ] Platform selection (Instacart, UberEats)
- [ ] Triggers agent orchestration

**Test Suite 6.2:**
**Manual Test Checklist:**
- [ ] All ingredients shown with quantities
- [ ] Can uncheck unwanted ingredients
- [ ] Selected count updates
- [ ] Platform toggles work
- [ ] "Start Shopping" enabled when valid
- [ ] Navigates to progress screen
- [ ] Agents start successfully

**Exit Criteria:**
✅ Can modify ingredient list
✅ Platform selection works
✅ Triggers /api/start-agents
✅ Navigates to next screen

---

### Task 6.3: Agent Progress Screen
**Deliverables:**
- [ ] WebSocket connection to /ws/agent-progress
- [ ] Real-time progress indicators
- [ ] Platform status cards
- [ ] Progress percentage or spinner
- [ ] Navigate to cart status when complete

**Test Suite 6.3:**
**Manual Test Checklist:**
- [ ] WebSocket connects on mount
- [ ] Progress updates appear in real-time
- [ ] Platform statuses update (running/completed/failed)
- [ ] Shows completion message
- [ ] Auto-navigates when all agents done
- [ ] WebSocket disconnects on unmount

**Automated Test:**
```javascript
// mobile/__tests__/AgentProgressScreen.test.tsx
import { render, waitFor } from '@testing-library/react-native';
import AgentProgressScreen from '../src/screens/AgentProgressScreen';

test('displays agent progress updates', async () => {
  const { getByText } = render(<AgentProgressScreen />);
  
  await waitFor(() => {
    expect(getByText(/instacart/i)).toBeTruthy();
  });
});
```

**Exit Criteria:**
✅ WebSocket connects successfully
✅ Real-time updates display
✅ Completion detected
✅ Navigation triggered

---

## Phase 7: Cart Management & Checkout
**Goal:** Display carts, handle diffs, and complete checkout

### Task 7.1: Cart Status Screen
**Deliverables:**
- [ ] Platform cards showing carts
- [ ] Expandable item lists
- [ ] Item prices and quantities
- [ ] Add/Remove item actions
- [ ] Diff tracking
- [ ] "Proceed to Checkout" button

**Test Suite 7.1:**
**Manual Test Checklist:**
- [ ] All platform carts displayed
- [ ] Can expand/collapse each cart
- [ ] Items show name, quantity, price, size
- [ ] Can remove items (records diff)
- [ ] Total updates when items removed
- [ ] "Proceed" button enabled

**Exit Criteria:**
✅ Carts display correctly
✅ Expand/collapse works
✅ Item removal records diffs
✅ Totals accurate

---

### Task 7.2: Checkout Screen
**Deliverables:**
- [ ] Final cart summary
- [ ] Total amount display
- [ ] Platform breakdown
- [ ] "Apply Changes" button (if diffs exist)
- [ ] "Pay Now" button
- [ ] Mock payment confirmation

**Test Suite 7.2:**
**Manual Test Checklist:**
- [ ] Shows all selected items
- [ ] Displays platform subtotals
- [ ] Shows grand total
- [ ] "Apply Changes" applies diffs
- [ ] "Pay Now" calls /api/checkout
- [ ] Success screen with transaction ID
- [ ] Can view transaction details

**Exit Criteria:**
✅ Checkout summary accurate
✅ Diffs applied if present
✅ Payment successful
✅ Transaction ID shown

---

## Phase 8: Integration Testing & Polish
**Goal:** End-to-end testing and UI improvements

### Task 8.1: Complete E2E Flow Test
**Deliverables:**
- [ ] Full user flow documented
- [ ] E2E test script
- [ ] All phases tested together

**Test Suite 8.1:**
**Complete E2E Test:**
```python
# tests/test_e2e_complete.py

async def test_complete_user_flow():
    """Test entire flow from signup to checkout"""
    
    # 1. Sign up new user
    signup_resp = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": f"e2e_{uuid4().hex[:8]}@example.com",
        "password": "Test123456!",
        "name": "E2E Test User"
    })
    assert signup_resp.status_code == 200
    token = signup_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 1. User signed up")
    
    # 2. Get recipe ingredients
    recipe_resp = requests.post(
        f"{BASE_URL}/api/recipe",
        json={"query": "caesar salad"},
        headers=headers
    )
    assert recipe_resp.status_code == 200
    session_id = recipe_resp.json()["session_id"]
    ingredients = recipe_resp.json()["ingredients"]
    print(f"✅ 2. Recipe parsed: {len(ingredients)} ingredients")
    
    # 3. Start agents with WebSocket
    ws_uri = f"ws://localhost:8000/ws/agent-progress?session_id={session_id}"
    async with websockets.connect(ws_uri) as websocket:
        print("✅ 3. WebSocket connected")
        
        agent_resp = requests.post(
            f"{BASE_URL}/api/start-agents",
            json={
                "session_id": session_id,
                "ingredients": ingredients[:3],
                "platforms": ["instacart"]
            },
            headers=headers
        )
        assert agent_resp.status_code == 200
        job_id = agent_resp.json()["job_id"]
        print(f"✅ 4. Agents started: {job_id}")
        
        # Wait for completion
        while True:
            message = await asyncio.wait_for(websocket.recv(), timeout=180.0)
            data = json.loads(message)
            if data.get("type") == "job_completed":
                print("✅ 5. Agents completed")
                break
    
    # 6. Check cart status
    cart_resp = requests.get(
        f"{BASE_URL}/api/cart-status?session_id={session_id}",
        headers=headers
    )
    assert cart_resp.status_code == 200
    cart_data = cart_resp.json()
    assert len(cart_data["carts"]) > 0
    print(f"✅ 6. Cart has {cart_data['total_items']} items")
    
    # 7. Save cart diffs (remove one item)
    diff_resp = requests.post(
        f"{BASE_URL}/api/cart-diffs",
        json={
            "session_id": session_id,
            "platform": "instacart",
            "diffs": [{"action": "remove", "item": cart_data["carts"][0]["items"][0]}]
        },
        headers=headers
    )
    assert diff_resp.status_code == 200
    print("✅ 7. Cart diff saved")
    
    # 8. Apply diffs
    apply_resp = requests.post(
        f"{BASE_URL}/api/apply-diffs",
        json={"session_id": session_id},
        headers=headers
    )
    assert apply_resp.status_code == 200
    print("✅ 8. Diffs applied")
    
    # 9. Checkout
    checkout_resp = requests.post(
        f"{BASE_URL}/api/checkout",
        json={"session_id": session_id},
        headers=headers
    )
    assert checkout_resp.status_code == 200
    transaction = checkout_resp.json()
    assert transaction["total_amount"] > 0
    print(f"✅ 9. Checkout complete: ${transaction['total_amount']:.2f}")
    print(f"✅ Transaction ID: {transaction['transaction_id']}")
    print(f"✅ Knot ID: {transaction['knot_transaction_id']}")
    
    print("\n🎉 COMPLETE E2E TEST PASSED!")
```

**Manual Mobile E2E Test:**
1. Open app (logged out)
2. Sign up with new account
3. Enter recipe: "pasta carbonara"
4. Review ingredients, uncheck one
5. Select Instacart platform
6. Start shopping
7. Watch agent progress
8. View cart status
9. Remove one item from cart
10. Proceed to checkout
11. Apply changes
12. Complete payment
13. View transaction confirmation

**Exit Criteria:**
✅ Complete backend flow works
✅ Complete mobile flow works
✅ No errors in any phase
✅ Data persists correctly

---

### Task 8.2: Error Handling & Edge Cases
**Deliverables:**
- [ ] Network error handling
- [ ] Empty state screens
- [ ] Loading states everywhere
- [ ] Offline mode graceful degradation
- [ ] Input validation

**Test Suite 8.2:**
**Edge Case Tests:**
- [ ] Test with no internet
- [ ] Test with invalid tokens
- [ ] Test with empty recipe query
- [ ] Test checkout with empty cart
- [ ] Test WebSocket disconnect/reconnect
- [ ] Test with Supabase down
- [ ] Test with Gemini API error
- [ ] Test with agent failures

**Exit Criteria:**
✅ All edge cases handled gracefully
✅ Error messages user-friendly
✅ App doesn't crash
✅ Can recover from errors

---

### Task 8.3: UI Polish & Accessibility
**Deliverables:**
- [ ] Consistent styling
- [ ] Loading skeletons
- [ ] Success/error toasts
- [ ] Smooth transitions
- [ ] Accessibility labels
- [ ] Dark mode support (optional)

**Test Suite 8.3:**
**Manual QA Checklist:**
- [ ] All buttons have appropriate feedback
- [ ] Colors meet contrast requirements
- [ ] Text is readable
- [ ] Touch targets >= 44px
- [ ] Screen reader compatible
- [ ] Animations smooth
- [ ] No layout shifts

**Exit Criteria:**
✅ UI polished and professional
✅ Accessibility standards met
✅ Smooth user experience
✅ No visual bugs

---

## Phase 9: Deployment & Documentation
**Goal:** Prepare for production deployment

### Task 9.1: Backend Deployment Prep
**Deliverables:**
- [ ] Environment variable documentation
- [ ] Docker configuration (optional)
- [ ] Production settings
- [ ] CORS properly configured
- [ ] Rate limiting (optional)

**Test Suite 9.1:**
```bash
# Test production build
cd server
pip install -r requirements.txt
python -m pytest server/tests/ -v

# Test with production env
export ENVIRONMENT=production
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

**Exit Criteria:**
✅ Server runs in production mode
✅ All tests pass
✅ Environment documented
✅ Security settings configured

---

### Task 9.2: Mobile App Build
**Deliverables:**
- [ ] EAS build configuration
- [ ] Production API URLs
- [ ] App icons and splash screen
- [ ] Build for iOS/Android
- [ ] Testing on real devices

**Test Suite 9.2:**
```bash
# Build Android
eas build --platform android --profile production

# Build iOS
eas build --platform ios --profile production

# Test builds
# Install on physical devices and test complete flow
```

**Exit Criteria:**
✅ Builds complete successfully
✅ Apps install on devices
✅ Production API works
✅ No build errors

---

### Task 9.3: Documentation & README
**Deliverables:**
- [ ] README.md with setup instructions
- [ ] API documentation
- [ ] Architecture diagram
- [ ] Environment setup guide
- [ ] Troubleshooting guide

**Exit Criteria:**
✅ Complete documentation
✅ New developer can set up
✅ All endpoints documented
✅ Clear troubleshooting steps

---

## 📊 Progress Tracking

### Phase Completion Checklist
- [x] Phase 1: Backend Foundation (4/4 tasks)
- [ ] Phase 2: Agent Integration (0/3 tasks)
- [ ] Phase 3: Cart Management (0/3 tasks)
- [ ] Phase 4: Checkout (0/1 tasks)
- [ ] Phase 5: Mobile Foundation (0/3 tasks)
- [ ] Phase 6: Mobile Core (0/3 tasks)
- [ ] Phase 7: Cart & Checkout Mobile (0/2 tasks)
- [ ] Phase 8: Integration Testing (0/3 tasks)
- [ ] Phase 9: Deployment (0/3 tasks)

### Overall Progress
**Backend:** 40% complete
**Frontend:** 0% complete
**Testing:** 30% complete
**Documentation:** 10% complete

---

## 🚀 Running Tests

### Backend Tests
```bash
cd server

# Run all tests
python -m pytest tests/ -v

# Run specific phase
python -m pytest tests/test_phase1_*.py -v

# Run with coverage
python -m pytest tests/ --cov=server --cov-report=html

# Run manual test script
python test_api.py
```

### Frontend Tests
```bash
cd mobile

# Run unit tests
npm test

# Run E2E tests
npm run test:e2e

# Type check
npx tsc --noEmit
```

---

## 📝 Notes
- Each phase MUST pass all tests before moving to next
- Document any blockers or issues immediately
- Make progressive git commits after each task
- **NEVER push to remote** (commits local only)
- Update this plan as requirements change

