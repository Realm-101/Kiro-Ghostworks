"""
Unit tests for authentication endpoints.
Tests individual authentication functions and endpoints in isolation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'api'))

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    AuthenticatedUser
)
from routes.auth import (
    register_user,
    login_user,
    refresh_token,
    get_current_user_info,
    logout_user
)
from models.user import User
from auth import UserRegistrationRequest, UserLoginRequest


class TestPasswordUtilities:
    """Unit tests for password hashing and verification utilities."""
    
    def test_hash_password(self):
        """Test password hashing function."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_hash_password_different_results(self):
        """Test that hashing the same password produces different results."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokenUtilities:
    """Unit tests for JWT token creation and verification utilities."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        user_id = "test-user-id"
        email = "test@example.com"
        
        token = create_access_token(user_id=user_id, email=email)
        
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are typically long
        assert token.count('.') == 2  # JWT has 3 parts separated by dots
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "test-user-id"
        email = "test@example.com"
        
        token = create_refresh_token(user_id=user_id, email=email)
        
        assert isinstance(token, str)
        assert len(token) > 100
        assert token.count('.') == 2
    
    def test_verify_access_token(self):
        """Test access token verification."""
        user_id = "test-user-id"
        email = "test@example.com"
        
        token = create_access_token(user_id=user_id, email=email)
        token_data = verify_token(token, "access")
        
        assert token_data.sub == user_id
        assert token_data.email == email
        assert token_data.token_type == "access"
        assert token_data.exp > datetime.utcnow()
    
    def test_verify_refresh_token(self):
        """Test refresh token verification."""
        user_id = "test-user-id"
        email = "test@example.com"
        
        token = create_refresh_token(user_id=user_id, email=email)
        token_data = verify_token(token, "refresh")
        
        assert token_data.sub == user_id
        assert token_data.email == email
        assert token_data.token_type == "refresh"
        assert token_data.exp > datetime.utcnow()
    
    def test_verify_token_wrong_type(self):
        """Test token verification with wrong token type."""
        user_id = "test-user-id"
        email = "test@example.com"
        
        access_token = create_access_token(user_id=user_id, email=email)
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(access_token, "refresh")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token, "access")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_verify_expired_token(self):
        """Test verification of expired token."""
        user_id = "test-user-id"
        email = "test@example.com"
        
        # Create token that expires immediately
        expired_token = create_access_token(
            user_id=user_id,
            email=email,
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token, "access")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthenticationEndpoints:
    """Unit tests for authentication endpoint functions."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """Test successful user registration."""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.return_value.scalar_one_or_none.return_value = None  # No existing user
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        # Mock user creation
        mock_user = User(
            id="test-user-id",
            email="test@example.com",
            hashed_password="hashed_password",
            first_name="Test",
            last_name="User",
            is_verified=True,
            is_active=True
        )
        
        with patch('routes.auth.User') as mock_user_class:
            mock_user_class.return_value = mock_user
            
            request_data = UserRegistrationRequest(
                email="test@example.com",
                password="TestPassword123!",
                first_name="Test",
                last_name="User"
            )
            
            result = await register_user(request_data, mock_session)
            
            assert result["email"] == request_data.email
            assert result["first_name"] == request_data.first_name
            assert result["last_name"] == request_data.last_name
            assert "user_id" in result
            assert result["verification_required"] is True
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self):
        """Test user registration with duplicate email."""
        # Mock database session with existing user
        mock_session = AsyncMock(spec=AsyncSession)
        existing_user = User(email="test@example.com")
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_user
        
        request_data = UserRegistrationRequest(
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await register_user(request_data, mock_session)
        
        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already registered" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_login_user_success(self):
        """Test successful user login."""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock user with correct password
        mock_user = User(
            id="test-user-id",
            email="test@example.com",
            hashed_password=hash_password("TestPassword123!"),
            is_verified=True,
            is_active=True
        )
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        request_data = UserLoginRequest(
            email="test@example.com",
            password="TestPassword123!"
        )
        
        result = await login_user(request_data, mock_session)
        
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        assert "expires_in" in result
        assert isinstance(result["expires_in"], int)
    
    @pytest.mark.asyncio
    async def test_login_user_invalid_email(self):
        """Test login with non-existent email."""
        # Mock database session with no user found
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        request_data = UserLoginRequest(
            email="nonexistent@example.com",
            password="TestPassword123!"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await login_user(request_data, mock_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_login_user_invalid_password(self):
        """Test login with incorrect password."""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock user with different password
        mock_user = User(
            id="test-user-id",
            email="test@example.com",
            hashed_password=hash_password("CorrectPassword123!"),
            is_verified=True,
            is_active=True
        )
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        request_data = UserLoginRequest(
            email="test@example.com",
            password="WrongPassword123!"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await login_user(request_data, mock_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_login_user_inactive_account(self):
        """Test login with inactive user account."""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock inactive user
        mock_user = User(
            id="test-user-id",
            email="test@example.com",
            hashed_password=hash_password("TestPassword123!"),
            is_verified=True,
            is_active=False  # Inactive account
        )
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        request_data = UserLoginRequest(
            email="test@example.com",
            password="TestPassword123!"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await login_user(request_data, mock_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Account is not active" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test successful token refresh."""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock user
        mock_user = User(
            id="test-user-id",
            email="test@example.com",
            is_verified=True,
            is_active=True
        )
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        # Mock authenticated user from refresh token
        mock_auth_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        result = await refresh_token(mock_auth_user, mock_session)
        
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        assert "expires_in" in result
    
    @pytest.mark.asyncio
    async def test_get_user_info_success(self):
        """Test getting user information."""
        # Mock authenticated user
        mock_auth_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        result = await get_current_user_info(mock_auth_user)
        
        assert result["id"] == mock_auth_user.id
        assert result["email"] == mock_auth_user.email
        assert result["is_verified"] == mock_auth_user.is_verified
        assert result["is_active"] == mock_auth_user.is_active
    
    @pytest.mark.asyncio
    async def test_logout_user_success(self):
        """Test successful user logout."""
        # Mock authenticated user
        mock_auth_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        result = await logout_user(mock_auth_user)
        
        assert "message" in result
        assert "Logged out successfully" in result["message"]


