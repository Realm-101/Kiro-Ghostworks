"""
Pydantic schemas for workspace API endpoints with comprehensive validation.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
import re

from pydantic import BaseModel, Field, field_validator, EmailStr


class WorkspaceBase(BaseModel):
    """Base workspace schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the workspace")
    description: Optional[str] = Field(None, max_length=500, description="Description of the workspace")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate workspace name with security checks."""
        if not v or not v.strip():
            raise ValueError("Workspace name cannot be empty")
        
        v = v.strip()
        
        if len(v) < 2:
            raise ValueError("Workspace name must be at least 2 characters long")
        
        if len(v) > 100:
            raise ValueError("Workspace name cannot exceed 100 characters")
        
        # Check for suspicious characters
        if any(char in v for char in ['<', '>', '"', "'", '&', '\x00']):
            raise ValueError("Workspace name contains invalid characters")
        
        # Must start with alphanumeric character
        if not v[0].isalnum():
            raise ValueError("Workspace name must start with a letter or number")
        
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate workspace description with security checks."""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
        
        if len(v) > 500:
            raise ValueError("Workspace description cannot exceed 500 characters")
        
        # Check for suspicious characters
        if '\x00' in v:
            raise ValueError("Workspace description contains invalid characters")
        
        return v


class CreateWorkspaceRequest(WorkspaceBase):
    """Schema for creating a new workspace."""
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Acme Corp",
                "description": "Main workspace for Acme Corporation projects"
            }
        }


class UpdateWorkspaceRequest(BaseModel):
    """Schema for updating workspace information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate workspace name if provided."""
        if v is None:
            return v
        return WorkspaceBase.validate_name(v)
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate workspace description if provided."""
        if v is None:
            return v
        return WorkspaceBase.validate_description(v)


class WorkspaceResponse(BaseModel):
    """Schema for workspace response data."""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    member_count: int
    current_user_role: str
    
    class Config:
        from_attributes = True


class InviteMemberRequest(BaseModel):
    """Schema for inviting a member to workspace."""
    email: EmailStr = Field(..., description="Email address of the user to invite")
    role: str = Field(..., description="Role to assign to the user")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate role is one of the allowed values."""
        allowed_roles = ['owner', 'admin', 'member']
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """Additional email validation."""
        # Basic length check
        if len(str(v)) > 254:  # RFC 5321 limit
            raise ValueError("Email address is too long")
        
        # Check for suspicious patterns
        email_str = str(v).lower()
        if any(char in email_str for char in ['\x00', '\r', '\n']):
            raise ValueError("Email contains invalid characters")
        
        return v


class UpdateMemberRoleRequest(BaseModel):
    """Schema for updating member role."""
    role: str = Field(..., description="New role for the member")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate role is one of the allowed values."""
        allowed_roles = ['owner', 'admin', 'member']
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v


class WorkspaceMemberResponse(BaseModel):
    """Schema for workspace member information."""
    id: UUID
    user_id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    joined_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class WorkspaceSwitchRequest(BaseModel):
    """Schema for switching to a workspace."""
    workspace_id: UUID = Field(..., description="ID of the workspace to switch to")
    
    @field_validator('workspace_id')
    @classmethod
    def validate_workspace_id(cls, v):
        """Validate workspace ID format."""
        if v is None:
            raise ValueError("Workspace ID is required")
        return v


class WorkspaceStatsResponse(BaseModel):
    """Schema for workspace statistics."""
    id: UUID
    name: str
    member_count: int
    artifact_count: int
    created_at: datetime
    last_activity: Optional[datetime]
    storage_used_bytes: int
    
    class Config:
        from_attributes = True