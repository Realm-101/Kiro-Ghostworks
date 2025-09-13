"""
User model for authentication and user management.
"""

from typing import Optional

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class User(Base):
    """
    User model for authentication and user management.
    
    Users can be members of multiple tenants with different roles.
    Authentication is handled through email/password with JWT tokens.
    """
    
    __tablename__ = "users"
    
    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User's email address (used for login)"
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )
    
    # User profile information
    first_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="User's first name"
    )
    
    last_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="User's last name"
    )
    
    # Account status and verification
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the user's email has been verified"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the user account is active"
    )
    
    # Relationships
    workspace_memberships = relationship(
        "WorkspaceMembership",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    created_artifacts = relationship(
        "Artifact",
        back_populates="created_by_user",
        foreign_keys="Artifact.created_by"
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email.split("@")[0]  # Fallback to email username
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', verified={self.is_verified})>"