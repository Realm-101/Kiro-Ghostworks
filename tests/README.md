# Ghostworks SaaS Testing Suite

This directory contains the comprehensive testing suite for the Ghostworks SaaS platform, implementing the requirements from Task 16 of the implementation plan.

## Overview

The testing suite includes:
- **Unit Tests**: Individual component and function testing
- **Integration Tests**: API endpoint and database integration testing  
- **End-to-End Tests**: Complete user workflow testing with Playwright
- **Performance Tests**: Load testing with K6
- **Test Utilities**: Shared helpers and fixtures

## Test Structure

```
tests/
├── unit/                    # Unit tests for backend logic
├── api/                     # Integration tests for API endpoints
├── performance/             # K6 performance tests
├── utils/                   # Shared test utilities and helpers
├── conftest.py             # Global pytest configuration
└── run_tests.py            # Comprehensive test runner

apps/web/tests/
├── e2e/                    # Playwright end-to-end tests
└── src/components/         # Frontend unit tests with Vitest
```

## Running Tests

### All Tests
```bash
# Run complete test suite with coverage and reporting
npm run test:all

# Or use the Python runner directly
python tests/run_tests.py
```

### Individual Test Suites

#### Backend Unit Tests
```bash
# Run all unit tests with coverage
npm run test:unit

# Run specific test file
python -m pytest tests/unit/test_auth_unit.py -v

# Run with coverage report
npm run test:coverage
```

#### Integration Tests
```bash
# Run all integration tests
npm run test:integration

# Run specific integration test
python -m pytest tests/api/test_auth_integration.py -v
```

#### Frontend Tests
```bash
# Run frontend unit tests
npm run test:frontend

# Run with UI
cd apps/web && npm run test:ui

# Run with coverage
cd apps/web && npm run test:coverage
```

#### End-to-End Tests
```bash
# Run E2E tests
npm run test:e2e

# Run with UI mode
cd apps/web && npm run test:e2e:ui

# Run in headed mode (see browser)
cd apps/web && npm run test:e2e:headed
```

#### Performance Tests
```bash
# Run performance tests (requires k6)
npm run test:performance

# Or directly with k6
k6 run tests/performance/api-load-test.js
```

## Test Configuration

### Pytest Configuration
- **File**: `pytest.ini`
- **Coverage Target**: 70% backend, 60% frontend
- **Markers**: unit, integration, e2e, slow, auth, artifacts, workspaces
- **Async Support**: Enabled with asyncio-mode=auto

### Vitest Configuration  
- **File**: `apps/web/vitest.config.ts`
- **Environment**: jsdom for DOM testing
- **Coverage**: v8 provider with HTML/JSON reports
- **Setup**: `apps/web/src/test/setup.ts`

### Playwright Configuration
- **File**: `apps/web/playwright.config.ts`
- **Browsers**: Chromium, Firefox, WebKit
- **Reports**: HTML and JSON output
- **Screenshots**: On failure

## Test Utilities

### Backend Test Helpers (`tests/utils/test_helpers.py`)

#### TestDataFactory
Creates test data objects:
```python
from tests.utils.test_helpers import TestDataFactory

user_data = TestDataFactory.create_user_data(email="test@example.com")
artifact_data = TestDataFactory.create_artifact_data(name="Test Artifact")
```

#### DatabaseTestHelper
Database operations for tests:
```python
from tests.utils.test_helpers import DatabaseTestHelper

user = await DatabaseTestHelper.create_user(session, user_data)
tenant = await DatabaseTestHelper.create_tenant(session)
artifact = await DatabaseTestHelper.create_artifact(session, tenant, user)
```

#### AuthTestHelper
Authentication utilities:
```python
from tests.utils.test_helpers import AuthTestHelper

headers = AuthTestHelper.create_auth_headers(user, tenant, membership)
```

#### APITestHelper
API testing utilities:
```python
from tests.utils.test_helpers import APITestHelper

user_response = await APITestHelper.register_user(client, user_data)
login_response = await APITestHelper.login_user(client, email, password)
```

### Frontend Test Utilities

#### Component Testing
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Render with providers
const renderWithProviders = (component) => {
  const queryClient = new QueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}
