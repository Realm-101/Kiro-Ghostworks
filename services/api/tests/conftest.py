"""
Test configuration and fixtures for API tests.
"""

import pytest
import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base
from models.user import User
from models.tenant import Tenant
from models.workspace_membership import WorkspaceMembership, WorkspaceRole
from models.artifact import Artifact


# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def sample_user(test_session):
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="User",
        is_verified=True,
        is_active=True
    )
    
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    return user


@pytest.fixture
async def sample_user_2(test_session):
    """Create a second sample user for testing."""
    user = User(
        email="test2@example.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="User2",
        is_verified=True,
        is_active=True
    )
    
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    return user


@pytest.fixture
async def sample_tenant(test_session):
    """Create a sample tenant for testing."""
    tenant = Tenant(
        name="Test Company",
        slug="test-company",
        description="A test company",
        settings={"theme": "dark"},
        is_active=True
    )
    
    test_session.add(tenant)
    await test_session.commit()
    await test_session.refresh(tenant)
    
    return tenant


@pytest.fixture
async def sample_tenant_2(test_session):
    """Create a second sample tenant for testing."""
    tenant = Tenant(
        name="Test Company 2",
        slug="test-company-2",
        description="A second test company",
        settings={"theme": "light"},
        is_active=True
    )
    
    test_session.add(tenant)
    await test_session.commit()
    await test_session.refresh(tenant)
    
    return tenant


@pytest.fixture
async def sample_membership(test_session, sample_user, sample_tenant):
    """Create a sample workspace membership with MEMBER role."""
    membership = WorkspaceMembership(
        user_id=sample_user.id,
        tenant_id=sample_tenant.id,
        role=WorkspaceRole.MEMBER,
        is_active=True
    )
    
    test_session.add(membership)
    await test_session.commit()
    await test_session.refresh(membership)
    
    return membership


@pytest.fixture
async def sample_admin_membership(test_session, sample_user, sample_tenant):
    """Create a sample workspace membership with ADMIN role."""
    membership = WorkspaceMembership(
        user_id=sample_user.id,
        tenant_id=sample_tenant.id,
        role=WorkspaceRole.ADMIN,
        is_active=True
    )
    
    test_session.add(membership)
    await test_session.commit()
    await test_session.refresh(membership)
    
    return membership


@pytest.fixture
async def sample_owner_membership(test_session, sample_user, sample_tenant):
    """Create a sample workspace membership with OWNER role."""
    membership = WorkspaceMembership(
        user_id=sample_user.id,
        tenant_id=sample_tenant.id,
        role=WorkspaceRole.OWNER,
        is_active=True
    )
    
    test_session.add(membership)
    await test_session.commit()
    await test_session.refresh(membership)
    
    return membership


@pytest.fixture
async def sample_artifact(test_session, sample_tenant, sample_user):
    """Create a sample artifact for testing."""
    artifact = Artifact(
        tenant_id=sample_tenant.id,
        name="Test Artifact",
        description="A test artifact",
        tags=["test", "example"],
        artifact_metadata={"version": "1.0"},
        created_by=sample_user.id,
        is_active=True
    )
    
    test_session.add(artifact)
    await test_session.commit()
    await test_session.refresh(artifact)
    
    return artifact


@pytest.fixture
def sample_user_data():
    """Sample user data for API requests."""
    return {
        "email": "newuser@example.com",
        "password": "SecurePassword123!",
        "first_name": "New",
        "last_name": "User"
    }


@pytest.fixture
def sample_tenant_data():
    """Sample tenant data for API requests."""
    return {
        "name": "New Company",
        "slug": "new-company",
        "description": "A new test company",
        "settings": {"theme": "auto"}
    }


@pytest.fixture
def sample_login_data():
    """Sample login data for API requests."""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!"
    }


@pytest.fixture
async def multiple_memberships(test_session, sample_user, sample_tenant, sample_tenant_2):
    """Create multiple workspace memberships for testing."""
    # Member of first tenant
    membership1 = WorkspaceMembership(
        user_id=sample_user.id,
        tenant_id=sample_tenant.id,
        role=WorkspaceRole.MEMBER,
        is_active=True
    )
    
    # Admin of second tenant
    membership2 = WorkspaceMembership(
        user_id=sample_user.id,
        tenant_id=sample_tenant_2.id,
        role=WorkspaceRole.ADMIN,
        is_active=True
    )
    
    test_session.add_all([membership1, membership2])
    await test_session.commit()
    await test_session.refresh(membership1)
    await test_session.refresh(membership2)
    
    return [membership1, membership2]


@pytest.fixture
async def inactive_membership(test_session, sample_user_2, sample_tenant):
    """Create an inactive workspace membership for testing."""
    membership = WorkspaceMembership(
        user_id=sample_user_2.id,
        tenant_id=sample_tenant.id,
        role=WorkspaceRole.MEMBER,
        is_active=False  # Inactive membership
    )
    
    test_session.add(membership)
    await test_session.commit()
    await test_session.refresh(membership)
    
    return membership


