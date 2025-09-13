# Database Setup and Management

This document describes the database setup and management for the Ghostworks SaaS API service.

## Overview

The API uses PostgreSQL with SQLAlchemy 2.0 (async) and Alembic for migrations. The database implements:

- **Multi-tenant architecture** with Row-Level Security (RLS)
- **Async connection pooling** for high performance
- **Comprehensive data models** for tenants, users, workspace memberships, and artifacts
- **Full-text search** capabilities with PostgreSQL extensions

## Database Models

### Core Models

1. **Tenant** - Represents workspaces/organizations
   - Multi-tenant isolation boundary
   - Configurable settings via JSONB
   - Unique slug for URL-friendly identifiers

2. **User** - User authentication and profiles
   - Email-based authentication
   - Profile information (first/last name)
   - Account verification and status

3. **WorkspaceMembership** - Role-based access control
   - Links users to tenants with roles (Owner, Admin, Member)
   - Hierarchical permission system
   - Active/inactive membership status

4. **Artifact** - Main business entities
   - Tenant-isolated with RLS policies
   - Flexible metadata via JSONB
   - Tag-based categorization
   - Full-text search support

## Multi-Tenant Security

### Row-Level Security (RLS)

The `artifacts` table uses PostgreSQL RLS to ensure tenant isolation:

```sql
-- Enable RLS on artifacts table
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;

-- Create policy for tenant isolation
CREATE POLICY tenant_isolation ON artifacts 
FOR ALL TO authenticated_users 
USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

### Tenant Context

Use `get_tenant_session()` to automatically set tenant context:

```python
async with get_tenant_session(tenant_id) as session:
    # All queries automatically filtered by tenant_id
    artifacts = await session.execute(select(Artifact))
```

## Database Connection

### Configuration

Database settings are managed via Pydantic Settings:

```python
# Environment variables
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ghostworks_dev
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_ECHO=false
```

### Connection Pooling

- **Production**: QueuePool with configurable size and overflow
- **Testing**: NullPool to avoid connection issues
- **Features**: Pre-ping validation, connection recycling, health checks

## Migrations

### Initial Setup

1. **Create database** (if it doesn't exist):
   ```bash
   python scripts/init_db.py
   ```

2. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

### Creating New Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Review and edit the generated migration file
# Then apply the migration
alembic upgrade head
```

### Migration Files

- Location: `alembic/versions/`
- Naming: `YYYY_MM_DD_HHMM-{revision}_{slug}.py`
- Include both `upgrade()` and `downgrade()` functions

## Database Extensions

The following PostgreSQL extensions are required:

- **uuid-ossp**: UUID generation functions
- **pg_trgm**: Trigram matching for full-text search

These are automatically enabled in the initial migration.

## Indexes and Performance

### Optimized Indexes

1. **Primary Keys**: UUID with B-tree indexes
2. **Foreign Keys**: Automatic indexes for relationships
3. **Tenant Queries**: Composite index on `(tenant_id, created_at)`
4. **Tag Search**: GIN index on tag arrays
5. **Metadata Search**: GIN index on JSONB metadata
6. **Full-text Search**: GIN trigram indexes on text fields

### Query Performance

- Use `EXPLAIN ANALYZE` to analyze query performance
- Monitor slow queries via database logs
- Consider additional indexes for specific query patterns

## Health Checks

The database health check endpoint (`/health/detailed`) provides:

- Connection status
- Pool statistics (active, idle, overflow connections)
- Response time metrics
- Error reporting

## Testing

### Test Database

Tests use a separate test database with:

- NullPool for connection management
- Isolated test data via fixtures
- Automatic cleanup between tests

### Running Tests

```bash
# Run all database tests
pytest tests/test_database.py -v

# Run model tests
pytest tests/test_models.py -v

# Run all tests
pytest tests/ -v
```

## Troubleshooting

### Common Issues

1. **Database doesn't exist**:
   ```bash
   python scripts/init_db.py
   ```

2. **Migration conflicts**:
   ```bash
   alembic heads  # Check for multiple heads
   alembic merge -m "Merge migrations"  # Merge if needed
   ```

3. **Connection pool exhaustion**:
   - Check `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW`
   - Monitor connection usage in health checks
   - Ensure proper session cleanup

4. **RLS policy issues**:
   - Verify tenant context is set: `current_setting('app.current_tenant_id')`
   - Check user has `authenticated_users` role
   - Review policy conditions

### Debugging

Enable SQL query logging:

```bash
export DATABASE_ECHO=true
```

Or set in configuration:

```python
settings.database_echo = True
```

## Security Considerations

1. **Connection Security**:
   - Use SSL connections in production
   - Rotate database credentials regularly
   - Limit database user permissions

2. **Data Protection**:
   - RLS policies enforce tenant isolation
   - Input validation via Pydantic models
   - Parameterized queries prevent SQL injection

3. **Access Control**:
   - Database users have minimal required permissions
   - Application-level authorization via workspace roles
   - Audit logging for sensitive operations

## Backup and Recovery

1. **Regular Backups**:
   - Automated daily backups
   - Point-in-time recovery capability
   - Cross-region backup replication

2. **Disaster Recovery**:
   - Documented recovery procedures
   - Regular recovery testing
   - RTO/RPO targets defined

## Monitoring

Key metrics to monitor:

- Connection pool utilization
- Query performance and slow queries
- Database size and growth
- Replication lag (if applicable)
- Error rates and connection failures