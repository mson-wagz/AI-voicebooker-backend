"""
Database models for RestoVoice AI Backend
Based on the Prisma schema from Next.js frontend
"""
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, Text, ForeignKey, UniqueConstraint, Date
from sqlalchemy.orm import relationship
from .connection import Base

# Enums
class UserRole(str, Enum):
    OWNER = "OWNER"
    STAFF = "STAFF"

class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

# User Model
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)  # Clerk User ID
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    role = Column(String, default=UserRole.OWNER)
    onboarding_complete = Column(Boolean, default=False)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="users")
    claimed_invites = relationship("StaffInvite", back_populates="claimed_by")

# Staff Invite Model
class StaffInvite(Base):
    __tablename__ = "staff_invites"
    
    id = Column(String, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=False)
    email = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="staff_invites")
    claimed_by = relationship("User", back_populates="claimed_invites")

# Restaurant Model
class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, nullable=False)
    vapi_assistant_id = Column(String, nullable=True)
    timezone = Column(String, default="UTC")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    policy = relationship("Policy", back_populates="restaurant", uselist=False)
    bookings = relationship("Booking", back_populates="restaurant")
    metrics = relationship("DailyMetric", back_populates="restaurant")
    users = relationship("User", back_populates="restaurant")
    staff_invites = relationship("StaffInvite", back_populates="restaurant")
    call_records = relationship("CallRecord", back_populates="restaurant")

# Policy Model
class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(String, primary_key=True)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), unique=True, nullable=False)
    deposit_required = Column(Boolean, default=False)
    deposit_amount = Column(Integer, nullable=True)  # Amount in cents
    max_party_size = Column(Integer, default=10)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="policy")
    deposit_rules = relationship("DepositRule", back_populates="policy")
    opening_hours = relationship("OpeningHour", back_populates="policy")

# Deposit Rule Model
class DepositRule(Base):
    __tablename__ = "deposit_rules"
    
    id = Column(String, primary_key=True)
    policy_id = Column(String, ForeignKey("policies.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Sunday-Saturday)
    min_party = Column(Integer, nullable=True)
    start_time = Column(String, nullable=True)  # HH:mm
    end_time = Column(String, nullable=True)  # HH:mm
    
    # Relationships
    policy = relationship("Policy", back_populates="deposit_rules")

# Opening Hour Model
class OpeningHour(Base):
    __tablename__ = "opening_hours"
    
    id = Column(String, primary_key=True)
    policy_id = Column(String, ForeignKey("policies.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0-6
    open_time = Column(String, nullable=False)  # HH:mm
    close_time = Column(String, nullable=False)  # HH:mm
    is_closed = Column(Boolean, default=False)
    
    # Relationships
    policy = relationship("Policy", back_populates="opening_hours")

# Booking Model
class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(String, primary_key=True)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=False)
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    party_size = Column(Integer, nullable=False)
    booking_time = Column(DateTime, nullable=False)
    status = Column(String, default=BookingStatus.PENDING)
    stripe_payment_id = Column(String, nullable=True)
    external_ref_id = Column(String, nullable=True)  # For external POS IDs
    call_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="bookings")
    transcript = relationship("CallTranscript", back_populates="booking", uselist=False)

# Call Transcript Model
class CallTranscript(Base):
    __tablename__ = "call_transcripts"
    
    id = Column(String, primary_key=True)
    booking_id = Column(String, ForeignKey("bookings.id"), unique=True, nullable=False)
    transcript = Column(Text, nullable=False)
    audio_url = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    booking = relationship("Booking", back_populates="transcript")

# Daily Metric Model
class DailyMetric(Base):
    __tablename__ = "daily_metrics"
    
    id = Column(String, primary_key=True)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=False)
    date = Column(Date, nullable=False)
    calls_total = Column(Integer, default=0)
    bookings_completed = Column(Integer, default=0)
    deposits_captured = Column(Integer, default=0)  # In cents
    handoffs_to_human = Column(Integer, default=0)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="metrics")
    
    __table_args__ = (UniqueConstraint('restaurant_id', 'date', name='_restaurant_date_uc'),)

# Call Record Model (for Vapi integration)
class CallRecord(Base):
    __tablename__ = "call_records"
    
    id = Column(String, primary_key=True)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=False)
    customer_phone = Column(String, nullable=False)
    call_id = Column(String, unique=True, nullable=False)  # Vapi call ID
    status = Column(String, nullable=False)  # started, ended, failed, etc.
    duration = Column(Integer, default=0)  # in seconds
    transcript = Column(Text, nullable=True)
    audio_url = Column(String, nullable=True)
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="call_records")
    booking = relationship("Booking", backref="call_record")

# Base methods for models
class BaseModelMethods:
    """Common methods for all models"""
    
    @classmethod
    def get_by_id(cls, db_session, model_id: str):
        """Get model by ID"""
        return db_session.query(cls).filter(cls.id == model_id).first()
    
    @classmethod
    def get_all(cls, db_session, **filters):
        """Get all models with optional filters"""
        query = db_session.query(cls)
        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.filter(getattr(cls, key) == value)
        return query.all()
    
    def update(self, db_session, **kwargs):
        """Update model instance"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        if hasattr(self, 'updated_at'):
            self.updated_at = datetime.utcnow()
        db_session.commit()
        db_session.refresh(self)
        return self
    
    def delete(self, db_session):
        """Delete model instance"""
        db_session.delete(self)
        db_session.commit()

# Add methods to existing models
class BaseModelMethods:
    """Common methods for all models"""
    pass

# For now, just use the basic models without additional methods
# We can add CRUD operations later in the API layer
