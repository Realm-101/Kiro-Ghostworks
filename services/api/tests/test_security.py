"""
Tests for security middleware and hardening features.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import json

from main import app
from security import SecurityHeadersMiddleware, InputValidationMiddleware, cookie_manager
from config import get_settings


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def settings():
    """Settings fixture."""
    return get_settings()


class TestSecurityHeaders:
    """Test security headers middleware."""
    
    def test_security_headers_present(self, client):
        """Test that security headers are present in responses."""
        response = client.get("/health")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        
        assert "Strict-Transport-Security" in response.headers
        assert "max-age=" in response.headers["Strict-Transport-Security"]
        
        assert "Content-Security-Policy" in response.headers
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]
        
        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    
    def test_server_header_removed(self, client):
        """Test that server header is removed for security."""
        response = client.get("/health")
        assert "server" not in response.headers.keys()


class TestInputValidation:
    """Test input validation middleware."""
    
    def test_oversized_request_rejected(self, client):
        """Test that oversized requests are rejected."""
        # Create a large payload
        large_data = {"data": "x" * (11 * 1024 * 1024)}  # 11MB
        
        response = client.post(
            "/api/v1/auth/register",
            json=large_data,
            headers={"Content-Length": str(len(json.dumps(large_data)))}
        )
        
        assert response.status_code == 413
        assert "request_too_large" in response.json()["error"]
    
    def test_invalid_content_length_rejected(self, client):
        """Test that invalid content-length headers are rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password"},
            headers={"Content-Length": "invalid"}
        )
        
        assert response.status_code == 400
        assert "invalid_content_length" in response.json()["error"]


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_auth_rate_limiting(self, client):
        """Test that authentication endpoints are rate limited."""
        # Make multiple rapid requests to exceed rate limit
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        responses = []
        for _ in range(10):  # Exceed the 5/minute limit
            response = client.post("/api/v1/auth/login", json=login_data)
            responses.append(response)
        
        # At least one response should be rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Expected at least one rate limited response"
        
        # Check rate limit response format
        rate_limited_response = next(r for r in responses if r.status_code == 429)
        assert "rate_limit_exceeded" in rate_limited_response.json()["error"]
        assert "Retry-After" in rate_limited_response.headers


class TestSecureCookies:
    """Test secure cookie management."""
    
    def test_cookie_security_attributes(self, settings):
        """Test that cookies have proper security attributes."""
        from fastapi import Response
        
        response = Response()
        access_token = "test_access_token"
        refresh_token = "test_refresh_token"
        
        cookie_manager.set_auth_cookies(response, access_token, refresh_token)
        
        # Check that cookies are set with security attributes
        set_cookie_headers = response.headers.getlist("set-cookie")
        
        access_cookie = next(
            (cookie for cookie in set_cookie_headers if "access_token" in cookie),
            None
        )
        refresh_cookie = next(
            (cookie for cookie in set_cookie_headers if "refresh_token" in cookie),
            None
        )
        
        assert access_cookie is not None
        assert refresh_cookie is not None
        
        # Check security attributes
        if settings.cookie_httponly:
            assert "HttpOnly" in access_cookie
            assert "HttpOnly" in refresh_cookie
        
        if settings.cookie_secure:
            assert "Secure" in access_cookie
            assert "Secure" in refresh_cookie
        
        assert f"SameSite={settings.cookie_samesite}" in access_cookie
        assert f"SameSite={settings.cookie_samesite}" in refresh_cookie
    
    def test_cookie_extraction(self):
        """Test token extraction from cookies."""
        from fastapi import Request
        from unittest.mock import Mock
        
        # Mock request with cookie
        request = Mock(spec=Request)
        request.cookies = {"access_token": "Bearer test_token_value"}
        
        token = cookie_manager.get_token_from_cookie(request, "access_token")
        assert token == "test_token_value"
        
        # Test with missing cookie
        request.cookies = {}
        token = cookie_manager.get_token_from_cookie(request, "access_token")
        assert token is None
        
        # Test with malformed cookie
        request.cookies = {"access_token": "malformed_token"}
        token = cookie_manager.get_token_from_cookie(request, "access_token")
        assert token is None


