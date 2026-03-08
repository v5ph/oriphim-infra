import React from 'react';
import type { HealthMetrics } from '@/types';

interface MetricsGridProps {
  health: HealthMetrics;
}

export const MetricsGrid: React.FC<MetricsGridProps> = ({ health }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="card">
        <p className="text-sm text-charcoal-brown">Uptime Requests</p>
        <p className="text-2xl font-bold text-carbon-black">{health.uptime_requests}</p>
      </div>
      <div className="card">
        <p className="text-sm text-charcoal-brown">Avg Divergence</p>
        <p className="text-2xl font-bold text-carbon-black">{health.recent_divergence_avg.toFixed(4)}</p>
      </div>
      <div className="card">
        <p className="text-sm text-charcoal-brown">Violation Rate</p>
        <p className="text-2xl font-bold text-carbon-black">{(health.recent_violation_rate * 100).toFixed(2)}%</p>
      </div>
      <div className="card">
        <p className="text-sm text-charcoal-brown">Drift Detected</p>
        <p className="text-2xl font-bold text-carbon-black">{health.drift_detected ? 'Yes' : 'No'}</p>
      </div>
    </div>
  );
};
