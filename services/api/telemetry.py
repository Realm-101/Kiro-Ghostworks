"""
OpenTelemetry configuration and instrumentation for Ghostworks API service.
Provides comprehensive tracing, metrics, and logging instrumentation.
"""

import os
from typing import Optional

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import structlog

logger = structlog.get_logger(__name__)


def get_resource() -> Resource:
    """Create OpenTelemetry resource with service information."""
    return Resource.create({
        "service.name": "ghostworks-api",
        "service.version": "0.1.0",
        "service.namespace": "ghostworks",
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        "service.instance.id": os.getenv("HOSTNAME", "unknown"),
    })


def setup_tracing(otlp_endpoint: Optional[str] = None) -> None:
    """Configure OpenTelemetry tracing with OTLP exporter."""
    if not otlp_endpoint:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otelcol:4317")
    
    # Create resource
    resource = get_resource()
    
    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)
    
    # Create OTLP span exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True,  # Use insecure connection for development
    )
    
    # Add batch span processor
    span_processor = BatchSpanProcessor(
        otlp_exporter,
        max_queue_size=2048,
        max_export_batch_size=512,
        export_timeout_millis=30000,
        schedule_delay_millis=5000,
    )
    tracer_provider.add_span_processor(span_processor)
    
    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    logger.info(
        "OpenTelemetry tracing configured",
        otlp_endpoint=otlp_endpoint,
        service_name="ghostworks-api"
    )


def setup_metrics(otlp_endpoint: Optional[str] = None) -> None:
    """Configure OpenTelemetry metrics with OTLP exporter."""
    if not otlp_endpoint:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otelcol:4317")
    
    # Create resource
    resource = get_resource()
    
    # Create OTLP metric exporter
    otlp_exporter = OTLPMetricExporter(
        endpoint=otlp_endpoint,
        insecure=True,  # Use insecure connection for development
    )
    
    # Create metric reader
    metric_reader = PeriodicExportingMetricReader(
        exporter=otlp_exporter,
        export_interval_millis=30000,  # Export every 30 seconds
    )
    
    # Create meter provider
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader]
    )
    
    # Set global meter provider
    metrics.set_meter_provider(meter_provider)
    
    logger.info(
        "OpenTelemetry metrics configured",
        otlp_endpoint=otlp_endpoint,
        service_name="ghostworks-api"
    )


def setup_auto_instrumentation() -> None:
    """Configure automatic instrumentation for common libraries."""
    
    # Instrument FastAPI
    FastAPIInstrumentor().instrument()
    logger.info("FastAPI instrumentation enabled")
    
    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    logger.info("SQLAlchemy instrumentation enabled")
    
    # Instrument HTTPX
    HTTPXClientInstrumentor().instrument()
    logger.info("HTTPX instrumentation enabled")
    
    # Instrument Requests
    RequestsInstrumentor().instrument()
    logger.info("Requests instrumentation enabled")


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance for custom spans."""
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """Get a meter instance for custom metrics."""
    return metrics.get_meter(name)


def setup_telemetry() -> None:
    """Initialize complete OpenTelemetry setup."""
    logger.info("Initializing OpenTelemetry instrumentation")
    
    # Setup tracing and metrics
    setup_tracing()
    setup_metrics()
    
    # Setup automatic instrumentation
    setup_auto_instrumentation()
    
    logger.info("OpenTelemetry instrumentation initialized successfully")


# Custom spans and metrics for business operations
class BusinessTelemetry:
    """Business-specific telemetry instrumentation."""
    
    def __init__(self):
        self.tracer = get_tracer("ghostworks.business")
        self.meter = get_meter("ghostworks.business")
        
        # Create custom metrics
        self.artifacts_created_counter = self.meter.create_counter(
            name="artifacts_created_total",
            description="Total number of artifacts created",
            unit="1"
        )
        
        self.auth_attempts_counter = self.meter.create_counter(
            name="auth_attempts_total",
            description="Total authentication attempts",
            unit="1"
        )
        
        self.workspace_operations_counter = self.meter.create_counter(
            name="workspace_operations_total",
            description="Total workspace operations",
            unit="1"
        )
        
        self.artifact_operations_histogram = self.meter.create_histogram(
            name="artifact_operation_duration_seconds",
            description="Duration of artifact operations",
            unit="s"
        )
    
    def record_artifact_created(self, tenant_id: str, user_id: str, artifact_type: str = "default"):
        """Record artifact creation event."""
        self.artifacts_created_counter.add(
            1,
            attributes={
                "tenant_id": tenant_id,
                "user_id": user_id,
                "artifact_type": artifact_type
            }
        )
    
    def record_auth_attempt(self, success: bool, method: str = "password"):
        """Record authentication attempt."""
        self.auth_attempts_counter.add(
            1,
            attributes={
                "success": str(success).lower(),
                "method": method
            }
        )
    
    def record_workspace_operation(self, operation: str, tenant_id: str, user_id: str):
        """Record workspace operation."""
        self.workspace_operations_counter.add(
            1,
            attributes={
                "operation": operation,
                "tenant_id": tenant_id,
                "user_id": user_id
            }
        )
    
    def time_artifact_operation(self, operation: str, tenant_id: str):
        """Create a context manager for timing artifact operations."""
        return self.artifact_operations_histogram.record(
            attributes={
                "operation": operation,
                "tenant_id": tenant_id
            }
        )


# Global business telemetry instance
business_telemetry = BusinessTelemetry()