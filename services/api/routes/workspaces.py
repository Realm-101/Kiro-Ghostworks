"""
Workspace management routes for multi-tenant authorization.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
import structlog

from auth import AuthenticatedUser, get_current_user
from database import get_database_session
from models.tenant import Tenant
from models.user import User
from models.workspace_membership import WorkspaceMembership, WorkspaceRole
from security import limiter
from metrics import metrics

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/workspaces", tags=["Workspaces"])


class CreateWorkspaceRequest(BaseModel):
    """Request model for creating a new workspace."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=1000)
    settings: dict = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "description": "Main workspace for Acme Corporation",
                "settings": {
                    "timezone": "UTC",
                    "features": ["artifacts", "analytics"]
                }
            }
        }


class UpdateWorkspaceRequest(BaseModel):
    """Request model for updating workspace information."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    settings: Optional[dict] = None
    is_active: Optional[bool] = None


class WorkspaceResponse(BaseModel):
    """Response model for workspace information."""
    id: str
    name: str
    slug: str
    description: Optional[str]
    settings: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime
    member_count: int
    user_role: Optional[str] = None


class WorkspaceMemberResponse(BaseModel):
    """Response model for workspace member information."""
    id: str
    user_id: str
    user_email: str
    user_name: str
    role: str
    is_active: bool
    joined_at: datetime


class InviteMemberRequest(BaseModel):
    """Request model for inviting a member to workspace."""
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    role: WorkspaceRole = Field(..., description="Role to assign to the member")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "role": "member"
            }
        }


class UpdateMemberRoleRequest(BaseModel):
    """Request model for updating member role."""
    role: WorkspaceRole = Field(..., description="New role for the member")


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_workspace(
    request: Request,
    workspace_data: CreateWorkspaceRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> WorkspaceResponse:
    """
    Create a new workspace.
    
    Creates a new tenant workspace and assigns the current user as owner.
    
    Args:
        request: FastAPI request object
        workspace_data: Workspace creation data
        current_user: Currently authenticated user
        
    Returns:
        Created workspace information
        
    Raises:
        HTTPException: If workspace slug already exists
    """
    async with get_database_session() as session:
        try:
            # Check if slug already exists
            existing_workspace = await session.execute(
                select(Tenant).where(Tenant.slug == workspace_data.slug)
            )
            if existing_workspace.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Workspace with slug '{workspace_data.slug}' already exists"
                )
            
            # Create new workspace
            new_workspace = Tenant(
                name=workspace_data.name,
                slug=workspace_data.slug,
                description=workspace_data.description,
                settings=workspace_data.settings,
                is_active=True
            )
            
            session.add(new_workspace)
            await session.flush()  # Get the ID
            
            # Add current user as owner
            membership = WorkspaceMembership(
                user_id=UUID(current_user.id),
                tenant_id=new_workspace.id,
                role=WorkspaceRole.OWNER,
                is_active=True
            )
            
            session.add(membership)
            await session.commit()
            await session.refresh(new_workspace)
            
            # Record workspace operation metric
            metrics.record_workspace_operation("create", str(new_workspace.id))
            
            logger.info(
                "Workspace created successfully",
                workspace_id=str(new_workspace.id),
                workspace_slug=new_workspace.slug,
                owner_id=current_user.id,
                request_id=getattr(request.state, "request_id", None)
            )
            
            return WorkspaceResponse(
                id=str(new_workspace.id),
                name=new_workspace.name,
                slug=new_workspace.slug,
                description=new_workspace.description,
                settings=new_workspace.settings,
                is_active=new_workspace.is_active,
                created_at=new_workspace.created_at,
                updated_at=new_workspace.updated_at,
                member_count=1,
                user_role=WorkspaceRole.OWNER.value
            )
            
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Workspace with slug '{workspace_data.slug}' already exists"
            )


@router.get("/", response_model=List[WorkspaceResponse])
@limiter.limit("60/minute")
async def list_user_workspaces(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> List[WorkspaceResponse]:
    """
    List all workspaces the current user is a member of.
    
    Returns workspaces with user's role in each workspace.
    
    Args:
        current_user: Currently authenticated user
        
    Returns:
        List of workspaces with user roles
    """
    async with get_database_session() as session:
        # Get user's workspace memberships with workspace details
        result = await session.execute(
            select(WorkspaceMembership, Tenant)
            .join(Tenant, WorkspaceMembership.tenant_id == Tenant.id)
            .where(
                and_(
                    WorkspaceMembership.user_id == UUID(current_user.id),
                    WorkspaceMembership.is_active == True,
                    Tenant.is_active == True
                )
            )
            .options(selectinload(WorkspaceMembership.tenant))
        )
        
        memberships_and_workspaces = result.all()
        
        workspaces = []
        for membership, workspace in memberships_and_workspaces:
            # Count active members
            member_count_result = await session.execute(
                select(WorkspaceMembership)
                .where(
                    and_(
                        WorkspaceMembership.tenant_id == workspace.id,
                        WorkspaceMembership.is_active == True
                    )
                )
            )
            member_count = len(member_count_result.all())
            
            workspaces.append(WorkspaceResponse(
                id=str(workspace.id),
                name=workspace.name,
                slug=workspace.slug,
                description=workspace.description,
                settings=workspace.settings,
                is_active=workspace.is_active,
                created_at=workspace.created_at,
                updated_at=workspace.updated_at,
                member_count=member_count,
                user_role=membership.role.value
            ))
        
        return workspaces


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> WorkspaceResponse:
    """
    Get workspace details.
    
    Returns workspace information if user is a member.
    
    Args:
        workspace_id: Workspace UUID
        current_user: Currently authenticated user
        
    Returns:
        Workspace information with user role
        
    Raises:
        HTTPException: If workspace not found or user not a member
    """
    async with get_database_session() as session:
        # Check if user is a member of this workspace
        membership_result = await session.execute(
            select(WorkspaceMembership)
            .where(
                and_(
                    WorkspaceMembership.user_id == UUID(current_user.id),
                    WorkspaceMembership.tenant_id == UUID(workspace_id),
                    WorkspaceMembership.is_active == True
                )
            )
        )
        membership = membership_result.scalar_one_or_none()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found or access denied"
            )
        
        # Get workspace details
        workspace_result = await session.execute(
            select(Tenant).where(
                and_(
                    Tenant.id == UUID(workspace_id),
                    Tenant.is_active == True
                )
            )
        )
        workspace = workspace_result.scalar_one_or_none()
        
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        # Count active members
        member_count_result = await session.execute(
            select(WorkspaceMembership)
            .where(
                and_(
                    WorkspaceMembership.tenant_id == workspace.id,
                    WorkspaceMembership.is_active == True
                )
            )
        )
        member_count = len(member_count_result.all())
        
        return WorkspaceResponse(
            id=str(workspace.id),
            name=workspace.name,
            slug=workspace.slug,
            description=workspace.description,
            settings=workspace.settings,
            is_active=workspace.is_active,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
            member_count=member_count,
            user_role=membership.role.value
        )


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    request: Request,
    workspace_id: str,
    workspace_data: UpdateWorkspaceRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> WorkspaceResponse:
    """
    Update workspace information.
    
    Only owners and admins can update workspace settings.
    
    Args:
        request: FastAPI request object
        workspace_id: Workspace UUID
        workspace_data: Updated workspace data
        current_user: Currently authenticated user
        
    Returns:
        Updated workspace information
        
    Raises:
        HTTPException: If workspace not found or insufficient permissions
    """
    from authorization import require_workspace_role
    
    # Check permissions (owner or admin required)
    await require_workspace_role(current_user.id, workspace_id, WorkspaceRole.ADMIN)
    
    async with get_database_session() as session:
        # Get workspace
        workspace_result = await session.execute(
            select(Tenant).where(Tenant.id == UUID(workspace_id))
        )
        workspace = workspace_result.scalar_one_or_none()
        
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        # Update workspace fields
        if workspace_data.name is not None:
            workspace.name = workspace_data.name
        if workspace_data.description is not None:
            workspace.description = workspace_data.description
        if workspace_data.settings is not None:
            workspace.settings = workspace_data.settings
        if workspace_data.is_active is not None:
            workspace.is_active = workspace_data.is_active
        
        await session.commit()
        await session.refresh(workspace)
        
        # Get user's role for response
        membership_result = await session.execute(
            select(WorkspaceMembership)
            .where(
                and_(
                    WorkspaceMembership.user_id == UUID(current_user.id),
                    WorkspaceMembership.tenant_id == workspace.id
                )
            )
        )
        membership = membership_result.scalar_one()
        
        # Count active members
        member_count_result = await session.execute(
            select(WorkspaceMembership)
            .where(
                and_(
                    WorkspaceMembership.tenant_id == workspace.id,
                    WorkspaceMembership.is_active == True
                )
            )
        )
        member_count = len(member_count_result.all())
        
        logger.info(
            "Workspace updated successfully",
            workspace_id=str(workspace.id),
            updated_by=current_user.id,
            request_id=getattr(request.state, "request_id", None)
        )
        
        return WorkspaceResponse(
            id=str(workspace.id),
            name=workspace.name,
            slug=workspace.slug,
            description=workspace.description,
            settings=workspace.settings,
            is_active=workspace.is_active,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
            member_count=member_count,
            user_role=membership.role.value
        )


@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> List[WorkspaceMemberResponse]:
    """
    List all members of a workspace.
    
    Only workspace members can view the member list.
    
    Args:
        workspace_id: Workspace UUID
        current_user: Currently authenticated user
        
    Returns:
        List of workspace members
        
    Raises:
        HTTPException: If workspace not found or user not a member
    """
    from authorization import require_workspace_membership
    
    # Check if user is a member of this workspace
    await require_workspace_membership(current_user.id, workspace_id)
    
    async with get_database_session() as session:
        # Get all active members with user details
        result = await session.execute(
            select(WorkspaceMembership, User)
            .join(User, WorkspaceMembership.user_id == User.id)
            .where(
                and_(
                    WorkspaceMembership.tenant_id == UUID(workspace_id),
                    WorkspaceMembership.is_active == True,
                    User.is_active == True
                )
            )
            .order_by(WorkspaceMembership.created_at)
        )
        
        members_and_users = result.all()
        
        members = []
        for membership, user in members_and_users:
            members.append(WorkspaceMemberResponse(
                id=str(membership.id),
                user_id=str(user.id),
                user_email=user.email,
                user_name=user.full_name,
                role=membership.role.value,
                is_active=membership.is_active,
                joined_at=membership.created_at
            ))
        
        return members


@router.post("/{workspace_id}/members", status_code=status.HTTP_201_CREATED)
async def invite_member(
    request: Request,
    workspace_id: str,
    invite_data: InviteMemberRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    """
    Invite a new member to the workspace.
    
    Only owners and admins can invite new members.
    
    Args:
        request: FastAPI request object
        workspace_id: Workspace UUID
        invite_data: Member invitation data
        current_user: Currently authenticated user
        
    Returns:
        Success message with membership details
        
    Raises:
        HTTPException: If insufficient permissions or user not found
    """
    from authorization import require_workspace_role
    
    # Check permissions (owner or admin required)
    await require_workspace_role(current_user.id, workspace_id, WorkspaceRole.ADMIN)
    
    async with get_database_session() as session:
        # Find user by email
        user_result = await session.execute(
            select(User).where(User.email == invite_data.email)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email '{invite_data.email}' not found"
            )
        
        # Check if user is already a member
        existing_membership = await session.execute(
            select(WorkspaceMembership)
            .where(
                and_(
                    WorkspaceMembership.user_id == user.id,
                    WorkspaceMembership.tenant_id == UUID(workspace_id)
                )
            )
        )
        
        if existing_membership.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this workspace"
            )
        
        # Create membership
        membership = WorkspaceMembership(
            user_id=user.id,
            tenant_id=UUID(workspace_id),
            role=invite_data.role,
            is_active=True
        )
        
        session.add(membership)
        await session.commit()
        
        # Record workspace operation metric
        metrics.record_workspace_operation("invite_member", workspace_id)
        
        logger.info(
            "Member invited successfully",
            workspace_id=workspace_id,
            invited_user_id=str(user.id),
            invited_by=current_user.id,
            role=invite_data.role.value,
            request_id=getattr(request.state, "request_id", None)
        )
        
        return {
            "message": "Member invited successfully",
            "user_id": str(user.id),
            "email": user.email,
            "role": invite_data.role.value
        }


@router.put("/{workspace_id}/members/{user_id}/role")
async def update_member_role(
    request: Request,
    workspace_id: str,
    user_id: str,
    role_data: UpdateMemberRoleRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    """
    Update a member's role in the workspace.
    
    Only owners can change roles. Owners cannot change their own role.
    
    Args:
        request: FastAPI request object
        workspace_id: Workspace UUID
        user_id: User UUID to update
        role_data: New role data
        current_user: Currently authenticated user
        
    Returns:
        Success message with updated role
        
    Raises:
        HTTPException: If insufficient permissions or invalid operation
    """
    from authorization import require_workspace_role
    
    # Check permissions (owner required)
    await require_workspace_role(current_user.id, workspace_id, WorkspaceRole.OWNER)
    
    # Prevent owners from changing their own role
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    async with get_database_session() as session:
        # Find the membership
        membership_result = await session.execute(
            select(WorkspaceMembership)
            .where(
                and_(
                    WorkspaceMembership.user_id == UUID(user_id),
                    WorkspaceMembership.tenant_id == UUID(workspace_id),
                    WorkspaceMembership.is_active == True
                )
            )
        )
        membership = membership_result.scalar_one_or_none()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in this workspace"
            )
        
        # Update role
        old_role = membership.role
        membership.role = role_data.role
        
        await session.commit()
        
        logger.info(
            "Member role updated successfully",
            workspace_id=workspace_id,
            user_id=user_id,
            old_role=old_role.value,
            new_role=role_data.role.value,
            updated_by=current_user.id,
            request_id=getattr(request.state, "request_id", None)
        )
        
        return {
            "message": "Member role updated successfully",
            "user_id": user_id,
            "old_role": old_role.value,
            "new_role": role_data.role.value
        }


@router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    request: Request,
    workspace_id: str,
    user_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    """
    Remove a member from the workspace.
    
    Only owners can remove members. Owners cannot remove themselves.
    
    Args:
        request: FastAPI request object
        workspace_id: Workspace UUID
        user_id: User UUID to remove
        current_user: Currently authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If insufficient permissions or invalid operation
    """
    from authorization import require_workspace_role
    
    # Check permissions (owner required)
    await require_workspace_role(current_user.id, workspace_id, WorkspaceRole.OWNER)
    
    # Prevent owners from removing themselves
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from the workspace"
        )
    
    async with get_database_session() as session:
        # Find the membership
        membership_result = await session.execute(
            select(WorkspaceMembership)
            .where(
                and_(
                    WorkspaceMembership.user_id == UUID(user_id),
                    WorkspaceMembership.tenant_id == UUID(workspace_id),
                    WorkspaceMembership.is_active == True
                )
            )
        )
        membership = membership_result.scalar_one_or_none()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in this workspace"
            )
        
        # Deactivate membership (soft delete)
        membership.is_active = False
        
        await session.commit()
        
        logger.info(
            "Member removed successfully",
            workspace_id=workspace_id,
            removed_user_id=user_id,
            removed_by=current_user.id,
            request_id=getattr(request.state, "request_id", None)
        )
        
        return {
            "message": "Member removed successfully",
            "user_id": user_id
        }


@router.post("/{workspace_id}/switch")
async def switch_workspace(
    request: Request,
    workspace_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    """
    Switch to a different workspace context.
    
    Updates the user's current workspace context and returns new tokens.
    
    Args:
        request: FastAPI request object
        workspace_id: Workspace UUID to switch to
        current_user: Currently authenticated user
        
    Returns:
        New tokens with workspace context
        
    Raises:
        HTTPException: If workspace not found or user not a member
    """
    from authorization import require_workspace_membership
    from auth import create_access_token, create_refresh_token
    from fastapi import Response
    from datetime import timedelta
    from config import get_settings
    
    settings = get_settings()
    
    # Check if user is a member of this workspace
    membership = await require_workspace_membership(current_user.id, workspace_id)
    
    # Create new tokens with workspace context
    access_token = create_access_token(
        user_id=current_user.id,
        email=current_user.email,
        tenant_id=workspace_id,
        role=membership.role.value
    )
    
    refresh_token = create_refresh_token(
        user_id=current_user.id,
        email=current_user.email
    )
    
    logger.info(
        "Workspace switched successfully",
        user_id=current_user.id,
        workspace_id=workspace_id,
        role=membership.role.value,
        request_id=getattr(request.state, "request_id", None)
    )
    
    return {
        "message": "Workspace switched successfully",
        "workspace_id": workspace_id,
        "role": membership.role.value,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": int(timedelta(minutes=settings.jwt_access_token_expire_minutes).total_seconds())
    }