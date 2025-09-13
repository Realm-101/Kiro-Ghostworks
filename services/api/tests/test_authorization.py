"""
Tests for authorization utilities and workspace management.
"""

import pytest
import sys
import os
from uuid import uuid4
from fastapi import HTTPException

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from authorization import (
    get_user_workspace_membership,
    require_workspace_membership,
    require_workspace_role,
    InsufficientPermissionsError,
    WorkspaceNotFoundError,
    validate_workspace_access
)
from models.workspace_membership import WorkspaceRole


class TestWorkspaceMembership:
    """Test workspace membership validation."""
    
    @pytest.mark.asyncio
    async def test_get_user_workspace_membership_exists(self, test_session, sample_user, sample_tenant, sample_membership):
        """Test getting existing workspace membership."""
        membership = await get_user_workspace_membership(
            str(sample_user.id),
            str(sample_tenant.id),
            test_session
        )
        
        assert membership is not None
        assert membership.user_id == sample_user.id
        assert membership.tenant_id == sample_tenant.id
        assert membership.role == WorkspaceRole.MEMBER
        assert membership.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_user_workspace_membership_not_exists(self, test_session, sample_user):
        """Test getting non-existent workspace membership."""
        non_existent_workspace_id = str(uuid4())
        
        membership = await get_user_workspace_membership(
            str(sample_user.id),
            non_existent_workspace_id,
            test_session
        )
        
        assert membership is None
    
    @pytest.mark.asyncio
    async def test_require_workspace_membership_success(self, test_session, sample_user, sample_tenant, sample_membership):
        """Test requiring workspace membership when user is a member."""
        membership = await require_workspace_membership(
            str(sample_user.id),
            str(sample_tenant.id),
            test_session
        )
        
        assert membership is not None
        assert membership.user_id == sample_user.id
        assert membership.tenant_id == sample_tenant.id
    
    @pytest.mark.asyncio
    async def test_require_workspace_membership_failure(self, test_session, sample_user):
        """Test requiring workspace membership when user is not a member."""
        non_existent_workspace_id = str(uuid4())
        
        with pytest.raises(WorkspaceNotFoundError):
            await require_workspace_membership(
                str(sample_user.id),
                non_existent_workspace_id,
                test_session
            )


class TestRoleBasedAccess:
    """Test role-based access control."""
    
    @pytest.mark.asyncio
    async def test_require_role_sufficient_permissions(self, test_session, sample_user, sample_tenant, sample_admin_membership):
        """Test requiring role when user has sufficient permissions."""
        membership = await require_workspace_role(
            str(sample_user.id),
            str(sample_tenant.id),
            WorkspaceRole.MEMBER,  # Admin has higher permissions than Member
            test_session
        )
        
        assert membership is not None
        assert membership.role == WorkspaceRole.ADMIN
    
    @pytest.mark.asyncio
    async def test_require_role_exact_permissions(self, test_session, sample_user, sample_tenant, sample_admin_membership):
        """Test requiring role when user has exact permissions."""
        membership = await require_workspace_role(
            str(sample_user.id),
            str(sample_tenant.id),
            WorkspaceRole.ADMIN,  # Exact match
            test_session
        )
        
        assert membership is not None
        assert membership.role == WorkspaceRole.ADMIN
    
    @pytest.mark.asyncio
    async def test_require_role_insufficient_permissions(self, test_session, sample_user, sample_tenant, sample_membership):
        """Test requiring role when user has insufficient permissions."""
        with pytest.raises(InsufficientPermissionsError) as exc_info:
            await require_workspace_role(
                str(sample_user.id),
                str(sample_tenant.id),
                WorkspaceRole.ADMIN,  # Member doesn't have Admin permissions
                test_session
            )
        
        assert "Insufficient permissions" in str(exc_info.value.detail)
        assert "Required: admin" in str(exc_info.value.detail)
        assert "Current: member" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_require_role_not_member(self, test_session, sample_user):
        """Test requiring role when user is not a member."""
        non_existent_workspace_id = str(uuid4())
        
        with pytest.raises(WorkspaceNotFoundError):
            await require_workspace_role(
                str(sample_user.id),
                non_existent_workspace_id,
                WorkspaceRole.MEMBER,
                test_session
            )


