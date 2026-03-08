import React from 'react';
import type { AuditEvent } from '@/types';
import { AuditEventCollapsible } from './AuditEventCollapsible';

interface AuditEventListProps {
  events: AuditEvent[];
}

export const AuditEventList: React.FC<AuditEventListProps> = ({ events }) => {
  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-charcoal-brown">
        No audit events found for the selected date range.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {events.map((event) => (
        <AuditEventCollapsible key={event.audit_id} event={event} />
      ))}
    </div>
  );
};
