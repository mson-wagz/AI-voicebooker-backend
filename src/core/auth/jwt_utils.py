"""
JWT token handling utilities for RestoVoice AI Backend
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
from pydantic import ValidationError
import secrets
import logging

logger = logging.getLogger(__name__)

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days
REFRESH_TOKEN_EXPIRE_MINUTES = 7 * 24 * 60  # 7 days


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password"""
    try:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except Exception as e:
        logger.error(f"Password hashing error: {str(e)}")
        raise ValueError("Failed to hash password")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {str(e)}")
        raise ValueError("Failed to create access token")


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Refresh token creation error: {str(e)}")
        raise ValueError("Failed to create refresh token")


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            logger.warning(f"Invalid token type: expected {token_type}, got {payload.get('type')}")
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
            logger.warning("Token has expired")
            return None
        
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return None


def generate_invite_code(length: int = 8) -> str:
    """Generate a random invite code"""
    return secrets.token_urlsafe(length)[:length].upper()


def generate_password_reset_token(email: str) -> str:
    """Generate a password reset token"""
    delta = timedelta(hours=1)  # Reset tokens expire in 1 hour
    now = datetime.utcnow()
    expires = now + delta
    
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email, "type": "password_reset"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token and return the email"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != "password_reset":
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
            return None
        
        email = payload.get("sub")
        return email
    except JWTError:
        return None


# def create_email_verification_token(email: str) -> str:
#     """Create an email verification token"""
#     delta = timedelta(hours=24)  # Email verification tokens expire in 24 hours
#     now = datetime.utcnow()
#     expires = now + delta
#     
#     exp = expires.timestamp()
#     encoded_jwt = jwt.encode(
#         {"exp": exp, "nbf": now, "sub": email, "type": "email_verification"},
#         SECRET_KEY,
#         algorithm=ALGORITHM,
#     )
#     return encoded_jwt


# def verify_email_verification_token(token: str) -> Optional[str]:
#     """Verify an email verification token and return the email"""
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         
#         # Check token type
#         if payload.get("type") != "email_verification":
#             return None
#         
#         # Check expiration
#         exp = payload.get("exp")
#         if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
#             return None
#         
#         email = payload.get("sub")
#         return email
#     except JWTError:
#         return None


def get_token_from_header(authorization: str) -> Optional[str]:
    """Extract token from Authorization header"""
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]


class TokenManager:
    """Token management utility class"""
    
    @staticmethod
    def create_token_pair(user_data: Dict[str, Any]) -> Dict[str, str]:
        """Create both access and refresh tokens"""
        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        }
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[str]:
        """Create new access token from refresh token"""
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        # Remove token-specific claims
        user_data = {k: v for k, v in payload.items() 
                    if k not in ["exp", "type", "iat"]}
        
        return create_access_token(user_data)


# Password validation utilities
def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return validation result"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    # Optional: Special character requirement
    # if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
    #     errors.append("Password must contain at least one special character")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }
