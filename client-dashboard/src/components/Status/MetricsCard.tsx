import React from 'react';

interface MetricsCardProps {
  label: string;
  value: string | number;
}

export const MetricsCard: React.FC<MetricsCardProps> = ({ label, value }) => {
  return (
    <div className="card">
      <p className="text-sm text-charcoal-brown">{label}</p>
      <p className="text-2xl font-bold text-carbon-black">{value}</p>
    </div>
  );
};
