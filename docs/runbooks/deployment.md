# Deployment Runbook

This runbook covers deployment procedures for the Ghostworks SaaS platform across different environments.

## 🎯 Overview

The Ghostworks platform uses Docker Compose for orchestration with environment-specific configurations. Deployments follow a blue-green strategy with automated rollback capabilities.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Application   │    │   Monitoring    │
│     (Nginx)     │────│    Services     │────│     Stack       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────┬─────┴─────┬─────────────────┐
         │                 │           │                 │
    ┌─────────┐    ┌──────────────┐   │    ┌─────────────────┐
    │Database │    │    Cache     │   │    │   Message Queue │
    │(Postgres)│    │   (Redis)    │   │    │    (Redis)      │
    └─────────┘    └──────────────┘   │    └─────────────────┘
```

## 🚀 Deployment Procedures

### Prerequisites

1. **System Requirements**
   - Docker 20.10+
   - Docker Compose 2.0+
   - 4GB+ RAM
   - 20GB+ disk space

2. **Access Requirements**
   - SSH access to deployment server
   - Docker registry credentials
   - Environment configuration files

3. **Pre-deployment Checklist**
   - [ ] All tests passing in CI/CD
   - [ ] Database migrations reviewed
   - [ ] Environment variables configured
   - [ ] Backup completed
   - [ ] Monitoring alerts configured

### Development Environment

```bash
# 1. Clone repository
git clone <repository-url>
cd ghostworks

# 2. Set up environment
cp .env.example .env
# Edit .env with development settings

# 3. Start services
docker-compose up -d

# 4. Initialize database
docker-compose exec api alembic upgrade head

# 5. Seed demo data
docker-compose exec api python scripts/seed_demo_data.py

# 6. Verify deployment
curl http://localhost:8000/api/v1/health
curl http://localhost:3000/api/health
```

### Staging Environment

```bash
# 1. Pull latest changes
git pull origin main

# 2. Build images
docker-compose -f docker-compose.yml -f docker-compose.staging.yml build

# 3. Run database migrations (if needed)
docker-compose exec api alembic upgrade head

# 4. Deploy services
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# 5. Run smoke tests
./scripts/smoke-tests.sh staging

# 6. Verify health
curl https://staging-api.ghostworks.dev/api/v1/health
```

### Production Environment

```bash
# 1. Create deployment tag
git tag -a v1.0.0 -m "Production release v1.0.0"
git push origin v1.0.0

# 2. Build production images
docker-compose -f docker-compose.prod.yml build

# 3. Pre-deployment backup
./scripts/backup-database.sh production

# 4. Deploy with zero downtime
./scripts/blue-green-deploy.sh v1.0.0

# 5. Run database migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# 6. Verify deployment
./scripts/health-check.sh production

# 7. Monitor for 15 minutes
./scripts/monitor-deployment.sh
```

## 🔄 Blue-Green Deployment

### Overview
Blue-green deployment ensures zero downtime by maintaining two identical production environments.

### Procedure

1. **Prepare Green Environment**
   ```bash
   # Deploy to green environment
   docker-compose -f docker-compose.prod.yml -f docker-compose.green.yml up -d
   
   # Run health checks
   ./scripts/health-check.sh green
   
   # Run integration tests
   ./scripts/integration-tests.sh green
   ```

2. **Switch Traffic**
   ```bash
   # Update load balancer configuration
   ./scripts/switch-traffic.sh green
   
   # Verify traffic routing
   ./scripts/verify-traffic.sh
   ```

3. **Monitor and Rollback (if needed)**
   ```bash
   # Monitor error rates and performance
   ./scripts/monitor-metrics.sh
   
   # Rollback if issues detected
   ./scripts/rollback.sh blue
   ```

## 📊 Database Migrations

### Migration Strategy

1. **Backward Compatible Migrations**
   - Add new columns with defaults
   - Create new tables
   - Add indexes (online)

2. **Breaking Changes**
   - Deploy in multiple phases
   - Use feature flags
   - Coordinate with application changes

### Migration Commands

```bash
# Create new migration
docker-compose exec api alembic revision --autogenerate -m "Description"

# Review migration file
# Edit alembic/versions/xxx_description.py

# Test migration in development
docker-compose exec api alembic upgrade head

# Apply to staging
docker-compose -f docker-compose.staging.yml exec api alembic upgrade head

# Apply to production (during deployment window)
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### Migration Rollback

```bash
# Rollback one migration
docker-compose exec api alembic downgrade -1

# Rollback to specific revision
docker-compose exec api alembic downgrade <revision_id>

# Check current revision
docker-compose exec api alembic current
```

## 🔧 Configuration Management

### Environment Variables

