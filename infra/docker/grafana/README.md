# Ghostworks Grafana Configuration

This directory contains the complete Grafana configuration for the Ghostworks platform, including dashboards, alerting rules, and notification channels.

## Dashboard Overview

### 1. System Overview (`system-overview.json`)
**UID:** `ghostworks-system-overview`

The main dashboard providing a high-level view of the entire platform:
- Service health status for all components
- Key performance indicators (KPIs)
- API traffic and error trends
- Resource utilization metrics
- Business activity trends
- Task processing health

**Use Case:** First dashboard to check for overall system health and quick issue identification.

### 2. API Golden Signals (`api-golden-signals.json`)
**UID:** `ghostworks-api-golden-signals`

Focused on the four golden signals of monitoring for the API service:
- **Latency:** P95 and P50 response times
- **Traffic:** Request rate per second
- **Errors:** 4xx and 5xx error rates
- **Saturation:** Requests in progress, database connections

**Use Case:** Deep dive into API performance and troubleshooting API-related issues.

### 3. Business Metrics (`business-metrics.json`)
**UID:** `ghostworks-business-metrics`

Business-focused metrics for understanding platform usage:
- Total artifacts created and user registrations
- Authentication success rates
- Artifact creation rates by tenant
- Workspace operations by type
- Artifact search performance
- Celery task processing metrics

**Use Case:** Understanding business growth, tenant activity, and feature usage patterns.

### 4. Worker Metrics (`worker-metrics.json`)
**UID:** `ghostworks-worker-metrics`

Comprehensive Celery worker monitoring:
- Task processing statistics
- Task duration percentiles
- Email task processing
- Data processing and maintenance tasks
- Queue length monitoring
- Task success/failure rates

**Use Case:** Monitoring background job processing and queue health.

## Alerting Configuration

### Alert Rules (`provisioning/alerting/rules.yml`)

#### Critical Alerts
- **API Error Rate High:** Triggers when 5xx error rate > 5% for 2 minutes
- **API Latency High:** Triggers when P95 latency > 500ms for 2 minutes

#### Warning Alerts
- **Database Connections High:** Triggers when active connections > 20 for 5 minutes
- **Celery Task Failure Rate High:** Triggers when task failure rate > 10% for 3 minutes

### Notification Channels (`provisioning/alerting/contact-points.yml`)

#### Default Receiver
- Webhook notifications to `${WEBHOOK_URL}`
- General purpose alerts with basic formatting

#### Critical Alerts
- Webhook to `${CRITICAL_WEBHOOK_URL}`
- Email to `${CRITICAL_EMAIL_ADDRESSES}`
- Enhanced formatting with runbook links
- Immediate notification (5s group wait)

#### Warning Alerts
- Webhook to `${WARNING_WEBHOOK_URL}`
- Standard formatting
- 10s group wait, 1h repeat interval

## Environment Variables

Configure these environment variables for alerting:

```bash
# Webhook URLs for alert notifications
WEBHOOK_URL=http://localhost:3000/api/alerts/webhook
CRITICAL_WEBHOOK_URL=http://localhost:3000/api/alerts/critical
WARNING_WEBHOOK_URL=http://localhost:3000/api/alerts/warning

# Email configuration for critical alerts
CRITICAL_EMAIL_ADDRESSES=admin@ghostworks.dev,ops@ghostworks.dev

# Grafana admin credentials
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
```

## Dashboard Access

Once the system is running, access dashboards at:

- **System Overview:** http://localhost:3001/d/ghostworks-system-overview
- **API Golden Signals:** http://localhost:3001/d/ghostworks-api-golden-signals
- **Business Metrics:** http://localhost:3001/d/ghostworks-business-metrics
- **Worker Metrics:** http://localhost:3001/d/ghostworks-worker-metrics

Default login: `admin` / `admin` (configurable via environment variables)

## Metrics Sources

### API Service Metrics (`api:8000/metrics`)
- HTTP request metrics (rate, duration, errors)
- Business metrics (artifacts, users, auth attempts)
- Database connection metrics
- Custom application metrics

### Worker Service Metrics (`worker:8001/metrics`)
- Celery task metrics (duration, success/failure)
- Queue length monitoring
- Email, data processing, and maintenance task metrics
- Worker health metrics

### OpenTelemetry Collector (`otelcol:8889/metrics`)
- Distributed tracing metrics
- Service mesh observability
- Cross-service correlation data

## Customization

### Adding New Dashboards
1. Create JSON file in `dashboards/` directory
2. Use unique UID in format `ghostworks-{name}`
3. Add appropriate tags for organization
4. Dashboard will be auto-provisioned on restart

### Modifying Alert Rules
1. Edit `provisioning/alerting/rules.yml`
2. Follow existing format for consistency
3. Include runbook URLs for operational guidance
4. Test thresholds in development environment

### Adding Notification Channels
1. Update `provisioning/alerting/contact-points.yml`
2. Configure routing in `provisioning/alerting/notification-policies.yml`
3. Set appropriate environment variables
4. Test notification delivery

## Troubleshooting

### Dashboard Not Loading
- Check Prometheus data source connectivity
- Verify metric names match those exposed by services
- Check Grafana logs: `docker logs ghostworks-grafana`

### Alerts Not Firing
- Verify Prometheus is scraping metrics correctly
- Check alert rule syntax in Grafana UI
- Confirm notification channel configuration
- Test with manual alert evaluation

### Missing Metrics
- Ensure services are exposing metrics endpoints
- Check Prometheus configuration and targets
- Verify network connectivity between services
- Review service logs for metric collection errors

## Performance Considerations

### Dashboard Refresh Rates
- System Overview: 5s (real-time monitoring)
- API Golden Signals: 5s (performance critical)
- Business Metrics: 5s (user activity tracking)
- Worker Metrics: 5s (task processing monitoring)

### Query Optimization
- Use appropriate time ranges for queries
- Leverage Prometheus recording rules for complex calculations
- Consider dashboard variables for filtering large datasets
- Monitor Grafana query performance in production

## Security Notes

- Change default Grafana credentials in production
- Use HTTPS for Grafana access in production
- Secure webhook endpoints with authentication
- Limit dashboard access based on user roles
- Regularly review and rotate notification credentials