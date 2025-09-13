"""
Ghostworks SaaS Platform - FastAPI Backend Service
Main application entry point with health endpoints and basic configuration.
"""

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize OpenTelemetry before other imports
from telemetry import setup_telemetry
setup_telemetry()

# Initialize Prometheus metrics
from metrics import metrics, prometheus_middleware, metrics_endpoint

# Configure structured logging
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from packages.shared.src.logging_config import configure_structured_logging, get_logger, bind_context

# Configure logging for API service
configure_structured_logging(
    service_name="api",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="logs/api.log",
    enable_console=True,
    enable_rotation=True,
    max_log_size_mb=10,
    backup_count=5
)

logger = get_logger(__name__)


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    database: str = "not_configured"
    redis: str = "not_configured"


class DetailedHealthResponse(BaseModel):
    """Detailed health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    services: Dict[str, Any]
    uptime_seconds: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Ghostworks API service")
    
    # Initialize database connection pool
    from database import get_database_engine
    engine = get_database_engine()
    logger.info("Database connection pool initialized")
    
    # TODO: Initialize Redis connection
    # OpenTelemetry instrumentation is already initialized at module level
    
    yield
    
    # Shutdown
    logger.info("Shutting down Ghostworks API service")
    
    # Close database connections
    from database import close_database_connections
    await close_database_connections()
    
    # TODO: Close Redis connections


# Create FastAPI application with async lifespan
app = FastAPI(
    title="Ghostworks SaaS API",
    description="Production-grade multi-tenant SaaS platform with AI-native capabilities",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Import security middleware
from security import (
    SecurityHeadersMiddleware, 
    InputValidationMiddleware, 
    create_rate_limit_handler,
    limiter
)
from config import get_settings

settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Add security middleware (order matters)
app.add_middleware(SecurityHeadersMiddleware, settings=settings)
app.add_middleware(InputValidationMiddleware, settings=settings)

# Add tenant isolation middleware
from authorization import TenantIsolationMiddleware
app.add_middleware(TenantIsolationMiddleware)

# Add Prometheus metrics middleware
app.middleware("http")(prometheus_middleware)

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, create_rate_limit_handler())

# Store application start time for uptime calculation
app.state.start_time = datetime.utcnow()

# Include API routes
from routes.auth import router as auth_router
from routes.workspaces import router as workspaces_router
from routes.artifacts import router as artifacts_router

app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(artifacts_router)


@app.middleware("http")
async def add_correlation_id_middleware(request: Request, call_next):
    """Add correlation ID and context to all requests for tracing."""
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    # Extract tenant and user context from request if available
    tenant_id = getattr(request.state, 'tenant_id', None)
    user_id = getattr(request.state, 'user_id', None)
    
    # Build context for logging
    log_context = {
        "correlation_id": correlation_id,
        "method": request.method,
        "path": request.url.path,
        "user_agent": request.headers.get("user-agent", "unknown")
    }
    
    if tenant_id:
        log_context["tenant_id"] = str(tenant_id)
    if user_id:
        log_context["user_id"] = str(user_id)
    
    # Bind context for the request lifecycle
    with structlog.contextvars.bound_contextvars(**log_context):
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params) if request.query_params else None
        )
        
        try:
            response = await call_next(request)
            
            logger.info(
                "Request completed",
                status_code=response.status_code,
                method=request.method,
                path=request.url.path
            )
            
            response.headers["X-Correlation-ID"] = correlation_id
            return response
            
        except Exception as exc:
            logger.error(
                "Request failed",
                error=str(exc),
                method=request.method,
                path=request.url.path,
                exc_info=True
            )
            raise


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Basic health check endpoint.
    Returns the current status of the API service.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="0.1.0",
        environment=os.getenv("ENVIRONMENT", "development")
    )


@app.get("/health/detailed", response_model=DetailedHealthResponse, tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check endpoint with service dependencies.
    Returns comprehensive status information about the API and its dependencies.
    """
    current_time = datetime.utcnow()
    uptime = (current_time - app.state.start_time).total_seconds()
    
    # Check database health
    from database import check_database_health
    database_health = await check_database_health()
    
    services = {
        "database": database_health,
        "redis": {
            "status": "not_configured",
            "response_time_ms": None,
            "memory_usage": None
        },
        "external_apis": {
            "status": "not_applicable",
            "services": []
        }
    }
    
    # Determine overall status
    overall_status = "healthy"
    if database_health.get("status") != "healthy":
        overall_status = "unhealthy"
    
    return DetailedHealthResponse(
        status=overall_status,
        timestamp=current_time,
        version="0.1.0",
        environment=os.getenv("ENVIRONMENT", "development"),
        services=services,
        uptime_seconds=uptime
    )


@app.get("/metrics", tags=["Metrics"])
async def get_metrics():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    return await metrics_endpoint()


@app.get("/api/v1/system/stats", tags=["System"])
async def get_system_stats():
    """
    Get system-wide statistics for the demo tour.
    Returns counts of users, workspaces, and artifacts across all tenants.
    Falls back to demo data if database is not available.
    """
    try:
        from database import get_database_session
        from models.user import User
        from models.tenant import Tenant
        from models.artifact import Artifact
        from sqlalchemy import select, func
        
        async with get_database_session() as session:
            # Get total users
            users_result = await session.execute(select(func.count()).select_from(User))
            total_users = users_result.scalar() or 0
            
            # Get total workspaces (tenants)
            workspaces_result = await session.execute(select(func.count()).select_from(Tenant))
            total_workspaces = workspaces_result.scalar() or 0
            
            # Get total artifacts
            artifacts_result = await session.execute(select(func.count()).select_from(Artifact))
            total_artifacts = artifacts_result.scalar() or 0
            
            # Get active artifacts
            active_artifacts_result = await session.execute(
                select(func.count()).where(Artifact.is_active == True)
            )
            active_artifacts = active_artifacts_result.scalar() or 0
            
            return {
                "users": total_users,
                "workspaces": total_workspaces,
                "artifacts": total_artifacts,
                "active_artifacts": active_artifacts,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        # Return demo data if database is not available
        logger.warning(f"Database not available for system stats, returning demo data: {e}")
        return {
            "users": 12,
            "workspaces": 3,
            "artifacts": 47,
            "active_artifacts": 42,
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Ghostworks SaaS API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    correlation_id = getattr(request.state, "correlation_id", None)
    
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )