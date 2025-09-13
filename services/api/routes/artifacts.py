"""
Artifact CRUD API endpoints with full-text search and filtering.
"""

import os
import sys
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from sqlalchemy import select, func, and_, or_, text, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

# Add the project root to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from packages.shared.src.logging_config import get_logger, log_context, with_async_operation

from auth import AuthenticatedUser, get_current_user
from authorization import (
    get_current_workspace_user,
    require_workspace_membership,
    set_tenant_context,
    WorkspaceRole
)
from database import get_database_session
from models.artifact import Artifact
from models.workspace_membership import WorkspaceMembership
from security import limiter
from schemas.artifact import (
    CreateArtifactRequest,
    UpdateArtifactRequest,
    ArtifactResponse,
    ArtifactSearchQuery,
    PaginatedArtifactResponse,
    ArtifactStatsResponse
)
from telemetry import get_tracer, business_telemetry
from metrics import metrics

logger = get_logger(__name__)
tracer = get_tracer(__name__)

router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}/artifacts", tags=["Artifacts"])


@router.post("", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_artifact(
    workspace_id: str,
    artifact_data: CreateArtifactRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session)
) -> ArtifactResponse:
    """
    Create a new artifact in the workspace.
    
    Requires workspace membership. All artifacts are automatically
    associated with the current workspace for tenant isolation.
    
    Args:
        workspace_id: Workspace UUID
        artifact_data: Artifact creation data
        request: FastAPI request object
        current_user: Currently authenticated user
        session: Database session
        
    Returns:
        Created artifact information
        
    Raises:
        HTTPException: If user lacks permissions or validation fails
    """
    with tracer.start_as_current_span("artifact.create") as span:
        # Add span attributes
        span.set_attribute("tenant.id", workspace_id)
        span.set_attribute("user.id", current_user.id)
        span.set_attribute("artifact.name", artifact_data.name)
        span.set_attribute("artifact.tags_count", len(artifact_data.tags))
        
        # Use structured logging context
        with log_context(
            tenant_id=workspace_id,
            user_id=current_user.id,
            operation="artifact.create",
            artifact_name=artifact_data.name,
            tags_count=len(artifact_data.tags)
        ):
            logger.info(
                "Creating artifact",
                artifact_name=artifact_data.name,
                tags=artifact_data.tags
            )
            
            # Verify workspace membership
            membership = await require_workspace_membership(current_user.id, workspace_id, session)
            
            # Set tenant context for RLS
            await set_tenant_context(session, workspace_id)
            
            try:
                # Create new artifact
                new_artifact = Artifact(
                    tenant_id=UUID(workspace_id),
                    name=artifact_data.name,
                    description=artifact_data.description,
                    tags=artifact_data.tags,
                    artifact_metadata=artifact_data.artifact_metadata,
                    created_by=UUID(current_user.id),
                    is_active=True
                )
                
                session.add(new_artifact)
                await session.commit()
                await session.refresh(new_artifact)
                
                # Record business metrics
                business_telemetry.record_artifact_created(
                    tenant_id=workspace_id,
                    user_id=current_user.id,
                    artifact_type="default"
                )
                metrics.record_artifact_created(workspace_id)
                
                # Add success attributes to span
                span.set_attribute("artifact.id", str(new_artifact.id))
                span.set_attribute("operation.success", True)
                
                logger.info(
                    "Artifact created successfully",
                    artifact_id=str(new_artifact.id),
                    artifact_name=new_artifact.name,
                    workspace_id=workspace_id,
                    user_id=current_user.id,
                    request_id=getattr(request.state, "request_id", None)
                )
                
                return ArtifactResponse.from_orm(new_artifact)
            
            except Exception as e:
                await session.rollback()
                
                # Add error attributes to span
                span.set_attribute("operation.success", False)
                span.set_attribute("error.message", str(e))
                
                logger.error(
                    "Failed to create artifact",
                    error=str(e),
                    workspace_id=workspace_id,
                    user_id=current_user.id,
                    request_id=getattr(request.state, "request_id", None)
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create artifact"
                )


