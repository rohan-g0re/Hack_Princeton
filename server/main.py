"""
FastAPI Backend for Grocery Super-App
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID, uuid4
from typing import Optional, List
import os
from dotenv import load_dotenv

from server.models import (
    RecipeRequest, RecipeResponse, IngredientItem,
    StartAgentsRequest, JobStatusResponse,
    CartStatusResponse, SaveCartDiffsRequest, ApplyDiffsRequest,
    CheckoutRequest, CheckoutResponse,
    SignUpRequest, SignInRequest, AuthResponse,
    PlatformCart, CartItem
)
from server.supabase_client import SupabaseClient, get_user_from_token
from server.gemini_service import GeminiService
from server.agent_runner import AgentRunner
from server.ws_manager import manager as ws_manager

# Load environment variables
load_dotenv()

# Initialize services
gemini_service: Optional[GeminiService] = None
agent_runner: Optional[AgentRunner] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global gemini_service, agent_runner
    
    # Startup
    print("🚀 Starting Grocery Super-App API...")
    
    # Initialize Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("⚠️  Warning: Supabase credentials not found in .env")
    else:
        SupabaseClient.initialize(supabase_url, supabase_key)
        print("✅ Supabase initialized")
    
    # Initialize Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        gemini_service = GeminiService(gemini_key)
        print("✅ Gemini service initialized")
    else:
        print("⚠️  Warning: GEMINI_API_KEY not found in .env")
    
    # Initialize Agent Runner
    agent_runner = AgentRunner(Path(__file__).parent)
    print("✅ Agent runner initialized")
    
    print("✨ Server ready!")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Grocery Super-App API",
    description="Backend for multi-platform grocery ordering app",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency for auth
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract and verify user from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        user = await get_user_from_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return user
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Grocery Super-App API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "supabase": SupabaseClient._instance is not None,
            "gemini": gemini_service is not None,
            "agent_runner": agent_runner is not None
        }
    }


# ============================================================================
# Auth Endpoints (Supabase Proxy)
# ============================================================================

@app.post("/auth/signup", response_model=AuthResponse)
async def signup(request: SignUpRequest):
    """Sign up a new user via Supabase"""
    try:
        client = SupabaseClient.get_client()
        
        response = client.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {"name": request.name} if request.name else {}
            }
        })
        
        if not response.user:
            raise HTTPException(status_code=400, detail="Sign up failed")
        
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user={
                "id": str(response.user.id),
                "email": response.user.email,
                "name": request.name
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sign up error: {str(e)}")


@app.post("/auth/signin", response_model=AuthResponse)
async def signin(request: SignInRequest):
    """Sign in an existing user via Supabase"""
    try:
        client = SupabaseClient.get_client()
        
        response = client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user={
                "id": str(response.user.id),
                "email": response.user.email,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Sign in error: {str(e)}")


@app.get("/auth/me")
async def get_me(user = Depends(get_current_user)):
    """Get current user info"""
    return user


# ============================================================================
# Recipe & Ingredients Endpoints
# ============================================================================

@app.post("/api/recipe", response_model=RecipeResponse)
async def get_recipe_ingredients(
    request: RecipeRequest,
    user = Depends(get_current_user)
):
    """
    Convert recipe query to ingredient list using Gemini
    """
    if not gemini_service:
        raise HTTPException(status_code=503, detail="Gemini service not available")
    
    try:
        # Get ingredients from Gemini
        result = await gemini_service.get_recipe_ingredients(request.query)
        
        # Create session in database
        client = SupabaseClient.get_client()
        session_data = {
            "user_id": user["user_id"],
            "recipe_query": request.query,
            "ingredients": result["ingredients"]
        }
        
        session_response = client.table("user_sessions").insert(session_data).execute()
        session_id = session_response.data[0]["id"]
        
        # Convert to response model
        ingredients = [
            IngredientItem(**ing) for ing in result["ingredients"]
        ]
        
        return RecipeResponse(
            recipe_name=result["recipe_name"],
            ingredients=ingredients,
            session_id=UUID(session_id)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing recipe: {str(e)}")


# ============================================================================
# Agent Orchestration Endpoints
# ============================================================================

@app.post("/api/start-agents")
async def start_agents(
    request: StartAgentsRequest,
    user = Depends(get_current_user)
):
    """
    Start Search & Order agents for selected platforms
    """
    if not agent_runner:
        raise HTTPException(status_code=503, detail="Agent runner not available")
    
    try:
        # Verify session belongs to user
        client = SupabaseClient.get_client()
        session_check = client.table("user_sessions").select("*").eq("id", str(request.session_id)).execute()
        
        if not session_check.data or session_check.data[0]["user_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Session not found or unauthorized")
        
        # Start agents
        job_id = await agent_runner.run_agents(
            str(request.session_id),
            request.ingredients,
            request.platforms
        )
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": f"Agents started for platforms: {', '.join(request.platforms)}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting agents: {str(e)}")


@app.get("/api/job/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str, user = Depends(get_current_user)):
    """
    Get current status of an agent job
    """
    if not agent_runner:
        raise HTTPException(status_code=503, detail="Agent runner not available")
    
    job_status = agent_runner.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        job_id=job_id,
        status=job_status["status"],
        platforms=job_status["platforms"]
    )


# ============================================================================
# Cart Management Endpoints
# ============================================================================

@app.get("/api/cart-status", response_model=CartStatusResponse)
async def get_cart_status(
    session_id: str,
    user = Depends(get_current_user)
):
    """
    Get current cart status for all platforms
    """
    try:
        client = SupabaseClient.get_client()
        
        # Verify session
        session_check = client.table("user_sessions").select("*").eq("id", session_id).execute()
        if not session_check.data or session_check.data[0]["user_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Get cart states
        cart_states = client.table("cart_states").select("*").eq("session_id", session_id).execute()
        
        carts = []
        total_items = 0
        total_amount = 0.0
        
        for cart_state in cart_states.data:
            items = [CartItem(**item) for item in cart_state["items"]]
            subtotal = sum(item.price * item.quantity for item in items)
            item_count = sum(item.quantity for item in items)
            
            carts.append(PlatformCart(
                platform=cart_state["platform"],
                items=items,
                subtotal=subtotal,
                item_count=item_count,
                updated_at=cart_state["updated_at"]
            ))
            
            total_items += item_count
            total_amount += subtotal
        
        return CartStatusResponse(
            session_id=UUID(session_id),
            carts=carts,
            total_items=total_items,
            total_amount=total_amount
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cart status: {str(e)}")


@app.post("/api/cart-diffs")
async def save_cart_diffs(
    request: SaveCartDiffsRequest,
    user = Depends(get_current_user)
):
    """
    Save user's cart modifications (diffs) to database
    """
    try:
        client = SupabaseClient.get_client()
        
        # Verify session
        session_check = client.table("user_sessions").select("*").eq("id", str(request.session_id)).execute()
        if not session_check.data or session_check.data[0]["user_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Save diffs
        diff_records = []
        for diff in request.diffs:
            diff_records.append({
                "session_id": str(request.session_id),
                "platform": request.platform,
                "action": diff.action,
                "item": diff.item.model_dump(),
                "applied": False
            })
        
        if diff_records:
            client.table("cart_diffs").insert(diff_records).execute()
        
        return {
            "status": "success",
            "message": f"Saved {len(diff_records)} cart diffs"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving diffs: {str(e)}")


@app.post("/api/apply-diffs")
async def apply_diffs(
    request: ApplyDiffsRequest,
    user = Depends(get_current_user)
):
    """
    Apply cart diffs using Edit_Cart agents
    """
    try:
        client = SupabaseClient.get_client()
        
        # Verify session
        session_check = client.table("user_sessions").select("*").eq("id", str(request.session_id)).execute()
        if not session_check.data or session_check.data[0]["user_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Get pending diffs
        diffs = client.table("cart_diffs").select("*").eq("session_id", str(request.session_id)).eq("applied", False).execute()
        
        if not diffs.data:
            return {"status": "success", "message": "No diffs to apply"}
        
        # TODO: Trigger Edit_Cart agents here
        # For now, just mark diffs as applied
        for diff in diffs.data:
            client.table("cart_diffs").update({"applied": True}).eq("id", diff["id"]).execute()
        
        return {
            "status": "success",
            "message": f"Applied {len(diffs.data)} cart diffs"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying diffs: {str(e)}")


# ============================================================================
# Checkout Endpoint
# ============================================================================

@app.post("/api/checkout", response_model=CheckoutResponse)
async def checkout(
    request: CheckoutRequest,
    user = Depends(get_current_user)
):
    """
    Process checkout: run Cart_Detail agents, aggregate totals, mock payment
    """
    try:
        client = SupabaseClient.get_client()
        
        # Verify session
        session_check = client.table("user_sessions").select("*").eq("id", str(request.session_id)).execute()
        if not session_check.data or session_check.data[0]["user_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Get final cart states
        cart_states = client.table("cart_states").select("*").eq("session_id", str(request.session_id)).execute()
        
        platforms_data = []
        total_amount = 0.0
        
        for cart_state in cart_states.data:
            items = cart_state["items"]
            subtotal = sum(item["price"] * item["quantity"] for item in items)
            item_count = sum(item["quantity"] for item in items)
            
            platforms_data.append({
                "platform": cart_state["platform"],
                "subtotal": subtotal,
                "items_count": item_count
            })
            
            total_amount += subtotal
        
        # Create transaction record
        transaction_data = {
            "session_id": str(request.session_id),
            "total_amount": total_amount,
            "platforms": platforms_data,
            "knot_transaction_id": f"mock_txn_{uuid4().hex[:12]}"  # Mock Knot API
        }
        
        transaction_response = client.table("transactions").insert(transaction_data).execute()
        transaction_id = transaction_response.data[0]["id"]
        created_at = transaction_response.data[0]["created_at"]
        
        return CheckoutResponse(
            transaction_id=UUID(transaction_id),
            total_amount=total_amount,
            platforms=platforms_data,
            knot_transaction_id=transaction_data["knot_transaction_id"],
            created_at=created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during checkout: {str(e)}")


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws/agent-progress")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket for real-time agent progress updates
    """
    await ws_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            # Echo or handle client messages if needed
    
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket, session_id)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run("server.main:app", host="0.0.0.0", port=port, reload=True)

