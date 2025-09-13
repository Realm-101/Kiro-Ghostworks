"""
Row-Level Security (RLS) smoke tests for tenant isolation.

These tests verify that PostgreSQL RLS policies prevent cross-tenant data access
and ensure proper tenant isolation at the database level.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.models.tenant import Tenant
from services.api.models.user import User
from services.api.models.workspace_membership import WorkspaceMembership, WorkspaceRole
from services.api.models.artifact import Artifact
from services.api.auth import hash_password


@pytest.fixture
async def test_tenants(db_session: AsyncSession):
    """Create test tenants for RLS testing."""
    tenant1 = Tenant(
        name="Test Tenant 1",
        slug="test-tenant-1",
        description="First test tenant for RLS",
        settings={"test": True},
        is_active=True
    )
    
    tenant2 = Tenant(
        name="Test Tenant 2", 
        slug="test-tenant-2",
        description="Second test tenant for RLS",
        settings={"test": True},
        is_active=True
    )
    
    db_session.add(tenant1)
    db_session.add(tenant2)
    await db_session.flush()
    
    return tenant1, tenant2


@pytest.fixture
async def test_users(db_session: AsyncSession, test_tenants):
    """Create test users for each tenant."""
    tenant1, tenant2 = test_tenants
    
    user1 = User(
        email="user1@tenant1.com",
        hashed_password=hash_password("testpass123"),
        first_name="User",
        last_name="One",
        is_verified=True,
        is_active=True
    )
    
    user2 = User(
        email="user2@tenant2.com", 
        hashed_password=hash_password("testpass123"),
        first_name="User",
        last_name="Two",
        is_verified=True,
        is_active=True
    )
    
    db_session.add(user1)
    db_session.add(user2)
    await db_session.flush()
    
    # Create workspace memberships
    membership1 = WorkspaceMembership(
        user_id=user1.id,
        tenant_id=tenant1.id,
        role=WorkspaceRole.OWNER,
        is_active=True
    )
    
    membership2 = WorkspaceMembership(
        user_id=user2.id,
        tenant_id=tenant2.id,
        role=WorkspaceRole.OWNER,
        is_active=True
    )
    
    db_session.add(membership1)
    db_session.add(membership2)
    await db_session.flush()
    
    return user1, user2


@pytest.fixture
async def test_artifacts(db_session: AsyncSession, test_tenants, test_users):
    """Create test artifacts for each tenant."""
    tenant1, tenant2 = test_tenants
    user1, user2 = test_users
    
    artifact1 = Artifact(
        tenant_id=tenant1.id,
        name="Tenant 1 Artifact",
        description="This artifact belongs to tenant 1",
        tags=["tenant1", "test"],
        artifact_metadata={"tenant": "1", "test": True},
        created_by=user1.id,
        is_active=True
    )
    
    artifact2 = Artifact(
        tenant_id=tenant2.id,
        name="Tenant 2 Artifact", 
        description="This artifact belongs to tenant 2",
        tags=["tenant2", "test"],
        artifact_metadata={"tenant": "2", "test": True},
        created_by=user2.id,
        is_active=True
    )
    
    db_session.add(artifact1)
    db_session.add(artifact2)
    await db_session.flush()
    
    return artifact1, artifact2


class TestRLSTenantIsolation:
    """Test suite for Row-Level Security tenant isolation."""
    
    async def test_rls_policy_exists(self, db_session: AsyncSession):
        """Verify that RLS policy exists on artifacts table."""
        result = await db_session.execute(text("""
            SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
            FROM pg_policies 
            WHERE tablename = 'artifacts' AND policyname = 'tenant_isolation'
        """))
        
        policy = result.fetchone()
        assert policy is not None, "RLS policy 'tenant_isolation' should exist on artifacts table"
        assert policy.tablename == 'artifacts'
        assert policy.policyname == 'tenant_isolation'
        
    async def test_rls_enabled_on_artifacts(self, db_session: AsyncSession):
        """Verify that RLS is enabled on the artifacts table."""
        result = await db_session.execute(text("""
            SELECT schemaname, tablename, rowsecurity
            FROM pg_tables 
            WHERE tablename = 'artifacts'
        """))
        
        table_info = result.fetchone()
        assert table_info is not None, "Artifacts table should exist"
        assert table_info.rowsecurity is True, "RLS should be enabled on artifacts table"
    
    async def test_same_tenant_access_allowed(self, db_session: AsyncSession, test_tenants, test_artifacts):
        """Test that users can access artifacts from their own tenant."""
        tenant1, tenant2 = test_tenants
        artifact1, artifact2 = test_artifacts
        
        # Set tenant context for tenant 1
        await db_session.execute(text(f"SET app.current_tenant_id = '{tenant1.id}'"))
        
        # Should be able to access tenant 1's artifact
        result = await db_session.execute(
            select(Artifact).where(Artifact.id == artifact1.id)
        )
        found_artifact = result.scalar_one_or_none()
        
        assert found_artifact is not None, "Should be able to access same tenant's artifact"
        assert found_artifact.id == artifact1.id
        assert found_artifact.tenant_id == tenant1.id
    
    async def test_cross_tenant_access_denied(self, db_session: AsyncSession, test_tenants, test_artifacts):
        """Test that users cannot access artifacts from other tenants."""
        tenant1, tenant2 = test_tenants
        artifact1, artifact2 = test_artifacts
        
        # Set tenant context for tenant 1
        await db_session.execute(text(f"SET app.current_tenant_id = '{tenant1.id}'"))
        
        # Should NOT be able to access tenant 2's artifact
        result = await db_session.execute(
            select(Artifact).where(Artifact.id == artifact2.id)
        )
        found_artifact = result.scalar_one_or_none()
        
        assert found_artifact is None, "Should NOT be able to access other tenant's artifact"
    
    async def test_tenant_context_switching(self, db_session: AsyncSession, test_tenants, test_artifacts):
        """Test that changing tenant context changes accessible artifacts."""
        tenant1, tenant2 = test_tenants
        artifact1, artifact2 = test_artifacts
        
        # Test access as tenant 1
        await db_session.execute(text(f"SET app.current_tenant_id = '{tenant1.id}'"))
        
        result = await db_session.execute(select(Artifact))
        tenant1_artifacts = result.scalars().all()
        
        # Should only see tenant 1's artifacts
        assert len(tenant1_artifacts) == 1
        assert tenant1_artifacts[0].id == artifact1.id
        assert tenant1_artifacts[0].tenant_id == tenant1.id
        
        # Switch to tenant 2
        await db_session.execute(text(f"SET app.current_tenant_id = '{tenant2.id}'"))
        
        result = await db_session.execute(select(Artifact))
        tenant2_artifacts = result.scalars().all()
        
        # Should only see tenant 2's artifacts
        assert len(tenant2_artifacts) == 1
        assert tenant2_artifacts[0].id == artifact2.id
        assert tenant2_artifacts[0].tenant_id == tenant2.id
    
    async def test_no_tenant_context_blocks_access(self, db_session: AsyncSession, test_artifacts):
        """Test that queries without tenant context are blocked."""
        artifact1, artifact2 = test_artifacts
        
        # Clear any tenant context
        await db_session.execute(text("RESET app.current_tenant_id"))
        
        # Should not be able to access any artifacts without tenant context
        result = await db_session.execute(select(Artifact))
        artifacts = result.scalars().all()
        
        assert len(artifacts) == 0, "Should not access any artifacts without tenant context"
    
    async def test_invalid_tenant_context_blocks_access(self, db_session: AsyncSession, test_artifacts):
        """Test that invalid tenant context blocks access."""
        artifact1, artifact2 = test_artifacts
        
        # Set invalid tenant context
        invalid_tenant_id = str(uuid.uuid4())
        await db_session.execute(text(f"SET app.current_tenant_id = '{invalid_tenant_id}'"))
        
        # Should not be able to access any artifacts with invalid tenant context
        result = await db_session.execute(select(Artifact))
        artifacts = result.scalars().all()
        
        assert len(artifacts) == 0, "Should not access any artifacts with invalid tenant context"
    
    async def test_rls_prevents_insert_to_wrong_tenant(self, db_session: AsyncSession, test_tenants, test_users):
        """Test that RLS prevents inserting artifacts with wrong tenant_id."""
        tenant1, tenant2 = test_tenants
        user1, user2 = test_users
        
        # Set tenant context for tenant 1
        await db_session.execute(text(f"SET app.current_tenant_id = '{tenant1.id}'"))
        
        # Try to insert artifact with tenant 2's ID (should fail or be filtered)
        malicious_artifact = Artifact(
            tenant_id=tenant2.id,  # Wrong tenant!
            name="Malicious Artifact",
            description="This should not be accessible",
            tags=["malicious"],
            artifact_metadata={"malicious": True},
            created_by=user1.id,
            is_active=True
        )
        
        db_session.add(malicious_artifact)
        await db_session.flush()
        
        # Even if insert succeeds, the artifact should not be visible
        # due to RLS policy on SELECT
        result = await db_session.execute(
            select(Artifact).where(Artifact.name == "Malicious Artifact")
        )
        found_artifact = result.scalar_one_or_none()
        
        assert found_artifact is None, "Malicious artifact should not be visible due to RLS"
    
    async def test_rls_prevents_update_of_other_tenant_data(self, db_session: AsyncSession, test_tenants, test_artifacts):
        """Test that RLS prevents updating artifacts from other tenants."""
        tenant1, tenant2 = test_tenants
        artifact1, artifact2 = test_artifacts
        
        # Set tenant context for tenant 1
        await db_session.execute(text(f"SET app.current_tenant_id = '{tenant1.id}'"))
        
        # Try to update tenant 2's artifact (should not work)
        await db_session.execute(
            text("UPDATE artifacts SET name = 'Hacked!' WHERE id = :artifact_id"),
            {"artifact_id": artifact2.id}
        )
        
        # Switch to tenant 2 to verify the artifact wasn't modified
        await db_session.execute(text(f"SET app.current_tenant_id = '{tenant2.id}'"))
        
        result = await db_session.execute(
            select(Artifact).where(Artifact.id == artifact2.id)
        )
        artifact = result.scalar_one()
        
        assert artifact.name != "Hacked!", "Artifact from other tenant should not be modifiable"
        assert artifact.name == "Tenant 2 Artifact", "Original name should be preserved"
    
    async def test_rls_prevents_delete_of_other_tenant_data(self, db_session: AsyncSession, test_tenants, test_artifacts):
        """Test that RLS prevents deleting artifacts from other tenants."""
        tenant1, tenant2 = test_tenants
        artifact1, artifact2 = test_artifacts
        
        # Set tenant context for tenant 1
        await db_session.execute(text(f"SET app.current_tenant_id = '{tenant1.id}'"))
        
        # Try to delete tenant 2's artifact (should not work)
        await db_session.execute(
            text("DELETE FROM artifacts WHERE id = :artifact_id"),
            {"artifact_id": artifact2.id}
        )
        
        # Switch to tenant 2 to verify the artifact still exists
        await db_session.execute(text(f"SET app.current_tenant_id = '{tenant2.id}'"))
        
        result = await db_session.execute(
            select(Artifact).where(Artifact.id == artifact2.id)
        )
        artifact = result.scalar_one_or_none()
        
        assert artifact is not None, "Artifact from other tenant should not be deletable"
        assert artifact.id == artifact2.id, "Artifact should still exist"


class TestRLSPerformance:
    """Test RLS performance and ensure policies don't cause significant overhead."""
    
    async def test_rls_query_performance(self, db_session: AsyncSession, test_tenants):
        """Test that RLS policies don't cause significant query performance degradation."""
        tenant1, tenant2 = test_tenants
        
        # Create multiple artifacts for performance testing
        artifacts = []
        for i in range(100):
            artifact = Artifact(
                tenant_id=tenant1.id if i % 2 == 0 else tenant2.id,
                name=f"Performance Test Artifact {i}",
                description=f"Artifact {i} for performance testing",
                tags=[f"perf{i}", "test"],
                artifact_metadata={"index": i, "test": True},
                created_by=None,
                is_active=True
            )
            artifacts.append(artifact)
        
        db_session.add_all(artifacts)
        await db_session.flush()
        
        # Set tenant context
        await db_session.execute(text(f"SET app.current_tenant_id = '{tenant1.id}'"))
        
        # Measure query performance (basic timing)
        import time
        start_time = time.time()
        
        result = await db_session.execute(select(Artifact))
        tenant_artifacts = result.scalars().all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Should only return tenant 1's artifacts (50 out of 100)
        assert len(tenant_artifacts) == 50, "Should return exactly 50 artifacts for tenant 1"
        
        # Query should complete reasonably quickly (less than 1 second for 100 records)
        assert query_time < 1.0, f"Query took {query_time:.3f}s, should be under 1s"
        
        # Verify all returned artifacts belong to tenant 1
        for artifact in tenant_artifacts:
            assert artifact.tenant_id == tenant1.id, "All artifacts should belong to tenant 1"


