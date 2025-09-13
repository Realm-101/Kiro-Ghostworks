# Troubleshooting Runbook

This runbook provides solutions for common issues encountered in the Ghostworks SaaS platform.

## 🎯 Overview

This guide covers the most frequently encountered issues and their solutions, organized by service and symptom. Use the quick reference section for immediate help during incidents.

## 🚨 Quick Reference

### Emergency Commands
```bash
# Check all service status
docker-compose ps

# View service logs
docker-compose logs -f [service-name]

# Restart all services
docker-compose restart

# Emergency stop
docker-compose down

# Health check all services
curl http://localhost:8000/api/v1/health
curl http://localhost:3000/api/health
```

### Service Ports
- **Web App**: 3000
- **API**: 8000
- **PostgreSQL**: 5432
- **Redis**: 6379
- **Prometheus**: 9090
- **Grafana**: 3001
- **Nginx**: 80, 443

## 🔧 Application Issues

### API Service Issues

#### Symptom: API Returns 500 Errors

**Possible Causes:**
- Database connection issues
- Configuration errors
- Application code bugs
- Resource exhaustion

**Diagnosis:**
```bash
# Check API logs
docker-compose logs api

# Check database connectivity
docker-compose exec api python -c "
from database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('Database connection OK')
except Exception as e:
    print(f'Database error: {e}')
"

# Check configuration
docker-compose exec api python -c "
from config import settings
print(f'Database URL: {settings.database_url}')
print(f'Environment: {settings.environment}')
"
```

**Solutions:**
1. **Database Connection Issues:**
   ```bash
   # Restart database
   docker-compose restart postgres
   
   # Check database logs
   docker-compose logs postgres
   
   # Verify connection string
   docker-compose exec api env | grep DATABASE_URL
   ```

2. **Configuration Issues:**
   ```bash
   # Validate environment variables
   docker-compose config
   
   # Check .env file
   cat .env
   
   # Restart API with fresh config
   docker-compose restart api
   ```

3. **Resource Issues:**
   ```bash
   # Check container resources
   docker stats
   
   # Check system resources
   free -h
   df -h
   ```

#### Symptom: API Slow Response Times

**Diagnosis:**
```bash
# Check API metrics
curl http://localhost:8000/metrics | grep http_request_duration

# Monitor database queries
docker-compose exec postgres psql -U postgres -d ghostworks -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
"

# Check system load
top
htop
```

**Solutions:**
1. **Database Performance:**
   ```bash
   # Analyze slow queries
   docker-compose exec postgres psql -U postgres -d ghostworks -c "
   SELECT query, total_exec_time, mean_exec_time, calls
   FROM pg_stat_statements
   WHERE mean_exec_time > 100
   ORDER BY mean_exec_time DESC;
   "
   
   # Check database connections
   docker-compose exec postgres psql -U postgres -d ghostworks -c "
   SELECT count(*) as active_connections 
   FROM pg_stat_activity 
   WHERE state = 'active';
   "
   ```

2. **Application Performance:**
   ```bash
   # Profile API endpoints
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/artifacts
   
   # Check memory usage
   docker-compose exec api python -c "
   import psutil
   process = psutil.Process()
   print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
   "
   ```

#### Symptom: Authentication Issues

**Diagnosis:**
```bash
# Test JWT token generation
docker-compose exec api python -c "
from auth import create_access_token
token = create_access_token(data={'sub': 'test@example.com'})
print(f'Token: {token}')
"

# Check JWT secret
docker-compose exec api env | grep JWT_SECRET_KEY

# Test authentication endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email": "owner@acme.com", "password": "demo123"}'
```

