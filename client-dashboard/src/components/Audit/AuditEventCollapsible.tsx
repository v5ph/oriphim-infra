import React, { useState } from 'react';
import type { AuditEvent } from '@/types';

interface AuditEventCollapsibleProps {
  event: AuditEvent;
}

export const AuditEventCollapsible: React.FC<AuditEventCollapsibleProps> = ({ event }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border border-subtle rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full text-left p-4 hover:bg-floral-white transition-colors flex justify-between items-start"
      >
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className="font-mono text-sm text-charcoal-brown">
              #{event.audit_id}
            </span>
            <span className="badge-review">{event.event_type}</span>
            {event.violations.length > 0 && (
              <span className="text-sm text-blood-red">
                {event.violations.length} violation{event.violations.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          <p className="text-sm text-carbon-black mb-1">{event.message}</p>
          <p className="text-xs text-charcoal-brown">
            {new Date(event.created_at).toLocaleString()}
          </p>
        </div>
        <div className="ml-4">
          <span className="text-charcoal-brown text-xl">
            {isExpanded ? '−' : '+'}
          </span>
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-subtle p-4 bg-floral-white/50 space-y-3">
          <div>
            <p className="text-sm text-charcoal-brown mb-1">Request ID</p>
            <p className="font-mono text-sm text-carbon-black">{event.request_id}</p>
          </div>

          {event.agent_id && (
            <div>
              <p className="text-sm text-charcoal-brown mb-1">Agent ID</p>
              <p className="font-mono text-sm text-carbon-black">{event.agent_id}</p>
            </div>
          )}

          {event.violations.length > 0 && (
            <div>
              <p className="text-sm text-charcoal-brown mb-1">Violations</p>
              <ul className="space-y-1">
                {event.violations.map((violation, idx) => (
                  <li key={idx} className="text-sm text-blood-red">
                    • {violation}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {event.regulatory_articles.length > 0 && (
            <div>
              <p className="text-sm text-charcoal-brown mb-1">Regulatory Articles</p>
              <ul className="space-y-1">
                {event.regulatory_articles.map((article, idx) => (
                  <li key={idx} className="text-sm text-carbon-black">
                    • {article}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="bg-white rounded p-3">
            <p className="text-sm text-charcoal-brown mb-1">Chain Hash</p>
            <p className="font-mono text-xs text-carbon-black break-all">{event.chain_hash}</p>
          </div>

          <div className="bg-white rounded p-3">
            <p className="text-sm text-charcoal-brown mb-1">Previous Hash</p>
            <p className="font-mono text-xs text-carbon-black break-all">{event.prev_hash}</p>
          </div>
        </div>
      )}
    </div>
  );
};
