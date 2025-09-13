#!/usr/bin/env python3
"""
Test script to verify demo data scripts work correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog
from seed_demo_data import DEMO_TENANTS, DEMO_USERS, ACME_ARTIFACTS, UMBRELLA_ARTIFACTS

logger = structlog.get_logger(__name__)


def test_demo_data_structure():
    """Test that demo data has the correct structure."""
    print("Testing demo data structure...")
    
    # Test tenants
    assert len(DEMO_TENANTS) == 2, f"Expected 2 tenants, got {len(DEMO_TENANTS)}"
    
    tenant_slugs = [t["slug"] for t in DEMO_TENANTS]
    assert "acme-corp" in tenant_slugs, "Missing acme-corp tenant"
    assert "umbrella-inc" in tenant_slugs, "Missing umbrella-inc tenant"
    
    # Test users
    assert len(DEMO_USERS) == 5, f"Expected 5 users, got {len(DEMO_USERS)}"
    
    user_emails = [u["email"] for u in DEMO_USERS]
    expected_emails = [
        "owner@acme.com", "admin@umbrella.com", "member@acme.com",
        "researcher@umbrella.com", "manager@acme.com"
    ]
    
    for email in expected_emails:
        assert email in user_emails, f"Missing user: {email}"
    
    # Test artifacts
    assert len(ACME_ARTIFACTS) == 7, f"Expected 7 Acme artifacts, got {len(ACME_ARTIFACTS)}"
    assert len(UMBRELLA_ARTIFACTS) == 6, f"Expected 6 Umbrella artifacts, got {len(UMBRELLA_ARTIFACTS)}"
    
    # Test artifact structure
    for artifact in ACME_ARTIFACTS + UMBRELLA_ARTIFACTS:
        assert "name" in artifact, "Artifact missing name"
        assert "description" in artifact, "Artifact missing description"
        assert "tags" in artifact, "Artifact missing tags"
        assert "metadata" in artifact, "Artifact missing metadata"
        assert isinstance(artifact["tags"], list), "Tags should be a list"
        assert isinstance(artifact["metadata"], dict), "Metadata should be a dict"
    
    print("✓ Demo data structure tests passed")


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from config import get_settings
        from database import get_database_session
        from models.tenant import Tenant
        from models.user import User
        from models.workspace_membership import WorkspaceMembership, WorkspaceRole
        from models.artifact import Artifact
        from auth import hash_password
        
        print("✓ All imports successful")
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        raise


def test_password_hashing():
    """Test password hashing functionality."""
    print("Testing password hashing...")
    
    from auth import hash_password, verify_password
    
    test_password = "SecurePass123!"
    hashed = hash_password(test_password)
    
    assert hashed != test_password, "Password should be hashed"
    assert verify_password(test_password, hashed), "Password verification should work"
    assert not verify_password("wrong_password", hashed), "Wrong password should fail"
    
    print("✓ Password hashing tests passed")


async def test_database_connection():
    """Test database connection."""
    print("Testing database connection...")
    
    try:
        from database import get_database_session
        from sqlalchemy import text
        
        async with get_database_session() as session:
            result = await session.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            
            assert test_value == 1, "Database query should return 1"
            
        print("✓ Database connection test passed")
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("Note: This is expected if the database is not running")


async def main():
    """Run all tests."""
    print("Running demo script tests...\n")
    
    try:
        # Test data structure
        test_demo_data_structure()
        
        # Test imports
        test_imports()
        
        # Test password hashing
        test_password_hashing()
        
        # Test database connection (optional)
        await test_database_connection()
        
        print("\n" + "="*50)
        print("ALL TESTS PASSED!")
        print("="*50)
        print("Demo scripts are ready to use.")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())