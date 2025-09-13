# Security Headers and Content Security Policy

This document outlines the security headers implementation and Content Security Policy (CSP) configuration for the Ghostworks SaaS platform.

## Content Security Policy (CSP)

The platform implements a strict Content Security Policy to prevent XSS attacks and other code injection vulnerabilities.

### Current CSP Configuration

```
default-src 'self'; 
script-src 'self' 'unsafe-eval'; 
style-src 'self' 'unsafe-inline'; 
img-src 'self' data: https:; 
font-src 'self' https: data:; 
connect-src 'self' https: wss:; 
media-src 'self'; 
object-src 'none'; 
base-uri 'self'; 
form-action 'self'; 
frame-ancestors 'none'; 
upgrade-insecure-requests
```

### CSP Directive Explanations

| Directive | Value | Reason |
|-----------|-------|---------|
| `default-src` | `'self'` | Only allow resources from same origin by default |
| `script-src` | `'self' 'unsafe-eval'` | Allow same-origin scripts + eval for Next.js dev mode |
| `style-src` | `'self' 'unsafe-inline'` | Allow same-origin styles + inline for Tailwind CSS |
| `img-src` | `'self' data: https:` | Allow same-origin, data URLs, and HTTPS images |
| `font-src` | `'self' https: data:` | Allow same-origin, HTTPS, and data URL fonts |
| `connect-src` | `'self' https: wss:` | Allow same-origin, HTTPS, and WebSocket connections |
| `media-src` | `'self'` | Only allow same-origin media |
| `object-src` | `'none'` | Block all plugins (Flash, etc.) |
| `base-uri` | `'self'` | Restrict base tag to same origin |
| `form-action` | `'self'` | Only allow forms to submit to same origin |
| `frame-ancestors` | `'none'` | Prevent embedding in frames (clickjacking protection) |
| `upgrade-insecure-requests` | - | Automatically upgrade HTTP to HTTPS |

### Production vs Development CSP

The CSP policy is the same across environments, but certain directives like `'unsafe-eval'` are necessary for Next.js development mode. In a production deployment, consider:

1. Removing `'unsafe-eval'` if not needed
2. Using nonces or hashes instead of `'unsafe-inline'` for styles
3. Implementing CSP reporting to monitor violations

### CSP Violation Reporting

To enable CSP violation reporting, add a `report-uri` or `report-to` directive:

```javascript
// Add to CSP policy
"report-uri /api/v1/security/csp-report; report-to csp-endpoint"
```

## Security Headers

The platform implements comprehensive security headers following OWASP recommendations.

### Implemented Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `Content-Security-Policy` | See above | Prevent XSS and code injection |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Force HTTPS connections |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME type sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS protection |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer information |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=(), payment=()` | Disable unnecessary browser features |
| `Cross-Origin-Embedder-Policy` | `require-corp` | Isolate browsing context |
| `Cross-Origin-Opener-Policy` | `same-origin` | Prevent cross-origin access |
| `Cross-Origin-Resource-Policy` | `same-origin` | Control cross-origin resource sharing |

### Header Configuration

Security headers are configured in `services/api/config.py`:

```python
# Security Headers
security_headers_enabled: bool = True
hsts_max_age: int = 31536000  # 1 year
csp_policy: str = "..."  # See above
```

Headers are applied by the `SecurityHeadersMiddleware` in `services/api/security.py`.

## Refresh Token Security Strategy

The platform implements a secure refresh token strategy using HttpOnly cookies with path restrictions.

### Token Configuration

| Token Type | Expiry | Storage | Path Restriction |
|------------|--------|---------|------------------|
| Access Token | 15 minutes | HttpOnly Cookie | `/` (all paths) |
| Refresh Token | 7 days | HttpOnly Cookie | `/auth/refresh` (restricted) |

### Security Features

1. **HttpOnly Cookies**: Prevents JavaScript access to tokens
2. **Secure Flag**: Ensures cookies only sent over HTTPS in production
3. **SameSite**: Set to `lax` to prevent CSRF while allowing normal navigation
4. **Path Restriction**: Refresh tokens only sent to refresh endpoint
5. **Automatic Rotation**: New refresh token issued on each refresh

### Cookie Attributes

```python
# Access token cookie
response.set_cookie(
    key="access_token",
    value=f"Bearer {access_token}",
    expires=datetime.utcnow() + timedelta(minutes=15),
    httponly=True,
    secure=True,  # Production only
    samesite="lax",
    path="/",
)

# Refresh token cookie (path-restricted)
response.set_cookie(
    key="refresh_token", 
    value=f"Bearer {refresh_token}",
    expires=datetime.utcnow() + timedelta(days=7),
    httponly=True,
    secure=True,  # Production only
    samesite="lax",
    path="/auth/refresh",  # Restricted path
)
```

### Token Rotation Flow

1. User authenticates → receives access + refresh tokens
2. Access token expires → client calls `/auth/refresh`
3. Refresh endpoint validates refresh token
4. New access token + refresh token issued
5. Old refresh token invalidated

### Security Benefits

- **Reduced Attack Surface**: Refresh tokens only accessible at one endpoint
- **Token Rotation**: Limits impact of token compromise
- **HttpOnly**: Prevents XSS token theft
- **Short Access Token Lifetime**: Limits exposure window
- **Secure Transport**: HTTPS-only in production

## Rate Limiting

API endpoints are protected with rate limiting to prevent abuse:

- **General API**: 60 requests per minute per IP
- **Authentication**: 5 requests per minute per IP
- **Burst Protection**: 10 request burst allowance

Rate limiting is implemented using `slowapi` with Redis backend.

## Input Validation

All input is validated using:

1. **Pydantic Models**: Schema validation and type checking
2. **Size Limits**: Request size and JSON payload limits
3. **Sanitization**: Input sanitization to prevent injection
4. **Content-Type Validation**: Strict content type checking

## Security Monitoring

The platform includes security monitoring features:

1. **Structured Logging**: All security events logged with correlation IDs
2. **Metrics**: Security-related metrics exported to Prometheus
3. **Alerting**: Automated alerts for security violations
4. **Audit Trail**: Complete audit trail for authentication and authorization

## Environment-Specific Security

### Development
- Demo credentials enabled (with warnings)
- Relaxed CSP for development tools
- Debug logging enabled

### Production
- Demo credentials disabled
- Strict CSP enforcement
- Security headers enforced
- HTTPS required
- Secure cookies enabled

## Security Testing

The platform includes comprehensive security testing:

1. **RLS Smoke Tests**: Verify tenant isolation at database level
2. **OWASP ZAP Scanning**: Automated security vulnerability scanning
3. **Dependency Scanning**: Regular dependency vulnerability checks
4. **Security Headers Testing**: Verify all security headers present

## Compliance

The security implementation supports compliance with:

- **OWASP Top 10**: Protection against common web vulnerabilities
- **SOC 2**: Security controls and monitoring
- **GDPR**: Data protection and privacy controls
- **ISO 27001**: Information security management

## Security Incident Response

In case of security incidents:

1. **Immediate Response**: Automated blocking of suspicious activity
2. **Logging**: Comprehensive security event logging
3. **Alerting**: Real-time alerts for security violations
4. **Investigation**: Audit trails for forensic analysis
5. **Recovery**: Automated recovery procedures where possible