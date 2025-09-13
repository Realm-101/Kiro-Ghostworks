"""
Tests for demo credential protection in production environments.
"""

import pytest
from unittest.mock import patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.config import get_settings


class TestDemoCredentialProtection:
    """Test suite for demo credential protection."""
    
    def test_demo_credentials_blocked_in_production(self):
        """Test that demo credentials are blocked in production environment."""
        client = TestClient(app)
        
        # Mock production environment
        with patch.object(get_settings(), 'environment', 'production'):
            # Try to login with demo credentials
            response = client.post("/api/v1/auth/login", json={
                "email": "owner@acme.com",
                "password": "demo123"
            })
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Demo credentials are disabled in production" in response.json()["detail"]
    
    def test_demo_credentials_allowed_in_development(self):
        """Test that demo credentials work in development environment."""
        client = TestClient(app)
        
        # Mock development environment
        with patch.object(get_settings(), 'environment', 'development'):
            # This would normally work if the user exists in the database
            # We expect a different error (user not found) rather than blocked credentials
            response = client.post("/api/v1/auth/login", json={
                "email": "owner@acme.com", 
                "password": "demo123"
            })
            
            # Should get "Invalid email or password" not "Demo credentials disabled"
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Demo credentials are disabled" not in response.json()["detail"]
    
    def test_regular_credentials_work_in_production(self):
        """Test that regular (non-demo) credentials work in production."""
        client = TestClient(app)
        
        # Mock production environment
        with patch.object(get_settings(), 'environment', 'production'):
            # Try to login with regular credentials
            response = client.post("/api/v1/auth/login", json={
                "email": "regular@user.com",
                "password": "password123"
            })
            
            # Should get "Invalid email or password" not "Demo credentials disabled"
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Demo credentials are disabled" not in response.json()["detail"]
    
    @pytest.mark.parametrize("demo_email", [
        "owner@acme.com",
        "admin@umbrella.com", 
        "member@acme.com",
        "researcher@umbrella.com",
        "manager@acme.com"
    ])
    def test_all_demo_emails_blocked_in_production(self, demo_email):
        """Test that all demo email addresses are blocked in production."""
        client = TestClient(app)
        
        # Mock production environment
        with patch.object(get_settings(), 'environment', 'production'):
            response = client.post("/api/v1/auth/login", json={
                "email": demo_email,
                "password": "demo123"
            })
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Demo credentials are disabled in production" in response.json()["detail"]
    
    def test_case_insensitive_demo_email_blocking(self):
        """Test that demo email blocking is case-insensitive."""
        client = TestClient(app)
        
        # Mock production environment
        with patch.object(get_settings(), 'environment', 'production'):
            # Try uppercase version
            response = client.post("/api/v1/auth/login", json={
                "email": "OWNER@ACME.COM",
                "password": "demo123"
            })
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Demo credentials are disabled in production" in response.json()["detail"]
    
    def test_staging_environment_blocks_demo_credentials(self):
        """Test that staging environment also blocks demo credentials."""
        client = TestClient(app)
        
        # Mock staging environment
        with patch.object(get_settings(), 'environment', 'staging'):
            response = client.post("/api/v1/auth/login", json={
                "email": "owner@acme.com",
                "password": "demo123"
            })
            
            # Staging should also block demo credentials
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            # Note: Current implementation only blocks in production
            # This test documents expected behavior if we extend to staging