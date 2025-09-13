#!/usr/bin/env python3
"""
Simple demo data seeding script that only adds data without resetting.
Useful for adding demo data to an existing database.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from seed_demo_data import seed_demo_data
import structlog

logger = structlog.get_logger(__name__)


async def main():
    """Main entry point for seeding only."""
    try:
        print("Seeding demo data to existing database...")
        await seed_demo_data()
        
        print("\n" + "="*50)
        print("DEMO DATA SEEDED SUCCESSFULLY!")
        print("="*50)
        print("Demo accounts are now available for testing.")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Demo data seeding failed: {e}")
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())