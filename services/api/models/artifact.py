"""
Artifact model for the catalog service.
"""

import uuid
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Artifact(Base):
    """
    Artifact model for the catalog service.
    
    Artifacts are the main entities managed by the SaaS platform.
    They support flexible metadata, tagging, and full-text search.
    All artifacts are tenant-isolated for multi-tenancy.
    """
    
    __tablename__ = "artifacts"
    
    # Tenant isolation - CRITICAL for multi-tenancy
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Tenant ID for multi-tenant isolation"
    )
    
    # Basic artifact information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Name of the artifact"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the artifact"
    )
    
    # Tagging and categorization
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Tags for categorization and filtering"
    )
    
    # Flexible metadata storage
    artifact_metadata: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Flexible metadata storage for artifact-specific data"
    )
    
    # Audit trail
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who created the artifact"
    )
    
    # Status and visibility
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Whether the artifact is active (soft delete support)"
    )
    
    # Relationships
    tenant = relationship("Tenant", back_populates="artifacts")
    created_by_user = relationship(
        "User", 
        back_populates="created_artifacts",
        foreign_keys=[created_by]
    )
    
    # Database indexes for performance
    __table_args__ = (
        # Composite index for tenant-scoped queries
        Index("ix_artifacts_tenant_created", "tenant_id", "created_at"),
        # Index for tag-based filtering
        Index("ix_artifacts_tags", "tags", postgresql_using="gin"),
        # Index for metadata queries
        Index("ix_artifacts_metadata", "artifact_metadata", postgresql_using="gin"),
        # Full-text search index on name and description
        Index(
            "ix_artifacts_search",
            "name",
            "description",
            postgresql_using="gin",
            postgresql_ops={
                "name": "gin_trgm_ops",
                "description": "gin_trgm_ops"
            }
        ),
    )
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the artifact if not already present."""
        if tag not in self.tags:
            self.tags = self.tags + [tag]
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the artifact if present."""
        if tag in self.tags:
            self.tags = [t for t in self.tags if t != tag]
    
    def has_tag(self, tag: str) -> bool:
        """Check if the artifact has a specific tag."""
        return tag in self.tags
    
    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"