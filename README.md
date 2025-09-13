# Ghostworks SaaS Platform

A production-grade, AI-native multi-tenant SaaS platform that demonstrates autonomous development capabilities. Built with Next.js, FastAPI, PostgreSQL, and comprehensive observability.

## 🚀 Quick Start

**Prerequisites**: Docker and Docker Compose

### One-Liner Launch
```bash
git clone https://github.com/Realm-101/Kiro-Ghostworks.git && cd Kiro-Ghostworks && make dev-up
```

**That's it!** The platform will be ready at:
- **Web App**: http://localhost:3000 (login: `owner@acme.com` / `demo123`)
- **API Docs**: http://localhost:8000/docs  
- **Grafana**: http://localhost:3001 (`admin`/`admin`)
- **Prometheus**: http://localhost:9090

### What `make dev-up` Does
1. Copies `.env.example` to `.env` with sensible defaults
2. Starts all services with Docker Compose
3. Initializes database with migrations
4. Seeds demo data automatically
5. Waits for services to be healthy
6. Shows you the URLs to access

<details>
<summary>📋 Manual Setup (if you prefer step-by-step)</summary>

### Manual Launch Steps

1. **Clone and setup**
   ```bash
   git clone https://github.com/Realm-101/Kiro-Ghostworks.git
   cd Kiro-Ghostworks
   cp .env.example .env
   ```

2. **Start services**
   ```bash
   docker-compose --profile dev up -d
   ```

3. **Initialize database**
   ```bash
   docker-compose exec api python -m alembic upgrade head
   ```

4. **Access the platform**
   - **Web Application**: http://localhost:3000
   - **API Documentation**: http://localhost:8000/docs
   - **Grafana Dashboards**: http://localhost:3001 (admin/admin)
   - **Prometheus Metrics**: http://localhost:9090

</details>

<details>
<summary>🔑 Demo Accounts (Development Only)</summary>

> **⚠️ SECURITY WARNING: DEMO CREDENTIALS ONLY**
> 
> **These credentials are ONLY available in local/development environments.**
> **They are automatically DISABLED in staging and production deployments.**
> **Never use these credentials in any production system.**

| Email | Password | Role | Workspace |
|-------|----------|------|-----------|
| owner@acme.com | demo123 | Owner | Acme Corp |
| admin@umbrella.com | demo123 | Admin | Umbrella Inc |
| member@acme.com | demo123 | Member | Acme Corp |

Demo credentials are loaded only when using the `dev` Docker Compose profile:
```bash
# Demo data is loaded automatically in development
docker-compose --profile dev up -d

# Production deployments exclude demo data entirely
docker-compose -f docker-compose.prod.yml up -d
```

</details>

## 🏗️ Architecture

### Services Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js Web   │    │   FastAPI API   │    │ Celery Worker   │
│     :3000       │────│     :8000       │────│   Background    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────┬─────┴─────┬─────────────────┐
         │                 │           │                 │
    ┌─────────┐    ┌──────────────┐   │    ┌─────────────────┐
    │ Nginx   │    │ PostgreSQL   │   │    │     Redis       │
    │  :80    │    │    :5432     │   │    │     :6379       │
    └─────────┘    └──────────────┘   │    └─────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
         ┌─────────┐         ┌─────────────┐         ┌─────────────┐
         │Prometheus│         │   Grafana   │         │ OpenTelemetry│
         │  :9090   │         │    :3001    │         │ Collector    │
         └─────────┘         └─────────────┘         └─────────────┘
