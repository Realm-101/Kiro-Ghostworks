"""
Tests for workspace management routes.
"""

import pytest
import sys
import os
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from models.workspace_membership import WorkspaceRole


class TestWorkspaceCreation:
    """Test workspace creation endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_workspace_success(self, test_session, sample_user):
        """Test successful workspace creation."""
        from routes.workspaces import create_workspace, CreateWorkspaceRequest
        from auth import AuthenticatedUser
        from unittest.mock import MagicMock
        
        # Mock request object
        request = MagicMock()
        request.state.request_id = "test-request-id"
        
        # Create authenticated user
        current_user = AuthenticatedUser(
            id=str(sample_user.id),
            email=sample_user.email,
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        # Create workspace data
        workspace_data = CreateWorkspaceRequest(
            name="Test Workspace",
            slug="test-workspace",
            description="A test workspace",
            settings={"theme": "dark"}
        )
        
        # Mock the database session
        with patch('routes.workspaces.get_database_session') as mock_session:
            mock_session.return_value.__aenter__.return_value = test_session
            
            # Call the endpoint
            response = await create_workspace(request, workspace_data, current_user)
            
            assert response.name == "Test Workspace"
            assert response.slug == "test-workspace"
            assert response.description == "A test workspace"
            assert response.settings == {"theme": "dark"}
            assert response.is_active is True
            assert response.member_count == 1
            assert response.user_role == "owner"
    
    @pytest.mark.asyncio
    async def test_create_workspace_duplicate_slug(self, test_session, sample_user, sample_tenant):
        """Test workspace creation with duplicate slug."""
        from routes.workspaces import create_workspace, CreateWorkspaceRequest
        from auth import AuthenticatedUser
        from fastapi import HTTPException
        from unittest.mock import MagicMock
        
        # Mock request object
        request = MagicMock()
        request.state.request_id = "test-request-id"
        
        # Create authenticated user
        current_user = AuthenticatedUser(
            id=str(sample_user.id),
            email=sample_user.email,
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        # Try to create workspace with existing slug
        workspace_data = CreateWorkspaceRequest(
            name="Duplicate Workspace",
            slug=sample_tenant.slug,  # Use existing slug
            description="This should fail"
        )
        
        # Mock the database session
        with patch('routes.workspaces.get_database_session') as mock_session:
            mock_session.return_value.__aenter__.return_value = test_session
            
            # Should raise conflict error
            with pytest.raises(HTTPException) as exc_info:
                await create_workspace(request, workspace_data, current_user)
            
            assert exc_info.value.status_code == 409
            assert "already exists" in exc_info.value.detail


class TestWorkspaceRetrieval:
    """Test workspace retrieval endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_user_workspaces(self, test_session, sample_user, multiple_memberships):
        """Test listing user's workspaces."""
        from routes.workspaces import list_user_workspaces
        from auth import AuthenticatedUser
        
        # Create authenticated user
        current_user = AuthenticatedUser(
            id=str(sample_user.id),
            email=sample_user.email,
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        # Mock the database session
        with patch('routes.workspaces.get_database_session') as mock_session:
            mock_session.return_value.__aenter__.return_value = test_session
            
            # Call the endpoint
            workspaces = await list_user_workspaces(current_user)
            
            assert len(workspaces) == 2
            
            # Check that workspaces have correct roles
            workspace_roles = {ws.slug: ws.user_role for ws in workspaces}
            assert "member" in workspace_roles.values()
            assert "admin" in workspace_roles.values()
    
    @pytest.mark.asyncio
    async def test_get_workspace_success(self, test_session, sample_user, sample_tenant, sample_membership):
        """Test getting workspace details as a member."""
        from routes.workspaces import get_workspace
        from auth import AuthenticatedUser
        
        # Create authenticated user
        current_user = AuthenticatedUser(
            id=str(sample_user.id),
            email=sample_user.email,
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        # Mock the database session
        with patch('routes.workspaces.get_database_session') as mock_session:
            mock_session.return_value.__aenter__.return_value = test_session
            
            # Call the endpoint
            workspace = await get_workspace(str(sample_tenant.id), current_user)
            
            assert workspace.id == str(sample_tenant.id)
            assert workspace.name == sample_tenant.name
            assert workspace.slug == sample_tenant.slug
            assert workspace.user_role == "member"
    
    @pytest.mark.asyncio
    async def test_get_workspace_not_member(self, test_session, sample_user_2, sample_tenant):
        """Test getting workspace details when not a member."""
        from routes.workspaces import get_workspace
        from auth import AuthenticatedUser
        from fastapi import HTTPException
        
        # Create authenticated user (not a member)
        current_user = AuthenticatedUser(
            id=str(sample_user_2.id),
            email=sample_user_2.email,
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        # Mock the database session
        with patch('routes.workspaces.get_database_session') as mock_session:
            mock_session.return_value.__aenter__.return_value = test_session
            
            # Should raise not found error
            with pytest.raises(HTTPException) as exc_info:
                await get_workspace(str(sample_tenant.id), current_user)
            
            assert exc_info.value.status_code == 404
            assert "not found or access denied" in exc_info.value.detail


class TestWorkspaceUpdates:
    """Test workspace update endpoints."""
    
    @pytest.mark.asyncio
    async def test_update_workspace_as_admin(self, test_session, sample_user, sample_tenant, sample_admin_membership):
        """Test updating workspace as admin."""
        from routes.workspaces import update_workspace, UpdateWorkspaceRequest
        from auth import AuthenticatedUser
        from unittest.mock import MagicMock
        
        # Mock request object
        request = MagicMock()
        request.state.request_id = "test-request-id"
        
        # Create authenticated user
        current_user = AuthenticatedUser(
            id=str(sample_user.id),
            email=sample_user.email,
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        # Update data
        update_data = UpdateWorkspaceRequest(
            name="Updated Workspace",
            description="Updated description",
            settings={"theme": "light"}
        )
        
        # Mock the authorization check
        with patch('routes.workspaces.require_workspace_role') as mock_auth:
            mock_auth.return_value = sample_admin_membership
            
            # Mock the database session
            with patch('routes.workspaces.get_database_session') as mock_session:
                mock_session.return_value.__aenter__.return_value = test_session
                
                # Call the endpoint
                response = await update_workspace(
                    request, str(sample_tenant.id), update_data, current_user
                )
                
                assert response.name == "Updated Workspace"
                assert response.description == "Updated description"
                assert response.settings == {"theme": "light"}


class TestMemberManagement:
    """Test member management endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_workspace_members(self, test_session, sample_user, sample_tenant, sample_membership):
        """Test listing workspace members."""
        from routes.workspaces import list_workspace_members
        from auth import AuthenticatedUser
        
        # Create authenticated user
        current_user = AuthenticatedUser(
            id=str(sample_user.id),
            email=sample_user.email,
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        # Mock the authorization check
        with patch('routes.workspaces.require_workspace_membership') as mock_auth:
            mock_auth.return_value = sample_membership
            
            # Mock the database session
            with patch('routes.workspaces.get_database_session') as mock_session:
                mock_session.return_value.__aenter__.return_value = test_session
                
                # Call the endpoint
                members = await list_workspace_members(str(sample_tenant.id), current_user)
                
                assert len(members) >= 1
                assert any(member.user_email == sample_user.email for member in members)
    
    @pytest.mark.asyncio
    async def test_invite_member_as_admin(self, test_session, sample_user, sample_user_2, sample_tenant, sample_admin_membership):
        """Test inviting a member as admin."""
        from routes.workspaces import invite_member, InviteMemberRequest
        from auth import AuthenticatedUser
        from unittest.mock import MagicMock
        
        # Mock request object
        request = MagicMock()
        request.state.request_id = "test-request-id"
        
        # Create authenticated user (admin)
        current_user = AuthenticatedUser(
            id=str(sample_user.id),
            email=sample_user.email,
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        # Invite data
        invite_data = InviteMemberRequest(
            email=sample_user_2.email,
            role=WorkspaceRole.MEMBER
        )
        
        # Mock the authorization check
        with patch('routes.workspaces.require_workspace_role') as mock_auth:
            mock_auth.return_value = sample_admin_membership
            
            # Mock the database session
            with patch('routes.workspaces.get_database_session') as mock_session:
                mock_session.return_value.__aenter__.return_value = test_session
                
                # Call the endpoint
                response = await invite_member(
                    request, str(sample_tenant.id), invite_data, current_user
                )
                
                assert response["message"] == "Member invited successfully"
                assert response["email"] == sample_user_2.email
                assert response["role"] == "member"
    
    @pytest.mark.asyncio
    async def test_invite_nonexistent_user(self, test_session, sample_user, sample_tenant, sample_admin_membership):
        """Test inviting a non-existent user."""
        from routes.workspaces import invite_member, InviteMemberRequest
        from auth import AuthenticatedUser
        from fastapi import HTTPException
        from unittest.mock import MagicMock
        
        # Mock request object
        request = MagicMock()
        request.state.request_id = "test-request-id"
        
        # Create authenticated user (admin)
        current_user = AuthenticatedUser(
            id=str(sample_user.id),
            email=sample_user.email,
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        # Invite data with non-existent email
        invite_data = InviteMemberRequest(
            email="nonexistent@example.com",
            role=WorkspaceRole.MEMBER
        )
        
        # Mock the authorization check
        with patch('routes.workspaces.require_workspace_role') as mock_auth:
            mock_auth.return_value = sample_admin_membership
            
            # Mock the database session
            with patch('routes.workspaces.get_database_session') as mock_session:
                mock_session.return_value.__aenter__.return_value = test_session
                
                # Should raise not found error
                with pytest.raises(HTTPException) as exc_info:
                    await invite_member(
                        request, str(sample_tenant.id), invite_data, current_user
                    )
                
                assert exc_info.value.status_code == 404
                assert "not found" in exc_info.value.detail


class TestWorkspaceSwitching:
    """Test workspace switching functionality."""
    
    @pytest.mark.asyncio
    async def test_switch_workspace_success(self, test_session, sample_user, sample_tenant, sample_membership):
        """Test successful workspace switching."""
        from routes.workspaces import switch_workspace
        from auth import AuthenticatedUser
        from unittest.mock import MagicMock
        
        # Mock request object
        request = MagicMock()
        request.state.request_id = "test-request-id"
        
        # Create authenticated user
        current_user = AuthenticatedUser(
            id=str(sample_user.id),
            email=sample_user.email,
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        # Mock the authorization check
        with patch('routes.workspaces.require_workspace_membership') as mock_auth:
            mock_auth.return_value = sample_membership
            
            # Mock token creation
            with patch('routes.workspaces.create_access_token') as mock_access_token, \
                 patch('routes.workspaces.create_refresh_token') as mock_refresh_token:
                
                mock_access_token.return_value = "new_access_token"
                mock_refresh_token.return_value = "new_refresh_token"
                
                # Call the endpoint
                response = await switch_workspace(
                    request, str(sample_tenant.id), current_user
                )
                
                assert response["message"] == "Workspace switched successfully"
                assert response["workspace_id"] == str(sample_tenant.id)
                assert response["role"] == "member"
                assert response["access_token"] == "new_access_token"
                assert response["refresh_token"] == "new_refresh_token"
    
    @pytest.mark.asyncio
    async def test_switch_workspace_not_member(self, test_session, sample_user_2, sample_tenant):
        """Test switching to workspace when not a member."""
        from routes.workspaces import switch_workspace
        from auth import AuthenticatedUser
        from authorization import WorkspaceNotFoundError
        from unittest.mock import MagicMock
        
        # Mock request object
        request = MagicMock()
        request.state.request_id = "test-request-id"
        
        # Create authenticated user (not a member)
        current_user = AuthenticatedUser(
            id=str(sample_user_2.id),
            email=sample_user_2.email,
            tenant_id=None,
            role=None,
            is_verified=True,
            is_active=True
        )
        
        # Mock the authorization check to raise error
        with patch('routes.workspaces.require_workspace_membership') as mock_auth:
            mock_auth.side_effect = WorkspaceNotFoundError(str(sample_tenant.id))
            
            # Should raise workspace not found error
            with pytest.raises(WorkspaceNotFoundError):
                await switch_workspace(
                    request, str(sample_tenant.id), current_user
                )