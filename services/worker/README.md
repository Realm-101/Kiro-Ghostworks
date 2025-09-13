# Ghostworks SaaS Worker Service

The Celery worker service handles background tasks for the Ghostworks SaaS platform, including email notifications, data processing, and system maintenance.

## Features

- **Email Tasks**: User verification, password reset, workspace invitations
- **Data Processing**: Analytics, reporting, bulk operations
- **Maintenance**: Token cleanup, health checks, log rotation
- **Observability**: Structured logging, OpenTelemetry tracing, Prometheus metrics
- **Error Handling**: Automatic retries with exponential backoff
- **Task Routing**: Separate queues for different task types

## Architecture

```
services/worker/
├── celery_app.py          # Celery application configuration
├── config.py              # Settings and configuration
├── database.py            # Shared database connection utilities
├── worker.py              # Main worker entry point
├── tasks/
│   ├── email_tasks.py     # Email notification tasks
│   ├── data_tasks.py      # Data processing tasks
│   └── maintenance_tasks.py # System maintenance tasks
└── requirements.txt       # Python dependencies
```

## Task Queues

- **email**: User notifications and communication
- **data_processing**: Analytics and bulk operations
- **maintenance**: System cleanup and health checks

## Configuration

The worker uses the same configuration system as the API service, with additional Celery-specific settings:

```python
# Environment variables
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/ghostworks
CELERY_BROKER_URL=redis://localhost:6379/0  # Optional, defaults to REDIS_URL
CELERY_RESULT_BACKEND=redis://localhost:6379/0  # Optional, defaults to REDIS_URL
```

## Running the Worker

### Development

```bash
cd services/worker
pip install -r requirements.txt
python worker.py
```

### Production

```bash
celery -A services.worker.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --queues=email,data_processing,maintenance \
  --hostname=ghostworks-worker@%h
```

### Docker

```bash
docker build -t ghostworks-worker .
docker run -d \
  --name ghostworks-worker \
  --env-file .env \
  ghostworks-worker
```

## Task Examples

### Email Tasks

```python
from services.worker.tasks.email_tasks import send_verification_email

# Send verification email
result = send_verification_email.delay(
    user_id="123e4567-e89b-12d3-a456-426614174000",
    email="user@example.com",
    verification_token="abc123"
)
```

### Data Processing Tasks

```python
from services.worker.tasks.data_tasks import process_artifact_analytics

# Process analytics for a tenant
result = process_artifact_analytics.delay(
    tenant_id="123e4567-e89b-12d3-a456-426614174000",
    date_range_days=7
)
```

### Maintenance Tasks

```python
from services.worker.tasks.maintenance_tasks import cleanup_expired_tokens

# Clean up expired tokens
result = cleanup_expired_tokens.delay()
```

## Monitoring

### Health Check

```python
from services.worker.celery_app import health_check

# Check worker health
result = health_check.delay()
print(result.get())  # {"status": "healthy", "worker": "ghostworks_worker"}
```

### Celery Flower (Optional)

```bash
pip install flower
celery -A services.worker.celery_app flower
```

Access the web interface at http://localhost:5555

## Error Handling

All tasks implement automatic retry with exponential backoff:

- **Max retries**: 3
- **Backoff**: 60 seconds * (2 ^ retry_count)
- **Exceptions**: Logged with full context

## Database Integration

The worker shares database models and connections with the API service:

```python
from services.worker.database import get_database_session

async def example_task():
    async with get_database_session() as session:
        # Use session for database operations
        result = await session.execute(query)
        return result
```

## Testing

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=services.worker tests/
```

## Security

- Database connections use connection pooling with limits
- All inputs are validated using Pydantic models
- Sensitive data is not logged
- Task results expire after 1 hour
- Worker processes are isolated and stateless

## Performance

- **Prefetch multiplier**: 1 (one task per worker at a time)
- **Max tasks per child**: 1000 (prevents memory leaks)
- **Task time limits**: 5 minutes hard, 4 minutes soft
- **Connection pooling**: Shared with API service

## Deployment Considerations

1. **Scaling**: Run multiple worker processes for high throughput
2. **Queues**: Separate workers can handle specific queues
3. **Monitoring**: Use Prometheus metrics and structured logs
4. **Health checks**: Built-in health check task for load balancers
5. **Graceful shutdown**: Workers handle SIGTERM properly