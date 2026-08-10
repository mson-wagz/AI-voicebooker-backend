"""
Admin Dashboard API Routes for RestoVoice AI Backend
FastAPI router for all admin dashboard endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import logging

from ..database.connection import get_db, prisma
from .jwt_utils import verify_token, get_token_from_header
from .service import get_auth_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/owner/dashboard", tags=["admin-dashboard"])

# Security scheme for JWT tokens
security = HTTPBearer()

# Pydantic models for responses
class OverviewStats(BaseModel):
    totalCalls: int
    successfulBookings: int
    successfulBookingsChange: float
    failedBookings: int
    failedBookingsChange: float
    conversionRate: float
    conversionRateChange: float

class CallRecord(BaseModel):
    id: str
    customer_phone: str
    call_duration: int
    call_status: str
    booking_result: Optional[str]
    timestamp: datetime
    transcript: Optional[str]
    sentiment: Optional[str]

class BookingRecord(BaseModel):
    id: str
    customer_name: str
    customer_phone: str
    party_size: int
    reservation_time: datetime
    status: str
    deposit_amount: Optional[int]
    deposit_status: Optional[str]
    created_at: datetime

class CallLogResponse(BaseModel):
    calls: List[CallRecord]
    total: int
    page: int
    limit: int

class BookingResponse(BaseModel):
    bookings: List[BookingRecord]
    total: int
    page: int
    limit: int

async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current authenticated admin user from JWT token"""
    try:
        token = credentials.credentials
        payload = verify_token(token, "access")
        
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify user exists and is owner/admin
        user = await prisma.user.find_unique(
            where={"id": user_id},
            include={"restaurant": True}
        )
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )
        
        if user.role not in ["OWNER", "ADMIN"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied. Admin privileges required.",
            )
        
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": user.role,
            "restaurant_id": user.restaurant_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/overview-stats", response_model=OverviewStats)
async def get_overview_stats(
    current_user: dict = Depends(get_current_admin_user),
    days: int = Query(default=30, description="Number of days to analyze")
):
    """Get overview statistics for the dashboard"""
    try:
        restaurant_id = current_user["restaurant_id"]
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        prev_start_date = start_date - timedelta(days=days)
        
        # Get total calls
        total_calls = await prisma.call_log.count(
            where={
                "restaurant_id": restaurant_id,
                "created_at": {"gte": start_date, "lte": end_date}
            }
        )
        
        # Get previous period calls for comparison
        prev_calls = await prisma.call_log.count(
            where={
                "restaurant_id": restaurant_id,
                "created_at": {"gte": prev_start_date, "lte": start_date}
            }
        )
        
        # Get successful bookings
        successful_bookings = await prisma.booking.count(
            where={
                "restaurant_id": restaurant_id,
                "status": "CONFIRMED",
                "created_at": {"gte": start_date, "lte": end_date}
            }
        )
        
        # Get previous successful bookings
        prev_successful_bookings = await prisma.booking.count(
            where={
                "restaurant_id": restaurant_id,
                "status": "CONFIRMED",
                "created_at": {"gte": prev_start_date, "lte": start_date}
            }
        )
        
        # Get failed bookings
        failed_bookings = await prisma.booking.count(
            where={
                "restaurant_id": restaurant_id,
                "status": {"in": ["CANCELLED", "FAILED"]},
                "created_at": {"gte": start_date, "lte": end_date}
            }
        )
        
        # Get previous failed bookings
        prev_failed_bookings = await prisma.booking.count(
            where={
                "restaurant_id": restaurant_id,
                "status": {"in": ["CANCELLED", "FAILED"]},
                "created_at": {"gte": prev_start_date, "lte": start_date}
            }
        )
        
        # Calculate conversion rates
        total_bookings = successful_bookings + failed_bookings
        prev_total_bookings = prev_successful_bookings + prev_failed_bookings
        
        conversion_rate = (successful_bookings / total_bookings * 100) if total_bookings > 0 else 0
        prev_conversion_rate = (prev_successful_bookings / prev_total_bookings * 100) if prev_total_bookings > 0 else 0
        
        # Calculate changes
        successful_change = ((successful_bookings - prev_successful_bookings) / prev_successful_bookings * 100) if prev_successful_bookings > 0 else 0
        failed_change = ((failed_bookings - prev_failed_bookings) / prev_failed_bookings * 100) if prev_failed_bookings > 0 else 0
        conversion_change = conversion_rate - prev_conversion_rate
        
        return OverviewStats(
            totalCalls=total_calls,
            successfulBookings=successful_bookings,
            successfulBookingsChange=round(successful_change, 2),
            failedBookings=failed_bookings,
            failedBookingsChange=round(failed_change, 2),
            conversionRate=round(conversion_rate, 2),
            conversionRateChange=round(conversion_change, 2)
        )
        
    except Exception as e:
        logger.error(f"Error getting overview stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve overview statistics"
        )

