"""
Shared structured logging configuration for Ghostworks SaaS Platform.
Provides consistent JSON logging with correlation IDs, tenant context, and log rotation.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from structlog.types import EventDict, Processor


def add_service_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add service name to log context."""
    service_name = os.getenv("SERVICE_NAME", "unknown")
    event_dict["service"] = service_name
    return event_dict


def add_correlation_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add correlation ID from context variables."""
    # Get correlation ID from structlog context variables
    correlation_id = structlog.contextvars.get_contextvars().get("correlation_id")
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def add_tenant_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add tenant and user context from context variables."""
    context_vars = structlog.contextvars.get_contextvars()
    
    tenant_id = context_vars.get("tenant_id")
    if tenant_id:
        event_dict["tenant_id"] = tenant_id
    
    user_id = context_vars.get("user_id")
    if user_id:
        event_dict["user_id"] = user_id
    
    return event_dict


def add_operation_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add operation name from context variables."""
    operation = structlog.contextvars.get_contextvars().get("operation")
    if operation:
        event_dict["operation"] = operation
    return event_dict


def setup_log_rotation(
    log_file: str,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Handler:
    """
    Set up rotating file handler for logs.
    
    Args:
        log_file: Path to log file
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    
    Returns:
        Configured rotating file handler
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create rotating file handler
    handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    return handler


def configure_structured_logging(
    service_name: str,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_rotation: bool = True,
    max_log_size_mb: int = 10,
    backup_count: int = 5
) -> None:
    """
    Configure structured logging for the service.
    
    Args:
        service_name: Name of the service (api, worker, etc.)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        enable_console: Whether to enable console logging
        enable_rotation: Whether to enable log rotation
        max_log_size_mb: Maximum log file size in MB before rotation
        backup_count: Number of backup files to keep
    """
    # Set service name in environment for processors
    os.environ["SERVICE_NAME"] = service_name
    
    # Configure processors
    processors: list[Processor] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_service_context,
        add_correlation_id,
        add_tenant_context,
        add_operation_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add JSON renderer for structured output
    processors.append(structlog.processors.JSONRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    handlers = []
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        handlers.append(console_handler)
    
    # File handler with rotation
    if log_file:
        if enable_rotation:
            file_handler = setup_log_rotation(
                log_file=log_file,
                max_bytes=max_log_size_mb * 1024 * 1024,
                backup_count=backup_count
            )
        else:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
        
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        format='%(message)s'
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


def bind_context(**kwargs) -> None:
    """
    Bind context variables for the current execution context.
    
    Args:
        **kwargs: Context variables to bind (tenant_id, user_id, operation, etc.)
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all context variables."""
    structlog.contextvars.clear_contextvars()


def with_operation(operation: str):
    """
    Decorator to add operation context to function calls.
    
    Args:
        operation: Operation name to add to logs
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with structlog.contextvars.bound_contextvars(operation=operation):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def with_async_operation(operation: str):
    """
    Decorator to add operation context to async function calls.
    
    Args:
        operation: Operation name to add to logs
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with structlog.contextvars.bound_contextvars(operation=operation):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


# Context managers for temporary context binding
class LogContext:
    """Context manager for temporary log context binding."""
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self.previous_context = None
    
    def __enter__(self):
        self.previous_context = structlog.contextvars.get_contextvars().copy()
        structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        structlog.contextvars.clear_contextvars()
        if self.previous_context:
            structlog.contextvars.bind_contextvars(**self.previous_context)


def log_context(**kwargs):
    """
    Create a log context manager.
    
    Usage:
        with log_context(tenant_id="123", operation="create_artifact"):
            logger.info("Creating artifact")
    """
    return LogContext(**kwargs)