"""
Restaurant Settings API Routes for RestoVoice AI Backend
FastAPI router for restaurant management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
from datetime import datetime, time, timedelta
from pydantic import BaseModel
import logging

from ..database.connection import get_db, prisma
from .jwt_utils import verify_token, get_token_from_header
from .service import get_auth_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/user", tags=["restaurant-settings"])

# Security scheme for JWT tokens
security = HTTPBearer()

# Pydantic models
class OpeningHours(BaseModel):
    day_of_week: int  # 0 = Monday, 6 = Sunday
    open_time: str
    close_time: str
    is_closed: bool = False

class RestaurantSettings(BaseModel):
    restaurant_name: str
    phone_number: str
    email: str
    address: str
    city: str
    state: str
    postal_code: str
    country: str
    timezone: str
    opening_hours: List[OpeningHours]

class PolicySettings(BaseModel):
    deposit_required: bool = False
    deposit_amount: Optional[int] = None
    deposit_deadline_hours: int = 24
    max_party_size: int = 10
    min_party_size: int = 1
    advance_booking_days: int = 30
    cancellation_policy: str
    auto_confirm: bool = False

class RestaurantResponse(BaseModel):
    id: str
    name: str
    phone_number: str
    email: str
    address: str
    city: str
    state: str
    postal_code: str
    country: str
    timezone: str
    opening_hours: List[Dict[str, Any]]
    policy: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current authenticated user from JWT token"""
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
        
        # Verify user exists
        user = await prisma.user.find_unique(
            where={"id": user_id},
            include={"restaurant": True}
        )
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
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

@router.get("/restaurant-settings", response_model=RestaurantResponse)
async def get_restaurant_settings(
    current_user: dict = Depends(get_current_user)
):
    """Get restaurant settings for the current user"""
    try:
        restaurant_id = current_user["restaurant_id"]
        
        if not restaurant_id:
            raise HTTPException(
                status_code=404,
                detail="Restaurant not found for this user"
            )
        
        restaurant = await prisma.restaurant.find_unique(
            where={"id": restaurant_id},
            include={
                "opening_hours": {"orderBy": {"day_of_week": "asc"}},
                "policy": True
            }
        )
        
        if not restaurant:
            raise HTTPException(
                status_code=404,
                detail="Restaurant not found"
            )
        
        return RestaurantResponse(
            id=restaurant.id,
            name=restaurant.name,
            phone_number=restaurant.phone_number,
            email=restaurant.email,
            address=restaurant.address,
            city=restaurant.city,
            state=restaurant.state,
            postal_code=restaurant.postal_code,
            country=restaurant.country,
            timezone=restaurant.timezone,
            opening_hours=[
                {
                    "id": oh.id,
                    "day_of_week": oh.day_of_week,
                    "open_time": oh.open_time,
                    "close_time": oh.close_time,
                    "is_closed": oh.is_closed
                } for oh in restaurant.opening_hours
            ],
            policy=restaurant.policy.__dict__ if restaurant.policy else None,
            created_at=restaurant.created_at,
            updated_at=restaurant.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting restaurant settings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve restaurant settings"
        )

@router.put("/restaurant-settings")
async def update_restaurant_settings(
    settings: RestaurantSettings,
    current_user: dict = Depends(get_current_user)
):
    """Update restaurant settings"""
    try:
        restaurant_id = current_user["restaurant_id"]
        
        if not restaurant_id:
            raise HTTPException(
                status_code=404,
                detail="Restaurant not found for this user"
            )
        
        # Update restaurant basic info
        updated_restaurant = await prisma.restaurant.update(
            where={"id": restaurant_id},
            data={
                "name": settings.restaurant_name,
                "phone_number": settings.phone_number,
                "email": settings.email,
                "address": settings.address,
                "city": settings.city,
                "state": settings.state,
                "postal_code": settings.postal_code,
                "country": settings.country,
                "timezone": settings.timezone,
                "updated_at": datetime.utcnow()
            }
        )
        
        # Update opening hours
        await prisma.opening_hours.delete_many(
            where={"restaurant_id": restaurant_id}
        )
        
        for hours in settings.opening_hours:
            await prisma.opening_hours.create(
                data={
                    "restaurant_id": restaurant_id,
                    "day_of_week": hours.day_of_week,
                    "open_time": hours.open_time,
                    "close_time": hours.close_time,
                    "is_closed": hours.is_closed
                }
            )
        
        return {
            "success": True,
            "message": "Restaurant settings updated successfully",
            "restaurant": updated_restaurant
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating restaurant settings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update restaurant settings"
        )

@router.get("/policy-settings")
async def get_policy_settings(
    current_user: dict = Depends(get_current_user)
):
    """Get restaurant policy settings"""
    try:
        restaurant_id = current_user["restaurant_id"]
        
        if not restaurant_id:
            raise HTTPException(
                status_code=404,
                detail="Restaurant not found for this user"
            )
        
        policy = await prisma.policy.find_first(
            where={"restaurant_id": restaurant_id}
        )
        
        if not policy:
            # Create default policy
            policy = await prisma.policy.create(
                data={
                    "restaurant_id": restaurant_id,
                    "deposit_required": False,
                    "max_party_size": 10,
                    "min_party_size": 1,
                    "advance_booking_days": 30,
                    "cancellation_policy": "Standard cancellation policy applies",
                    "auto_confirm": False
                }
            )
        
        return {
            "id": policy.id,
            "deposit_required": policy.deposit_required,
            "deposit_amount": policy.deposit_amount,
            "deposit_deadline_hours": policy.deposit_deadline_hours,
            "max_party_size": policy.max_party_size,
            "min_party_size": policy.min_party_size,
            "advance_booking_days": policy.advance_booking_days,
            "cancellation_policy": policy.cancellation_policy,
            "auto_confirm": policy.auto_confirm,
            "created_at": policy.created_at,
            "updated_at": policy.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy settings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve policy settings"
        )

@router.put("/policy-settings")
async def update_policy_settings(
    policy: PolicySettings,
    current_user: dict = Depends(get_current_user)
):
    """Update restaurant policy settings"""
    try:
        restaurant_id = current_user["restaurant_id"]
        
        if not restaurant_id:
            raise HTTPException(
                status_code=404,
                detail="Restaurant not found for this user"
            )
        
        # Check if policy exists
        existing_policy = await prisma.policy.find_first(
            where={"restaurant_id": restaurant_id}
        )
        
        if existing_policy:
            # Update existing policy
            updated_policy = await prisma.policy.update(
                where={"id": existing_policy.id},
                data={
                    "deposit_required": policy.deposit_required,
                    "deposit_amount": policy.deposit_amount,
                    "deposit_deadline_hours": policy.deposit_deadline_hours,
                    "max_party_size": policy.max_party_size,
                    "min_party_size": policy.min_party_size,
                    "advance_booking_days": policy.advance_booking_days,
                    "cancellation_policy": policy.cancellation_policy,
                    "auto_confirm": policy.auto_confirm,
                    "updated_at": datetime.utcnow()
                }
            )
        else:
            # Create new policy
            updated_policy = await prisma.policy.create(
                data={
                    "restaurant_id": restaurant_id,
                    "deposit_required": policy.deposit_required,
                    "deposit_amount": policy.deposit_amount,
                    "deposit_deadline_hours": policy.deposit_deadline_hours,
                    "max_party_size": policy.max_party_size,
                    "min_party_size": policy.min_party_size,
                    "advance_booking_days": policy.advance_booking_days,
                    "cancellation_policy": policy.cancellation_policy,
                    "auto_confirm": policy.auto_confirm
                }
            )
        
        return {
            "success": True,
            "message": "Policy settings updated successfully",
            "policy": updated_policy
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating policy settings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update policy settings"
        )

