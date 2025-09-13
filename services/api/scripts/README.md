# Demo Data Scripts

This directory contains scripts for managing demo data in the Ghostworks SaaS platform.

## Scripts Overview

### `seed_demo_data.py`
Main demo data seeding script that creates realistic demo data including:
- **2 Tenant Workspaces**: Acme Corp and Umbrella Inc
- **5 Demo Users** with different roles
- **13 Sample Artifacts** with varied metadata and tags

### `reset_demo_environment.py`
Complete database reset utility that:
- Drops all existing tables and data
- Recreates the database schema
- Seeds fresh demo data
- Includes safety confirmation prompts

### `seed_only.py`
Simple seeding script that only adds demo data without resetting the database.

### `init_db.py`
Database initialization script for setting up the database from scratch.

## Demo Data Details

### Tenants Created

#### Acme Corp (`acme-corp`)
- **Description**: A leading technology company specializing in innovative solutions
- **Plan**: Enterprise (100 users, 1TB storage)
- **Features**: Analytics, integrations, advanced search
- **Artifacts**: 7 technology-focused artifacts (dashboards, APIs, mobile apps, etc.)

#### Umbrella Inc (`umbrella-inc`)
- **Description**: Multinational biotechnology and pharmaceutical research corporation
- **Plan**: Professional (50 users, 500GB storage)
- **Features**: Compliance, audit trail, data retention
- **Artifacts**: 6 biotech-focused artifacts (clinical trials, drug discovery, lab systems, etc.)

### Demo User Accounts

| Email | Password | Tenant | Role | Name |
|-------|----------|--------|------|------|
| `owner@acme.com` | `SecurePass123!` | Acme Corp | Owner | Alice Johnson |
| `manager@acme.com` | `SecurePass123!` | Acme Corp | Admin | Eva Martinez |
| `member@acme.com` | `SecurePass123!` | Acme Corp | Member | Carol Davis |
| `admin@umbrella.com` | `SecurePass123!` | Umbrella Inc | Admin | Bob Smith |
| `researcher@umbrella.com` | `SecurePass123!` | Umbrella Inc | Member | David Wilson |

### Sample Artifacts

#### Acme Corp Artifacts
1. **Customer Analytics Dashboard** - Interactive analytics with performance metrics
2. **API Gateway Configuration** - Microservices routing and authentication
3. **Mobile App User Interface** - React Native components with accessibility
4. **Database Migration Scripts** - Cloud migration with rollback strategies
5. **Security Audit Report** - Compliance and vulnerability assessment
6. **Machine Learning Model** - Customer churn prediction with 94% accuracy
7. **CI/CD Pipeline Configuration** - Automated deployment with 98% success rate

#### Umbrella Inc Artifacts
1. **Clinical Trial Data Management** - FDA/EMA compliant trial system
2. **Drug Discovery Algorithm** - AI-driven molecular analysis
3. **Laboratory Information System** - Sample tracking and quality control
4. **Regulatory Submission Portal** - Health authority submission tracking
5. **Biomarker Analysis Pipeline** - Genomics and proteomics processing
6. **Patient Safety Database** - Adverse event tracking and pharmacovigilance

## Usage

### Using Docker Compose (Recommended)

```bash
# Initialize database and seed demo data (first time setup)
make init-demo

# Seed demo data to existing database
make seed-demo

# Reset database and seed fresh demo data (with confirmation)
make reset-demo-interactive

# Reset database and seed fresh demo data (no confirmation)
make reset-demo
```

### Direct Script Execution

```bash
# Navigate to the API service directory
cd services/api

# Seed demo data only
python scripts/seed_only.py

# Reset database with confirmation
python scripts/reset_demo_environment.py

# Reset database without confirmation
python scripts/reset_demo_environment.py --force

# Seed data only (without reset)
python scripts/reset_demo_environment.py --seed-only
```

### Environment Requirements

Ensure the following environment variables are set:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ghostworks
JWT_SECRET_KEY=your-secret-key-here
```

## Script Features

### Data Realism
- **Varied Creation Dates**: Artifacts created over the past 30-45 days
- **Realistic Metadata**: Technology stacks, performance metrics, compliance info
- **Diverse Tags**: Categorization reflecting real-world usage patterns
- **User Attribution**: Artifacts created by different users in each tenant

### Safety Features
- **Confirmation Prompts**: Interactive confirmation before destructive operations
- **Duplicate Prevention**: Checks for existing data before creation
- **Transaction Safety**: All operations wrapped in database transactions
- **Comprehensive Logging**: Detailed logging for troubleshooting

### Verification
- **Data Validation**: Verifies all data was created successfully
- **Count Reporting**: Shows summary of created entities
- **Health Checks**: Confirms database connectivity and schema

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check if PostgreSQL is running
   docker-compose ps postgres
   
   # Check database connectivity
   docker-compose exec postgres psql -U postgres -d ghostworks -c "SELECT 1;"
   ```

2. **Permission Errors**
   ```bash
   # Ensure scripts are executable
   chmod +x services/api/scripts/*.py
   ```

3. **Import Errors**
   ```bash
   # Run from the correct directory
   cd services/api
   python scripts/seed_demo_data.py
   ```

4. **Alembic Migration Issues**
   ```bash
   # Run migrations first
   docker-compose exec api alembic upgrade head
   ```

### Logs and Debugging

All scripts use structured logging. Check logs for detailed information:

```bash
# View API container logs
docker-compose logs api

# Run scripts with debug logging
LOG_LEVEL=DEBUG python scripts/seed_demo_data.py
```

## Development Notes

### Adding New Demo Data

To add new demo data:

1. **Tenants**: Add to `DEMO_TENANTS` list in `seed_demo_data.py`
2. **Users**: Add to `DEMO_USERS` list with tenant association
3. **Artifacts**: Add to tenant-specific artifact lists (`ACME_ARTIFACTS`, `UMBRELLA_ARTIFACTS`)

### Customizing Metadata

Artifact metadata supports any JSON structure. Common fields:
- `type`: Category of artifact (system, dashboard, algorithm, etc.)
- `technology`: Tech stack or platform
- `status`: Development status (production, development, research)
- `compliance`: Regulatory compliance information
- `performance_metrics`: Quantitative performance data

### Testing Changes

Always test script changes in a development environment:

```bash
# Test with a clean database
make clean
make up
make init-demo
```

## Security Considerations

- **Demo Passwords**: All demo accounts use the same password for simplicity
- **Production Warning**: Never run these scripts in production environments
- **Data Sensitivity**: Demo data is fictional but follows realistic patterns
- **Access Control**: Scripts require database access and should be run securely

## Integration with CI/CD

These scripts can be integrated into CI/CD pipelines for:
- **Testing Environments**: Automatic demo data seeding
- **Development Setup**: Onboarding new developers
- **Demo Environments**: Refreshing demo instances

Example GitHub Actions usage:
```yaml
- name: Seed Demo Data
  run: |
    docker-compose exec -T api python scripts/seed_only.py
```