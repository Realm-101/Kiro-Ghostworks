# ADR-0004: Deployment Strategy and CI/CD Approach

## Status
Accepted

## Context
Ghostworks requires a robust deployment strategy that supports:

1. **Development Velocity**: Fast, reliable deployments with minimal friction
2. **Production Reliability**: Zero-downtime deployments with rollback capabilities
3. **Multi-Environment Support**: Consistent deployments across dev, staging, and production
4. **Security**: Automated security scanning and compliance checks
5. **Observability**: Comprehensive monitoring and alerting during deployments
6. **Cost Efficiency**: Optimal resource utilization and infrastructure costs
7. **Developer Experience**: Simple local development setup and testing

Key requirements:
- Containerized applications for consistency and portability
- Automated CI/CD pipeline with quality gates
- Infrastructure as Code for reproducible environments
- Comprehensive testing at multiple levels
- Security scanning and vulnerability management
- Monitoring and alerting integration

## Decision
We have implemented a **Docker Compose-based deployment strategy** with **GitHub Actions CI/CD pipeline**:

### Deployment Architecture
1. **Containerization**: Docker containers for all services with multi-stage builds
2. **Orchestration**: Docker Compose for local development and production deployment
3. **CI/CD**: GitHub Actions for automated testing, building, and deployment
4. **Infrastructure**: Infrastructure as Code using Docker Compose configurations
5. **Security**: Integrated security scanning and vulnerability assessment
6. **Monitoring**: Comprehensive observability stack deployment

### Container Strategy
```dockerfile
# Multi-stage build for FastAPI service
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim as runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Configuration
```yaml
# docker-compose.yml - Production configuration
version: '3.8'

services:
  api:
    build: 
      context: ./services/api
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
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
    restart: unless-stopped

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=${API_URL}
    depends_on:
      api:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### CI/CD Pipeline
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r services/api/requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run linting
        run: |
          ruff check services/api/
          black --check services/api/
      
      - name: Run unit tests
        run: |
          pytest services/api/tests/unit/ --cov=services/api --cov-report=xml
      
      - name: Run integration tests
        run: |
          docker-compose -f docker-compose.test.yml up -d
          pytest services/api/tests/integration/
          docker-compose -f docker-compose.test.yml down

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run security scan
        uses: securecodewarrior/github-action-add-sarif@v1
        with:
          sarif-file: 'security-scan-results.sarif'
      
      - name: OWASP ZAP Baseline Scan
        uses: zaproxy/action-baseline@v0.7.0
        with:
          target: 'http://localhost:8000'

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker images
        run: |
          docker-compose build
      
      - name: Run E2E tests
        run: |
          docker-compose up -d
          npm run test:e2e
          docker-compose down
      
      - name: Generate Kiro Score
        run: |
          python scripts/generate_kiro_score.py
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: kiro-score
          path: kiro_score.json

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to production
        run: |
          # Production deployment logic
          docker-compose -f docker-compose.prod.yml up -d
```

## Alternatives Considered

### 1. Kubernetes with Helm
**Description**: Deploy to Kubernetes cluster using Helm charts for package management.

**Pros**:
- Industry standard for container orchestration
- Excellent scalability and high availability
- Rich ecosystem of tools and operators
- Advanced deployment strategies (blue-green, canary)
- Service mesh integration capabilities

**Cons**:
- High complexity for initial setup and management
- Steep learning curve for development team
- Operational overhead of managing Kubernetes cluster
- Overkill for current scale and requirements
- Higher infrastructure costs

**Rejected**: Complexity outweighs benefits for current scale and team size.

### 2. AWS ECS/Fargate
**Description**: Use AWS container services for managed container deployment.

**Pros**:
- Managed service reduces operational overhead
- Good integration with AWS ecosystem
- Auto-scaling capabilities
- Pay-per-use pricing model

**Cons**:
- Vendor lock-in to AWS
- Less flexibility than self-managed solutions
- Learning curve for AWS-specific concepts
- Potential cost increases at scale

**Rejected**: Platform should demonstrate cloud-agnostic capabilities.

### 3. Traditional VM Deployment
**Description**: Deploy applications directly on virtual machines with configuration management.

**Pros**:
- Simple and well-understood deployment model
- Full control over environment configuration
- Lower resource overhead than containers

**Cons**:
- Environment inconsistency between dev/prod
- Complex dependency management
- Slower deployment and rollback processes
- Manual scaling and management

**Rejected**: Containers provide better consistency and deployment velocity.

### 4. Serverless (AWS Lambda/Vercel)
**Description**: Deploy as serverless functions with managed infrastructure.

**Pros**:
- Zero infrastructure management
- Automatic scaling
- Pay-per-execution pricing
- Fast cold start times (for some platforms)

**Cons**:
- Vendor lock-in and platform limitations
- Cold start latency issues
- Limited runtime and resource constraints
- Complex state management for stateful applications

**Rejected**: Not suitable for our database-heavy, stateful application architecture.

### 5. Platform as a Service (Heroku, Railway)
**Description**: Deploy to managed PaaS platform with git-based deployments.

**Pros**:
- Extremely simple deployment process
- Managed infrastructure and scaling
- Good developer experience
- Built-in CI/CD capabilities

**Cons**:
- Vendor lock-in and limited customization
- Higher costs at scale
- Less control over infrastructure
- Limited observability and debugging options

**Rejected**: Platform should demonstrate infrastructure control and cost efficiency.

## Consequences

### Positive Consequences

1. **Simplicity**: Docker Compose provides simple, understandable deployment model
2. **Consistency**: Identical environments across development, staging, and production
3. **Portability**: Can run on any Docker-compatible infrastructure
4. **Cost Efficiency**: Optimal resource utilization without orchestration overhead
5. **Developer Experience**: Simple local development setup with `docker-compose up`
6. **Rapid Deployment**: Fast build and deployment cycles
7. **Rollback Capability**: Easy rollback using Docker image tags
8. **Observability**: Integrated monitoring and logging from day one

### Negative Consequences

1. **Scalability Limitations**: Manual scaling compared to Kubernetes auto-scaling
2. **High Availability**: Single point of failure without orchestration layer
3. **Service Discovery**: Manual service configuration vs. automatic discovery
4. **Load Balancing**: Basic nginx load balancing vs. advanced traffic management
5. **Rolling Updates**: Manual coordination vs. automated rolling deployments
6. **Resource Management**: Less sophisticated resource allocation and limits

### Migration Path
The Docker Compose approach provides a clear migration path to more sophisticated orchestration:

1. **Phase 1**: Docker Compose for initial deployment and validation
2. **Phase 2**: Add load balancing and health checking improvements
3. **Phase 3**: Implement blue-green deployment strategies
4. **Phase 4**: Migrate to Kubernetes when scale demands it

## Implementation Details

### Environment Management
```bash
# Environment-specific configurations
.env.development    # Local development settings
.env.staging       # Staging environment settings
.env.production    # Production environment settings

