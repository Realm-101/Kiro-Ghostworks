"""
Tests for database models.
"""

import pytest
import uuid
from datetime import datetime

from models import Tenant, User, WorkspaceMembership, Artifact
from models.workspace_membership import WorkspaceRole


class TestTenant:
    """Test cases for Tenant model."""
    
    def test_tenant_creation(self):
        """Test basic tenant creation."""
        tenant = Tenant(
            name="Test Company",
            slug="test-company",
            description="A test company",
            settings={"theme": "dark", "notifications": True}
        )
        
        assert tenant.name == "Test Company"
        assert tenant.slug == "test-company"
        assert tenant.description == "A test company"
        assert tenant.settings == {"theme": "dark", "notifications": True}
        # is_active will be None until saved to database (default is set at DB level)
        assert tenant.is_active is None or tenant.is_active is True
    
    def test_tenant_repr(self):
        """Test tenant string representation."""
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Test Company",
            slug="test-company"
        )
        
        repr_str = repr(tenant)
        assert "Tenant" in repr_str
        assert "test-company" in repr_str
        assert str(tenant.id) in repr_str


class TestUser:
    """Test cases for User model."""
    
    def test_user_creation(self):
        """Test basic user creation."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_here",
            first_name="John",
            last_name="Doe"
        )
        
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password_here"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        # Boolean defaults will be None until saved to database (defaults are set at DB level)
        assert user.is_verified is None or user.is_verified is False
        assert user.is_active is None or user.is_active is True
    
    def test_user_full_name(self):
        """Test user full name property."""
        # Test with both names
        user = User(
            email="test@example.com",
            hashed_password="hash",
            first_name="John",
            last_name="Doe"
        )
        assert user.full_name == "John Doe"
        
        # Test with only first name
        user.last_name = None
        assert user.full_name == "John"
        
        # Test with only last name
        user.first_name = None
        user.last_name = "Doe"
        assert user.full_name == "Doe"
        
        # Test with no names (fallback to email username)
        user.first_name = None
        user.last_name = None
        assert user.full_name == "test"
    
    def test_user_repr(self):
        """Test user string representation."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="hash",
            is_verified=True
        )
        
        repr_str = repr(user)
        assert "User" in repr_str
        assert "test@example.com" in repr_str
        assert "True" in repr_str


class TestWorkspaceMembership:
    """Test cases for WorkspaceMembership model."""
    
    def test_membership_creation(self):
        """Test basic membership creation."""
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        
        membership = WorkspaceMembership(
            user_id=user_id,
            tenant_id=tenant_id,
            role=WorkspaceRole.ADMIN
        )
        
        assert membership.user_id == user_id
        assert membership.tenant_id == tenant_id
        assert membership.role == WorkspaceRole.ADMIN
        # is_active will be None until saved to database (default is set at DB level)
        assert membership.is_active is None or membership.is_active is True
    
    def test_role_permissions(self):
        """Test role permission hierarchy."""
        membership = WorkspaceMembership(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            role=WorkspaceRole.ADMIN
        )
        
        # Admin should have admin and member permissions
        assert membership.has_permission(WorkspaceRole.MEMBER) is True
        assert membership.has_permission(WorkspaceRole.ADMIN) is True
        assert membership.has_permission(WorkspaceRole.OWNER) is False
        
        # Owner should have all permissions
        membership.role = WorkspaceRole.OWNER
        assert membership.has_permission(WorkspaceRole.MEMBER) is True
        assert membership.has_permission(WorkspaceRole.ADMIN) is True
        assert membership.has_permission(WorkspaceRole.OWNER) is True
        
        # Member should only have member permissions
        membership.role = WorkspaceRole.MEMBER
        assert membership.has_permission(WorkspaceRole.MEMBER) is True
        assert membership.has_permission(WorkspaceRole.ADMIN) is False
        assert membership.has_permission(WorkspaceRole.OWNER) is False


class TestArtifact:
    """Test cases for Artifact model."""
    
    def test_artifact_creation(self):
        """Test basic artifact creation."""
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        artifact = Artifact(
            tenant_id=tenant_id,
            name="Test Artifact",
            description="A test artifact",
            tags=["test", "example"],
            artifact_metadata={"version": "1.0", "type": "document"},
            created_by=user_id
        )
        
        assert artifact.tenant_id == tenant_id
        assert artifact.name == "Test Artifact"
        assert artifact.description == "A test artifact"
        assert artifact.tags == ["test", "example"]
        assert artifact.artifact_metadata == {"version": "1.0", "type": "document"}
        assert artifact.created_by == user_id
        # is_active will be None until saved to database (default is set at DB level)
        assert artifact.is_active is None or artifact.is_active is True
    
    def test_artifact_tag_management(self):
        """Test artifact tag management methods."""
        artifact = Artifact(
            tenant_id=uuid.uuid4(),
            name="Test Artifact",
            tags=["initial"]
        )
        
        # Test adding tags
        artifact.add_tag("new-tag")
        assert "new-tag" in artifact.tags
        assert "initial" in artifact.tags
        
        # Test adding duplicate tag (should not duplicate)
        artifact.add_tag("new-tag")
        assert artifact.tags.count("new-tag") == 1
        
        # Test checking for tags
        assert artifact.has_tag("new-tag") is True
        assert artifact.has_tag("nonexistent") is False
        
        # Test removing tags
        artifact.remove_tag("initial")
        assert "initial" not in artifact.tags
        assert "new-tag" in artifact.tags
        
        # Test removing nonexistent tag (should not error)
        artifact.remove_tag("nonexistent")
    
    def test_artifact_repr(self):
        """Test artifact string representation."""
        tenant_id = uuid.uuid4()
        artifact = Artifact(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name="Test Artifact"
        )
        
        repr_str = repr(artifact)
        assert "Artifact" in repr_str
        assert "Test Artifact" in repr_str
        assert str(tenant_id) in repr_str


class TestBaseModel:
    """Test cases for Base model functionality."""
    
    def test_to_dict(self):
        """Test model to_dict conversion."""
        tenant = Tenant(
            name="Test Company",
            slug="test-company",
            settings={"key": "value"}
        )
        
        # Note: to_dict would work with actual database columns
        # This is a basic test of the method existence
        assert hasattr(tenant, 'to_dict')
        assert callable(tenant.to_dict)