"""
Tests for authentication functionality.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select
import uuid

from main import app
from auth import hash_password, verify_password, create_access_token, verify_token, validate_password_strength
from models.user import User
from database import get_async_session


client = TestClient(app)


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        assert hashed.startswith("$2b$")  # bcrypt prefix
    
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


class TestPasswordValidation:
    """Test password strength validation."""
    
    def test_valid_password(self):
        """Test that valid password passes validation."""
        password = "ValidPassword123!"
        # Should not raise exception
        validate_password_strength(password)
    
    def test_password_too_short(self):
        """Test that short password fails validation."""
        password = "Short1!"
        with pytest.raises(Exception) as exc_info:
            validate_password_strength(password)
        assert "at least 8 characters" in str(exc_info.value)
    
    def test_password_no_uppercase(self):
        """Test that password without uppercase fails validation."""
        password = "lowercase123!"
        with pytest.raises(Exception) as exc_info:
            validate_password_strength(password)
        assert "uppercase letter" in str(exc_info.value)
    
    def test_password_no_lowercase(self):
        """Test that password without lowercase fails validation."""
        password = "UPPERCASE123!"
        with pytest.raises(Exception) as exc_info:
            validate_password_strength(password)
        assert "lowercase letter" in str(exc_info.value)
    
    def test_password_no_digit(self):
        """Test that password without digit fails validation."""
        password = "NoDigitsHere!"
        with pytest.raises(Exception) as exc_info:
            validate_password_strength(password)
        assert "digit" in str(exc_info.value)
    
    def test_password_no_special_char(self):
        """Test that password without special character fails validation."""
        password = "NoSpecialChars123"
        with pytest.raises(Exception) as exc_info:
            validate_password_strength(password)
        assert "special character" in str(exc_info.value)


class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        
        token = create_access_token(user_id, email)
        
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are long
    
    def test_verify_access_token(self):
        """Test access token verification."""
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        
        token = create_access_token(user_id, email)
        token_data = verify_token(token, "access")
        
        assert token_data.sub == user_id
        assert token_data.email == email
        assert token_data.token_type == "access"
    
    def test_verify_expired_token(self):
        """Test that expired token fails verification."""
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        
        # Create token that expires immediately
        token = create_access_token(
            user_id, 
            email, 
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(Exception) as exc_info:
            verify_token(token, "access")
        assert "401" in str(exc_info.value)
    
    def test_verify_wrong_token_type(self):
        """Test that wrong token type fails verification."""
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        
        token = create_access_token(user_id, email)
        
        with pytest.raises(Exception) as exc_info:
            verify_token(token, "refresh")
        assert "Invalid token type" in str(exc_info.value)


class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""
    
    @pytest.fixture
    def test_user_data(self):
        """Test user registration data."""
        return {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
    
    def test_register_user_success(self, test_user_data):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "user_id" in data
        assert data["verification_required"] is True
    
    def test_register_user_weak_password(self, test_user_data):
        """Test user registration with weak password."""
        test_user_data["password"] = "weak"
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 422
        assert "at least 8 characters" in response.json()["detail"]
    
    def test_register_user_invalid_email(self, test_user_data):
        """Test user registration with invalid email."""
        test_user_data["email"] = "invalid-email"
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 422
    
    def test_register_duplicate_email(self, test_user_data):
        """Test user registration with duplicate email."""
        # Register first user
        response1 = client.post("/api/v1/auth/register", json=test_user_data)
        assert response1.status_code == 201
        
        # Try to register with same email
        response2 = client.post("/api/v1/auth/register", json=test_user_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]
    
    def test_login_success(self, test_user_data):
        """Test successful user login."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        
        # Check that cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
    
    def test_login_invalid_email(self):
        """Test login with non-existent email."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "TestPassword123!"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, test_user_data):
        """Test login with incorrect password."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_get_current_user_authenticated(self, test_user_data):
        """Test getting current user info when authenticated."""
        # Register and login user
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        
        # Get current user info
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["first_name"] == test_user_data["first_name"]
        assert data["last_name"] == test_user_data["last_name"]
        assert "id" in data
        assert "created_at" in data
    
    def test_get_current_user_unauthenticated(self):
        """Test getting current user info when not authenticated."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
    
    def test_logout_success(self, test_user_data):
        """Test successful logout."""
        # Register and login user
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/api/v1/auth/logout", headers=headers)
        
        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]
    
    def test_refresh_token_success(self, test_user_data):
        """Test successful token refresh."""
        # Register and login user
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        headers = {"Authorization": f"Bearer {refresh_token}"}
        response = client.post("/api/v1/auth/refresh", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"