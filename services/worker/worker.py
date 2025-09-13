"""
Main Celery worker entry point for Ghostworks SaaS.
Handles task execution with proper error handling and observability.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Initialize OpenTelemetry before other imports
from services.worker.telemetry import setup_telemetry
setup_telemetry()

# Initialize Prometheus metrics
from services.worker.metrics import setup_celery_metrics_signals, start_metrics_server
setup_celery_metrics_signals()

import structlog
from celery import Celery
from celery.signals import setup_logging

from services.worker.celery_app import celery_app
from services.worker.config import get_worker_settings

# Configure structured logging
from packages.shared.src.logging_config import configure_structured_logging, get_logger

# Configure logging
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


def main():
    """Main entry point for the Celery worker."""
    settings = get_worker_settings()
    
    logger = get_logger(__name__)
    logger.info(
        "Starting Ghostworks Celery worker",
        environment=settings.environment,
        broker_url=settings.celery_broker_url,
        result_backend=settings.celery_result_backend,
        log_level=settings.log_level,
    )
    
    # Start metrics server
    start_metrics_server(port=8001)
    
    # Start the Celery worker
    celery_app.start([
        'worker',
        '--loglevel=INFO',
        '--concurrency=4',
        '--queues=email,data_processing,maintenance',
        '--hostname=ghostworks-worker@%h',
    ])


if __name__ == "__main__":
    main()