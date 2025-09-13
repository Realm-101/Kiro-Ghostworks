"""
Ghostworks SaaS Celery Worker Service.
Handles background tasks for email, data processing, and maintenance.
"""

from .celery_app import celery_app
from .config import get_worker_settings
from .database import get_database_session, close_database_connections

__version__ = "1.0.0"

__all__ = [
    "celery_app",
    "get_worker_settings", 
    "get_database_session",
    "close_database_connections",
]