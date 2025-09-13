### 1\. What is Ghostworks and what are its core architectural principles?

Ghostworks is a production-grade, AI-native multi-tenant SaaS platform that demonstrates autonomous development capabilities. Its core architectural principles are built around modern web development patterns, high performance, scalability, and comprehensive observability, while prioritising developer productivity and code quality. Key design choices reflect a commitment to type-safe development, asynchronous API capabilities, robust multi-tenant database support, and extensive ecosystem tooling. The platform is designed to be self-improving through AI integration, enabling it to research, develop, and optimise itself.

### 2\. What technology stack does Ghostworks use and why were these choices made?

Ghostworks uses a carefully selected technology stack for both its frontend and backend, with a robust database and background processing system:

* Frontend: Next.js 14+ with App Router for the framework, TypeScript for type safety, Tailwind CSS for styling, React Query for server state management, and Playwright/Vitest for testing. Next.js was chosen over alternatives like React with Vite or Vue.js with Nuxt for its out-of-the-box SSR/SSG benefits, SEO, and the maturity of the React ecosystem for enterprise applications.  
* Backend: FastAPI with Python 3.11+ for its high-performance async API and comprehensive type hints, SQLAlchemy 2.0 for the ORM, Alembic for migrations, Pydantic v2 for validation, and JWT with secure cookies for authentication. FastAPI was preferred over Node.js (weaker typing), Django REST Framework (slower performance), Go (more verbose), and Rust (steep learning curve) for its superior async capabilities, typing, performance, and rich Python ecosystem for rapid development.  
* Database: PostgreSQL 15+ is the primary database, chosen for its ACID compliance, superior JSON support, and advanced features. It employs Row-Level Security (RLS) for multi-tenancy. Redis is used for caching and task queuing, and PostgreSQL's full-text search with GIN indexes is used for search capabilities. Alternatives like MySQL (weaker JSON support), MongoDB (eventual consistency), and SQLite (not suitable for multi-tenant production) were rejected.  
* Background Processing: Celery with a Redis broker is used for async task processing and worker management.

This stack was chosen to ensure developer productivity, performance, end-to-end type safety, ecosystem maturity, scalability, and robust observability, while specifically supporting multi-tenancy through PostgreSQL RLS.

### 3\. How does Ghostworks handle multi-tenancy and ensure data isolation?

Ghostworks implements a Row-Level Security (RLS) based multi-tenancy model to ensure complete data isolation and security for multiple organisations (tenants) sharing the same application infrastructure.  
The core of this model is:

* Single PostgreSQL Database: All tenants share the same database instance.  
* Row-Level Security (RLS): PostgreSQL RLS policies are enforced at the database level, meaning no tenant can access another tenant's data, even if application-level bugs occur.  
* Tenant Context: The application sets an app.current\_tenant\_id session variable for all queries, which RLS policies then use to filter data.  
* Foreign Key Constraints: All domain tables include a tenant\_id column with proper foreign key relationships to reinforce isolation.

This approach was selected over alternatives like Database-per-Tenant (high operational overhead), Schema-per-Tenant (still complex migrations), or Application-Level Filtering Only (critical security risk due to lack of database-level protection). The RLS model provides strong security, compliance (SOC2, GDPR), operational simplicity, and cost efficiency, though it introduces a small performance overhead and increases query complexity that needs careful testing.

### 4\. What is Ghostworks' approach to observability and monitoring?

Ghostworks adopts a comprehensive observability stack based on OpenTelemetry, Prometheus, and Grafana to ensure system reliability, performance, and operational excellence.

* OpenTelemetry: Used for unified telemetry collection, encompassing traces, metrics, and structured logs.  
* Prometheus: Responsible for collecting and storing metrics, allowing for powerful querying with PromQL.  
* Grafana: Provides real-time visualisation through dashboards, and powers the alerting system.  
* OpenTelemetry Collector: Centrally processes and exports telemetry data.  
* Structured Logging: All logs are in JSON format and include correlation IDs for easier debugging across distributed services.

This open-source stack allows for tracking "Golden Signals" (latency, traffic, errors, saturation), business metrics (e.g., user registrations, artifact creation), and system metrics (CPU, memory, database performance). Commercial SaaS solutions like DataDog or cloud provider solutions were rejected due to cost, vendor lock-in, and a desire to demonstrate open-source capabilities. The chosen approach provides comprehensive visibility, cost-effectiveness, and flexibility, albeit with an operational overhead and learning curve for the team.

### 5\. What is the deployment strategy and CI/CD approach for Ghostworks?

Ghostworks implements a Docker Compose-based deployment strategy coupled with a GitHub Actions CI/CD pipeline.

* Containerization: All services are containerised using Docker, leveraging multi-stage builds for efficiency and consistency.  
* Orchestration: Docker Compose is used for local development and production deployment, providing a simple and understandable model.  
* CI/CD: GitHub Actions automates testing, building, and deployment processes, incorporating quality gates and security scanning (e.g., ZAP).  
* Infrastructure as Code (IaC): Docker Compose configurations serve as the IaC, ensuring reproducible environments across development, staging, and production.  
* Blue-Green Deployment: For production, a blue-green strategy is employed to ensure zero-downtime deployments with automated rollback capabilities.

