---
inclusion: fileMatch
fileMatchPattern: "services/**/*.py|apps/**/*.ts|apps/**/*.tsx"
---

# Security Policies and Guidelines

This document outlines security policies aligned with OWASP ASVS (Application Security Verification Standard) for the Ghostworks SaaS platform.

## Authentication Security (ASVS V2)

### Password Management
- Use bcrypt with minimum 12 salt rounds for password hashing
- Enforce password complexity: minimum 8 characters, mixed case, numbers, symbols
- Implement account lockout after 5 failed login attempts
- Require password reset after 90 days for admin accounts

### Session Management
- Use JWT tokens with short expiration (15 minutes for access, 7 days for refresh)
- Implement secure token storage with httpOnly, secure, and sameSite cookies
- Rotate refresh tokens on each use
- Invalidate all sessions on password change

### Multi-Factor Authentication
- Require MFA for admin and owner roles
- Support TOTP and backup codes
- Implement rate limiting on MFA attempts

## Authorization and Access Control (ASVS V4)

### Role-Based Access Control
- Implement principle of least privilege
- Use enum-based role definitions: Owner, Admin, Member
- Validate permissions at both API and database levels
- Log all authorization decisions for audit trails

### Tenant Isolation
- Enforce Row-Level Security (RLS) in PostgreSQL
- Validate tenant context in all database operations
- Use tenant-scoped connection pools
- Implement tenant-aware logging and monitoring

## Input Validation (ASVS V5)

### Server-Side Validation
- Validate all inputs using Pydantic models
- Sanitize HTML content to prevent XSS
- Use parameterized queries to prevent SQL injection
- Implement file upload restrictions (type, size, content validation)

### API Security
- Implement request size limits (1MB for JSON, 10MB for file uploads)
- Use CORS policies restrictively
- Validate Content-Type headers
- Implement API rate limiting per user/tenant

## Cryptography (ASVS V6)

### Data Protection
- Encrypt sensitive data at rest using AES-256
- Use TLS 1.3 for all communications
- Implement proper key rotation policies
- Store encryption keys in secure key management system

### Secure Random Generation
- Use cryptographically secure random number generators
- Generate secure session tokens and API keys
- Implement proper entropy for password reset tokens

## Error Handling and Logging (ASVS V7)

### Secure Error Handling
- Never expose sensitive information in error messages
- Log security events with appropriate detail levels
- Implement structured logging with correlation IDs
- Use generic error messages for authentication failures

### Security Logging
- Log all authentication attempts (success/failure)
- Log authorization decisions and failures
- Log data access patterns for anomaly detection
- Implement log integrity protection

## Data Protection (ASVS V9)

### Privacy Controls
- Implement data minimization principles
- Support data export and deletion requests
- Encrypt PII fields in database
- Implement data retention policies

### Backup Security
- Encrypt all database backups
- Test backup restoration procedures regularly
- Implement secure backup storage with access controls
- Document data recovery procedures

## Communication Security (ASVS V9)

### TLS Configuration
- Use TLS 1.3 with strong cipher suites
- Implement HSTS headers with long max-age
- Use certificate pinning for critical connections
- Implement proper certificate validation

### API Security Headers
```python
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY", 
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}
```

## Security Testing Requirements

### Automated Security Testing
- Run OWASP ZAP baseline scans in CI/CD
- Implement dependency vulnerability scanning
- Use static analysis security testing (SAST)
- Perform dynamic application security testing (DAST)

### Penetration Testing
- Conduct annual penetration testing
- Test multi-tenant isolation boundaries
- Validate authentication and authorization controls
- Test for common OWASP Top 10 vulnerabilities

## Incident Response

### Security Incident Handling
- Implement automated alerting for security events
- Document incident response procedures
- Maintain security contact information
- Implement breach notification procedures

### Monitoring and Detection
- Monitor for suspicious authentication patterns
- Detect privilege escalation attempts
- Alert on unusual data access patterns
- Implement real-time security dashboards

## Compliance and Governance

### Security Reviews
- Require security review for all code changes
- Implement security checkpoints in CI/CD pipeline
- Document security architecture decisions
- Maintain security risk register

### Training and Awareness
- Provide security training for all developers
- Implement secure coding guidelines
- Regular security awareness updates
- Document security best practices

## Implementation Guidelines

### Code Review Checklist
- [ ] Input validation implemented and tested
- [ ] Authentication/authorization properly enforced
- [ ] Sensitive data properly protected
- [ ] Error handling doesn't leak information
- [ ] Security headers configured
- [ ] Logging includes security events
- [ ] Dependencies scanned for vulnerabilities
- [ ] Tests include security test cases

### Security Configuration
- Use environment variables for all secrets
- Implement proper secret rotation
- Use secure defaults for all configurations
- Document security configuration requirements