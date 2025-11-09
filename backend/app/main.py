from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import recipes, shopping, driver, comparison
from app.routes import orders, receipts, profiling  # Phase 3
import logging
import sys

# Configure logging
logging.basicConfig(
    level=settings.log_level.upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Recipe Cart Optimizer API",
    description="Backend for Phase 1-3",
    version="2.0.0"
)

logger.info("=" * 60)
logger.info("Recipe Cart Optimizer API Starting...")
logger.info(f"Log level: {settings.log_level.upper()}")
logger.info(f"Data directory: {settings.data_dir_path}")
logger.info("=" * 60)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 1-2 Routes
app.include_router(recipes.router)
app.include_router(shopping.router)
app.include_router(driver.router)
app.include_router(comparison.router)

# Phase 3 Routes
app.include_router(orders.router)
app.include_router(receipts.router)
app.include_router(profiling.router)


@app.get("/health")
async def health():
    return {"status": "ok", "phase": "1-3"}

