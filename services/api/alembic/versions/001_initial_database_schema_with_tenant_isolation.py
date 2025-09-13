"""Initial database schema with tenant isolation

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema with tenant isolation."""
    
    # Enable required PostgreSQL extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    
    # Create tenants table
    op.create_table('tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Display name of the tenant/workspace'),
        sa.Column('slug', sa.String(length=100), nullable=False, comment='URL-friendly identifier for the tenant'),
        sa.Column('description', sa.Text(), nullable=True, comment='Optional description of the tenant/workspace'),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default=sa.text("'{}'::jsonb"), comment='Tenant-specific configuration settings'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='Whether the tenant is active and can be accessed'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_tenants_id'), 'tenants', ['id'], unique=False)
    op.create_index(op.f('ix_tenants_slug'), 'tenants', ['slug'], unique=False)
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(length=255), nullable=False, comment="User's email address (used for login)"),
        sa.Column('hashed_password', sa.String(length=255), nullable=False, comment='Bcrypt hashed password'),
        sa.Column('first_name', sa.String(length=100), nullable=True, comment="User's first name"),
        sa.Column('last_name', sa.String(length=100), nullable=True, comment="User's last name"),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False, comment="Whether the user's email has been verified"),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='Whether the user account is active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    
    # Create workspace_memberships table
    op.create_table('workspace_memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Reference to the user'),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Reference to the tenant/workspace'),
        sa.Column('role', sa.Enum('owner', 'admin', 'member', name='workspacerole'), nullable=False, comment="User's role within the workspace"),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='Whether the membership is active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant_membership')
    )
    op.create_index(op.f('ix_workspace_memberships_id'), 'workspace_memberships', ['id'], unique=False)
    op.create_index(op.f('ix_workspace_memberships_user_id'), 'workspace_memberships', ['user_id'], unique=False)
    op.create_index(op.f('ix_workspace_memberships_tenant_id'), 'workspace_memberships', ['tenant_id'], unique=False)
    
    # Create artifacts table
    op.create_table('artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Tenant ID for multi-tenant isolation'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Name of the artifact'),
        sa.Column('description', sa.Text(), nullable=True, comment='Detailed description of the artifact'),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=False, default=sa.text("'{}'::text[]"), comment='Tags for categorization and filtering'),
        sa.Column('artifact_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default=sa.text("'{}'::jsonb"), comment='Flexible metadata storage for artifact-specific data'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True, comment='User who created the artifact'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='Whether the artifact is active (soft delete support)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_artifacts_id'), 'artifacts', ['id'], unique=False)
    op.create_index(op.f('ix_artifacts_tenant_id'), 'artifacts', ['tenant_id'], unique=False)
    op.create_index('ix_artifacts_tenant_created', 'artifacts', ['tenant_id', 'created_at'], unique=False)
    op.create_index('ix_artifacts_tags', 'artifacts', ['tags'], unique=False, postgresql_using='gin')
    op.create_index('ix_artifacts_metadata', 'artifacts', ['artifact_metadata'], unique=False, postgresql_using='gin')
    op.create_index('ix_artifacts_search', 'artifacts', ['name', 'description'], unique=False, 
                   postgresql_using='gin', 
                   postgresql_ops={'name': 'gin_trgm_ops', 'description': 'gin_trgm_ops'})
    
    # Enable Row-Level Security on artifacts table
    op.execute('ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY')
    
    # Create RLS policy for tenant isolation
    op.execute("""
        CREATE POLICY tenant_isolation ON artifacts 
        FOR ALL TO authenticated_users 
        USING (tenant_id = COALESCE(current_setting('app.current_tenant_id', true)::uuid, '00000000-0000-0000-0000-000000000000'::uuid))
    """)
    
    # Create a role for authenticated users (this would typically be managed by your auth system)
    op.execute('CREATE ROLE IF NOT EXISTS authenticated_users')
    
    # Create trigger function for updating updated_at timestamps
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create triggers for updated_at columns
    for table in ['tenants', 'users', 'workspace_memberships', 'artifacts']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at 
            BEFORE UPDATE ON {table} 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    """Drop all tables and related objects."""
    
    # Drop triggers
    for table in ['tenants', 'users', 'workspace_memberships', 'artifacts']:
        op.execute(f'DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}')
    
    # Drop trigger function
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Drop RLS policy and role
    op.execute('DROP POLICY IF EXISTS tenant_isolation ON artifacts')
    op.execute('DROP ROLE IF EXISTS authenticated_users')
    
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_table('artifacts')
    op.drop_table('workspace_memberships')
    op.drop_table('users')
    op.drop_table('tenants')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS workspacerole')