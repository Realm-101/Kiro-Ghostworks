# Ghostworks Demo Script: "How to Show This Off"

This guide provides a comprehensive script for demonstrating the Ghostworks SaaS platform, highlighting its key features and AI-native capabilities.

## 🎯 Demo Overview

**Duration**: 15-20 minutes  
**Audience**: Technical stakeholders, developers, product managers  
**Goal**: Showcase production-grade SaaS architecture with AI-native development workflows

## 🚀 Pre-Demo Setup (5 minutes before)

### 1. Demo Asset Validation (CRITICAL)
```bash
# Validate all required screenshots are present
make validate-demo-assets

# This MUST pass before proceeding with demo
# If it fails, you'll get specific instructions on what to capture
```

### 2. Environment Check
```bash
# Ensure all services are running
docker-compose ps

# Check health endpoints
curl http://localhost:8000/api/v1/health
curl http://localhost:3000/api/health
```

### 3. Browser Tabs Setup
Open these tabs in order:
1. **Main App**: http://localhost:3000
2. **API Docs**: http://localhost:8000/docs
3. **Grafana**: http://localhost:3001 (admin/admin)
4. **Prometheus**: http://localhost:9090
5. **Tour Page**: http://localhost:3000/tour

### 4. Demo Data Verification
```bash
# Ensure demo data is loaded
docker-compose exec api python scripts/validate_demo_data.py
```

### 🚨 Pre-Flight Checklist
- [ ] `make validate-demo-assets` passes ✅
- [ ] All services healthy ✅
- [ ] Browser tabs open ✅
- [ ] Demo data loaded ✅
- [ ] Screenshots ready for reference ✅

**If any item fails, DO NOT proceed with the demo until fixed.**

## 📋 Demo Script

### Opening Hook (2 minutes)

> "Today I'm going to show you Ghostworks - a production-grade SaaS platform that demonstrates something unique: it can build and improve itself using AI. This isn't just another demo app - it's a fully functional multi-tenant platform with enterprise-grade observability, security, and autonomous development capabilities."

**Key Points to Emphasize:**
- Production-ready architecture, not a toy example
- AI-native development workflow
- Real observability and monitoring
- Multi-tenant security model

### Part 1: Core Platform Features (5 minutes)

#### 1.1 Authentication & Multi-tenancy (2 minutes)

**Navigate to**: http://localhost:3000

> "Let's start with the basics. Ghostworks implements secure multi-tenant authentication with role-based access control."

**Demo Steps:**
1. **Login** with `owner@acme.com` / `demo123`
   - Point out the clean, responsive UI
   - Mention JWT-based authentication with refresh tokens
   - *Reference: `auth-login-form.png`*

2. **Show Workspace Switching**
   - Click workspace dropdown (*Reference: `auth-workspace-selector.png`*)
   - Switch to different workspace (*Reference: `auth-workspace-switching.png`*)
   - Explain tenant isolation at database level

**Talking Points:**
- "Notice how switching workspaces completely changes the data context"
- "This uses PostgreSQL Row-Level Security for true tenant isolation"
- "Each tenant's data is cryptographically separated"

#### 1.2 Artifact Management (3 minutes)

**Stay on**: Main dashboard

> "The core functionality is artifact management - think of it as a flexible catalog system that could represent products, documents, or any business entities."

**Demo Steps:**
1. **Browse Artifacts**
   - Show existing artifacts from demo data (*Reference: `artifacts-list-view.png`*)
   - Point out pagination and clean UI

2. **Search & Filter**
   - Use search bar: "marketing" (*Reference: `artifacts-search-filter.png`*)
   - Filter by tags
   - Show real-time search with debouncing

3. **Create New Artifact**
   - Click "Create Artifact" (*Reference: `artifacts-create-modal.png`*)
   - Fill in: Name: "Demo Widget", Tags: ["demo", "widget"]
   - Show optimistic UI updates

4. **Edit Artifact**
   - Click edit on newly created artifact (*Reference: `artifacts-edit-modal.png`*)
   - Show modal with form validation
   - Update and save

