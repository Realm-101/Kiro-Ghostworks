#!/usr/bin/env python3
"""
RLS smoke test runner script.
Runs the Row-Level Security tests to verify tenant isolation.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the services/api directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api"))

import pytest


def main():
    """Run RLS smoke tests."""
    print("🔒 Running Row-Level Security (RLS) smoke tests...")
    print("   Verifying tenant isolation at database level")
    print()
    
    # Set test environment
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/ghostworks_test"
    )
    
    # Run the RLS tests
    test_file = Path(__file__).parent.parent / "tests" / "security" / "test_rls_smoke.py"
    
    exit_code = pytest.main([
        str(test_file),
        "-v",
        "--tb=short",
        "--no-header",
        "-x"  # Stop on first failure
    ])
    
    if exit_code == 0:
        print("\n✅ RLS smoke tests PASSED")
        print("   Tenant isolation is working correctly")
    else:
        print("\n❌ RLS smoke tests FAILED")
        print("   Tenant isolation may be compromised!")
        
    return exit_code


if __name__ == "__main__":
    sys.exit(main())