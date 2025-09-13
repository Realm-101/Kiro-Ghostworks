#!/usr/bin/env python3
"""
Demo data seeding script for Ghostworks SaaS platform.
Creates realistic demo data including tenants, users, and artifacts.

SECURITY NOTE: This script only runs in development environments.
Demo credentials are automatically disabled in production.
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import random

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from config import get_settings
from database import get_database_session
from models.tenant import Tenant
from models.user import User
from models.workspace_membership import WorkspaceMembership, WorkspaceRole
from models.artifact import Artifact
from auth import hash_password

logger = structlog.get_logger(__name__)

# Demo data configuration
DEMO_TENANTS = [
    {
        "name": "Acme Corp",
        "slug": "acme-corp",
        "description": "A leading technology company specializing in innovative solutions for modern businesses.",
        "settings": {
            "theme": "corporate",
            "features": ["analytics", "integrations", "advanced_search"],
            "plan": "enterprise",
            "max_users": 100,
            "storage_limit_gb": 1000
        }
    },
    {
        "name": "Umbrella Inc",
        "slug": "umbrella-inc",
        "description": "A multinational corporation focused on biotechnology and pharmaceutical research.",
        "settings": {
            "theme": "medical",
            "features": ["compliance", "audit_trail", "data_retention"],
            "plan": "professional",
            "max_users": 50,
            "storage_limit_gb": 500
        }
    }
]

DEMO_USERS = [
    {
        "email": "owner@acme.com",
        "password": "demo123",
        "first_name": "Alice",
        "last_name": "Johnson",
        "is_verified": True,
        "tenant_slug": "acme-corp",
        "role": WorkspaceRole.OWNER
    },
    {
        "email": "admin@umbrella.com",
        "password": "demo123",
        "first_name": "Bob",
        "last_name": "Smith",
        "is_verified": True,
        "tenant_slug": "umbrella-inc",
        "role": WorkspaceRole.ADMIN
    },
    {
        "email": "member@acme.com",
        "password": "demo123",
        "first_name": "Carol",
        "last_name": "Davis",
        "is_verified": True,
        "tenant_slug": "acme-corp",
        "role": WorkspaceRole.MEMBER
    },
    {
        "email": "researcher@umbrella.com",
        "password": "demo123",
        "first_name": "David",
        "last_name": "Wilson",
        "is_verified": True,
        "tenant_slug": "umbrella-inc",
        "role": WorkspaceRole.MEMBER
    },
    {
        "email": "manager@acme.com",
        "password": "demo123",
        "first_name": "Eva",
        "last_name": "Martinez",
        "is_verified": True,
        "tenant_slug": "acme-corp",
        "role": WorkspaceRole.ADMIN
    }
]

# Artifact templates for realistic demo data
ACME_ARTIFACTS = [
    {
        "name": "Customer Analytics Dashboard",
        "description": "Interactive dashboard showing customer behavior patterns, conversion rates, and engagement metrics across all digital touchpoints.",
        "tags": ["analytics", "dashboard", "customer", "metrics"],
        "metadata": {
            "type": "dashboard",
            "technology": "React",
            "status": "production",
            "last_updated": "2024-01-10",
            "owner": "Analytics Team",
            "url": "https://analytics.acme.com/dashboard",
            "performance_score": 95
        }
    },
    {
        "name": "API Gateway Configuration",
        "description": "Centralized API gateway configuration managing authentication, rate limiting, and routing for all microservices.",
        "tags": ["api", "gateway", "configuration", "microservices"],
        "metadata": {
            "type": "configuration",
            "technology": "Kong",
            "status": "production",
            "version": "2.1.0",
            "endpoints": 47,
            "rate_limit": "1000/min",
            "auth_methods": ["JWT", "OAuth2", "API Key"]
        }
    },
    {
        "name": "Mobile App User Interface",
        "description": "Modern, responsive user interface components for the Acme mobile application with accessibility features.",
        "tags": ["mobile", "ui", "components", "accessibility"],
        "metadata": {
            "type": "ui_components",
            "technology": "React Native",
            "status": "development",
            "accessibility_score": "AA",
            "components_count": 23,
            "supported_platforms": ["iOS", "Android"],
            "design_system": "Acme Design System v3"
        }
    },
    {
        "name": "Database Migration Scripts",
        "description": "Collection of database migration scripts for transitioning from legacy system to new cloud-native architecture.",
        "tags": ["database", "migration", "scripts", "cloud"],
        "metadata": {
            "type": "scripts",
            "technology": "PostgreSQL",
            "status": "testing",
            "migration_count": 15,
            "data_volume": "2.3TB",
            "estimated_downtime": "4 hours",
            "rollback_strategy": "automated"
        }
    },
    {
        "name": "Security Audit Report",
        "description": "Comprehensive security audit report covering penetration testing, vulnerability assessment, and compliance review.",
        "tags": ["security", "audit", "compliance", "report"],
        "metadata": {
            "type": "document",
            "format": "PDF",
            "status": "completed",
            "audit_date": "2024-01-05",
            "vulnerabilities_found": 3,
            "compliance_frameworks": ["SOC2", "ISO27001", "GDPR"],
            "risk_level": "low"
        }
    },
    {
        "name": "Machine Learning Model",
        "description": "Predictive model for customer churn analysis using advanced machine learning algorithms and feature engineering.",
        "tags": ["ml", "model", "prediction", "churn"],
        "metadata": {
            "type": "ml_model",
            "technology": "Python",
            "status": "production",
            "accuracy": 0.94,
            "model_type": "Random Forest",
            "training_data_size": "1M records",
            "last_retrained": "2024-01-08"
        }
    },
    {
        "name": "CI/CD Pipeline Configuration",
        "description": "Automated continuous integration and deployment pipeline configuration with testing, security scanning, and deployment stages.",
        "tags": ["cicd", "pipeline", "automation", "deployment"],
        "metadata": {
            "type": "pipeline",
            "technology": "GitHub Actions",
            "status": "production",
            "stages": ["test", "security-scan", "build", "deploy"],
            "deployment_frequency": "daily",
            "success_rate": 0.98,
            "average_duration": "12 minutes"
        }
    }
]

UMBRELLA_ARTIFACTS = [
    {
        "name": "Clinical Trial Data Management",
        "description": "Comprehensive system for managing clinical trial data with regulatory compliance and audit trail capabilities.",
        "tags": ["clinical", "trial", "data", "compliance"],
        "metadata": {
            "type": "system",
            "technology": "Java",
            "status": "production",
            "compliance": ["FDA", "EMA", "GCP"],
            "trial_count": 23,
            "patient_records": 15000,
            "data_integrity_score": 99.8
        }
    },
    {
        "name": "Drug Discovery Algorithm",
        "description": "Advanced algorithm for identifying potential drug compounds using molecular modeling and AI-driven analysis.",
        "tags": ["drug", "discovery", "algorithm", "ai"],
        "metadata": {
            "type": "algorithm",
            "technology": "Python",
            "status": "research",
            "compounds_analyzed": 50000,
            "success_rate": 0.12,
            "patent_applications": 3,
            "research_phase": "Phase II"
        }
    },
    {
        "name": "Laboratory Information System",
        "description": "Integrated laboratory information management system for tracking samples, results, and quality control processes.",
        "tags": ["laboratory", "lims", "samples", "quality"],
        "metadata": {
            "type": "system",
            "technology": ".NET",
            "status": "production",
            "sample_capacity": "10000/day",
            "instruments_connected": 45,
            "quality_metrics": "Six Sigma",
            "uptime": 99.95
        }
    },
    {
        "name": "Regulatory Submission Portal",
        "description": "Secure portal for submitting regulatory documents and tracking approval status with health authorities.",
        "tags": ["regulatory", "submission", "portal", "approval"],
        "metadata": {
            "type": "portal",
            "technology": "Angular",
            "status": "production",
            "submissions_count": 127,
            "approval_rate": 0.89,
            "average_review_time": "45 days",
            "supported_regions": ["US", "EU", "APAC"]
        }
    },
    {
        "name": "Biomarker Analysis Pipeline",
        "description": "Automated pipeline for processing and analyzing biomarker data from genomic sequencing and proteomics studies.",
        "tags": ["biomarker", "analysis", "pipeline", "genomics"],
        "metadata": {
            "type": "pipeline",
            "technology": "R",
            "status": "production",
            "samples_processed": 8500,
            "analysis_types": ["RNA-seq", "Proteomics", "Metabolomics"],
            "processing_time": "2 hours/sample",
            "accuracy": 0.96
        }
    },
    {
        "name": "Patient Safety Database",
        "description": "Centralized database for tracking adverse events, safety signals, and pharmacovigilance activities.",
        "tags": ["safety", "database", "adverse", "pharmacovigilance"],
        "metadata": {
            "type": "database",
            "technology": "Oracle",
            "status": "production",
            "adverse_events": 12000,
            "safety_signals": 45,
            "reporting_compliance": "100%",
            "data_retention": "25 years"
        }
    }
]


async def create_demo_tenants(session: AsyncSession) -> Dict[str, Tenant]:
    """Create demo tenant workspaces."""
    logger.info("Creating demo tenants...")
    
    tenants = {}
    
    for tenant_data in DEMO_TENANTS:
        # Check if tenant already exists
        result = await session.execute(
            select(Tenant).where(Tenant.slug == tenant_data["slug"])
        )
        existing_tenant = result.scalar_one_or_none()
        
        if existing_tenant:
            logger.info(f"Tenant {tenant_data['slug']} already exists, skipping...")
            tenants[tenant_data["slug"]] = existing_tenant
            continue
        
        tenant = Tenant(
            name=tenant_data["name"],
            slug=tenant_data["slug"],
            description=tenant_data["description"],
            settings=tenant_data["settings"],
            is_active=True
        )
        
        session.add(tenant)
        await session.flush()  # Get the ID
        
        tenants[tenant_data["slug"]] = tenant
        
        logger.info(f"Created tenant: {tenant.name} ({tenant.slug})")
    
    return tenants


async def create_demo_users(session: AsyncSession, tenants: Dict[str, Tenant]) -> Dict[str, User]:
    """Create demo users and workspace memberships."""
    logger.info("Creating demo users...")
    
    users = {}
    
    for user_data in DEMO_USERS:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == user_data["email"])
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.info(f"User {user_data['email']} already exists, skipping...")
            users[user_data["email"]] = existing_user
            continue
        
        # Create user
        user = User(
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            is_verified=user_data["is_verified"],
            is_active=True
        )
        
        session.add(user)
        await session.flush()  # Get the ID
        
        # Create workspace membership
        tenant = tenants[user_data["tenant_slug"]]
        membership = WorkspaceMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role=user_data["role"],
            is_active=True
        )
        
        session.add(membership)
        
        users[user_data["email"]] = user
        
        logger.info(f"Created user: {user.email} ({user_data['role'].value} in {tenant.name})")
    
    return users


async def create_demo_artifacts(session: AsyncSession, tenants: Dict[str, Tenant], users: Dict[str, User]) -> None:
    """Create demo artifacts for each tenant."""
    logger.info("Creating demo artifacts...")
    
    # Create Acme Corp artifacts
    acme_tenant = tenants["acme-corp"]
    acme_users = [users["owner@acme.com"], users["member@acme.com"], users["manager@acme.com"]]
    
    for i, artifact_data in enumerate(ACME_ARTIFACTS):
        # Vary creation dates over the past 30 days
        created_at = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        created_by = random.choice(acme_users)
        
        artifact = Artifact(
            tenant_id=acme_tenant.id,
            name=artifact_data["name"],
            description=artifact_data["description"],
            tags=artifact_data["tags"],
            artifact_metadata=artifact_data["metadata"],
            created_by=created_by.id,
            is_active=True,
            created_at=created_at,
            updated_at=created_at + timedelta(hours=random.randint(1, 48))
        )
        
        session.add(artifact)
        
        logger.info(f"Created Acme artifact: {artifact.name}")
    
    # Create Umbrella Inc artifacts
    umbrella_tenant = tenants["umbrella-inc"]
    umbrella_users = [users["admin@umbrella.com"], users["researcher@umbrella.com"]]
    
    for i, artifact_data in enumerate(UMBRELLA_ARTIFACTS):
        # Vary creation dates over the past 45 days
        created_at = datetime.utcnow() - timedelta(days=random.randint(1, 45))
        created_by = random.choice(umbrella_users)
        
        artifact = Artifact(
            tenant_id=umbrella_tenant.id,
            name=artifact_data["name"],
            description=artifact_data["description"],
            tags=artifact_data["tags"],
            artifact_metadata=artifact_data["metadata"],
            created_by=created_by.id,
            is_active=True,
            created_at=created_at,
            updated_at=created_at + timedelta(hours=random.randint(1, 72))
        )
        
        session.add(artifact)
        
        logger.info(f"Created Umbrella artifact: {artifact.name}")


async def verify_demo_data(session: AsyncSession) -> None:
    """Verify that demo data was created successfully."""
    logger.info("Verifying demo data...")
    
    # Count tenants
    result = await session.execute(select(Tenant))
    tenant_count = len(result.scalars().all())
    
    # Count users
    result = await session.execute(select(User))
    user_count = len(result.scalars().all())
    
    # Count workspace memberships
    result = await session.execute(select(WorkspaceMembership))
    membership_count = len(result.scalars().all())
    
    # Count artifacts
    result = await session.execute(select(Artifact))
    artifact_count = len(result.scalars().all())
    
    # Count artifacts by tenant
    acme_result = await session.execute(
        select(Artifact).join(Tenant).where(Tenant.slug == "acme-corp")
    )
    acme_artifacts = len(acme_result.scalars().all())
    
    umbrella_result = await session.execute(
        select(Artifact).join(Tenant).where(Tenant.slug == "umbrella-inc")
    )
    umbrella_artifacts = len(umbrella_result.scalars().all())
    
    logger.info(f"Demo data verification complete:")
    logger.info(f"  - Tenants: {tenant_count}")
    logger.info(f"  - Users: {user_count}")
    logger.info(f"  - Workspace memberships: {membership_count}")
    logger.info(f"  - Total artifacts: {artifact_count}")
    logger.info(f"  - Acme Corp artifacts: {acme_artifacts}")
    logger.info(f"  - Umbrella Inc artifacts: {umbrella_artifacts}")


async def seed_demo_data():
    """Main function to seed demo data."""
    logger.info("Starting demo data seeding...")
    
    try:
        async with get_database_session() as session:
            # Create demo data in order
            tenants = await create_demo_tenants(session)
            users = await create_demo_users(session, tenants)
            await create_demo_artifacts(session, tenants, users)
            
            # Commit all changes
            await session.commit()
            
            # Verify the data
            await verify_demo_data(session)
            
            logger.info("Demo data seeding completed successfully!")
            
    except Exception as e:
        logger.error(f"Demo data seeding failed: {e}")
        raise


async def main():
    """Main entry point."""
    # Security check: Only allow demo data in development environments
    environment = os.getenv("ENVIRONMENT", "development")
    enable_demo_data = os.getenv("ENABLE_DEMO_DATA", "false").lower() == "true"
    
    if environment == "production":
        print("❌ SECURITY: Demo data seeding is DISABLED in production environments")
        print("   This is a security feature to prevent demo credentials in production.")
        sys.exit(1)
    
    if not enable_demo_data and environment != "development":
        print("❌ SECURITY: Demo data seeding is DISABLED")
        print("   Set ENABLE_DEMO_DATA=true to enable (development only)")
        sys.exit(1)
    
    print("⚠️  SECURITY WARNING: Creating demo credentials for DEVELOPMENT ONLY")
    print("   These credentials will NOT work in production environments")
    print()
    
    try:
        await seed_demo_data()
        
        print("\n" + "="*60)
        print("DEMO DATA SEEDING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n⚠️  SECURITY WARNING: DEMO CREDENTIALS CREATED")
        print("   These are for DEVELOPMENT/TESTING ONLY")
        print("   They are DISABLED in production environments")
        print("\nDemo Accounts Created:")
        print("  Acme Corp (acme-corp):")
        print("    - owner@acme.com (Owner) - Password: demo123")
        print("    - manager@acme.com (Admin) - Password: demo123")
        print("    - member@acme.com (Member) - Password: demo123")
        print("\n  Umbrella Inc (umbrella-inc):")
        print("    - admin@umbrella.com (Admin) - Password: demo123")
        print("    - researcher@umbrella.com (Member) - Password: demo123")
        print("\nDemo Data Summary:")
        print(f"  - 2 tenant workspaces created")
        print(f"  - 5 demo users created")
        print(f"  - {len(ACME_ARTIFACTS)} Acme Corp artifacts")
        print(f"  - {len(UMBRELLA_ARTIFACTS)} Umbrella Inc artifacts")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Demo data seeding failed: {e}")
        print(f"\nERROR: Demo data seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())