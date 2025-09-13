# Monitoring Runbook

This runbook covers monitoring setup, maintenance, and troubleshooting for the Ghostworks SaaS platform.

## 🎯 Overview

The Ghostworks platform implements comprehensive observability using the OpenTelemetry, Prometheus, and Grafana stack. This provides metrics, traces, and logs for complete system visibility.

## 📊 Monitoring Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │  OpenTelemetry  │    │   Prometheus    │
│    Services     │───▶│   Collector     │───▶│    Server       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │     Tempo       │              │
         └─────────────▶│   (Traces)      │              │
                        └─────────────────┘              │
                                 │                       │
                        ┌─────────────────┐              │
                        │    Grafana      │◀─────────────┘
                        │  (Dashboards)   │
                        └─────────────────┘
```

## 🔧 Monitoring Stack Components

### OpenTelemetry Collector
- **Purpose**: Collects, processes, and exports telemetry data
- **Configuration**: `infra/docker/otelcol/otelcol-config.yml`
- **Port**: 4317 (gRPC), 4318 (HTTP)

### Prometheus
- **Purpose**: Metrics collection and storage
- **Configuration**: `infra/docker/prometheus/prometheus.yml`
- **Port**: 9090
- **Retention**: 15 days (configurable)

### Grafana
- **Purpose**: Visualization and alerting
- **Configuration**: `infra/docker/grafana/`
- **Port**: 3001
- **Credentials**: admin/admin (change in production)

### Tempo (Optional)
- **Purpose**: Distributed tracing storage
- **Configuration**: `infra/docker/tempo/tempo.yml`
- **Port**: 3200

## 📈 Key Metrics

### Golden Signals

#### Latency
```promql
# API response time percentiles
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Database query duration
histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))
```

#### Traffic
```promql
# Requests per second
rate(http_requests_total[5m])

# Requests by endpoint
sum(rate(http_requests_total[5m])) by (endpoint)

# Active users
increase(user_login_total[1h])
```

#### Errors
```promql
# Error rate percentage
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# Error count by service
sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)

# Database errors
rate(db_errors_total[5m])
```

#### Saturation
```promql
# CPU usage
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Database connections
db_connections_active / db_connections_max * 100
```

### Business Metrics

```promql
# User registrations
increase(user_registrations_total[1d])

# Artifacts created
increase(artifacts_created_total[1d])

# Workspace activity
sum(rate(workspace_activity_total[5m])) by (tenant_id)

# Revenue metrics (if applicable)
increase(subscription_revenue_total[1d])
```

### System Metrics

```promql
# Disk usage
(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100

# Network I/O
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])

# Container metrics
container_memory_usage_bytes
container_cpu_usage_seconds_total
```

## 🚨 Alerting Rules

### Critical Alerts

#### High Error Rate
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100 > 5
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value }}% for the last 5 minutes"
```

#### High Latency
```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High latency detected"
    description: "95th percentile latency is {{ $value }}s"
```

#### Database Issues
```yaml
- alert: DatabaseConnectionsHigh
  expr: db_connections_active / db_connections_max * 100 > 80
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Database connections high"
    description: "Database connection usage is {{ $value }}%"

- alert: DatabaseDown
  expr: up{job="postgres"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Database is down"
    description: "PostgreSQL database is not responding"
```

#### System Resources
```yaml
- alert: HighCPUUsage
  expr: 100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High CPU usage"
    description: "CPU usage is {{ $value }}% on {{ $labels.instance }}"

- alert: HighMemoryUsage
  expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "High memory usage"
    description: "Memory usage is {{ $value }}% on {{ $labels.instance }}"

- alert: DiskSpaceLow
  expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 90
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Disk space low"
    description: "Disk usage is {{ $value }}% on {{ $labels.instance }}"
```

### Warning Alerts

#### Performance Degradation
```yaml
- alert: PerformanceDegradation
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.2
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Performance degradation detected"
    description: "95th percentile latency is {{ $value }}s"
```

