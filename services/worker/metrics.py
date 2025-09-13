"""
Prometheus metrics collection for Ghostworks Worker service.
Implements Celery task metrics and custom business metrics.
"""

import time
from typing import Optional, Dict, Any
from functools import wraps

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, REGISTRY, start_http_server
)
from celery.signals import (
    task_prerun, task_postrun, task_failure, task_success,
    worker_ready, worker_shutdown
)
import structlog

logger = structlog.get_logger(__name__)


class WorkerPrometheusMetrics:
    """Prometheus metrics collector for Celery worker."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize Prometheus metrics with optional custom registry."""
        self.registry = registry or REGISTRY
        
        # Celery task metrics
        self.celery_tasks_total = Counter(
            'celery_tasks_total',
            'Total Celery tasks processed',
            ['task_name', 'status', 'queue'],
            registry=self.registry
        )
        
        self.celery_task_duration_seconds = Histogram(
            'celery_task_duration_seconds',
            'Celery task duration in seconds',
            ['task_name', 'queue'],
            buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
            registry=self.registry
        )
        
        self.celery_tasks_in_progress = Gauge(
            'celery_tasks_in_progress',
            'Celery tasks currently being processed',
            ['task_name', 'queue'],
            registry=self.registry
        )
        
        self.celery_task_failures_total = Counter(
            'celery_task_failures_total',
            'Total Celery task failures',
            ['task_name', 'exception_type', 'queue'],
            registry=self.registry
        )
        
        # Business-specific task metrics
        self.email_tasks_total = Counter(
            'email_tasks_total',
            'Total email tasks processed',
            ['task_type', 'status'],
            registry=self.registry
        )
        
        self.data_processing_tasks_total = Counter(
            'data_processing_tasks_total',
            'Total data processing tasks',
            ['task_type', 'records_processed'],
            registry=self.registry
        )
        
        self.maintenance_tasks_total = Counter(
            'maintenance_tasks_total',
            'Total maintenance tasks processed',
            ['task_type', 'status'],
            registry=self.registry
        )
        
        # Worker system metrics
        self.worker_active_tasks = Gauge(
            'worker_active_tasks',
            'Number of active tasks on this worker',
            registry=self.registry
        )
        
        self.worker_processed_tasks_total = Counter(
            'worker_processed_tasks_total',
            'Total tasks processed by this worker',
            registry=self.registry
        )
        
        # Queue metrics
        self.queue_length = Gauge(
            'celery_queue_length',
            'Number of tasks in queue',
            ['queue_name'],
            registry=self.registry
        )
        
        # Application info
        self.app_info = Info(
            'ghostworks_worker_info',
            'Worker application information',
            registry=self.registry
        )
        
        # Set application info
        self.app_info.info({
            'version': '0.1.0',
            'service': 'ghostworks-worker',
            'environment': 'development'
        })
        
        # Task execution tracking
        self._task_start_times: Dict[str, float] = {}
        
        logger.info("Worker Prometheus metrics initialized")
    
    def record_task_start(self, task_name: str, task_id: str, queue: str = "default") -> None:
        """Record the start of a Celery task."""
        self.celery_tasks_in_progress.labels(task_name=task_name, queue=queue).inc()
        self.worker_active_tasks.inc()
        self._task_start_times[task_id] = time.time()
        logger.debug("Task started", task_name=task_name, task_id=task_id, queue=queue)
    
    def record_task_end(self, task_name: str, task_id: str, status: str, queue: str = "default") -> None:
        """Record the end of a Celery task."""
        # Calculate duration
        start_time = self._task_start_times.pop(task_id, time.time())
        duration = time.time() - start_time
        
        # Record metrics
        self.celery_tasks_total.labels(task_name=task_name, status=status, queue=queue).inc()
        self.celery_task_duration_seconds.labels(task_name=task_name, queue=queue).observe(duration)
        self.celery_tasks_in_progress.labels(task_name=task_name, queue=queue).dec()
        self.worker_active_tasks.dec()
        self.worker_processed_tasks_total.inc()
        
        logger.debug(
            "Task completed",
            task_name=task_name,
            task_id=task_id,
            status=status,
            duration=duration,
            queue=queue
        )
    
    def record_task_failure(self, task_name: str, task_id: str, exception_type: str, queue: str = "default") -> None:
        """Record a Celery task failure."""
        self.celery_task_failures_total.labels(
            task_name=task_name,
            exception_type=exception_type,
            queue=queue
        ).inc()
        
        # Also record as completed task with failure status
        self.record_task_end(task_name, task_id, "failure", queue)
        
        logger.warning(
            "Task failed",
            task_name=task_name,
            task_id=task_id,
            exception_type=exception_type,
            queue=queue
        )
    
    def record_email_task(self, task_type: str, status: str) -> None:
        """Record email task execution."""
        self.email_tasks_total.labels(task_type=task_type, status=status).inc()
        logger.debug("Email task recorded", task_type=task_type, status=status)
    
    def record_data_processing_task(self, task_type: str, records_processed: int) -> None:
        """Record data processing task."""
        self.data_processing_tasks_total.labels(
            task_type=task_type,
            records_processed=str(records_processed)
        ).inc()
        logger.debug(
            "Data processing task recorded",
            task_type=task_type,
            records_processed=records_processed
        )
    
    def record_maintenance_task(self, task_type: str, status: str) -> None:
        """Record maintenance task execution."""
        self.maintenance_tasks_total.labels(task_type=task_type, status=status).inc()
        logger.debug("Maintenance task recorded", task_type=task_type, status=status)
    
    def set_queue_length(self, queue_name: str, length: int) -> None:
        """Set the current queue length."""
        self.queue_length.labels(queue_name=queue_name).set(length)
    
    def get_metrics(self) -> str:
        """Generate Prometheus metrics in text format."""
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get Prometheus metrics content type."""
        return CONTENT_TYPE_LATEST


# Global metrics instance
worker_metrics = WorkerPrometheusMetrics()


def setup_celery_metrics_signals():
    """Set up Celery signal handlers for metrics collection."""
    
    @task_prerun.connect
    def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
        """Handle task prerun signal."""
        task_name = sender.name if sender else "unknown"
        queue = getattr(sender, 'queue', 'default') if sender else 'default'
        worker_metrics.record_task_start(task_name, task_id, queue)
    
    @task_postrun.connect
    def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
        """Handle task postrun signal."""
        task_name = sender.name if sender else "unknown"
        queue = getattr(sender, 'queue', 'default') if sender else 'default'
        status = state.lower() if state else "success"
        worker_metrics.record_task_end(task_name, task_id, status, queue)
    
    @task_failure.connect
    def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
        """Handle task failure signal."""
        task_name = sender.name if sender else "unknown"
        queue = getattr(sender, 'queue', 'default') if sender else 'default'
        exception_type = type(exception).__name__ if exception else "UnknownException"
        worker_metrics.record_task_failure(task_name, task_id, exception_type, queue)
    
    @task_success.connect
    def task_success_handler(sender=None, result=None, **kwds):
        """Handle task success signal."""
        # Task success is already handled in postrun with status
        pass
    
    @worker_ready.connect
    def worker_ready_handler(sender=None, **kwds):
        """Handle worker ready signal."""
        logger.info("Worker ready, metrics collection active")
    
    @worker_shutdown.connect
    def worker_shutdown_handler(sender=None, **kwds):
        """Handle worker shutdown signal."""
        logger.info("Worker shutting down, finalizing metrics")
    
    logger.info("Celery metrics signals configured")


def track_task_metric(metric_type: str, **labels):
    """Decorator to track specific task metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Record specific metrics based on task type
                if metric_type == "email_task":
                    task_type = labels.get("task_type", "unknown")
                    worker_metrics.record_email_task(task_type, "success")
                elif metric_type == "data_processing_task":
                    task_type = labels.get("task_type", "unknown")
                    records = labels.get("records_processed", 0)
                    worker_metrics.record_data_processing_task(task_type, records)
                elif metric_type == "maintenance_task":
                    task_type = labels.get("task_type", "unknown")
                    worker_metrics.record_maintenance_task(task_type, "success")
                
                return result
                
            except Exception as e:
                # Record failure metrics
                if metric_type == "email_task":
                    task_type = labels.get("task_type", "unknown")
                    worker_metrics.record_email_task(task_type, "failure")
                elif metric_type == "maintenance_task":
                    task_type = labels.get("task_type", "unknown")
                    worker_metrics.record_maintenance_task(task_type, "failure")
                
                raise e
        
        return wrapper
    return decorator


def start_metrics_server(port: int = 8001):
    """Start HTTP server to expose Prometheus metrics."""
    try:
        start_http_server(port, registry=worker_metrics.registry)
        logger.info(f"Worker metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")


def get_queue_inspector():
    """Get Celery queue inspector for monitoring queue lengths."""
    try:
        from celery_app import celery_app
        return celery_app.control.inspect()
    except ImportError:
        logger.warning("Could not import celery_app for queue inspection")
        return None


def update_queue_metrics():
    """Update queue length metrics."""
    inspector = get_queue_inspector()
    if not inspector:
        return
    
    try:
        # Get active queues
        active_queues = inspector.active_queues()
        if active_queues:
            for worker, queues in active_queues.items():
                for queue_info in queues:
                    queue_name = queue_info.get('name', 'default')
                    # Note: This gets active queues, not queue length
                    # For actual queue length, we'd need Redis inspection
                    worker_metrics.set_queue_length(queue_name, 0)  # Placeholder
    
    except Exception as e:
        logger.warning(f"Failed to update queue metrics: {e}")