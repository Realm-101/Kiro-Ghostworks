#!/usr/bin/env python3
"""
Quick test script to verify security hardening implementation.
"""

from fastapi.testclient import TestClient
from main import app
from security import SecurityHeadersMiddleware, cookie_manager
from config import get_settings

def test_security_headers():
    """Test that security headers are present."""
    client = TestClient(app)
    response = client.get("/health")
    
    print("=== Security Headers Test ===")
    print(f"Status Code: {response.status_code}")
    
    expected_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options", 
        "X-XSS-Protection",
        "Strict-Transport-Security",
        "Content-Security-Policy",
        "Referrer-Policy"
    ]
    
    for header in expected_headers:
        if header in response.headers:
            print(f"✓ {header}: {response.headers[header]}")
        else:
            print(f"✗ {header}: NOT FOUND")
    
    # Check server header is removed
    if "server" not in response.headers:
        print("✓ Server header removed")
    else:
        print(f"✗ Server header present: {response.headers['server']}")
    
    print()

def test_input_validation():
    """Test input validation schemas."""
    print("=== Input Validation Test ===")
    
    try:
        from schemas.artifact import CreateArtifactRequest
        
        # Test valid artifact
        valid_artifact = CreateArtifactRequest(
            name="Test Artifact",
            description="A test artifact",
            tags=["test", "valid"]
        )
        print("✓ Valid artifact creation passed")
        
        # Test invalid artifact with XSS
        try:
            invalid_artifact = CreateArtifactRequest(
                name="<script>alert('xss')</script>",
                description="Test",
                tags=["test"]
            )
            print("✗ XSS validation failed - should have been rejected")
        except ValueError as e:
            print(f"✓ XSS validation passed: {e}")
        
        # Test oversized tags
        try:
            oversized_tags = CreateArtifactRequest(
                name="Test",
                tags=[f"tag{i}" for i in range(25)]  # Over 20 limit
            )
            print("✗ Tag limit validation failed")
        except ValueError as e:
            print(f"✓ Tag limit validation passed: {e}")
            
    except Exception as e:
        print(f"✗ Input validation test failed: {e}")
    
    print()

def test_password_validation():
    """Test password validation."""
    print("=== Password Validation Test ===")
    
    try:
        from auth import UserRegistrationRequest
        
        # Test weak password
        try:
            weak_user = UserRegistrationRequest(
                email="test@example.com",
                password="weak"
            )
            print("✗ Weak password validation failed")
        except ValueError as e:
            print(f"✓ Weak password rejected: {e}")
        
        # Test strong password
        strong_user = UserRegistrationRequest(
            email="test@example.com", 
            password="StrongPassword123!"
        )
        print("✓ Strong password accepted")
        
    except Exception as e:
        print(f"✗ Password validation test failed: {e}")
    
    print()

def test_configuration():
    """Test security configuration."""
    print("=== Configuration Test ===")
    
    settings = get_settings()
    
    # Check security settings
    security_checks = [
        ("Security headers enabled", settings.security_headers_enabled),
        ("Rate limiting enabled", settings.rate_limit_enabled),
        ("Cookie HttpOnly", settings.cookie_httponly),
        ("HSTS max age set", settings.hsts_max_age > 0),
        ("CSP policy configured", bool(settings.csp_policy)),
    ]
    
    for check_name, check_result in security_checks:
        if check_result:
            print(f"✓ {check_name}")
        else:
            print(f"✗ {check_name}")
    
    print(f"  JWT Secret Key type: {type(settings.jwt_secret_key)}")
    print(f"  Bcrypt rounds: {settings.bcrypt_rounds}")
    print(f"  Max request size: {settings.max_request_size} bytes")
    
    print()

def test_rate_limiting():
    """Test rate limiting configuration."""
    print("=== Rate Limiting Test ===")
    
    try:
        from security import limiter
        print("✓ Rate limiter imported successfully")
        print(f"  Default limits: {limiter.default_limits}")
        
        # Test rate limit decorator
        client = TestClient(app)
        
        # Make a few requests to a rate-limited endpoint
        responses = []
        for i in range(3):
            response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "wrongpassword"
            })
            responses.append(response.status_code)
        
        print(f"  Login attempt responses: {responses}")
        
    except Exception as e:
        print(f"✗ Rate limiting test failed: {e}")
    
    print()

if __name__ == "__main__":
    print("Testing Security Hardening Implementation")
    print("=" * 50)
    
    test_security_headers()
    test_input_validation()
    test_password_validation()
    test_configuration()
    test_rate_limiting()
    
    print("Security hardening test completed!")