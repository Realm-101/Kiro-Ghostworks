# Worker Service Structured Logging

This document describes the structured logging implementation specific to the Ghostworks Worker service.

## Overview

The Worker service uses the shared structured logging configuration with Celery-specific enhancements for task tracking and context management.

## Celery Integration

### Signal Handlers

The worker service uses Celery signals to automatically manage logging context:

```python
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Log task start with context binding."""
    task_name = task.name if task else "unknown"
    
    # Extract tenant_id and user_id from task kwargs if available
    tenant_id = kwargs.get("tenant_id") if kwargs else None
    user_id = kwargs.get("user_id") if kwargs else None
    
    # Bind context for the task execution
    context = {
        "task_id": task_id,
        "operation": f"task.{task_name}",
    }
    
    if tenant_id:
        context["tenant_id"] = str(tenant_id)
    if user_id:
        context["user_id"] = str(user_id)
    
    bind_context(**context)
    
    logger.info("Task starting", task_name=task_name)
```

### Task Implementation

Tasks should pass tenant and user context in their arguments:

```python
# When calling a task
send_verification_email.delay(
    user_id="user-123",
    email="user@example.com",
    verification_token="token-456",
    tenant_id="tenant-789"  # Include for context
)

# Task implementation
@celery_app.task(bind=True, name="send_verification_email")
def send_verification_email(self, user_id: str, email: str, verification_token: str, tenant_id: str = None):
    with log_context(
        user_id=user_id,
        tenant_id=tenant_id,
        operation="email.send_verification",
        email_type="verification"
    ):
        logger.info("Sending verification email", email=email)
        # Task logic here
```

## Task Logging Examples

### Email Tasks

```python
@celery_app.task(bind=True, name="send_verification_email")
def send_verification_email(self, user_id: str, email: str, verification_token: str):
    with log_context(
        user_id=user_id,
        operation="email.send_verification",
        email_type="verification",
        email_recipient=email
    ):
        try:
            logger.info("Sending verification email", email=email)
            # Email sending logic
            logger.info("Verification email sent successfully")
            
            return {"status": "success", "user_id": user_id}
            
        except Exception as e:
            logger.error(
                "Failed to send verification email",
                error=str(e),
                exc_info=True
            )
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
```

### Data Processing Tasks

```python
@celery_app.task(bind=True, name="process_artifact_data")
def process_artifact_data(self, artifact_id: str, tenant_id: str, user_id: str):
    with log_context(
        tenant_id=tenant_id,
        user_id=user_id,
        operation="data.process_artifact",
        artifact_id=artifact_id
    ):
        logger.info("Starting artifact data processing")
        
        try:
            # Processing logic
            logger.info("Artifact processing completed", processing_time_ms=1500)
            
        except Exception as e:
            logger.error(
                "Artifact processing failed",
                error=str(e),
                exc_info=True
            )
            raise
```

### Maintenance Tasks

```python
@celery_app.task(bind=True, name="cleanup_expired_tokens")
def cleanup_expired_tokens(self):
    with log_context(operation="maintenance.cleanup_tokens"):
        logger.info("Starting token cleanup")
        
        # Cleanup logic
        expired_count = 42  # Example
        
        logger.info(
            "Token cleanup completed",
            expired_tokens_removed=expired_count,
            cleanup_duration_ms=2300
        )
```

## Log Output Examples

### Task Start

```json
{
  "timestamp": "2025-09-12T20:05:03.001184Z",
  "level": "info",
  "service": "worker",
  "logger": "services.worker.celery_app",
  "event": "Task starting",
  "task_id": "task-123e4567-e89b-12d3-a456-426614174000",
  "operation": "task.send_verification_email",
  "task_name": "send_verification_email",
  "args_count": 3,
  "kwargs_keys": ["tenant_id"]
}
```

### Task Execution

```json
{
  "timestamp": "2025-09-12T20:05:03.002182Z",
  "level": "info",
  "service": "worker",
  "logger": "services.worker.tasks.email_tasks",
  "event": "Sending verification email",
  "task_id": "task-123e4567-e89b-12d3-a456-426614174000",
  "tenant_id": "tenant-456",
  "user_id": "user-789",
  "operation": "email.send_verification",
  "email_type": "verification",
  "email_recipient": "user@example.com",
  "email": "user@example.com"
}
```

### Task Completion