```

### Technology Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, React Query
- **Backend**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **Database**: PostgreSQL with Row-Level Security
- **Cache/Queue**: Redis with Celery
- **Observability**: OpenTelemetry, Prometheus, Grafana
- **Testing**: Playwright, pytest, Vitest
- **Infrastructure**: Docker Compose, Nginx

## 🎯 Key Features

### Multi-Tenant Architecture
- **Tenant Isolation**: Row-Level Security at database level
- **Role-Based Access**: Owner, Admin, Member roles
- **Workspace Management**: Secure workspace switching
- **Data Segregation**: Complete tenant data isolation

*Screenshots: See [Authentication Flow](docs/screenshots/README.md#authentication-flow)*

### Artifact Management
- **CRUD Operations**: Full artifact lifecycle management
- **Search & Filter**: Full-text search with tag filtering
- **Optimistic Updates**: Responsive UI with React Query
- **Validation**: Comprehensive server-side validation

*Screenshots: See [Artifact Management](docs/screenshots/README.md#artifact-management)*

### Observability Stack
- **Distributed Tracing**: OpenTelemetry across all services
- **Metrics Collection**: Prometheus with golden signals
- **Dashboards**: Grafana with business and technical metrics
- **Structured Logging**: JSON logs with correlation IDs
- **Alerting**: Automated alerts for SLA violations

*Screenshots: See [Monitoring Dashboards](docs/screenshots/README.md#grafana-dashboards)*

### Security Features
- **Authentication**: JWT with refresh tokens (HttpOnly cookies, 15min access / 7day refresh)
- **Authorization**: RBAC with tenant isolation via PostgreSQL Row-Level Security
- **Input Validation**: Pydantic models with sanitization
- **Security Headers**: Strict Content-Security-Policy and OWASP-compliant headers
- **Rate Limiting**: API endpoint protection (60 req/min, 5 auth req/min)
- **Refresh Token Strategy**: Secure rotation with path-restricted cookies (`/auth/refresh`)
- **Tenant Isolation**: Database-level RLS policies prevent cross-tenant data access

### AI Integration
- **MCP Servers**: GitHub and AWS documentation integration
- **Agent Hooks**: Asset optimization and release automation
- **Steering Documents**: AI development guidance
- **Autonomous Workflows**: Self-improving development processes

*Screenshots: See [Development Tools](docs/screenshots/README.md#development-tools)*

## 🛠️ Development

### Local Development Setup

1. **Install dependencies**
   ```bash
   # Frontend
   cd apps/web && npm install
   
   # Backend
   cd services/api && pip install -r requirements.txt
   
   # Worker
   cd services/worker && pip install -r requirements.txt
   ```

2. **Start development services**
   ```bash
   # Database and Redis
   docker-compose up -d postgres redis
   
   # API server
   cd services/api && uvicorn main:app --reload --port 8000
   
   # Worker
   cd services/worker && celery -A celery_app worker --loglevel=info
   
   # Frontend
   cd apps/web && npm run dev
   ```

### Running Tests

```bash
# All tests
make test

# Backend tests
cd services/api && pytest

# Frontend tests
cd apps/web && npm test

# E2E tests
cd apps/web && npx playwright test

# Performance tests
cd tests/performance && k6 run api-load-test.js
```

### Code Quality

```bash
# Linting and formatting
make lint
make format

# Type checking
make typecheck

# Security scanning
make security-scan
```

## 📊 Monitoring & Operations

### Health Checks

- **API Health**: `GET /api/v1/health`
- **Database**: Connection pool status
- **Redis**: Cache connectivity
- **Worker**: Task queue status

### Key Metrics

- **Golden Signals**: Latency, traffic, errors, saturation
- **Business Metrics**: Users, workspaces, artifacts
- **System Metrics**: CPU, memory, disk, network

### Alerting Thresholds

- API error rate > 5%
- P95 latency > 500ms
- Database connections > 80%
- Worker queue backlog > 1000

## 🚢 Deployment

### Production Deployment

1. **Build images**
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```

2. **Deploy stack**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Run migrations**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

### Environment Configuration

Key environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: JWT signing secret
- `OPENTELEMETRY_ENDPOINT`: Telemetry collector endpoint
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)

## 📚 Documentation

- **[Getting Started Guide](docs/getting-started.md)** - Detailed setup and development guide
- **[Demo Script](docs/DEMO_SCRIPT.md)** - Comprehensive presentation guide
- **[API Documentation](http://localhost:8000/docs)** - Interactive OpenAPI docs (when running)
- **[Architecture Decisions](docs/adr/)** - Technical decision records
- **[CI/CD Pipeline](docs/ci-cd-pipeline.md)** - Complete pipeline documentation
- **[Operational Runbooks](docs/runbooks/)** - Production operations guide
- **[Security Documentation](docs/security/)** - Security policies and implementation

## 🎪 Demo & Tour

### Interactive Tour

Visit `/tour` for an interactive demonstration featuring:

- Live system metrics and health status
- Real-time telemetry visualization
- Asset optimization demonstrations
- Guided feature walkthrough

### Demo Script

See `docs/DEMO_SCRIPT.md` for a comprehensive presentation guide.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### Development Guidelines

- Follow the code conventions in `.kiro/steering/code-conventions.md`
- Maintain test coverage above 70% (backend) and 60% (frontend)
- Update documentation for new features
- Follow security guidelines in `.kiro/steering/security-policies.md`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` directory
- **Runbooks**: `docs/runbooks/`
- **Security**: See `SECURITY.md`

---

**Ghostworks** - Demonstrating the future of AI-native development