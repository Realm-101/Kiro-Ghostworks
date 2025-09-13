# Structured Logging Implementation

This document describes the structured logging implementation for the Ghostworks SaaS platform.

## Overview

The platform uses structured logging with JSON format to provide consistent, searchable, and analyzable logs across all services. The implementation includes:

- **JSON-formatted logs** with consistent field names
- **Correlation IDs** for request tracing
- **Tenant and user context** for multi-tenant isolation
- **Operation context** for business logic tracking
- **Log rotation** to manage disk space
- **Centralized configuration** shared between services

## Architecture

### Shared Logging Configuration

The logging configuration is centralized in `packages/shared/src/logging_config.py` and provides:

- Consistent JSON formatting across all services
- Context variable management for correlation IDs, tenant IDs, and user IDs
- Log rotation with configurable size limits
- Service-specific log files
- Console and file output options

### Service Integration

Each service (API and Worker) configures structured logging during startup:

```python
from packages.shared.src.logging_config import configure_structured_logging, get_logger

# Configure logging for the service
configure_structured_logging(
    service_name="api",  # or "worker"
    log_level="INFO",
    log_file="logs/api.log",
    enable_console=True,
    enable_rotation=True,
    max_log_size_mb=10,
    backup_count=5
)

logger = get_logger(__name__)
```

## Log Format

All logs are formatted as JSON with the following standard fields:

```json
{
  "timestamp": "2025-09-12T20:04:33.074789Z",
  "level": "info",
  "service": "api",
  "logger": "services.api.routes.artifacts",
  "event": "Artifact created successfully",
  "correlation_id": "req-123e4567-e89b-12d3-a456-426614174000",
  "tenant_id": "tenant-456",
  "user_id": "user-789",
  "operation": "artifact.create",
  "artifact_id": "artifact-999",
  "duration_ms": 150
}
```

### Standard Fields

- **timestamp**: ISO 8601 formatted timestamp
- **level**: Log level (debug, info, warning, error, critical)
- **service**: Service name (api, worker)
- **logger**: Logger name (usually module name)
- **event**: Human-readable log message

### Context Fields

- **correlation_id**: Unique ID for request tracing
- **tenant_id**: Tenant UUID for multi-tenant context
- **user_id**: User UUID for user-specific operations
- **operation**: Business operation being performed

### Custom Fields

Additional fields can be added per log entry for specific context.

## Usage Examples

### Basic Logging

```python
from packages.shared.src.logging_config import get_logger

logger = get_logger(__name__)

logger.info("User logged in", user_id="user-123", login_method="password")
logger.warning("Rate limit approaching", current_requests=95, limit=100)
logger.error("Database connection failed", error="Connection timeout", exc_info=True)
```

### Context Logging

```python
from packages.shared.src.logging_config import log_context

# Use context manager for temporary context
with log_context(tenant_id="tenant-123", user_id="user-456", operation="artifact.create"):
    logger.info("Starting artifact creation", artifact_name="test-artifact")
    # All logs within this block will include the context
    logger.info("Artifact created successfully", artifact_id="artifact-789")
```

### Binding Context

```python
from packages.shared.src.logging_config import bind_context

# Bind context for the current execution
bind_context(correlation_id="req-123", tenant_id="tenant-456")
logger.info("Processing request")  # Will include bound context
```

### Decorators

```python
from packages.shared.src.logging_config import with_async_operation

@with_async_operation("user.authenticate")
async def authenticate_user(email: str, password: str):
    logger.info("Authenticating user", email=email)
    # Operation context is automatically added
```

## API Service Integration

### Request Middleware

The API service includes middleware that automatically adds correlation IDs and context:

```python
@app.middleware("http")
async def add_correlation_id_middleware(request: Request, call_next):
    correlation_id = str(uuid.uuid4())
    
    # Extract tenant and user context
    tenant_id = getattr(request.state, 'tenant_id', None)
    user_id = getattr(request.state, 'user_id', None)
    
    # Bind context for the request lifecycle
    with structlog.contextvars.bound_contextvars(
        correlation_id=correlation_id,
        tenant_id=tenant_id,
        user_id=user_id
    ):
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
```