**Talking Points:**
- "Notice the optimistic updates - UI responds immediately"
- "Full-text search is powered by PostgreSQL's built-in capabilities"
- "All operations are validated both client and server-side"

### Part 2: Observability & Monitoring (4 minutes)

#### 2.1 Live Metrics Dashboard (2 minutes)

**Navigate to**: http://localhost:3000/tour

> "Now here's where it gets interesting. This platform has comprehensive observability built in from day one."

**Demo Steps:**
1. **Show Live Metrics** (*Reference: `tour-landing-page.png`*)
   - Point out real-time counters (*Reference: `tour-metrics-dashboard.png`*)
   - Explain the metrics being displayed
   - Refresh to show updates (*Reference: `tour-telemetry-demo.png`*)

2. **Explain the Stack**
   - OpenTelemetry for distributed tracing
   - Prometheus for metrics collection
   - Grafana for visualization

**Talking Points:**
- "These aren't fake numbers - they're live metrics from the running system"
- "Every API call, database query, and user action is instrumented"
- "This is production-grade observability from day one"

#### 2.2 Grafana Dashboards (2 minutes)

**Navigate to**: http://localhost:3001

> "Let's look at the actual monitoring dashboards that would be used in production."

**Demo Steps:**
1. **API Golden Signals Dashboard** (*Reference: `grafana-api-golden-signals.png`*)
   - Show latency percentiles
   - Point out error rates
   - Explain throughput metrics

2. **Business Metrics Dashboard** (*Reference: `grafana-business-metrics.png`*)
   - Show user activity
   - Artifact creation trends
   - Workspace utilization

3. **System Overview** (*Reference: `grafana-system-overview.png`*)
   - Database performance
   - Memory and CPU usage
   - Service health status

**Talking Points:**
- "These dashboards show both technical and business metrics"
- "Alerts are configured for SLA violations"
- "This gives you complete visibility into system health"

### Part 3: AI-Native Development (4 minutes)

#### 3.1 MCP Integration (2 minutes)

**Navigate to**: File explorer or show `.kiro/settings/mcp.json`

> "Here's what makes this truly AI-native. The platform integrates with Model Context Protocol servers for autonomous development."

**Demo Steps:**
1. **Show MCP Configuration** (*Reference: `mcp-configuration.png`*)
   - Open `.kiro/settings/mcp.json`
   - Explain GitHub and AWS docs integration
   - Point out auto-approval settings

2. **Demonstrate MCP Usage**
   - Show how AI can access GitHub repos
   - Explain AWS documentation integration
   - Mention security boundaries

**Talking Points:**
- "MCP allows AI agents to safely interact with external systems"
- "The platform can research AWS best practices automatically"
- "It can analyze its own codebase for improvements"

#### 3.2 Agent Hooks (2 minutes)

**Navigate to**: http://localhost:3000/tour (Asset Gardener section)

> "The platform also has autonomous agent hooks that can improve itself."

**Demo Steps:**
1. **Asset Gardener Demo** (*Reference: `tour-asset-gardener.png`*)
   - Click "Optimize Images" button
   - Show the processing happening
   - Explain what it's doing behind the scenes

2. **Release Notes Automation** (*Reference: `agent-hooks-interface.png`*)
   - Explain the release notes hook
   - Show generated CHANGELOG.md
   - Mention conventional commit parsing

**Talking Points:**
- "The Asset Gardener automatically optimizes images and generates responsive variants"
- "Release notes are generated from conventional commits"
- "These hooks can be triggered manually or automatically"

### Part 4: Architecture & Security (3 minutes)

#### 4.1 API Documentation (1.5 minutes)

**Navigate to**: http://localhost:8000/docs

> "Let's look at the API that powers all of this."

**Demo Steps:**
1. **Show OpenAPI Docs** (*Reference: `api-docs-swagger-ui.png`*)
   - Browse available endpoints
   - Show authentication requirements (*Reference: `api-docs-authentication.png`*)
   - Point out comprehensive documentation

