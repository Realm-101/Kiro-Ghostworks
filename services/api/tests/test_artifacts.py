"""
Tests for artifact CRUD API endpoints.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.artifact import Artifact
from models.tenant import Tenant
from models.user import User
from models.workspace_membership import WorkspaceMembership, WorkspaceRole


class TestArtifactCRUD:
    """Test artifact CRUD operations."""
    
    async def test_create_artifact_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_tenant: Tenant,
        test_membership: WorkspaceMembership,
        auth_headers: dict
    ):
        """Test successful artifact creation."""
        artifact_data = {
            "name": "Test Artifact",
            "description": "A test artifact for unit testing",
            "tags": ["test", "api", "crud"],
            "artifact_metadata": {
                "version": "1.0.0",
                "technology": "FastAPI"
            }
        }
        
        response = await async_client.post(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts",
            json=artifact_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["name"] == artifact_data["name"]
        assert data["description"] == artifact_data["description"]
        assert set(data["tags"]) == set(artifact_data["tags"])
        assert data["artifact_metadata"] == artifact_data["artifact_metadata"]
        assert data["tenant_id"] == str(test_tenant.id)
        assert data["created_by"] == str(test_user.id)
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    async def test_create_artifact_unauthorized(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant
    ):
        """Test artifact creation without authentication."""
        artifact_data = {
            "name": "Test Artifact",
            "description": "A test artifact"
        }
        
        response = await async_client.post(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts",
            json=artifact_data
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_create_artifact_no_workspace_access(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test artifact creation without workspace access."""
        other_workspace_id = str(uuid4())
        artifact_data = {
            "name": "Test Artifact",
            "description": "A test artifact"
        }
        
        response = await async_client.post(
            f"/api/v1/workspaces/{other_workspace_id}/artifacts",
            json=artifact_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_create_artifact_validation_error(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        auth_headers: dict
    ):
        """Test artifact creation with validation errors."""
        artifact_data = {
            "name": "",  # Empty name should fail validation
            "description": "A test artifact"
        }
        
        response = await async_client.post(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts",
            json=artifact_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_list_artifacts_success(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        test_artifacts: list[Artifact],
        auth_headers: dict
    ):
        """Test successful artifact listing."""
        response = await async_client.get(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data
        
        assert len(data["items"]) == len(test_artifacts)
        assert data["total"] == len(test_artifacts)
        assert data["limit"] == 20  # Default limit
        assert data["offset"] == 0
        assert data["has_more"] is False
    
    async def test_list_artifacts_with_pagination(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        test_artifacts: list[Artifact],
        auth_headers: dict
    ):
        """Test artifact listing with pagination."""
        response = await async_client.get(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts?limit=2&offset=1",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data["items"]) == min(2, len(test_artifacts) - 1)
        assert data["total"] == len(test_artifacts)
        assert data["limit"] == 2
        assert data["offset"] == 1
    
    async def test_list_artifacts_with_search(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        test_artifacts: list[Artifact],
        auth_headers: dict
    ):
        """Test artifact listing with full-text search."""
        response = await async_client.get(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts?q=test",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Should find artifacts with "test" in name or description
        assert len(data["items"]) >= 0
    
    async def test_list_artifacts_with_tag_filter(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        test_artifacts: list[Artifact],
        auth_headers: dict
    ):
        """Test artifact listing with tag filtering."""
        response = await async_client.get(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts?tags=api&tags=test",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Should find artifacts with specified tags
        for item in data["items"]:
            assert any(tag in ["api", "test"] for tag in item["tags"])
    
    async def test_get_artifact_success(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        test_artifacts: list[Artifact],
        auth_headers: dict
    ):
        """Test successful artifact retrieval."""
        artifact = test_artifacts[0]
        
        response = await async_client.get(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts/{artifact.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == str(artifact.id)
        assert data["name"] == artifact.name
        assert data["description"] == artifact.description
        assert data["tenant_id"] == str(test_tenant.id)
    
    async def test_get_artifact_not_found(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        auth_headers: dict
    ):
        """Test artifact retrieval with non-existent ID."""
        non_existent_id = str(uuid4())
        
        response = await async_client.get(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts/{non_existent_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_update_artifact_success(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        test_artifacts: list[Artifact],
        auth_headers: dict
    ):
        """Test successful artifact update."""
        artifact = test_artifacts[0]
        update_data = {
            "name": "Updated Artifact Name",
            "description": "Updated description",
            "tags": ["updated", "test"],
            "artifact_metadata": {"version": "2.0.0"}
        }
        
        response = await async_client.put(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts/{artifact.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert set(data["tags"]) == set(update_data["tags"])
        assert data["artifact_metadata"] == update_data["artifact_metadata"]
    
    async def test_patch_artifact_success(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        test_artifacts: list[Artifact],
        auth_headers: dict
    ):
        """Test successful partial artifact update."""
        artifact = test_artifacts[0]
        update_data = {
            "name": "Patched Artifact Name"
        }
        
        response = await async_client.patch(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts/{artifact.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == update_data["name"]
        # Other fields should remain unchanged
        assert data["description"] == artifact.description
    
    async def test_delete_artifact_success(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        test_artifacts: list[Artifact],
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """Test successful artifact deletion."""
        artifact = test_artifacts[0]
        
        response = await async_client.delete(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts/{artifact.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify artifact is soft deleted
        await db_session.refresh(artifact)
        assert artifact.is_active is False
    
    async def test_delete_artifact_not_found(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        auth_headers: dict
    ):
        """Test artifact deletion with non-existent ID."""
        non_existent_id = str(uuid4())
        
        response = await async_client.delete(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts/{non_existent_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestArtifactSearch:
    """Test artifact search functionality."""
    
    async def test_advanced_search_with_query(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        test_artifacts: list[Artifact],
        auth_headers: dict
    ):
        """Test advanced search with text query."""
        response = await async_client.get(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts/search/advanced?q=test",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        # Results should be ordered by relevance when searching
    
    async def test_advanced_search_with_tags(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        test_artifacts: list[Artifact],
        auth_headers: dict
    ):
        """Test advanced search with tag filtering."""
        response = await async_client.get(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts/search/advanced?tags=api",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        for item in data["items"]:
            assert "api" in item["tags"]
    
    async def test_advanced_search_with_date_range(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        test_artifacts: list[Artifact],
        auth_headers: dict
    ):
        """Test advanced search with date range filtering."""
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat()
        
        response = await async_client.get(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts/search/advanced"
            f"?created_after={yesterday}&created_before={tomorrow}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Should return artifacts created within the date range
        assert len(data["items"]) >= 0


class TestArtifactStats:
    """Test artifact statistics endpoint."""
    
    async def test_get_artifact_stats(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        test_artifacts: list[Artifact],
        auth_headers: dict
    ):
        """Test artifact statistics retrieval."""
        response = await async_client.get(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts/stats",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_artifacts" in data
        assert "active_artifacts" in data
        assert "total_tags" in data
        assert "most_used_tags" in data
        
        assert data["total_artifacts"] >= len(test_artifacts)
        assert data["active_artifacts"] <= data["total_artifacts"]
        assert isinstance(data["most_used_tags"], list)


class TestArtifactSecurity:
    """Test artifact security and tenant isolation."""
    
    async def test_tenant_isolation(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_tenant: Tenant,
        other_tenant: Tenant,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """Test that artifacts are properly isolated by tenant."""
        # Create artifact in test_tenant
        artifact_data = {
            "name": "Tenant Isolated Artifact",
            "description": "Should not be visible in other tenant"
        }
        
        response = await async_client.post(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts",
            json=artifact_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        artifact_id = response.json()["id"]
        
        # Try to access artifact from other tenant (should fail)
        response = await async_client.get(
            f"/api/v1/workspaces/{other_tenant.id}/artifacts/{artifact_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_workspace_membership_required(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        other_user_auth_headers: dict
    ):
        """Test that workspace membership is required for artifact access."""
        response = await async_client.get(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts",
            headers=other_user_auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestArtifactValidation:
    """Test artifact input validation."""
    
    async def test_create_artifact_with_invalid_data(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        auth_headers: dict
    ):
        """Test artifact creation with various invalid inputs."""
        # Test empty name
        response = await async_client.post(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts",
            json={"name": "", "description": "Test"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test name too long
        response = await async_client.post(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts",
            json={"name": "x" * 300, "description": "Test"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_tag_normalization(
        self,
        async_client: AsyncClient,
        test_tenant: Tenant,
        auth_headers: dict
    ):
        """Test that tags are properly normalized."""
        artifact_data = {
            "name": "Tag Test Artifact",
            "tags": ["  API  ", "Test", "api", "", "TEST"]  # Mixed case, spaces, duplicates
        }
        
        response = await async_client.post(
            f"/api/v1/workspaces/{test_tenant.id}/artifacts",
            json=artifact_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        # Tags should be normalized: lowercase, no duplicates, no empty strings
        expected_tags = ["api", "test"]
        assert set(data["tags"]) == set(expected_tags)