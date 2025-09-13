"""
Configuration management for Ghostworks SaaS Worker.
Shares database configuration with API service.
"""

import os
from typing import List, Optional
from pydantic import PostgresDsn, RedisDsn, validator
from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    """Worker settings with environment variable support."""
    
    # Environment
    environment: str = "development"
    debug: bool = False
    
    # Database (shared with API service)
    database_url: PostgresDsn
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_echo: bool = False
    
    # Redis/Celery
    redis_url: RedisDsn = "redis://localhost:6379/0"
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    
    # Celery Configuration
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: List[str] = ["json"]
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True
    celery_task_track_started: bool = True
    celery_task_time_limit: int = 300  # 5 minutes
    celery_task_soft_time_limit: int = 240  # 4 minutes
    celery_worker_prefetch_multiplier: int = 1
    celery_worker_max_tasks_per_child: int = 1000
    
    # Observability
    opentelemetry_endpoint: Optional[str] = None
    prometheus_metrics_enabled: bool = True
    log_level: str = "INFO"
    
    @validator("celery_broker_url", pre=True, always=True)
    def set_celery_broker_url(cls, v, values):
        """Set Celery broker URL from Redis URL if not provided."""
        if v is None:
            redis_url = values.get("redis_url")
            if redis_url:
                return str(redis_url)
        return v
    
    @validator("celery_result_backend", pre=True, always=True)
    def set_celery_result_backend(cls, v, values):
        """Set Celery result backend from Redis URL if not provided."""
        if v is None:
            redis_url = values.get("redis_url")
            if redis_url:
                return str(redis_url)
        return v
    
    @validator("debug", pre=True)
    def parse_debug(cls, v, values):
        """Set debug mode based on environment."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return values.get("environment") == "development"
    
    @validator("database_echo", pre=True)
    def parse_database_echo(cls, v, values):
        """Enable database query logging in debug mode."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return values.get("debug", False)
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


# Global settings instance
worker_settings = WorkerSettings()


def get_worker_settings() -> WorkerSettings:
    """Get worker settings instance."""
    return worker_settings