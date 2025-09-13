# Screenshots Documentation

This directory contains screenshots of key UI flows and monitoring dashboards for the Ghostworks SaaS platform.

## 📸 Screenshot Categories

### User Interface Flows

#### Authentication Flow
- `auth-login-form.png` - Login form with validation
- `auth-registration-form.png` - User registration form
- `auth-workspace-selector.png` - Workspace selection dropdown
- `auth-workspace-switching.png` - Switching between workspaces

#### Artifact Management
- `artifacts-list-view.png` - Main artifact listing page with pagination
- `artifacts-search-filter.png` - Search and filtering interface
- `artifacts-create-modal.png` - Create new artifact modal
- `artifacts-edit-modal.png` - Edit artifact modal with tag management
- `artifacts-tag-autocomplete.png` - Tag input with autocomplete

#### Dashboard and Tour
- `tour-landing-page.png` - Interactive tour landing page
- `tour-metrics-dashboard.png` - Live metrics display
- `tour-asset-gardener.png` - Asset Gardener demonstration
- `tour-telemetry-demo.png` - Telemetry visualization

### Monitoring Dashboards

#### Grafana Dashboards
- `grafana-api-golden-signals.png` - API performance metrics (latency, throughput, errors)
- `grafana-business-metrics.png` - Business KPIs (users, artifacts, workspaces)
- `grafana-system-overview.png` - System resource monitoring
- `grafana-database-performance.png` - Database query performance and connections
- `grafana-alert-overview.png` - Active alerts and notification status

#### Prometheus Metrics
- `prometheus-targets.png` - Service discovery and target status
- `prometheus-query-interface.png` - PromQL query interface
- `prometheus-alerts.png` - Alert rules and firing status

### API Documentation
- `api-docs-swagger-ui.png` - OpenAPI documentation interface
- `api-docs-authentication.png` - Authentication endpoint documentation
- `api-docs-artifacts.png` - Artifact CRUD endpoint documentation
- `api-docs-error-responses.png` - Error response format examples

### Development Tools
- `mcp-configuration.png` - MCP server configuration interface
- `agent-hooks-interface.png` - Agent hooks management
- `ci-cd-pipeline.png` - GitHub Actions workflow status
- `test-results.png` - Comprehensive test suite results

## 📋 Screenshot Guidelines

### Capture Requirements

**Resolution**: 1920x1080 minimum for desktop views, 375x812 for mobile
**Format**: PNG for UI screenshots, JPG for photographs
**Quality**: High quality, no compression artifacts
**Content**: Include realistic demo data, avoid sensitive information

### Naming Convention

```
[category]-[feature]-[view].png

Examples:
- auth-login-form.png
- artifacts-list-view.png
- grafana-api-golden-signals.png
- tour-metrics-dashboard.png
```

### Content Standards

**UI Screenshots:**
- Use demo accounts (owner@acme.com, admin@umbrella.com)
- Include realistic artifact data from seeded demo
- Show various UI states (loading, success, error)
- Capture responsive design on different screen sizes

**Dashboard Screenshots:**
- Show meaningful metrics with realistic data
- Include time ranges that demonstrate trends
- Capture both normal and alert conditions
- Show different dashboard panels and layouts

**Documentation Screenshots:**
- Include clear, readable text
- Show complete workflows and processes
- Highlight key features and capabilities
- Use consistent browser and styling

## 🔄 Update Process

### When to Update Screenshots

1. **UI Changes**: Any significant interface modifications
2. **New Features**: Addition of new functionality
3. **Dashboard Updates**: Changes to monitoring visualizations
4. **Quarterly Reviews**: Regular freshness updates

### Update Procedure

1. **Prepare Environment**
   ```bash
   # Ensure demo data is fresh
   docker-compose exec api python scripts/seed_demo_data.py
   
   # Start all services
   docker-compose up -d
   
   # Wait for services to be ready
   sleep 30
   ```

2. **Capture Screenshots**
   - Use consistent browser (Chrome/Firefox)
   - Clear browser cache and cookies
   - Use incognito/private mode
   - Maintain consistent window size
   - Use demo accounts for authentication

3. **Process Images**
   - Crop to remove unnecessary browser chrome
   - Resize to standard dimensions
   - Optimize file size without quality loss
   - Add annotations if needed

4. **Update Documentation**
   - Replace old screenshots
   - Update README references
   - Commit changes with descriptive messages
   - Update screenshot inventory

## 📊 Screenshot Inventory

### 🎯 Demo-Critical Screenshots (MUST HAVE)

These screenshots are **required** for the demo script and presentation. The demo script will validate their presence before proceeding.

#### Authentication Flow (Demo Section 1.1) 
- [ ] **CRITICAL** `auth-login-form.png` - Login form with demo credentials visible
- [ ] **CRITICAL** `auth-workspace-selector.png` - Workspace dropdown showing Acme Corp/Umbrella Inc
- [ ] **CRITICAL** `auth-workspace-switching.png` - Before/after workspace switch showing data isolation

