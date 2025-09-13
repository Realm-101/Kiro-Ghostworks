"""
Authentication routes for user registration, login, and token management.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import structlog

from auth import (
    UserRegistrationRequest,
    UserLoginRequest,
    TokenResponse,
    AuthenticatedUser,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    validate_password_strength,
    get_current_user,
    security
)
from security import cookie_manager
from database import get_database_session
from models.user import User
from config import get_settings
from telemetry import get_tracer, business_telemetry
from metrics import metrics
from security import limiter

logger = structlog.get_logger()
settings = get_settings()
tracer = get_tracer(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register_user(
    request: Request,
    user_data: UserRegistrationRequest
) -> dict:
    """
    Register a new user account.
    
    Creates a new user with email verification required.
    Validates password strength and email uniqueness.
    
    Args:
        request: FastAPI request object
        user_data: User registration data
        
    Returns:
        Success message with user ID
        
    Raises:
        HTTPException: If email already exists or validation fails
    """
    # Validate password strength
    validate_password_strength(user_data.password)
    
    # Hash the password
    hashed_password = hash_password(user_data.password)
    
    async with get_database_session() as session:
        try:
            # Check if user already exists
            existing_user = await session.execute(
                select(User).where(User.email == user_data.email)
            )
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists"
                )
            
            # Create new user
            new_user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                is_verified=False,  # Email verification required
                is_active=True
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            # Record user registration metric
            metrics.record_user_registration()
            
            logger.info(
                "User registered successfully",
                user_id=str(new_user.id),
                email=new_user.email,
                request_id=getattr(request.state, "request_id", None)
            )
            
            # TODO: Send email verification email
            # This would be implemented in a future task with email service
            
            return {
                "message": "User registered successfully",
                "user_id": str(new_user.id),
                "email": new_user.email,
                "verification_required": True
            }
            
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login_user(
    request: Request,
    response: Response,
    user_data: UserLoginRequest
) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.
    
    Validates email/password and returns access and refresh tokens.
    Sets secure HTTP-only cookies for token storage.
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        user_data: User login credentials
        
    Returns:
        JWT tokens and expiration info
        
    Raises:
        HTTPException: If authentication fails
    """
    with tracer.start_as_current_span("auth.login") as span:
        # Add span attributes
        span.set_attribute("auth.method", "password")
        span.set_attribute("user.email", user_data.email)
        
        # Security check: Block demo credentials in production
        demo_emails = {
            "owner@acme.com", "admin@umbrella.com", "member@acme.com",
            "researcher@umbrella.com", "manager@acme.com"
        }
        
        if (settings.environment == "production" and 
            user_data.email.lower() in demo_emails):
            logger.warning(
                "Demo credential login attempt blocked in production",
                email=user_data.email,
                environment=settings.environment,
                request_id=getattr(request.state, "request_id", None)
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Demo credentials are disabled in production environments"
            )
        
        async with get_database_session() as session:
            # Find user by email
            result = await session.execute(
                select(User).where(User.email == user_data.email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Record failed auth attempt
                business_telemetry.record_auth_attempt(success=False, method="password")
                metrics.record_authentication_attempt(success=False, method="password")
                span.set_attribute("auth.success", False)
                span.set_attribute("auth.failure_reason", "user_not_found")
                
                logger.warning(
                    "Login attempt with non-existent email",
                    email=user_data.email,
                    request_id=getattr(request.state, "request_id", None)
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Verify password
            if not verify_password(user_data.password, user.hashed_password):
                # Record failed auth attempt
                business_telemetry.record_auth_attempt(success=False, method="password")
                metrics.record_authentication_attempt(success=False, method="password")
                span.set_attribute("auth.success", False)
                span.set_attribute("auth.failure_reason", "invalid_password")
                span.set_attribute("user.id", str(user.id))
                
                logger.warning(
                    "Login attempt with invalid password",
                    user_id=str(user.id),
                    email=user.email,
                    request_id=getattr(request.state, "request_id", None)
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Check if user is active
            if not user.is_active:
                # Record failed auth attempt
                business_telemetry.record_auth_attempt(success=False, method="password")
                metrics.record_authentication_attempt(success=False, method="password")
                span.set_attribute("auth.success", False)
                span.set_attribute("auth.failure_reason", "user_inactive")
                span.set_attribute("user.id", str(user.id))
                
                logger.warning(
                    "Login attempt for inactive user",
                    user_id=str(user.id),
                    email=user.email,
                    request_id=getattr(request.state, "request_id", None)
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive"
                )
        
        # Create tokens (no workspace context on initial login)
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email
        )
        
        refresh_token = create_refresh_token(
            user_id=str(user.id),
            email=user.email
        )
        
        # Set secure HTTP-only cookies using cookie manager
        cookie_manager.set_auth_cookies(response, access_token, refresh_token)
        
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        
        # Record successful auth attempt
        business_telemetry.record_auth_attempt(success=True, method="password")
        metrics.record_authentication_attempt(success=True, method="password")
        span.set_attribute("auth.success", True)
        span.set_attribute("user.id", str(user.id))
        
        logger.info(
            "User logged in successfully",
            user_id=str(user.id),
            email=user.email,
            request_id=getattr(request.state, "request_id", None)
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    
    Validates refresh token and issues new access and refresh tokens.
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        credentials: HTTP Bearer credentials with refresh token
        
    Returns:
        New JWT tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    # Try to get refresh token from Authorization header or secure cookie
    refresh_token_value = None
    
    if credentials:
        refresh_token_value = credentials.credentials
    else:
        # Try to get from secure cookie
        refresh_token_value = cookie_manager.get_token_from_cookie(request, "refresh_token")
    
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify refresh token
    token_data = verify_token(refresh_token_value, "refresh")
    
    async with get_database_session() as session:
        # Verify user still exists and is active
        result = await session.execute(
            select(User).where(User.id == token_data.sub)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens (preserve workspace context if present)
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            tenant_id=token_data.tenant_id,
            role=token_data.role
        )
        
        new_refresh_token = create_refresh_token(
            user_id=str(user.id),
            email=user.email
        )
        
        # Set new secure cookies using cookie manager
        cookie_manager.set_auth_cookies(response, access_token, new_refresh_token)
        
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        
        logger.info(
            "Token refreshed successfully",
            user_id=str(user.id),
            email=user.email,
            request_id=getattr(request.state, "request_id", None)
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )


@router.post("/logout")
async def logout_user(
    request: Request,
    response: Response,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    """
    Logout user by clearing authentication cookies.
    
    Clears access and refresh token cookies.
    In a production system, this would also blacklist the tokens.
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        current_user: Currently authenticated user
        
    Returns:
        Success message
    """
    # Clear authentication cookies using cookie manager
    cookie_manager.clear_auth_cookies(response)
    
    logger.info(
        "User logged out successfully",
        user_id=current_user.id,
        email=current_user.email,
        request_id=getattr(request.state, "request_id", None)
    )
    
    # TODO: In production, add token to blacklist/revocation list
    # This would prevent the token from being used even if someone has it
    
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    """
    Get current authenticated user information.
    
    Returns user profile information for the authenticated user.
    
    Args:
        current_user: Currently authenticated user
        
    Returns:
        User profile information
    """
    async with get_database_session() as session:
        result = await session.execute(
            select(User).where(User.id == current_user.id)
        )
        user = result.scalar_one()
        
        # Get current workspace info if available
        workspace_info = None
        if current_user.tenant_id:
            from models.tenant import Tenant
            workspace_result = await session.execute(
                select(Tenant).where(Tenant.id == current_user.tenant_id)
            )
            workspace = workspace_result.scalar_one_or_none()
            if workspace:
                workspace_info = {
                    "id": str(workspace.id),
                    "name": workspace.name,
                    "slug": workspace.slug,
                    "role": current_user.role
                }
        
        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "is_verified": user.is_verified,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "current_workspace": workspace_info
        }


@router.post("/verify-email")
async def verify_email(
    request: Request,
    verification_token: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    """
    Verify user email address.
    
    This is a placeholder implementation. In production, this would:
    1. Validate a secure verification token sent via email
    2. Update the user's is_verified status
    
    Args:
        request: FastAPI request object
        verification_token: Email verification token
        current_user: Currently authenticated user
        
    Returns:
        Success message
    """
    # TODO: Implement proper email verification with secure tokens
    # For now, this is a placeholder that marks the user as verified
    
    async with get_database_session() as session:
        result = await session.execute(
            select(User).where(User.id == current_user.id)
        )
        user = result.scalar_one()
        
        if user.is_verified:
            return {"message": "Email already verified"}
        
        user.is_verified = True
        await session.commit()
        
        logger.info(
            "Email verified successfully",
            user_id=str(user.id),
            email=user.email,
            request_id=getattr(request.state, "request_id", None)
        )
        
        return {"message": "Email verified successfully"}