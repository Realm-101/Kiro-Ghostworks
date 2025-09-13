"""
Test utilities and helper functions for the test suite.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import API modules
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "services" / "api"))

from auth import create_access_token, create_refresh_token, hash_password
from models.user import User
from models.tenant import Tenant
from models.workspace_membership import WorkspaceMembership, WorkspaceRole
from models.artifact import Artifact


class TestDataFactory:
    """Factory for creating test data objects."""
    
    @staticmethod
    def create_user_data(
        email: Optional[str] = None,
        password: str = "TestPassword123!",
        first_name: str = "Test",
        last_name: str = "User",
        is_verified: bool = True,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """Create user data for testing."""
        return {
            "email": email or f"test-{uuid.uuid4().hex[:8]}@example.com",
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "is_verified": is_verified,
            "is_active": is_active
        }
    
    @staticmethod
    def create_tenant_data(
        name: Optional[str] = None,
        slug: Optional[str] = None,
        description: str = "A test tenant",
        settings: Optional[Dict[str, Any]] = None,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """Create tenant data for testing."""
        unique_id = uuid.uuid4().hex[:8]
        return {
            "name": name or f"Test Company {unique_id}",
            "slug": slug or f"test-company-{unique_id}",
            "description": description,
            "settings": settings or {"theme": "dark"},
            "is_active": is_active
        }
    
    @staticmethod
    def create_artifact_data(
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create artifact data for testing."""
        unique_id = uuid.uuid4().hex[:8]
        return {
            "name": name or f"Test Artifact {unique_id}",
            "description": description or f"A test artifact for testing purposes {unique_id}",
            "tags": tags or ["test", "api", "example"],
            "artifact_metadata": metadata or {"version": "1.0.0", "technology": "FastAPI"}
        }


