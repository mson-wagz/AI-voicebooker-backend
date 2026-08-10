"""
Authentication API routes for RestoVoice AI Backend
FastAPI router for all authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from ..database.connection import get_db, prisma
from .service import get_auth_service, AuthService
from .schemas import (
    OwnerSignupRequest,
    LoginRequest,  # Removed StaffSignupRequest
    OnboardingRequest,
    AuthResponse,  # Removed InviteValidationRequest,
    # Removed InviteValidationResponse, PasswordResetRequest, PasswordResetConfirmRequest
)
from .jwt_utils import verify_token, get_token_from_header
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current authenticated user from JWT token"""
    try:
        token = credentials.credentials
        payload = verify_token(token, "access")

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role"),
            "restaurant_id": payload.get("restaurant_id"),
        }

    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get current active user (additional validation if needed)"""
    # Add any additional user validation here
    # For example, check if user is active, not suspended, etc.
    return current_user


# Owner signup endpoint
@router.post("/owner/signup", response_model=AuthResponse)
async def owner_signup(signup_data: OwnerSignupRequest):
    """Create a new owner account and restaurant"""
    try:
        auth_service = get_auth_service()
        result = await auth_service.create_owner_account(signup_data)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Owner signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Login endpoint
@router.post("/login", response_model=AuthResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return access token"""
    try:
        auth_service = get_auth_service()
        result = await auth_service.authenticate_user(login_data)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.message,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Staff signup endpoint
# @router.post("/staff/signup", response_model=AuthResponse)
# async def staff_signup(
#     signup_data: StaffSignupRequest,
#     db: Session = Depends(get_db)
# ):
#     """Create a new staff account using invite code"""
#     try:
#         auth_service = get_auth_service(db)
#         result = await auth_service.create_staff_account(signup_data)
#
#         if not result.success:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=result.message,
#             )
#
#         return result
#
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Staff signup error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error"
#         )


# Validate invite code endpoint
# @router.post("/validate-invite", response_model=InviteValidationResponse)
# async def validate_invite_code(
#     invite_data: InviteValidationRequest,
#     db: Session = Depends(get_db)
# ):
#     """Validate a staff invite code"""
#     try:
#         auth_service = get_auth_service(db)
#         result = await auth_service.validate_invite_code(invite_data.invite_code)
#         return result
#
#     except Exception as e:
#         logger.error(f"Invite validation error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error"
#         )


# Onboarding completion endpoint
@router.post("/onboarding/complete", response_model=AuthResponse)
async def complete_onboarding(
    onboarding_data: OnboardingRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Complete user onboarding"""
    try:
        auth_service = get_auth_service()
        result = await auth_service.complete_onboarding(
            current_user["user_id"], onboarding_data
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Onboarding completion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Dashboard endpoint
@router.get("/dashboard", response_model=AuthResponse)
async def get_dashboard(current_user: dict = Depends(get_current_active_user)):
    """Get user dashboard data"""
    try:
        auth_service = get_auth_service()
        result = await auth_service.get_user_dashboard(current_user["user_id"])

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Create staff invite endpoint (owners only)
# @router.post("/staff/invite", response_model=AuthResponse)
# async def create_staff_invite(
#     email: Optional[str] = None,
#     expires_days: int = 7,
#     current_user: dict = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Create a new staff invite code (owners only)"""
#     try:
#         # Check if user is owner
#         if current_user["role"] != "OWNER":
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Only owners can create staff invites"
#             )
#
#         if not current_user["restaurant_id"]:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Restaurant not found"
#             )
#
#         auth_service = get_auth_service(db)
#         result = await auth_service.create_staff_invite(
#             current_user["restaurant_id"],
#             email,
#             expires_days
#         )
#
#         if not result.success:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=result.message,
#             )
#
#         return result
#
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Staff invite creation error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error"
#         )


# Password reset request endpoint
# @router.post("/password/reset-request")
# async def request_password_reset(
#     reset_data: PasswordResetRequest,
#     db: Session = Depends(get_db)
# ):
#     """Request password reset"""
#     try:
#         # This would typically send an email with reset link
#         # For now, we'll just return a success message
#         return {
#             "success": True,
#             "message": "If an account with that email exists, a password reset link has been sent"
#         }
#
#     except Exception as e:
#         logger.error(f"Password reset request error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error"
#         )


# Password reset confirmation endpoint
# @router.post("/password/reset-confirm")
# async def confirm_password_reset(
#     reset_data: PasswordResetConfirmRequest,
#     db: Session = Depends(get_db)
# ):
#     """Confirm password reset"""
#     try:
#         # This would verify the reset token and update the password
#         # For now, we'll just return a success message
#         return {
#             "success": True,
#             "message": "Password has been reset successfully"
#         }
#
#     except Exception as e:
#         logger.error(f"Password reset confirmation error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error"
#         )


# Logout endpoint (client-side token removal)
@router.post("/logout")
async def logout():
    """Logout user (client-side token removal)"""
    return {"success": True, "message": "Logout successful"}


# Refresh token endpoint
@router.post("/refresh")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Refresh access token"""
    try:
        token = credentials.credentials
        # This would validate refresh token and issue new access token
        # For now, we'll return an error
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Token refresh not implemented yet",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Get current user info
@router.get("/me", response_model=AuthResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    """Get current user information"""
    try:
        auth_service = get_auth_service()
        result = await auth_service.get_user_dashboard(current_user["user_id"])

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