2. **Test an Endpoint**
   - Try the health check endpoint
   - Show the response format
   - Mention rate limiting

**Talking Points:**
- "Fully documented OpenAPI specification"
- "All endpoints have proper error handling"
- "Rate limiting and security headers are built in"

#### 4.2 Security Features (1.5 minutes)

**Navigate back to**: Main app or show code

> "Security is built into every layer of this platform."

**Key Points to Cover:**
- **Multi-tenant isolation**: Row-Level Security in PostgreSQL
- **Authentication**: JWT with refresh tokens, secure cookies
- **Input validation**: Pydantic models with comprehensive validation
- **Security headers**: OWASP-compliant headers on all responses
- **Rate limiting**: Protection against abuse
- **Audit logging**: All operations are logged with correlation IDs

**Talking Points:**
- "Every database query is automatically scoped to the current tenant"
- "Input validation happens at multiple layers"
- "Security scanning is integrated into the CI/CD pipeline"

### Closing & Q&A (2 minutes)

#### Summary Points

> "So what have we seen today?"

1. **Production-Grade Architecture**
   - Multi-tenant SaaS with proper isolation
   - Comprehensive observability and monitoring
   - Enterprise security practices

2. **AI-Native Development**
   - MCP integration for autonomous research and development
   - Agent hooks for self-improvement
   - Steering documents for AI guidance

3. **Modern Tech Stack**
   - Next.js frontend with TypeScript
   - FastAPI backend with async support
   - PostgreSQL with Row-Level Security
   - Docker Compose orchestration

4. **Developer Experience**
   - Comprehensive testing (unit, integration, E2E)
   - CI/CD pipeline with quality gates
   - Documentation and runbooks

#### Call to Action

> "This demonstrates what's possible when you combine modern SaaS architecture with AI-native development practices. The platform can literally improve itself while maintaining production-grade quality and security."

**Questions to Anticipate:**
- **"How does tenant isolation work?"** → PostgreSQL RLS with tenant_id scoping
- **"What about scalability?"** → Async architecture, connection pooling, horizontal scaling ready
- **"How secure is the AI integration?"** → MCP provides safe boundaries, read-only by default
- **"Can this work in production?"** → Yes, includes monitoring, alerting, security scanning

## 🎛️ Demo Variations

### For Technical Audiences (Add 5 minutes)
- Show actual code structure and patterns
- Demonstrate testing suite execution
- Deep dive into database schema and migrations
- Show CI/CD pipeline in action

### For Business Audiences (Reduce to 10 minutes)
- Focus on user experience and business value
- Emphasize multi-tenancy and security
- Show metrics and business intelligence
- Skip technical implementation details

### For Security-Focused Audiences (Add 3 minutes)
- Demonstrate security scanning results
- Show audit logs and correlation IDs
- Explain threat model and mitigations
- Walk through security headers and validation

## 🔧 Troubleshooting

### Common Issues

**Services not responding:**
```bash
docker-compose restart
docker-compose logs [service-name]
```

**Demo data missing:**
```bash
docker-compose exec api python scripts/seed_demo_data.py
```

**Grafana dashboards not loading:**
```bash
docker-compose restart grafana
# Wait 30 seconds for provisioning
```

### Backup Demo Flow

If live demo fails, have these ready:
- Screenshots of key UI flows
- Pre-recorded video of agent hooks
- Static Grafana dashboard exports
- Postman collection for API demo

## 📊 Success Metrics

A successful demo should achieve:
- Clear understanding of multi-tenant architecture
- Appreciation for AI-native development approach
- Recognition of production-grade quality
- Interest in implementation details or adoption

## 📝 Follow-up Materials

Provide attendees with:
- Link to GitHub repository
- Architecture documentation
- Getting started guide
- Contact information for technical questions

---

**Remember**: The goal is to show that AI can build production-grade software, not just prototypes. Emphasize the quality, security, and operational readiness throughout the demo.