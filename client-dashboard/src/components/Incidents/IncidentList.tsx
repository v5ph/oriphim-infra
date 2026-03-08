import React from 'react';
import type { ValidationMetrics } from '@/types';

interface IncidentListProps {
  incidents: ValidationMetrics[];
  onRewind: (agentId: string) => void;
}

export const IncidentList: React.FC<IncidentListProps> = ({ incidents, onRewind }) => {
  if (incidents.length === 0) {
    return (
      <div className="text-center py-8 text-charcoal-brown">
        No active incidents. System operating normally.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {incidents.map((incident, idx) => {
        const agentId = incident.request_id || `unknown-${idx}`;

        return (
          <div
            key={`${incident.request_id}-${incident.timestamp}-${idx}`}
            className="bg-danger-bg border border-blood-red rounded-lg p-4"
          >
            <div className="flex justify-between items-start mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="badge-block">BLOCKED</span>
                  <span className="text-sm text-charcoal-brown">
                    {new Date(incident.timestamp).toLocaleString()}
                  </span>
                </div>
                <p className="font-mono text-sm text-carbon-black">
                  Agent: {agentId.substring(0, 16)}{agentId.length > 16 ? '...' : ''}
                </p>
              </div>
              <button
                onClick={() => onRewind(agentId)}
                className="btn-secondary px-4 py-2 rounded text-sm font-medium"
              >
                Rewind Agent
              </button>
            </div>

            <div className="mb-2">
              <p className="text-sm text-charcoal-brown mb-1">Reason:</p>
              <p className="text-sm text-carbon-black">{incident.action_reason}</p>
            </div>

            {incident.violations.length > 0 && (
              <div>
                <p className="text-sm text-charcoal-brown mb-1">
                  Violations ({incident.violations.length}):
                </p>
                <ul className="space-y-1">
                  {incident.violations.slice(0, 3).map((violation, vIdx) => (
                    <li key={vIdx} className="text-sm text-blood-red">
                      • {violation}
                    </li>
                  ))}
                  {incident.violations.length > 3 && (
                    <li className="text-sm text-charcoal-brown italic">
                      +{incident.violations.length - 3} more
                    </li>
                  )}
                </ul>
              </div>
            )}

            {incident.overall_severity_score !== null && (
              <div className="mt-3 pt-3 border-t border-blood-red/20">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-charcoal-brown">Severity Score</span>
                  <span className="font-bold text-blood-red">
                    {incident.overall_severity_score.toFixed(2)}
                  </span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
