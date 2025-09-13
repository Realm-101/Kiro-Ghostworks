"""
Integration tests for authentication flows.
Tests the complete authentication workflow including registration, login, token refresh, and logout.
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from tests.utils.test_helpers import (
    TestDataFactory,
    APITestHelper,
    AssertionHelper
)


class TestAuthenticationIntegration:
    """Integration tests for authentication workflows."""
    
    async def test_complete_registration_flow(self, async_client: AsyncClient):
        """Test complete user registration flow."""
        # Create user data
        user_data = TestDataFactory.create_user_data(
            email="integration_test@example.com",
            first_name="Integration",
            last_name="Test"
        )
        
        # Register user
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        
        response_data = response.json()
        assert response_data["email"] == user_data["email"]
        assert response_data["first_name"] == user_data["first_name"]
        assert response_data["last_name"] == user_data["last_name"]
        assert response_data["verification_required"] is True
        assert "user_id" in response_data
        assert "created_at" in response_data
    
    async def test_complete_login_flow(self, async_client: AsyncClient):
        """Test complete user login flow."""
        # Register user first
        user_data = TestDataFactory.create_user_data(email="login_test@example.com")
        await APITestHelper.register_user(async_client, user_data)
        
        # Login user
        login_response = await APITestHelper.login_user(
            async_client, 
            user_data["email"], 
            user_data["password"]
        )
        
        # Verify login response
        assert "access_token" in login_response
        assert "refresh_token" in login_response
        assert login_response["token_type"] == "bearer"
        assert "expires_in" in login_response
        assert isinstance(login_response["expires_in"], int)
        assert login_response["expires_in"] > 0
    
    async def test_authenticated_user_info_flow(self, async_client: AsyncClient):
        """Test getting authenticated user information."""
        # Register and login user
        user_data = TestDataFactory.create_user_data(email="userinfo_test@example.com")
        await APITestHelper.register_user(async_client, user_data)
        
        login_response = await APITestHelper.login_user(
            async_client,
            user_data["email"],
            user_data["password"]
        )
        
        # Get user info with token
        headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        user_info = response.json()
        assert user_info["email"] == user_data["email"]
        assert user_info["first_name"] == user_data["first_name"]
        assert user_info["last_name"] == user_data["last_name"]
        assert user_info["is_verified"] is True
        assert user_info["is_active"] is True
        assert "id" in user_info
        assert "created_at" in user_info
    
    async def test_token_refresh_flow(self, async_client: AsyncClient):
        """Test token refresh workflow."""
        # Register and login user
        user_data = TestDataFactory.create_user_data(email="refresh_test@example.com")
        await APITestHelper.register_user(async_client, user_data)
        
        login_response = await APITestHelper.login_user(
            async_client,
            user_data["email"],
            user_data["password"]
        )
        
        # Use refresh token to get new access token
        refresh_headers = {"Authorization": f"Bearer {login_response['refresh_token']}"}
        response = await async_client.post("/api/v1/auth/refresh", headers=refresh_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        refresh_response = response.json()
        assert "access_token" in refresh_response
        assert "refresh_token" in refresh_response
        assert refresh_response["token_type"] == "bearer"
        assert "expires_in" in refresh_response
        
        # Verify new access token works
        new_headers = {"Authorization": f"Bearer {refresh_response['access_token']}"}
        user_response = await async_client.get("/api/v1/auth/me", headers=new_headers)
        assert user_response.status_code == status.HTTP_200_OK
    
    async def test_logout_flow(self, async_client: AsyncClient):
        """Test user logout workflow."""
        # Register and login user
        user_data = TestDataFactory.create_user_data(email="logout_test@example.com")
        await APITestHelper.register_user(async_client, user_data)
        
        login_response = await APITestHelper.login_user(
            async_client,
            user_data["email"],
            user_data["password"]
        )
        
        # Logout user
        headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        response = await async_client.post("/api/v1/auth/logout", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        logout_response = response.json()
        assert "message" in logout_response
        assert "Logged out successfully" in logout_response["message"]


class TestAuthenticationErrorHandling:
    """Integration tests for authentication error scenarios."""
    
    async def test_duplicate_email_registration(self, async_client: AsyncClient):
        """Test registration with duplicate email."""
        user_data = TestDataFactory.create_user_data(email="duplicate@example.com")
        
        # Register user first time
        response1 = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Try to register with same email
        response2 = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == status.HTTP_409_CONFLICT
        
        error_data = response2.json()
        AssertionHelper.assert_error_response(error_data, "user_already_exists")
    
    async def test_invalid_login_credentials(self, async_client: AsyncClient):
        """Test login with invalid credentials."""
        # Test with non-existent email
        login_data = {
            "email": "nonexistent@example.com",
            "password": "TestPassword123!"
        }
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        error_data = response.json()
        assert "Invalid email or password" in error_data["detail"]
        
        # Register user and test with wrong password
        user_data = TestDataFactory.create_user_data(email="wrongpass@example.com")
        await APITestHelper.register_user(async_client, user_data)
        
        wrong_login_data = {
            "email": user_data["email"],
            "password": "WrongPassword123!"
        }
        response = await async_client.post("/api/v1/auth/login", json=wrong_login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_invalid_token_access(self, async_client: AsyncClient):
        """Test API access with invalid tokens."""
        # Test with no token
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test with malformed token
        headers = {"Authorization": "InvalidFormat"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_expired_token_handling(self, async_client: AsyncClient):
        """Test handling of expired tokens."""
        from datetime import timedelta
        from auth import create_access_token
        
        # Create an expired token
        expired_token = create_access_token(
            user_id="test-user-id",
            email="test@example.com",
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        error_data = response.json()
        assert "Could not validate credentials" in error_data["detail"]


class TestPasswordValidationIntegration:
    """Integration tests for password validation."""
    
    @pytest.mark.parametrize("invalid_password,expected_error", [
        ("short", "at least 8 characters"),
        ("nouppercase123!", "uppercase letter"),
        ("NOLOWERCASE123!", "lowercase letter"),
        ("NoDigitsHere!", "digit"),
        ("NoSpecialChars123", "special character"),
    ])
    async def test_password_validation_errors(
        self, 
        async_client: AsyncClient, 
        invalid_password: str, 
        expected_error: str
    ):
        """Test various password validation errors."""
        user_data = TestDataFactory.create_user_data(
            email="password_test@example.com",
            password=invalid_password
        )
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert expected_error in error_data["detail"]
    
    async def test_valid_password_acceptance(self, async_client: AsyncClient):
        """Test that valid passwords are accepted."""
        valid_passwords = [
            "ValidPassword123!",
            "AnotherGood1@",
            "Complex#Pass9",
            "Secure$123Pass"
        ]
        
        for i, password in enumerate(valid_passwords):
            user_data = TestDataFactory.create_user_data(
                email=f"valid_pass_{i}@example.com",
                password=password
            )
            
            response = await async_client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == status.HTTP_201_CREATED


class TestAuthenticationSecurity:
    """Integration tests for authentication security features."""
    
    async def test_token_type_validation(self, async_client: AsyncClient):
        """Test that token types are properly validated."""
        # Register and login user
        user_data = TestDataFactory.create_user_data(email="token_type@example.com")
        await APITestHelper.register_user(async_client, user_data)
        
        login_response = await APITestHelper.login_user(
            async_client,
            user_data["email"],
            user_data["password"]
        )
        
        # Try to use refresh token for access endpoint
        refresh_headers = {"Authorization": f"Bearer {login_response['refresh_token']}"}
        response = await async_client.get("/api/v1/auth/me", headers=refresh_headers)
        
        # This should fail because we're using a refresh token for an access endpoint
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_password_hashing_security(self, async_client: AsyncClient):
        """Test that passwords are properly hashed and not stored in plain text."""
        from database import get_database_session
        from models.user import User
        from sqlalchemy import select
        
        user_data = TestDataFactory.create_user_data(email="hash_test@example.com")
        
        # Register user
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        user_id = response.json()["user_id"]
        
        # Check that password is hashed in database
        async with get_database_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one()
            
            # Password should be hashed (bcrypt format)
            assert user.hashed_password != user_data["password"]
            assert user.hashed_password.startswith("$2b$")
            assert len(user.hashed_password) > 50
    
    async def test_jwt_token_structure(self, async_client: AsyncClient):
        """Test JWT token structure and claims."""
        from auth import verify_token
        
        # Register and login user
        user_data = TestDataFactory.create_user_data(email="jwt_test@example.com")
        await APITestHelper.register_user(async_client, user_data)
        
        login_response = await APITestHelper.login_user(
            async_client,
            user_data["email"],
            user_data["password"]
        )
        
        # Verify access token structure
        access_token = login_response["access_token"]
        token_data = verify_token(access_token, "access")
        
        assert token_data.email == user_data["email"]
        assert token_data.token_type == "access"
        assert token_data.sub is not None
        assert token_data.exp is not None
        assert token_data.iat is not None
        assert token_data.jti is not None
        
        # Verify refresh token structure
        refresh_token = login_response["refresh_token"]
        refresh_data = verify_token(refresh_token, "refresh")
        
        assert refresh_data.email == user_data["email"]
        assert refresh_data.token_type == "refresh"
        assert refresh_data.sub == token_data.sub  # Same user