class TestInputSanitization:
    """Test input sanitization and validation."""
    
    def test_artifact_name_validation(self, client):
        """Test artifact name validation."""
        # Test with malicious input
        malicious_data = {
            "name": "<script>alert('xss')</script>",
            "description": "Test description",
            "tags": ["test"]
        }
        
        # This should be rejected by validation
        response = client.post(
            "/api/v1/workspaces/test-workspace/artifacts",
            json=malicious_data,
            headers={"Authorization": "Bearer fake_token"}
        )
        
        # Should fail validation before reaching auth
        assert response.status_code in [401, 422]  # Auth or validation error
    
    def test_tag_validation(self):
        """Test tag validation in artifact schema."""
        from schemas.artifact import CreateArtifactRequest
        
        # Test with too many tags
        with pytest.raises(ValueError, match="Maximum 20 tags allowed"):
            CreateArtifactRequest(
                name="Test",
                tags=[f"tag{i}" for i in range(25)]
            )
        
        # Test with invalid characters
        with pytest.raises(ValueError, match="Tags can only contain"):
            CreateArtifactRequest(
                name="Test",
                tags=["valid_tag", "<script>"]
            )
        
        # Test with oversized tag
        with pytest.raises(ValueError, match="Tag length cannot exceed"):
            CreateArtifactRequest(
                name="Test",
                tags=["x" * 60]
            )
    
    def test_metadata_validation(self):
        """Test metadata validation in artifact schema."""
        from schemas.artifact import CreateArtifactRequest
        
        # Test with too many keys
        large_metadata = {f"key{i}": f"value{i}" for i in range(60)}
        with pytest.raises(ValueError, match="Maximum 50 metadata keys allowed"):
            CreateArtifactRequest(
                name="Test",
                artifact_metadata=large_metadata
            )
        
        # Test with invalid key characters
        with pytest.raises(ValueError, match="Metadata keys can only contain"):
            CreateArtifactRequest(
                name="Test",
                artifact_metadata={"<script>": "value"}
            )
        
        # Test with oversized value
        with pytest.raises(ValueError, match="Metadata string values cannot exceed"):
            CreateArtifactRequest(
                name="Test",
                artifact_metadata={"key": "x" * 1100}
            )


class TestPasswordValidation:
    """Test password validation."""
    
    def test_password_strength_validation(self):
        """Test password strength requirements."""
        from auth import UserRegistrationRequest
        
        # Test weak passwords
        weak_passwords = [
            "short",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoNumbers!",  # No numbers
            "NoSpecialChars123",  # No special characters
        ]
        
        for password in weak_passwords:
            with pytest.raises(ValueError):
                UserRegistrationRequest(
                    email="test@example.com",
                    password=password
                )
        
        # Test valid password
        valid_request = UserRegistrationRequest(
            email="test@example.com",
            password="ValidPassword123!"
        )
        assert valid_request.password == "ValidPassword123!"
    
    def test_name_validation(self):
        """Test name field validation."""
        from auth import UserRegistrationRequest
        
        # Test with malicious input
        with pytest.raises(ValueError, match="Name contains invalid characters"):
            UserRegistrationRequest(
                email="test@example.com",
                password="ValidPassword123!",
                first_name="<script>alert('xss')</script>"
            )
        
        # Test with oversized input
        with pytest.raises(ValueError, match="Name must be less than 50 characters"):
            UserRegistrationRequest(
                email="test@example.com",
                password="ValidPassword123!",
                first_name="x" * 60
            )


class TestWorkspaceValidation:
    """Test workspace validation."""
    
    def test_workspace_name_validation(self):
        """Test workspace name validation."""
        from schemas.workspace import CreateWorkspaceRequest
        
        # Test with malicious input
        with pytest.raises(ValueError, match="Workspace name contains invalid characters"):
            CreateWorkspaceRequest(name="<script>alert('xss')</script>")
        
        # Test with invalid start character
        with pytest.raises(ValueError, match="Workspace name must start with"):
            CreateWorkspaceRequest(name="-invalid-start")
        
        # Test too short
        with pytest.raises(ValueError, match="Workspace name must be at least 2 characters"):
            CreateWorkspaceRequest(name="a")
        
        # Test valid name
        valid_request = CreateWorkspaceRequest(name="Valid Workspace Name")
        assert valid_request.name == "Valid Workspace Name"
    
    def test_email_validation_in_invite(self):
        """Test email validation in member invite."""
        from schemas.workspace import InviteMemberRequest
        
        # Test with oversized email
        long_email = "x" * 250 + "@example.com"
        with pytest.raises(ValueError, match="Email address is too long"):
            InviteMemberRequest(email=long_email, role="member")
        
        # Test with invalid characters
        with pytest.raises(ValueError, match="Email contains invalid characters"):
            InviteMemberRequest(email="test\x00@example.com", role="member")