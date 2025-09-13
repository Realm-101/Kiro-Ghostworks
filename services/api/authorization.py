"""
Authorization utilities for role-based access control and tenant isolation.
"""

from functools import wraps
from typing import Optional, Callable, Any
from uuid import UUID

from fastapi import HTTPException, status, Depends, Request
from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from auth import AuthenticatedUser, get_current_user
from database import get_database_session
from models.workspace_membership import WorkspaceMembership, WorkspaceRole
from models.tenant import Tenant

logger = structlog.get_logger()


class InsufficientPermissionsError(HTTPException):
    """Custom exception for insufficient permissions."""
    
    def __init__(self, required_role: WorkspaceRole, user_role: Optional[WorkspaceRole] = None):
        detail = f"Insufficient permissions. Required: {required_role.value}"
        if user_role:
            detail += f", Current: {user_role.value}"
        
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class WorkspaceNotFoundError(HTTPException):
    """Custom exception for workspace not found or access denied."""
    
    def __init__(self, workspace_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace not found or access denied: {workspace_id}"
        )


async def get_user_workspace_membership(
    user_id: str,
    workspace_id: str,
    session: Optional[AsyncSession] = None
) -> Optional[WorkspaceMembership]:
    """
    Get user's membership in a specific workspace.
    
    Args:
        user_id: User UUID
        workspace_id: Workspace UUID
        session: Optional database session
        
    Returns:
        WorkspaceMembership if found, None otherwise
    """
    if session is None:
        async with get_database_session() as session:
            return await get_user_workspace_membership(user_id, workspace_id, session)
    
    result = await session.execute(
        select(WorkspaceMembership)
        .where(
            and_(
                WorkspaceMembership.user_id == UUID(user_id),
                WorkspaceMembership.tenant_id == UUID(workspace_id),
                WorkspaceMembership.is_active == True
            )
        )
    )
    
    return result.scalar_one_or_none()


async def require_workspace_membership(
    user_id: str,
    workspace_id: str,
    session: Optional[AsyncSession] = None
) -> WorkspaceMembership:
    """
    Require user to be a member of the specified workspace.
    
    Args:
        user_id: User UUID
        workspace_id: Workspace UUID
        session: Optional database session
        
    Returns:
        WorkspaceMembership if user is a member
        
    Raises:
        WorkspaceNotFoundError: If user is not a member
    """
    membership = await get_user_workspace_membership(user_id, workspace_id, session)
    
    if not membership:
        logger.warning(
            "Access denied: user not a member of workspace",
            user_id=user_id,
            workspace_id=workspace_id
        )
        raise WorkspaceNotFoundError(workspace_id)
    
    return membership


async def require_workspace_role(
    user_id: str,
    workspace_id: str,
    required_role: WorkspaceRole,
    session: Optional[AsyncSession] = None
) -> WorkspaceMembership:
    """
    Require user to have a specific role or higher in the workspace.
    
    Role hierarchy: OWNER > ADMIN > MEMBER
    
    Args:
        user_id: User UUID
        workspace_id: Workspace UUID
        required_role: Minimum required role
        session: Optional database session
        
    Returns:
        WorkspaceMembership if user has sufficient permissions
        
    Raises:
        WorkspaceNotFoundError: If user is not a member
        InsufficientPermissionsError: If user doesn't have required role
    """
    membership = await require_workspace_membership(user_id, workspace_id, session)
    
    if not membership.has_permission(required_role):
        logger.warning(
            "Access denied: insufficient permissions",
            user_id=user_id,
            workspace_id=workspace_id,
            required_role=required_role.value,
            user_role=membership.role.value
        )
        raise InsufficientPermissionsError(required_role, membership.role)
    
    return membership


