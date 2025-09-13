/**
 * K6 Performance Test for Ghostworks API
 * Tests API endpoints under load to ensure performance requirements are met.
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const authLatency = new Trend('auth_latency');
const artifactLatency = new Trend('artifact_latency');

// Test configuration with realistic, route-class specific thresholds
export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 users
    { duration: '1m', target: 20 },    // Stay at 20 users
    { duration: '30s', target: 50 },   // Ramp up to 50 users
    { duration: '2m', target: 50 },    // Stay at 50 users
    { duration: '30s', target: 0 },    // Ramp down
  ],
  thresholds: {
    // Overall API performance (general CRUD operations)
    http_req_duration: ['p(95)<200'],     // 95% of requests under 200ms
    http_req_failed: ['rate<0.01'],       // Error rate under 1% (more aggressive)
    
    // Route-class specific thresholds
    'http_req_duration{route_class:health}': ['p(95)<50'],      // Health checks: 50ms
    'http_req_duration{route_class:auth}': ['p(95)<150'],       // Auth operations: 150ms (crypto overhead)
    'http_req_duration{route_class:crud_simple}': ['p(95)<200'], // Simple CRUD: 200ms
    'http_req_duration{route_class:search}': ['p(95)<500'],     // Search operations: 500ms
    
    // Custom metrics
    errors: ['rate<0.01'],
    auth_latency: ['p(95)<150'],          // Auth-specific latency
    artifact_latency: ['p(95)<200'],      // Artifact operations
    
    // Cold start exclusions (for local development)
    'http_req_duration{exclude_cold_start:true}': ['p(95)<200'],
  },
  
  // Environment-specific overrides
  ...((__ENV.ENVIRONMENT === 'production') ? {
    // Production: More aggressive thresholds
    thresholds: {
      http_req_duration: ['p(95)<150'],   // Tighter production SLA
      http_req_failed: ['rate<0.005'],    // 0.5% error rate for production
    }
  } : {}),
  
  ...((__ENV.ENVIRONMENT === 'local') ? {
    // Local: More lenient thresholds (cold starts, dev overhead)
    thresholds: {
      http_req_duration: ['p(95)<500'],   // More lenient for local dev
      http_req_failed: ['rate<0.02'],     // 2% error rate acceptable locally
    }
  } : {}),
};

// Test data
const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';
const TEST_USER = {
  email: `perf-test-${Date.now()}@example.com`,
  password: 'TestPassword123!',
  first_name: 'Performance',
  last_name: 'Test'
};

let authToken = '';
let workspaceId = '';

export function setup() {
  console.log('Setting up performance test...');
  
  // Register test user
  const registerResponse = http.post(`${BASE_URL}/api/v1/auth/register`, JSON.stringify(TEST_USER), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  if (registerResponse.status !== 201) {
    console.error('Failed to register test user:', registerResponse.body);
    return {};
  }
  
  // Login to get auth token
  const loginResponse = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
    email: TEST_USER.email,
    password: TEST_USER.password
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  if (loginResponse.status !== 200) {
    console.error('Failed to login test user:', loginResponse.body);
    return {};
  }
  
  const loginData = JSON.parse(loginResponse.body);
  authToken = loginData.access_token;
  
  // Create test workspace
  const workspaceResponse = http.post(`${BASE_URL}/api/v1/workspaces`, JSON.stringify({
    name: 'Performance Test Workspace',
    description: 'Workspace for performance testing'
  }), {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
  });
  
  if (workspaceResponse.status !== 201) {
    console.error('Failed to create test workspace:', workspaceResponse.body);
    return { authToken };
  }
  
  const workspaceData = JSON.parse(workspaceResponse.body);
  workspaceId = workspaceData.id;
  
  console.log('Performance test setup complete');
  return { authToken, workspaceId };
}

export default function(data) {
  const { authToken, workspaceId } = data;
  
  if (!authToken || !workspaceId) {
    console.error('Missing setup data, skipping test iteration');
    return;
  }
  
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
  
  // Skip first iteration to exclude cold start effects in local development
  const excludeColdStart = __ENV.ENVIRONMENT === 'local' && __ITER === 0;
  
  // Test 1: Health check (should be very fast)
  const healthResponse = http.get(`${BASE_URL}/api/v1/health`, {
    tags: { 
      route_class: 'health',
      exclude_cold_start: excludeColdStart ? 'false' : 'true'
    }
  });
  
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 50ms': (r) => r.timings.duration < 50,
  }) || errorRate.add(1);
  
  sleep(0.1);
  
  // Test 2: Get user info (auth performance)
  const userInfoStart = Date.now();
  const userInfoResponse = http.get(`${BASE_URL}/api/v1/auth/me`, { 
    headers,
    tags: { 
      route_class: 'auth',
      exclude_cold_start: excludeColdStart ? 'false' : 'true'
    }
  });
  const userInfoDuration = Date.now() - userInfoStart;
  
  authLatency.add(userInfoDuration);
  
  check(userInfoResponse, {
    'user info status is 200': (r) => r.status === 200,
    'user info has email': (r) => JSON.parse(r.body).email !== undefined,
  }) || errorRate.add(1);
  
  sleep(0.2);
  
  // Test 3: List artifacts (read performance)
  const listArtifactsStart = Date.now();
  const listResponse = http.get(`${BASE_URL}/api/v1/workspaces/${workspaceId}/artifacts`, { 
    headers,
    tags: { 
      route_class: 'crud_simple',
      exclude_cold_start: excludeColdStart ? 'false' : 'true'
    }
  });
  const listDuration = Date.now() - listArtifactsStart;
  
  artifactLatency.add(listDuration);
  
  check(listResponse, {
    'list artifacts status is 200': (r) => r.status === 200,
    'list artifacts has items': (r) => JSON.parse(r.body).items !== undefined,
    'list artifacts has pagination': (r) => {
      const body = JSON.parse(r.body);
      return body.total !== undefined && body.limit !== undefined;
    },
  }) || errorRate.add(1);
  
  sleep(0.3);
  
  // Test 4: Create artifact (write performance)
  const artifactData = {
    name: `Performance Test Artifact ${__VU}-${__ITER}`,
    description: 'An artifact created during performance testing',
    tags: ['performance', 'test', 'k6'],
    artifact_metadata: {
      test_run: __ITER,
      virtual_user: __VU,
      timestamp: new Date().toISOString()
    }
  };
  
  const createArtifactStart = Date.now();
  const createResponse = http.post(
    `${BASE_URL}/api/v1/workspaces/${workspaceId}/artifacts`,
    JSON.stringify(artifactData),
    { 
      headers,
      tags: { 
        route_class: 'crud_simple',
        exclude_cold_start: excludeColdStart ? 'false' : 'true'
      }
    }
  );
  const createDuration = Date.now() - createArtifactStart;
  
  artifactLatency.add(createDuration);
  
  const createSuccess = check(createResponse, {
    'create artifact status is 201': (r) => r.status === 201,
    'create artifact returns id': (r) => JSON.parse(r.body).id !== undefined,
    'create artifact preserves data': (r) => {
      const body = JSON.parse(r.body);
      return body.name === artifactData.name && 
             body.description === artifactData.description;
    },
  });
  
  if (!createSuccess) {
    errorRate.add(1);
  }
  
  // Test 5: Search artifacts (search performance)
  if (createSuccess && createResponse.status === 201) {
    sleep(0.1);
    
    const searchResponse = http.get(
      `${BASE_URL}/api/v1/workspaces/${workspaceId}/artifacts?q=Performance`,
      { 
        headers,
        tags: { 
          route_class: 'search',
          exclude_cold_start: excludeColdStart ? 'false' : 'true'
        }
      }
    );
    
    check(searchResponse, {
      'search artifacts status is 200': (r) => r.status === 200,
      'search finds results': (r) => {
        const body = JSON.parse(r.body);
        return body.items && body.items.length > 0;
      },
    }) || errorRate.add(1);
  }
  
  sleep(0.5);
}

export function teardown(data) {
  console.log('Cleaning up performance test...');
  
  const { authToken, workspaceId } = data;
  
  if (authToken && workspaceId) {
    // Clean up test workspace (this will cascade delete artifacts)
    const deleteResponse = http.del(`${BASE_URL}/api/v1/workspaces/${workspaceId}`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    
    if (deleteResponse.status === 204) {
      console.log('Test workspace cleaned up successfully');
    } else {
      console.warn('Failed to clean up test workspace:', deleteResponse.status);
    }
  }
  
  console.log('Performance test teardown complete');
}

// Custom summary function
export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test_duration: data.state.testRunDurationMs,
    metrics: {
      http_req_duration: {
        avg: data.metrics.http_req_duration.values.avg,
        p95: data.metrics.http_req_duration.values['p(95)'],
        p99: data.metrics.http_req_duration.values['p(99)'],
        max: data.metrics.http_req_duration.values.max
      },
      http_req_failed: {
        rate: data.metrics.http_req_failed.values.rate,
        count: data.metrics.http_req_failed.values.count
      },
      http_reqs: {
        count: data.metrics.http_reqs.values.count,
        rate: data.metrics.http_reqs.values.rate
      },
      vus: {
        max: data.metrics.vus.values.max
      }
    },
    thresholds: data.thresholds,
    performance_grade: calculatePerformanceGrade(data)
  };
  
  return {
    'performance-summary.json': JSON.stringify(summary, null, 2),
    'stdout': generateTextSummary(summary)
  };
}

function calculatePerformanceGrade(data) {
  const p95Latency = data.metrics.http_req_duration.values['p(95)'];
  const errorRate = data.metrics.http_req_failed.values.rate;
  
  if (p95Latency < 100 && errorRate < 0.01) return 'A';
  if (p95Latency < 200 && errorRate < 0.05) return 'B';
  if (p95Latency < 500 && errorRate < 0.1) return 'C';
  if (p95Latency < 1000 && errorRate < 0.2) return 'D';
  return 'F';
}

function generateTextSummary(summary) {
  return `
🚀 Performance Test Results
==========================
Duration: ${(summary.test_duration / 1000).toFixed(1)}s
Grade: ${summary.performance_grade}

📊 Key Metrics:
- Average Response Time: ${summary.metrics.http_req_duration.avg.toFixed(1)}ms
- 95th Percentile: ${summary.metrics.http_req_duration.p95.toFixed(1)}ms
- Error Rate: ${(summary.metrics.http_req_failed.rate * 100).toFixed(2)}%
- Total Requests: ${summary.metrics.http_reqs.count}
- Requests/sec: ${summary.metrics.http_reqs.rate.toFixed(1)}

🎯 Thresholds:
${Object.entries(summary.thresholds).map(([key, value]) => 
  `- ${key}: ${value.ok ? '✅ PASS' : '❌ FAIL'}`
).join('\n')}
`;
}