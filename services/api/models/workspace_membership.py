"""
Workspace membership model for role-based access control.
"""

import enum
import uuid

from sqlalchemy import String, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class WorkspaceRole(str, enum.Enum):
    """
    Workspace roles for role-based access control.
    
    - OWNER: Full control over workspace, billing, and member management
    - ADMIN: User management, artifact management, and settings
    - MEMBER: Artifact read/write access within workspace
    """
    
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class WorkspaceMembership(Base):
    """
    Workspace membership model linking users to tenants with roles.
    
    This model implements role-based access control (RBAC) by defining
    the relationship between users and tenants with specific roles.
    """
    
    __tablename__ = "workspace_memberships"
    
    # Foreign key relationships
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the user"
    )
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the tenant/workspace"
    )
    
    # Role assignment
    role: Mapped[WorkspaceRole] = mapped_column(
        Enum(WorkspaceRole),
        nullable=False,
        comment="User's role within the workspace"
    )
    
    # Membership status
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Whether the membership is active"
    )
    
    # Relationships
    user = relationship("User", back_populates="workspace_memberships")
    tenant = relationship("Tenant", back_populates="workspace_memberships")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "user_id", 
            "tenant_id", 
            name="uq_user_tenant_membership"
        ),
    )
    
    def has_permission(self, required_role: WorkspaceRole) -> bool:
        """
        Check if the membership has the required role or higher.
        
        Role hierarchy: OWNER > ADMIN > MEMBER
        """
        role_hierarchy = {
            WorkspaceRole.MEMBER: 1,
            WorkspaceRole.ADMIN: 2,
            WorkspaceRole.OWNER: 3
        }
        
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)
    
    def __repr__(self) -> str:
        return f"<WorkspaceMembership(user_id={self.user_id}, tenant_id={self.tenant_id}, role={self.role.value})>"