# Environment variable validation
DATABASE_URL=postgresql://user:pass@postgres:5432/ghostworks
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=${JWT_SECRET_KEY}
OPENTELEMETRY_ENDPOINT=http://otelcol:4317
```

### Health Checks and Monitoring
```yaml
# Comprehensive health checking
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

# Dependency management
depends_on:
  postgres:
    condition: service_healthy
  redis:
    condition: service_healthy
```

### Security Configuration
```yaml
# Security hardening in production
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp
  - /var/tmp
user: "1001:1001"
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE
```

### Backup and Recovery
```bash
# Database backup strategy
#!/bin/bash
# backup.sh
docker-compose exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup_$(date +%Y%m%d_%H%M%S).sql

# Volume backup
docker run --rm -v ghostworks_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### Deployment Scripts
```bash
#!/bin/bash
# deploy.sh - Production deployment script

set -e

echo "Starting deployment..."

# Pull latest images
docker-compose pull

# Run database migrations
docker-compose run --rm api alembic upgrade head

# Deploy with zero downtime
docker-compose up -d --no-deps api worker

# Health check
sleep 30
curl -f http://localhost/health || exit 1

echo "Deployment completed successfully"
```

### Monitoring Integration
```yaml
# Observability stack deployment
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infra/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./infra/grafana/datasources:/etc/grafana/provisioning/datasources
```

## Security Considerations

### Container Security
- Use official, minimal base images (alpine variants)
- Regular security scanning with Trivy or similar tools
- Non-root user execution in containers
- Read-only filesystems where possible
- Minimal capability sets and security options

### Secrets Management
```yaml
# Docker secrets for sensitive data
secrets:
  jwt_secret:
    external: true
  db_password:
    external: true

services:
  api:
    secrets:
      - jwt_secret
      - db_password
```

### Network Security
```yaml
# Network isolation
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access

services:
  api:
    networks:
      - frontend
      - backend
  postgres:
    networks:
      - backend  # Only internal access
```

## Performance Optimization

### Build Optimization
- Multi-stage Docker builds to minimize image size
- Layer caching optimization for faster builds
- Dependency caching in CI/CD pipeline
- Parallel build processes where possible

### Runtime Optimization
- Resource limits and reservations
- Connection pooling configuration
- Caching strategies (Redis, application-level)
- Database query optimization

### Monitoring and Alerting
- Container resource usage monitoring
- Application performance metrics
- Infrastructure health checks
- Automated alerting for deployment issues

## Testing Strategy

### Local Testing
```bash
# Local development testing
docker-compose -f docker-compose.test.yml up -d
pytest tests/
docker-compose -f docker-compose.test.yml down
```

### CI/CD Testing
- Unit tests with coverage requirements
- Integration tests with test database
- E2E tests with full stack deployment
- Security scanning and vulnerability assessment
- Performance testing with realistic load

### Production Validation
- Health check endpoints for all services
- Smoke tests after deployment
- Monitoring and alerting validation
- Rollback procedures testing

## Operational Procedures

### Deployment Process
1. **Pre-deployment**: Run full test suite and security scans
2. **Database Migration**: Apply schema changes with rollback plan
3. **Service Deployment**: Rolling update with health checks
4. **Post-deployment**: Validation tests and monitoring verification
5. **Rollback Plan**: Automated rollback on failure detection

### Maintenance Procedures
- Regular security updates and patching
- Database maintenance and optimization
- Log rotation and cleanup
- Backup verification and testing
- Performance monitoring and optimization

## References
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Container Security Best Practices](https://sysdig.com/blog/dockerfile-best-practices/)
- [12-Factor App Methodology](https://12factor.net/)
- [OWASP Container Security](https://owasp.org/www-project-container-security/)