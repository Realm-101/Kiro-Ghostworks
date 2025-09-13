"""
Unit tests for artifact endpoints.
Tests individual artifact functions and endpoints in isolation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'api'))

from routes.artifacts import (
    create_artifact,
    list_artifacts,
    get_artifact,
    update_artifact,
    delete_artifact,
    advanced_search_artifacts
)
from models.artifact import Artifact
from models.user import User
from models.tenant import Tenant
from schemas.artifact import CreateArtifactRequest, UpdateArtifactRequest, ArtifactSearchQuery
from auth import AuthenticatedUser


class TestArtifactCreation:
    """Unit tests for artifact creation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_artifact_success(self):
        """Test successful artifact creation."""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        # Mock authenticated user
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        # Mock artifact creation
        mock_artifact = Artifact(
            id=str(uuid4()),
            tenant_id="test-tenant-id",
            name="Test Artifact",
            description="A test artifact",
            tags=["test", "example"],
            artifact_metadata={"version": "1.0"},
            created_by="test-user-id",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        with patch('routes.artifacts.Artifact') as mock_artifact_class:
            mock_artifact_class.return_value = mock_artifact
            
            request_data = CreateArtifactRequest(
                name="Test Artifact",
                description="A test artifact",
                tags=["test", "example"],
                artifact_metadata={"version": "1.0"}
            )
            
            result = await create_artifact(
                workspace_id="test-tenant-id",
                artifact_data=request_data,
                current_user=mock_user,
                session=mock_session
            )
            
            assert result["name"] == request_data.name
            assert result["description"] == request_data.description
            assert result["tags"] == request_data.tags
            assert result["artifact_metadata"] == request_data.artifact_metadata
            assert result["tenant_id"] == "test-tenant-id"
            assert result["created_by"] == "test-user-id"
    
    @pytest.mark.asyncio
    async def test_create_artifact_unauthorized_workspace(self):
        """Test artifact creation with unauthorized workspace access."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock user without access to the workspace
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="different-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        request_data = CreateArtifactRequest(
            name="Test Artifact",
            description="A test artifact",
            tags=["test"],
            artifact_metadata={}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await create_artifact(
                workspace_id="test-tenant-id",
                artifact_data=request_data,
                current_user=mock_user,
                session=mock_session
            )
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_create_artifact_validation_error(self):
        """Test artifact creation with validation errors."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        # Test with empty name
        with pytest.raises(ValueError):
            request_data = CreateArtifactRequest(
                name="",  # Empty name should fail validation
                description="A test artifact",
                tags=["test"],
                artifact_metadata={}
            )
    
    @pytest.mark.asyncio
    async def test_create_artifact_database_error(self):
        """Test artifact creation with database error."""
        # Mock database session that raises an exception
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit.side_effect = Exception("Database error")
        
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        request_data = CreateArtifactRequest(
            name="Test Artifact",
            description="A test artifact",
            tags=["test"],
            artifact_metadata={}
        )
        
        with patch('routes.artifacts.Artifact'):
            with pytest.raises(Exception):
                await create_artifact(
                    workspace_id="test-tenant-id",
                    artifact_data=request_data,
                    current_user=mock_user,
                    session=mock_session
                )


class TestArtifactRetrieval:
    """Unit tests for artifact retrieval functionality."""
    
    @pytest.mark.asyncio
    async def test_get_artifacts_success(self):
        """Test successful artifacts listing."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock artifacts from database
        mock_artifacts = [
            Artifact(
                id=str(uuid4()),
                tenant_id="test-tenant-id",
                name=f"Test Artifact {i}",
                description=f"Description {i}",
                tags=[f"tag{i}"],
                artifact_metadata={"version": f"{i}.0"},
                created_by="test-user-id",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            for i in range(3)
        ]
        
        # Mock query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_artifacts
        mock_session.execute.return_value = mock_result
        
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 3
        mock_session.execute.return_value = mock_count_result
        
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        result = await list_artifacts(
            workspace_id="test-tenant-id",
            limit=20,
            offset=0,
            current_user=mock_user,
            session=mock_session
        )
        
        assert "items" in result
        assert "total" in result
        assert "limit" in result
        assert "offset" in result
        assert "has_more" in result
        assert result["limit"] == 20
        assert result["offset"] == 0
    
    @pytest.mark.asyncio
    async def test_get_artifact_success(self):
        """Test successful single artifact retrieval."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        artifact_id = str(uuid4())
        mock_artifact = Artifact(
            id=artifact_id,
            tenant_id="test-tenant-id",
            name="Test Artifact",
            description="A test artifact",
            tags=["test"],
            artifact_metadata={"version": "1.0"},
            created_by="test-user-id",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_artifact
        mock_session.execute.return_value = mock_result
        
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        result = await get_artifact(
            workspace_id="test-tenant-id",
            artifact_id=artifact_id,
            current_user=mock_user,
            session=mock_session
        )
        
        assert result["id"] == artifact_id
        assert result["name"] == "Test Artifact"
        assert result["tenant_id"] == "test-tenant-id"
    
    @pytest.mark.asyncio
    async def test_get_artifact_not_found(self):
        """Test artifact retrieval when artifact doesn't exist."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock no artifact found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_artifact(
                workspace_id="test-tenant-id",
                artifact_id=str(uuid4()),
                current_user=mock_user,
                session=mock_session
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_get_artifacts_unauthorized_workspace(self):
        """Test artifacts listing with unauthorized workspace access."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock user without access to the workspace
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="different-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await list_artifacts(
                workspace_id="test-tenant-id",
                limit=20,
                offset=0,
                current_user=mock_user,
                session=mock_session
            )
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestArtifactUpdate:
    """Unit tests for artifact update functionality."""
    
    @pytest.mark.asyncio
    async def test_update_artifact_success(self):
        """Test successful artifact update."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        artifact_id = str(uuid4())
        mock_artifact = Artifact(
            id=artifact_id,
            tenant_id="test-tenant-id",
            name="Original Name",
            description="Original description",
            tags=["original"],
            artifact_metadata={"version": "1.0"},
            created_by="test-user-id",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock finding the artifact
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_artifact
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        update_data = UpdateArtifactRequest(
            name="Updated Name",
            description="Updated description",
            tags=["updated"],
            artifact_metadata={"version": "2.0"}
        )
        
        result = await update_artifact(
            workspace_id="test-tenant-id",
            artifact_id=artifact_id,
            artifact_data=update_data,
            current_user=mock_user,
            session=mock_session
        )
        
        assert result["name"] == "Updated Name"
        assert result["description"] == "Updated description"
        assert result["tags"] == ["updated"]
        assert result["artifact_metadata"] == {"version": "2.0"}
    
    @pytest.mark.asyncio
    async def test_update_artifact_not_found(self):
        """Test artifact update when artifact doesn't exist."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock no artifact found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        update_data = UpdateArtifactRequest(
            name="Updated Name",
            description="Updated description",
            tags=["updated"],
            artifact_metadata={"version": "2.0"}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await update_artifact(
                workspace_id="test-tenant-id",
                artifact_id=str(uuid4()),
                artifact_data=update_data,
                current_user=mock_user,
                session=mock_session
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_update_artifact_partial_update(self):
        """Test partial artifact update."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        artifact_id = str(uuid4())
        mock_artifact = Artifact(
            id=artifact_id,
            tenant_id="test-tenant-id",
            name="Original Name",
            description="Original description",
            tags=["original"],
            artifact_metadata={"version": "1.0"},
            created_by="test-user-id",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_artifact
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        # Only update name and tags
        update_data = UpdateArtifactRequest(
            name="Updated Name",
            tags=["updated"]
        )
        
        result = await update_artifact(
            workspace_id="test-tenant-id",
            artifact_id=artifact_id,
            artifact_data=update_data,
            current_user=mock_user,
            session=mock_session
        )
        
        assert result["name"] == "Updated Name"
        assert result["tags"] == ["updated"]
        # Description should remain unchanged
        assert result["description"] == "Original description"


class TestArtifactDeletion:
    """Unit tests for artifact deletion functionality."""
    
    @pytest.mark.asyncio
    async def test_delete_artifact_success(self):
        """Test successful artifact deletion."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        artifact_id = str(uuid4())
        mock_artifact = Artifact(
            id=artifact_id,
            tenant_id="test-tenant-id",
            name="Test Artifact",
            description="A test artifact",
            tags=["test"],
            artifact_metadata={"version": "1.0"},
            created_by="test-user-id",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_artifact
        mock_session.execute.return_value = mock_result
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()
        
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        # Should not raise an exception
        await delete_artifact(
            workspace_id="test-tenant-id",
            artifact_id=artifact_id,
            current_user=mock_user,
            session=mock_session
        )
        
        # Verify delete was called
        mock_session.delete.assert_called_once_with(mock_artifact)
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_artifact_not_found(self):
        """Test artifact deletion when artifact doesn't exist."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock no artifact found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_artifact(
                workspace_id="test-tenant-id",
                artifact_id=str(uuid4()),
                current_user=mock_user,
                session=mock_session
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestArtifactSearch:
    """Unit tests for artifact search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_artifacts_by_query(self):
        """Test artifact search by text query."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock search results
        mock_artifacts = [
            Artifact(
                id=str(uuid4()),
                tenant_id="test-tenant-id",
                name="API Service",
                description="A REST API service",
                tags=["api", "service"],
                artifact_metadata={"version": "1.0"},
                created_by="test-user-id",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_artifacts
        mock_session.execute.return_value = mock_result
        
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_count_result
        
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        search_query = ArtifactSearchQuery(
            q="API",
            limit=20,
            offset=0
        )
        
        result = await search_artifacts(
            workspace_id="test-tenant-id",
            search_query=search_query,
            current_user=mock_user,
            session=mock_session
        )
        
        assert "items" in result
        assert "total" in result
        assert len(result["items"]) == 1
        assert "API" in result["items"][0]["name"]
    
    @pytest.mark.asyncio
    async def test_search_artifacts_by_tags(self):
        """Test artifact search by tags."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        mock_artifacts = [
            Artifact(
                id=str(uuid4()),
                tenant_id="test-tenant-id",
                name="Database Tool",
                description="A database management tool",
                tags=["database", "tool"],
                artifact_metadata={"version": "1.0"},
                created_by="test-user-id",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_artifacts
        mock_session.execute.return_value = mock_result
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_count_result
        
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        search_query = ArtifactSearchQuery(
            tags=["database"],
            limit=20,
            offset=0
        )
        
        result = await search_artifacts(
            workspace_id="test-tenant-id",
            search_query=search_query,
            current_user=mock_user,
            session=mock_session
        )
        
        assert "items" in result
        assert len(result["items"]) == 1
        assert "database" in result["items"][0]["tags"]
    
    @pytest.mark.asyncio
    async def test_search_artifacts_empty_results(self):
        """Test artifact search with no results."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock empty results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_count_result
        
        mock_user = AuthenticatedUser(
            id="test-user-id",
            email="test@example.com",
            tenant_id="test-tenant-id",
            role="member",
            is_verified=True,
            is_active=True
        )
        
        search_query = ArtifactSearchQuery(
            q="nonexistent",
            limit=20,
            offset=0
        )
        
        result = await search_artifacts(
            workspace_id="test-tenant-id",
            search_query=search_query,
            current_user=mock_user,
            session=mock_session
        )
        
        assert "items" in result
        assert "total" in result
        assert len(result["items"]) == 0
        assert result["total"] == 0
        assert result["has_more"] is False


class TestArtifactValidation:
    """Unit tests for artifact data validation."""
    
    def test_artifact_create_request_validation(self):
        """Test CreateArtifactRequest validation."""
        # Valid request
        valid_request = CreateArtifactRequest(
            name="Test Artifact",
            description="A test artifact",
            tags=["test", "example"],
            artifact_metadata={"version": "1.0"}
        )
        
        assert valid_request.name == "Test Artifact"
        assert valid_request.description == "A test artifact"
        assert valid_request.tags == ["test", "example"]
        assert valid_request.artifact_metadata == {"version": "1.0"}
    
    def test_artifact_create_request_minimal(self):
        """Test CreateArtifactRequest with minimal data."""
        minimal_request = CreateArtifactRequest(
            name="Minimal Artifact"
        )
        
        assert minimal_request.name == "Minimal Artifact"
        assert minimal_request.description is None
        assert minimal_request.tags == []
        assert minimal_request.artifact_metadata == {}
    
    def test_artifact_update_request_validation(self):
        """Test UpdateArtifactRequest validation."""
        update_request = UpdateArtifactRequest(
            name="Updated Artifact",
            description="Updated description",
            tags=["updated"],
            artifact_metadata={"version": "2.0"}
        )
        
        assert update_request.name == "Updated Artifact"
        assert update_request.description == "Updated description"
        assert update_request.tags == ["updated"]
        assert update_request.artifact_metadata == {"version": "2.0"}
    
    def test_artifact_search_query_validation(self):
        """Test ArtifactSearchQuery validation."""
        search_query = ArtifactSearchQuery(
            q="search term",
            tags=["tag1", "tag2"],
            limit=10,
            offset=20
        )
        
        assert search_query.q == "search term"
        assert search_query.tags == ["tag1", "tag2"]
        assert search_query.limit == 10
        assert search_query.offset == 20
    
    def test_artifact_search_query_defaults(self):
        """Test ArtifactSearchQuery default values."""
        search_query = ArtifactSearchQuery()
        
        assert search_query.q is None
        assert search_query.tags == []
        assert search_query.limit == 20
        assert search_query.offset == 0