**Solutions:**
1. **JWT Configuration:**
   ```bash
   # Verify JWT secret is set
   docker-compose exec api python -c "
   from config import settings
   print(f'JWT Secret length: {len(settings.jwt_secret_key)}')
   "
   
   # Regenerate JWT secret if needed
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **User Authentication:**
   ```bash
   # Check user exists
   docker-compose exec postgres psql -U postgres -d ghostworks -c "
   SELECT id, email, is_verified FROM users WHERE email = 'owner@acme.com';
   "
   
   # Reset user password
   docker-compose exec api python -c "
   from auth import get_password_hash
   print(get_password_hash('demo123'))
   "
   ```

### Frontend Issues

#### Symptom: Frontend Won't Load

**Diagnosis:**
```bash
# Check frontend logs
docker-compose logs web

# Check if API is accessible
curl http://localhost:8000/api/v1/health

# Check network connectivity
docker-compose exec web curl http://api:8000/api/v1/health
```

**Solutions:**
1. **Build Issues:**
   ```bash
   # Rebuild frontend
   docker-compose build web
   
   # Check for build errors
   docker-compose logs web | grep -i error
   
   # Clear build cache
   docker-compose build --no-cache web
   ```

2. **API Connectivity:**
   ```bash
   # Check API URL configuration
   docker-compose exec web env | grep NEXT_PUBLIC_API_URL
   
   # Test API from frontend container
   docker-compose exec web curl http://api:8000/api/v1/health
   ```

#### Symptom: Frontend API Calls Failing

**Diagnosis:**
```bash
# Check browser console for errors
# Check network tab in browser dev tools

# Test API directly
curl http://localhost:8000/api/v1/artifacts \
  -H "Authorization: Bearer <token>"

# Check CORS configuration
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     http://localhost:8000/api/v1/artifacts
```

**Solutions:**
1. **CORS Issues:**
   ```bash
   # Check CORS configuration in API
   docker-compose exec api python -c "
   from main import app
   print(app.middleware)
   "
   
   # Update CORS origins if needed
   # Edit services/api/main.py
   ```

2. **Authentication Issues:**
   ```bash
   # Check token storage in browser
   # Verify token format and expiration
   
   # Test token refresh
   curl -X POST http://localhost:8000/api/v1/auth/refresh \
     -H 'Content-Type: application/json' \
     -d '{"refresh_token": "<refresh_token>"}'
   ```

## 🗄️ Database Issues

### Connection Issues

#### Symptom: Database Connection Refused

**Diagnosis:**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres pg_isready -U postgres
```

**Solutions:**
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check PostgreSQL configuration
docker-compose exec postgres cat /var/lib/postgresql/data/postgresql.conf

# Verify network connectivity
docker-compose exec api ping postgres

# Check connection limits
docker-compose exec postgres psql -U postgres -c "SHOW max_connections;"
```

#### Symptom: Too Many Connections

**Diagnosis:**
```bash
# Check active connections
docker-compose exec postgres psql -U postgres -d ghostworks -c "
SELECT count(*) as total_connections,
       count(*) FILTER (WHERE state = 'active') as active_connections,
       count(*) FILTER (WHERE state = 'idle') as idle_connections
FROM pg_stat_activity;
"

# Check connection sources
docker-compose exec postgres psql -U postgres -d ghostworks -c "
SELECT client_addr, count(*) as connections
FROM pg_stat_activity
GROUP BY client_addr
ORDER BY connections DESC;
"
```

**Solutions:**
```bash
# Kill idle connections
docker-compose exec postgres psql -U postgres -d ghostworks -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < now() - interval '5 minutes';
"

# Increase connection limit (temporary)
docker-compose exec postgres psql -U postgres -c "
ALTER SYSTEM SET max_connections = 200;
SELECT pg_reload_conf();
"

# Check application connection pooling
docker-compose exec api python -c "
from database import engine
print(f'Pool size: {engine.pool.size()}')
print(f'Checked out: {engine.pool.checkedout()}')
"
```

### Performance Issues

#### Symptom: Slow Database Queries

**Diagnosis:**
```bash
# Enable query logging (if not enabled)
docker-compose exec postgres psql -U postgres -c "
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();
"

