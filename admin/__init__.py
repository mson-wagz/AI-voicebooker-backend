"""
Admin service initialization and utilities
"""
import logging
from fastapi import FastAPI
from admin.admin_service import router as admin_router

logger = logging.getLogger(__name__)

def initialize_admin_service(app: FastAPI):
    """
    Initialize admin service and register routes
    """
    try:
        # Include admin routes
        app.include_router(admin_router)
        logger.info("✅ Admin service initialized successfully")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize admin service: {str(e)}")
        return False

# Health check for admin service
@admin_router.get("/health")
async def admin_health_check():
    """Admin service health check"""
    return {
        "status": "healthy",
        "service": "admin",
        "version": "1.0.0",
        "features": ["dashboard_stats", "policy_management", "call_logs", "booking_logs"]
    }
