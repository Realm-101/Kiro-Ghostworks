'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

interface MetricCardProps {
  title: string;
  value: number | string;
  description: string;
  icon: string;
  isLoading?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  description, 
  icon, 
  isLoading = false 
}) => (
  <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className="text-3xl font-bold text-gray-900 mt-2">
          {isLoading ? (
            <span className="animate-pulse bg-gray-200 rounded w-16 h-8 inline-block"></span>
          ) : (
            value
          )}
        </p>
        <p className="text-sm text-gray-500 mt-1">{description}</p>
      </div>
      <div className="text-4xl">{icon}</div>
    </div>
  </div>
);

export const MetricsDashboard: React.FC = () => {
  const { data: systemStats, isLoading, error } = useQuery({
    queryKey: ['systemStats'],
    queryFn: () => apiClient.getSystemStats(),
    refetchInterval: 5000, // Refresh every 5 seconds for live demo
    retry: 3,
  });

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">
          Failed to load system metrics. This might be expected if the API is not running.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          📊 Live System Metrics
        </h2>
        <p className="text-gray-600">
          Real-time statistics from the Ghostworks platform
        </p>
        {systemStats?.timestamp && (
          <p className="text-sm text-gray-500 mt-2">
            Last updated: {new Date(systemStats.timestamp).toLocaleTimeString()}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Users"
          value={systemStats?.users ?? 0}
          description="Registered platform users"
          icon="👥"
          isLoading={isLoading}
        />
        
        <MetricCard
          title="Workspaces"
          value={systemStats?.workspaces ?? 0}
          description="Active tenant workspaces"
          icon="🏢"
          isLoading={isLoading}
        />
        
        <MetricCard
          title="Total Artifacts"
          value={systemStats?.artifacts ?? 0}
          description="All artifacts in system"
          icon="📦"
          isLoading={isLoading}
        />
        
        <MetricCard
          title="Active Artifacts"
          value={systemStats?.active_artifacts ?? 0}
          description="Currently active artifacts"
          icon="✅"
          isLoading={isLoading}
        />
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">🔄 Live Updates</h3>
        <p className="text-blue-800 text-sm">
          These metrics refresh automatically every 5 seconds to demonstrate real-time monitoring capabilities.
          In a production environment, these would be sourced from Prometheus metrics and displayed in Grafana dashboards.
        </p>
      </div>
    </div>
  );
};