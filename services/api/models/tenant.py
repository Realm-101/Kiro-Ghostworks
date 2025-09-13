"""
Tenant model for multi-tenant SaaS platform.
"""

from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Tenant(Base):
    """
    Tenant model representing a workspace/organization in the SaaS platform.
    
    Each tenant represents an isolated workspace with its own users,
    artifacts, and configuration settings.
    """
    
    __tablename__ = "tenants"
    
    # Basic tenant information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name of the tenant/workspace"
    )
    
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="URL-friendly identifier for the tenant"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description of the tenant/workspace"
    )
    
    # Tenant configuration and settings
    settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Tenant-specific configuration settings"
    )
    
    # Tenant status and metadata
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Whether the tenant is active and can be accessed"
    )
    
    # Relationships
    workspace_memberships = relationship(
        "WorkspaceMembership",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    
    artifacts = relationship(
        "Artifact",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, slug='{self.slug}', name='{self.name}')>"