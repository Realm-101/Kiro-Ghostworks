"""
Pydantic schemas for artifact API endpoints.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
import re


class ArtifactBase(BaseModel):
    """Base artifact schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the artifact")
    description: Optional[str] = Field(None, description="Detailed description of the artifact")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization and filtering")
    artifact_metadata: Dict[str, Any] = Field(default_factory=dict, description="Flexible metadata storage")
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate tags are non-empty strings with security checks."""
        if v is None:
            return []
        
        if len(v) > 20:  # Limit number of tags
            raise ValueError("Maximum 20 tags allowed")
        
        # Remove empty tags and duplicates
        cleaned_tags = []
        seen = set()
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("Tags must be strings")
            
            tag = tag.strip()
            if not tag:
                continue
                
            if len(tag) > 50:  # Limit tag length
                raise ValueError("Tag length cannot exceed 50 characters")
            
            # Check for suspicious characters
            if not re.match(r'^[a-zA-Z0-9\-_\s]+$', tag):
                raise ValueError("Tags can only contain letters, numbers, hyphens, underscores, and spaces")
            
            cleaned_tag = tag.lower()
            if cleaned_tag not in seen:
                cleaned_tags.append(cleaned_tag)
                seen.add(cleaned_tag)
        
        return cleaned_tags
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name with security checks."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        
        v = v.strip()
        
        if len(v) > 255:
            raise ValueError("Name cannot exceed 255 characters")
        
        # Check for suspicious characters that could indicate injection attempts
        if any(char in v for char in ['<', '>', '"', "'", '&', '\x00']):
            raise ValueError("Name contains invalid characters")
        
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate description with security checks."""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
        
        if len(v) > 2000:  # Limit description length
            raise ValueError("Description cannot exceed 2000 characters")
        
        # Check for suspicious characters
        if any(char in v for char in ['\x00']):
            raise ValueError("Description contains invalid characters")
        
        return v
    
    @field_validator('artifact_metadata')
    @classmethod
    def validate_metadata(cls, v):
        """Validate metadata with security checks."""
        if v is None:
            return {}
        
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        
        if len(v) > 50:  # Limit number of metadata keys
            raise ValueError("Maximum 50 metadata keys allowed")
        
        # Validate keys and values
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("Metadata keys must be strings")
            
            if len(key) > 100:
                raise ValueError("Metadata key length cannot exceed 100 characters")
            
            # Check for suspicious key patterns
            if not re.match(r'^[a-zA-Z0-9_\-\.]+$', key):
                raise ValueError("Metadata keys can only contain letters, numbers, underscores, hyphens, and dots")
            
            # Validate value types and sizes
            if isinstance(value, str):
                if len(value) > 1000:
                    raise ValueError("Metadata string values cannot exceed 1000 characters")
                if '\x00' in value:
                    raise ValueError("Metadata values contain invalid characters")
            elif isinstance(value, (int, float, bool)):
                pass  # These are safe
            elif value is None:
                pass  # None is acceptable
            else:
                raise ValueError("Metadata values must be strings, numbers, booleans, or null")
        
        return v


class CreateArtifactRequest(ArtifactBase):
    """Schema for creating a new artifact."""
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "User Authentication Service",
                "description": "Microservice handling user authentication and authorization",
                "tags": ["authentication", "microservice", "security"],
                "artifact_metadata": {
                    "technology": "FastAPI",
                    "version": "1.0.0",
                    "repository": "https://github.com/company/auth-service"
                }
            }
        }


class UpdateArtifactRequest(BaseModel):
    """Schema for updating an existing artifact."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Name of the artifact")
    description: Optional[str] = Field(None, description="Detailed description of the artifact")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization and filtering")
    artifact_metadata: Optional[Dict[str, Any]] = Field(None, description="Flexible metadata storage")
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate tags are non-empty strings."""
        if v is None:
            return None
        
        # Use the same validation as CreateArtifactRequest
        return ArtifactBase.validate_tags(v)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name is not empty after stripping."""
        if v is None:
            return None
        
        # Use the same validation as ArtifactBase
        return ArtifactBase.validate_name(v)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated User Authentication Service",
                "description": "Enhanced microservice with OAuth2 support",
                "tags": ["authentication", "microservice", "security", "oauth2"],
                "artifact_metadata": {
                    "technology": "FastAPI",
                    "version": "1.1.0",
                    "repository": "https://github.com/company/auth-service",
                    "features": ["JWT", "OAuth2", "RBAC"]
                }
            }
        }


class ArtifactResponse(BaseModel):
    """Schema for artifact response."""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    tags: List[str]
    artifact_metadata: Dict[str, Any]
    created_by: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "User Authentication Service",
                "description": "Microservice handling user authentication and authorization",
                "tags": ["authentication", "microservice", "security"],
                "artifact_metadata": {
                    "technology": "FastAPI",
                    "version": "1.0.0",
                    "repository": "https://github.com/company/auth-service"
                },
                "created_by": "123e4567-e89b-12d3-a456-426614174002",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class ArtifactSearchQuery(BaseModel):
    """Schema for artifact search and filtering."""
    q: Optional[str] = Field(None, description="Full-text search query")
    tags: List[str] = Field(default_factory=list, description="Filter by tags")
    created_after: Optional[datetime] = Field(None, description="Filter artifacts created after this date")
    created_before: Optional[datetime] = Field(None, description="Filter artifacts created before this date")
    limit: int = Field(default=20, ge=1, le=100, description="Number of results to return")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate and normalize tags."""
        if v is None:
            return []
        
        # Normalize tags to lowercase
        return [tag.strip().lower() for tag in v if tag and tag.strip()]
    
    class Config:
        json_schema_extra = {
            "example": {
                "q": "authentication service",
                "tags": ["microservice", "security"],
                "created_after": "2024-01-01T00:00:00Z",
                "limit": 20,
                "offset": 0
            }
        }


class PaginatedArtifactResponse(BaseModel):
    """Schema for paginated artifact responses."""
    items: List[ArtifactResponse]
    total: int = Field(..., ge=0, description="Total number of artifacts matching the query")
    limit: int = Field(..., ge=1, description="Number of results requested")
    offset: int = Field(..., ge=0, description="Number of results skipped")
    has_more: bool = Field(..., description="Whether there are more results available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
                        "name": "User Authentication Service",
                        "description": "Microservice handling user authentication and authorization",
                        "tags": ["authentication", "microservice", "security"],
                        "artifact_metadata": {
                            "technology": "FastAPI",
                            "version": "1.0.0"
                        },
                        "created_by": "123e4567-e89b-12d3-a456-426614174002",
                        "is_active": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "total": 1,
                "limit": 20,
                "offset": 0,
                "has_more": False
            }
        }


class ArtifactStatsResponse(BaseModel):
    """Schema for artifact statistics."""
    total_artifacts: int
    active_artifacts: int
    total_tags: int
    most_used_tags: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_artifacts": 150,
                "active_artifacts": 142,
                "total_tags": 45,
                "most_used_tags": [
                    {"tag": "microservice", "count": 25},
                    {"tag": "api", "count": 18},
                    {"tag": "security", "count": 12}
                ]
            }
        }