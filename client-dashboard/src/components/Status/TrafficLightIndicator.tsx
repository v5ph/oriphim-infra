import React from 'react';
import type { IndicatorStatus } from '@/types';

interface TrafficLightProps {
  status: IndicatorStatus;
  size?: 'sm' | 'md' | 'lg';
}

export const TrafficLightIndicator: React.FC<TrafficLightProps> = ({ status, size = 'lg' }) => {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-16 h-16',
    lg: 'w-24 h-24',
  };

  const statusClasses = {
    GREEN: 'bg-green-500 shadow-green-500/50',
    YELLOW: 'bg-yellow-500 shadow-yellow-500/50',
    RED: 'bg-blood-red shadow-blood-red/50',
  };

  const labelClasses = {
    GREEN: 'text-green-700',
    YELLOW: 'text-yellow-700',
    RED: 'text-blood-red',
  };

  return (
    <div className="flex flex-col items-center gap-3">
      <div className={`${sizeClasses[size]} rounded-full ${statusClasses[status]} shadow-lg animate-pulse`} />
      <span className={`text-lg font-bold ${labelClasses[status]}`}>{status}</span>
    </div>
  );
};
