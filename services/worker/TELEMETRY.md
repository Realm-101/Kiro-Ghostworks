# OpenTelemetry Instrumentation - Worker Service

This document describes the OpenTelemetry instrumentation setup for the Ghostworks Worker service.

## Overview

The Worker service is fully instrumented with OpenTelemetry for:
- **Distributed Tracing**: Custom spans for task execution
- **Metrics Collection**: Task performance and business metrics
- **Automatic Instrumentation**: Celery, SQLAlchemy, HTTPX, and Requests

## Configuration

OpenTelemetry is configured in `telemetry.py` and automatically initialized when the worker starts.

### Environment Variables

- `OTEL_EXPORTER_OTLP_ENDPOINT`: OpenTelemetry Collector endpoint (default: `http://otelcol:4317`)
- `ENVIRONMENT`: Deployment environment (development, staging, production)

## Automatic Instrumentation

The following libraries are automatically instrumented:

- **Celery**: Task execution tracing with automatic span creation
- **SQLAlchemy**: Database query tracing
- **HTTPX**: HTTP client request tracing
- **Requests**: HTTP client request tracing

## Custom Spans

Custom spans are added to key task operations:

### Email Tasks
- `email.send_verification`: Email verification sending
- `email.send_password_reset`: Password reset email sending
- `email.send_workspace_invitation`: Workspace invitation emails

### Data Processing Tasks
- `data.process_batch`: Batch data processing
- `data.cleanup`: Data cleanup operations
- `data.export`: Data export tasks

### Span Attributes

All custom spans include relevant attributes:
- `task.id`: Celery task identifier
- `task.name`: Task name
- `queue`: Task queue name
- `user.id`: User identifier (when applicable)
- `email.type`: Email type for email tasks
- `email.success`: Email sending success status

## Business Metrics

Custom business metrics are collected:

### Counters
- `celery_tasks_processed_total`: Total tasks processed by name/status/queue
- `email_tasks_total`: Email tasks by type and success status
- `data_processing_tasks_total`: Data processing tasks by type

### Histograms
- `celery_task_duration_seconds`: Task execution duration by name/queue

## Usage Example

```python
from telemetry import get_tracer, worker_telemetry

tracer = get_tracer(__name__)

@celery_app.task(bind=True)
def my_task(self, data):
    with tracer.start_as_current_span("task.my_operation") as span:
        span.set_attribute("task.id", self.request.id)
        span.set_attribute("data.size", len(data))
        
        try:
            # Your task logic here
            result = process_data(data)
            
            # Record success metrics
            worker_telemetry.record_task_processed(
                task_name="my_task",
                status="success",
                queue="default"
            )
            
            span.set_attribute("task.success", True)
            return result
            
        except Exception as e:
            # Record failure metrics
            worker_telemetry.record_task_processed(
                task_name="my_task",
                status="failed",
                queue="default"
            )
            
            span.set_attribute("task.success", False)
            span.set_attribute("error.message", str(e))
            raise
```

## Task Correlation

Worker tasks are automatically correlated with API requests through:
- Request IDs passed as task arguments
- Trace context propagation
- Shared tenant/user identifiers

## Observability Stack

The instrumentation works with the following observability stack:

- **OpenTelemetry Collector**: Receives and processes telemetry data
- **Prometheus**: Metrics storage and querying
- **Grafana**: Dashboards and visualization
- **Jaeger**: Distributed tracing (optional)

## Development

When running locally without the full Docker stack, you may see connection errors to the OpenTelemetry Collector. This is expected and doesn't affect functionality.

To test the instrumentation:

```bash
# Start the full Docker stack
docker-compose up -d

# Check worker logs
docker logs ghostworks-worker

# Check OpenTelemetry Collector logs
docker logs ghostworks-otelcol

# View metrics in Prometheus
open http://localhost:9090

# View dashboards in Grafana
open http://localhost:3001
```

## Celery Integration

The Celery instrumentation automatically:
- Creates spans for each task execution
- Tracks task state changes (PENDING, STARTED, SUCCESS, FAILURE)
- Correlates tasks with their producers
- Measures task execution time
- Records task retry attempts