@router.get("", response_model=PaginatedArtifactResponse)
@limiter.limit("60/minute")
async def list_artifacts(
    request: Request,
    workspace_id: str,
    q: Optional[str] = Query(None, description="Full-text search query"),
    tags: List[str] = Query(default=[], description="Filter by tags"),
    created_after: Optional[datetime] = Query(None, description="Filter artifacts created after this date"),
    created_before: Optional[datetime] = Query(None, description="Filter artifacts created before this date"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session)
) -> PaginatedArtifactResponse:
    """
    List artifacts in the workspace with optional filtering and search.
    
    Supports full-text search on name and description, tag filtering,
    date range filtering, and pagination.
    
    Args:
        workspace_id: Workspace UUID
        q: Full-text search query
        tags: List of tags to filter by
        created_after: Filter artifacts created after this date
        created_before: Filter artifacts created before this date
        limit: Number of results to return
        offset: Number of results to skip
        current_user: Currently authenticated user
        session: Database session
        
    Returns:
        Paginated list of artifacts
        
    Raises:
        HTTPException: If user lacks permissions
    """
    # Verify workspace membership
    await require_workspace_membership(current_user.id, workspace_id, session)
    
    # Set tenant context for RLS
    await set_tenant_context(session, workspace_id)
    
    try:
        # Build base query
        query = select(Artifact).where(
            and_(
                Artifact.tenant_id == UUID(workspace_id),
                Artifact.is_active == True
            )
        )
        
        # Add full-text search
        if q:
            # Use simple ILIKE search for compatibility (PostgreSQL-specific features in production)
            search_condition = or_(
                Artifact.name.ilike(f"%{q}%"),
                Artifact.description.ilike(f"%{q}%")
            )
            query = query.where(search_condition)
        
        # Add tag filtering
        if tags:
            # Use PostgreSQL array overlap operator
            query = query.where(Artifact.tags.op("&&")(tags))
        
        # Add date range filtering
        if created_after:
            query = query.where(Artifact.created_at >= created_after)
        
        if created_before:
            query = query.where(Artifact.created_at <= created_before)
        
        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Add ordering and pagination
        query = query.order_by(desc(Artifact.created_at))
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await session.execute(query)
        artifacts = result.scalars().all()
        
        # Convert to response models
        artifact_responses = [ArtifactResponse.from_orm(artifact) for artifact in artifacts]
        
        logger.info(
            "Artifacts listed successfully",
            workspace_id=workspace_id,
            user_id=current_user.id,
            total_results=total,
            returned_results=len(artifact_responses),
            search_query=q,
            tag_filters=tags
        )
        
        return PaginatedArtifactResponse(
            items=artifact_responses,
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + limit < total
        )
        
    except Exception as e:
        logger.error(
            "Failed to list artifacts",
            error=str(e),
            workspace_id=workspace_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve artifacts"
        )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
@limiter.limit("60/minute")
async def get_artifact(
    request: Request,
    workspace_id: str,
    artifact_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session)
) -> ArtifactResponse:
    """
    Get a specific artifact by ID.
    
    Args:
        workspace_id: Workspace UUID
        artifact_id: Artifact UUID
        current_user: Currently authenticated user
        session: Database session
        
    Returns:
        Artifact information
        
    Raises:
        HTTPException: If artifact not found or user lacks permissions
    """
    # Verify workspace membership
    await require_workspace_membership(current_user.id, workspace_id, session)
    
    # Set tenant context for RLS
    await set_tenant_context(session, workspace_id)
    
    try:
        # Query artifact with tenant isolation
        result = await session.execute(
            select(Artifact).where(
                and_(
                    Artifact.id == UUID(artifact_id),
                    Artifact.tenant_id == UUID(workspace_id),
                    Artifact.is_active == True
                )
            )
        )
        
        artifact = result.scalar_one_or_none()
        
        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact not found: {artifact_id}"
            )
        
        logger.info(
            "Artifact retrieved successfully",
            artifact_id=artifact_id,
            workspace_id=workspace_id,
            user_id=current_user.id
        )
        
        return ArtifactResponse.from_orm(artifact)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve artifact",
            error=str(e),
            artifact_id=artifact_id,
            workspace_id=workspace_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve artifact"
        )


@router.put("/{artifact_id}", response_model=ArtifactResponse)
@limiter.limit("30/minute")
async def update_artifact(
    workspace_id: str,
    artifact_id: str,
    artifact_data: UpdateArtifactRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session)
) -> ArtifactResponse:
    """
    Update an existing artifact.
    
    Args:
        workspace_id: Workspace UUID
        artifact_id: Artifact UUID
        artifact_data: Artifact update data
        request: FastAPI request object
        current_user: Currently authenticated user
        session: Database session
        
    Returns:
        Updated artifact information
        
    Raises:
        HTTPException: If artifact not found or user lacks permissions
    """
    # Verify workspace membership
    await require_workspace_membership(current_user.id, workspace_id, session)
    
    # Set tenant context for RLS
    await set_tenant_context(session, workspace_id)
    
    try:
        # Query existing artifact
        result = await session.execute(
            select(Artifact).where(
                and_(
                    Artifact.id == UUID(artifact_id),
                    Artifact.tenant_id == UUID(workspace_id),
                    Artifact.is_active == True
                )
            )
        )
        
        artifact = result.scalar_one_or_none()
        
        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact not found: {artifact_id}"
            )
        
        # Update fields that were provided
        update_data = artifact_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(artifact, field, value)
        
        # Update timestamp
        artifact.updated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(artifact)
        
        logger.info(
            "Artifact updated successfully",
            artifact_id=artifact_id,
            workspace_id=workspace_id,
            user_id=current_user.id,
            updated_fields=list(update_data.keys()),
            request_id=getattr(request.state, "request_id", None)
        )
        
        return ArtifactResponse.from_orm(artifact)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(
            "Failed to update artifact",
            error=str(e),
            artifact_id=artifact_id,
            workspace_id=workspace_id,
            user_id=current_user.id,
            request_id=getattr(request.state, "request_id", None)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update artifact"
        )


@router.patch("/{artifact_id}", response_model=ArtifactResponse)
async def patch_artifact(
    workspace_id: str,
    artifact_id: str,
    artifact_data: UpdateArtifactRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session)
) -> ArtifactResponse:
    """
    Partially update an existing artifact.
    
    This is an alias for the PUT endpoint to support both HTTP methods.
    
    Args:
        workspace_id: Workspace UUID
        artifact_id: Artifact UUID
        artifact_data: Artifact update data
        request: FastAPI request object
        current_user: Currently authenticated user
        session: Database session
        
    Returns:
        Updated artifact information
    """
    return await update_artifact(
        workspace_id, artifact_id, artifact_data, request, current_user, session
    )


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_artifact(
    workspace_id: str,
    artifact_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session)
) -> None:
    """
    Delete an artifact (soft delete).
    
    This performs a soft delete by setting is_active to False,
    preserving the data for audit purposes.
    
    Args:
        workspace_id: Workspace UUID
        artifact_id: Artifact UUID
        request: FastAPI request object
        current_user: Currently authenticated user
        session: Database session
        
    Raises:
        HTTPException: If artifact not found or user lacks permissions
    """
    # Verify workspace membership
    await require_workspace_membership(current_user.id, workspace_id, session)
    
    # Set tenant context for RLS
    await set_tenant_context(session, workspace_id)
    
    try:
        # Query existing artifact
        result = await session.execute(
            select(Artifact).where(
                and_(
                    Artifact.id == UUID(artifact_id),
                    Artifact.tenant_id == UUID(workspace_id),
                    Artifact.is_active == True
                )
            )
        )
        
        artifact = result.scalar_one_or_none()
        
        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact not found: {artifact_id}"
            )
        
        # Soft delete
        artifact.is_active = False
        artifact.updated_at = datetime.utcnow()
        
        await session.commit()
        
        logger.info(
            "Artifact deleted successfully",
            artifact_id=artifact_id,
            artifact_name=artifact.name,
            workspace_id=workspace_id,
            user_id=current_user.id,
            request_id=getattr(request.state, "request_id", None)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(
            "Failed to delete artifact",
            error=str(e),
            artifact_id=artifact_id,
            workspace_id=workspace_id,
            user_id=current_user.id,
            request_id=getattr(request.state, "request_id", None)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete artifact"
        )


@router.get("/search/advanced", response_model=PaginatedArtifactResponse)
@limiter.limit("60/minute")
async def advanced_search_artifacts(
    request: Request,
    workspace_id: str,
    search_params: ArtifactSearchQuery = Depends(),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session)
) -> PaginatedArtifactResponse:
    """
    Advanced artifact search with full-text search and filtering.
    
    This endpoint provides more sophisticated search capabilities
    including relevance scoring and advanced filtering options.
    
    Args:
        workspace_id: Workspace UUID
        search_params: Search parameters
        current_user: Currently authenticated user
        session: Database session
        
    Returns:
        Paginated search results with relevance scoring
    """
    # Verify workspace membership
    await require_workspace_membership(current_user.id, workspace_id, session)
    
    # Set tenant context for RLS
    await set_tenant_context(session, workspace_id)
    
    try:
        # Build base query
        query = select(Artifact).where(
            and_(
                Artifact.tenant_id == UUID(workspace_id),
                Artifact.is_active == True
            )
        )
        
        # Add full-text search with relevance scoring
        if search_params.q:
            # Use simple ILIKE search for compatibility (PostgreSQL-specific features in production)
            search_condition = or_(
                Artifact.name.ilike(f"%{search_params.q}%"),
                Artifact.description.ilike(f"%{search_params.q}%")
            )
            query = query.where(search_condition)
            
            # Simple ordering by name for compatibility
            query = query.order_by(Artifact.name)
        
        # Add tag filtering
        if search_params.tags:
            query = query.where(Artifact.tags.op("&&")(search_params.tags))
        
        # Add date range filtering
        if search_params.created_after:
            query = query.where(Artifact.created_at >= search_params.created_after)
        
        if search_params.created_before:
            query = query.where(Artifact.created_at <= search_params.created_before)
        
        # Get total count
        if search_params.q:
            # For search queries, count without relevance scoring
            count_query = select(func.count()).select_from(
                query.with_only_columns(Artifact.id).subquery()
            )
        else:
            count_query = select(func.count()).select_from(query.subquery())
            
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Add default ordering if no search query
        if not search_params.q:
            query = query.order_by(desc(Artifact.created_at))
        
        # Add pagination
        query = query.offset(search_params.offset).limit(search_params.limit)
        
        # Execute query
        result = await session.execute(query)
        artifacts = result.scalars().all()
        
        # Convert to response models
        artifact_responses = [ArtifactResponse.from_orm(artifact) for artifact in artifacts]
        
        logger.info(
            "Advanced artifact search completed",
            workspace_id=workspace_id,
            user_id=current_user.id,
            total_results=total,
            returned_results=len(artifact_responses),
            search_query=search_params.q,
            tag_filters=search_params.tags
        )
        
        return PaginatedArtifactResponse(
            items=artifact_responses,
            total=total,
            limit=search_params.limit,
            offset=search_params.offset,
            has_more=search_params.offset + search_params.limit < total
        )
        
    except Exception as e:
        logger.error(
            "Advanced artifact search failed",
            error=str(e),
            workspace_id=workspace_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )


@router.get("/stats", response_model=ArtifactStatsResponse)
@limiter.limit("60/minute")
async def get_artifact_stats(
    request: Request,
    workspace_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_database_session)
) -> ArtifactStatsResponse:
    """
    Get artifact statistics for the workspace.
    
    Returns counts and analytics about artifacts in the workspace.
    
    Args:
        workspace_id: Workspace UUID
        current_user: Currently authenticated user
        session: Database session
        
    Returns:
        Artifact statistics
    """
    # Verify workspace membership
    await require_workspace_membership(current_user.id, workspace_id, session)
    
    # Set tenant context for RLS
    await set_tenant_context(session, workspace_id)
    
    try:
        # Get total and active artifact counts
        total_result = await session.execute(
            select(func.count()).where(Artifact.tenant_id == UUID(workspace_id))
        )
        total_artifacts = total_result.scalar()
        
        active_result = await session.execute(
            select(func.count()).where(
                and_(
                    Artifact.tenant_id == UUID(workspace_id),
                    Artifact.is_active == True
                )
            )
        )
        active_artifacts = active_result.scalar()
        
        # Get tag statistics
        tag_stats_result = await session.execute(
            text("""
                SELECT unnest(tags) as tag, COUNT(*) as count
                FROM artifacts 
                WHERE tenant_id = :tenant_id AND is_active = true
                GROUP BY tag
                ORDER BY count DESC
                LIMIT 10
            """),
            {"tenant_id": str(workspace_id)}
        )
        
        tag_stats = tag_stats_result.all()
        most_used_tags = [{"tag": row.tag, "count": row.count} for row in tag_stats]
        total_tags = len(tag_stats)
        
        logger.info(
            "Artifact statistics retrieved",
            workspace_id=workspace_id,
            user_id=current_user.id,
            total_artifacts=total_artifacts,
            active_artifacts=active_artifacts
        )
        
        return ArtifactStatsResponse(
            total_artifacts=total_artifacts,
            active_artifacts=active_artifacts,
            total_tags=total_tags,
            most_used_tags=most_used_tags
        )
        
    except Exception as e:
        logger.error(
            "Failed to retrieve artifact statistics",
            error=str(e),
            workspace_id=workspace_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )