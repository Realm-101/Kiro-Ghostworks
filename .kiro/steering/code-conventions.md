---
inclusion: always
---

# Code Conventions and Style Guide

This document establishes consistent coding standards for TypeScript and Python across the Ghostworks SaaS platform.

## General Principles

### Code Quality Standards
- **Readability First**: Code should be self-documenting and easy to understand
- **Consistency**: Follow established patterns throughout the codebase
- **Maintainability**: Write code that is easy to modify and extend
- **Performance**: Consider performance implications of code decisions
- **Security**: Follow secure coding practices by default

### Documentation Requirements
- All public APIs must have comprehensive documentation
- Complex business logic requires inline comments
- README files for each service and package
- Architecture Decision Records (ADRs) for significant decisions

## TypeScript Conventions

### Naming Conventions
**Variables and Functions**
```typescript
// Use camelCase for variables and functions
const userCount = 10;
const artifactList = [];

// Use descriptive names
const calculateArtifactScore = (artifact: Artifact) => { };
const fetchUserWorkspaces = async (userId: string) => { };
```

**Types and Interfaces**
```typescript
// Use PascalCase for types and interfaces
interface UserProfile {
  id: string;
  email: string;
  displayName: string;
}

type WorkspaceRole = 'owner' | 'admin' | 'member';

// Use descriptive type names
interface CreateArtifactRequest {
  name: string;
  description?: string;
  tags: string[];
}
```

**Constants and Enums**
```typescript
// Use SCREAMING_SNAKE_CASE for constants
const MAX_UPLOAD_SIZE = 10 * 1024 * 1024; // 10MB
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

// Use PascalCase for enums
enum ArtifactStatus {
  Draft = 'draft',
  Published = 'published',
  Archived = 'archived'
}
```

**Files and Directories**
```
// Use kebab-case for file names
artifact-list.tsx
user-profile.component.ts
api-client.service.ts

// Use camelCase for directory names
components/
  artifactManagement/
  userProfile/
  workspaceSettings/
```

### Code Structure and Organization

**Import Organization**
```typescript
// 1. Node modules
import React from 'react';
import { NextPage } from 'next';
import { useQuery } from '@tanstack/react-query';

// 2. Internal modules (absolute imports)
import { ApiClient } from '@/lib/api-client';
import { useAuth } from '@/contexts/auth-context';

// 3. Relative imports
import { ArtifactCard } from './artifact-card';
import { SearchBar } from '../search/search-bar';

// 4. Type-only imports (separate)
import type { Artifact, User } from '@/types';
```

**Component Structure**
```typescript
// Component file structure
interface ComponentProps {
  // Props interface first
}

export const ComponentName: React.FC<ComponentProps> = ({ 
  prop1, 
  prop2 
}) => {
  // 1. Hooks
  const { user } = useAuth();
  const { data, isLoading } = useQuery(/* ... */);
  
  // 2. State
  const [localState, setLocalState] = useState('');
  
  // 3. Effects
  useEffect(() => {
    // Effect logic
  }, []);
  
  // 4. Event handlers
  const handleSubmit = (event: FormEvent) => {
    // Handler logic
  };
  
  // 5. Render helpers
  const renderContent = () => {
    // Render logic
  };
  
  // 6. Main render
  return (
    <div>
      {/* JSX */}
    </div>
  );
};
```

### TypeScript Best Practices

**Type Safety**
```typescript
// Use strict type definitions
interface ApiResponse<T> {
  data: T;
  message: string;
  success: boolean;
}

// Avoid 'any' - use specific types
const processArtifact = (artifact: Artifact): ProcessedArtifact => {
  // Implementation
};

// Use type guards for runtime type checking
const isArtifact = (obj: unknown): obj is Artifact => {
  return typeof obj === 'object' && 
         obj !== null && 
         'id' in obj && 
         'name' in obj;
};
```

**Error Handling**
```typescript
// Use Result pattern for error handling
type Result<T, E = Error> = 
  | { success: true; data: T }
  | { success: false; error: E };

const fetchArtifact = async (id: string): Promise<Result<Artifact>> => {
  try {
    const artifact = await apiClient.getArtifact(id);
    return { success: true, data: artifact };
  } catch (error) {
    return { success: false, error: error as Error };
  }
};
```