**Required Variables:**
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
POSTGRES_DB=ghostworks
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_URL=redis://redis:6379/0

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Observability
OPENTELEMETRY_ENDPOINT=http://otelcol:4317
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc_dir
```

**Optional Variables:**
```bash
# Email (if configured)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=noreply@ghostworks.dev
SMTP_PASSWORD=smtp_password

# External Services
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Configuration Files

1. **Docker Compose Overrides**
   - `docker-compose.override.yml` - Development
   - `docker-compose.staging.yml` - Staging
   - `docker-compose.prod.yml` - Production

2. **Application Configuration**
   - `services/api/config.py` - API settings
   - `apps/web/.env.local` - Frontend settings
   - `infra/nginx/conf.d/` - Nginx configuration

## 🚨 Rollback Procedures

### Automatic Rollback Triggers

- API error rate > 10%
- Response time P95 > 2 seconds
- Health check failures > 3 consecutive
- Database connection failures

### Manual Rollback

```bash
# 1. Identify last known good version
git log --oneline -10

# 2. Rollback application
./scripts/rollback.sh <previous_version>

# 3. Rollback database (if needed)
docker-compose exec api alembic downgrade <revision>

# 4. Verify rollback
./scripts/health-check.sh production

# 5. Update monitoring
./scripts/update-deployment-status.sh rolled_back
```

### Emergency Rollback

```bash
# Immediate traffic switch (< 30 seconds)
./scripts/emergency-rollback.sh

# This script:
# 1. Switches load balancer to previous version
# 2. Stops new deployments
# 3. Alerts on-call team
# 4. Creates incident ticket
```

## 📈 Post-Deployment Verification

### Health Checks

```bash
# API Health
curl -f https://api.ghostworks.dev/api/v1/health

# Database Connectivity
docker-compose exec api python -c "
from database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database OK')
"

# Redis Connectivity
docker-compose exec api python -c "
import redis
r = redis.from_url('redis://redis:6379/0')
r.ping()
print('Redis OK')
"
```

### Smoke Tests

```bash
# Authentication flow
./scripts/test-auth-flow.sh

# Artifact CRUD operations
./scripts/test-artifact-crud.sh

# Multi-tenant isolation
./scripts/test-tenant-isolation.sh

# Performance benchmarks
./scripts/performance-test.sh
```

### Monitoring Verification

1. **Check Grafana Dashboards**
   - API golden signals
   - Business metrics
   - System resources

2. **Verify Alerts**
   - Test alert rules
   - Confirm notification channels
   - Check escalation policies

3. **Log Analysis**
   - Check for error patterns
   - Verify log aggregation
   - Confirm correlation IDs

## 🔍 Troubleshooting

### Common Deployment Issues

**Service Won't Start**
```bash
# Check logs
docker-compose logs [service-name]

# Check resource usage
docker stats

# Verify configuration
docker-compose config
```

**Database Connection Issues**
```bash
# Check database status
docker-compose exec postgres pg_isready

# Verify connection string
docker-compose exec api python -c "
from config import settings
print(settings.database_url)
"

# Test connection
docker-compose exec postgres psql -U postgres -d ghostworks -c "SELECT version();"
```

**Migration Failures**
```bash
# Check migration status
docker-compose exec api alembic current

# View migration history
docker-compose exec api alembic history

# Manual migration repair
docker-compose exec api alembic stamp head
```

### Performance Issues

**High Response Times**
1. Check database query performance
2. Verify connection pool settings
3. Review application logs for bottlenecks
4. Check system resources (CPU, memory)

**Memory Leaks**
1. Monitor container memory usage
2. Check for unclosed database connections
3. Review application code for memory leaks
4. Restart services if necessary

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Code review completed
- [ ] Database migrations reviewed
- [ ] Configuration updated
- [ ] Backup completed
- [ ] Rollback plan prepared

### During Deployment
- [ ] Services deployed successfully
- [ ] Database migrations applied
- [ ] Health checks passing
- [ ] Smoke tests completed
- [ ] Monitoring active

### Post-Deployment
- [ ] Performance metrics normal
- [ ] Error rates acceptable
- [ ] User acceptance testing
- [ ] Documentation updated
- [ ] Team notified

## 📞 Emergency Contacts

### Escalation Path
1. **Platform Team Lead**: [Phone/Slack]
2. **DevOps Engineer**: [Phone/Slack]
3. **Engineering Manager**: [Phone/Slack]
4. **CTO**: [Phone/Slack]

### External Contacts
- **Infrastructure Provider**: [Contact Info]
- **Database Support**: [Contact Info]
- **Security Team**: [Contact Info]

---

**Last Updated**: [Current Date]  
**Next Review**: [Next Month]