"""
Integration tests for artifact CRUD flows.
Tests the complete artifact management workflow including creation, retrieval, updates, and deletion.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
from uuid import uuid4

from tests.utils.test_helpers import (
    TestDataFactory,
    DatabaseTestHelper,
    APITestHelper,
    AuthTestHelper,
    AssertionHelper
)


class TestArtifactCRUDIntegration:
    """Integration tests for artifact CRUD workflows."""
    
    async def test_complete_artifact_creation_flow(self, async_client: AsyncClient):
        """Test complete artifact creation workflow."""
        # Register user and create workspace
        user_data = TestDataFactory.create_user_data(email="artifact_create@example.com")
        user_response = await APITestHelper.register_user(async_client, user_data)
        
        login_response = await APITestHelper.login_user(
            async_client, user_data["email"], user_data["password"]
        )
        
        auth_headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        
        # Create workspace
        workspace_data = TestDataFactory.create_tenant_data()
        workspace_response = await APITestHelper.create_workspace(
            async_client, auth_headers, workspace_data
        )
        
        workspace_id = workspace_response["id"]
        
        # Create artifact
        artifact_data = TestDataFactory.create_artifact_data(
            name="Integration Test Artifact",
            description="An artifact created during integration testing",
            tags=["integration", "test", "api"]
        )
        
        artifact_response = await APITestHelper.create_artifact(
            async_client, workspace_id, auth_headers, artifact_data
        )
        
        # Verify artifact creation
        assert artifact_response["name"] == artifact_data["name"]
        assert artifact_response["description"] == artifact_data["description"]
        assert set(artifact_response["tags"]) == set(artifact_data["tags"])
        assert artifact_response["tenant_id"] == workspace_id
        assert "id" in artifact_response
        assert "created_at" in artifact_response
        assert "updated_at" in artifact_response
    
    async def test_complete_artifact_retrieval_flow(self, async_client: AsyncClient):
        """Test complete artifact retrieval workflow."""
        # Setup user, workspace, and artifacts
        user_data = TestDataFactory.create_user_data(email="artifact_retrieve@example.com")
        await APITestHelper.register_user(async_client, user_data)
        
        login_response = await APITestHelper.login_user(
            async_client, user_data["email"], user_data["password"]
        )
        
        auth_headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        
        workspace_data = TestDataFactory.create_tenant_data()
        workspace_response = await APITestHelper.create_workspace(
            async_client, auth_headers, workspace_data
        )
        
        workspace_id = workspace_response["id"]
        
        # Create multiple artifacts
        artifacts = []
        for i in range(3):
            artifact_data = TestDataFactory.create_artifact_data(
                name=f"Test Artifact {i+1}",
                tags=[f"tag{i+1}", "common"]
            )
            artifact_response = await APITestHelper.create_artifact(
                async_client, workspace_id, auth_headers, artifact_data
            )
            artifacts.append(artifact_response)
        
        # Test listing all artifacts
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace_id}/artifacts",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        list_response = response.json()
        AssertionHelper.assert_paginated_response(list_response, expected_total=3)
        assert len(list_response["items"]) == 3
        
        # Test retrieving specific artifact
        artifact_id = artifacts[0]["id"]
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace_id}/artifacts/{artifact_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        artifact_response = response.json()
        assert artifact_response["id"] == artifact_id
        assert artifact_response["name"] == artifacts[0]["name"]
    
    async def test_complete_artifact_update_flow(self, async_client: AsyncClient):
        """Test complete artifact update workflow."""
        # Setup user, workspace, and artifact
        user_data = TestDataFactory.create_user_data(email="artifact_update@example.com")
        await APITestHelper.register_user(async_client, user_data)
        
        login_response = await APITestHelper.login_user(
            async_client, user_data["email"], user_data["password"]
        )
        
        auth_headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        
        workspace_data = TestDataFactory.create_tenant_data()
        workspace_response = await APITestHelper.create_workspace(
            async_client, auth_headers, workspace_data
        )
        
        workspace_id = workspace_response["id"]
        
        # Create artifact
        artifact_data = TestDataFactory.create_artifact_data()
        artifact_response = await APITestHelper.create_artifact(
            async_client, workspace_id, auth_headers, artifact_data
        )
        
        artifact_id = artifact_response["id"]
        
        # Update artifact
        update_data = {
            "name": "Updated Artifact Name",
            "description": "Updated description for the artifact",
            "tags": ["updated", "modified", "test"],
            "artifact_metadata": {"version": "2.0.0", "status": "updated"}
        }
        
        response = await async_client.put(
            f"/api/v1/workspaces/{workspace_id}/artifacts/{artifact_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        updated_artifact = response.json()
        assert updated_artifact["name"] == update_data["name"]
        assert updated_artifact["description"] == update_data["description"]
        assert set(updated_artifact["tags"]) == set(update_data["tags"])
        assert updated_artifact["artifact_metadata"] == update_data["artifact_metadata"]
        assert updated_artifact["updated_at"] != artifact_response["updated_at"]
    
    async def test_complete_artifact_deletion_flow(self, async_client: AsyncClient):
        """Test complete artifact deletion workflow."""
        # Setup user, workspace, and artifact
        user_data = TestDataFactory.create_user_data(email="artifact_delete@example.com")
        await APITestHelper.register_user(async_client, user_data)
        
        login_response = await APITestHelper.login_user(
            async_client, user_data["email"], user_data["password"]
        )
        
        auth_headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        
        workspace_data = TestDataFactory.create_tenant_data()
        workspace_response = await APITestHelper.create_workspace(
            async_client, auth_headers, workspace_data
        )
        
        workspace_id = workspace_response["id"]
        
        # Create artifact
        artifact_data = TestDataFactory.create_artifact_data()
        artifact_response = await APITestHelper.create_artifact(
            async_client, workspace_id, auth_headers, artifact_data
        )
        
        artifact_id = artifact_response["id"]
        
        # Delete artifact
        response = await async_client.delete(
            f"/api/v1/workspaces/{workspace_id}/artifacts/{artifact_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify artifact is deleted
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace_id}/artifacts/{artifact_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_artifact_search_and_filtering_flow(self, async_client: AsyncClient):
        """Test artifact search and filtering workflow."""
        # Setup user, workspace, and multiple artifacts
        user_data = TestDataFactory.create_user_data(email="artifact_search@example.com")
        await APITestHelper.register_user(async_client, user_data)
        
        login_response = await APITestHelper.login_user(
            async_client, user_data["email"], user_data["password"]
        )
        
        auth_headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        
        workspace_data = TestDataFactory.create_tenant_data()
        workspace_response = await APITestHelper.create_workspace(
            async_client, auth_headers, workspace_data
        )
        
        workspace_id = workspace_response["id"]
        
        # Create artifacts with different characteristics
        artifacts_data = [
            {
                "name": "API Service Documentation",
                "description": "Documentation for the REST API service",
                "tags": ["api", "documentation", "service"]
            },
            {
                "name": "Database Migration Scripts",
                "description": "Scripts for database schema migrations",
                "tags": ["database", "migration", "scripts"]
            },
            {
                "name": "API Testing Framework",
                "description": "Framework for testing API endpoints",
                "tags": ["api", "testing", "framework"]
            }
        ]
        
        for artifact_data in artifacts_data:
            await APITestHelper.create_artifact(
                async_client, workspace_id, auth_headers, artifact_data
            )
        
        # Test search by name
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace_id}/artifacts",
            params={"q": "API"},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        search_results = response.json()
        assert len(search_results["items"]) == 2  # Two artifacts contain "API"
        
        # Test filter by tags
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace_id}/artifacts",
            params={"tags": "database"},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        filter_results = response.json()
        assert len(filter_results["items"]) == 1  # One artifact has "database" tag
        assert "database" in filter_results["items"][0]["tags"]
        
        # Test pagination
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace_id}/artifacts",
            params={"limit": 2, "offset": 0},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        paginated_results = response.json()
        AssertionHelper.assert_paginated_response(
            paginated_results, 
            expected_total=3, 
            expected_limit=2, 
            expected_offset=0
        )
        assert len(paginated_results["items"]) == 2
        assert paginated_results["has_more"] is True


class TestArtifactAuthorizationIntegration:
    """Integration tests for artifact authorization workflows."""
    
    async def test_workspace_isolation_flow(self, async_client: AsyncClient):
        """Test that artifacts are properly isolated between workspaces."""
        # Create two users with separate workspaces
        user1_data = TestDataFactory.create_user_data(email="user1_isolation@example.com")
        user2_data = TestDataFactory.create_user_data(email="user2_isolation@example.com")
        
        await APITestHelper.register_user(async_client, user1_data)
        await APITestHelper.register_user(async_client, user2_data)
        
        # Login both users
        login1_response = await APITestHelper.login_user(
            async_client, user1_data["email"], user1_data["password"]
        )
        login2_response = await APITestHelper.login_user(
            async_client, user2_data["email"], user2_data["password"]
        )
        
        auth1_headers = {"Authorization": f"Bearer {login1_response['access_token']}"}
        auth2_headers = {"Authorization": f"Bearer {login2_response['access_token']}"}
        
        # Create separate workspaces
        workspace1_data = TestDataFactory.create_tenant_data(name="User 1 Workspace")
        workspace2_data = TestDataFactory.create_tenant_data(name="User 2 Workspace")
        
        workspace1_response = await APITestHelper.create_workspace(
            async_client, auth1_headers, workspace1_data
        )
        workspace2_response = await APITestHelper.create_workspace(
            async_client, auth2_headers, workspace2_data
        )
        
        workspace1_id = workspace1_response["id"]
        workspace2_id = workspace2_response["id"]
        
        # Create artifacts in each workspace
        artifact1_data = TestDataFactory.create_artifact_data(name="User 1 Artifact")
        artifact2_data = TestDataFactory.create_artifact_data(name="User 2 Artifact")
        
        artifact1_response = await APITestHelper.create_artifact(
            async_client, workspace1_id, auth1_headers, artifact1_data
        )
        artifact2_response = await APITestHelper.create_artifact(
            async_client, workspace2_id, auth2_headers, artifact2_data
        )
        
        # Test that user1 cannot access user2's artifacts
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace2_id}/artifacts/{artifact2_response['id']}",
            headers=auth1_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test that user2 cannot access user1's artifacts
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace1_id}/artifacts/{artifact1_response['id']}",
            headers=auth2_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test that users can access their own artifacts
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace1_id}/artifacts/{artifact1_response['id']}",
            headers=auth1_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace2_id}/artifacts/{artifact2_response['id']}",
            headers=auth2_headers
        )
        assert response.status_code == status.HTTP_200_OK
    
    async def test_role_based_access_flow(self, async_client: AsyncClient):
        """Test role-based access control for artifacts."""
        # Create owner and member users
        owner_data = TestDataFactory.create_user_data(email="owner_rbac@example.com")
        member_data = TestDataFactory.create_user_data(email="member_rbac@example.com")
        
        await APITestHelper.register_user(async_client, owner_data)
        await APITestHelper.register_user(async_client, member_data)
        
        # Login both users
        owner_login = await APITestHelper.login_user(
            async_client, owner_data["email"], owner_data["password"]
        )
        member_login = await APITestHelper.login_user(
            async_client, member_data["email"], member_data["password"]
        )
        
        owner_headers = {"Authorization": f"Bearer {owner_login['access_token']}"}
        member_headers = {"Authorization": f"Bearer {member_login['access_token']}"}
        
        # Owner creates workspace
        workspace_data = TestDataFactory.create_tenant_data()
        workspace_response = await APITestHelper.create_workspace(
            async_client, owner_headers, workspace_data
        )
        
        workspace_id = workspace_response["id"]
        
        # Owner invites member to workspace (this would be done through workspace membership API)
        # For this test, we'll assume the member has been added with MEMBER role
        
        # Both users should be able to create artifacts
        owner_artifact_data = TestDataFactory.create_artifact_data(name="Owner Artifact")
        member_artifact_data = TestDataFactory.create_artifact_data(name="Member Artifact")
        
        owner_artifact = await APITestHelper.create_artifact(
            async_client, workspace_id, owner_headers, owner_artifact_data
        )
        member_artifact = await APITestHelper.create_artifact(
            async_client, workspace_id, member_headers, member_artifact_data
        )
        
        # Both users should be able to read all artifacts in the workspace
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace_id}/artifacts/{owner_artifact['id']}",
            headers=member_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace_id}/artifacts/{member_artifact['id']}",
            headers=owner_headers
        )
        assert response.status_code == status.HTTP_200_OK


class TestArtifactErrorHandlingIntegration:
    """Integration tests for artifact error scenarios."""
    
    async def test_invalid_artifact_data_flow(self, async_client: AsyncClient):
        """Test handling of invalid artifact data."""
        # Setup user and workspace
        user_data = TestDataFactory.create_user_data(email="invalid_artifact@example.com")
        await APITestHelper.register_user(async_client, user_data)
        
        login_response = await APITestHelper.login_user(
            async_client, user_data["email"], user_data["password"]
        )
        
        auth_headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        
        workspace_data = TestDataFactory.create_tenant_data()
        workspace_response = await APITestHelper.create_workspace(
            async_client, auth_headers, workspace_data
        )
        
        workspace_id = workspace_response["id"]
        
        # Test with missing required fields
        invalid_data = {"description": "Missing name field"}
        
        response = await async_client.post(
            f"/api/v1/workspaces/{workspace_id}/artifacts",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "name" in str(error_data["detail"])
        
        # Test with invalid data types
        invalid_data = {
            "name": "Valid Name",
            "tags": "should_be_array_not_string",
            "artifact_metadata": "should_be_object_not_string"
        }
        
        response = await async_client.post(
            f"/api/v1/workspaces/{workspace_id}/artifacts",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_nonexistent_artifact_operations(self, async_client: AsyncClient):
        """Test operations on non-existent artifacts."""
        # Setup user and workspace
        user_data = TestDataFactory.create_user_data(email="nonexistent_artifact@example.com")
        await APITestHelper.register_user(async_client, user_data)
        
        login_response = await APITestHelper.login_user(
            async_client, user_data["email"], user_data["password"]
        )
        
        auth_headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        
        workspace_data = TestDataFactory.create_tenant_data()
        workspace_response = await APITestHelper.create_workspace(
            async_client, auth_headers, workspace_data
        )
        
        workspace_id = workspace_response["id"]
        nonexistent_id = str(uuid4())
        
        # Test GET on non-existent artifact
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace_id}/artifacts/{nonexistent_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test PUT on non-existent artifact
        update_data = TestDataFactory.create_artifact_data()
        response = await async_client.put(
            f"/api/v1/workspaces/{workspace_id}/artifacts/{nonexistent_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test DELETE on non-existent artifact
        response = await async_client.delete(
            f"/api/v1/workspaces/{workspace_id}/artifacts/{nonexistent_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_unauthorized_artifact_access(self, async_client: AsyncClient):
        """Test unauthorized access to artifacts."""
        workspace_id = str(uuid4())
        artifact_id = str(uuid4())
        
        # Test without authentication
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace_id}/artifacts/{artifact_id}"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.get(
            f"/api/v1/workspaces/{workspace_id}/artifacts/{artifact_id}",
            headers=invalid_headers
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED