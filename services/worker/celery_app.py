"""
Celery application configuration for Ghostworks Worker.
Handles task routing, error handling, and observability.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from celery import Celery
from celery.signals import worker_init, worker_shutdown, task_prerun, task_postrun, task_failure
import structlog

from .config import get_worker_settings
from packages.shared.src.logging_config import get_logger, bind_context, log_context

logger = get_logger(__name__)

# Get worker settings
settings = get_worker_settings()

# Create Celery application
celery_app = Celery(
    "ghostworks_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "services.worker.tasks.email_tasks",
        "services.worker.tasks.data_tasks",
        "services.worker.tasks.maintenance_tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    # Serialization
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    
    # Timezone
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    
    # Task execution
    task_track_started=settings.celery_task_track_started,
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    
    # Worker configuration
    worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
    worker_max_tasks_per_child=settings.celery_worker_max_tasks_per_child,
    
    # Task routing
    task_routes={
        "services.worker.tasks.email_tasks.*": {"queue": "email"},
        "services.worker.tasks.data_tasks.*": {"queue": "data_processing"},
        "services.worker.tasks.maintenance_tasks.*": {"queue": "maintenance"},
    },
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


# Signal handlers for lifecycle management
@worker_init.connect
def worker_init_handler(sender=None, **kwargs):
    """Initialize worker resources."""
    logger.info(
        "Worker initializing",
        worker_id=sender,
        settings_environment=settings.environment,
    )


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Cleanup worker resources."""
    logger.info("Worker shutting down", worker_id=sender)
    
    # Close database connections
    import asyncio
    from .database import close_database_connections
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(close_database_connections())
        loop.close()
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))


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
    
    logger.info(
        "Task starting",
        task_name=task_name,
        args_count=len(args) if args else 0,
        kwargs_keys=list(kwargs.keys()) if kwargs else [],
    )


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Log task completion."""
    task_name = task.name if task else "unknown"
    
    logger.info(
        "Task completed",
        task_name=task_name,
        state=state,
        has_return_value=retval is not None,
    )


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Log task failure."""
    task_name = sender.name if sender else "unknown"
    
    logger.error(
        "Task failed",
        task_name=task_name,
        exception=str(exception),
        exc_info=True,
    )


# Health check task
@celery_app.task(name="health_check")
def health_check():
    """Health check task for monitoring."""
    return {"status": "healthy", "worker": "ghostworks_worker"}


if __name__ == "__main__":
    celery_app.start()