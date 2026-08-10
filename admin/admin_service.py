from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# Pydantic models
class DashboardStats(BaseModel):
    total_calls: int
    successful_bookings: int
    failed_bookings: int
    total_calls_today: int
    total_bookings_today: int
    success_rate: float
    recent_calls: List[Dict[str, Any]]
    recent_bookings: List[Dict[str, Any]]

class PolicyCreate(BaseModel):
    deposit_required: bool = False
    deposit_amount: Optional[int] = None
    max_party_size: int = 10
    opening_hours: List[Dict[str, Any]]
    deposit_rules: Optional[List[Dict[str, Any]]] = []

class PolicyUpdate(BaseModel):
    deposit_required: Optional[bool] = None
    deposit_amount: Optional[int] = None
    max_party_size: Optional[int] = None
    opening_hours: Optional[List[Dict[str, Any]]] = None
    deposit_rules: Optional[List[Dict[str, Any]]] = None

class PolicyResponse(BaseModel):
    id: str
    restaurant_id: str
    deposit_required: bool
    deposit_amount: Optional[int]
    max_party_size: int
    opening_hours: List[Dict[str, Any]]
    deposit_rules: List[Dict[str, Any]]

# Database dependency
def get_db():
    from src.core.database.connection import get_db_session
    return next(get_db_session())

