"""
AI Backend Main Application

FastAPI application for AI-only functionality with database operations.
Integrates Vapi AI for telephone orchestration and manages restaurant bookings.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.ai.availability import router as availability_router
from src.core.ai.availability_check import router as availability_check_router
from src.core.ai.tools import router as tools_router
from src.core.voice.vapi_api import router as vapi_router
from src.core.auth.routes import router as auth_router
from src.core.auth.admin_routes import router as admin_dashboard_router
from src.core.auth.restaurant_routes import router as restaurant_router
# from src.core.database.api import router as db_router
from src.core.database.connection import init_db, close_db
# from src.core.automation.service import get_automation_service
import logging
from datetime import datetime
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add admin directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import admin service
try:
    from admin import initialize_admin_service
    ADMIN_AVAILABLE = True
    logger.info("Admin service imported successfully")
except ImportError as e:
    ADMIN_AVAILABLE = False
    logger.warning(f"Admin service not available: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    try:
        await init_db()
        logger.info("Database initialized successfully")
        
        # Start browser automation processing loop
        try:
            from src.core.automation.browser_use import get_booking_processor
            booking_processor = get_booking_processor()
            
            # Start processing in background (don't block startup)
            import asyncio
            asyncio.create_task(booking_processor.start_processing_loop())
            logger.info("Browser automation processing loop started")
        except Exception as e:
            logger.warning(f"Browser automation not available: {e}")
        
        # Initialize admin service
        if ADMIN_AVAILABLE:
            try:
                admin_initialized = initialize_admin_service(app)
                if admin_initialized:
                    logger.info("Admin service initialized successfully")
                else:
                    logger.warning("Admin service initialization failed")
            except Exception as e:
                logger.error(f"Admin service initialization error: {e}")
        else:
            logger.info("Admin service not available - skipping initialization")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    try:
        await close_db()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title="RestoVoice AI Backend",
    description="AI-powered voice intelligence for restaurant reservations with Vapi integration",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ai-voicebooker.onrender.com",
        "http://localhost:3000",
        "https://restovoice.com",
        "http://127.0.0.1:5500",
        "https://smart-pugs-create.loca.lt",
        "https://neat-games-lose.loca.lt",
        "https://olive-coins-move.loca.lt",
        "https://little-peaches-make.loca.lt",
    ],  # Next.js frontend + localtunnel + live server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_dashboard_router, prefix="/api/v1")
app.include_router(restaurant_router, prefix="/api/v1")
app.include_router(availability_router, prefix="/api/v1")
app.include_router(availability_check_router, prefix="/api/v1")
app.include_router(tools_router, prefix="/api/v1")
app.include_router(vapi_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "RestoVoice AI Backend",
        "status": "healthy",
        "version": "1.0.0",
        "features": {
            "authentication": "/v1/auth",
            "admin_dashboard": "/v1/owner/dashboard",
            "restaurant_settings": "/v1/user",
            "ai_availability": "/v1/ai/check-availability",
            "ai_tools": "/v1/tools/discover",
            "vapi_webhooks": "/v1/vapi/webhooks/vapi",
            "vapi_test": "/v1/vapi/test"
        },
    }


@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify server reload"""
    return {"message": "Test endpoint working", "timestamp": datetime.utcnow().isoformat()}


@app.get("/health")
async def health_check():
    """Detailed health check."""
    features = {
        "authentication": "operational",
        "database": "operational",
    }
    
    if ADMIN_AVAILABLE:
        features["admin_service"] = "operational"
    else:
        features["admin_service"] = "unavailable"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": features,
    }


if __name__ == "__main__":
    import uvicorn
    import os

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000)
