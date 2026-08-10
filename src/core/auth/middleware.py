"""
Authentication middleware for RestoVoice AI Backend
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
from typing import Optional

from .jwt_utils import verify_token, get_token_from_header

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for protecting routes"""
    
    def __init__(self, app, public_paths: Optional[list] = None):
        super().__init__(app)
        self.public_paths = public_paths or [
            "/",
            "/health",
            "/v1/auth/login",
            "/v1/auth/owner/signup",
            "/v1/auth/staff/signup",
            "/v1/auth/validate-invite",
            "/v1/auth/password/reset-request",
            "/v1/auth/password/reset-confirm",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request and validate authentication"""
        
        # Check if path is public
        path = request.url.path
        
        # Skip authentication for public paths and OPTIONS requests
        if (path in self.public_paths or 
            path.startswith("/docs") or 
            path.startswith("/redoc") or
            path.startswith("/openapi") or
            request.method == "OPTIONS"):
            return await call_next(request)
        
        # Skip authentication for static files
        if path.startswith("/static") or path.endswith((".css", ".js", ".ico", ".png", ".jpg", ".svg")):
            return await call_next(request)
        
        try:
            # Get authorization header
            authorization = request.headers.get("authorization")
            
            if not authorization:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authorization header missing",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Extract token
            token = get_token_from_header(authorization)
            
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization header format",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Verify token
            payload = verify_token(token, "access")
            
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Add user info to request state
            request.state.user = {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role"),
                "restaurant_id": payload.get("restaurant_id")
            }
            
            # Continue with the request
            response = await call_next(request)
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication middleware error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


class RoleBasedAccessMiddleware(BaseHTTPMiddleware):
    """Role-based access control middleware"""
    
    def __init__(self, app, required_roles: Optional[list] = None, admin_paths: Optional[list] = None):
        super().__init__(app)
        self.required_roles = required_roles or []
        self.admin_paths = admin_paths or [
            "/v1/auth/staff/invite",
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request and validate role-based access"""
        
        path = request.url.path
        
        # Check if path requires admin access
        if path in self.admin_paths:
            user = getattr(request.state, 'user', None)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            
            if user.get("role") != "OWNER":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions. Owner access required.",
                )
        
        # Check if path requires specific roles
        if self.required_roles:
            user = getattr(request.state, 'user', None)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            
            if user.get("role") not in self.required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {', '.join(self.required_roles)}",
                )
        
        # Continue with the request
        response = await call_next(request)
        return response


class RestaurantAccessMiddleware(BaseHTTPMiddleware):
    """Middleware to validate restaurant access"""
    
    def __init__(self, app, protected_paths: Optional[list] = None):
        super().__init__(app)
        self.protected_paths = protected_paths or [
            "/v1/reservations",
            "/v1/restaurant",
            "/v1/policy",
            "/v1/analytics",
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request and validate restaurant access"""
        
        path = request.url.path
        
        # Check if path requires restaurant access validation
        is_protected = any(path.startswith(protected_path) for protected_path in self.protected_paths)
        
        if is_protected:
            user = getattr(request.state, 'user', None)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            
            # Check if user has restaurant_id
            if not user.get("restaurant_id"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Restaurant access required. Please complete onboarding first.",
                )
        
        # Continue with the request
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers"""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add CORS headers if needed
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging"""
    
    async def dispatch(self, request: Request, call_next):
        """Log request details"""
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get user info if available
        user = getattr(request.state, 'user', None)
        user_email = user.get("email") if user else "anonymous"
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip} by {user_email}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log response
            logger.info(
                f"Response: {response.status_code} for {request.method} {request.url.path}"
            )
            
            return response
            
        except Exception as e:
            # Log error
            logger.error(
                f"Error processing {request.method} {request.url.path}: {str(e)}"
            )
            raise


def get_current_user_middleware(request: Request) -> Optional[dict]:
    """Get current user from request state"""
    return getattr(request.state, 'user', None)


def require_auth(request: Request) -> dict:
    """Require authentication and return user"""
    user = getattr(request.state, 'user', None)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    
    return user


def require_role(request: Request, required_role: str) -> dict:
    """Require specific role and return user"""
    user = require_auth(request)
    
    if user.get("role") != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. {required_role} role required.",
        )
    
    return user


def require_restaurant_access(request: Request) -> dict:
    """Require restaurant access and return user"""
    user = require_auth(request)
    
    if not user.get("restaurant_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Restaurant access required. Please complete onboarding first.",
        )
    
    return user
