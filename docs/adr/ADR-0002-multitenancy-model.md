# ADR-0002: Multi-tenancy Model and Tenant Isolation

## Status
Accepted

## Context
Ghostworks is a multi-tenant SaaS platform where multiple organizations (tenants) share the same application infrastructure while maintaining complete data isolation. The platform must ensure that:

1. Tenant data is completely isolated and secure
2. Performance remains consistent across tenants
3. The system can scale to support many tenants
4. Operational complexity is manageable
5. Compliance requirements (SOC2, GDPR) can be met
6. Development and testing workflows remain efficient

Critical security requirements:
- No tenant can access another tenant's data under any circumstances
- Database-level isolation prevents application bugs from causing data leaks
- Audit trails must track all cross-tenant access attempts
- Performance isolation prevents one tenant from affecting others

## Decision
We have implemented a **Row-Level Security (RLS) based multi-tenancy model** with the following architecture:

### Database-Level Isolation
1. **Single Database, Multiple Tenants**: All tenants share the same PostgreSQL database
2. **Row-Level Security (RLS)**: PostgreSQL RLS policies enforce tenant isolation at the database level
3. **Tenant Context**: Application sets `app.current_tenant_id` session variable for all queries
4. **Foreign Key Constraints**: All domain tables include `tenant_id` with proper foreign key relationships

### Application-Level Implementation
```sql
-- Enable RLS on all tenant-specific tables
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;

-- Create isolation policy
CREATE POLICY tenant_isolation ON artifacts 
FOR ALL TO authenticated_users 
USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Ensure tenant context is always set
CREATE OR REPLACE FUNCTION ensure_tenant_context()
RETURNS TRIGGER AS $$
BEGIN
    IF current_setting('app.current_tenant_id', true) IS NULL THEN
        RAISE EXCEPTION 'Tenant context not set';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Middleware Implementation
```python
@app.middleware("http")
async def tenant_isolation_middleware(request: Request, call_next):
    """Set tenant context for all database operations."""
    tenant_id = extract_tenant_from_request(request)
    
    if tenant_id and request.url.path.startswith("/api/"):
        # Set tenant context for database session
        await set_tenant_context(tenant_id)
    
    response = await call_next(request)
    return response
```

### Schema Design
```sql
-- Core tenant table
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- All domain tables include tenant_id
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workspace membership for RBAC
CREATE TABLE workspace_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, tenant_id)
);
```

## Alternatives Considered

### 1. Database-per-Tenant
**Description**: Each tenant gets their own PostgreSQL database.

**Pros**:
- Complete physical isolation
- Easy backup and restore per tenant
- Can optimize database settings per tenant
- Simpler application logic (no tenant context needed)

**Cons**:
- High operational overhead (managing hundreds of databases)
- Expensive resource usage (connection pools per database)
- Complex schema migrations across all databases
- Difficult cross-tenant analytics and reporting
- Higher infrastructure costs

**Rejected**: Operational complexity and cost outweigh benefits for our scale.

### 2. Schema-per-Tenant
**Description**: Each tenant gets their own PostgreSQL schema within a shared database.

**Pros**:
- Good isolation with shared infrastructure
- Easier than database-per-tenant to manage
- Can set different permissions per schema

**Cons**:
- Complex connection routing logic
- Schema migrations still complex
- PostgreSQL schema limits (performance degrades with many schemas)
- Application complexity for schema switching

**Rejected**: Still too complex for the benefits provided.

### 3. Application-Level Filtering Only
**Description**: Single database with tenant_id filtering in application code only.

**Pros**:
- Simplest to implement initially
- Best performance (no RLS overhead)
- Easy cross-tenant operations

**Cons**:
- **Critical Security Risk**: Application bugs can cause data leaks
- No database-level protection
- Difficult to audit and verify isolation
- Compliance challenges

**Rejected**: Security risks are unacceptable for a SaaS platform.

### 4. Hybrid: Critical Data Separate, Shared Analytics
**Description**: Tenant-specific data in separate databases, shared analytics database.

**Pros**:
- Maximum security for sensitive data
- Shared analytics capabilities

**Cons**:
- Complex data synchronization
- Operational overhead of multiple approaches
- Difficult to maintain consistency

**Rejected**: Complexity outweighs benefits for our current requirements.

## Consequences

### Positive Consequences

1. **Security**: Database-level isolation prevents application bugs from causing data leaks
2. **Compliance**: RLS provides auditable tenant isolation for SOC2/GDPR requirements
3. **Operational Simplicity**: Single database to manage, backup, and monitor
4. **Cost Efficiency**: Shared infrastructure reduces per-tenant costs
5. **Development Velocity**: Single codebase and database schema to maintain
6. **Analytics**: Cross-tenant analytics possible with proper authorization
7. **Scalability**: PostgreSQL can handle thousands of tenants with proper indexing

### Negative Consequences

1. **Performance Overhead**: RLS adds small query overhead (~5-10%)
2. **Query Complexity**: All queries must include tenant context
3. **Testing Complexity**: Must test tenant isolation thoroughly
4. **Migration Risks**: Schema changes affect all tenants simultaneously
5. **Noisy Neighbor**: One tenant's heavy usage can affect others
6. **Backup Granularity**: Cannot backup individual tenants easily

### Risk Mitigation Strategies

1. **Performance Monitoring**: 
   - Comprehensive metrics on RLS policy performance
   - Query optimization for tenant-specific indexes
   - Connection pooling optimization

2. **Testing Strategy**:
   - Automated tests for tenant isolation
   - Load testing with multiple tenants
   - Security penetration testing

3. **Operational Safeguards**:
   - Database query monitoring and alerting
   - Automated tenant context validation
   - Regular security audits of RLS policies

4. **Backup Strategy**:
   - Point-in-time recovery capabilities
   - Logical backups with tenant filtering
   - Disaster recovery procedures

## Implementation Details

### Tenant Context Management
```python
class TenantContextManager:
    """Manages tenant context for database operations."""
    
    async def set_tenant_context(self, session: AsyncSession, tenant_id: str):
        """Set tenant context for the database session."""
        await session.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        )
    
    async def clear_tenant_context(self, session: AsyncSession):
        """Clear tenant context (for system operations)."""
        await session.execute(text("RESET app.current_tenant_id"))
```

### Authorization Integration
```python
@require_workspace_access("admin")
async def create_artifact(
    artifact_data: ArtifactCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace)
):
    """Create artifact with automatic tenant isolation."""
    # Tenant context automatically set by middleware
    # RLS ensures artifact is created in correct tenant
    return await artifact_service.create(artifact_data, current_user.id)
```

### Monitoring and Alerting
- Monitor RLS policy performance impact
- Alert on tenant context violations
- Track cross-tenant access attempts
- Monitor per-tenant resource usage

## Testing Strategy

### Isolation Testing
```python
async def test_tenant_isolation():
    """Verify complete tenant data isolation."""
    # Create data in tenant A
    tenant_a_artifact = await create_artifact(tenant_a_context, artifact_data)
    
    # Switch to tenant B context
    set_tenant_context(tenant_b_id)
    
    # Verify tenant A data is not accessible
    with pytest.raises(ArtifactNotFoundError):
        await get_artifact(tenant_a_artifact.id)
```

### Performance Testing
- Benchmark RLS overhead with realistic data volumes
- Test query performance with multiple tenants
- Validate connection pool efficiency

## Migration Path
1. **Phase 1**: Implement RLS policies on existing tables
2. **Phase 2**: Add tenant context middleware and validation
3. **Phase 3**: Comprehensive testing and security audit
4. **Phase 4**: Production deployment with monitoring

## References
- [PostgreSQL Row Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Multi-tenant SaaS Database Tenancy Patterns](https://docs.microsoft.com/en-us/azure/sql-database/saas-tenancy-app-design-patterns)
- [Building Multi-tenant Applications with PostgreSQL](https://www.citusdata.com/blog/2016/10/03/designing-your-saas-database-for-high-scalability/)
- [OWASP Multi-tenancy Security](https://cheatsheetseries.owasp.org/cheatsheets/Multitenant_Architecture_Cheat_Sheet.html)