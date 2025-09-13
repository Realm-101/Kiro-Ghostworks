"""
Global pytest configuration and fixtures for the test suite.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "services" / "api"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient

from main import app
from database import get_database_session, Base
from auth import get_current_user
from models.user import User
from models.tenant import Tenant
from models.workspace_membership import WorkspaceMembership
from models.artifact import Artifact

# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(test_session: AsyncSession):
    """Override database dependency for testing."""
    async def _override_get_db():
        yield test_session
    
    app.dependency_overrides[get_database_session] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_current_user():
    """Create mock current user for dependency override."""
    from auth import AuthenticatedUser
    
    mock_user = AuthenticatedUser(
        id="test-user-id",
        email="test@example.com",
        tenant_id="test-tenant-id",
        role="member",
        is_verified=True,
        is_active=True
    )
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield mock_user
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_session: AsyncSession) -> User:
    """Create test user in database."""
    from tests.utils.test_helpers import DatabaseTestHelper
    
    user = await DatabaseTestHelper.create_user(test_session)
    return user


@pytest.fixture
async def test_tenant(test_session: AsyncSession) -> Tenant:
    """Create test tenant in database."""
    from tests.utils.test_helpers import DatabaseTestHelper
    
    tenant = await DatabaseTestHelper.create_tenant(test_session)
    return tenant


@pytest.fixture
async def test_membership(
    test_session: AsyncSession, 
    test_user: User, 
    test_tenant: Tenant
) -> WorkspaceMembership:
    """Create test workspace membership."""
    from tests.utils.test_helpers import DatabaseTestHelper
    
    membership = await DatabaseTestHelper.create_membership(
        test_session, test_user, test_tenant
    )
    return membership


@pytest.fixture
async def test_artifact(
    test_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User
) -> Artifact:
    """Create test artifact in database."""
    from tests.utils.test_helpers import DatabaseTestHelper
    
    artifact = await DatabaseTestHelper.create_artifact(
        test_session, test_tenant, test_user
    )
    return artifact


@pytest.fixture
async def multiple_test_artifacts(
    test_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User
) -> list[Artifact]:
    """Create multiple test artifacts in database."""
    from tests.utils.test_helpers import DatabaseTestHelper
    
    artifacts = await DatabaseTestHelper.create_multiple_artifacts(
        test_session, test_tenant, test_user, count=5
    )
    return artifacts


@pytest.fixture
def auth_headers(test_user: User, test_tenant: Tenant, test_membership: WorkspaceMembership):
    """Create authentication headers for API requests."""
    from tests.utils.test_helpers import AuthTestHelper
    
    return AuthTestHelper.create_workspace_auth_headers(
        test_user, test_tenant, test_membership
    )


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file paths."""
    for item in items:
        # Add markers based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath) or "api" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Mark async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# Async test configuration
@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"