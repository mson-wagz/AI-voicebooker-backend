"""
Database operations API endpoints
Moved from Next.js frontend to AI backend using Prisma
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, date, time
import logging

from ..database.connection import get_db, prisma
from prisma.models import (
    Restaurant, User, Policy, OpeningHour, DepositRule,
    Booking, CallRecord, DailyMetric, StaffInvite
)
from prisma import Client as PrismaClient

# Configure logging
logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/v1/db", tags=["database"])

# Pydantic models for requests/responses
class RestaurantCreate(BaseModel):
    name: str
    phone_number: str
    timezone: str = "UTC"

class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    timezone: Optional[str] = None
    vapi_assistant_id: Optional[str] = None

class PolicyCreate(BaseModel):
    restaurant_id: str
    deposit_required: bool = False
    deposit_amount: Optional[int] = None
    max_party_size: int = 10

class OpeningHourCreate(BaseModel):
    policy_id: str
    day_of_week: int  # 0-6
    open_time: str  # HH:mm
    close_time: str  # HH:mm
    is_closed: bool = False

class BookingCreate(BaseModel):
    restaurant_id: str
    customer_name: str
    customer_phone: str
    party_size: int
    booking_time: datetime
    status: str = "PENDING"

class BookingUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    party_size: Optional[int] = None
    booking_time: Optional[datetime] = None
    status: Optional[str] = None

# Restaurant endpoints

@router.post("/restaurants")
async def create_restaurant(
    restaurant: RestaurantCreate,
    db: PrismaClient = Depends(get_db)
):
    """Create new restaurant"""
    try:
        # Check if phone number already exists
        existing = await db.restaurant.find_first(where={"phoneNumber": restaurant.phone_number})
        if existing:
            raise HTTPException(status_code=400, detail="Phone number already registered")
        
        # Create restaurant
        db_restaurant = await db.restaurant.create({
            "name": restaurant.name,
            "phoneNumber": restaurant.phone_number,
            "timezone": restaurant.timezone
        })
        
        # Create default policy
        await db.policy.create({
            "restaurantId": db_restaurant.id,
            "depositRequired": False,
            "maxPartySize": 10
        })
        
        return {
            "success": True,
            "restaurant": {
                "id": db_restaurant.id,
                "name": db_restaurant.name,
                "phone_number": db_restaurant.phoneNumber,
                "timezone": db_restaurant.timezone,
                "created_at": db_restaurant.createdAt
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create restaurant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create restaurant: {str(e)}")

@router.get("/restaurants/{restaurant_id}")
async def get_restaurant(restaurant_id: str, db: PrismaClient = Depends(get_db)):
    """Get restaurant by ID"""
    try:
        restaurant = await db.restaurant.find_unique(where={"id": restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        return {
            "id": restaurant.id,
            "name": restaurant.name,
            "phone_number": restaurant.phoneNumber,
            "timezone": restaurant.timezone,
            "vapi_assistant_id": restaurant.vapiAssistantId,
            "created_at": restaurant.createdAt,
            "updated_at": restaurant.updatedAt
        }
        
    except Exception as e:
        logger.error(f"Failed to get restaurant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get restaurant: {str(e)}")

@router.put("/restaurants/{restaurant_id}")
async def update_restaurant(
    restaurant_id: str,
    update: RestaurantUpdate,
    db: PrismaClient = Depends(get_db)
):
    """Update restaurant"""
    try:
        restaurant = await db.restaurant.find_unique(where={"id": restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Update fields
        if update.name is not None:
            restaurant.name = update.name
        if update.phone_number is not None:
            restaurant.phone_number = update.phone_number
        if update.timezone is not None:
            restaurant.timezone = update.timezone
        if update.vapi_assistant_id is not None:
            restaurant.vapi_assistant_id = update.vapi_assistant_id
        
        restaurant.updated_at = datetime.utcnow()
        await db.restaurant.update(where={"id": restaurant_id}, data=restaurant)
        
        return {
            "success": True,
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "phone_number": restaurant.phone_number,
                "timezone": restaurant.timezone,
                "vapi_assistant_id": restaurant.vapi_assistant_id,
                "updated_at": restaurant.updated_at
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to update restaurant: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update restaurant: {str(e)}")

# Policy endpoints

@router.post("/policies", response_model=Dict[str, Any])
async def create_policy(policy: PolicyCreate, db: PrismaClient = Depends(get_db)):
    """Create policy for restaurant"""
    try:
        # Check if restaurant exists
        restaurant = await db.restaurant.find_unique(where={"id": policy.restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Check if policy already exists
        existing = await db.policy.find_unique(where={"restaurant_id": policy.restaurant_id})
        if existing:
            raise HTTPException(status_code=400, detail="Policy already exists for this restaurant")
        
        # Create policy
        db_policy = Policy(
            restaurant_id=policy.restaurant_id,
            deposit_required=policy.deposit_required,
            deposit_amount=policy.deposit_amount,
            max_party_size=policy.max_party_size
        )
        db.add(db_policy)
        db.commit()
        db.refresh(db_policy)
        
        return {
            "success": True,
            "policy": {
                "id": db_policy.id,
                "restaurant_id": db_policy.restaurant_id,
                "deposit_required": db_policy.deposit_required,
                "deposit_amount": db_policy.deposit_amount,
                "max_party_size": db_policy.max_party_size
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create policy: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")

@router.get("/restaurants/{restaurant_id}/policy")
async def get_restaurant_policy(restaurant_id: str, db: PrismaClient = Depends(get_db)):
    """Get restaurant policy"""
    try:
        policy = await db.policy.find_unique(where={"restaurant_id": restaurant_id})
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return {
            "id": policy.id,
            "restaurant_id": policy.restaurant_id,
            "deposit_required": policy.deposit_required,
            "deposit_amount": policy.deposit_amount,
            "max_party_size": policy.max_party_size
        }
        
    except Exception as e:
        logger.error(f"Failed to get policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get policy: {str(e)}")

# Opening Hours endpoints

@router.post("/opening-hours/batch", response_model=Dict[str, Any])
async def update_opening_hours(
    policy_id: str,
    hours: List[OpeningHourCreate],
    db: PrismaClient = Depends(get_db)
):
    """Update opening hours for a policy (replaces all existing hours)"""
    try:
        # Verify policy exists
        policy = await db.policy.find_unique(where={"id": policy_id})
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Delete existing hours
        await db.openinghour.delete_many(where={"policy_id": policy_id})
        
        # Create new hours
        for hour in hours:
            await db.openinghour.create(data={
                "policy_id": policy_id,
                "day_of_week": hour.day_of_week,
                "open_time": hour.open_time,
                "close_time": hour.close_time,
                "is_closed": hour.is_closed
            })
        
        return {
            "success": True,
            "message": f"Updated {len(hours)} opening hours",
            "policy_id": policy_id
        }
        
    except Exception as e:
        logger.error(f"Failed to update opening hours: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update opening hours: {str(e)}")

@router.get("/policies/{policy_id}/opening-hours")
async def get_opening_hours(policy_id: str, db: PrismaClient = Depends(get_db)):
    """Get opening hours for a policy"""
    try:
        hours = await db.openinghour.find_many(where={"policy_id": policy_id})
        
        return {
            "policy_id": policy_id,
            "opening_hours": [
                {
                    "id": hour.id,
                    "day_of_week": hour.day_of_week,
                    "open_time": hour.open_time,
                    "close_time": hour.close_time,
                    "is_closed": hour.is_closed
                }
                for hour in hours
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get opening hours: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get opening hours: {str(e)}")

# Booking endpoints

@router.post("/bookings", response_model=Dict[str, Any])
async def create_booking(booking: BookingCreate, db: PrismaClient = Depends(get_db)):
    """Create new booking"""
    try:
        # Verify restaurant exists
        restaurant = await db.restaurant.find_unique(where={"id": booking.restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Create booking
        db_booking = Booking(
            restaurant_id=booking.restaurant_id,
            customer_name=booking.customer_name,
            customer_phone=booking.customer_phone,
            party_size=booking.party_size,
            booking_time=booking.booking_time,
            status=booking.status
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        
        return {
            "success": True,
            "booking": {
                "id": db_booking.id,
                "restaurant_id": db_booking.restaurant_id,
                "customer_name": db_booking.customer_name,
                "customer_phone": db_booking.customer_phone,
                "party_size": db_booking.party_size,
                "booking_time": db_booking.booking_time,
                "status": db_booking.status,
                "created_at": db_booking.created_at
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create booking: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create booking: {str(e)}")

@router.get("/restaurants/{restaurant_id}/bookings")
async def get_restaurant_bookings(
    restaurant_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: PrismaClient = Depends(get_db)
):
    """Get bookings for a restaurant"""
    try:
        query = db.booking.find_many(where={"restaurant_id": restaurant_id})
        
        if status:
            query = query.filter(Booking.status == status)
        
        bookings = query.order_by(Booking.created_at.desc()).limit(limit).offset(offset).all()
        
        return {
            "restaurant_id": restaurant_id,
            "total_bookings": len(bookings),
            "bookings": [
                {
                    "id": booking.id,
                    "customer_name": booking.customer_name,
                    "customer_phone": booking.customer_phone,
                    "party_size": booking.party_size,
                    "booking_time": booking.booking_time,
                    "status": booking.status,
                    "created_at": booking.created_at
                }
                for booking in bookings
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get bookings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get bookings: {str(e)}")

@router.put("/bookings/{booking_id}")
async def update_booking(
    booking_id: str,
    update: BookingUpdate,
    db: PrismaClient = Depends(get_db)
):
    """Update booking"""
    try:
        booking = await db.booking.find_unique(where={"id": booking_id})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Update fields
        if update.customer_name is not None:
            booking.customer_name = update.customer_name
        if update.customer_phone is not None:
            booking.customer_phone = update.customer_phone
        if update.party_size is not None:
            booking.party_size = update.party_size
        if update.booking_time is not None:
            booking.booking_time = update.booking_time
        if update.status is not None:
            booking.status = update.status
        
        db.commit()
        db.refresh(booking)
        
        return {
            "success": True,
            "booking": {
                "id": booking.id,
                "restaurant_id": booking.restaurant_id,
                "customer_name": booking.customer_name,
                "customer_phone": booking.customer_phone,
                "party_size": booking.party_size,
                "booking_time": booking.booking_time,
                "status": booking.status,
                "created_at": booking.created_at
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to update booking: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update booking: {str(e)}")

# Analytics endpoints

@router.get("/restaurants/{restaurant_id}/analytics")
async def get_restaurant_analytics(
    restaurant_id: str,
    start_date: date,
    end_date: date,
    db: PrismaClient = Depends(get_db)
):
    """Get analytics for a restaurant"""
    try:
        # Verify restaurant exists
        restaurant = await db.restaurant.find_unique(where={"id": restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Get metrics
        metrics = db.query(DailyMetric)\
            .filter(DailyMetric.restaurant_id == restaurant_id)\
            .filter(DailyMetric.date >= start_date)\
            .filter(DailyMetric.date <= end_date)\
            .all()
        
        # Get booking stats
        total_bookings = db.query(Booking)\
            .filter(Booking.restaurant_id == restaurant_id)\
            .filter(Booking.created_at >= start_date)\
            .filter(Booking.created_at <= end_date)\
            .count()
        
        confirmed_bookings = db.query(Booking)\
            .filter(Booking.restaurant_id == restaurant_id)\
            .filter(Booking.status == "CONFIRMED")\
            .filter(Booking.created_at >= start_date)\
            .filter(Booking.created_at <= end_date)\
            .count()
        
        return {
            "restaurant_id": restaurant_id,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "metrics": [
                {
                    "date": metric.date,
                    "calls_total": metric.calls_total,
                    "bookings_completed": metric.bookings_completed,
                    "deposits_captured": metric.deposits_captured,
                    "handoffs_to_human": metric.handoffs_to_human
                }
                for metric in metrics
            ],
            "summary": {
                "total_bookings": total_bookings,
                "confirmed_bookings": confirmed_bookings,
                "conversion_rate": (confirmed_bookings / total_bookings * 100) if total_bookings > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")
