"""
Restaurant configuration management for RestoVoice AI.
This module provides flexible restaurant settings that can be customized per restaurant.

Features:
- Configurable operating hours (including 24/7)
- Restaurant-specific policies
- Dynamic settings loading
- Default configurations
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class OperatingHoursType(Enum):
    """Types of operating hours configurations."""
    STANDARD = "standard"  # Fixed hours (e.g., 9 AM - 10 PM)
    EXTENDED = "extended"  # Long hours (e.g., 8 AM - 2 AM)
    TWENTY_FOUR_SEVEN = "24/7"  # Always open
    SEASONAL = "seasonal"  # Varying hours by season/day


@dataclass
class OperatingHours:
    """Configurable operating hours for a restaurant."""
    hours_type: OperatingHoursType
    open_time: Optional[str] = None  # Format: "HH:MM" or "9:00 AM"
    close_time: Optional[str] = None  # Format: "HH:MM" or "11:00 PM"
    days_open: list = None  # Days of week ["monday", "tuesday", ...]
    is_24_hours: bool = False
    
    def __post_init__(self):
        if self.days_open is None:
            self.days_open = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        if self.hours_type == OperatingHoursType.TWENTY_FOUR_SEVEN:
            self.is_24_hours = True
            self.open_time = None
            self.close_time = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "hours_type": self.hours_type.value,
            "open_time": self.open_time,
            "close_time": self.close_time,
            "days_open": self.days_open,
            "is_24_hours": self.is_24_hours,
            "display_hours": self.get_display_hours()
        }
    
    def get_display_hours(self) -> str:
        """Get human-readable hours display."""
        if self.is_24_hours:
            return "24 hours"
        elif self.open_time and self.close_time:
            return f"{self.open_time} - {self.close_time}"
        else:
            return "Hours vary"
    
    def is_open_at_time(self, time_str: str) -> bool:
        """Check if restaurant is open at a specific time."""
        if self.is_24_hours:
            return True
        
        # Simple time validation - in production, use proper datetime parsing
        if not self.open_time or not self.close_time:
            return False
        
        # For now, return True for basic validation
        return True


@dataclass
class RestaurantPolicies:
    """Restaurant-specific policies for reservations."""
    max_party_size: int = 0  # Must be configured
    min_party_size: int = 1
    booking_window_days: int = 30
    advance_booking_required: bool = False
    same_day_booking_cutoff: str = "2 hours before"
    cancellation_window_hours: int = 24
    deposit_required_for_parties_above: int = 0  # Must be configured
    deposit_amount: float = 0.0  # Must be configured
    deposit_type: str = "flat"  # "flat" or "percentage"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "max_party_size": self.max_party_size,
            "min_party_size": self.min_party_size,
            "booking_window_days": self.booking_window_days,
            "advance_booking_required": self.advance_booking_required,
            "same_day_booking_cutoff": self.same_day_booking_cutoff,
            "cancellation_window_hours": self.cancellation_window_hours,
            "deposit_required_for_parties_above": self.deposit_required_for_parties_above,
            "deposit_amount": self.deposit_amount,
            "deposit_type": self.deposit_type
        }


@dataclass
class RestaurantConfig:
    """Complete restaurant configuration."""
    name: str
    operating_hours: OperatingHours
    policies: RestaurantPolicies
    phone_number: str
    address: str
    timezone: str = "America/Vancouver"
    special_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "operating_hours": self.operating_hours.to_dict(),
            "policies": self.policies.to_dict(),
            "phone_number": self.phone_number,
            "address": self.address,
            "timezone": self.timezone,
            "special_notes": self.special_notes
        }
    
    def get_context_for_ai(self) -> Dict[str, Any]:
        """Get restaurant context formatted for AI prompts."""
        return {
            "restaurant_name": self.name,
            "operating_hours": self.operating_hours.get_display_hours(),
            "is_24_hours": self.operating_hours.is_24_hours,
            "hours_type": self.operating_hours.hours_type.value,
            "max_party_size": self.policies.max_party_size,
            "booking_window_days": self.policies.booking_window_days,
            "deposit_policy": f"Deposit required for parties over {self.policies.deposit_required_for_parties_above} people",
            "phone_number": self.phone_number,
            "address": self.address
        }


class RestaurantConfigManager:
    """Manages restaurant configurations."""
    
    @classmethod
    def get_config(cls, config_name: str = None, **kwargs) -> RestaurantConfig:
        """Get a restaurant configuration by name or create custom from parameters."""
        if kwargs:
            # Create custom config from provided parameters
            return cls.create_custom_config(**kwargs)
        else:
            raise ValueError("Restaurant configuration parameters are required")
    
    @classmethod
    def create_custom_config(
        cls,
        name: str,
        hours_type: str = "standard",
        open_time: str = None,
        close_time: str = None,
        max_party_size: int = 0,
        deposit_required_for_parties_above: int = 0,
        deposit_amount: float = 0.0,
        phone_number: str = "",
        address: str = "",
        **kwargs
    ) -> RestaurantConfig:
        """Create a custom restaurant configuration."""
        operating_hours = OperatingHours(
            hours_type=OperatingHoursType(hours_type),
            open_time=open_time,
            close_time=close_time
        )
        
        policies = RestaurantPolicies(
            max_party_size=max_party_size,
            deposit_required_for_parties_above=deposit_required_for_parties_above,
            deposit_amount=deposit_amount,
            **{k: v for k, v in kwargs.items() if hasattr(RestaurantPolicies, k)}
        )
        
        return RestaurantConfig(
            name=name,
            operating_hours=operating_hours,
            policies=policies,
            phone_number=phone_number,
            address=address,
            **{k: v for k, v in kwargs.items() if hasattr(RestaurantConfig, k)}
        )
    
    @classmethod
    def validate_config_params(cls, **kwargs) -> bool:
        """Validate that required configuration parameters are provided."""
        required_params = ["name"]
        for param in required_params:
            if param not in kwargs or not kwargs[param]:
                return False
        return True