### Route Handlers

Route handlers use context logging for business operations:

```python
@router.post("/artifacts")
async def create_artifact(artifact_data: CreateArtifactRequest, ...):
    with log_context(
        tenant_id=workspace_id,
        user_id=current_user.id,
        operation="artifact.create"
    ):
        logger.info("Creating artifact", artifact_name=artifact_data.name)
        # Business logic here
        logger.info("Artifact created successfully", artifact_id=str(new_artifact.id))
```

## Worker Service Integration

### Task Context

Celery tasks automatically extract context from task arguments:

```python
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    # Extract context from task kwargs
    tenant_id = kwargs.get("tenant_id") if kwargs else None
    user_id = kwargs.get("user_id") if kwargs else None
    
    # Bind context for task execution
    bind_context(
        task_id=task_id,
        tenant_id=tenant_id,
        user_id=user_id,
        operation=f"task.{task.name}"
    )
```

### Task Implementation

Tasks use context logging for operations:

```python
@celery_app.task(bind=True, name="send_verification_email")
def send_verification_email(self, user_id: str, email: str, verification_token: str):
    with log_context(
        user_id=user_id,
        operation="email.send_verification",
        email_type="verification"
    ):
        logger.info("Sending verification email", email=email)
        # Email sending logic
        logger.info("Verification email sent successfully")
```

## Log Rotation

Log rotation is configured automatically:

- **File size limit**: 10MB per log file (configurable)
- **Backup count**: 5 backup files (configurable)
- **Rotation format**: `api.log`, `api.log.1`, `api.log.2`, etc.
- **Encoding**: UTF-8

## File Locations

- **API logs**: `services/api/logs/api.log`
- **Worker logs**: `services/worker/logs/worker.log`
- **Test logs**: `services/*/logs/*_test.log`

## Configuration Options

The logging configuration supports the following options:

```python
configure_structured_logging(
    service_name="api",           # Service identifier
    log_level="INFO",             # Minimum log level
    log_file="logs/api.log",      # Log file path (optional)
    enable_console=True,          # Console output
    enable_rotation=True,         # Log rotation
    max_log_size_mb=10,          # Max file size before rotation
    backup_count=5               # Number of backup files
)
```

## Best Practices

### 1. Use Consistent Field Names

- Use snake_case for field names
- Use consistent naming across services
- Include units in field names (e.g., `duration_ms`, `size_bytes`)

### 2. Include Context

- Always include tenant_id for multi-tenant operations
- Include user_id for user-specific operations
- Use correlation_id for request tracing

### 3. Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational information
- **WARNING**: Something unexpected but not an error
- **ERROR**: Error conditions that need attention
- **CRITICAL**: Serious errors that may cause service failure

### 4. Error Logging

Always include exception information for errors:

```python
try:
    # Some operation
    pass
except Exception as e:
    logger.error(
        "Operation failed",
        error=str(e),
        error_type=type(e).__name__,
        exc_info=True  # Include stack trace
    )
```

### 5. Performance Logging

Include timing information for performance monitoring:

```python
start_time = time.time()
# Operation
duration_ms = int((time.time() - start_time) * 1000)
logger.info("Operation completed", duration_ms=duration_ms)
```

## Testing

Test scripts are provided to verify logging functionality:

- `services/api/test_logging.py` - API service logging tests
- `services/worker/test_logging.py` - Worker service logging tests

Run tests with:

```bash
cd services/api && python test_logging.py
cd services/worker && python test_logging.py
```

## Integration with Observability

The structured logs integrate with the platform's observability stack:

- **Correlation IDs** match OpenTelemetry trace IDs
- **JSON format** is easily parsed by log aggregation systems
- **Context fields** provide filtering and grouping capabilities
- **Consistent timestamps** enable time-series analysis

This structured logging implementation provides comprehensive observability for the Ghostworks SaaS platform while maintaining consistency and ease of use across all services.