class TestAuthenticationDependencies:
    """Unit tests for authentication dependency functions."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test successful current user retrieval."""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock user from database
        mock_user = User(
            id="test-user-id",
            email="test@example.com",
            is_verified=True,
            is_active=True
        )
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        # Create valid token
        token = create_access_token(
            user_id="test-user-id",
            email="test@example.com"
        )
        
        result = await get_current_user(token, mock_session)
        
        assert isinstance(result, AuthenticatedUser)
        assert result.id == "test-user-id"
        assert result.email == "test@example.com"
        assert result.is_verified is True
        assert result.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test current user retrieval with invalid token."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("invalid_token", mock_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self):
        """Test current user retrieval when user doesn't exist in database."""
        # Mock database session with no user found
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        # Create valid token for non-existent user
        token = create_access_token(
            user_id="nonexistent-user-id",
            email="nonexistent@example.com"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token, mock_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(self):
        """Test current user retrieval with inactive user."""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock inactive user
        mock_user = User(
            id="test-user-id",
            email="test@example.com",
            is_verified=True,
            is_active=False  # Inactive user
        )
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        # Create valid token
        token = create_access_token(
            user_id="test-user-id",
            email="test@example.com"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token, mock_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User account is not active" in exc_info.value.detail


class TestAuthenticatedUserModel:
    """Unit tests for AuthenticatedUser model."""
    
    def test_authenticated_user_creation(self):
        """Test AuthenticatedUser model creation."""
        user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="admin",
            is_verified=True,
            is_active=True
        )
        
        assert user.id == "test-user-id"
        assert user.email == "test@example.com"
        assert user.tenant_id == "test-tenant-id"
        assert user.role == "admin"
        assert user.is_verified is True
        assert user.is_active is True
    
    def test_authenticated_user_without_workspace(self):
        """Test AuthenticatedUser model without workspace context."""
        user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        assert user.tenant_id is None
        assert user.role is None
        assert user.has_workspace_context() is False
    
    def test_authenticated_user_with_workspace(self):
        """Test AuthenticatedUser model with workspace context."""
        user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        assert user.has_workspace_context() is True
        assert user.can_access_workspace("test-tenant-id") is True
        assert user.can_access_workspace("other-tenant-id") is False