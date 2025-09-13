#!/usr/bin/env python3
"""
Validation script to check if demo data exists in the database.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
import structlog

from database import get_database_session
from models.tenant import Tenant
from models.user import User
from models.workspace_membership import WorkspaceMembership
from models.artifact import Artifact

logger = structlog.get_logger(__name__)


async def validate_demo_data():
    """Validate that demo data exists in the database."""
    print("Validating demo data in database...")
    
    try:
        async with get_database_session() as session:
            # Check tenants
            result = await session.execute(select(Tenant))
            tenants = result.scalars().all()
            
            print(f"\nTenants found: {len(tenants)}")
            for tenant in tenants:
                print(f"  - {tenant.name} ({tenant.slug})")
            
            # Check users
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            print(f"\nUsers found: {len(users)}")
            for user in users:
                print(f"  - {user.email} ({user.full_name})")
            
            # Check workspace memberships
            result = await session.execute(select(WorkspaceMembership))
            memberships = result.scalars().all()
            
            print(f"\nWorkspace memberships found: {len(memberships)}")
            
            # Check artifacts by tenant
            for tenant in tenants:
                result = await session.execute(
                    select(Artifact).where(Artifact.tenant_id == tenant.id)
                )
                artifacts = result.scalars().all()
                
                print(f"\n{tenant.name} artifacts: {len(artifacts)}")
                for artifact in artifacts[:3]:  # Show first 3
                    print(f"  - {artifact.name}")
                if len(artifacts) > 3:
                    print(f"  ... and {len(artifacts) - 3} more")
            
            # Summary
            total_artifacts = await session.execute(select(func.count(Artifact.id)))
            artifact_count = total_artifacts.scalar()
            
            print(f"\n" + "="*50)
            print("DEMO DATA SUMMARY")
            print("="*50)
            print(f"Tenants: {len(tenants)}")
            print(f"Users: {len(users)}")
            print(f"Memberships: {len(memberships)}")
            print(f"Total Artifacts: {artifact_count}")
            
            # Check if we have the expected demo data
            expected_tenants = ["acme-corp", "umbrella-inc"]
            expected_users = ["owner@acme.com", "admin@umbrella.com", "member@acme.com"]
            
            tenant_slugs = [t.slug for t in tenants]
            user_emails = [u.email for u in users]
            
            missing_tenants = [t for t in expected_tenants if t not in tenant_slugs]
            missing_users = [u for u in expected_users if u not in user_emails]
            
            if missing_tenants or missing_users:
                print(f"\nWARNING: Missing expected demo data")
                if missing_tenants:
                    print(f"Missing tenants: {missing_tenants}")
                if missing_users:
                    print(f"Missing users: {missing_users}")
                print("Run 'make seed-demo' to add demo data")
            else:
                print(f"\n✓ All expected demo data found!")
            
    except Exception as e:
        print(f"Error validating demo data: {e}")
        print("Make sure the database is running and accessible")
        sys.exit(1)


async def main():
    """Main entry point."""
    await validate_demo_data()


if __name__ == "__main__":
    asyncio.run(main())