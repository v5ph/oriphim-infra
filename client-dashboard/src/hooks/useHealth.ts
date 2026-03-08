import { useEffect, useState } from 'react';
import APIClient from '@services/api';
import type { HealthMetrics } from '@/types';
import { env } from '@config/env';

export const useHealth = (pollIntervalMs: number = env.healthCheckIntervalMs) => {
  const [health, setHealth] = useState<HealthMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      setLoading(true);
      try {
        const client = new APIClient();
        const response = await client.getHealth();
        setHealth(response.data);
        setError(null);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();

    const interval = setInterval(fetchHealth, pollIntervalMs);

    return () => clearInterval(interval);
  }, [pollIntervalMs]);

  return { health, loading, error };
};
