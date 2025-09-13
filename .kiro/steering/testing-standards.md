---
inclusion: fileMatch
fileMatchPattern: "**/*test*|**/*spec*|tests/**/*"
---

# Testing Standards and Guidelines

This document defines comprehensive testing standards for the Ghostworks SaaS platform with specific coverage targets and quality requirements.

## Coverage Requirements

### Backend Coverage Targets
- **Minimum Coverage**: 70% overall code coverage
- **Critical Paths**: 90% coverage for authentication, authorization, and data access
- **Business Logic**: 85% coverage for artifact management and tenant operations
- **API Endpoints**: 100% coverage for all public API endpoints

### Frontend Coverage Targets
- **Minimum Coverage**: 60% overall code coverage
- **Components**: 70% coverage for reusable UI components
- **Business Logic**: 80% coverage for API clients and state management
- **Critical Flows**: 90% coverage for authentication and core user journeys

## Testing Pyramid Structure

### Unit Tests (70% of total tests)
**Backend (pytest)**
- Test individual functions and methods in isolation
- Mock external dependencies (database, Redis, external APIs)
- Focus on business logic validation and edge cases
- Run in < 5 seconds total execution time

**Frontend (Vitest)**
- Test component rendering and behavior
- Test utility functions and custom hooks
- Test state management logic
- Mock API calls and external dependencies

### Integration Tests (20% of total tests)
**API Integration Tests**
- Test full request/response cycles with real database
- Validate authentication and authorization flows
- Test multi-tenant data isolation
- Verify error handling and edge cases

**Component Integration Tests**
- Test component interactions and data flow
- Test form submissions and API integrations
- Validate routing and navigation
- Test error boundaries and loading states

### End-to-End Tests (10% of total tests)
**Critical User Journeys**
- User registration and email verification
- Login and workspace switching
- Artifact creation, editing, and deletion
- Search and filtering functionality
- Multi-tenant isolation verification

## Test Organization and Structure

### Backend Test Structure
```
services/api/tests/
├── unit/
│   ├── test_models.py          # Model validation and business logic
│   ├── test_services.py        # Service layer unit tests
│   └── test_utils.py           # Utility function tests
├── integration/
│   ├── test_auth_integration.py    # Auth flow integration tests
│   ├── test_artifacts_integration.py # Artifact CRUD integration
│   └── test_workspaces_integration.py # Workspace management
├── conftest.py                 # Shared fixtures and configuration
└── test_security.py           # Security-specific test cases
```

### Frontend Test Structure
```
apps/web/src/
├── components/
│   └── __tests__/              # Component unit tests
├── lib/
│   └── __tests__/              # Utility and API client tests
├── hooks/
│   └── __tests__/              # Custom hook tests
└── tests/
    ├── e2e/                    # Playwright E2E tests
    ├── setup.ts                # Test configuration
    └── mocks/                  # Mock data and handlers
```

## Test Quality Standards

### Test Naming Conventions
**Backend (pytest)**
```python
def test_create_artifact_with_valid_data_should_return_201():
    """Test that creating an artifact with valid data returns 201 status."""
    pass

def test_create_artifact_without_authentication_should_return_401():
    """Test that creating an artifact without auth returns 401 status."""
    pass
```

**Frontend (Vitest)**
```typescript
describe('ArtifactList', () => {
  it('should render artifacts when data is loaded', () => {
    // Test implementation
  });
  
  it('should show loading state while fetching data', () => {
    // Test implementation
  });
});
```

### Test Data Management
**Fixtures and Factories**
- Use factory patterns for test data generation
- Implement database fixtures with proper cleanup
- Create realistic test data that mirrors production
- Isolate test data between test runs

**Example Factory Pattern**
```python
@pytest.fixture
def artifact_factory():
    def _create_artifact(**kwargs):
        defaults = {
            'name': 'Test Artifact',
            'description': 'Test description',
            'tags': ['test', 'sample'],
            'tenant_id': str(uuid4())
        }
        defaults.update(kwargs)
        return Artifact(**defaults)
    return _create_artifact
```

### Assertion Standards
**Clear and Specific Assertions**
```python
# Good: Specific assertion with clear message
assert response.status_code == 201, f"Expected 201, got {response.status_code}"
assert 'artifact_id' in response.json(), "Response should contain artifact_id"

# Avoid: Generic assertions without context
assert response.ok
assert data
```

**Frontend Assertions**
```typescript
// Good: Specific DOM assertions
expect(screen.getByRole('button', { name: 'Create Artifact' })).toBeInTheDocument();
expect(screen.getByText('Artifact created successfully')).toBeVisible();

// Good: State assertions
expect(mockCreateArtifact).toHaveBeenCalledWith({
  name: 'Test Artifact',
  description: 'Test description'
});
```

