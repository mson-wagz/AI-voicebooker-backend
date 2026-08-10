"""
Authentication schemas for RestoVoice AI Backend
Pydantic models for request/response validation
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
import re


class OwnerSignupRequest(BaseModel):
    """Owner signup request schema"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    restaurant_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str
    phone_number: str = Field(..., min_length=10, max_length=20)
    country_state: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    agree_to_terms: bool = Field(..., description="Must agree to terms of service")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """Validate password confirmation"""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', v)
        if len(digits) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v

    @field_validator('agree_to_terms')
    @classmethod
    def validate_terms(cls, v):
        """Validate terms agreement"""
        if not v:
            raise ValueError('Must agree to terms of service')
        return v


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


# class StaffSignupRequest(BaseModel):
#     """Staff signup request schema using invite code"""
#     first_name: str = Field(..., min_length=1, max_length=100)
#     last_name: str = Field(..., min_length=1, max_length=100)
#     email: EmailStr
#     password: str = Field(..., min_length=8, max_length=128)
#     confirm_password: str
#     phone_number: str = Field(..., min_length=10, max_length=20)
#     invite_code: str = Field(..., min_length=6, max_length=20)
#     agree_to_terms: bool = Field(..., description="Must agree to terms of service")

#     @validator('password')
#     def validate_password(cls, v):
#         """Validate password strength"""
#         if len(v) < 8:
#             raise ValueError('Password must be at least 8 characters long')
#         if not re.search(r'[A-Z]', v):
#             raise ValueError('Password must contain at least one uppercase letter')
#         if not re.search(r'[a-z]', v):
#             raise ValueError('Password must contain at least one lowercase letter')
#         if not re.search(r'\d', v):
#             raise ValueError('Password must contain at least one digit')
#         return v

#     @validator('confirm_password')
#     def passwords_match(cls, v, values):
#         """Validate password confirmation"""
#         if 'password' in values and v != values['password']:
#             raise ValueError('Passwords do not match')
#         return v

#     @validator('phone_number')
#     def validate_phone(cls, v):
#         """Validate phone number format"""
#         digits = re.sub(r'\D', '', v)
#         if len(digits) < 10:
#             raise ValueError('Phone number must have at least 10 digits')
#         return v

#     @validator('agree_to_terms')
#     def must_agree_to_terms(cls, v):
#         """Validate terms agreement"""
#         if not v:
#             raise ValueError('Must agree to terms of service')
#         return v


class OnboardingRequest(BaseModel):
    """Onboarding completion request"""
    restaurant_id: str
    timezone: str = Field(default="UTC")
    phone_number: str = Field(..., min_length=10, max_length=20)
    address: Optional[str] = None
    cuisine_type: Optional[str] = None
    max_party_size: Optional[int] = Field(default=10, ge=1, le=50)
    deposit_required: Optional[bool] = False
    deposit_amount: Optional[int] = Field(default=0, ge=0)


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    email: str
    name: Optional[str]
    role: str
    onboarding_complete: bool
    restaurant_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RestaurantResponse(BaseModel):
    """Restaurant response schema"""
    id: str
    name: str
    phone_number: str
    timezone: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# class StaffInviteResponse(BaseModel):
#     """Staff invite response schema"""
#     id: str
#     code: str
#     restaurant_id: str
#     email: Optional[str]
#     expires_at: datetime
#     used_at: Optional[datetime]
#     created_at: datetime
#     restaurant: Optional[RestaurantResponse]

#     class Config:
#         from_attributes = True


class AuthResponse(BaseModel):
    """Generic authentication response"""
    success: bool
    message: str
    data: Optional[dict] = None
    errors: Optional[List[str]] = None


class DashboardResponse(BaseModel):
    """Dashboard shell response"""
    user: UserResponse
    restaurant: Optional[RestaurantResponse]
    features: List[str]
    onboarding_required: bool


# class InviteValidationRequest(BaseModel):
#     """Invite code validation request"""
#     invite_code: str


# class InviteValidationResponse(BaseModel):
#     """Invite code validation response"""
#     valid: bool
#     restaurant: Optional[RestaurantResponse] = None
#     expires_at: Optional[datetime] = None
#     error: Optional[str] = None


# class PasswordResetRequest(BaseModel):
#     """Password reset request"""
#     email: EmailStr


# class PasswordResetConfirmRequest(BaseModel):
#     """Password reset confirmation"""
#     token: str
#     new_password: str = Field(..., min_length=8, max_length=128)
#     confirm_password: str

#     @validator('new_password')
#     def validate_password(cls, v):
#         """Validate password strength"""
#         if len(v) < 8:
#             raise ValueError('Password must be at least 8 characters long')
#         if not re.search(r'[A-Z]', v):
#             raise ValueError('Password must contain at least one uppercase letter')
#         if not re.search(r'[a-z]', v):
#             raise ValueError('Password must contain at least one lowercase letter')
#         if not re.search(r'\d', v):
#             raise ValueError('Password must contain at least one digit')
#         return v

#     @validator('confirm_password')
#     def passwords_match(cls, v, values):
#         """Validate password confirmation"""
#         if 'new_password' in values and v != values['new_password']:
#             raise ValueError('Passwords do not match')
#         return v
