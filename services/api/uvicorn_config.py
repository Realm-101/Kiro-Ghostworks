"""
Uvicorn server configuration for different environments.
"""

import os
from typing import Dict, Any


def get_uvicorn_config(environment: str = None) -> Dict[str, Any]:
    """
    Get uvicorn configuration based on environment.
    
    Args:
        environment: Target environment (development, staging, production)
        
    Returns:
        Dictionary with uvicorn configuration parameters
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
    base_config = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 8000)),
    }
    
    if environment == "development":
        return {
            **base_config,
            "reload": True,
            "reload_dirs": ["./"],
            "log_level": "debug",
            "access_log": True,
            "use_colors": True,
            "workers": 1,
        }
    
    elif environment == "staging":
        return {
            **base_config,
            "reload": False,
            "log_level": "info",
            "access_log": True,
            "workers": 2,
            "worker_class": "uvicorn.workers.UvicornWorker",
        }
    
    elif environment == "production":
        return {
            **base_config,
            "reload": False,
            "log_level": "warning",
            "access_log": False,  # Use structured logging instead
            "workers": int(os.getenv("WORKERS", 4)),
            "worker_class": "uvicorn.workers.UvicornWorker",
            "keepalive": 2,
            "max_requests": 1000,
            "max_requests_jitter": 100,
        }
    
    else:
        raise ValueError(f"Unknown environment: {environment}")


if __name__ == "__main__":
    import uvicorn
    
    config = get_uvicorn_config()
    uvicorn.run(**config)