async def set_tenant_context(
    session: AsyncSession,
    tenant_id: str
) -> None:
    """
    Set the tenant context for Row-Level Security (RLS).
    
    This sets the PostgreSQL session variable that RLS policies use
    to filter data by tenant.
    
    Args:
        session: Database session
        tenant_id: Tenant UUID to set as context
    """
    await session.execute(
        text("SET app.current_tenant_id = :tenant_id"),
        {"tenant_id": tenant_id}
    )
    
    logger.debug(
        "Tenant context set for RLS",
        tenant_id=tenant_id
    )


async def clear_tenant_context(session: AsyncSession) -> None:
    """
    Clear the tenant context for Row-Level Security (RLS).
    
    Args:
        session: Database session
    """
    await session.execute(text("RESET app.current_tenant_id"))
    
    logger.debug("Tenant context cleared")


def require_role(required_role: WorkspaceRole):
    """
    Decorator to require a specific workspace role for an endpoint.
    
    This decorator extracts the workspace_id from the path parameters
    and checks if the current user has the required role.
    
    Args:
        required_role: Minimum required role
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract workspace_id from kwargs (path parameters)
            workspace_id = kwargs.get("workspace_id")
            if not workspace_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="workspace_id is required"
                )
            
            # Extract current_user from kwargs (dependency injection)
            current_user = None
            for arg in args:
                if isinstance(arg, AuthenticatedUser):
                    current_user = arg
                    break
            
            if not current_user:
                for value in kwargs.values():
                    if isinstance(value, AuthenticatedUser):
                        current_user = value
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check role permissions
            await require_workspace_role(current_user.id, workspace_id, required_role)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_membership():
    """
    Decorator to require workspace membership for an endpoint.
    
    This decorator extracts the workspace_id from the path parameters
    and checks if the current user is a member of the workspace.
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract workspace_id from kwargs (path parameters)
            workspace_id = kwargs.get("workspace_id")
            if not workspace_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="workspace_id is required"
                )
            
            # Extract current_user from kwargs (dependency injection)
            current_user = None
            for arg in args:
                if isinstance(arg, AuthenticatedUser):
                    current_user = arg
                    break
            
            if not current_user:
                for value in kwargs.values():
                    if isinstance(value, AuthenticatedUser):
                        current_user = value
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check membership
            await require_workspace_membership(current_user.id, workspace_id)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


