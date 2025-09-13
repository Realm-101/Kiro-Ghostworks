"""
Tests for database connectivity and basic operations.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from database import (
    create_database_engine,
    get_database_engine,
    get_session_factory,
    check_database_health,
    close_database_connections
)


class TestDatabaseEngine:
    """Test database engine creation and management."""
    
    def test_create_database_engine(self):
        """Test database engine creation."""
        with patch('database.get_settings') as mock_settings:
            # Mock settings
            mock_settings.return_value.database_url = "postgresql+asyncpg://user:pass@localhost/test"
            mock_settings.return_value.environment = "test"
            mock_settings.return_value.database_echo = False
            
            engine = create_database_engine()
            
            assert engine is not None
            assert hasattr(engine, 'connect')
    
    def test_get_database_engine_singleton(self):
        """Test that get_database_engine returns the same instance."""
        with patch('database.create_database_engine') as mock_create:
            mock_engine = AsyncMock()
            mock_create.return_value = mock_engine
            
            # First call should create engine
            engine1 = get_database_engine()
            assert engine1 == mock_engine
            assert mock_create.call_count == 1
            
            # Second call should return same engine
            engine2 = get_database_engine()
            assert engine2 == mock_engine
            assert mock_create.call_count == 1  # Should not create again
    
    def test_get_session_factory(self):
        """Test session factory creation."""
        with patch('database.get_database_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_get_engine.return_value = mock_engine
            
            session_factory = get_session_factory()
            
            assert session_factory is not None
            assert callable(session_factory)


class TestDatabaseHealth:
    """Test database health checking."""
    
    @pytest.mark.asyncio
    async def test_check_database_health_success(self):
        """Test successful database health check."""
        with patch('database.get_database_session') as mock_get_session:
            # Mock successful database session
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            
            # Create a proper mock row object
            class MockRow:
                health_check = 1
            
            mock_result.fetchone = lambda: MockRow()
            mock_session.execute = AsyncMock(return_value=mock_result)
            
            # Mock the async context manager
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_get_session.return_value.__aexit__.return_value = None
            
            # Mock engine and pool
            with patch('database.get_database_engine') as mock_get_engine:
                # Create a mock pool with regular methods (not async)
                class MockPool:
                    def size(self):
                        return 5
                    def checkedin(self):
                        return 3
                    def checkedout(self):
                        return 2
                    def overflow(self):
                        return 0
                
                mock_pool = MockPool()
                mock_engine = AsyncMock()
                mock_engine.pool = mock_pool
                mock_get_engine.return_value = mock_engine
                
                health = await check_database_health()
                
                assert health["status"] == "healthy"
                assert "connection_pool" in health
                assert health["connection_pool"]["size"] == 5
    
    @pytest.mark.asyncio
    async def test_check_database_health_failure(self):
        """Test database health check failure."""
        with patch('database.get_database_session') as mock_get_session:
            # Mock database connection failure
            mock_get_session.side_effect = Exception("Connection failed")
            
            health = await check_database_health()
            
            assert health["status"] == "unhealthy"
            assert "error" in health
            assert "Connection failed" in health["error"]


class TestDatabaseCleanup:
    """Test database cleanup operations."""
    
    @pytest.mark.asyncio
    async def test_close_database_connections(self):
        """Test closing database connections."""
        with patch('database._engine') as mock_engine:
            mock_engine.dispose = AsyncMock()
            
            await close_database_connections()
            
            mock_engine.dispose.assert_called_once()


class TestTenantSession:
    """Test tenant-isolated database sessions."""
    
    @pytest.mark.asyncio
    async def test_get_tenant_session(self):
        """Test tenant session context setting."""
        import uuid
        from database import get_tenant_session
        
        tenant_id = uuid.uuid4()
        
        with patch('database.get_database_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_get_session.return_value.__aexit__.return_value = None
            
            async with get_tenant_session(tenant_id) as session:
                # Verify tenant context was set
                mock_session.execute.assert_called_with(
                    "SET LOCAL app.current_tenant_id = :tenant_id",
                    {"tenant_id": str(tenant_id)}
                )
                
                assert session == mock_session