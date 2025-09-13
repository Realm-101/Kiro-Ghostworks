#!/usr/bin/env python3
"""
Database initialization script for Ghostworks SaaS platform.
Creates the database and runs initial migrations.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from config import get_settings
from database import get_database_engine, create_database_tables
import structlog

logger = structlog.get_logger(__name__)


async def create_database_if_not_exists():
    """Create the database if it doesn't exist."""
    settings = get_settings()
    
    # Parse the database URL to get connection details
    db_url = str(settings.database_url)
    
    # Extract database name from URL
    # Format: postgresql+asyncpg://user:pass@host:port/dbname
    db_name = db_url.split("/")[-1]
    
    # Create connection URL without database name for initial connection
    base_url = db_url.rsplit("/", 1)[0]
    
    # Convert asyncpg URL to regular asyncpg format
    base_url = base_url.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        # Connect to postgres database to create our target database
        conn = await asyncpg.connect(f"{base_url}/postgres")
        
        # Check if database exists
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        
        if not result:
            logger.info(f"Creating database: {db_name}")
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            logger.info(f"Database {db_name} created successfully")
        else:
            logger.info(f"Database {db_name} already exists")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        raise


async def run_migrations():
    """Run Alembic migrations."""
    import subprocess
    
    try:
        logger.info("Running Alembic migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Migrations completed successfully")
            if result.stdout:
                logger.info(f"Migration output: {result.stdout}")
        else:
            logger.error(f"Migration failed: {result.stderr}")
            raise RuntimeError(f"Migration failed: {result.stderr}")
            
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        raise


async def verify_database_setup():
    """Verify that the database is set up correctly."""
    try:
        from database import check_database_health
        health = await check_database_health()
        
        if health.get("status") == "healthy":
            logger.info("Database setup verification successful")
            logger.info(f"Connection pool stats: {health.get('connection_pool', {})}")
        else:
            logger.error(f"Database setup verification failed: {health}")
            raise RuntimeError("Database verification failed")
            
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        raise


async def main():
    """Main initialization function."""
    logger.info("Starting database initialization...")
    
    try:
        # Step 1: Create database if it doesn't exist
        await create_database_if_not_exists()
        
        # Step 2: Run migrations
        await run_migrations()
        
        # Step 3: Verify setup
        await verify_database_setup()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())