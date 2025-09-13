# Ghostworks SaaS API Service

Production-grade FastAPI backend service for the Ghostworks multi-tenant SaaS platform.

## Features

- **FastAPI** with async/await support
- **SQLAlchemy 2.0** with async database operations
- **Alembic** for database migrations
- **Pydantic v2** for data validation and settings
- **Structured logging** with JSON output
- **Health check endpoints** with detailed service status
- **OpenTelemetry** instrumentation ready
- **Prometheus metrics** support

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Redis (for Celery worker integration)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the development server:
```bash
python run.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Configuration

The service uses Pydantic Settings for 12-Factor App compliance. Configuration can be provided via:

1. Environment variables
2. `.env` file
3. Default values

### Key Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Runtime environment |
| `DATABASE_URL` | Required | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Required | Secret key for JWT tokens |
| `PORT` | `8000` | Server port |
| `LOG_LEVEL` | `INFO` | Logging level |

## Database Migrations

The service uses Alembic for database schema management:

```bash
# Check migration status
alembic current

# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
```

## API Endpoints

### Health Checks

- `GET /health` - Basic health status
- `GET /health/detailed` - Detailed service status with dependencies

### Core API

- `GET /` - API information and links

## Development

### Running Tests

```bash
python test_config.py
```

### Code Quality

The service follows these standards:
- Type hints for all functions
- Structured logging with correlation IDs
- Comprehensive error handling
- Security best practices

### Project Structure

```
services/api/
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── run.py               # Development server
├── requirements.txt     # Python dependencies
├── alembic.ini         # Alembic configuration
├── alembic/            # Database migrations
│   ├── env.py          # Migration environment
│   ├── script.py.mako  # Migration template
│   └── versions/       # Migration files
└── .env.example        # Environment template
```

## Production Deployment

For production deployment:

1. Set `ENVIRONMENT=production`
2. Use a production WSGI server (uvicorn with multiple workers)
3. Configure proper database connection pooling
4. Set up monitoring and logging aggregation
5. Enable security headers and HTTPS

## Observability

The service includes built-in observability features:

- **Structured Logging**: JSON logs with correlation IDs
- **Health Checks**: Comprehensive service status
- **Metrics**: Prometheus-compatible metrics endpoint
- **Tracing**: OpenTelemetry instrumentation ready

## Security

Security features include:

- JWT-based authentication
- CORS configuration
- Input validation with Pydantic
- Security headers middleware
- Environment-based configuration