class DatabaseTestHelper:
    """Helper class for database operations in tests."""
    
    @staticmethod
    async def create_user(
        session: AsyncSession,
        user_data: Optional[Dict[str, Any]] = None
    ) -> User:
        """Create a user in the test database."""
        data = user_data or TestDataFactory.create_user_data()
        
        user = User(
            email=data["email"],
            hashed_password=hash_password(data["password"]),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            is_verified=data.get("is_verified", True),
            is_active=data.get("is_active", True)
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        return user
    
    @staticmethod
    async def create_tenant(
        session: AsyncSession,
        tenant_data: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        """Create a tenant in the test database."""
        data = tenant_data or TestDataFactory.create_tenant_data()
        
        tenant = Tenant(
            name=data["name"],
            slug=data["slug"],
            description=data.get("description"),
            settings=data.get("settings", {}),
            is_active=data.get("is_active", True)
        )
        
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
        
        return tenant
    
    @staticmethod
    async def create_membership(
        session: AsyncSession,
        user: User,
        tenant: Tenant,
        role: WorkspaceRole = WorkspaceRole.MEMBER,
        is_active: bool = True
    ) -> WorkspaceMembership:
        """Create a workspace membership in the test database."""
        membership = WorkspaceMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role=role,
            is_active=is_active
        )
        
        session.add(membership)
        await session.commit()
        await session.refresh(membership)
        
        return membership
    
    @staticmethod
    async def create_artifact(
        session: AsyncSession,
        tenant: Tenant,
        user: User,
        artifact_data: Optional[Dict[str, Any]] = None
    ) -> Artifact:
        """Create an artifact in the test database."""
        data = artifact_data or TestDataFactory.create_artifact_data()
        
        artifact = Artifact(
            tenant_id=tenant.id,
            name=data["name"],
            description=data.get("description"),
            tags=data.get("tags", []),
            artifact_metadata=data.get("artifact_metadata", {}),
            created_by=user.id,
            is_active=True
        )
        
        session.add(artifact)
        await session.commit()
        await session.refresh(artifact)
        
        return artifact
    
    @staticmethod
    async def create_multiple_artifacts(
        session: AsyncSession,
        tenant: Tenant,
        user: User,
        count: int = 3
    ) -> List[Artifact]:
        """Create multiple artifacts for testing."""
        artifacts = []
        
        artifact_templates = [
            {
                "name": "API Service",
                "description": "A REST API service for data management",
                "tags": ["api", "service", "rest"],
                "artifact_metadata": {"version": "1.0.0", "technology": "FastAPI"}
            },
            {
                "name": "Database Migration Tool",
                "description": "Tool for managing database schema migrations",
                "tags": ["database", "migration", "tool"],
                "artifact_metadata": {"version": "2.1.0", "technology": "Alembic"}
            },
            {
                "name": "Authentication Library",
                "description": "Library for handling user authentication and authorization",
                "tags": ["auth", "library", "security"],
                "artifact_metadata": {"version": "1.5.0", "technology": "Python"}
            },
            {
                "name": "Frontend Component",
                "description": "Reusable React component for user interfaces",
                "tags": ["frontend", "react", "component"],
                "artifact_metadata": {"version": "3.2.1", "technology": "React"}
            },
            {
                "name": "Data Processing Pipeline",
                "description": "Pipeline for processing and transforming data",
                "tags": ["data", "pipeline", "etl"],
                "artifact_metadata": {"version": "1.8.0", "technology": "Python"}
            }
        ]
        
        for i in range(min(count, len(artifact_templates))):
            template = artifact_templates[i]
            artifact = await DatabaseTestHelper.create_artifact(
                session, tenant, user, template
            )
            artifacts.append(artifact)
        
        # If we need more artifacts than templates, create generic ones
        for i in range(len(artifact_templates), count):
            artifact = await DatabaseTestHelper.create_artifact(
                session, tenant, user, 
                TestDataFactory.create_artifact_data(name=f"Generic Artifact {i+1}")
            )
            artifacts.append(artifact)
        
        return artifacts


class AuthTestHelper:
    """Helper class for authentication-related test operations."""
    
    @staticmethod
    def create_auth_headers(
        user: User,
        tenant: Optional[Tenant] = None,
        role: Optional[str] = None
    ) -> Dict[str, str]:
        """Create authentication headers for API requests."""
        token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            tenant_id=str(tenant.id) if tenant else None,
            role=role
        )
        
        return {"Authorization": f"Bearer {token}"}
    
    @staticmethod
    def create_refresh_token_headers(user: User) -> Dict[str, str]:
        """Create refresh token headers for API requests."""
        token = create_refresh_token(
            user_id=str(user.id),
            email=user.email
        )
        
        return {"Authorization": f"Bearer {token}"}
    
    @staticmethod
    def create_workspace_auth_headers(
        user: User,
        tenant: Tenant,
        membership: WorkspaceMembership
    ) -> Dict[str, str]:
        """Create authentication headers with workspace context."""
        return AuthTestHelper.create_auth_headers(
            user=user,
            tenant=tenant,
            role=membership.role.value
        )


