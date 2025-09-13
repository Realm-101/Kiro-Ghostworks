# OpenTelemetry Instrumentation

This document describes the OpenTelemetry instrumentation setup for the Ghostworks API service.

## Overview

The API service is fully instrumented with OpenTelemetry for:
- **Distributed Tracing**: Custom spans for business operations
- **Metrics Collection**: Business and technical metrics
- **Automatic Instrumentation**: FastAPI, SQLAlchemy, HTTPX, and Requests

## Configuration

OpenTelemetry is configured in `telemetry.py` and automatically initialized when the service starts.

### Environment Variables

- `OTEL_EXPORTER_OTLP_ENDPOINT`: OpenTelemetry Collector endpoint (default: `http://otelcol:4317`)
- `ENVIRONMENT`: Deployment environment (development, staging, production)

## Automatic Instrumentation

The following libraries are automatically instrumented:

- **FastAPI**: HTTP request/response tracing
- **SQLAlchemy**: Database query tracing
- **HTTPX**: HTTP client request tracing
- **Requests**: HTTP client request tracing

## Custom Spans

Custom spans are added to key business operations:

### Authentication Operations
- `auth.login`: User login attempts with success/failure tracking
- `auth.register`: User registration process
- `auth.refresh`: Token refresh operations

### Artifact Operations
- `artifact.create`: Artifact creation with tenant and user context
- `artifact.list`: Artifact listing with search parameters
- `artifact.update`: Artifact updates
- `artifact.delete`: Artifact deletion

### Span Attributes

All custom spans include relevant attributes:
- `tenant.id`: Tenant/workspace identifier
- `user.id`: User identifier
- `operation.success`: Success/failure status
- `error.message`: Error details (on failure)

## Business Metrics

Custom business metrics are collected:

### Counters
- `artifacts_created_total`: Total artifacts created by tenant
- `auth_attempts_total`: Authentication attempts by success/method
- `workspace_operations_total`: Workspace operations by type

### Histograms
- `artifact_operation_duration_seconds`: Duration of artifact operations

## Usage Example

```python
from telemetry import get_tracer, business_telemetry

tracer = get_tracer(__name__)

# Custom span
with tracer.start_as_current_span("my.operation") as span:
    span.set_attribute("tenant.id", tenant_id)
    span.set_attribute("operation.type", "create")
    
    # Your business logic here
    
    # Record business metric
    business_telemetry.record_artifact_created(
        tenant_id=tenant_id,
        user_id=user_id,
        artifact_type="document"
    )
```

## Observability Stack

The instrumentation works with the following observability stack:

- **OpenTelemetry Collector**: Receives and processes telemetry data
- **Prometheus**: Metrics storage and querying
- **Grafana**: Dashboards and visualization
- **Jaeger**: Distributed tracing (optional)

## Development

When running locally without the full Docker stack, you may see connection errors to the OpenTelemetry Collector. This is expected and doesn't affect functionality - the instrumentation will retry and eventually timeout gracefully.

To test the instrumentation:

```bash
# Start the full Docker stack
docker-compose up -d

# Check OpenTelemetry Collector logs
docker logs ghostworks-otelcol

# View metrics in Prometheus
open http://localhost:9090

# View dashboards in Grafana
open http://localhost:3001
```