@router.get("/calls", response_model=CallLogResponse)
async def get_call_logs(
    current_user: dict = Depends(get_current_admin_user),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None)
):
    """Get call logs with pagination and filtering"""
    try:
        restaurant_id = current_user["restaurant_id"]
        skip = (page - 1) * limit
        
        # Build where clause
        where_clause = {"restaurant_id": restaurant_id}
        
        if status:
            where_clause["call_status"] = status
            
        if start_date:
            where_clause["created_at"] = {"gte": datetime.combine(start_date, datetime.min.time())}
            
        if end_date:
            if "created_at" in where_clause:
                where_clause["created_at"]["lte"] = datetime.combine(end_date, datetime.max.time())
            else:
                where_clause["created_at"] = {"lte": datetime.combine(end_date, datetime.max.time())}
        
        # Get calls and total count
        calls = await prisma.call_log.find_many(
            where=where_clause,
            order={"created_at": "desc"},
            skip=skip,
            take=limit,
            include={
                "booking": True
            }
        )
        
        total = await prisma.call_log.count(where=where_clause)
        
        # Format response
        formatted_calls = []
        for call in calls:
            formatted_calls.append(CallRecord(
                id=call.id,
                customer_phone=call.customer_phone or "Unknown",
                call_duration=call.call_duration or 0,
                call_status=call.call_status or "UNKNOWN",
                booking_result=call.booking.status if call.booking else None,
                timestamp=call.created_at,
                transcript=call.transcript,
                sentiment=call.sentiment
            ))
        
        return CallLogResponse(
            calls=formatted_calls,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error getting call logs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve call logs"
        )

@router.get("/bookings", response_model=BookingResponse)
async def get_bookings(
    current_user: dict = Depends(get_current_admin_user),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None)
):
    """Get bookings with pagination and filtering"""
    try:
        restaurant_id = current_user["restaurant_id"]
        skip = (page - 1) * limit
        
        # Build where clause
        where_clause = {"restaurant_id": restaurant_id}
        
        if status:
            where_clause["status"] = status
            
        if start_date:
            where_clause["created_at"] = {"gte": datetime.combine(start_date, datetime.min.time())}
            
        if end_date:
            if "created_at" in where_clause:
                where_clause["created_at"]["lte"] = datetime.combine(end_date, datetime.max.time())
            else:
                where_clause["created_at"] = {"lte": datetime.combine(end_date, datetime.max.time())}
        
        # Get bookings and total count
        bookings = await prisma.booking.find_many(
            where=where_clause,
            order={"created_at": "desc"},
            skip=skip,
            take=limit
        )
        
        total = await prisma.booking.count(where=where_clause)
        
        # Format response
        formatted_bookings = []
        for booking in bookings:
            formatted_bookings.append(BookingRecord(
                id=booking.id,
                customer_name=booking.customer_name or "Unknown",
                customer_phone=booking.customer_phone or "Unknown",
                party_size=booking.party_size or 0,
                reservation_time=booking.reservation_time,
                status=booking.status,
                deposit_amount=booking.deposit_amount,
                deposit_status=booking.deposit_status,
                created_at=booking.created_at
            ))
        
        return BookingResponse(
            bookings=formatted_bookings,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error getting bookings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve bookings"
        )

