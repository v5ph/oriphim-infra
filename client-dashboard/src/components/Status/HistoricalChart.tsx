import React from 'react';
import type { HealthMetrics } from '@/types';

interface HistoricalChartProps {
  health: HealthMetrics;
}

export const HistoricalChart: React.FC<HistoricalChartProps> = ({ health }) => {
  return (
    <div className="text-charcoal-brown">
      Historical chart placeholder. Current divergence: {health.recent_divergence_avg.toFixed(4)}
    </div>
  );
};