```json
{
  "timestamp": "2025-09-12T20:05:03.005182Z",
  "level": "info",
  "service": "worker",
  "logger": "services.worker.celery_app",
  "event": "Task completed",
  "task_id": "task-123e4567-e89b-12d3-a456-426614174000",
  "task_name": "send_verification_email",
  "state": "SUCCESS",
  "has_return_value": true
}
```

### Task Failure

```json
{
  "timestamp": "2025-09-12T20:05:03.008182Z",
  "level": "error",
  "service": "worker",
  "logger": "services.worker.celery_app",
  "event": "Task failed",
  "task_id": "task-123e4567-e89b-12d3-a456-426614174000",
  "task_name": "send_verification_email",
  "exception": "ConnectionError: SMTP server unavailable",
  "exception": "Traceback (most recent call last):\n  File \"...\", line 45, in send_verification_email\n    smtp.send(message)\nConnectionError: SMTP server unavailable"
}
```

## Best Practices for Worker Logging

### 1. Include Task Context

Always include relevant context in task arguments:

```python
# Good
send_email.delay(
    user_id="user-123",
    email="user@example.com",
    tenant_id="tenant-456"  # Include for logging context
)

# Better - use kwargs for context
send_email.delay(
    "user@example.com",
    user_id="user-123",
    tenant_id="tenant-456"
)
```

### 2. Use Operation-Specific Context

```python
with log_context(
    operation="email.send_verification",  # Specific operation
    email_type="verification",            # Operation details
    email_recipient=email                 # Relevant data
):
    # Task logic
```

### 3. Log Task Progress

For long-running tasks, log progress:

```python
@celery_app.task(bind=True)
def process_large_dataset(self, dataset_id: str, tenant_id: str):
    with log_context(
        tenant_id=tenant_id,
        operation="data.process_dataset",
        dataset_id=dataset_id
    ):
        logger.info("Starting dataset processing", total_records=10000)
        
        for i, record in enumerate(records):
            if i % 1000 == 0:
                logger.info("Processing progress", processed_records=i, total_records=10000)
            
            # Process record
        
        logger.info("Dataset processing completed", total_processed=10000)
```

### 4. Handle Retries Properly

```python
@celery_app.task(bind=True, max_retries=3)
def unreliable_task(self, data: dict):
    try:
        # Task logic
        logger.info("Task completed successfully")
        
    except Exception as e:
        retry_count = self.request.retries
        max_retries = self.max_retries
        
        logger.warning(
            "Task failed, retrying",
            error=str(e),
            retry_count=retry_count,
            max_retries=max_retries
        )
        
        if retry_count >= max_retries:
            logger.error(
                "Task failed permanently after max retries",
                error=str(e),
                retry_count=retry_count,
                exc_info=True
            )
            raise
        
        raise self.retry(
            exc=e,
            countdown=60 * (2 ** retry_count)  # Exponential backoff
        )
```

### 5. Log Resource Usage

For resource-intensive tasks:

```python
import psutil
import time

@celery_app.task(bind=True)
def resource_intensive_task(self, data: dict):
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss
    
    with log_context(operation="data.intensive_processing"):
        logger.info("Starting resource-intensive task", data_size=len(data))
        
        # Task logic
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        logger.info(
            "Task completed",
            duration_ms=int((end_time - start_time) * 1000),
            memory_used_mb=int((end_memory - start_memory) / 1024 / 1024)
        )
```

## Configuration

The worker service logging is configured in `worker.py`:

```python
@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Configure structured logging for Celery."""
    settings = get_worker_settings()
    
    configure_structured_logging(
        service_name="worker",
        log_level=settings.log_level,
        log_file="logs/worker.log",
        enable_console=True,
        enable_rotation=True,
        max_log_size_mb=10,
        backup_count=5
    )
```

## Testing

Test the worker logging with:

```bash
cd services/worker
python test_logging.py
```

This will create test logs in `logs/worker_test.log` demonstrating all logging features.

## Integration with Monitoring

Worker logs integrate with the platform's monitoring stack:

- **Task IDs** correlate with OpenTelemetry traces
- **Tenant context** enables per-tenant monitoring
- **Error logs** trigger alerts in monitoring systems
- **Performance metrics** feed into dashboards

The structured logging provides comprehensive visibility into worker task execution, failures, and performance characteristics.