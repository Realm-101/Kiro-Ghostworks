# Ghostworks Docker Infrastructure

This directory contains all Docker-related configuration files for the Ghostworks platform.

## Quick Start

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Start the development stack:**
   ```bash
   make up
   # or
   docker-compose up -d
   ```

3. **Check service health:**
   ```bash
   make health
   ```

4. **Access services:**
   - Web Application: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - Grafana Dashboards: http://localhost:3001 (admin/admin)
   - Prometheus Metrics: http://localhost:9090
   - Flower (Celery): http://localhost:5555
   - Adminer (Database): http://localhost:8080

## Architecture

### Services

- **web**: Next.js frontend application
- **api**: FastAPI backend service
- **worker**: Celery background worker
- **postgres**: PostgreSQL database
- **redis**: Redis cache and message broker
- **nginx**: Reverse proxy and load balancer
- **prometheus**: Metrics collection
- **grafana**: Metrics visualization
- **otelcol**: OpenTelemetry collector

### Development Services

Additional services available in development mode:

- **flower**: Celery task monitoring
- **adminer**: Database administration
- **redis-commander**: Redis management

## Configuration Files

### Docker Compose Files

- `docker-compose.yml`: Base configuration
- `docker-compose.override.yml`: Development overrides (auto-loaded)
- `docker-compose.prod.yml`: Production configuration

### Service Configurations

- `nginx/`: Nginx reverse proxy configuration
- `prometheus/`: Prometheus monitoring configuration
- `grafana/`: Grafana dashboards and provisioning
- `otelcol/`: OpenTelemetry collector configuration
- `postgres/`: Database initialization scripts

### Dockerfiles

- `services/api/Dockerfile`: FastAPI service
- `services/worker/Dockerfile`: Celery worker
- `apps/web/Dockerfile`: Next.js application

## Environment Variables

Key environment variables (see `.env.example`):

```bash
# Database
POSTGRES_DB=ghostworks
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Security
JWT_SECRET_KEY=your-secret-key-change-in-production

# Ports
API_PORT=8000
WEB_PORT=3000
GRAFANA_PORT=3001
PROMETHEUS_PORT=9090
```

## Common Commands

### Development

```bash
# Start all services
make up

# View logs
make logs

# Restart services
make restart

# Stop services
make down
```

### Production

```bash
# Build for production
make prod-build

# Start production stack
make prod-up

# View production logs
make prod-logs
```

### Individual Services

```bash
# Start only API and dependencies
make api

# Start only web service
make web

# Start observability stack
make observability
```

### Database Management

```bash
# Run migrations
make db-migrate

# Reset database (WARNING: destroys data)
make db-reset

# Open database shell
make shell-db
```

### Monitoring

```bash
# Check service health
make health

# Open Prometheus
make metrics

# Open Grafana
make dashboards

# Open Celery Flower
make flower
```

## Networking

All services communicate through the `ghostworks-network` bridge network:

- Internal service-to-service communication uses service names
- External access is routed through nginx proxy
- Database and Redis are not exposed externally in production

## Volumes

Persistent data volumes:

- `postgres_data`: Database files
- `redis_data`: Redis persistence
- `prometheus_data`: Metrics storage
- `grafana_data`: Dashboard configurations
- `api_logs`, `worker_logs`, `nginx_logs`: Application logs

## Security Considerations

### Development

- Default passwords are used (change for production)
- All services are accessible directly
- Debug logging is enabled
- Hot reloading is enabled

### Production

- Strong passwords required
- Services only accessible through nginx
- Resource limits enforced
- Structured logging
- Health checks enabled

## Troubleshooting

### Common Issues

1. **Port conflicts**: Check if ports are already in use
2. **Permission issues**: Ensure Docker has proper permissions
3. **Memory issues**: Increase Docker memory allocation
4. **Network issues**: Check firewall settings

### Debugging

```bash
# View service logs
docker-compose logs [service-name]

# Check service status
docker-compose ps

# Inspect service configuration
docker-compose config

# Execute commands in containers
docker-compose exec [service-name] [command]
```

### Health Checks

All services include health checks:

```bash
# Check individual service health
docker-compose ps

# Test API health endpoint
curl http://localhost:8000/api/v1/health

# Test web application
curl http://localhost:3000/health
```

## Performance Tuning

### Resource Limits

Production configuration includes resource limits:

- API: 512MB RAM, 0.5 CPU
- Worker: 512MB RAM, 0.5 CPU
- Web: 256MB RAM, 0.25 CPU
- Database: 1GB RAM, 1.0 CPU

### Scaling

Scale services horizontally:

```bash
# Scale API service
docker-compose up -d --scale api=3

# Scale worker service
docker-compose up -d --scale worker=2
```

## Monitoring and Observability

### Metrics

- **Prometheus**: Collects metrics from all services
- **Grafana**: Visualizes metrics with pre-built dashboards
- **OpenTelemetry**: Distributed tracing and telemetry

### Logs

- **Structured logging**: JSON format for all services
- **Log rotation**: Automatic log file rotation
- **Centralized collection**: All logs available through Docker

### Alerts

Configure alerts in Grafana for:

- High error rates
- Slow response times
- Resource utilization
- Service availability

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres ghostworks > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U postgres ghostworks < backup.sql
```

### Volume Backup

```bash
# Backup all volumes
docker run --rm -v ghostworks_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

## Development Workflow

1. **Start services**: `make up`
2. **Make changes**: Edit code (hot reload enabled)
3. **Run tests**: Execute in containers or locally
4. **Check logs**: `make logs`
5. **Debug**: Use service shells (`make shell-api`)
6. **Monitor**: Use Grafana dashboards
7. **Stop services**: `make down`

This Docker setup provides a complete development and production environment for the Ghostworks platform with comprehensive observability and monitoring capabilities.