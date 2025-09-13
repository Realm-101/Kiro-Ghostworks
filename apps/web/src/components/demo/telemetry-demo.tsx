'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

interface PrometheusMetric {
  name: string;
  value: string;
  help: string;
  type: string;
}

const parsePrometheusMetrics = (metricsText: string): PrometheusMetric[] => {
  const lines = metricsText.split('\n');
  const metrics: PrometheusMetric[] = [];
  let currentMetric: Partial<PrometheusMetric> = {};

  for (const line of lines) {
    if (line.startsWith('# HELP ')) {
      const parts = line.split(' ');
      const name = parts[2];
      const help = parts.slice(3).join(' ');
      currentMetric = { name, help };
    } else if (line.startsWith('# TYPE ')) {
      const parts = line.split(' ');
      const type = parts[3];
      if (currentMetric.name) {
        currentMetric.type = type;
      }
    } else if (line && !line.startsWith('#') && currentMetric.name) {
      const [metricLine, value] = line.split(' ');
      if (metricLine.startsWith(currentMetric.name)) {
        metrics.push({
          name: currentMetric.name,
          value: value || '0',
          help: currentMetric.help || '',
          type: currentMetric.type || 'unknown'
        });
        currentMetric = {};
      }
    }
  }

  return metrics;
};

export const TelemetryDemo: React.FC = () => {
  const [selectedMetricType, setSelectedMetricType] = useState<string>('all');
  
  const { data: metricsText, isLoading, error } = useQuery({
    queryKey: ['prometheusMetrics'],
    queryFn: () => apiClient.getPrometheusMetrics(),
    refetchInterval: 10000, // Refresh every 10 seconds
    retry: 2,
  });

  const metrics = metricsText ? parsePrometheusMetrics(metricsText) : [];
  
  // Filter metrics by type
  const filteredMetrics = selectedMetricType === 'all' 
    ? metrics 
    : metrics.filter(m => m.type === selectedMetricType);

  // Get unique metric types
  const metricTypes = ['all', ...Array.from(new Set(metrics.map(m => m.type)))];

  // Sample Grafana dashboard URLs (these would be real in production)
  const grafanaDashboards = [
    {
      title: 'API Golden Signals',
      description: 'Request latency, throughput, and error rates',
      url: 'http://localhost:3001/d/api-golden-signals',
      preview: '/api/placeholder-dashboard-1.png'
    },
    {
      title: 'Business Metrics',
      description: 'User activity, artifact creation, workspace usage',
      url: 'http://localhost:3001/d/business-metrics',
      preview: '/api/placeholder-dashboard-2.png'
    },
    {
      title: 'System Overview',
      description: 'Infrastructure health, database performance, resource usage',
      url: 'http://localhost:3001/d/system-overview',
      preview: '/api/placeholder-dashboard-3.png'
    }
  ];

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          📈 Telemetry & Observability
        </h2>
        <p className="text-gray-600">
          Comprehensive monitoring with Prometheus metrics and Grafana dashboards
        </p>
      </div>

      {/* Prometheus Metrics Section */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            🔍 Live Prometheus Metrics
          </h3>
          <select
            value={selectedMetricType}
            onChange={(e) => setSelectedMetricType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {metricTypes.map(type => (
              <option key={type} value={type}>
                {type === 'all' ? 'All Types' : type.charAt(0).toUpperCase() + type.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-2">Loading metrics...</p>
          </div>
        ) : error ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-800">
              Metrics endpoint not available. In a production environment, this would show live Prometheus metrics.
            </p>
          </div>
        ) : (
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {filteredMetrics.slice(0, 10).map((metric, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="font-mono text-sm text-gray-900">{metric.name}</p>
                    <p className="text-xs text-gray-600 mt-1">{metric.help}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-mono text-sm font-semibold text-blue-600">{metric.value}</p>
                    <p className="text-xs text-gray-500">{metric.type}</p>
                  </div>
                </div>
              </div>
            ))}
            {filteredMetrics.length === 0 && (
              <p className="text-gray-500 text-center py-4">No metrics found for selected type</p>
            )}
          </div>
        )}
      </div>

      {/* Grafana Dashboards Section */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          📊 Grafana Dashboards
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {grafanaDashboards.map((dashboard, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="aspect-video bg-gray-100 rounded-lg mb-3 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-4xl mb-2">📈</div>
                  <p className="text-sm text-gray-600">Dashboard Preview</p>
                </div>
              </div>
              
              <h4 className="font-semibold text-gray-900 mb-1">{dashboard.title}</h4>
              <p className="text-sm text-gray-600 mb-3">{dashboard.description}</p>
              
              <button
                onClick={() => window.open(dashboard.url, '_blank')}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 px-4 rounded-md transition-colors"
              >
                View Dashboard
              </button>
            </div>
          ))}
        </div>

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 mb-2">🎯 Observability Features</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <p className="font-medium">Golden Signals Monitoring:</p>
              <ul className="list-disc list-inside mt-1 space-y-1">
                <li>Request latency (P50, P95, P99)</li>
                <li>Request throughput (RPS)</li>
                <li>Error rates by endpoint</li>
                <li>Service saturation metrics</li>
              </ul>
            </div>
            <div>
              <p className="font-medium">Business Intelligence:</p>
              <ul className="list-disc list-inside mt-1 space-y-1">
                <li>User registration trends</li>
                <li>Artifact creation patterns</li>
                <li>Workspace activity metrics</li>
                <li>Feature usage analytics</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* OpenTelemetry Tracing */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          🔗 Distributed Tracing
        </h3>
        
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="font-mono text-sm">trace_id: 1a2b3c4d5e6f7890</span>
            <span className="text-xs text-gray-500">Duration: 245ms</span>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-sm">POST /api/v1/artifacts</span>
              <span className="text-xs text-gray-500">120ms</span>
            </div>
            <div className="flex items-center space-x-2 ml-4">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm">database.create_artifact</span>
              <span className="text-xs text-gray-500">85ms</span>
            </div>
            <div className="flex items-center space-x-2 ml-4">
              <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
              <span className="text-sm">auth.verify_permissions</span>
              <span className="text-xs text-gray-500">15ms</span>
            </div>
            <div className="flex items-center space-x-2 ml-4">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span className="text-sm">metrics.record_creation</span>
              <span className="text-xs text-gray-500">5ms</span>
            </div>
          </div>
          
          <p className="text-xs text-gray-600 mt-3">
            OpenTelemetry traces provide detailed request flow analysis across all services
          </p>
        </div>
      </div>
    </div>
  );
};