#### Artifact Management (Demo Section 1.2)
- [ ] **CRITICAL** `artifacts-list-view.png` - Main listing with demo artifacts from seeded data
- [ ] **CRITICAL** `artifacts-search-filter.png` - Search results for "marketing" query
- [ ] **CRITICAL** `artifacts-create-modal.png` - Create modal with "Demo Widget" example
- [ ] **CRITICAL** `artifacts-edit-modal.png` - Edit modal showing tag management

#### Live Metrics Dashboard (Demo Section 2.1)
- [ ] **CRITICAL** `tour-landing-page.png` - Interactive tour page at /tour
- [ ] **CRITICAL** `tour-metrics-dashboard.png` - Live metrics with real numbers
- [ ] **CRITICAL** `tour-telemetry-demo.png` - Telemetry visualization in action

#### Grafana Dashboards (Demo Section 2.2)
- [ ] **CRITICAL** `grafana-api-golden-signals.png` - API performance with realistic data
- [ ] **CRITICAL** `grafana-business-metrics.png` - Business KPIs showing activity
- [ ] **CRITICAL** `grafana-system-overview.png` - System health with green status

#### AI-Native Features (Demo Section 3)
- [ ] **CRITICAL** `tour-asset-gardener.png` - Asset Gardener demo in progress
- [ ] **CRITICAL** `mcp-configuration.png` - MCP settings showing GitHub/AWS integration
- [ ] **CRITICAL** `agent-hooks-interface.png` - Hook management interface

#### API Documentation (Demo Section 4.1)
- [ ] **CRITICAL** `api-docs-swagger-ui.png` - OpenAPI docs homepage
- [ ] **CRITICAL** `api-docs-authentication.png` - Auth endpoints expanded

### 📋 Supporting Screenshots (NICE TO HAVE)

#### Extended Authentication & User Management
- [ ] Registration form with password requirements
- [ ] User profile and settings page
- [ ] Password reset flow
- [ ] Email verification interface

#### Extended Artifact Management  
- [ ] Artifact detail view with metadata
- [ ] Tag autocomplete in action
- [ ] Bulk operations interface
- [ ] Export/import functionality

#### Extended Monitoring & Observability
- [ ] Prometheus targets and alerts
- [ ] Log aggregation interface
- [ ] Alert notification settings
- [ ] Performance trending over time

#### Development & Operations
- [ ] CI/CD pipeline status
- [ ] Test results and coverage reports
- [ ] Security scan results
- [ ] Deployment status dashboard

#### Mobile Screenshots
- [ ] Mobile login interface
- [ ] Mobile artifact listing
- [ ] Mobile navigation menu
- [ ] Mobile dashboard view

### 🚨 Demo Script Integration

The demo script (`docs/DEMO_SCRIPT.md`) includes a pre-flight check that validates all **CRITICAL** screenshots exist:

```bash
# Pre-demo validation
make validate-demo-assets

# This checks for:
# - All CRITICAL screenshots present
# - Proper naming convention
# - Minimum resolution requirements
# - File size optimization
```

**Demo sections that depend on screenshots:**
- **Section 1.1**: Requires `auth-*` screenshots
- **Section 1.2**: Requires `artifacts-*` screenshots  
- **Section 2.1**: Requires `tour-*` screenshots
- **Section 2.2**: Requires `grafana-*` screenshots
- **Section 3**: Requires AI feature screenshots
- **Section 4.1**: Requires `api-docs-*` screenshots

### 📸 Screenshot Capture Priority

**Phase 1 (Demo Blockers)**: Capture all **CRITICAL** screenshots first
**Phase 2 (Enhancement)**: Add supporting screenshots for documentation
**Phase 3 (Polish)**: Mobile views and edge cases

## 🎯 Usage in Documentation

### README.md Integration
Screenshots are referenced in the main README.md to provide visual context:

```markdown
## 🎯 Key Features

### Multi-Tenant Authentication
![Login Interface](docs/screenshots/auth-login-form.png)

### Artifact Management
![Artifact Listing](docs/screenshots/artifacts-list-view.png)

### Real-time Monitoring
![Grafana Dashboard](docs/screenshots/grafana-api-golden-signals.png)
```

### Demo Script Integration
Screenshots support the demo script by providing visual references:

```markdown
**Navigate to**: http://localhost:3000
![Tour Landing Page](docs/screenshots/tour-landing-page.png)

**Show Live Metrics**
![Metrics Dashboard](docs/screenshots/tour-metrics-dashboard.png)
```

## 🔧 Tools and Setup

### Recommended Tools
- **Browser**: Chrome or Firefox (latest version)
- **Screenshot Tool**: Built-in browser tools, Lightshot, or Snagit
- **Image Editor**: GIMP, Photoshop, or online tools
- **Optimization**: TinyPNG, ImageOptim

### Browser Setup
```javascript
// Console commands for consistent screenshots
// Set viewport size
window.resizeTo(1920, 1080);

// Remove animations for consistent captures
document.body.style.animation = 'none';
document.body.style.transition = 'none';

// Hide cursor for cleaner screenshots
document.body.style.cursor = 'none';
```

### Automation (Future Enhancement)
Consider implementing automated screenshot capture using:
- Playwright for UI screenshots
- Grafana API for dashboard exports
- Scheduled updates via CI/CD

---

**Note**: Screenshots should be captured and added to this directory following the guidelines above. This README serves as a placeholder and guide for the screenshot documentation process.