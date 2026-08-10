"""
Availability Check API for Vapi Integration
Provides real-time availability checking with natural language responses
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import asyncio

from ..automation.browser_use import BrowserAutomation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/availability", tags=["availability"])

class AvailabilityRequest(BaseModel):
    """Request model for availability checking"""
    restaurant_name: str = Field(..., description="Restaurant name or type")
    location: str = Field(..., description="Location/area")
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    time: str = Field(..., description="Time (HH:MM or 7:30 PM)")
    party_size: int = Field(default=2, description="Number of people")
    customer_name: Optional[str] = Field(None, description="Customer name")
    customer_phone: Optional[str] = Field(None, description="Customer phone")

class AvailabilityResponse(BaseModel):
    """Response model for availability checking"""
    success: bool = Field(..., description="Request successful")
    available: bool = Field(..., description="Any restaurants found")
    requested_time_available: bool = Field(..., description="Requested time available")
    message: str = Field(..., description="Natural language response for Vapi")
    alternatives: list = Field(default=[], description="Alternative time options")
    best_option: Optional[Dict[str, Any]] = Field(None, description="Best alternative")
    processing_time: float = Field(..., description="Processing time in seconds")

# Global automation instance (shared across requests)
automation_instance = None

async def get_automation():
    """Get or create automation instance"""
    global automation_instance
    if automation_instance is None:
        automation_instance = BrowserAutomation()
        await automation_instance.initialize()
    return automation_instance

@router.post("/check", response_model=AvailabilityResponse)
async def check_availability(request: AvailabilityRequest):
    """
    Check availability for restaurant booking
    Returns natural language response suitable for Vapi
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"[AVAILABILITY API] Checking {request.restaurant_name} in {request.location}")
        
        # Get automation instance
        automation = await get_automation()
        
        # Parse time to standard format
        time_24h = _parse_time(request.time)
        
        # Check availability
        result = await automation.check_availability(
            restaurant_name=request.restaurant_name,
            location=request.location,
            requested_date=request.date,
            requested_time=time_24h,
            party_size=request.party_size
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"[AVAILABILITY API] Completed in {processing_time:.2f}s")
        
        return AvailabilityResponse(
            success=True,
            available=result["available"],
            requested_time_available=result["requested_time_available"],
            message=result["message"],
            alternatives=result["alternatives"],
            best_option=result["best_option"],
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"[AVAILABILITY API] Error: {e}")
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return AvailabilityResponse(
            success=False,
            available=False,
            requested_time_available=False,
            message=f"I'm sorry, I encountered an error checking availability: {str(e)}",
            alternatives=[],
            best_option=None,
            processing_time=processing_time
        )

@router.post("/book", response_model=Dict[str, Any])
async def book_restaurant(request: AvailabilityRequest):
    """
    Proceed with booking based on availability check
    This would be called after user confirms availability
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"[BOOKING API] Booking {request.restaurant_name} for {request.date} at {request.time}")
        
        automation = await get_automation()
        
        # Create booking metadata
        from ..metadata.storage import CallMetadata
        
        booking_metadata = CallMetadata(
            call_id=f"direct_booking_{int(start_time.timestamp())}",
            restaurant_id="search_based",
            customer_phone=request.customer_phone or "+1234567890",
            customer_name=request.customer_name or "Customer",
            booking_request={
                "restaurant_name": request.restaurant_name,
                "location": request.location,
                "date": request.date,
                "time": request.time,
                "party_size": request.party_size,
                "customer_name": request.customer_name,
                "customer_phone": request.customer_phone
            },
            call_status="direct_booking"
        )
        
        # Process booking
        result = await automation.process_booking(booking_metadata)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            message = f"Great! I've successfully booked your table at {request.restaurant_name} for {request.date} at {request.time} for {request.party_size} people. Your confirmation number is {result.booking_reference}."
        else:
            message = f"I'm sorry, I couldn't complete the booking. {result.error_message}"
        
        return {
            "success": result.success,
            "message": message,
            "booking_reference": result.booking_reference,
            "confirmation_details": result.confirmation_details,
            "processing_time": processing_time
        }
        
    except Exception as e:
        logger.error(f"[BOOKING API] Error: {e}")
        return {
            "success": False,
            "message": f"Booking failed: {str(e)}",
            "booking_reference": None,
            "confirmation_details": None,
            "processing_time": (datetime.utcnow() - start_time).total_seconds()
        }

def _parse_time(time_str: str) -> str:
    """Parse time string to 24-hour format"""
    try:
        # Remove spaces and convert to lowercase
        time_str = time_str.strip().lower()
        
        # Handle formats like "7:30 PM", "7 PM", "19:30"
        if "pm" in time_str and "am" not in time_str:
            # Convert PM to 24-hour
            time_str = time_str.replace("pm", "").strip()
            if ":" in time_str:
                hour, minute = time_str.split(":")
                hour = int(hour) + 12 if int(hour) < 12 else int(hour)
            else:
                hour = int(time_str) + 12 if int(time_str) < 12 else int(time_str)
                minute = "00"
            return f"{hour:02d}:{minute}"
        elif "am" in time_str:
            # Convert AM to 24-hour
            time_str = time_str.replace("am", "").strip()
            if ":" in time_str:
                hour, minute = time_str.split(":")
                hour = int(hour) if int(hour) < 12 else 0  # 12 AM = 0
            else:
                hour = int(time_str) if int(time_str) < 12 else 0
                minute = "00"
            return f"{hour:02d}:{minute}"
        elif ":" in time_str:
            # Already in 24-hour format
            return time_str
        else:
            # Assume it's just an hour
            hour = int(time_str)
            return f"{hour:02d}:00"
    except:
        # Fallback to original string
        return time_str

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "availability-check"}