@pytest.fixture
def mock_request_id():
    """Mock request ID for testing."""
    return str(uuid4())


@pytest.fixture
def mock_authenticated_user(sample_user):
    """Mock authenticated user for dependency injection."""
    from auth import AuthenticatedUser
    
    return AuthenticatedUser(
        id=str(sample_user.id),
        email=sample_user.email,
        tenant_id=None,
        role=None,
        is_verified=sample_user.is_verified,
        is_active=sample_user.is_active
    )


@pytest.fixture
def mock_authenticated_user_with_workspace(sample_user, sample_tenant):
    """Mock authenticated user with workspace context."""
    from auth import AuthenticatedUser
    
    return AuthenticatedUser(
        id=str(sample_user.id),
        email=sample_user.email,
        tenant_id=str(sample_tenant.id),
        role="member",
        is_verified=sample_user.is_verified,
        is_active=sample_user.is_active
    )


# Additional fixtures for artifact testing

@pytest.fixture
async def test_user(test_session):
    """Create a test user for artifact tests."""
    user = User(
        email="artifact_test@example.com",
        hashed_password="$2b$12$hashed_password_here",
        first_name="Artifact",
        last_name="Tester",
        is_verified=True,
        is_active=True
    )
    
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    return user


@pytest.fixture
async def other_user(test_session):
    """Create another test user for isolation tests."""
    user = User(
        email="other_test@example.com",
        hashed_password="$2b$12$hashed_password_here",
        first_name="Other",
        last_name="User",
        is_verified=True,
        is_active=True
    )
    
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    return user


@pytest.fixture
async def test_tenant(test_session):
    """Create a test tenant for artifact tests."""
    tenant = Tenant(
        name="Artifact Test Company",
        slug="artifact-test-company",
        description="A company for testing artifacts",
        settings={"theme": "dark"},
        is_active=True
    )
    
    test_session.add(tenant)
    await test_session.commit()
    await test_session.refresh(tenant)
    
    return tenant


@pytest.fixture
async def other_tenant(test_session):
    """Create another test tenant for isolation tests."""
    tenant = Tenant(
        name="Other Test Company",
        slug="other-test-company",
        description="Another company for testing isolation",
        settings={"theme": "light"},
        is_active=True
    )
    
    test_session.add(tenant)
    await test_session.commit()
    await test_session.refresh(tenant)
    
    return tenant


@pytest.fixture
async def test_membership(test_session, test_user, test_tenant):
    """Create a test workspace membership."""
    membership = WorkspaceMembership(
        user_id=test_user.id,
        tenant_id=test_tenant.id,
        role=WorkspaceRole.MEMBER,
        is_active=True
    )
    
    test_session.add(membership)
    await test_session.commit()
    await test_session.refresh(membership)
    
    return membership


@pytest.fixture
async def test_artifacts(test_session, test_tenant, test_user):
    """Create multiple test artifacts."""
    artifacts = []
    
    artifact_data = [
        {
            "name": "Test API Service",
            "description": "A test API service for unit testing",
            "tags": ["api", "test", "service"],
            "artifact_metadata": {"version": "1.0.0", "technology": "FastAPI"}
        },
        {
            "name": "Database Migration Tool",
            "description": "Tool for managing database migrations",
            "tags": ["database", "migration", "tool"],
            "artifact_metadata": {"version": "2.1.0", "technology": "Alembic"}
        },
        {
            "name": "Authentication Library",
            "description": "Library for handling user authentication",
            "tags": ["auth", "library", "security"],
            "artifact_metadata": {"version": "1.5.0", "technology": "Python"}
        }
    ]
    
    for data in artifact_data:
        artifact = Artifact(
            tenant_id=test_tenant.id,
            name=data["name"],
            description=data["description"],
            tags=data["tags"],
            artifact_metadata=data["artifact_metadata"],
            created_by=test_user.id,
            is_active=True
        )
        
        test_session.add(artifact)
        artifacts.append(artifact)
    
    await test_session.commit()
    
    for artifact in artifacts:
        await test_session.refresh(artifact)
    
    return artifacts


@pytest.fixture
async def db_session(test_session):
    """Alias for test_session to match test expectations."""
    return test_session


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for API requests."""
    # In a real test, this would create a valid JWT token
    # For now, we'll mock it
    from auth import create_access_token
    
    token = create_access_token(
        user_id=str(test_user.id),
        email=test_user.email
    )
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_auth_headers(other_user):
    """Create authentication headers for the other user."""
    from auth import create_access_token
    
    token = create_access_token(
        user_id=str(other_user.id),
        email=other_user.email
    )
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def async_client():
    """Create async HTTP client for testing."""
    from httpx import AsyncClient
    from main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client