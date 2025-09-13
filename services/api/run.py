#!/usr/bin/env python3
"""
Development server runner for Ghostworks SaaS API.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    import uvicorn
    from config import get_settings
    
    settings = get_settings()
    
    # Development server configuration
    uvicorn_config = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": settings.port,
        "reload": settings.reload and settings.environment == "development",
        "log_level": settings.log_level.lower(),
        "access_log": True,
    }
    
    if settings.environment == "development":
        uvicorn_config.update({
            "reload_dirs": [str(current_dir)],
            "use_colors": True,
        })
    
    print(f"Starting Ghostworks API server on port {settings.port}")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    print(f"Documentation: http://localhost:{settings.port}/docs")
    
    uvicorn.run(**uvicorn_config)