"""
AI Backend - Availability Check Endpoint

Handles intelligent availability checking using AI reasoning.
This is AI-only logic - no database operations, no business logic outside AI scope.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request/Response Models
class AvailabilityRequest(BaseModel):
    restaurant_id: str = Field(..., description="Restaurant identifier")
    booking_timestamp: str = Field(..., description="ISO booking timestamp")
    party_size: int = Field(..., ge=1, le=20, description="Party size (1-20)")
    request_context: Optional[Dict[str, Any]] = Field(
        None, description="Request context for correlation"
    )


class Alternative(BaseModel):
    time: str = Field(..., description="Alternative time slot")
    party_size: int = Field(..., description="Party size for alternative")
    confidence: int = Field(..., ge=0, le=100, description="AI confidence percentage")


class AvailabilityResponse(BaseModel):
    available: bool = Field(..., description="Whether requested time is available")
    reasoning: Optional[str] = Field(None, description="AI reasoning for decision")
    alternatives: Optional[List[Alternative]] = Field(
        None, description="Alternative time slots if unavailable"
    )


# AI Router
router = APIRouter(prefix="/v1/ai", tags=["ai"])


def generate_availability_reasoning(
    restaurant_id: str, booking_timestamp: str, party_size: int
) -> tuple[bool, str, List[Alternative]]:
    """
    Generate AI reasoning for availability.

    This is pure AI logic - no database access, no business rules.
    Returns tuple of (available, reasoning, alternatives)
    """

    # Parse the booking time
    try:
        booking_dt = datetime.fromisoformat(booking_timestamp.replace("Z", "+00:00"))
        hour = booking_dt.hour
        day_of_week = booking_dt.weekday()  # 0=Monday, 6=Sunday
    except ValueError:
        return True, "Invalid timestamp format", []

    # AI reasoning based on patterns (mock logic for demonstration)
    # In real implementation, this would use ML models or trained AI

    # Peak hours logic (6-9 PM Friday/Saturday are peak)
    is_peak_time = 18 <= hour <= 21 and day_of_week in (4, 5)  # Friday, Saturday
    is_large_party = party_size > 6

    # Basic availability simulation
    if is_peak_time and is_large_party:
        # Unlikely during peak with large party
        available = False
        reasoning = f"Peak time (hour {hour}) with large party ({party_size}) - high demand period"

        # Generate alternatives
        alternatives = [
            Alternative(
                time=(booking_dt.replace(hour=hour - 1)).isoformat(),
                party_size=party_size,
                confidence=75,
            ),
            Alternative(
                time=(booking_dt.replace(day=booking_dt.day + 1)).isoformat(),
                party_size=min(party_size, 4),
                confidence=82,
            ),
        ]
    elif is_peak_time:
        # Peak time but smaller party
        available = True
        reasoning = f"Peak time but manageable party size ({party_size})"
        alternatives = []
    elif is_large_party:
        # Large party outside peak
        available = False
        reasoning = f"Large party ({party_size}) requires advance booking - current availability limited"

        alternatives = [
            Alternative(
                time=(booking_dt.replace(hour=14)).isoformat(),
                party_size=party_size,
                confidence=68,
            )
        ]
    else:
        # Off-peak, normal party
        available = True
        reasoning = (
            f"Off-peak time with standard party size ({party_size}) - good availability"
        )
        alternatives = []

    return available, reasoning, alternatives


@router.post("/check-availability", response_model=AvailabilityResponse)
async def check_availability(request: AvailabilityRequest):
    """
    AI-powered availability checking endpoint.

    This endpoint provides AI reasoning for availability but does NOT:
    - Access database
    - Make reservations
    - Process payments
    - Handle authentication

    Those responsibilities belong to the Next.js backend.
    """

    # Log request for correlation
    request_context = request.request_context or {}
    session_id = request_context.get("session_id", f"session_{uuid.uuid4().hex[:8]}")
    logger.info(
        f"[AVAILABILITY_CHECK] Session: {session_id}, "
        f"Restaurant: {request.restaurant_id}, "
        f"Time: {request.booking_timestamp}, "
        f"Party: {request.party_size}, "
        f"Source: {request_context.get('source', 'unknown')}"
    )

    try:
        # Generate AI reasoning
        available, reasoning, alternatives = generate_availability_reasoning(
            request.restaurant_id, request.booking_timestamp, request.party_size
        )

        # Create response
        response = AvailabilityResponse(
            available=available, reasoning=reasoning, alternatives=alternatives
        )

        # Log result for correlation
        logger.info(
            f"[AVAILABILITY_RESULT] Session: {session_id}, "
            f"Available: {available}, "
            f"Alternatives: {len(alternatives)}, "
            f"Reasoning: {reasoning[:100]}..."
            if len(reasoning) > 100
            else reasoning
        )

        return response

    except Exception as e:
        logger.error(f"[AVAILABILITY_ERROR] Session: {session_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI processing error",
        )
