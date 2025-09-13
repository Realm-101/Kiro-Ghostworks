"""
Authentication utilities for JWT token management and password hashing.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, field_validator
import structlog

from config import get_settings
from security import cookie_manager, sanitize_input

logger = structlog.get_logger()
settings = get_settings()

# Password hashing context with bcrypt (12+ rounds as per requirements)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.bcrypt_rounds)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Token payload data model."""
    sub: str  # User ID
    email: str
    tenant_id: Optional[str] = None
    role: Optional[str] = None
    token_type: str  # "access" or "refresh"
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for token revocation


class TokenResponse(BaseModel):
    """Token response model for login endpoints."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Access token expiry in seconds


class UserRegistrationRequest(BaseModel):
    """User registration request model with comprehensive validation."""
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 128:
            raise ValueError("Password must be less than 128 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError("Password must contain at least one special character")
        
        return v
    
    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v):
        """Validate and sanitize name fields."""
        if v is None:
            return v
        
        v = sanitize_input(v)
        if len(v) > 50:
            raise ValueError("Name must be less than 50 characters")
        
        # Check for suspicious patterns
        if any(char in v for char in ['<', '>', '"', "'", '&']):
            raise ValueError("Name contains invalid characters")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!",
                "first_name": "John",
                "last_name": "Doe"
            }
        }


class UserLoginRequest(BaseModel):
    """User login request model with validation."""
    email: EmailStr
    password: str
    
    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v):
        """Basic password validation for login."""
        if len(v) > 128:
            raise ValueError("Password is too long")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!"
            }
        }


class AuthenticatedUser(BaseModel):
    """Authenticated user model for dependency injection."""
    id: str
    email: str
    tenant_id: Optional[str] = None
    role: Optional[str] = None
    is_verified: bool
    is_active: bool


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with configured rounds.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: str,
    email: str,
    tenant_id: Optional[str] = None,
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User's unique identifier
        email: User's email address
        tenant_id: Current tenant/workspace ID
        role: User's role in the current tenant
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    now = datetime.utcnow()
    token_data = {
        "sub": user_id,
        "email": email,
        "tenant_id": tenant_id,
        "role": role,
        "token_type": "access",
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4())
    }
    
    encoded_jwt = jwt.encode(token_data, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)
    
    logger.info(
        "Access token created",
        user_id=user_id,
        email=email,
        tenant_id=tenant_id,
        expires_at=expire.isoformat()
    )
    
    return encoded_jwt


def create_refresh_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        user_id: User's unique identifier
        email: User's email address
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT refresh token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    
    now = datetime.utcnow()
    token_data = {
        "sub": user_id,
        "email": email,
        "token_type": "refresh",
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4())
    }
    
    encoded_jwt = jwt.encode(token_data, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)
    
    logger.info(
        "Refresh token created",
        user_id=user_id,
        email=email,
        expires_at=expire.isoformat()
    )
    
    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> TokenData:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        Decoded token data
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key.get_secret_value(), algorithms=[settings.jwt_algorithm])
        
        # Validate token type
        token_type = payload.get("token_type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}, got {token_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract token data
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(
            sub=user_id,
            email=email,
            tenant_id=payload.get("tenant_id"),
            role=payload.get("role"),
            token_type=token_type,
            exp=datetime.fromtimestamp(payload.get("exp")),
            iat=datetime.fromtimestamp(payload.get("iat")),
            jti=payload.get("jti")
        )
        
    except JWTError as e:
        logger.warning("JWT token verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthenticatedUser:
    """
    Dependency to get the current authenticated user from JWT token.
    Supports both Authorization header and secure cookies.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        
    Returns:
        Authenticated user information
        
    Raises:
        HTTPException: If authentication fails
    """
    # Try to get token from Authorization header or secure cookie
    token = None
    
    if credentials:
        token = credentials.credentials
    else:
        # Try to get from secure cookie
        token = cookie_manager.get_token_from_cookie(request, "access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the access token
    token_data = verify_token(token, "access")
    
    # Get user from database
    from database import get_database_session
    from models.user import User
    from sqlalchemy import select
    
    async with get_database_session() as session:
        result = await session.execute(
            select(User).where(User.id == token_data.sub)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            logger.warning("User not found for valid token", user_id=token_data.sub)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Add user context to structured logging
        logger.info(
            "User authenticated",
            user_id=str(user.id),
            email=user.email,
            tenant_id=token_data.tenant_id,
            request_id=getattr(request.state, "request_id", None)
        )
        
        return AuthenticatedUser(
            id=str(user.id),
            email=user.email,
            tenant_id=token_data.tenant_id,
            role=token_data.role,
            is_verified=user.is_verified,
            is_active=user.is_active
        )


def validate_password_strength(password: str) -> None:
    """
    Validate password strength according to security requirements.
    
    Args:
        password: Password to validate
        
    Raises:
        HTTPException: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long"
        )
    
    if not any(c.isupper() for c in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one uppercase letter"
        )
    
    if not any(c.islower() for c in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one lowercase letter"
        )
    
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one digit"
        )
    
    # Check for special characters
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one special character"
        )