@router.get("/call/{call_id}")
async def get_call_details(
    call_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """Get detailed information about a specific call"""
    try:
        restaurant_id = current_user["restaurant_id"]
        
        call = await prisma.call_log.find_first(
            where={
                "id": call_id,
                "restaurant_id": restaurant_id
            },
            include={
                "booking": True
            }
        )
        
        if not call:
            raise HTTPException(
                status_code=404,
                detail="Call not found"
            )
        
        return {
            "id": call.id,
            "customer_phone": call.customer_phone,
            "call_duration": call.call_duration,
            "call_status": call.call_status,
            "timestamp": call.created_at,
            "transcript": call.transcript,
            "sentiment": call.sentiment,
            "recording_url": call.recording_url,
            "booking": call.booking,
            "ai_analysis": call.ai_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve call details"
        )

@router.get("/booking/{booking_id}")
async def get_booking_details(
    booking_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """Get detailed information about a specific booking"""
    try:
        restaurant_id = current_user["restaurant_id"]
        
        booking = await prisma.booking.find_first(
            where={
                "id": booking_id,
                "restaurant_id": restaurant_id
            }
        )
        
        if not booking:
            raise HTTPException(
                status_code=404,
                detail="Booking not found"
            )
        
        return {
            "id": booking.id,
            "customer_name": booking.customer_name,
            "customer_phone": booking.customer_phone,
            "customer_email": booking.customer_email,
            "party_size": booking.party_size,
            "reservation_time": booking.reservation_time,
            "status": booking.status,
            "deposit_amount": booking.deposit_amount,
            "deposit_status": booking.deposit_status,
            "special_requests": booking.special_requests,
            "created_at": booking.created_at,
            "updated_at": booking.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting booking details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve booking details"
        )

@router.put("/booking/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    status_update: Dict[str, str],
    current_user: dict = Depends(get_current_admin_user)
):
    """Update booking status"""
    try:
        restaurant_id = current_user["restaurant_id"]
        new_status = status_update.get("status")
        
        if new_status not in ["CONFIRMED", "CANCELLED", "COMPLETED", "NO_SHOW"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid status"
            )
        
        # Verify booking exists and belongs to user's restaurant
        booking = await prisma.booking.find_first(
            where={
                "id": booking_id,
                "restaurant_id": restaurant_id
            }
        )
        
        if not booking:
            raise HTTPException(
                status_code=404,
                detail="Booking not found"
            )
        
        # Update booking
        updated_booking = await prisma.booking.update(
            where={"id": booking_id},
            data={
                "status": new_status,
                "updated_at": datetime.utcnow()
            }
        )
        
        return {
            "success": True,
            "message": f"Booking status updated to {new_status}",
            "booking": updated_booking
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating booking status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update booking status"
        )

@router.get("/analytics/calls-trend")
async def get_calls_trend(
    current_user: dict = Depends(get_current_admin_user),
    days: int = Query(default=30, description="Number of days to analyze")
):
    """Get call volume trend over time"""
    try:
        restaurant_id = current_user["restaurant_id"]
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily call counts
        calls = await prisma.query_raw(
            """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as call_count,
                SUM(CASE WHEN call_status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_calls,
                SUM(CASE WHEN call_status = 'FAILED' THEN 1 ELSE 0 END) as failed_calls
            FROM CallLog 
            WHERE restaurant_id = $1 
            AND created_at >= $2 
            AND created_at <= $3
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """,
            restaurant_id, start_date, end_date
        )
        
        return {
            "trend": calls,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting calls trend: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve calls trend"
        )

@router.get("/analytics/performance-metrics")
async def get_performance_metrics(
    current_user: dict = Depends(get_current_admin_user),
    days: int = Query(default=30, description="Number of days to analyze")
):
    """Get detailed performance metrics"""
    try:
        restaurant_id = current_user["restaurant_id"]
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Average call duration
        avg_duration_result = await prisma.query_raw(
            """
            SELECT AVG(call_duration) as avg_duration
            FROM CallLog 
            WHERE restaurant_id = $1 
            AND created_at >= $2 
            AND created_at <= $3
            AND call_duration IS NOT NULL
            """,
            restaurant_id, start_date, end_date
        )
        
        avg_duration = avg_duration_result[0]["avg_duration"] if avg_duration_result else 0
        
        # Peak call times
        peak_hours = await prisma.query_raw(
            """
            SELECT 
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as call_count
            FROM CallLog 
            WHERE restaurant_id = $1 
            AND created_at >= $2 
            AND created_at <= $3
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY call_count DESC
            LIMIT 5
            """,
            restaurant_id, start_date, end_date
        )
        
        # Booking success rate by time of day
        success_by_hour = await prisma.query_raw(
            """
            SELECT 
                EXTRACT(HOUR FROM cl.created_at) as hour,
                COUNT(*) as total_calls,
                SUM(CASE WHEN b.status = 'CONFIRMED' THEN 1 ELSE 0 END) as successful_bookings
            FROM CallLog cl
            LEFT JOIN Booking b ON cl.id = b.call_log_id
            WHERE cl.restaurant_id = $1 
            AND cl.created_at >= $2 
            AND cl.created_at <= $3
            GROUP BY EXTRACT(HOUR FROM cl.created_at)
            ORDER BY hour
            """,
            restaurant_id, start_date, end_date
        )
        
        return {
            "average_call_duration": round(float(avg_duration), 2) if avg_duration else 0,
            "peak_call_hours": peak_hours,
            "success_rate_by_hour": success_by_hour,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve performance metrics"
        )