#### Queue Backlog
```yaml
- alert: CeleryQueueBacklog
  expr: celery_queue_length > 100
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Celery queue backlog"
    description: "Queue length is {{ $value }} tasks"
```

## 📊 Grafana Dashboards

### API Golden Signals Dashboard

**Panels:**
1. **Request Rate** - Requests per second over time
2. **Error Rate** - Error percentage over time
3. **Response Time** - Latency percentiles (P50, P95, P99)
4. **Throughput** - Total requests by endpoint
5. **Status Codes** - Distribution of HTTP status codes
6. **Top Endpoints** - Most frequently accessed endpoints

**Queries:**
```promql
# Request rate
sum(rate(http_requests_total[5m])) by (service)

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) by (service) / sum(rate(http_requests_total[5m])) by (service) * 100

# Response time
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))
```

### Business Metrics Dashboard

**Panels:**
1. **Active Users** - Current active user count
2. **User Registrations** - New registrations over time
3. **Artifact Creation** - Artifacts created per day
4. **Workspace Activity** - Activity by workspace
5. **Revenue Metrics** - Subscription and usage metrics
6. **Feature Usage** - Most used features

### System Overview Dashboard

**Panels:**
1. **Service Health** - Up/down status of all services
2. **Resource Usage** - CPU, memory, disk usage
3. **Database Performance** - Query performance and connections
4. **Network I/O** - Network traffic patterns
5. **Container Metrics** - Docker container resource usage
6. **Log Volume** - Log messages per service

## 🔍 Log Management

### Structured Logging Format

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "api",
  "request_id": "req_123456",
  "tenant_id": "tenant_uuid",
  "user_id": "user_uuid",
  "operation": "artifact.create",
  "duration_ms": 45,
  "status": "success",
  "message": "Artifact created successfully",
  "metadata": {
    "artifact_id": "artifact_uuid",
    "tags": ["demo", "widget"]
  }
}
```

### Log Aggregation

**ELK Stack (Optional):**
```yaml
# docker-compose.logging.yml
services:
  elasticsearch:
    image: elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

  logstash:
    image: logstash:8.5.0
    volumes:
      - ./infra/logstash/pipeline:/usr/share/logstash/pipeline
    depends_on:
      - elasticsearch

  kibana:
    image: kibana:8.5.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

### Log Queries

**Common Log Searches:**
```bash
# Errors in the last hour
grep -E '"level":"ERROR"' /var/log/ghostworks/api.log | jq -r '.timestamp, .message'

# Requests by user
grep -E '"user_id":"user_123"' /var/log/ghostworks/api.log | jq -r '.operation, .timestamp'

# Slow queries
grep -E '"duration_ms":[0-9]{4,}' /var/log/ghostworks/api.log | jq -r '.operation, .duration_ms'
```

## 🔧 Monitoring Setup

### Initial Setup

1. **Start Monitoring Stack**
   ```bash
   docker-compose up -d prometheus grafana otelcol
   ```

2. **Import Dashboards**
   ```bash
   # Dashboards are automatically provisioned from infra/docker/grafana/dashboards/
   # Manual import via Grafana UI if needed
   ```

3. **Configure Alerts**
   ```bash
   # Alert rules are in infra/docker/grafana/provisioning/alerting/rules.yml
   # Notification channels configured in provisioning/alerting/
   ```

4. **Verify Setup**
   ```bash
   # Check Prometheus targets
   curl http://localhost:9090/api/v1/targets

   # Check Grafana health
   curl http://localhost:3001/api/health

   # Verify metrics collection
   curl http://localhost:8000/metrics
   ```

### Configuration Updates

**Adding New Metrics:**
1. Update application code to expose metrics
2. Add Prometheus scrape configuration
3. Create/update Grafana dashboards
4. Add relevant alert rules

