# Getting Started with Ghostworks

This guide provides comprehensive instructions for setting up and developing with the Ghostworks SaaS platform.

## 🚀 Quick Start

**Prerequisites**: Docker and Docker Compose

### One-Liner Setup
```bash
git clone https://github.com/Realm-101/Kiro-Ghostworks.git && cd Kiro-Ghostworks && make dev-up
```

This single command will:
1. Clone the repository
2. Set up environment variables
3. Start all services
4. Initialize the database
5. Seed demo data
6. Show you all access URLs

## 📋 Prerequisites

### Required Software
- **Docker Desktop** (latest version)
- **Docker Compose** (included with Docker Desktop)
- **Git** (for cloning the repository)

### Optional (for local development)
- **Node.js 18+** (for frontend development)
- **Python 3.11+** (for backend development)
- **Make** (for using Makefile commands)

### System Requirements
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space
- **OS**: Windows 10+, macOS 10.15+, or Linux

## 🛠️ Detailed Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Realm-101/Kiro-Ghostworks.git
cd Kiro-Ghostworks
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional)
nano .env  # or your preferred editor
```

**Key Environment Variables:**
```bash
# Database
POSTGRES_DB=ghostworks
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Security
JWT_SECRET_KEY=your-secret-key-change-in-production

# Services
API_PORT=8000
WEB_PORT=3000
GRAFANA_PORT=3001
```

### 3. Start Services

#### Option A: Full Development Stack
```bash
make dev-up
```

#### Option B: Manual Step-by-Step
```bash
# Start all services
docker-compose --profile dev up -d

# Initialize database
docker-compose exec api python -m alembic upgrade head

# Seed demo data
docker-compose exec api python scripts/seed_demo_data.py
```

#### Option C: Individual Services
```bash
# Start only core services
make api          # API + database + Redis
make web          # Web app + API
make observability # Monitoring stack only
```

### 4. Verify Installation
```bash
# Check service health
make health

# Validate demo data
make validate-demo-assets
```

## 🌐 Access URLs

Once running, access the platform at:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Web Application** | http://localhost:3000 | `owner@acme.com` / `demo123` |
| **API Documentation** | http://localhost:8000/docs | - |
| **Grafana Dashboards** | http://localhost:3001 | `admin` / `admin` |
| **Prometheus Metrics** | http://localhost:9090 | - |
| **Interactive Tour** | http://localhost:3000/tour | - |

### Demo Accounts

| Email | Password | Role | Workspace |
|-------|----------|------|-----------|
| owner@acme.com | demo123 | Owner | Acme Corp |
| admin@umbrella.com | demo123 | Admin | Umbrella Inc |
| member@acme.com | demo123 | Member | Acme Corp |

> **⚠️ Security Note**: Demo credentials only work in development. They are automatically disabled in production.

## 🧪 Development Workflow

### Local Development Setup

1. **Install Dependencies**
   ```bash
   # Frontend
   cd apps/web && npm install
   
   # Backend
   cd services/api && pip install -r requirements.txt
   
   # Worker
   cd services/worker && pip install -r requirements.txt
   ```

2. **Start Development Services**
   ```bash
   # Start infrastructure
   docker-compose up -d postgres redis
   
   # Start API (with hot reload)
   cd services/api && uvicorn main:app --reload --port 8000
   
   # Start worker
   cd services/worker && celery -A celery_app worker --loglevel=info
   
   # Start frontend (with hot reload)
   cd apps/web && npm run dev
   ```

### Testing

```bash
# Run all tests
make test

# Specific test types
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-e2e          # End-to-end tests
make test-security     # Security tests
make test-performance  # Performance tests
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

## 🔧 Common Commands

### Service Management
```bash
make up              # Start all services
make down            # Stop all services
make restart         # Restart all services
make logs            # View logs
make status          # Service status
```

### Database Operations
```bash
make db-migrate      # Run migrations
make db-reset        # Reset database (⚠️ destroys data)
make seed-demo       # Seed demo data
make validate-demo   # Validate demo data
```

### Development Tools
```bash
make shell-api       # API container shell
make shell-db        # Database shell
make shell-web       # Web container shell
```

### Monitoring
```bash
make metrics         # Open Prometheus
make dashboards      # Open Grafana
make flower          # Open Celery monitoring
```

## 🐛 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker is running
docker --version
docker-compose --version

# Check port conflicts
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Reset everything
make clean && make dev-up
```

#### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Reset database
make db-reset

# Check logs
docker-compose logs postgres
```

#### Demo Data Missing
```bash
# Re-seed demo data
make seed-demo

# Validate data exists
make validate-demo
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Restart services
make restart

# Check logs for errors
make logs
```

### Getting Help

1. **Check Service Logs**
   ```bash
   make logs
   docker-compose logs [service-name]
   ```

2. **Validate Configuration**
   ```bash
   make health
   make validate-demo-assets
   ```

3. **Reset Environment**
   ```bash
   make clean
   make dev-up
   ```

4. **Documentation**
   - [Demo Script](DEMO_SCRIPT.md) - Presentation guide
   - [CI/CD Pipeline](ci-cd-pipeline.md) - Development workflow
   - [Runbooks](runbooks/) - Operational procedures

## 🚀 Next Steps

### For New Users
1. **Take the Tour**: Visit http://localhost:3000/tour
2. **Explore Features**: Login and browse artifacts
3. **Check Monitoring**: View Grafana dashboards
4. **Read Documentation**: Browse the `/docs` directory

### For Developers
1. **Review Architecture**: See `docs/adr/` for decisions
2. **Understand Testing**: Check `tests/` directory structure
3. **Explore Hooks**: See `hooks/` for AI automation
4. **Study Security**: Review `.kiro/steering/security-policies.md`

### For Presenters
1. **Validate Assets**: Run `make validate-demo-assets`
2. **Practice Demo**: Follow `docs/DEMO_SCRIPT.md`
3. **Prepare Environment**: Ensure all services healthy
4. **Review Features**: Understand key capabilities

## 📚 Additional Resources

- **[Architecture Overview](../README.md#architecture)** - System design
- **[Security Documentation](security/)** - Security implementation
- **[API Reference](http://localhost:8000/docs)** - Interactive API docs
- **[Contributing Guide](../CONTRIBUTING.md)** - Development guidelines
- **[Deployment Guide](runbooks/deployment.md)** - Production deployment