@pytest.mark.integration
class TestRLSIntegration:
    """Integration tests for RLS with application-level security."""
    
    async def test_rls_with_application_auth(self, db_session: AsyncSession, test_tenants, test_users, test_artifacts):
        """Test that RLS works correctly with application-level authentication."""
        tenant1, tenant2 = test_tenants
        user1, user2 = test_users
        artifact1, artifact2 = test_artifacts
        
        # Simulate application setting tenant context based on user's membership
        # This would normally be done by the authentication middleware
        
        # User 1 should only see tenant 1's artifacts
        await db_session.execute(text(f"SET app.current_tenant_id = '{tenant1.id}'"))
        
        result = await db_session.execute(select(Artifact))
        user1_artifacts = result.scalars().all()
        
        assert len(user1_artifacts) == 1
        assert user1_artifacts[0].tenant_id == tenant1.id
        
        # User 2 should only see tenant 2's artifacts
        await db_session.execute(text(f"SET app.current_tenant_id = '{tenant2.id}'"))
        
        result = await db_session.execute(select(Artifact))
        user2_artifacts = result.scalars().all()
        
        assert len(user2_artifacts) == 1
        assert user2_artifacts[0].tenant_id == tenant2.id
    
    async def test_rls_regression_protection(self, db_session: AsyncSession):
        """Test that RLS policies are properly configured and haven't regressed."""
        # This test ensures that the RLS configuration hasn't been accidentally
        # modified or disabled, which could lead to data leaks
        
        # Check that RLS is enabled
        result = await db_session.execute(text("""
            SELECT schemaname, tablename, rowsecurity
            FROM pg_tables 
            WHERE tablename = 'artifacts' AND rowsecurity = true
        """))
        
        rls_enabled = result.fetchone()
        assert rls_enabled is not None, "RLS must be enabled on artifacts table"
        
        # Check that the tenant isolation policy exists and is active
        result = await db_session.execute(text("""
            SELECT policyname, permissive, roles, cmd, qual
            FROM pg_policies 
            WHERE tablename = 'artifacts' 
            AND policyname = 'tenant_isolation'
        """))
        
        policy = result.fetchone()
        assert policy is not None, "Tenant isolation policy must exist"
        assert policy.permissive == 'PERMISSIVE', "Policy should be permissive"
        assert 'authenticated_users' in policy.roles, "Policy should apply to authenticated_users role"
        
        # Verify the policy condition includes tenant_id check
        assert 'tenant_id' in policy.qual, "Policy should check tenant_id"
        assert 'current_setting' in policy.qual, "Policy should use current_setting for tenant context"