class APITestHelper:
    """Helper class for API testing operations."""
    
    @staticmethod
    async def register_user(
        client: AsyncClient,
        user_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Register a user via API and return response data."""
        data = user_data or TestDataFactory.create_user_data()
        
        response = await client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 201
        
        return response.json()
    
    @staticmethod
    async def login_user(
        client: AsyncClient,
        email: str,
        password: str = "TestPassword123!"
    ) -> Dict[str, Any]:
        """Login a user via API and return response data."""
        login_data = {"email": email, "password": password}
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        return response.json()
    
    @staticmethod
    async def create_workspace(
        client: AsyncClient,
        auth_headers: Dict[str, str],
        workspace_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a workspace via API and return response data."""
        data = workspace_data or TestDataFactory.create_tenant_data()
        
        response = await client.post(
            "/api/v1/workspaces",
            json=data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        return response.json()
    
    @staticmethod
    async def create_artifact(
        client: AsyncClient,
        workspace_id: str,
        auth_headers: Dict[str, str],
        artifact_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create an artifact via API and return response data."""
        data = artifact_data or TestDataFactory.create_artifact_data()
        
        response = await client.post(
            f"/api/v1/workspaces/{workspace_id}/artifacts",
            json=data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        return response.json()


class MockHelper:
    """Helper class for creating mocks in tests."""
    
    @staticmethod
    def create_mock_request(request_id: Optional[str] = None):
        """Create a mock FastAPI request object."""
        from unittest.mock import MagicMock
        
        mock_request = MagicMock()
        mock_request.state.request_id = request_id or str(uuid.uuid4())
        
        return mock_request
    
    @staticmethod
    def create_mock_authenticated_user(
        user: User,
        tenant: Optional[Tenant] = None,
        role: Optional[str] = None
    ):
        """Create a mock authenticated user for dependency injection."""
        from auth import AuthenticatedUser
        
        return AuthenticatedUser(
            id=str(user.id),
            email=user.email,
            tenant_id=str(tenant.id) if tenant else None,
            role=role,
            is_verified=user.is_verified,
            is_active=user.is_active
        )


class AssertionHelper:
    """Helper class for common test assertions."""
    
    @staticmethod
    def assert_user_response(response_data: Dict[str, Any], expected_user: User):
        """Assert that user response data matches expected user."""
        assert response_data["id"] == str(expected_user.id)
        assert response_data["email"] == expected_user.email
        assert response_data["first_name"] == expected_user.first_name
        assert response_data["last_name"] == expected_user.last_name
        assert response_data["is_verified"] == expected_user.is_verified
        assert response_data["is_active"] == expected_user.is_active
        assert "created_at" in response_data
        assert "updated_at" in response_data
    
    @staticmethod
    def assert_tenant_response(response_data: Dict[str, Any], expected_tenant: Tenant):
        """Assert that tenant response data matches expected tenant."""
        assert response_data["id"] == str(expected_tenant.id)
        assert response_data["name"] == expected_tenant.name
        assert response_data["slug"] == expected_tenant.slug
        assert response_data["description"] == expected_tenant.description
        assert response_data["settings"] == expected_tenant.settings
        assert response_data["is_active"] == expected_tenant.is_active
        assert "created_at" in response_data
        assert "updated_at" in response_data
    
    @staticmethod
    def assert_artifact_response(response_data: Dict[str, Any], expected_artifact: Artifact):
        """Assert that artifact response data matches expected artifact."""
        assert response_data["id"] == str(expected_artifact.id)
        assert response_data["tenant_id"] == str(expected_artifact.tenant_id)
        assert response_data["name"] == expected_artifact.name
        assert response_data["description"] == expected_artifact.description
        assert set(response_data["tags"]) == set(expected_artifact.tags)
        assert response_data["artifact_metadata"] == expected_artifact.artifact_metadata
        assert response_data["created_by"] == str(expected_artifact.created_by)
        assert response_data["is_active"] == expected_artifact.is_active
        assert "created_at" in response_data
        assert "updated_at" in response_data
    
    @staticmethod
    def assert_paginated_response(
        response_data: Dict[str, Any],
        expected_total: int,
        expected_limit: int = 20,
        expected_offset: int = 0
    ):
        """Assert that paginated response has correct structure."""
        assert "items" in response_data
        assert "total" in response_data
        assert "limit" in response_data
        assert "offset" in response_data
        assert "has_more" in response_data
        
        assert response_data["total"] == expected_total
        assert response_data["limit"] == expected_limit
        assert response_data["offset"] == expected_offset
        assert isinstance(response_data["items"], list)
        
        expected_has_more = (expected_offset + expected_limit) < expected_total
        assert response_data["has_more"] == expected_has_more
    
    @staticmethod
    def assert_error_response(
        response_data: Dict[str, Any],
        expected_error: str,
        expected_message: Optional[str] = None
    ):
        """Assert that error response has correct structure."""
        assert "error" in response_data
        assert "message" in response_data
        assert "timestamp" in response_data
        
        assert response_data["error"] == expected_error
        
        if expected_message:
            assert expected_message in response_data["message"]


# Export all helper classes for easy importing
__all__ = [
    "TestDataFactory",
    "DatabaseTestHelper", 
    "AuthTestHelper",
    "APITestHelper",
    "MockHelper",
    "AssertionHelper"
]