# Dashboard Stats
@router.get("/dashboard/stats/{restaurant_id}", response_model=DashboardStats)
async def get_dashboard_stats(restaurant_id: str, db: Session = Depends(get_db)):
    """Get comprehensive dashboard statistics for a restaurant"""
    try:
        from src.core.database.models import Restaurant, CallRecord, Booking, BookingStatus
        
        # Verify restaurant exists
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Total stats
        total_calls = db.query(CallRecord).filter(CallRecord.restaurant_id == restaurant_id).count()
        
        successful_bookings = db.query(Booking).filter(
            Booking.restaurant_id == restaurant_id,
            Booking.status == BookingStatus.CONFIRMED
        ).count()
        
        failed_bookings = db.query(Booking).filter(
            Booking.restaurant_id == restaurant_id,
            Booking.status.in_([BookingStatus.FAILED, BookingStatus.CANCELLED])
        ).count()
        
        # Today's stats
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        
        total_calls_today = db.query(CallRecord).filter(
            CallRecord.restaurant_id == restaurant_id,
            CallRecord.created_at >= today_start
        ).count()
        
        total_bookings_today = db.query(Booking).filter(
            Booking.restaurant_id == restaurant_id,
            Booking.created_at >= today_start
        ).count()
        
        # Success rate
        total_bookings = successful_bookings + failed_bookings
        success_rate = (successful_bookings / total_bookings * 100) if total_bookings > 0 else 0
        
        # Recent calls (last 10)
        recent_calls = db.query(CallRecord).filter(
            CallRecord.restaurant_id == restaurant_id
        ).order_by(CallRecord.created_at.desc()).limit(10).all()
        
        recent_calls_data = []
        for call in recent_calls:
            recent_calls_data.append({
                "id": call.id,
                "customer_phone": call.customer_phone,
                "status": call.status,
                "duration": call.duration,
                "created_at": call.created_at.isoformat(),
                "transcript": call.transcript[:200] + "..." if call.transcript and len(call.transcript) > 200 else call.transcript
            })
        
        # Recent bookings (last 10)
        recent_bookings = db.query(Booking).filter(
            Booking.restaurant_id == restaurant_id
        ).order_by(Booking.created_at.desc()).limit(10).all()
        
        recent_bookings_data = []
        for booking in recent_bookings:
            recent_bookings_data.append({
                "id": booking.id,
                "customer_name": booking.customer_name,
                "customer_phone": booking.customer_phone,
                "party_size": booking.party_size,
                "booking_time": booking.booking_time.isoformat(),
                "status": booking.status,
                "created_at": booking.created_at.isoformat()
            })
        
        return DashboardStats(
            total_calls=total_calls,
            successful_bookings=successful_bookings,
            failed_bookings=failed_bookings,
            total_calls_today=total_calls_today,
            total_bookings_today=total_bookings_today,
            success_rate=round(success_rate, 2),
            recent_calls=recent_calls_data,
            recent_bookings=recent_bookings_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

# Policy Management
@router.get("/policies/{restaurant_id}", response_model=PolicyResponse)
async def get_policy(restaurant_id: str, db: Session = Depends(get_db)):
    """Get restaurant policy"""
    try:
        from src.core.database.models import Restaurant, Policy, OpeningHour, DepositRule
        
        # Verify restaurant exists
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Get or create policy
        policy = db.query(Policy).filter(Policy.restaurant_id == restaurant_id).first()
        
        if not policy:
            # Create default policy
            policy = Policy(
                restaurant_id=restaurant_id,
                deposit_required=False,
                max_party_size=10
            )
            db.add(policy)
            db.commit()
            db.refresh(policy)
        
        # Get opening hours
        opening_hours = db.query(OpeningHour).filter(OpeningHour.policy_id == policy.id).all()
        opening_hours_data = []
        for oh in opening_hours:
            opening_hours_data.append({
                "id": oh.id,
                "day_of_week": oh.day_of_week,
                "open_time": oh.open_time,
                "close_time": oh.close_time,
                "is_closed": oh.is_closed
            })
        
        # Get deposit rules
        deposit_rules = db.query(DepositRule).filter(DepositRule.policy_id == policy.id).all()
        deposit_rules_data = []
        for dr in deposit_rules:
            deposit_rules_data.append({
                "id": dr.id,
                "day_of_week": dr.day_of_week,
                "min_party": dr.min_party,
                "start_time": dr.start_time,
                "end_time": dr.end_time
            })
        
        return PolicyResponse(
            id=policy.id,
            restaurant_id=policy.restaurant_id,
            deposit_required=policy.deposit_required,
            deposit_amount=policy.deposit_amount,
            max_party_size=policy.max_party_size,
            opening_hours=opening_hours_data,
            deposit_rules=deposit_rules_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get policy: {str(e)}")

@router.post("/policies/{restaurant_id}", response_model=PolicyResponse)
async def create_policy(restaurant_id: str, policy: PolicyCreate, db: Session = Depends(get_db)):
    """Create or update restaurant policy"""
    try:
        from src.core.database.models import Restaurant, Policy, OpeningHour, DepositRule
        
        # Verify restaurant exists
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Delete existing policy if exists
        existing_policy = db.query(Policy).filter(Policy.restaurant_id == restaurant_id).first()
        if existing_policy:
            # Delete related records
            db.query(OpeningHour).filter(OpeningHour.policy_id == existing_policy.id).delete()
            db.query(DepositRule).filter(DepositRule.policy_id == existing_policy.id).delete()
            db.delete(existing_policy)
        
        # Create new policy
        new_policy = Policy(
            restaurant_id=restaurant_id,
            deposit_required=policy.deposit_required,
            deposit_amount=policy.deposit_amount,
            max_party_size=policy.max_party_size
        )
        db.add(new_policy)
        db.commit()
        db.refresh(new_policy)
        
        # Create opening hours
        opening_hours_data = []
        for oh_data in policy.opening_hours:
            opening_hour = OpeningHour(
                policy_id=new_policy.id,
                day_of_week=oh_data["day_of_week"],
                open_time=oh_data["open_time"],
                close_time=oh_data["close_time"],
                is_closed=oh_data.get("is_closed", False)
            )
            db.add(opening_hour)
            opening_hours_data.append({
                "id": opening_hour.id,
                "day_of_week": opening_hour.day_of_week,
                "open_time": opening_hour.open_time,
                "close_time": opening_hour.close_time,
                "is_closed": opening_hour.is_closed
            })
        
        # Create deposit rules
        deposit_rules_data = []
        if policy.deposit_rules:
            for dr_data in policy.deposit_rules:
                deposit_rule = DepositRule(
                    policy_id=new_policy.id,
                    day_of_week=dr_data["day_of_week"],
                    min_party=dr_data.get("min_party"),
                    start_time=dr_data.get("start_time"),
                    end_time=dr_data.get("end_time")
                )
                db.add(deposit_rule)
                deposit_rules_data.append({
                    "id": deposit_rule.id,
                    "day_of_week": deposit_rule.day_of_week,
                    "min_party": deposit_rule.min_party,
                    "start_time": deposit_rule.start_time,
                    "end_time": deposit_rule.end_time
                })
        
        db.commit()
        
        return PolicyResponse(
            id=new_policy.id,
            restaurant_id=new_policy.restaurant_id,
            deposit_required=new_policy.deposit_required,
            deposit_amount=new_policy.deposit_amount,
            max_party_size=new_policy.max_party_size,
            opening_hours=opening_hours_data,
            deposit_rules=deposit_rules_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")

@router.put("/policies/{restaurant_id}", response_model=PolicyResponse)
async def update_policy(restaurant_id: str, policy_update: PolicyUpdate, db: Session = Depends(get_db)):
    """Update restaurant policy"""
    try:
        from src.core.database.models import Restaurant, Policy, OpeningHour, DepositRule
        
        # Verify restaurant exists
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Get existing policy
        policy = db.query(Policy).filter(Policy.restaurant_id == restaurant_id).first()
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Update policy fields
        if policy_update.deposit_required is not None:
            policy.deposit_required = policy_update.deposit_required
        if policy_update.deposit_amount is not None:
            policy.deposit_amount = policy_update.deposit_amount
        if policy_update.max_party_size is not None:
            policy.max_party_size = policy_update.max_party_size
        
        # Update opening hours if provided
        opening_hours_data = []
        if policy_update.opening_hours is not None:
            # Delete existing opening hours
            db.query(OpeningHour).filter(OpeningHour.policy_id == policy.id).delete()
            
            # Create new opening hours
            for oh_data in policy_update.opening_hours:
                opening_hour = OpeningHour(
                    policy_id=policy.id,
                    day_of_week=oh_data["day_of_week"],
                    open_time=oh_data["open_time"],
                    close_time=oh_data["close_time"],
                    is_closed=oh_data.get("is_closed", False)
                )
                db.add(opening_hour)
                opening_hours_data.append({
                    "id": opening_hour.id,
                    "day_of_week": opening_hour.day_of_week,
                    "open_time": opening_hour.open_time,
                    "close_time": opening_hour.close_time,
                    "is_closed": opening_hour.is_closed
                })
        else:
            # Get existing opening hours
            opening_hours = db.query(OpeningHour).filter(OpeningHour.policy_id == policy.id).all()
            opening_hours_data = []
            for oh in opening_hours:
                opening_hours_data.append({
                    "id": oh.id,
                    "day_of_week": oh.day_of_week,
                    "open_time": oh.open_time,
                    "close_time": oh.close_time,
                    "is_closed": oh.is_closed
                })
        
        # Update deposit rules if provided
        deposit_rules_data = []
        if policy_update.deposit_rules is not None:
            # Delete existing deposit rules
            db.query(DepositRule).filter(DepositRule.policy_id == policy.id).delete()
            
            # Create new deposit rules
            if policy_update.deposit_rules:
                for dr_data in policy_update.deposit_rules:
                    deposit_rule = DepositRule(
                        policy_id=policy.id,
                        day_of_week=dr_data["day_of_week"],
                        min_party=dr_data.get("min_party"),
                        start_time=dr_data.get("start_time"),
                        end_time=dr_data.get("end_time")
                    )
                    db.add(deposit_rule)
                    deposit_rules_data.append({
                        "id": deposit_rule.id,
                        "day_of_week": deposit_rule.day_of_week,
                        "min_party": deposit_rule.min_party,
                        "start_time": deposit_rule.start_time,
                        "end_time": deposit_rule.end_time
                    })
        else:
            # Get existing deposit rules
            deposit_rules = db.query(DepositRule).filter(DepositRule.policy_id == policy.id).all()
            deposit_rules_data = []
            for dr in deposit_rules:
                deposit_rules_data.append({
                    "id": dr.id,
                    "day_of_week": dr.day_of_week,
                    "min_party": dr.min_party,
                    "start_time": dr.start_time,
                    "end_time": dr.end_time
                })
        
        db.commit()
        
        return PolicyResponse(
            id=policy.id,
            restaurant_id=policy.restaurant_id,
            deposit_required=policy.deposit_required,
            deposit_amount=policy.deposit_amount,
            max_party_size=policy.max_party_size,
            opening_hours=opening_hours_data,
            deposit_rules=deposit_rules_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update policy: {str(e)}")

# Call logs and transcripts
@router.get("/calls/{restaurant_id}")
async def get_call_logs(
    restaurant_id: str,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get call logs for a restaurant with pagination"""
    try:
        from src.core.database.models import Restaurant, CallRecord
        
        # Verify restaurant exists
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Get call records
        calls = db.query(CallRecord).filter(
            CallRecord.restaurant_id == restaurant_id
        ).order_by(CallRecord.created_at.desc()).offset(offset).limit(limit).all()
        
        # Get total count
        total_calls = db.query(CallRecord).filter(CallRecord.restaurant_id == restaurant_id).count()
        
        calls_data = []
        for call in calls:
            calls_data.append({
                "id": call.id,
                "call_id": call.call_id,
                "customer_phone": call.customer_phone,
                "status": call.status,
                "duration": call.duration,
                "transcript": call.transcript,
                "audio_url": call.audio_url,
                "booking_id": call.booking_id,
                "created_at": call.created_at.isoformat(),
                "updated_at": call.updated_at.isoformat()
            })
        
        return {
            "calls": calls_data,
            "total": total_calls,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get call logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get call logs: {str(e)}")

@router.get("/bookings/{restaurant_id}")
async def get_booking_logs(
    restaurant_id: str,
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get booking logs for a restaurant with pagination and filtering"""
    try:
        from src.core.database.models import Restaurant, Booking, BookingStatus
        
        # Verify restaurant exists
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Build query
        query = db.query(Booking).filter(Booking.restaurant_id == restaurant_id)
        
        if status:
            query = query.filter(Booking.status == status.upper())
        
        # Get bookings
        bookings = query.order_by(Booking.created_at.desc()).offset(offset).limit(limit).all()
        
        # Get total count
        total_bookings = query.count()
        
        bookings_data = []
        for booking in bookings:
            bookings_data.append({
                "id": booking.id,
                "customer_name": booking.customer_name,
                "customer_phone": booking.customer_phone,
                "party_size": booking.party_size,
                "booking_time": booking.booking_time.isoformat(),
                "status": booking.status,
                "stripe_payment_id": booking.stripe_payment_id,
                "external_ref_id": booking.external_ref_id,
                "call_confidence": booking.call_confidence,
                "created_at": booking.created_at.isoformat()
            })
        
        return {
            "bookings": bookings_data,
            "total": total_bookings,
            "limit": limit,
            "offset": offset,
            "status_filter": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get booking logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get booking logs: {str(e)}")