import React, { useEffect, useState } from 'react';
import type { ValidationMetrics } from '@/types';
import { ValidationTable } from './ValidationTable';

export const RecentValidations: React.FC = () => {
  const [validations, setValidations] = useState<ValidationMetrics[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchValidations = async () => {
      setLoading(true);
      try {
        setValidations([]);
      } catch (err) {
        console.error('Failed to fetch validations:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchValidations();
    const interval = setInterval(fetchValidations, 5000);

    return () => clearInterval(interval);
  }, []);

  if (loading && validations.length === 0) {
    return <div className="p-8 text-center">Loading validations...</div>;
  }

  return (
    <div className="space-y-4 p-8">
      <h2 className="text-2xl font-bold text-carbon-black">Recent Validations</h2>
      <div className="card">
        <ValidationTable validations={validations} />
      </div>
    </div>
  );
};