# Check slow queries
docker-compose exec postgres psql -U postgres -d ghostworks -c "
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# Check table sizes
docker-compose exec postgres psql -U postgres -d ghostworks -c "
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

**Solutions:**
```bash
# Analyze table statistics
docker-compose exec postgres psql -U postgres -d ghostworks -c "
ANALYZE;
"

# Check missing indexes
docker-compose exec postgres psql -U postgres -d ghostworks -c "
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
AND n_distinct > 100
ORDER BY n_distinct DESC;
"

# Vacuum tables
docker-compose exec postgres psql -U postgres -d ghostworks -c "
VACUUM ANALYZE;
"
```

### Migration Issues

#### Symptom: Migration Fails

**Diagnosis:**
```bash
# Check migration status
docker-compose exec api alembic current

# Check migration history
docker-compose exec api alembic history

# Check for migration conflicts
docker-compose exec api alembic check
```

**Solutions:**
```bash
# Rollback to previous migration
docker-compose exec api alembic downgrade -1

# Mark migration as complete (if manually applied)
docker-compose exec api alembic stamp head

# Resolve migration conflicts
docker-compose exec api alembic merge -m "Merge migrations"

# Apply specific migration
docker-compose exec api alembic upgrade <revision>
```

## 🔄 Redis Issues

### Connection Issues

#### Symptom: Redis Connection Failed

**Diagnosis:**
```bash
# Check Redis status
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Test Redis connectivity
docker-compose exec redis redis-cli ping
```

**Solutions:**
```bash
# Restart Redis
docker-compose restart redis

# Check Redis configuration
docker-compose exec redis redis-cli CONFIG GET "*"

# Test from application
docker-compose exec api python -c "
import redis
r = redis.from_url('redis://redis:6379/0')
print(r.ping())
"
```

#### Symptom: Redis Memory Issues

**Diagnosis:**
```bash
# Check Redis memory usage
docker-compose exec redis redis-cli INFO memory

# Check key count
docker-compose exec redis redis-cli DBSIZE

# Check largest keys
docker-compose exec redis redis-cli --bigkeys
```

**Solutions:**
```bash
# Set memory limit
docker-compose exec redis redis-cli CONFIG SET maxmemory 256mb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Clear specific keys
docker-compose exec redis redis-cli FLUSHDB

# Monitor memory usage
docker-compose exec redis redis-cli --latency-history -i 1
```

## 🔍 Monitoring Issues

### Metrics Not Collecting

#### Symptom: Missing Metrics in Prometheus

**Diagnosis:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check application metrics endpoint
curl http://localhost:8000/metrics

# Check OpenTelemetry collector
docker-compose logs otelcol
```

**Solutions:**
```bash
# Restart monitoring stack
docker-compose restart prometheus grafana otelcol

# Check Prometheus configuration
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml

# Verify metrics are being generated
docker-compose exec api python -c "
from prometheus_client import generate_latest, REGISTRY
print(generate_latest(REGISTRY).decode())
"
```

### Grafana Issues

#### Symptom: Dashboards Not Loading

**Diagnosis:**
```bash
# Check Grafana logs
docker-compose logs grafana

# Check data source connectivity
curl -u admin:admin http://localhost:3001/api/datasources

# Test Prometheus from Grafana
curl -u admin:admin "http://localhost:3001/api/datasources/proxy/1/api/v1/query?query=up"
```

**Solutions:**
```bash
# Restart Grafana
docker-compose restart grafana

# Reset Grafana database
docker-compose down
docker volume rm ghostworks_grafana-storage
docker-compose up -d grafana

# Import dashboards manually
# Use Grafana UI to import from infra/docker/grafana/dashboards/
```

## 🌐 Network Issues

### Service Communication

#### Symptom: Services Can't Communicate

**Diagnosis:**
```bash
# Check Docker network
docker network ls
docker network inspect ghostworks_default