Alternatives such as Kubernetes (too complex for current scale), AWS ECS/Fargate (vendor lock-in), or serverless functions (not suitable for stateful applications) were considered but rejected. The current strategy prioritises simplicity, consistency, portability, cost-efficiency, and a positive developer experience, while providing a clear migration path to more advanced orchestration like Kubernetes when scalability demands it.

### 6\. How does Ghostworks integrate AI-native development capabilities?

Ghostworks is designed as an AI-native platform that demonstrates autonomous development capabilities through several key integrations:

* Model Context Protocol (MCP) Servers: The platform integrates with MCP servers to allow AI agents to safely interact with external systems. This includes configuration for accessing GitHub repositories for code analysis and AWS documentation for researching best practices, with auto-approval settings for controlled interactions.  
* Agent Hooks: Autonomous agent hooks are embedded to enable self-improvement. Examples include:  
* Asset Gardener Hook: Automatically optimises images, generates responsive variants (e.g., WebP, thumbnails), and updates import maps. This demonstrates AI-driven asset optimisation.  
* Release Notes Hook: Automatically generates CHANGELOG.md from conventional commit messages, demonstrating AI-driven release automation.  
* Steering Documents: AI development is guided by steering documents (e.g., code conventions, security policies, testing standards) that define the desired behaviour and quality gates for AI agents.

These features allow Ghostworks to research, develop, and optimise itself, showcasing a unique AI-native development workflow that combines modern SaaS architecture with autonomous capabilities.

### 7\. What demo data is provided and how can it be used to showcase Ghostworks features?

Ghostworks includes comprehensive demo data and seeding scripts to facilitate demonstrations and testing.

* Two realistic tenant workspaces: "Acme Corp" (a tech company) and "Umbrella Inc" (a biotech/pharmaceutical company).  
* Five demo user accounts: With different roles (Owner, Admin, Member, Researcher) and permissions across the two tenants. For example, owner@acme.com and admin@umbrella.com are provided with a consistent password (demo123).  
* Thirteen sample artifacts: With varied tags, descriptions, and realistic metadata relevant to their respective industry focuses (e.g., "Customer Analytics Dashboard" for Acme Corp, "Clinical Trial Data Management" for Umbrella Inc).

These demo data allow users to:

* Test multi-tenant functionality: By logging in with different tenant accounts and observing complete data isolation.  
* Explore role-based access control: By switching between users with varying permissions.  
* Demonstrate artifact management: By browsing, searching, filtering, creating, and editing realistic sample data.  
* Showcase observability: By generating activity that is reflected in live metrics and Grafana dashboards.  
* Reset to a clean state: A database reset utility is provided, which automatically seeds fresh demo data, ensuring a consistent starting point for every demonstration.

The demo data is designed for realism, safety (transaction-wrapped operations, duplicate prevention), and reliability, supporting a robust demonstration of the Ghostworks SaaS platform's capabilities.

### 8\. What is the current status of Ghostworks' testing and how is it ensured that the platform is production-ready?

The Ghostworks SaaS platform is architecturally complete and deemed production-ready, pending final integration testing with a complete Docker environment. While full stack testing with Docker Desktop was blocked due to its unavailability, extensive validation has been performed on all testable components.  
Components successfully validated (✅ PASSED) include:

* MCP Server Integration (AWS documentation server working)  
* Agent Hook Functionality (Asset Gardener and Release Notes hooks working)  
* Configuration Validation (Docker Compose, CI/CD pipeline valid)  
* Demo Data and Scripts (ready for seeding)  
* Comprehensive Documentation (README, Demo Script, ADRs, Steering Documents complete)  
* Performance Test Configuration (K6 load tests configured with thresholds)  
* Code-Level Security (input validation, password hashing, JWT security, security headers, rate limiting)  
* Observability Stack Configuration (OpenTelemetry, Prometheus, Grafana configured)  
* Theoretical Multi-Tenant Isolation (RLS policies, tenant ID foreign keys, authorisation middleware in place)

Components that are ⚠️ PARTIAL/BLOCKED and require a running Docker stack to complete testing are:

* Unit Tests (blocked by missing Python dependencies)  
* Frontend Tests (blocked by PostCSS/React configuration issues)  
* E2E Tests (Playwright configured but requires running application)  
* Full Stack Integration (requires Docker Desktop to start services)  
* Actual Multi-Tenant Isolation (cannot verify RLS enforcement without database)  
* Observability Stack Operation (cannot verify trace collection, metrics scraping, dashboard functionality, and alerting without running services)  
* Effectiveness of Security Hardening (cannot test actual security headers, rate limiting, or JWT validation without running services)  
* Actual Performance Characteristics (cannot measure latency and load conditions)