class TestRoleHierarchy:
    """Test role hierarchy validation."""
    
    def test_member_permissions(self, sample_membership):
        """Test member role permissions."""
        assert sample_membership.has_permission(WorkspaceRole.MEMBER) is True
        assert sample_membership.has_permission(WorkspaceRole.ADMIN) is False
        assert sample_membership.has_permission(WorkspaceRole.OWNER) is False
    
    def test_admin_permissions(self, sample_admin_membership):
        """Test admin role permissions."""
        assert sample_admin_membership.has_permission(WorkspaceRole.MEMBER) is True
        assert sample_admin_membership.has_permission(WorkspaceRole.ADMIN) is True
        assert sample_admin_membership.has_permission(WorkspaceRole.OWNER) is False
    
    def test_owner_permissions(self, sample_owner_membership):
        """Test owner role permissions."""
        assert sample_owner_membership.has_permission(WorkspaceRole.MEMBER) is True
        assert sample_owner_membership.has_permission(WorkspaceRole.ADMIN) is True
        assert sample_owner_membership.has_permission(WorkspaceRole.OWNER) is True


class TestValidateWorkspaceAccess:
    """Test workspace access validation utility."""
    
    @pytest.mark.asyncio
    async def test_validate_access_membership_only(self, test_session, sample_user, sample_tenant, sample_membership):
        """Test validating workspace access without role requirement."""
        membership = await validate_workspace_access(
            str(sample_user.id),
            str(sample_tenant.id)
        )
        
        assert membership is not None
        assert membership.user_id == sample_user.id
    
    @pytest.mark.asyncio
    async def test_validate_access_with_role(self, test_session, sample_user, sample_tenant, sample_admin_membership):
        """Test validating workspace access with role requirement."""
        membership = await validate_workspace_access(
            str(sample_user.id),
            str(sample_tenant.id),
            WorkspaceRole.ADMIN
        )
        
        assert membership is not None
        assert membership.role == WorkspaceRole.ADMIN
    
    @pytest.mark.asyncio
    async def test_validate_access_insufficient_role(self, test_session, sample_user, sample_tenant, sample_membership):
        """Test validating workspace access with insufficient role."""
        with pytest.raises(InsufficientPermissionsError):
            await validate_workspace_access(
                str(sample_user.id),
                str(sample_tenant.id),
                WorkspaceRole.OWNER  # Member doesn't have Owner permissions
            )
    
    @pytest.mark.asyncio
    async def test_validate_access_not_member(self, test_session, sample_user):
        """Test validating workspace access when not a member."""
        non_existent_workspace_id = str(uuid4())
        
        with pytest.raises(WorkspaceNotFoundError):
            await validate_workspace_access(
                str(sample_user.id),
                non_existent_workspace_id
            )


class TestExceptionHandling:
    """Test custom exception handling."""
    
    def test_insufficient_permissions_error_with_user_role(self):
        """Test InsufficientPermissionsError with user role."""
        error = InsufficientPermissionsError(WorkspaceRole.ADMIN, WorkspaceRole.MEMBER)
        
        assert error.status_code == 403
        assert "Insufficient permissions" in error.detail
        assert "Required: admin" in error.detail
        assert "Current: member" in error.detail
    
    def test_insufficient_permissions_error_without_user_role(self):
        """Test InsufficientPermissionsError without user role."""
        error = InsufficientPermissionsError(WorkspaceRole.OWNER)
        
        assert error.status_code == 403
        assert "Insufficient permissions" in error.detail
        assert "Required: owner" in error.detail
        assert "Current:" not in error.detail
    
    def test_workspace_not_found_error(self):
        """Test WorkspaceNotFoundError."""
        workspace_id = str(uuid4())
        error = WorkspaceNotFoundError(workspace_id)
        
        assert error.status_code == 404
        assert "Workspace not found or access denied" in error.detail
        assert workspace_id in error.detail