```

## Test Coverage Requirements

### Backend Coverage (Target: ≥70%)
- **Models**: 90%+ (data validation, relationships)
- **Routes**: 80%+ (endpoint logic, error handling)
- **Services**: 85%+ (business logic)
- **Auth**: 95%+ (security critical)
- **Database**: 75%+ (queries, migrations)

### Frontend Coverage (Target: ≥60%)
- **Components**: 70%+ (rendering, interactions)
- **Hooks**: 80%+ (state management)
- **Utils**: 85%+ (pure functions)
- **API Client**: 75%+ (HTTP calls, error handling)

## Performance Requirements

### API Performance Targets
- **P95 Latency**: < 200ms for all endpoints
- **Error Rate**: < 5% under normal load
- **Throughput**: Handle 50 concurrent users
- **Auth Latency**: < 100ms for login/token refresh

### Load Testing Scenarios
1. **Ramp-up**: 10 → 20 → 50 users over 4 minutes
2. **Sustained Load**: 50 users for 2 minutes
3. **Critical Paths**: Auth, artifact CRUD, search
4. **Error Handling**: Network failures, timeouts

## Continuous Integration

### Test Pipeline
1. **Code Quality**: Linting, formatting checks
2. **Unit Tests**: Fast feedback on logic
3. **Integration Tests**: API contract validation
4. **E2E Tests**: Critical user journeys
5. **Performance Tests**: Regression detection
6. **Coverage Reports**: Ensure quality gates

### Quality Gates
- All tests must pass
- Coverage thresholds met
- Performance benchmarks satisfied
- No critical security issues
- Code quality standards met

## Test Data Management

### Database Isolation
- Each test uses isolated database session
- Automatic rollback after each test
- Factory patterns for consistent data
- Fixtures for complex scenarios

### Mock Strategies
- **External APIs**: Mock HTTP calls
- **Authentication**: Mock user sessions
- **File System**: Mock file operations
- **Time**: Mock datetime for consistency

## Debugging Tests

### Backend Debugging
```bash
# Run single test with verbose output
python -m pytest tests/unit/test_auth_unit.py::TestPasswordUtilities::test_hash_password -v -s

# Debug with pdb
python -m pytest tests/unit/test_auth_unit.py --pdb

# Run with coverage and open HTML report
python -m pytest --cov=services/api --cov-report=html
open htmlcov/index.html
```

### Frontend Debugging
```bash
# Run tests in watch mode
cd apps/web && npm run test:watch

# Debug specific test
cd apps/web && npm run test -- --run src/components/auth/__tests__/login-form.test.tsx

# Run E2E tests in debug mode
cd apps/web && npm run test:e2e:debug
```

### Performance Debugging
```bash
# Run with detailed output
k6 run --out json=results.json tests/performance/api-load-test.js

# Analyze results
cat results.json | jq '.metrics'
```

## Best Practices

### Writing Tests
1. **Arrange-Act-Assert**: Clear test structure
2. **Descriptive Names**: Test intent should be obvious
3. **Single Responsibility**: One assertion per test
4. **Independent Tests**: No test dependencies
5. **Fast Execution**: Mock external dependencies

### Test Organization
1. **Group Related Tests**: Use describe blocks
2. **Shared Setup**: Use fixtures and beforeEach
3. **Clean Teardown**: Proper cleanup after tests
4. **Consistent Naming**: Follow naming conventions
5. **Documentation**: Comment complex test logic

### Maintenance
1. **Regular Updates**: Keep tests current with code
2. **Flaky Test Fixes**: Address intermittent failures
3. **Performance Monitoring**: Track test execution time
4. **Coverage Analysis**: Identify untested code paths
5. **Refactoring**: Keep test code clean and DRY

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database is running
docker-compose ps postgres

# Reset test database
docker-compose restart postgres
```

#### Import Errors
```bash
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/services/api"

# Install test dependencies
pip install -r requirements-test.txt
```

#### Playwright Issues
```bash
# Install browsers
npx playwright install

# Update Playwright
npm install @playwright/test@latest
```

#### Performance Test Failures
```bash
# Check API is running
curl http://localhost:8000/api/v1/health

# Verify k6 installation
k6 version
```

## Reports and Artifacts

### Generated Reports
- `htmlcov/index.html` - Backend coverage report
- `apps/web/coverage/index.html` - Frontend coverage report  
- `apps/web/playwright-report/index.html` - E2E test report
- `performance-summary.json` - Performance test results
- `kiro_score.json` - Overall quality score

### CI Artifacts
- `test-results-unit.xml` - Unit test results (JUnit format)
- `test-results-integration.xml` - Integration test results
- `test-results-e2e.json` - E2E test results
- `coverage-unit.json` - Coverage data (JSON format)

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all test types are covered
3. Update test documentation
4. Verify coverage thresholds
5. Run full test suite before PR

For test improvements:
1. Identify gaps in coverage
2. Add missing test scenarios
3. Improve test performance
4. Enhance test utilities
5. Update documentation