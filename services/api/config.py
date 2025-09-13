"""
Configuration management for Ghostworks SaaS API.
Uses Pydantic Settings for 12-Factor App compliance.
"""

import os
from typing import List, Optional
from pydantic import PostgresDsn, RedisDsn, field_validator, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support following 12-Factor principles."""
    
    # Environment
    environment: str = "development"
    debug: bool = False
    
    # Database
    database_url: PostgresDsn
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False
    
    # Redis
    redis_url: RedisDsn = "redis://localhost:6379/0"
    
    # Authentication & Security
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12
    
    # Security Headers
    security_headers_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year
    csp_policy: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-eval'; "  # unsafe-eval needed for Next.js dev
        "style-src 'self' 'unsafe-inline'; "  # unsafe-inline needed for Tailwind
        "img-src 'self' data: https:; "
        "font-src 'self' https: data:; "
        "connect-src 'self' https: wss:; "  # wss: for WebSocket connections
        "media-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "upgrade-insecure-requests"
    )
    
    # Cookie Security
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"
    cookie_domain: Optional[str] = None
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_auth_requests_per_minute: int = 5
    rate_limit_burst_size: int = 10
    
    # CORS
    cors_origins: str = "http://localhost:3000"
    cors_allow_credentials: bool = True
    
    # Server
    port: int = 8000
    workers: int = 1
    reload: bool = True
    host: str = "0.0.0.0"
    
    # Observability
    opentelemetry_endpoint: Optional[str] = None
    prometheus_metrics_enabled: bool = True
    log_level: str = "INFO"
    
    # Input Validation
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    max_json_payload_size: int = 1024 * 1024  # 1MB
    max_form_fields: int = 100
    max_form_field_size: int = 1024 * 1024  # 1MB
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return [self.cors_origins]
    
    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v, info):
        """Set debug mode based on environment."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return info.data.get("environment") == "development"
    
    @field_validator("database_echo", mode="before")
    @classmethod
    def parse_database_echo(cls, v, info):
        """Enable database query logging in debug mode."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return info.data.get("debug", False)
    
    @field_validator("cookie_secure", mode="before")
    @classmethod
    def parse_cookie_secure(cls, v, info):
        """Set secure cookies in production."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return info.data.get("environment") != "development"
    
    @field_validator("cookie_samesite", mode="before")
    @classmethod
    def validate_cookie_samesite(cls, v):
        """Validate SameSite cookie attribute."""
        if v.lower() not in ("strict", "lax", "none"):
            raise ValueError("cookie_samesite must be 'strict', 'lax', or 'none'")
        return v.lower()
    
    @field_validator("csp_policy", mode="before")
    @classmethod
    def validate_csp_policy(cls, v):
        """Validate CSP policy format."""
        if not v or not isinstance(v, str):
            raise ValueError("CSP policy must be a non-empty string")
        return v.strip()
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings