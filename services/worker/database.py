"""
Database connection utilities for Ghostworks Worker.
Provides shared database access with the API service.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
import structlog

from .config import get_worker_settings

logger = structlog.get_logger(__name__)

# Global database engine and session factory
_engine = None
_async_session_factory = None


def create_database_engine():
    """Create async database engine with connection pooling."""
    global _engine
    
    if _engine is not None:
        return _engine
    
    settings = get_worker_settings()
    
    # Create async engine with connection pooling
    _engine = create_async_engine(
        str(settings.database_url),
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=settings.database_echo,
        # Use NullPool for worker to avoid connection issues
        poolclass=NullPool if settings.environment == "test" else None,
    )
    
    logger.info(
        "Database engine created",
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=settings.database_echo,
    )
    
    return _engine


def create_session_factory():
    """Create async session factory."""
    global _async_session_factory
    
    if _async_session_factory is not None:
        return _async_session_factory
    
    engine = create_database_engine()
    _async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    logger.info("Database session factory created")
    return _async_session_factory


@asynccontextmanager
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session with automatic cleanup.
    
    Usage:
        async with get_database_session() as session:
            # Use session for database operations
            result = await session.execute(query)
    """
    session_factory = create_session_factory()
    session = session_factory()
    
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error("Database session error", error=str(e))
        raise
    finally:
        await session.close()


async def close_database_connections():
    """Close all database connections."""
    global _engine, _async_session_factory
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
        logger.info("Database connections closed")


# Synchronous wrapper for Celery tasks
def get_sync_database_session():
    """
    Get synchronous database session for Celery tasks.
    
    Note: This creates a new event loop for each call.
    Use sparingly and prefer async tasks when possible.
    """
    async def _get_session():
        async with get_database_session() as session:
            return session
    
    # Create new event loop for synchronous context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(_get_session())
    finally:
        loop.close()