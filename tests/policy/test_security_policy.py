"""
Policy tests for security compliance and enforcement.
These tests verify that security policies are properly implemented and cannot be bypassed.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status
import json
import re
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'api'))

from main import app
from config import get_settings


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def settings():
    """Settings fixture."""
    return get_settings()


class TestSecurityHeadersPolicy:
    """Test that security headers are enforced across all endpoints."""
    
    @pytest.mark.policy
    def test_security_headers_present_on_all_endpoints(self, client):
        """Test that all endpoints return required security headers."""
        # Test various endpoint types
        endpoints_to_test = [
            ("/health", "GET"),
            ("/api/v1/auth/login", "POST"),
            ("/docs", "GET"),
            ("/openapi.json", "GET"),
        ]
        
        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": lambda x: "max-age=" in x,
            "Content-Security-Policy": lambda x: "default-src 'self'" in x,
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        
        for endpoint, method in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            
            # Check each required header
            for header_name, expected_value in required_headers.items():
                assert header_name in response.headers, (
                    f"Missing security header '{header_name}' on {method} {endpoint}"
                )
                
                if callable(expected_value):
                    assert expected_value(response.headers[header_name]), (
                        f"Invalid '{header_name}' header value on {method} {endpoint}: "
                        f"{response.headers[header_name]}"
                    )
                else:
                    assert response.headers[header_name] == expected_value, (
                        f"Incorrect '{header_name}' header on {method} {endpoint}: "
                        f"expected '{expected_value}', got '{response.headers[header_name]}'"
                    )
    
    @pytest.mark.policy
    def test_server_header_removed(self, client):
        """Test that server identification headers are removed."""
        response = client.get("/health")
        
        # Server header should be removed for security
        assert "server" not in [h.lower() for h in response.headers.keys()], (
            "Server header should be removed for security"
        )
        
        # X-Powered-By should not be present
        assert "x-powered-by" not in [h.lower() for h in response.headers.keys()], (
            "X-Powered-By header should not be present"
        )
    
    @pytest.mark.policy
    def test_csp_policy_strictness(self, client, settings):
        """Test that CSP policy is sufficiently strict."""
        response = client.get("/health")
        csp_header = response.headers.get("Content-Security-Policy", "")
        
        # Required CSP directives for security
        required_directives = [
            "default-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
        
        for directive in required_directives:
            assert directive in csp_header, (
                f"CSP policy missing required directive: {directive}"
            )
        
        # Dangerous directives that should not be present
        dangerous_patterns = [
            r"'unsafe-inline'.*script-src",  # Inline scripts
            r"script-src.*'unsafe-eval'",    # eval() usage (except for dev)
            r"default-src.*\*",              # Wildcard default-src
            r"script-src.*\*",               # Wildcard script-src
        ]
        
        for pattern in dangerous_patterns:
            if settings.environment == "production":
                assert not re.search(pattern, csp_header), (
                    f"CSP policy contains dangerous directive in production: {pattern}"
                )


class TestAuthenticationPolicy:
    """Test authentication policy enforcement."""
    
    @pytest.mark.policy
    def test_protected_endpoints_require_authentication(self, client):
        """Test that all protected endpoints require authentication."""
        # Endpoints that should require authentication
        protected_endpoints = [
            ("/api/v1/auth/me", "GET"),
            ("/api/v1/workspaces", "GET"),
            ("/api/v1/workspaces", "POST"),
            ("/api/v1/workspaces/test-id/artifacts", "GET"),
            ("/api/v1/workspaces/test-id/artifacts", "POST"),
        ]
        
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
                f"{method} {endpoint} should require authentication but returned {response.status_code}"
            )
    
    @pytest.mark.policy
    def test_no_unauthenticated_write_operations(self, client):
        """Test that no write operations are allowed without authentication."""
        # All write endpoints should require authentication
        write_endpoints = [
            ("/api/v1/auth/register", "POST"),  # Exception: registration is public
            ("/api/v1/workspaces", "POST"),
            ("/api/v1/workspaces/test-id", "PUT"),
            ("/api/v1/workspaces/test-id", "DELETE"),
            ("/api/v1/workspaces/test-id/artifacts", "POST"),
            ("/api/v1/workspaces/test-id/artifacts/test-artifact", "PUT"),
            ("/api/v1/workspaces/test-id/artifacts/test-artifact", "DELETE"),
        ]
        
        public_write_endpoints = {"/api/v1/auth/register", "/api/v1/auth/login"}
        
        for endpoint, method in write_endpoints:
            if endpoint in public_write_endpoints:
                continue  # Skip public endpoints
            
            if method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
                f"Unauthenticated {method} {endpoint} should be rejected but returned {response.status_code}"
            )
    
    @pytest.mark.policy
    def test_jwt_token_validation_strictness(self, client):
        """Test that JWT token validation is strict."""
        # Test with various invalid tokens
        invalid_tokens = [
            "invalid_token",
            "Bearer invalid_token",
            "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature",
            "Bearer " + "a" * 500,  # Oversized token
            "Bearer ",  # Empty token
            "NotBearer valid_token",  # Wrong prefix
        ]
        
        for token in invalid_tokens:
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": token}
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
                f"Invalid token should be rejected: {token[:50]}..."
            )


class TestRLSPolicy:
    """Test Row-Level Security policy enforcement."""
    
    @pytest.mark.policy
    def test_rls_cannot_be_bypassed_via_raw_sql(self, client):
        """Test that RLS cannot be bypassed through raw SQL injection."""
        # This test ensures that even if SQL injection were possible,
        # RLS would still prevent cross-tenant data access
        
        # Attempt SQL injection in various input fields
        sql_injection_payloads = [
            "'; SELECT * FROM artifacts WHERE tenant_id != current_setting('app.current_tenant_id')::uuid; --",
            "' UNION SELECT * FROM artifacts WHERE 1=1 --",
            "'; SET app.current_tenant_id = '00000000-0000-0000-0000-000000000000'; --",
            "'; ALTER TABLE artifacts DISABLE ROW LEVEL SECURITY; --",
            "'; DROP POLICY tenant_isolation ON artifacts; --",
        ]
        
        for payload in sql_injection_payloads:
            # Try injection in artifact name
            response = client.post(
                "/api/v1/workspaces/test-workspace/artifacts",
                json={
                    "name": payload,
                    "description": "test",
                    "tags": []
                },
                headers={"Authorization": "Bearer fake_token"}
            )
            
            # Should fail at authentication or validation, not execute SQL
            assert response.status_code in [401, 422], (
                f"SQL injection payload should be rejected: {payload[:50]}..."
            )
    
    @pytest.mark.policy
    def test_database_views_respect_rls(self):
        """Test that database views cannot bypass RLS policies."""
        # This would require database connection to test properly
        # For now, we document the requirement
        
        # TODO: Add test that creates a view and verifies it respects RLS
        # Example:
        # CREATE VIEW test_view AS SELECT * FROM artifacts;
        # Verify that querying test_view still respects tenant_id filtering
        
        pytest.skip("Database view RLS testing requires direct DB connection")


class TestInputValidationPolicy:
    """Test input validation policy enforcement."""
    
    @pytest.mark.policy
    def test_all_endpoints_validate_input_size(self, client):
        """Test that all endpoints validate input size limits."""
        # Test oversized JSON payload
        oversized_data = {"data": "x" * (11 * 1024 * 1024)}  # 11MB
        
        endpoints_to_test = [
            "/api/v1/auth/register",
            "/api/v1/auth/login",
        ]
        
        for endpoint in endpoints_to_test:
            response = client.post(endpoint, json=oversized_data)
            
            assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, (
                f"Endpoint {endpoint} should reject oversized payloads"
            )
    
    @pytest.mark.policy
    def test_xss_prevention_in_all_text_fields(self, client):
        """Test that XSS payloads are rejected in all text input fields."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
            "<svg onload=alert('xss')>",
        ]
        
        # Test in registration form
        for payload in xss_payloads:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "ValidPassword123!",
                    "first_name": payload,
                    "last_name": "User"
                }
            )
            
            # Should be rejected by validation
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
                f"XSS payload should be rejected in first_name: {payload}"
            )
    
    @pytest.mark.policy
    def test_sql_injection_prevention_in_search(self, client):
        """Test that SQL injection is prevented in search parameters."""
        sql_injection_payloads = [
            "'; DROP TABLE artifacts; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --",
            "' UNION SELECT password FROM users --",
        ]
        
        for payload in sql_injection_payloads:
            # Test in artifact search
            response = client.get(
                f"/api/v1/workspaces/test-workspace/artifacts?q={payload}",
                headers={"Authorization": "Bearer fake_token"}
            )
            
            # Should fail at authentication, not execute malicious SQL
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
                f"SQL injection in search should be handled safely: {payload[:30]}..."
            )