# Test connectivity between services
docker-compose exec web ping api
docker-compose exec api ping postgres
docker-compose exec api ping redis
```

**Solutions:**
```bash
# Recreate network
docker-compose down
docker-compose up -d

# Check firewall rules
sudo iptables -L

# Verify service names in configuration
docker-compose config
```

### External Connectivity

#### Symptom: Can't Access External Services

**Diagnosis:**
```bash
# Test external connectivity from containers
docker-compose exec api ping google.com
docker-compose exec api curl https://httpbin.org/get

# Check DNS resolution
docker-compose exec api nslookup google.com
```

**Solutions:**
```bash
# Check Docker daemon DNS settings
cat /etc/docker/daemon.json

# Restart Docker daemon
sudo systemctl restart docker

# Use custom DNS servers
# Edit docker-compose.yml to add dns: ["8.8.8.8", "1.1.1.1"]
```

## 🔒 Security Issues

### SSL/TLS Issues

#### Symptom: SSL Certificate Errors

**Diagnosis:**
```bash
# Check certificate validity
openssl s_client -connect localhost:443 -servername localhost

# Check Nginx SSL configuration
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf
```

**Solutions:**
```bash
# Generate self-signed certificate for development
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout infra/docker/nginx/ssl/nginx.key \
  -out infra/docker/nginx/ssl/nginx.crt

# Update Nginx configuration
# Edit infra/docker/nginx/conf.d/default.conf

# Restart Nginx
docker-compose restart nginx
```

### Authentication Issues

#### Symptom: JWT Token Issues

**Diagnosis:**
```bash
# Decode JWT token
echo "<token>" | cut -d. -f2 | base64 -d | jq

# Check token expiration
docker-compose exec api python -c "
import jwt
from config import settings
token = '<token>'
try:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=['HS256'])
    print(payload)
except jwt.ExpiredSignatureError:
    print('Token expired')
except jwt.InvalidTokenError as e:
    print(f'Invalid token: {e}')
"
```

**Solutions:**
```bash
# Generate new JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update JWT configuration
# Edit .env file with new JWT_SECRET_KEY

# Restart API service
docker-compose restart api
```

## 📋 Maintenance Tasks

### Regular Maintenance

#### Daily Tasks
```bash
# Check service health
docker-compose ps
curl http://localhost:8000/api/v1/health

# Check disk space
df -h

# Check logs for errors
docker-compose logs --since 24h | grep -i error
```

#### Weekly Tasks
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Clean up Docker resources
docker system prune -f

# Backup database
docker-compose exec postgres pg_dump -U postgres ghostworks > backup_$(date +%Y%m%d).sql

# Check security updates
docker-compose pull
```

#### Monthly Tasks
```bash
# Full system backup
tar -czf backup_$(date +%Y%m%d).tar.gz .

# Review and rotate logs
docker-compose logs --since 30d > logs_$(date +%Y%m%d).log

# Update monitoring dashboards
# Export from Grafana and commit to repository

# Security audit
docker-compose exec api pip-audit
npm audit --prefix apps/web
```

## 📞 Escalation Procedures

### When to Escalate

**Immediate Escalation (P0):**
- Complete service outage
- Data loss or corruption
- Security breach
- Database unavailable

**Escalate within 30 minutes (P1):**
- Significant performance degradation
- Partial service outage
- Authentication system down
- Critical feature unavailable

### Escalation Contacts

1. **Platform Team Lead**: [Contact Info]
2. **DevOps Engineer**: [Contact Info]
3. **Database Administrator**: [Contact Info]
4. **Security Team**: [Contact Info]
5. **Engineering Manager**: [Contact Info]

### Incident Documentation

For each incident, document:
- **Time of occurrence**
- **Symptoms observed**
- **Diagnostic steps taken**
- **Root cause identified**
- **Resolution applied**
- **Prevention measures**

---

**Last Updated**: [Current Date]  
**Next Review**: [Next Month]