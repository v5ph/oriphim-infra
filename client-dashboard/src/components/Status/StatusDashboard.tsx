import React from 'react';
import { useHealth } from '@hooks/useHealth';
import { TrafficLightIndicator } from './TrafficLightIndicator';
import { MetricsGrid } from './MetricsGrid';
import { HistoricalChart } from './HistoricalChart';

export const StatusDashboard: React.FC = () => {
  const { health, loading, error } = useHealth();

  if (loading && !health) {
    return <div className="p-8 text-center">Loading system status...</div>;
  }

  if (error && !health) {
    return (
      <div className="p-8 alert-danger">
        <div className="flex items-center gap-3">
          <svg className="w-5 h-5 text-danger-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div>
            <p className="font-semibold text-danger-800">API Connection Failed</p>
            <p className="text-sm text-danger-700 mt-1">{error}</p>
            <p className="text-xs text-danger-600 mt-2">Ensure backend is running at <code className="code-inline">localhost:8000</code></p>
          </div>
        </div>
      </div>
    );
  }

  if (!health) {
    return <div className="p-8 text-center">No health data available</div>;
  }

  return (
    <div className="space-y-8 p-8">
      <section className="card flex justify-center">
        <TrafficLightIndicator status={health.indicator} size="lg" />
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4 text-primary">System Metrics</h2>
        <MetricsGrid health={health} />
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4 text-primary">Last 24 Hours</h2>
        <div className="card">
          <HistoricalChart health={health} />
        </div>
      </section>

      <section className="card">
        <h3 className="text-lg font-bold text-primary mb-2">Status Summary</h3>
        <p className="text-secondary">
          System is currently <strong>{health.status}</strong>.
          {health.indicator === 'RED' && <> Review active incidents immediately.</>}
          {health.indicator === 'YELLOW' && <> Monitor system for escalation.</>}
          {health.indicator === 'GREEN' && <> All systems operating normally.</>}
        </p>
      </section>
    </div>
  );
};
