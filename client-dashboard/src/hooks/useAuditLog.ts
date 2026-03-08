import { useEffect, useState } from 'react';
import type { AuditEvent } from '@/types';

export const useAuditLog = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);

  useEffect(() => {
    setEvents([]);
  }, []);

  return { events };
};
