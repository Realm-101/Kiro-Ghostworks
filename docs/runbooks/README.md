# Operational Runbooks

This directory contains operational runbooks for the Ghostworks SaaS platform. These runbooks provide step-by-step procedures for common operational tasks, troubleshooting, and incident response.

## 📚 Available Runbooks

### Deployment & Infrastructure
- [**Deployment Guide**](deployment.md) - Complete deployment procedures for all environments
- [**Environment Setup**](environment-setup.md) - Setting up new environments and configurations
- [**Backup & Recovery**](backup-recovery.md) - Data backup and disaster recovery procedures

### Monitoring & Observability
- [**Monitoring Guide**](monitoring.md) - Comprehensive monitoring setup and maintenance
- [**Alert Response**](alert-response.md) - Procedures for responding to system alerts
- [**Performance Tuning**](performance-tuning.md) - System optimization and performance troubleshooting

### Troubleshooting
- [**Common Issues**](troubleshooting.md) - Solutions for frequently encountered problems
- [**Database Issues**](database-troubleshooting.md) - Database-specific troubleshooting procedures
- [**Network & Connectivity**](network-troubleshooting.md) - Network and service connectivity issues

### Security & Maintenance
- [**Security Incident Response**](security-incident-response.md) - Security incident handling procedures
- [**Maintenance Procedures**](maintenance.md) - Routine maintenance and updates
- [**User Management**](user-management.md) - User account and workspace management

## 🚨 Emergency Contacts

### On-Call Escalation
1. **Primary**: Platform Team Lead
2. **Secondary**: DevOps Engineer
3. **Escalation**: Engineering Manager

### External Contacts
- **Infrastructure Provider**: [Contact Info]
- **Security Team**: [Contact Info]
- **Database Administrator**: [Contact Info]

## 📋 Quick Reference

### Service URLs (Production)
- **Web Application**: https://app.ghostworks.dev
- **API**: https://api.ghostworks.dev
- **Grafana**: https://monitoring.ghostworks.dev
- **Prometheus**: https://metrics.ghostworks.dev

### Key Commands
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f [service]

# Restart service
docker-compose restart [service]

# Database backup
docker-compose exec postgres pg_dump -U postgres ghostworks > backup.sql

# Health checks
curl https://api.ghostworks.dev/api/v1/health
```

### Critical Thresholds
- **API Error Rate**: > 5% (Critical)
- **Response Time P95**: > 500ms (Warning), > 1s (Critical)
- **Database Connections**: > 80% (Warning), > 95% (Critical)
- **Disk Space**: < 20% (Warning), < 10% (Critical)
- **Memory Usage**: > 80% (Warning), > 90% (Critical)

## 🔄 Runbook Maintenance

### Review Schedule
- **Monthly**: Review and update procedures
- **Quarterly**: Test disaster recovery procedures
- **After Incidents**: Update based on lessons learned

### Version Control
All runbooks are version controlled and changes should be:
1. Reviewed by team lead
2. Tested in staging environment
3. Documented with change rationale

### Feedback
If you encounter issues with these runbooks or have suggestions for improvement, please:
1. Create an issue in the repository
2. Propose changes via pull request
3. Contact the platform team directly

---

**Last Updated**: [Current Date]  
**Next Review**: [Next Month]