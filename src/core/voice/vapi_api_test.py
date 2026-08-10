"""
Minimal Vapi API test to isolate import issues
"""
from fastapi import APIRouter
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/v1/vapi", tags=["vapi"])

# Simple test endpoint
@router.get("/test")
async def test_vapi():
    """Test Vapi functionality"""
    logger.info("VAPI test endpoint accessed successfully")
    return {"status": "working", "message": "Vapi router is accessible"}

@router.post("/configure-inbound")
async def configure_inbound_calling():
    """Configure Vapi phone number for inbound calls"""
    logger.info("Configure inbound endpoint accessed successfully")
    return {
        "success": True,
        "message": "Inbound calling configured successfully",
        "status": "test_mode"
    }
