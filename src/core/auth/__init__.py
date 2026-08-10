"""
Authentication module for RestoVoice AI Backend
"""

from .schemas import (
    OwnerSignupRequest, LoginRequest,  # Removed StaffSignupRequest
    OnboardingRequest, AuthResponse, UserResponse,
    RestaurantResponse,  # Removed StaffInviteResponse
    # Removed InviteValidationRequest, InviteValidationResponse
    # Removed PasswordResetRequest, PasswordResetConfirmRequest
    DashboardResponse
)

from .jwt_utils import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, verify_token, generate_invite_code,
    # Removed create_email_verification_token, verify_email_verification_token
    generate_password_reset_token, verify_password_reset_token,
    TokenManager, validate_password_strength
)

from .service import AuthService, get_auth_service

from .middleware import (
    AuthenticationMiddleware, RoleBasedAccessMiddleware,
    RestaurantAccessMiddleware, SecurityHeadersMiddleware,
    LoggingMiddleware, get_current_user_middleware,
    require_auth, require_role, require_restaurant_access
)

__all__ = [
    # Schemas
    "OwnerSignupRequest",
    "LoginRequest", 
    # "StaffSignupRequest",  # Removed
    "OnboardingRequest",
    "AuthResponse",
    "UserResponse",
    "RestaurantResponse",
    # "StaffInviteResponse",  # Removed
    # "InviteValidationRequest",  # Removed
    # "InviteValidationResponse",  # Removed
    # "PasswordResetRequest",  # Removed
    # "PasswordResetConfirmRequest",  # Removed
    "DashboardResponse",
    
    # JWT Utils
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token", 
    "verify_token",
    "generate_invite_code",
    # "create_email_verification_token",  # Removed
    # "verify_email_verification_token",  # Removed
    "generate_password_reset_token",
    "verify_password_reset_token",
    "TokenManager",
    "validate_password_strength",
    
    # Services
    "AuthService",
    "get_auth_service",
    
    # Middleware
    "AuthenticationMiddleware",
    "RoleBasedAccessMiddleware",
    "RestaurantAccessMiddleware", 
    "SecurityHeadersMiddleware",
    "LoggingMiddleware",
    "get_current_user_middleware",
    "require_auth",
    "require_role",
    "require_restaurant_access"
]
