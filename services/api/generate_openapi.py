#!/usr/bin/env python3
"""
Generate OpenAPI specification from FastAPI application.
"""

import json
import sys
from pathlib import Path

# Add the services/api directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from main import app
from fastapi.openapi.utils import get_openapi


def generate_openapi_spec():
    """Generate OpenAPI specification and save to docs directory."""
    
    # Generate OpenAPI schema
    openapi_schema = get_openapi(
        title="Ghostworks API",
        version="1.0.0",
        description="""
        Production-grade multi-tenant SaaS platform API.
        
        ## Features
        
        - **Multi-tenant Architecture**: Secure tenant isolation with Row-Level Security
        - **Authentication**: JWT-based authentication with refresh tokens
        - **Authorization**: Role-based access control (Owner, Admin, Member)
        - **Artifact Management**: Full CRUD operations with search and filtering
        - **Observability**: Comprehensive metrics, tracing, and logging
        
        ## Authentication
        
        Most endpoints require authentication. Include the JWT token in the Authorization header:
        
        ```
        Authorization: Bearer <your-jwt-token>
        ```
        
        ## Multi-tenancy
        
        All operations are scoped to the authenticated user's current workspace.
        Use the workspace switching endpoints to change context.
        
        ## Rate Limiting
        
        API endpoints are rate-limited to prevent abuse:
        - Authentication endpoints: 5 requests per minute
        - General API endpoints: 100 requests per minute
        
        ## Error Handling
        
        The API returns structured error responses with the following format:
        
        ```json
        {
          "error": "error_code",
          "message": "Human-readable error message",
          "details": {},
          "request_id": "unique-request-id",
          "timestamp": "2024-01-15T10:30:00Z"
        }
        ```
        """,
        routes=app.routes,
        servers=[
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://api.ghostworks.dev", "description": "Production server"}
        ]
    )
    
    # Ensure docs directory exists
    docs_dir = Path(__file__).parent.parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Save OpenAPI spec
    openapi_file = docs_dir / "openapi.json"
    with open(openapi_file, 'w') as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"OpenAPI specification generated: {openapi_file}")
    
    # Also generate a YAML version
    try:
        import yaml
        yaml_file = docs_dir / "openapi.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(openapi_schema, f, default_flow_style=False, sort_keys=False)
        print(f"OpenAPI YAML specification generated: {yaml_file}")
    except ImportError:
        print("PyYAML not installed, skipping YAML generation")


if __name__ == "__main__":
    generate_openapi_spec()