**React Patterns**
```typescript
// Use custom hooks for reusable logic
const useArtifacts = (workspaceId: string) => {
  return useQuery({
    queryKey: ['artifacts', workspaceId],
    queryFn: () => apiClient.getArtifacts(workspaceId),
    enabled: !!workspaceId
  });
};

// Use proper prop types
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}
```

## Python Conventions

### Naming Conventions
**Variables and Functions**
```python
# Use snake_case for variables and functions
user_count = 10
artifact_list = []

def calculate_artifact_score(artifact: Artifact) -> float:
    """Calculate the relevance score for an artifact."""
    pass

async def fetch_user_workspaces(user_id: str) -> list[Workspace]:
    """Fetch all workspaces for a given user."""
    pass
```

**Classes and Types**
```python
# Use PascalCase for classes
class ArtifactService:
    """Service for managing artifact operations."""
    
    def __init__(self, db: Database) -> None:
        self.db = db
    
    async def create_artifact(self, data: CreateArtifactRequest) -> Artifact:
        """Create a new artifact."""
        pass

# Use PascalCase for Pydantic models
class CreateArtifactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    tags: list[str] = Field(default_factory=list)
```

**Constants and Enums**
```python
# Use SCREAMING_SNAKE_CASE for constants
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_PAGE_SIZE = 20
JWT_ALGORITHM = "HS256"

# Use PascalCase for enums
class WorkspaceRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
```

**Files and Modules**
```
# Use snake_case for file names
artifact_service.py
user_repository.py
workspace_models.py

# Use snake_case for package names
services/
  artifact_management/
  user_profile/
  workspace_settings/
```

### Code Structure and Organization

**Import Organization**
```python
# 1. Standard library imports
import asyncio
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

# 2. Third-party imports
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local application imports
from app.core.config import settings
from app.core.database import get_db
from app.models.artifact import Artifact
from app.schemas.artifact import ArtifactCreate, ArtifactResponse
```

**Module Structure**
```python
"""
Module docstring describing the purpose and functionality.

This module handles artifact management operations including
creation, retrieval, updating, and deletion of artifacts.
"""

# Module-level constants
LOGGER = logging.getLogger(__name__)
MAX_ARTIFACTS_PER_PAGE = 100

# Type aliases
ArtifactID = str
UserID = str

# Main classes and functions
class ArtifactService:
    """Service class for artifact operations."""
    
    def __init__(self, db: AsyncSession) -> None:
        """Initialize the artifact service."""
        self.db = db
    
    async def create_artifact(
        self, 
        data: ArtifactCreate, 
        user_id: UserID
    ) -> Artifact:
        """
        Create a new artifact.
        
        Args:
            data: The artifact creation data
            user_id: ID of the user creating the artifact
            
        Returns:
            The created artifact
            
        Raises:
            ValidationError: If the data is invalid
            PermissionError: If the user lacks permissions
        """
        # Implementation
        pass
```

### Python Best Practices

**Type Hints**
```python
# Use comprehensive type hints
from typing import Any, Dict, List, Optional, Union
from collections.abc import Sequence

def process_artifacts(
    artifacts: Sequence[Artifact],
    filters: Dict[str, Any],
    user_id: Optional[str] = None
) -> List[Dict[str, Union[str, int, bool]]]:
    """Process artifacts with given filters."""
    pass

# Use generic types appropriately
from typing import Generic, TypeVar

T = TypeVar('T')

class Repository(Generic[T]):
    """Generic repository pattern."""
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID."""
        pass
```

**Error Handling**
```python
# Use specific exception types
class ArtifactNotFoundError(Exception):
    """Raised when an artifact is not found."""
    pass

class InsufficientPermissionsError(Exception):
    """Raised when user lacks required permissions."""
    pass

# Proper exception handling
async def get_artifact(artifact_id: str, user_id: str) -> Artifact:
    """Get artifact by ID with permission check."""
    try:
        artifact = await artifact_repository.get_by_id(artifact_id)
        if not artifact:
            raise ArtifactNotFoundError(f"Artifact {artifact_id} not found")
        
        if not await has_permission(user_id, artifact):
            raise InsufficientPermissionsError("User cannot access this artifact")
        
        return artifact
    except DatabaseError as e:
        logger.error(f"Database error retrieving artifact {artifact_id}: {e}")
        raise
```

