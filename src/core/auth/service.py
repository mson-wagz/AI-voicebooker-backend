"""
Authentication service layer for RestoVoice AI Backend
Handles all authentication business logic
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from ..database.connection import get_db, prisma
from .schemas import (
    OwnerSignupRequest, LoginRequest,  # Removed StaffSignupRequest
    OnboardingRequest, UserResponse, RestaurantResponse, 
    # Removed StaffInviteResponse
    AuthResponse  # Removed InviteValidationResponse
)
from .jwt_utils import (
    verify_password, get_password_hash, create_access_token,
    # Removed generate_invite_code
    TokenManager, validate_password_strength
)
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service class"""
    
    def __init__(self, db):
        self.db = db  # This will be the Prisma client
    
    async def create_owner_account(self, signup_data: OwnerSignupRequest) -> AuthResponse:
        """Create a new owner account and restaurant"""
        try:
            # Check if user already exists
            existing_user = await self.db.user.find_unique(
                where={"email": signup_data.email},
            )
            
            if existing_user:
                return AuthResponse(
                    success=False,
                    message="An account with this email already exists",
                    errors=["Email already registered"]
                )
            
            # Validate password strength
            password_validation = validate_password_strength(signup_data.password)
            if not password_validation["is_valid"]:
                return AuthResponse(
                    success=False,
                    message="Password does not meet requirements",
                    errors=password_validation["errors"]
                )
            
            # Hash password
            hashed_password = get_password_hash(signup_data.password)
            
            # Create restaurant
            restaurant = await self.db.restaurant.create(
                data={
                    "name": signup_data.restaurant_name,
                    "phoneNumber": signup_data.phone_number,
                    "timezone": "UTC",
                }
            )

            # Create user (owner)
            user_id = str(uuid.uuid4())
            user = await self.db.user.create(
                data={
                    "id": user_id,
                    "email": signup_data.email,
                    "name": f"{signup_data.first_name} {signup_data.last_name}",
                    "passwordHash": hashed_password,
                    "role": "OWNER",
                    "onboardingComplete": False,
                    "restaurantId": restaurant.id,
                }
            )

            # Create default policy
            await self.db.policy.create(
                data={
                    "restaurantId": restaurant.id,
                    "depositRequired": False,
                    "maxPartySize": 10,
                }
            )
            
            # Create JWT token
            token_data = {
                "sub": user.id,
                "email": user.email,
                "role": user.role,
                "restaurant_id": restaurant.id,
            }
            
            access_token = create_access_token(token_data)
            
            # Prepare response data
            user_response = UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role,
                onboarding_complete=user.onboardingComplete,
                restaurant_id=user.restaurantId,
                created_at=user.createdAt,
                updated_at=user.updatedAt,
            )

            restaurant_response = RestaurantResponse(
                id=restaurant.id,
                name=restaurant.name,
                phone_number=restaurant.phoneNumber,
                timezone=restaurant.timezone,
                created_at=restaurant.createdAt,
                updated_at=restaurant.updatedAt,
            )

            return AuthResponse(
                success=True,
                message="Owner account created successfully",
                data={
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": 30 * 24 * 60 * 60,  # 30 days in seconds
                    "user": user_response.dict(),
                    "restaurant": restaurant_response.dict()
                }
            )
            
        except Exception as e:
            logger.error(f"Owner account creation error: {str(e)}")
            return AuthResponse(
                success=False,
                message="Failed to create owner account",
                errors=["Internal server error"]
            )
    
    async def authenticate_user(self, login_data: LoginRequest) -> AuthResponse:
        """Authenticate user and return token"""
        try:
            # Find user by email
            user = await self.db.user.find_unique(
                where={"email": login_data.email},
            )

            if not user:
                return AuthResponse(
                    success=False,
                    message="Invalid email or password",
                    errors=["Authentication failed"],
                )

            if not verify_password(login_data.password, user.passwordHash):
                return AuthResponse(
                    success=False,
                    message="Invalid email or password",
                    errors=["Authentication failed"],
                )

            token_data = {
                "sub": user.id,
                "email": user.email,
                "role": user.role,
                "restaurant_id": user.restaurantId,
            }

            access_token = create_access_token(token_data)

            restaurant = None
            if user.restaurantId:
                restaurant = await self.db.restaurant.find_unique(
                    where={"id": user.restaurantId}
                )

            user_response = UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role,
                onboarding_complete=user.onboardingComplete,
                restaurant_id=user.restaurantId,
                created_at=user.createdAt,
                updated_at=user.updatedAt,
            )

            restaurant_response = None
            if restaurant:
                restaurant_response = RestaurantResponse(
                    id=restaurant.id,
                    name=restaurant.name,
                    phone_number=restaurant.phoneNumber,
                    timezone=restaurant.timezone,
                    created_at=restaurant.createdAt,
                    updated_at=restaurant.updatedAt,
                )
            
            return AuthResponse(
                success=True,
                message="Login successful",
                data={
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": 30 * 24 * 60 * 60,  # 30 days in seconds
                    "user": user_response.dict(),
                    "restaurant": restaurant_response.dict() if restaurant_response else None,
                    "onboarding_required": not user.onboarding_complete
                }
            )
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return AuthResponse(
                success=False,
                message="Authentication failed",
                errors=["Internal server error"]
            )
    
    async def complete_onboarding(self, user_id: str, onboarding_data: OnboardingRequest) -> AuthResponse:
        """Complete user onboarding"""
        try:
            # Get user
            user = await self.db.user.find_unique(where={"id": user_id})

            if not user:
                return AuthResponse(
                    success=False,
                    message="User not found",
                    errors=["User not found"],
                )

            restaurant = await self.db.restaurant.find_unique(
                where={"id": onboarding_data.restaurant_id}
            )

            if not restaurant or restaurant.id != user.restaurantId:
                return AuthResponse(
                    success=False,
                    message="Restaurant not found or access denied",
                    errors=["Invalid restaurant"],
                )

            updated_restaurant = await self.db.restaurant.update(
                where={"id": restaurant.id},
                data={"timezone": onboarding_data.timezone, "phoneNumber": onboarding_data.phone_number},
            )

            policy_data: Dict[str, Any] = {}
            if onboarding_data.max_party_size:
                policy_data["maxPartySize"] = onboarding_data.max_party_size
            if onboarding_data.deposit_required is not None:
                policy_data["depositRequired"] = onboarding_data.deposit_required
            if onboarding_data.deposit_amount:
                policy_data["depositAmount"] = onboarding_data.deposit_amount
            if policy_data:
                await self.db.policy.update_many(
                    where={"restaurantId": restaurant.id},
                    data=policy_data,
                )

            updated_user = await self.db.user.update(
                where={"id": user_id},
                data={"onboardingComplete": True},
            )

            user_response = UserResponse(
                id=updated_user.id,
                email=updated_user.email,
                name=updated_user.name,
                role=updated_user.role,
                onboarding_complete=updated_user.onboardingComplete,
                restaurant_id=updated_user.restaurantId,
                created_at=updated_user.createdAt,
                updated_at=updated_user.updatedAt,
            )

            restaurant_response = RestaurantResponse(
                id=updated_restaurant.id,
                name=updated_restaurant.name,
                phone_number=updated_restaurant.phoneNumber,
                timezone=updated_restaurant.timezone,
                created_at=updated_restaurant.createdAt,
                updated_at=updated_restaurant.updatedAt,
            )
            
            return AuthResponse(
                success=True,
                message="Onboarding completed successfully",
                data={
                    "user": user_response.dict(),
                    "restaurant": restaurant_response.dict()
                }
            )
            
        except Exception as e:
            logger.error(f"Onboarding completion error: {str(e)}")
            return AuthResponse(
                success=False,
                message="Failed to complete onboarding",
                errors=["Internal server error"]
            )
    
    async def get_user_dashboard(self, user_id: str) -> AuthResponse:
        """Get user dashboard data"""
        try:
            # Get user
            user = await self.db.user.find_unique(where={"id": user_id})

            if not user:
                return AuthResponse(
                    success=False,
                    message="User not found",
                    errors=["User not found"],
                )

            restaurant = None
            if user.restaurantId:
                restaurant = await self.db.restaurant.find_unique(
                    where={"id": user.restaurantId}
                )

            features = ["dashboard", "reservations", "settings", "analytics", "phone_management"] \
                if user.role == "OWNER" else []

            user_response = UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role,
                onboarding_complete=user.onboardingComplete,
                restaurant_id=user.restaurantId,
                created_at=user.createdAt,
                updated_at=user.updatedAt,
            )

            restaurant_response = None
            if restaurant:
                restaurant_response = RestaurantResponse(
                    id=restaurant.id,
                    name=restaurant.name,
                    phone_number=restaurant.phoneNumber,
                    timezone=restaurant.timezone,
                    created_at=restaurant.createdAt,
                    updated_at=restaurant.updatedAt,
                )
            
            return AuthResponse(
                success=True,
                message="Dashboard data retrieved successfully",
                data={
                    "user": user_response.dict(),
                    "restaurant": restaurant_response.dict() if restaurant_response else None,
                    "features": features,
                    "onboarding_required": not user.onboarding_complete
                }
            )
            
        except Exception as e:
            logger.error(f"Dashboard retrieval error: {str(e)}")
            return AuthResponse(
                success=False,
                message="Failed to retrieve dashboard data",
                errors=["Internal server error"]
            )


# Dependency function to get auth service
def get_auth_service(db = None) -> AuthService:
    """Get auth service instance"""
    if db is None:
        # For now, we'll create a new instance
        # In production, this should be injected properly
        return AuthService(prisma)
    return AuthService(db)
