'use client';

import React from 'react';
import { MainLayout } from '@/components/layout/main-layout';
import { GuidedTour } from '@/components/demo/guided-tour';
import { MetricsDashboard } from '@/components/demo/metrics-dashboard';
import { TelemetryDemo } from '@/components/demo/telemetry-demo';
import { AssetGardenerDemo } from '@/components/demo/asset-gardener-demo';

export default function Tour() {
  const tourSteps = [
    {
      id: 'welcome',
      title: 'Welcome',
      description: 'Introduction to Ghostworks SaaS Platform',
      icon: '👋',
      content: (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Welcome to Ghostworks
            </h3>
            <p className="text-lg text-gray-600 mb-6">
              A production-grade, AI-native multi-tenant SaaS platform that demonstrates 
              autonomous development capabilities.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-blue-50 rounded-lg p-6 text-center">
              <div className="text-3xl mb-3">🏗️</div>
              <h4 className="font-semibold text-gray-900 mb-2">Modern Architecture</h4>
              <p className="text-sm text-gray-600">
                Next.js frontend, FastAPI backend, Celery workers, and PostgreSQL with full Docker orchestration
              </p>
            </div>

            <div className="bg-green-50 rounded-lg p-6 text-center">
              <div className="text-3xl mb-3">🤖</div>
              <h4 className="font-semibold text-gray-900 mb-2">AI-Native Development</h4>
              <p className="text-sm text-gray-600">
                MCP integration, autonomous agent hooks, and AI-powered development workflows
              </p>
            </div>

            <div className="bg-purple-50 rounded-lg p-6 text-center">
              <div className="text-3xl mb-3">📊</div>
              <h4 className="font-semibold text-gray-900 mb-2">Full Observability</h4>
              <p className="text-sm text-gray-600">
                OpenTelemetry tracing, Prometheus metrics, Grafana dashboards, and structured logging
              </p>
            </div>

            <div className="bg-yellow-50 rounded-lg p-6 text-center">
              <div className="text-3xl mb-3">🔒</div>
              <h4 className="font-semibold text-gray-900 mb-2">Security First</h4>
              <p className="text-sm text-gray-600">
                Multi-tenant isolation, RBAC, JWT authentication, and ASVS-aligned security practices
              </p>
            </div>

            <div className="bg-red-50 rounded-lg p-6 text-center">
              <div className="text-3xl mb-3">🧪</div>
              <h4 className="font-semibold text-gray-900 mb-2">Comprehensive Testing</h4>
              <p className="text-sm text-gray-600">
                Unit tests, integration tests, E2E tests with Playwright, and performance testing
              </p>
            </div>

            <div className="bg-indigo-50 rounded-lg p-6 text-center">
              <div className="text-3xl mb-3">🚀</div>
              <h4 className="font-semibold text-gray-900 mb-2">Production Ready</h4>
              <p className="text-sm text-gray-600">
                CI/CD pipelines, Docker deployment, monitoring, alerting, and operational tooling
              </p>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h4 className="font-semibold text-gray-900 mb-3">🎯 What You&apos;ll See in This Tour</h4>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-center space-x-2">
                <span className="text-green-500">✓</span>
                <span>Live system metrics and real-time monitoring</span>
              </li>
              <li className="flex items-center space-x-2">
                <span className="text-green-500">✓</span>
                <span>Telemetry and observability demonstrations</span>
              </li>
              <li className="flex items-center space-x-2">
                <span className="text-green-500">✓</span>
                <span>AI-powered automation with Asset Gardener</span>
              </li>
              <li className="flex items-center space-x-2">
                <span className="text-green-500">✓</span>
                <span>Multi-tenant architecture and security features</span>
              </li>
              <li className="flex items-center space-x-2">
                <span className="text-green-500">✓</span>
                <span>Development workflow and engineering practices</span>
              </li>
            </ul>
          </div>
        </div>
      )
    },
    {
      id: 'metrics',
      title: 'Live Metrics',
      description: 'Real-time system statistics and monitoring',
      icon: '📊',
      content: <MetricsDashboard />
    },
    {
      id: 'telemetry',
      title: 'Observability',
      description: 'Prometheus metrics and Grafana dashboards',
      icon: '📈',
      content: <TelemetryDemo />
    },
    {
      id: 'automation',
      title: 'AI Automation',
      description: 'Asset Gardener and autonomous development',
      icon: '🤖',
      content: <AssetGardenerDemo />
    },
    {
      id: 'architecture',
      title: 'Architecture',
      description: 'Multi-tenant design and security model',
      icon: '🏗️',
      content: (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Platform Architecture
            </h3>
            <p className="text-lg text-gray-600 mb-6">
              Modern, scalable, and secure multi-tenant SaaS architecture
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h4 className="font-semibold text-gray-900 mb-4">🏢 Multi-Tenant Design</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h5 className="font-medium text-gray-900 mb-2">Row-Level Security (RLS)</h5>
                <p className="text-sm text-gray-600">
                  PostgreSQL RLS ensures complete tenant isolation at the database level. 
                  Each query automatically filters data by tenant_id.
                </p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h5 className="font-medium text-gray-900 mb-2">Role-Based Access Control</h5>
                <p className="text-sm text-gray-600">
                  Three-tier RBAC system: Owner, Admin, and Member roles with 
                  granular permissions for workspace operations.
                </p>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 rounded-lg p-6">
            <h4 className="font-semibold text-blue-900 mb-4">🔧 Technology Stack</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <h5 className="font-medium text-blue-900 mb-2">Frontend</h5>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Next.js 15 with App Router</li>
                  <li>• TypeScript & Tailwind CSS</li>
                  <li>• React Query for state management</li>
                  <li>• Playwright for E2E testing</li>
                </ul>
              </div>
              <div>
                <h5 className="font-medium text-blue-900 mb-2">Backend</h5>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• FastAPI with async/await</li>
                  <li>• SQLAlchemy 2.0 & Alembic</li>
                  <li>• Pydantic v2 validation</li>
                  <li>• Celery background workers</li>
                </ul>
              </div>
              <div>
                <h5 className="font-medium text-blue-900 mb-2">Infrastructure</h5>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• PostgreSQL with RLS</li>
                  <li>• Redis for caching & queues</li>
                  <li>• Docker Compose orchestration</li>
                  <li>• Nginx reverse proxy</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-green-50 rounded-lg p-6">
            <h4 className="font-semibold text-green-900 mb-4">🛡️ Security Features</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h5 className="font-medium text-green-900 mb-2">Authentication & Authorization</h5>
                <ul className="text-sm text-green-800 space-y-1">
                  <li>• JWT access & refresh tokens</li>
                  <li>• Secure HTTP-only cookies</li>
                  <li>• Password strength validation</li>
                  <li>• Rate limiting on auth endpoints</li>
                </ul>
              </div>
              <div>
                <h5 className="font-medium text-green-900 mb-2">Data Protection</h5>
                <ul className="text-sm text-green-800 space-y-1">
                  <li>• Input validation & sanitization</li>
                  <li>• SQL injection prevention</li>
                  <li>• XSS protection headers</li>
                  <li>• CSRF protection</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 rounded-lg p-6">
            <h4 className="font-semibold text-purple-900 mb-4">📦 Monorepo Structure</h4>
            <div className="bg-white rounded-lg p-4 font-mono text-sm">
              <div className="space-y-1 text-gray-700">
                <div>📁 apps/web/ <span className="text-gray-500">- Next.js frontend</span></div>
                <div>📁 services/api/ <span className="text-gray-500">- FastAPI backend</span></div>
                <div>📁 services/worker/ <span className="text-gray-500">- Celery workers</span></div>
                <div>📁 packages/shared/ <span className="text-gray-500">- Shared utilities</span></div>
                <div>📁 infra/docker/ <span className="text-gray-500">- Infrastructure config</span></div>
                <div>📁 tests/ <span className="text-gray-500">- Test suites</span></div>
                <div>📁 .kiro/specs/ <span className="text-gray-500">- Feature specifications</span></div>
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'development',
      title: 'Development',
      description: 'AI-native development workflow and practices',
      icon: '⚡',
      content: (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              AI-Native Development Workflow
            </h3>
            <p className="text-lg text-gray-600 mb-6">
              Autonomous development with AI agents, comprehensive testing, and modern DevOps practices
            </p>
          </div>

          <div className="bg-blue-50 rounded-lg p-6">
            <h4 className="font-semibold text-blue-900 mb-4">🤖 MCP Integration & Agent Hooks</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h5 className="font-medium text-gray-900 mb-2">🌱 Asset Gardener Hook</h5>
                <p className="text-sm text-gray-600 mb-3">
                  Automatically optimizes images, generates responsive variants, and updates import maps.
                </p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• WebP & AVIF format conversion</li>
                  <li>• Multiple size variants (thumbnail to xlarge)</li>
                  <li>• TypeScript import map generation</li>
                  <li>• File watch triggers & manual controls</li>
                </ul>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h5 className="font-medium text-gray-900 mb-2">📝 Release Notes Hook</h5>
                <p className="text-sm text-gray-600 mb-3">
                  Parses conventional commits and generates structured release notes.
                </p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• Conventional commit parsing</li>
                  <li>• CHANGELOG.md generation</li>
                  <li>• Semantic version tagging</li>
                  <li>• Git integration & automation</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-green-50 rounded-lg p-6">
            <h4 className="font-semibold text-green-900 mb-4">🧪 Comprehensive Testing Strategy</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h5 className="font-medium text-gray-900 mb-2">Unit Testing</h5>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• pytest for Python backend</li>
                  <li>• Vitest for TypeScript frontend</li>
                  <li>• ≥70% backend coverage target</li>
                  <li>• ≥60% frontend coverage target</li>
                </ul>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h5 className="font-medium text-gray-900 mb-2">Integration Testing</h5>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• API contract validation</li>
                  <li>• Database integration tests</li>
                  <li>• Multi-tenant isolation verification</li>
                  <li>• Authentication flow testing</li>
                </ul>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h5 className="font-medium text-gray-900 mb-2">E2E Testing</h5>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Playwright browser automation</li>
                  <li>• Critical user journey validation</li>
                  <li>• Cross-browser compatibility</li>
                  <li>• Performance regression testing</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 rounded-lg p-6">
            <h4 className="font-semibold text-yellow-900 mb-4">🚀 CI/CD Pipeline</h4>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h5 className="font-medium text-gray-900">GitHub Actions Workflow</h5>
                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Automated</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                <div className="text-center">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
                    <span className="text-blue-600 font-semibold">1</span>
                  </div>
                  <p className="font-medium text-gray-900">Code Quality</p>
                  <p className="text-gray-600 text-xs">Linting, formatting, security scanning</p>
                </div>
                <div className="text-center">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
                    <span className="text-green-600 font-semibold">2</span>
                  </div>
                  <p className="font-medium text-gray-900">Testing</p>
                  <p className="text-gray-600 text-xs">Unit, integration, E2E tests</p>
                </div>
                <div className="text-center">
                  <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-2">
                    <span className="text-purple-600 font-semibold">3</span>
                  </div>
                  <p className="font-medium text-gray-900">Build & Deploy</p>
                  <p className="text-gray-600 text-xs">Container builds, staging deployment</p>
                </div>
                <div className="text-center">
                  <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-2">
                    <span className="text-orange-600 font-semibold">4</span>
                  </div>
                  <p className="font-medium text-gray-900">Validation</p>
                  <p className="text-gray-600 text-xs">Performance tests, kiro_score.json</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 rounded-lg p-6">
            <h4 className="font-semibold text-purple-900 mb-4">📋 Engineering Standards</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h5 className="font-medium text-purple-900 mb-2">Code Conventions</h5>
                <ul className="text-sm text-purple-800 space-y-1">
                  <li>• TypeScript strict mode</li>
                  <li>• Python type hints</li>
                  <li>• ESLint & Prettier formatting</li>
                  <li>• Conventional commit messages</li>
                </ul>
              </div>
              <div>
                <h5 className="font-medium text-purple-900 mb-2">Security Policies</h5>
                <ul className="text-sm text-purple-800 space-y-1">
                  <li>• ASVS-aligned practices</li>
                  <li>• Automated security scanning</li>
                  <li>• Dependency vulnerability checks</li>
                  <li>• OWASP ZAP baseline scans</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )
    }
  ];

  return (
    <MainLayout>
      <div className="py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <GuidedTour steps={tourSteps} />
        </div>
      </div>
    </MainLayout>
  );
}
