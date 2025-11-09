from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import recipes, shopping, driver, comparison

app = FastAPI(
    title="Recipe Cart Optimizer API",
    description="Backend for Phase 1-2",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(recipes.router)
app.include_router(shopping.router)
app.include_router(driver.router)
app.include_router(comparison.router)


@app.get("/health")
async def health():
    return {"status": "ok", "phase": "1-2"}