@router.get("/opening-hours")
async def get_opening_hours(
    current_user: dict = Depends(get_current_user)
):
    """Get restaurant opening hours"""
    try:
        restaurant_id = current_user["restaurant_id"]
        
        if not restaurant_id:
            raise HTTPException(
                status_code=404,
                detail="Restaurant not found for this user"
            )
        
        opening_hours = await prisma.opening_hours.find_many(
            where={"restaurant_id": restaurant_id},
            order={"day_of_week": "asc"}
        )
        
        return {
            "opening_hours": [
                {
                    "id": oh.id,
                    "day_of_week": oh.day_of_week,
                    "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][oh.day_of_week],
                    "open_time": oh.open_time,
                    "close_time": oh.close_time,
                    "is_closed": oh.is_closed
                } for oh in opening_hours
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting opening hours: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve opening hours"
        )

@router.put("/opening-hours")
async def update_opening_hours(
    opening_hours_data: List[OpeningHours],
    current_user: dict = Depends(get_current_user)
):
    """Update restaurant opening hours"""
    try:
        restaurant_id = current_user["restaurant_id"]
        
        if not restaurant_id:
            raise HTTPException(
                status_code=404,
                detail="Restaurant not found for this user"
            )
        
        # Delete existing opening hours
        await prisma.opening_hours.delete_many(
            where={"restaurant_id": restaurant_id}
        )
        
        # Create new opening hours
        new_opening_hours = []
        for hours in opening_hours_data:
            new_hours = await prisma.opening_hours.create(
                data={
                    "restaurant_id": restaurant_id,
                    "day_of_week": hours.day_of_week,
                    "open_time": hours.open_time,
                    "close_time": hours.close_time,
                    "is_closed": hours.is_closed
                }
            )
            new_opening_hours.append(new_hours)
        
        return {
            "success": True,
            "message": "Opening hours updated successfully",
            "opening_hours": new_opening_hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating opening hours: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update opening hours"
        )

@router.get("/availability")
async def get_restaurant_availability(
    current_user: dict = Depends(get_current_user),
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    """Get restaurant availability for a specific date"""
    try:
        restaurant_id = current_user["restaurant_id"]
        
        if not restaurant_id:
            raise HTTPException(
                status_code=404,
                detail="Restaurant not found for this user"
            )
        
        # Parse date
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # Get day of week
        day_of_week = target_date.weekday()
        
        # Get opening hours for that day
        opening_hours = await prisma.opening_hours.find_first(
            where={
                "restaurant_id": restaurant_id,
                "day_of_week": day_of_week
            }
        )
        
        if not opening_hours or opening_hours.is_closed:
            return {
                "date": date,
                "is_closed": True,
                "available_slots": []
            }
        
        # Get existing bookings for that date
        bookings = await prisma.booking.find_many(
            where={
                "restaurant_id": restaurant_id,
                "reservation_time": {
                    "gte": datetime.combine(target_date, datetime.min.time()),
                    "lte": datetime.combine(target_date, datetime.max.time())
                },
                "status": {"in": ["CONFIRMED", "PENDING"]}
            }
        )
        
        # Generate available time slots (simplified - you might want more sophisticated logic)
        open_time = datetime.strptime(opening_hours.open_time, "%H:%M").time()
        close_time = datetime.strptime(opening_hours.close_time, "%H:%M").time()
        
        # Generate hourly slots
        slots = []
        current_time = datetime.combine(target_date, open_time)
        end_time = datetime.combine(target_date, close_time)
        
        while current_time < end_time:
            slot_time = current_time.time()
            # Check if slot is booked
            is_booked = any(
                booking.reservation_time.time() == slot_time 
                for booking in bookings
            )
            
            if not is_booked:
                slots.append({
                    "time": slot_time.strftime("%H:%M"),
                    "available": True
                })
            
            current_time += timedelta(hours=1)
        
        return {
            "date": date,
            "is_closed": False,
            "open_time": opening_hours.open_time,
            "close_time": opening_hours.close_time,
            "available_slots": slots,
            "existing_bookings": len(bookings)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting availability: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve availability"
        )