## Performance Testing Standards

### Load Testing Requirements
**API Performance Targets**
- P95 response time < 200ms for CRUD operations
- P99 response time < 500ms for search operations
- Support 100 concurrent users per service instance
- Database queries < 50ms average execution time

**Frontend Performance Targets**
- Initial page load < 2 seconds
- Route transitions < 500ms
- Component render time < 100ms
- Bundle size < 500KB gzipped

### Performance Test Implementation
```javascript
// K6 load test example
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 10 },
    { duration: '5m', target: 50 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],
    http_req_failed: ['rate<0.05'],
  },
};
```

## Security Testing Standards

### Security Test Categories
**Authentication Tests**
- Test password complexity requirements
- Verify account lockout mechanisms
- Test JWT token expiration and refresh
- Validate multi-factor authentication flows

**Authorization Tests**
- Test role-based access control
- Verify tenant isolation boundaries
- Test privilege escalation prevention
- Validate API endpoint permissions

**Input Validation Tests**
- Test SQL injection prevention
- Verify XSS protection mechanisms
- Test file upload security
- Validate input sanitization

### Security Test Implementation
```python
def test_sql_injection_prevention():
    """Test that SQL injection attempts are blocked."""
    malicious_input = "'; DROP TABLE users; --"
    response = client.post("/api/v1/artifacts", json={
        "name": malicious_input,
        "description": "test"
    })
    # Verify the request is handled safely
    assert response.status_code in [400, 422]
```

## Test Automation and CI/CD Integration

### Continuous Testing Pipeline
1. **Pre-commit Hooks**: Run linting and basic unit tests
2. **Pull Request**: Run full test suite with coverage reporting
3. **Staging Deployment**: Run integration and E2E tests
4. **Production Deployment**: Run smoke tests and health checks

### Test Reporting Requirements
**Coverage Reports**
- Generate HTML coverage reports for code review
- Track coverage trends over time
- Fail builds if coverage drops below thresholds
- Exclude generated code and migrations from coverage

**Test Results**
- Generate JUnit XML reports for CI integration
- Create test result dashboards
- Track test execution time trends
- Alert on test failures and flaky tests

## Mock and Stub Guidelines

### External Service Mocking
**Database Mocking**
- Use in-memory SQLite for unit tests
- Use test PostgreSQL instance for integration tests
- Mock Redis operations in unit tests
- Use real Redis instance for integration tests

**API Mocking**
```python
# Backend mocking with pytest-mock
def test_email_service_integration(mocker):
    mock_send = mocker.patch('services.email.send_email')
    mock_send.return_value = {'status': 'sent', 'id': '12345'}
    
    result = send_verification_email('user@example.com')
    assert result['status'] == 'sent'
    mock_send.assert_called_once()
```

**Frontend Mocking**
```typescript
// MSW (Mock Service Worker) for API mocking
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/v1/artifacts', (req, res, ctx) => {
    return res(
      ctx.json({
        items: [{ id: '1', name: 'Test Artifact' }],
        total: 1
      })
    );
  }),
];
```

## Test Environment Management

### Environment Configuration
**Test Database Setup**
- Use separate test databases for each test suite
- Implement database seeding for consistent test data
- Clean up test data after each test run
- Use transactions for test isolation

**Environment Variables**
```python
# Test-specific configuration
TEST_DATABASE_URL = "postgresql://test:test@localhost:5433/ghostworks_test"
TEST_REDIS_URL = "redis://localhost:6380/1"
JWT_SECRET_KEY = "test-secret-key-not-for-production"
```

### Test Data Lifecycle
1. **Setup**: Create test database and seed initial data
2. **Execution**: Run tests with isolated data
3. **Teardown**: Clean up test data and close connections
4. **Reset**: Restore database to clean state for next run

## Quality Gates and Metrics

### Test Quality Metrics
- **Test Coverage**: Track line, branch, and function coverage
- **Test Execution Time**: Monitor and optimize slow tests
- **Test Reliability**: Track flaky test rates and fix unstable tests
- **Defect Escape Rate**: Measure bugs found in production vs. tests

### Quality Gates
- All tests must pass before merge
- Coverage must meet minimum thresholds
- No critical security vulnerabilities
- Performance tests must meet SLA requirements
- E2E tests must pass on target browsers

### Continuous Improvement
- Regular test suite maintenance and refactoring
- Remove obsolete tests and update outdated ones
- Optimize test execution time and resource usage
- Implement test result analytics and reporting