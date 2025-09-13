---
inclusion: fileMatch
fileMatchPattern: "docker-compose*|Dockerfile*|.github/**/*|infra/**/*|Makefile"
---

# Deployment Workflow and CI/CD Guidelines

This document outlines the deployment strategies, Docker containerization standards, and CI/CD pipeline requirements for the Ghostworks SaaS platform.

## Environment Strategy

### Environment Parity (12-Factor)
All environments (development, staging, production) must maintain parity in:
- **Dependencies**: Same versions of all services and libraries
- **Configuration**: Environment-specific config via environment variables only
- **Services**: Identical backing services (PostgreSQL, Redis, etc.)
- **Build Process**: Same Docker images across all environments

### Environment Configuration
```yaml
# Development Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://dev:dev@localhost:5432/ghostworks_dev
REDIS_URL=redis://localhost:6379/0

# Staging Environment  
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://staging:${DB_PASSWORD}@db-staging:5432/ghostworks_staging
REDIS_URL=redis://redis-staging:6379/0

# Production Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://prod:${DB_PASSWORD}@db-prod:5432/ghostworks_prod
REDIS_URL=redis://redis-prod:6379/0
```

## Docker Containerization Standards

### Multi-Stage Dockerfile Pattern
```dockerfile
# Example: FastAPI Service Dockerfile
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production
COPY . .
RUN useradd --create-home --shell /bin/bash app
USER app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Container Security Standards
```dockerfile
# Security best practices
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set secure file permissions
COPY --chown=appuser:appgroup . /app
WORKDIR /app

# Use non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Security labels
LABEL security.scan="enabled" \
      security.policy="restricted"
```

### Image Optimization
- Use multi-stage builds to minimize image size
- Leverage Docker layer caching effectively
- Use .dockerignore to exclude unnecessary files
- Pin base image versions for reproducibility
- Scan images for vulnerabilities in CI pipeline

## Docker Compose Orchestration

### Service Definition Standards
```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
      target: ${BUILD_TARGET:-development}
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=${NODE_ENV:-development}
      - NEXT_PUBLIC_API_URL=${API_URL:-http://localhost:8000}
    volumes:
      - ./apps/web:/app
      - /app/node_modules
    depends_on:
      api:
        condition: service_healthy
    restart: unless-stopped
    
  api:
    build:
      context: ./services/api
      dockerfile: Dockerfile
      target: ${BUILD_TARGET:-development}
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - ./services/api:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=${POSTGRES_DB:-ghostworks}
      - POSTGRES_USER=${POSTGRES_USER:-postgres}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: ghostworks-network
```

### Environment-Specific Overrides
```yaml
# docker-compose.override.yml (development)
version: '3.8'

services:
  web:
    volumes:
      - ./apps/web:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - CHOKIDAR_USEPOLLING=true

  api:
    volumes:
      - ./services/api:/app
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG

# docker-compose.prod.yml (production)
version: '3.8'

services:
  web:
    build:
      target: production
    volumes: []
    
  api:
    build:
      target: production
    volumes: []
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infra/docker/nginx/conf.d:/etc/nginx/conf.d
      - ./infra/docker/nginx/ssl:/etc/nginx/ssl
    depends_on:
      - web
      - api
```

## CI/CD Pipeline Architecture

### GitHub Actions Workflow Structure
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          
      - name: Install dependencies
        run: |
          pip install -r services/api/requirements.txt
          pip install -r services/api/requirements-dev.txt
          npm ci
          
      - name: Run linting
        run: |
          ruff check services/api/
          npm run lint
          
      - name: Run unit tests
        run: |
          pytest services/api/tests/unit/ --cov=services/api --cov-report=xml
          npm run test:unit
          
      - name: Run integration tests
        run: |
          pytest services/api/tests/integration/
          
      - name: Run E2E tests
        run: |
          npm run test:e2e
          
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### Security Scanning Integration
```yaml
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
          
      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
          
      - name: Run OWASP ZAP Baseline Scan
        uses: zaproxy/action-baseline@v0.7.0
        with:
          target: 'http://localhost:8000'
          rules_file_name: '.zap/rules.tsv'
```

### Build and Deploy Pipeline
```yaml
  build:
    name: Build and Push Images
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{branch}}-
            
      - name: Build and push API image
        uses: docker/build-push-action@v5
        with:
          context: ./services/api
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          
  deploy:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    environment: staging
    
    steps:
      - name: Deploy to staging
        run: |
          # Deployment commands
          echo "Deploying to staging environment"
```

## Deployment Strategies

### Rolling Deployment
```yaml
# docker-compose.prod.yml with rolling updates
version: '3.8'

services:
  api:
    image: ${API_IMAGE}:${VERSION}
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
        order: start-first
      rollback_config:
        parallelism: 1
        delay: 5s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

### Blue-Green Deployment
```bash
#!/bin/bash
# deploy.sh - Blue-green deployment script

set -e

CURRENT_ENV=$(docker-compose ps --services | grep -E "(blue|green)" | head -1)
NEW_ENV=$([ "$CURRENT_ENV" = "blue" ] && echo "green" || echo "blue")

echo "Current environment: $CURRENT_ENV"
echo "Deploying to: $NEW_ENV"

# Deploy to new environment
docker-compose -f docker-compose.yml -f docker-compose.$NEW_ENV.yml up -d

# Health check
echo "Performing health checks..."
for i in {1..30}; do
  if curl -f http://localhost:8001/health; then
    echo "Health check passed"
    break
  fi
  sleep 10
done

# Switch traffic
echo "Switching traffic to $NEW_ENV"
docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up -d nginx

# Stop old environment
echo "Stopping $CURRENT_ENV environment"
docker-compose -f docker-compose.yml -f docker-compose.$CURRENT_ENV.yml down
```

## Database Migration Strategy

### Alembic Migration Workflow
```python
# Migration script template
"""Add artifact tags support

Revision ID: 001_add_artifact_tags
Revises: 000_initial_schema
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_add_artifact_tags'
down_revision = '000_initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add tags column to artifacts table."""
    op.add_column('artifacts', 
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True)
    )
    
    # Create index for tag searches
    op.create_index('ix_artifacts_tags', 'artifacts', ['tags'], 
                   postgresql_using='gin')

def downgrade() -> None:
    """Remove tags column from artifacts table."""
    op.drop_index('ix_artifacts_tags', table_name='artifacts')
    op.drop_column('artifacts', 'tags')
```

### Migration Deployment Process
```bash
#!/bin/bash
# migrate.sh - Database migration script

set -e

echo "Starting database migration..."

# Backup database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migrations
alembic upgrade head

# Verify migration
python -c "
import asyncio
from app.database import engine
from app.models import Base

async def verify():
    async with engine.begin() as conn:
        # Verify schema changes
        result = await conn.execute('SELECT version_num FROM alembic_version')
        print(f'Current migration version: {result.scalar()}')

asyncio.run(verify())
"

echo "Migration completed successfully"
```

## Monitoring and Observability in Deployment

### Health Check Endpoints
```python
# Health check implementation
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
import redis

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with dependency verification."""
    checks = {}
    
    # Database check
    try:
        await db.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
    
    # Redis check
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    
    # Overall status
    overall_status = "healthy" if all(
        status == "healthy" for status in checks.values()
    ) else "unhealthy"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow()
    }
```

### Deployment Metrics
```python
# Deployment metrics collection
from prometheus_client import Counter, Histogram, Gauge

deployment_counter = Counter(
    'deployments_total', 
    'Total number of deployments',
    ['service', 'environment', 'status']
)

deployment_duration = Histogram(
    'deployment_duration_seconds',
    'Time spent on deployments',
    ['service', 'environment']
)

service_version = Gauge(
    'service_version_info',
    'Service version information',
    ['service', 'version', 'commit_sha']
)
```

## Rollback Procedures

### Automated Rollback Triggers
```yaml
# Rollback conditions in CI/CD
rollback_conditions:
  - health_check_failures: 3
  - error_rate_threshold: 5%
  - response_time_threshold: 1000ms
  - manual_trigger: true
```

### Rollback Script
```bash
#!/bin/bash
# rollback.sh - Automated rollback script

set -e

PREVIOUS_VERSION=$1
SERVICE=$2

if [ -z "$PREVIOUS_VERSION" ] || [ -z "$SERVICE" ]; then
    echo "Usage: $0 <previous_version> <service>"
    exit 1
fi

echo "Rolling back $SERVICE to version $PREVIOUS_VERSION"

# Stop current version
docker-compose down $SERVICE

# Deploy previous version
export VERSION=$PREVIOUS_VERSION
docker-compose up -d $SERVICE

# Wait for health check
echo "Waiting for service to be healthy..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health; then
        echo "Rollback successful"
        exit 0
    fi
    sleep 10
done

echo "Rollback failed - service not healthy"
exit 1
```

## Environment-Specific Configurations

### Development Environment
- Hot reloading enabled
- Debug logging
- Local file volumes for development
- Relaxed security settings for testing

### Staging Environment
- Production-like configuration
- Automated testing deployment
- Performance monitoring
- Security scanning

### Production Environment
- Optimized Docker images
- Strict security policies
- Comprehensive monitoring
- Automated backup procedures
- Load balancing and scaling

## Secrets Management

### Environment Variables
```bash
# .env.example
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key-here
OPENTELEMETRY_ENDPOINT=http://localhost:4317
```

### Docker Secrets (Production)
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    secrets:
      - db_password
      - jwt_secret
    environment:
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password
      - JWT_SECRET_KEY_FILE=/run/secrets/jwt_secret

secrets:
  db_password:
    external: true
  jwt_secret:
    external: true
```

This deployment workflow ensures consistent, secure, and reliable deployments across all environments while maintaining the flexibility needed for development and the robustness required for production.