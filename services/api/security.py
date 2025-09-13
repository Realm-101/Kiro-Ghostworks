"""
Security middleware and utilities for Ghostworks SaaS API.
Implements security headers, rate limiting, and input validation.
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog

from config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    Implements OWASP security header recommendations.
    """
    
    def __init__(self, app, settings=None):
        super().__init__(app)
        self.settings = settings or get_settings()
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)
        
        if not self.settings.security_headers_enabled:
            return response
        
        # Security headers
        security_headers = {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # XSS protection (legacy but still useful)
            "X-XSS-Protection": "1; mode=block",
            
            # HSTS - Force HTTPS
            "Strict-Transport-Security": f"max-age={self.settings.hsts_max_age}; includeSubDomains; preload",
            
            # Content Security Policy
            "Content-Security-Policy": self.settings.csp_policy,
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions policy (formerly Feature Policy)
            "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
            
            # Cross-Origin policies
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin"
        }
        
        # Add headers to response
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate request size and content.
    Prevents oversized requests and malformed data.
    """
    
    def __init__(self, app, settings=None):
        super().__init__(app)
        self.settings = settings or get_settings()
    
    async def dispatch(self, request: Request, call_next):
        """Validate request input before processing."""
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > self.settings.max_request_size:
                    logger.warning(
                        "Request size exceeded limit",
                        content_length=content_length,
                        max_size=self.settings.max_request_size,
                        path=request.url.path
                    )
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": "request_too_large",
                            "message": f"Request size {content_length} exceeds maximum {self.settings.max_request_size} bytes",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
            except ValueError:
                logger.warning("Invalid content-length header", content_length=content_length)
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "invalid_content_length",
                        "message": "Invalid Content-Length header",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
        
        # Validate content type for POST/PUT/PATCH requests
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            
            # Check for JSON payload size
            if "application/json" in content_type and content_length:
                if content_length > self.settings.max_json_payload_size:
                    logger.warning(
                        "JSON payload size exceeded limit",
                        content_length=content_length,
                        max_size=self.settings.max_json_payload_size
                    )
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": "json_payload_too_large",
                            "message": f"JSON payload size exceeds maximum {self.settings.max_json_payload_size} bytes",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
        
        return await call_next(request)


# Rate limiter configuration
def get_rate_limiter():
    """Get configured rate limiter instance."""
    return Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.rate_limit_requests_per_minute}/minute"]
    )


# Rate limiter instance
limiter = get_rate_limiter()


def create_rate_limit_handler():
    """Create custom rate limit exceeded handler."""
    
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        """Handle rate limit exceeded errors."""
        logger.warning(
            "Rate limit exceeded",
            path=request.url.path,
            method=request.method,
            client_ip=get_remote_address(request),
            limit=str(exc.detail)
        )
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "detail": str(exc.detail),
                "retry_after": 60,  # seconds
                "timestamp": datetime.utcnow().isoformat()
            },
            headers={"Retry-After": "60"}
        )
    
    return rate_limit_handler


class SecureCookieManager:
    """
    Utility class for managing secure JWT cookies.
    Implements secure cookie attributes and management.
    """
    
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
    
    def set_auth_cookies(
        self,
        response: Response,
        access_token: str,
        refresh_token: str
    ) -> None:
        """
        Set secure authentication cookies.
        
        Args:
            response: FastAPI response object
            access_token: JWT access token
            refresh_token: JWT refresh token
        """
        # Access token cookie (shorter expiry)
        access_expires = datetime.utcnow() + timedelta(
            minutes=self.settings.jwt_access_token_expire_minutes
        )
        
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            expires=access_expires,
            httponly=self.settings.cookie_httponly,
            secure=self.settings.cookie_secure,
            samesite=self.settings.cookie_samesite,
            domain=self.settings.cookie_domain,
            path="/",
        )
        
        # Refresh token cookie (longer expiry)
        refresh_expires = datetime.utcnow() + timedelta(
            days=self.settings.jwt_refresh_token_expire_days
        )
        
        response.set_cookie(
            key="refresh_token",
            value=f"Bearer {refresh_token}",
            expires=refresh_expires,
            httponly=self.settings.cookie_httponly,
            secure=self.settings.cookie_secure,
            samesite=self.settings.cookie_samesite,
            domain=self.settings.cookie_domain,
            path="/auth/refresh",  # Restrict refresh token to refresh endpoint
        )
        
        logger.info(
            "Authentication cookies set",
            access_expires=access_expires.isoformat(),
            refresh_expires=refresh_expires.isoformat(),
            secure=self.settings.cookie_secure,
            httponly=self.settings.cookie_httponly,
            samesite=self.settings.cookie_samesite
        )
    
    def clear_auth_cookies(self, response: Response) -> None:
        """
        Clear authentication cookies on logout.
        
        Args:
            response: FastAPI response object
        """
        # Clear access token cookie
        response.set_cookie(
            key="access_token",
            value="",
            expires=datetime.utcnow() - timedelta(days=1),
            httponly=self.settings.cookie_httponly,
            secure=self.settings.cookie_secure,
            samesite=self.settings.cookie_samesite,
            domain=self.settings.cookie_domain,
            path="/",
        )
        
        # Clear refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value="",
            expires=datetime.utcnow() - timedelta(days=1),
            httponly=self.settings.cookie_httponly,
            secure=self.settings.cookie_secure,
            samesite=self.settings.cookie_samesite,
            domain=self.settings.cookie_domain,
            path="/auth/refresh",
        )
        
        logger.info("Authentication cookies cleared")
    
    def get_token_from_cookie(self, request: Request, cookie_name: str) -> Optional[str]:
        """
        Extract JWT token from secure cookie.
        
        Args:
            request: FastAPI request object
            cookie_name: Name of the cookie containing the token
            
        Returns:
            JWT token string or None if not found
        """
        cookie_value = request.cookies.get(cookie_name)
        if cookie_value and cookie_value.startswith("Bearer "):
            return cookie_value[7:]  # Remove "Bearer " prefix
        return None


def validate_request_headers(request: Request) -> None:
    """
    Validate request headers for security.
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: If headers are invalid or suspicious
    """
    # Check for suspicious headers
    suspicious_headers = [
        "x-forwarded-host",
        "x-original-url", 
        "x-rewrite-url"
    ]
    
    for header in suspicious_headers:
        if header in request.headers:
            logger.warning(
                "Suspicious header detected",
                header=header,
                value=request.headers[header],
                path=request.url.path,
                client_ip=get_remote_address(request)
            )
    
    # Validate User-Agent
    user_agent = request.headers.get("user-agent", "")
    if not user_agent or len(user_agent) > 512:
        logger.warning(
            "Invalid or missing User-Agent",
            user_agent=user_agent[:100] if user_agent else None,
            path=request.url.path
        )
    
    # Check for host header injection
    host = request.headers.get("host", "")
    if host and ("localhost" not in host and "127.0.0.1" not in host):
        # In production, validate against allowed hosts
        allowed_hosts = ["api.ghostworks.com", "ghostworks.com"]  # Configure as needed
        if settings.environment == "production" and host not in allowed_hosts:
            logger.warning(
                "Potential host header injection",
                host=host,
                path=request.url.path,
                client_ip=get_remote_address(request)
            )


def sanitize_input(data: Any) -> Any:
    """
    Sanitize input data to prevent injection attacks.
    
    Args:
        data: Input data to sanitize
        
    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        # Remove null bytes and control characters
        data = data.replace('\x00', '').replace('\r', '').replace('\n', ' ')
        
        # Limit string length
        if len(data) > 10000:  # Configurable limit
            data = data[:10000]
        
        return data.strip()
    
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    
    return data


# Global cookie manager instance
cookie_manager = SecureCookieManager()