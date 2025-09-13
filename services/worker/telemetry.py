"""
OpenTelemetry configuration and instrumentation for Ghostworks Worker service.
Provides comprehensive tracing, metrics, and logging instrumentation for Celery tasks.
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
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import structlog

logger = structlog.get_logger(__name__)


def get_resource() -> Resource:
    """Create OpenTelemetry resource with service information."""
    return Resource.create({
        "service.name": "ghostworks-worker",
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
        service_name="ghostworks-worker"
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
        service_name="ghostworks-worker"
    )


def setup_auto_instrumentation() -> None:
    """Configure automatic instrumentation for common libraries."""
    
    # Instrument Celery
    CeleryInstrumentor().instrument()
    logger.info("Celery instrumentation enabled")
    
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
    logger.info("Initializing OpenTelemetry instrumentation for worker")
    
    # Setup tracing and metrics
    setup_tracing()
    setup_metrics()
    
    # Setup automatic instrumentation
    setup_auto_instrumentation()
    
    logger.info("OpenTelemetry instrumentation initialized successfully for worker")


# Custom spans and metrics for worker operations
class WorkerTelemetry:
    """Worker-specific telemetry instrumentation."""
    
    def __init__(self):
        self.tracer = get_tracer("ghostworks.worker")
        self.meter = get_meter("ghostworks.worker")
        
        # Create custom metrics
        self.tasks_processed_counter = self.meter.create_counter(
            name="celery_tasks_processed_total",
            description="Total number of Celery tasks processed",
            unit="1"
        )
        
        self.task_duration_histogram = self.meter.create_histogram(
            name="celery_task_duration_seconds",
            description="Duration of Celery task execution",
            unit="s"
        )
        
        self.email_tasks_counter = self.meter.create_counter(
            name="email_tasks_total",
            description="Total email tasks processed",
            unit="1"
        )
        
        self.data_processing_tasks_counter = self.meter.create_counter(
            name="data_processing_tasks_total",
            description="Total data processing tasks",
            unit="1"
        )
    
    def record_task_processed(self, task_name: str, status: str, queue: str = "default"):
        """Record task processing event."""
        self.tasks_processed_counter.add(
            1,
            attributes={
                "task_name": task_name,
                "status": status,
                "queue": queue
            }
        )
    
    def record_email_task(self, task_type: str, success: bool):
        """Record email task execution."""
        self.email_tasks_counter.add(
            1,
            attributes={
                "task_type": task_type,
                "success": str(success).lower()
            }
        )
    
    def record_data_processing_task(self, task_type: str, records_processed: int):
        """Record data processing task."""
        self.data_processing_tasks_counter.add(
            1,
            attributes={
                "task_type": task_type,
                "records_processed": str(records_processed)
            }
        )
    
    def time_task_execution(self, task_name: str, queue: str = "default"):
        """Create a context manager for timing task execution."""
        return self.task_duration_histogram.record(
            attributes={
                "task_name": task_name,
                "queue": queue
            }
        )


# Global worker telemetry instance
worker_telemetry = WorkerTelemetry()