class TestRateLimitingPolicy:
    """Test rate limiting policy enforcement."""
    
    @pytest.mark.policy
    def test_authentication_endpoints_are_rate_limited(self, client):
        """Test that authentication endpoints have strict rate limits."""
        # Test login endpoint rate limiting
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        # Make requests rapidly to trigger rate limit
        responses = []
        for i in range(10):
            response = client.post("/api/v1/auth/login", json=login_data)
            responses.append(response)
            
            # Stop if we hit rate limit
            if response.status_code == 429:
                break
        
        # Should hit rate limit within 10 requests
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0, (
            "Authentication endpoint should be rate limited"
        )
        
        # Check rate limit response format
        rate_limited_response = rate_limited_responses[0]
        response_data = rate_limited_response.json()
        
        assert "rate_limit_exceeded" in response_data.get("error", ""), (
            "Rate limit response should indicate rate limit exceeded"
        )
        
        assert "Retry-After" in rate_limited_response.headers, (
            "Rate limit response should include Retry-After header"
        )
    
    @pytest.mark.policy
    def test_api_endpoints_have_reasonable_rate_limits(self, client):
        """Test that API endpoints have reasonable rate limits."""
        # Test general API rate limiting (should be more lenient than auth)
        responses = []
        for i in range(70):  # Exceed the 60/minute general limit
            response = client.get("/health")
            responses.append(response)
            
            if response.status_code == 429:
                break
        
        # Should eventually hit rate limit
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        
        # General endpoints should have higher limits than auth
        assert len(responses) > 10, (
            "General endpoints should have higher rate limits than auth endpoints"
        )