**Modifying Alert Rules:**
1. Edit `infra/docker/grafana/provisioning/alerting/rules.yml`
2. Restart Grafana service
3. Verify rules in Grafana UI

**Dashboard Updates:**
1. Export dashboard JSON from Grafana
2. Save to `infra/docker/grafana/dashboards/`
3. Commit to version control

## 🚨 Incident Response

### Alert Triage

**Priority Levels:**
- **P0 (Critical)**: Service down, data loss, security breach
- **P1 (High)**: Significant performance degradation, partial outage
- **P2 (Medium)**: Minor performance issues, non-critical features affected
- **P3 (Low)**: Cosmetic issues, monitoring alerts

### Response Procedures

**High Error Rate Alert:**
1. Check Grafana dashboard for affected services
2. Review recent deployments
3. Check application logs for error patterns
4. Verify database connectivity
5. Consider rollback if recent deployment

**High Latency Alert:**
1. Identify slow endpoints from metrics
2. Check database query performance
3. Review system resource usage
4. Check for external service dependencies
5. Scale resources if needed

**Database Issues:**
1. Check database connectivity
2. Review connection pool settings
3. Identify slow queries
4. Check disk space and I/O
5. Consider read replica failover

### Escalation Matrix

| Alert Type | Response Time | Escalation |
|------------|---------------|------------|
| P0 Critical | 5 minutes | Immediate |
| P1 High | 15 minutes | 30 minutes |
| P2 Medium | 1 hour | 4 hours |
| P3 Low | 4 hours | Next business day |

## 📋 Maintenance Tasks

### Daily Tasks
- [ ] Review overnight alerts
- [ ] Check system resource usage
- [ ] Verify backup completion
- [ ] Monitor error rates and performance

### Weekly Tasks
- [ ] Review and update alert thresholds
- [ ] Analyze performance trends
- [ ] Update monitoring documentation
- [ ] Test alert notification channels

### Monthly Tasks
- [ ] Review and optimize dashboards
- [ ] Update monitoring stack components
- [ ] Conduct monitoring system health check
- [ ] Review and update runbooks

### Quarterly Tasks
- [ ] Comprehensive monitoring system review
- [ ] Update monitoring strategy
- [ ] Conduct disaster recovery testing
- [ ] Review and update SLAs/SLOs

## 🔍 Troubleshooting

### Common Issues

**Metrics Not Appearing:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify application metrics endpoint
curl http://localhost:8000/metrics

# Check OpenTelemetry collector logs
docker-compose logs otelcol
```

**Grafana Dashboard Issues:**
```bash
# Check Grafana logs
docker-compose logs grafana

# Verify data source configuration
curl -u admin:admin http://localhost:3001/api/datasources

# Test Prometheus connectivity from Grafana
curl -u admin:admin http://localhost:3001/api/datasources/proxy/1/api/v1/query?query=up
```

**Alert Not Firing:**
```bash
# Check alert rule syntax
curl http://localhost:9090/api/v1/rules

# Verify alert manager configuration
curl http://localhost:9093/api/v1/status

# Test notification channels
curl -X POST http://localhost:3001/api/alerts/test
```

### Performance Issues

**High Memory Usage:**
1. Check for memory leaks in applications
2. Review Prometheus retention settings
3. Optimize Grafana dashboard queries
4. Consider increasing system resources

**Slow Dashboard Loading:**
1. Optimize PromQL queries
2. Reduce time range for heavy queries
3. Use recording rules for complex calculations
4. Consider query result caching

## 📞 Emergency Contacts

### On-Call Rotation
- **Primary**: Platform Team Lead
- **Secondary**: DevOps Engineer
- **Escalation**: Engineering Manager

### External Contacts
- **Infrastructure Provider**: [Contact Info]
- **Monitoring Vendor**: [Contact Info]
- **Database Support**: [Contact Info]

---

**Last Updated**: [Current Date]  
**Next Review**: [Next Month]