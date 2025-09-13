#!/usr/bin/env python3
"""
Database reset utility script for Ghostworks SaaS platform.
Provides clean demo environment by resetting database and reseeding demo data.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from config import get_settings
from database import get_database_session, get_database_engine
from models import Base
from seed_demo_data import seed_demo_data

logger = structlog.get_logger(__name__)


async def confirm_reset() -> bool:
    """
    Ask user for confirmation before resetting the database.
    
    Returns:
        True if user confirms, False otherwise
    """
    print("\n" + "="*60)
    print("DATABASE RESET WARNING")
    print("="*60)
    print("This operation will:")
    print("  1. DROP all existing tables and data")
    print("  2. Recreate the database schema")
    print("  3. Seed fresh demo data")
    print("\nALL EXISTING DATA WILL BE PERMANENTLY LOST!")
    print("="*60)
    
    while True:
        response = input("\nAre you sure you want to continue? (yes/no): ").strip().lower()
        
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'")


async def drop_all_tables():
    """Drop all tables in the database."""
    logger.info("Dropping all database tables...")
    
    engine = get_database_engine()
    
    async with engine.begin() as conn:
        # Drop all tables using SQLAlchemy metadata
        await conn.run_sync(Base.metadata.drop_all)
        
        # Also drop any remaining tables that might not be in our models
        # This handles cases where there might be leftover tables from migrations
        await conn.execute(text("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                -- Drop all tables in the public schema
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
                
                -- Drop all sequences
                FOR r IN (SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public') LOOP
                    EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
                END LOOP;
                
                -- Drop all views
                FOR r IN (SELECT viewname FROM pg_views WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP VIEW IF EXISTS ' || quote_ident(r.viewname) || ' CASCADE';
                END LOOP;
            END $$;
        """))
    
    logger.info("All database tables dropped successfully")


async def create_fresh_schema():
    """Create fresh database schema."""
    logger.info("Creating fresh database schema...")
    
    engine = get_database_engine()
    
    async with engine.begin() as conn:
        # Create all tables from our models
        await conn.run_sync(Base.metadata.create_all)
        
        # Enable required PostgreSQL extensions
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\""))
        
        # Set up Row-Level Security policies
        await conn.execute(text("""
            -- Enable RLS on artifacts table
            ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
            
            -- Create RLS policy for tenant isolation
            DROP POLICY IF EXISTS tenant_isolation ON artifacts;
            CREATE POLICY tenant_isolation ON artifacts
                FOR ALL TO public
                USING (tenant_id = COALESCE(current_setting('app.current_tenant_id', true)::uuid, tenant_id));
        """))
    
    logger.info("Fresh database schema created successfully")


async def run_alembic_stamp():
    """Stamp the database with the current Alembic revision."""
    import subprocess
    
    try:
        logger.info("Stamping database with current Alembic revision...")
        
        # Get the current head revision
        result = subprocess.run(
            ["alembic", "current"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # If no current revision, stamp with head
            logger.info("No current revision found, stamping with head...")
            result = subprocess.run(
                ["alembic", "stamp", "head"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("Database stamped with Alembic head revision")
            else:
                logger.warning(f"Failed to stamp database: {result.stderr}")
        else:
            logger.info("Database already has Alembic revision")
            
    except Exception as e:
        logger.warning(f"Failed to run Alembic stamp: {e}")


async def verify_reset():
    """Verify that the database reset was successful."""
    logger.info("Verifying database reset...")
    
    try:
        async with get_database_session() as session:
            # Check that we can connect and query
            result = await session.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            
            if test_value == 1:
                logger.info("Database connectivity verified")
            else:
                raise RuntimeError("Database connectivity test failed")
                
            # Check that tables exist
            result = await session.execute(text("""
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """))
            table_count = result.scalar()
            
            if table_count >= 4:  # tenants, users, workspace_memberships, artifacts
                logger.info(f"Database schema verified ({table_count} tables found)")
            else:
                raise RuntimeError(f"Expected at least 4 tables, found {table_count}")
                
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        raise


async def reset_demo_environment(skip_confirmation: bool = False):
    """
    Reset the demo environment with fresh data.
    
    Args:
        skip_confirmation: If True, skip user confirmation prompt
    """
    if not skip_confirmation:
        if not await confirm_reset():
            print("Database reset cancelled.")
            return
    
    logger.info("Starting database reset...")
    
    try:
        # Step 1: Drop all existing tables
        await drop_all_tables()
        
        # Step 2: Create fresh schema
        await create_fresh_schema()
        
        # Step 3: Stamp with Alembic revision
        await run_alembic_stamp()
        
        # Step 4: Verify the reset
        await verify_reset()
        
        # Step 5: Seed demo data
        await seed_demo_data()
        
        logger.info("Database reset completed successfully!")
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reset demo environment database")
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--seed-only", 
        action="store_true", 
        help="Only seed demo data without resetting database"
    )
    
    args = parser.parse_args()
    
    try:
        if args.seed_only:
            print("Seeding demo data only...")
            await seed_demo_data()
        else:
            await reset_demo_environment(skip_confirmation=args.force)
        
        print("\n" + "="*60)
        print("DEMO ENVIRONMENT READY!")
        print("="*60)
        print("You can now:")
        print("  1. Start the API server: uvicorn main:app --reload")
        print("  2. Access the web application at http://localhost:3000")
        print("  3. Login with any of the demo accounts:")
        print("     - owner@acme.com / SecurePass123!")
        print("     - admin@umbrella.com / SecurePass123!")
        print("     - member@acme.com / SecurePass123!")
        print("="*60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())