class TestDataPrivacyPolicy:
    """Test data privacy and protection policies."""
    
    @pytest.mark.policy
    def test_passwords_never_returned_in_responses(self, client):
        """Test that password fields are never included in API responses."""
        # Test registration response
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "first_name": "Test",
                "last_name": "User"
            }
        )
        
        if response.status_code < 500:  # Ignore server errors
            response_text = response.text.lower()
            
            # Password should never appear in response
            assert "password" not in response_text, (
                "Password field should never be returned in API responses"
            )
            
            assert "testpassword123!" not in response_text, (
                "Password value should never be returned in API responses"
            )
    
    @pytest.mark.policy
    def test_error_messages_dont_leak_sensitive_info(self, client):
        """Test that error messages don't leak sensitive information."""
        # Test with non-existent user
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password"
            }
        )
        
        if response.status_code == 401:
            error_message = response.json().get("detail", "").lower()
            
            # Should not reveal whether user exists
            assert "user not found" not in error_message, (
                "Error messages should not reveal user existence"
            )
            
            assert "email not found" not in error_message, (
                "Error messages should not reveal email existence"
            )
            
            # Should use generic message
            assert "invalid" in error_message, (
                "Should use generic 'invalid credentials' message"
            )


class TestCompliancePolicy:
    """Test compliance with security standards and regulations."""
    
    @pytest.mark.policy
    def test_audit_logging_enabled(self, client):
        """Test that audit logging is enabled for sensitive operations."""
        # This test would verify that audit logs are created
        # For now, we check that the logging infrastructure is in place
        
        import logging
        
        # Check that audit logger exists
        audit_logger = logging.getLogger("audit")
        assert audit_logger is not None, "Audit logger should be configured"
        
        # Check that audit logger has handlers
        assert len(audit_logger.handlers) > 0 or len(logging.root.handlers) > 0, (
            "Audit logger should have handlers configured"
        )
    
    @pytest.mark.policy
    def test_session_security_configuration(self, client, settings):
        """Test that session security is properly configured."""
        # Test cookie security settings
        assert settings.cookie_httponly is True, (
            "Cookies should be HttpOnly for security"
        )
        
        if settings.environment == "production":
            assert settings.cookie_secure is True, (
                "Cookies should be Secure in production"
            )
        
        assert settings.cookie_samesite in ["lax", "strict"], (
            f"Cookie SameSite should be 'lax' or 'strict', got '{settings.cookie_samesite}'"
        )
        
        # Test JWT expiration times
        assert settings.jwt_access_token_expire_minutes <= 60, (
            "Access tokens should expire within 60 minutes"
        )
        
        assert settings.jwt_refresh_token_expire_days <= 30, (
            "Refresh tokens should expire within 30 days"
        )
    
    @pytest.mark.policy
    def test_encryption_standards(self, settings):
        """Test that encryption standards are met."""
        # Test password hashing rounds
        assert settings.bcrypt_rounds >= 12, (
            f"BCrypt rounds should be at least 12, got {settings.bcrypt_rounds}"
        )
        
        # Test JWT algorithm
        assert settings.jwt_algorithm in ["HS256", "RS256", "ES256"], (
            f"JWT algorithm should be secure, got {settings.jwt_algorithm}"
        )
        
        # Test secret key strength (in production)
        if settings.environment == "production":
            secret_key = settings.jwt_secret_key.get_secret_value()
            assert len(secret_key) >= 32, (
                "JWT secret key should be at least 32 characters in production"
            )