async def get_current_workspace_user(
    workspace_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> tuple[AuthenticatedUser, WorkspaceMembership]:
    """
    Dependency to get current user with workspace membership.
    
    This is a FastAPI dependency that can be used in route handlers
    to get both the authenticated user and their workspace membership.
    
    Args:
        workspace_id: Workspace UUID from path parameter
        current_user: Current authenticated user
        
    Returns:
        Tuple of (user, membership)
        
    Raises:
        WorkspaceNotFoundError: If user is not a member
    """
    membership = await require_workspace_membership(current_user.id, workspace_id)
    return current_user, membership


async def get_current_workspace_admin(
    workspace_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> tuple[AuthenticatedUser, WorkspaceMembership]:
    """
    Dependency to get current user with admin or owner role.
    
    Args:
        workspace_id: Workspace UUID from path parameter
        current_user: Current authenticated user
        
    Returns:
        Tuple of (user, membership)
        
    Raises:
        WorkspaceNotFoundError: If user is not a member
        InsufficientPermissionsError: If user is not admin or owner
    """
    membership = await require_workspace_role(current_user.id, workspace_id, WorkspaceRole.ADMIN)
    return current_user, membership


async def get_current_workspace_owner(
    workspace_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> tuple[AuthenticatedUser, WorkspaceMembership]:
    """
    Dependency to get current user with owner role.
    
    Args:
        workspace_id: Workspace UUID from path parameter
        current_user: Current authenticated user
        
    Returns:
        Tuple of (user, membership)
        
    Raises:
        WorkspaceNotFoundError: If user is not a member
        InsufficientPermissionsError: If user is not owner
    """
    membership = await require_workspace_role(current_user.id, workspace_id, WorkspaceRole.OWNER)
    return current_user, membership


class TenantIsolationMiddleware:
    """
    Middleware to handle tenant isolation for multi-tenant requests.
    
    This middleware automatically sets the tenant context for RLS
    when a workspace_id is present in the request path or token.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Create a request wrapper to access path parameters
        from fastapi import Request
        request = Request(scope, receive)
        
        # Try to extract workspace_id from path
        workspace_id = None
        path_params = scope.get("path_params", {})
        workspace_id = path_params.get("workspace_id")
        
        # If no workspace_id in path, try to get from token
        if not workspace_id:
            try:
                # Try to get from Authorization header
                auth_header = None
                for header_name, header_value in scope.get("headers", []):
                    if header_name == b"authorization":
                        auth_header = header_value.decode()
                        break
                
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    from auth import verify_token
                    token_data = verify_token(token, "access")
                    workspace_id = token_data.tenant_id
                
            except Exception:
                # If token verification fails, continue without tenant context
                pass
        
        # Set tenant context in request state for use by route handlers
        if workspace_id:
            scope["state"] = scope.get("state", {})
            scope["state"]["tenant_id"] = workspace_id
            
            # Also try to extract user_id from token for logging context
            user_id = None
            try:
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    from auth import verify_token
                    token_data = verify_token(token, "access")
                    user_id = token_data.sub
                    scope["state"]["user_id"] = user_id
            except Exception:
                pass
            
            logger.debug(
                "Tenant context detected",
                tenant_id=workspace_id,
                user_id=user_id,
                path=scope.get("path", "")
            )
        
        await self.app(scope, receive, send)


async def with_tenant_context(
    session: AsyncSession,
    tenant_id: str,
    operation: Callable[[], Any]
) -> Any:
    """
    Execute an operation with tenant context set for RLS.
    
    This is a utility function that sets the tenant context,
    executes the operation, and then clears the context.
    
    Args:
        session: Database session
        tenant_id: Tenant UUID
        operation: Async operation to execute
        
    Returns:
        Result of the operation
    """
    try:
        await set_tenant_context(session, tenant_id)
        result = await operation()
        return result
    finally:
        await clear_tenant_context(session)


def get_tenant_from_request(request: Request) -> Optional[str]:
    """
    Extract tenant ID from request state.
    
    This utility function gets the tenant ID that was set by
    the TenantIsolationMiddleware.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Tenant ID if available, None otherwise
    """
    return getattr(request.state, "tenant_id", None)


async def validate_workspace_access(
    user_id: str,
    workspace_id: str,
    required_role: Optional[WorkspaceRole] = None
) -> WorkspaceMembership:
    """
    Validate that a user has access to a workspace with optional role check.
    
    This is a utility function that combines membership and role validation.
    
    Args:
        user_id: User UUID
        workspace_id: Workspace UUID
        required_role: Optional minimum required role
        
    Returns:
        WorkspaceMembership if access is valid
        
    Raises:
        WorkspaceNotFoundError: If user is not a member
        InsufficientPermissionsError: If user doesn't have required role
    """
    if required_role:
        return await require_workspace_role(user_id, workspace_id, required_role)
    else:
        return await require_workspace_membership(user_id, workspace_id)


async def get_user_workspaces(user_id: str) -> list[dict]:
    """
    Get all workspaces a user is a member of.
    
    Args:
        user_id: User UUID
        
    Returns:
        List of workspace information with user roles
    """
    async with get_database_session() as session:
        result = await session.execute(
            select(WorkspaceMembership, Tenant)
            .join(Tenant, WorkspaceMembership.tenant_id == Tenant.id)
            .where(
                and_(
                    WorkspaceMembership.user_id == UUID(user_id),
                    WorkspaceMembership.is_active == True,
                    Tenant.is_active == True
                )
            )
        )
        
        memberships_and_workspaces = result.all()
        
        workspaces = []
        for membership, workspace in memberships_and_workspaces:
            workspaces.append({
                "id": str(workspace.id),
                "name": workspace.name,
                "slug": workspace.slug,
                "role": membership.role.value,
                "joined_at": membership.created_at.isoformat()
            })
        
        return workspaces