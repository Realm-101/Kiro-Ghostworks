"""
Prometheus metrics collection for Ghostworks API service.
Implements golden signals and custom business metrics.
"""

import time
from typing import Dict, Any, Optional
from functools import wraps

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, REGISTRY
)
from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse
import structlog

logger = structlog.get_logger(__name__)


class PrometheusMetrics:
    """Prometheus metrics collector for FastAPI application."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize Prometheus metrics with optional custom registry."""
        self.registry = registry or REGISTRY
        
        # Golden Signals - Request metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
            registry=self.registry
        )
        
        self.http_requests_in_progress = Gauge(
            'http_requests_in_progress',
            'HTTP requests currently being processed',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Custom Business Metrics
        self.artifacts_created_total = Counter(
            'artifacts_created_total',
            'Total artifacts created',
            ['tenant_id'],
            registry=self.registry
        )
        
        self.user_registrations_total = Counter(
            'user_registrations_total',
            'Total user registrations',
            registry=self.registry
        )
        
        self.authentication_attempts_total = Counter(
            'authentication_attempts_total',
            'Total authentication attempts',
            ['success', 'method'],
            registry=self.registry
        )
        
        self.workspace_operations_total = Counter(
            'workspace_operations_total',
            'Total workspace operations',
            ['operation', 'tenant_id'],
            registry=self.registry
        )
        
        self.artifact_search_duration_seconds = Histogram(
            'artifact_search_duration_seconds',
            'Duration of artifact search operations',
            ['tenant_id'],
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
            registry=self.registry
        )
        
        # System metrics
        self.database_connections_active = Gauge(
            'database_connections_active',
            'Active database connections',
            registry=self.registry
        )
        
        self.database_query_duration_seconds = Histogram(
            'database_query_duration_seconds',
            'Database query duration in seconds',
            ['operation'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
            registry=self.registry
        )
        
        # Application info
        self.app_info = Info(
            'ghostworks_api_info',
            'Application information',
            registry=self.registry
        )
        
        # Set application info
        self.app_info.info({
            'version': '0.1.0',
            'service': 'ghostworks-api',
            'environment': 'development'
        })
        
        logger.info("Prometheus metrics initialized")
    
    def record_request_start(self, method: str, endpoint: str) -> None:
        """Record the start of an HTTP request."""
        self.http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
    
    def record_request_end(self, method: str, endpoint: str, status_code: int, duration: float) -> None:
        """Record the end of an HTTP request."""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        self.http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
    
    def record_artifact_created(self, tenant_id: str) -> None:
        """Record artifact creation."""
        self.artifacts_created_total.labels(tenant_id=tenant_id).inc()
        logger.debug("Recorded artifact creation", tenant_id=tenant_id)
    
    def record_user_registration(self) -> None:
        """Record user registration."""
        self.user_registrations_total.inc()
        logger.debug("Recorded user registration")
    
    def record_authentication_attempt(self, success: bool, method: str = "password") -> None:
        """Record authentication attempt."""
        self.authentication_attempts_total.labels(
            success=str(success).lower(),
            method=method
        ).inc()
        logger.debug("Recorded authentication attempt", success=success, method=method)
    
    def record_workspace_operation(self, operation: str, tenant_id: str) -> None:
        """Record workspace operation."""
        self.workspace_operations_total.labels(
            operation=operation,
            tenant_id=tenant_id
        ).inc()
        logger.debug("Recorded workspace operation", operation=operation, tenant_id=tenant_id)
    
    def time_artifact_search(self, tenant_id: str):
        """Context manager for timing artifact search operations."""
        return self.artifact_search_duration_seconds.labels(tenant_id=tenant_id).time()
    
    def record_database_query(self, operation: str, duration: float) -> None:
        """Record database query duration."""
        self.database_query_duration_seconds.labels(operation=operation).observe(duration)
    
    def set_database_connections(self, count: int) -> None:
        """Set current database connection count."""
        self.database_connections_active.set(count)
    
    def get_metrics(self) -> str:
        """Generate Prometheus metrics in text format."""
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get Prometheus metrics content type."""
        return CONTENT_TYPE_LATEST


# Global metrics instance
metrics = PrometheusMetrics()


def get_endpoint_name(request: Request) -> str:
    """Extract endpoint name from request for metrics labeling."""
    # Get the route pattern if available
    if hasattr(request, 'route') and request.route:
        return request.route.path
    
    # Fallback to path with parameter normalization
    path = request.url.path
    
    # Normalize common patterns
    if path.startswith('/api/v1/artifacts/') and len(path.split('/')) > 4:
        return '/api/v1/artifacts/{id}'
    elif path.startswith('/api/v1/workspaces/') and len(path.split('/')) > 4:
        return '/api/v1/workspaces/{id}'
    
    return path


async def prometheus_middleware(request: Request, call_next):
    """Middleware to collect HTTP request metrics."""
    method = request.method
    endpoint = get_endpoint_name(request)
    
    # Record request start
    metrics.record_request_start(method, endpoint)
    start_time = time.time()
    
    try:
        # Process request
        response = await call_next(request)
        
        # Record successful request
        duration = time.time() - start_time
        metrics.record_request_end(method, endpoint, response.status_code, duration)
        
        return response
        
    except Exception as e:
        # Record failed request
        duration = time.time() - start_time
        metrics.record_request_end(method, endpoint, 500, duration)
        raise e


def track_business_metric(metric_name: str, **labels):
    """Decorator to track business metrics on function calls."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # Record metric based on function result
                if metric_name == "artifact_created" and "tenant_id" in labels:
                    metrics.record_artifact_created(labels["tenant_id"])
                elif metric_name == "user_registration":
                    metrics.record_user_registration()
                elif metric_name == "authentication_attempt":
                    success = labels.get("success", True)
                    method = labels.get("method", "password")
                    metrics.record_authentication_attempt(success, method)
                elif metric_name == "workspace_operation":
                    operation = labels.get("operation", "unknown")
                    tenant_id = labels.get("tenant_id", "unknown")
                    metrics.record_workspace_operation(operation, tenant_id)
                
                return result
                
            except Exception as e:
                # Record failure metrics if applicable
                if metric_name == "authentication_attempt":
                    metrics.record_authentication_attempt(False, labels.get("method", "password"))
                raise e
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Record metric based on function result
                if metric_name == "artifact_created" and "tenant_id" in labels:
                    metrics.record_artifact_created(labels["tenant_id"])
                elif metric_name == "user_registration":
                    metrics.record_user_registration()
                
                return result
                
            except Exception as e:
                # Record failure metrics if applicable
                raise e
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


async def metrics_endpoint() -> FastAPIResponse:
    """Endpoint to expose Prometheus metrics."""
    metrics_data = metrics.get_metrics()
    return FastAPIResponse(
        content=metrics_data,
        media_type=metrics.get_content_type()
    )