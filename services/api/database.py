"""
Database connection and session management for Ghostworks SaaS platform.
Provides async SQLAlchemy engine with connection pooling and tenant isolation.
"""

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.pool import NullPool, QueuePool
import structlog

from config import get_settings
from models import Base

logger = structlog.get_logger(__name__)

# Global database engine and session factory
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def create_database_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine with connection pooling.
    
    Returns:
        AsyncEngine: Configured async database engine
    """
    settings = get_settings()
    
    # Configure connection pool based on environment
    engine_kwargs = {
        "echo": settings.database_echo,
        "pool_pre_ping": True,  # Validate connections before use
        "pool_recycle": 3600,   # Recycle connections after 1 hour
        "connect_args": {
            "server_settings": {
                "application_name": "ghostworks_api",
            }
        }
    }
    
    if settings.environment == "test":
        # Use NullPool for testing to avoid connection issues
        engine_kwargs["poolclass"] = NullPool
    else:
        # Use QueuePool for production with configured limits
        engine_kwargs["poolclass"] = QueuePool
        engine_kwargs["pool_size"] = settings.database_pool_size
        engine_kwargs["max_overflow"] = settings.database_max_overflow
    
    engine = create_async_engine(
        str(settings.database_url),
        **engine_kwargs
    )
    
    logger.info(
        "Database engine created",
        database_url=str(settings.database_url).split("@")[-1],  # Hide credentials
        poolclass=engine_kwargs.get("poolclass", QueuePool).__name__,
        echo=settings.database_echo
    )
    
    return engine


def get_database_engine() -> AsyncEngine:
    """
    Get the global database engine, creating it if necessary.
    
    Returns:
        AsyncEngine: The global database engine
    """
    global _engine
    
    if _engine is None:
        _engine = create_database_engine()
    
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get the global session factory, creating it if necessary.
    
    Returns:
        async_sessionmaker: Session factory for creating database sessions
    """
    global _session_factory
    
    if _session_factory is None:
        engine = get_database_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
    
    return _session_factory


@asynccontextmanager
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session with automatic cleanup.
    
    Yields:
        AsyncSession: Database session for executing queries
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_tenant_session(tenant_id: uuid.UUID) -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session with tenant isolation context set.
    
    This sets the PostgreSQL session variable for Row-Level Security (RLS)
    to ensure all queries are automatically filtered by tenant.
    
    Args:
        tenant_id: UUID of the tenant for isolation
        
    Yields:
        AsyncSession: Database session with tenant context
    """
    async with get_database_session() as session:
        try:
            # Set tenant context for Row-Level Security
            await session.execute(
                "SET LOCAL app.current_tenant_id = :tenant_id",
                {"tenant_id": str(tenant_id)}
            )
            
            logger.debug(
                "Tenant context set for database session",
                tenant_id=str(tenant_id)
            )
            
            yield session
            
        except Exception:
            await session.rollback()
            raise


async def create_database_tables():
    """
    Create all database tables defined in the models.
    
    This should only be used in development or testing.
    In production, use Alembic migrations.
    """
    engine = get_database_engine()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created")


async def drop_database_tables():
    """
    Drop all database tables.
    
    WARNING: This will delete all data! Only use in testing.
    """
    engine = get_database_engine()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.warning("Database tables dropped")


async def close_database_connections():
    """
    Close all database connections and dispose of the engine.
    
    Should be called during application shutdown.
    """
    global _engine, _session_factory
    
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        
        logger.info("Database connections closed")


async def check_database_health() -> dict:
    """
    Check database connectivity and return health status.
    
    Returns:
        dict: Database health information
    """
    try:
        async with get_database_session() as session:
            # Simple query to test connectivity
            result = await session.execute("SELECT 1 as health_check")
            row = result.fetchone()
            
            if row and row.health_check == 1:
                # Get connection pool stats
                engine = get_database_engine()
                pool = engine.pool
                
                return {
                    "status": "healthy",
                    "response_time_ms": None,  # Could add timing here
                    "connection_pool": {
                        "size": pool.size() if hasattr(pool, 'size') else 0,
                        "checked_in": pool.checkedin() if hasattr(pool, 'checkedin') else 0,
                        "checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else 0,
                        "overflow": pool.overflow() if hasattr(pool, 'overflow') else 0,
                    }
                }
            else:
                return {"status": "unhealthy", "error": "Health check query failed"}
                
    except Exception as e:
        logger.error("Database health check failed", exc_info=e)
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Dependency for FastAPI routes
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting database sessions.
    
    Yields:
        AsyncSession: Database session for request handling
    """
    async with get_database_session() as session:
        yield session


# Dependency for FastAPI routes with tenant context
def get_tenant_db_session(tenant_id: uuid.UUID):
    """
    FastAPI dependency factory for getting tenant-isolated database sessions.
    
    Args:
        tenant_id: UUID of the tenant for isolation
        
    Returns:
        Callable that yields tenant-isolated database session
    """
    async def _get_tenant_session() -> AsyncGenerator[AsyncSession, None]:
        async with get_tenant_session(tenant_id) as session:
            yield session
    
    return _get_tenant_session