-- Initialize Ghostworks database
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create application user (if not using default postgres user)
-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ghostworks_app') THEN
--         CREATE ROLE ghostworks_app WITH LOGIN PASSWORD 'app_password';
--     END IF;
-- END
-- $$;

-- Grant necessary permissions
-- GRANT CONNECT ON DATABASE ghostworks TO ghostworks_app;
-- GRANT USAGE ON SCHEMA public TO ghostworks_app;
-- GRANT CREATE ON SCHEMA public TO ghostworks_app;

-- Set up Row Level Security function for multi-tenancy
CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS UUID AS $$
BEGIN
    RETURN COALESCE(
        NULLIF(current_setting('app.current_tenant_id', true), ''),
        '00000000-0000-0000-0000-000000000000'
    )::UUID;
END;
$$ LANGUAGE plpgsql STABLE;

-- Create a function to set tenant context
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_uuid UUID) RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', tenant_uuid::text, true);
END;
$$ LANGUAGE plpgsql;

-- Create indexes for better performance
-- These will be created by Alembic migrations, but we can prepare the database

-- Log successful initialization
INSERT INTO pg_stat_statements_info (dealloc) VALUES (0) ON CONFLICT DO NOTHING;

-- Create a simple health check table
CREATE TABLE IF NOT EXISTS health_check (
    id SERIAL PRIMARY KEY,
    status TEXT DEFAULT 'healthy',
    last_check TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO health_check (status) VALUES ('initialized') ON CONFLICT DO NOTHING;