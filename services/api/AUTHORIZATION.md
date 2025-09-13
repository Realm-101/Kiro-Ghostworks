# Multi-Tenant Authorization System

This document describes the implementation of the multi-tenant authorization system for the Ghostworks SaaS platform.

## Overview

The authorization system implements Role-Based Access Control (RBAC) with tenant isolation to ensure secure multi-tenant operations. It provides:

- **Workspace membership management** - Users can be members of multiple workspaces
- **Role-based permissions** - Three-tier role hierarchy (Owner > Admin > Member)
- **Tenant isolation** - Row-Level Security (RLS) at the database level
- **Workspace switching** - Users can switch between workspace contexts
- **Authorization utilities** - Decorators and dependencies for route protection

## Architecture

### Role Hierarchy

The system implements a three-tier role hierarchy:

1. **Owner** - Full workspace control, billing, member management
2. **Admin** - User management, artifact management, settings
3. **Member** - Artifact read/write access within workspace

Role permissions are hierarchical: Owner > Admin > Member

### Database Schema

```sql
-- Workspace membership with RBAC
CREATE TABLE workspace_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, tenant_id)
);

-- Row-Level Security for tenant isolation
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON artifacts 
FOR ALL TO authenticated_users 
USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

## API Endpoints

### Workspace Management

#### Create Workspace
```http
POST /api/v1/workspaces/
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "description": "Main workspace for Acme Corporation",
  "settings": {
    "timezone": "UTC",
    "features": ["artifacts", "analytics"]
  }
}
```

#### List User Workspaces
```http
GET /api/v1/workspaces/
Authorization: Bearer <token>
```

#### Get Workspace Details
```http
GET /api/v1/workspaces/{workspace_id}
Authorization: Bearer <token>
```

#### Update Workspace (Admin/Owner only)
```http
PUT /api/v1/workspaces/{workspace_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Updated Workspace Name",
  "description": "Updated description",
  "settings": {"theme": "dark"}
}
```

### Member Management

#### List Workspace Members
```http
GET /api/v1/workspaces/{workspace_id}/members
Authorization: Bearer <token>
```

#### Invite Member (Admin/Owner only)
```http
POST /api/v1/workspaces/{workspace_id}/members
Content-Type: application/json
Authorization: Bearer <token>

{
  "email": "user@example.com",
  "role": "member"
}
```

#### Update Member Role (Owner only)
```http
PUT /api/v1/workspaces/{workspace_id}/members/{user_id}/role
Content-Type: application/json
Authorization: Bearer <token>

{
  "role": "admin"
}
```

#### Remove Member (Owner only)
```http
DELETE /api/v1/workspaces/{workspace_id}/members/{user_id}
Authorization: Bearer <token>
```

### Workspace Switching

#### Switch Workspace Context
```http
POST /api/v1/workspaces/{workspace_id}/switch
Authorization: Bearer <token>
```

Returns new JWT tokens with workspace context:
```json
{
  "message": "Workspace switched successfully",
  "workspace_id": "uuid",
  "role": "admin",
  "access_token": "new_jwt_token",
  "refresh_token": "new_refresh_token",
  "token_type": "bearer",
  "expires_in": 900
}
```

## Authorization Utilities

### Permission Checking Functions

```python
from authorization import (
    require_workspace_membership,
    require_workspace_role,
    validate_workspace_access
)

# Check if user is a member
membership = await require_workspace_membership(user_id, workspace_id)

# Check if user has specific role or higher
membership = await require_workspace_role(user_id, workspace_id, WorkspaceRole.ADMIN)

# Validate access with optional role requirement
membership = await validate_workspace_access(user_id, workspace_id, WorkspaceRole.MEMBER)
```

### FastAPI Dependencies

```python
from authorization import (
    get_current_workspace_user,
    get_current_workspace_admin,
    get_current_workspace_owner
)

@router.get("/protected-endpoint")
async def protected_endpoint(
    workspace_user: tuple = Depends(get_current_workspace_user)
):
    current_user, membership = workspace_user
    # User is guaranteed to be a member of the workspace
    pass

@router.post("/admin-endpoint")
async def admin_endpoint(
    workspace_admin: tuple = Depends(get_current_workspace_admin)
):
    current_user, membership = workspace_admin
    # User is guaranteed to have admin or owner role
    pass
```

### Decorators

```python
from authorization import require_role, require_membership

@require_role(WorkspaceRole.ADMIN)
async def admin_only_function(workspace_id: str, current_user: AuthenticatedUser):
    # Function requires admin or owner role
    pass

@require_membership()
async def member_function(workspace_id: str, current_user: AuthenticatedUser):
    # Function requires workspace membership
    pass
```

## Tenant Isolation

### Row-Level Security (RLS)

The system uses PostgreSQL Row-Level Security to enforce tenant isolation:

```python
from authorization import set_tenant_context, with_tenant_context

# Manual context setting
async with get_database_session() as session:
    await set_tenant_context(session, tenant_id)
    # All queries now filtered by tenant_id
    artifacts = await session.execute(select(Artifact))

# Context manager approach
async with get_database_session() as session:
    result = await with_tenant_context(
        session, 
        tenant_id,
        lambda: session.execute(select(Artifact))
    )
```

### Middleware Integration

The `TenantIsolationMiddleware` automatically sets tenant context:

```python
# Automatically extracts tenant_id from:
# 1. Path parameters (workspace_id)
# 2. JWT token (tenant_id claim)
# 3. Request headers

app.add_middleware(TenantIsolationMiddleware)
```

## JWT Token Structure

### Access Token with Workspace Context

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "tenant_id": "workspace_uuid",
  "role": "admin",
  "token_type": "access",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "token_uuid"
}
```

### Token Lifecycle

1. **Initial Login** - No workspace context
2. **Workspace Switch** - New tokens with workspace context
3. **Token Refresh** - Preserves workspace context
4. **Logout** - Clears all tokens

## Error Handling

### Custom Exceptions

```python
from authorization import InsufficientPermissionsError, WorkspaceNotFoundError

# Insufficient permissions (403)
raise InsufficientPermissionsError(WorkspaceRole.ADMIN, current_role)

# Workspace not found or access denied (404)
raise WorkspaceNotFoundError(workspace_id)
```

### Error Responses

```json
{
  "error": "insufficient_permissions",
  "message": "Insufficient permissions. Required: admin, Current: member",
  "request_id": "uuid",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Security Considerations

### Permission Validation

- All workspace operations require authentication
- Role hierarchy is strictly enforced
- Owners cannot change their own role or remove themselves
- Inactive memberships are excluded from all operations

### Tenant Isolation

- Database-level isolation using RLS policies
- Automatic tenant context setting via middleware
- All queries filtered by tenant_id
- No cross-tenant data access possible

### Token Security

- Short-lived access tokens (15 minutes)
- Secure HTTP-only cookies
- Token rotation on refresh
- Workspace context preserved across refreshes

## Testing

### Unit Tests

```bash
# Run authorization tests
python -m pytest services/api/tests/test_authorization.py -v

# Run workspace route tests
python -m pytest services/api/tests/test_workspaces.py -v
```

### Test Coverage

- Role hierarchy validation
- Permission checking functions
- Workspace CRUD operations
- Member management
- Error handling
- Token lifecycle

## Usage Examples

### Creating a Workspace

```python
from routes.workspaces import CreateWorkspaceRequest

workspace_data = CreateWorkspaceRequest(
    name="My Company",
    slug="my-company",
    description="Company workspace",
    settings={"theme": "dark"}
)

# POST /api/v1/workspaces/
# User automatically becomes owner
```

### Inviting Members

```python
from routes.workspaces import InviteMemberRequest

invite_data = InviteMemberRequest(
    email="colleague@company.com",
    role=WorkspaceRole.MEMBER
)

# POST /api/v1/workspaces/{workspace_id}/members
# Requires admin or owner role
```

### Switching Workspaces

```python
# POST /api/v1/workspaces/{workspace_id}/switch
# Returns new tokens with workspace context
# All subsequent requests operate in that workspace
```

This authorization system provides comprehensive multi-tenant security with role-based access control, ensuring data isolation and proper permission management across all workspace operations.