**Async/Await Patterns**
```python
# Proper async function definitions
async def fetch_user_artifacts(
    user_id: str, 
    db: AsyncSession
) -> List[Artifact]:
    """Fetch all artifacts for a user."""
    query = select(Artifact).where(Artifact.created_by == user_id)
    result = await db.execute(query)
    return result.scalars().all()

# Use async context managers
async def process_with_transaction(data: Any) -> None:
    """Process data within a database transaction."""
    async with get_db_session() as session:
        async with session.begin():
            # Transaction operations
            await session.commit()
```

## Code Quality and Linting

### ESLint Configuration (TypeScript)
```json
{
  "extends": [
    "next/core-web-vitals",
    "@typescript-eslint/recommended",
    "prettier"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "warn",
    "@typescript-eslint/no-explicit-any": "error",
    "prefer-const": "error",
    "no-var": "error"
  }
}
```

### Ruff Configuration (Python)
```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]

[tool.ruff.lint.isort]
known-first-party = ["app", "tests"]
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.(js|ts|tsx)$
        args: [--fix]
```

## Documentation Standards

### Code Comments
```typescript
// TypeScript documentation
/**
 * Calculates the relevance score for an artifact based on user preferences.
 * 
 * @param artifact - The artifact to score
 * @param userPreferences - User's preference settings
 * @returns A score between 0 and 1, where 1 is most relevant
 * 
 * @example
 * ```typescript
 * const score = calculateRelevanceScore(artifact, preferences);
 * if (score > 0.8) {
 *   // High relevance artifact
 * }
 * ```
 */
const calculateRelevanceScore = (
  artifact: Artifact, 
  userPreferences: UserPreferences
): number => {
  // Implementation
};
```

```python
# Python documentation
def calculate_relevance_score(
    artifact: Artifact, 
    user_preferences: UserPreferences
) -> float:
    """
    Calculate the relevance score for an artifact based on user preferences.
    
    Args:
        artifact: The artifact to score
        user_preferences: User's preference settings
        
    Returns:
        A score between 0.0 and 1.0, where 1.0 is most relevant
        
    Raises:
        ValueError: If artifact or preferences are invalid
        
    Example:
        >>> score = calculate_relevance_score(artifact, preferences)
        >>> if score > 0.8:
        ...     # High relevance artifact
        ...     pass
    """
    # Implementation
    pass
```

### API Documentation
```python
# FastAPI endpoint documentation
@router.post(
    "/artifacts",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new artifact",
    description="Create a new artifact in the specified workspace",
    responses={
        201: {"description": "Artifact created successfully"},
        400: {"description": "Invalid input data"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Validation error"}
    }
)
async def create_artifact(
    artifact_data: ArtifactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ArtifactResponse:
    """Create a new artifact with the provided data."""
    # Implementation
    pass
```

## Performance Guidelines

### TypeScript Performance
- Use React.memo for expensive components
- Implement proper dependency arrays in useEffect
- Use useMemo and useCallback judiciously
- Avoid inline object/function creation in render

### Python Performance
- Use async/await for I/O operations
- Implement proper database query optimization
- Use connection pooling for database access
- Cache expensive computations appropriately

## Security Considerations

### Input Validation
```typescript
// TypeScript validation with Zod
import { z } from 'zod';

const CreateArtifactSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().max(1000).optional(),
  tags: z.array(z.string()).max(10)
});
```

```python
# Python validation with Pydantic
class CreateArtifactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: List[str] = Field(default_factory=list, max_items=10)
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tag format and content."""
        for tag in v:
            if not tag.strip() or len(tag) > 50:
                raise ValueError("Invalid tag format")
        return v
```

### Secure Coding Practices
- Always validate and sanitize user input
- Use parameterized queries for database operations
- Implement proper error handling without information leakage
- Follow principle of least privilege for permissions
- Use secure random number generation for tokens and IDs