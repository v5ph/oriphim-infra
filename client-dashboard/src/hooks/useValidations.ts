import { useEffect, useState } from 'react';
import type { ValidationMetrics } from '@/types';

export const useValidations = () => {
  const [validations, setValidations] = useState<ValidationMetrics[]>([]);

  useEffect(() => {
    setValidations([]);
  }, []);

  return { validations };
};
