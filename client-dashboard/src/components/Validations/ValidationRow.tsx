import React from 'react';
import type { ValidationMetrics } from '@/types';

interface ValidationRowProps {
  validation: ValidationMetrics;
  onClick: () => void;
}

export const ValidationRow: React.FC<ValidationRowProps> = ({ validation, onClick }) => {
  const getActionBadgeClass = (action: string) => {
    switch (action) {
      case 'ALLOW':
        return 'badge-allow';
      case 'REVIEW':
      case 'CAUTION':
        return 'badge-review';
      case 'BLOCK':
        return 'badge-block';
      default:
        return 'badge-review';
    }
  };

  const getIndicatorClass = (indicator: string) => {
    switch (indicator) {
      case 'GREEN':
        return 'status-green';
      case 'YELLOW':
        return 'status-yellow';
      case 'RED':
        return 'status-red';
      default:
        return '';
    }
  };

  return (
    <tr
      onClick={onClick}
      className="border-b border-subtle/50 hover:bg-floral-white cursor-pointer transition-colors"
    >
      <td className="py-3 pr-4">
        <span className="font-mono text-sm text-carbon-black">
          {validation.request_id?.substring(0, 8) || 'N/A'}
        </span>
      </td>
      <td className="py-3 pr-4">
        <span className="text-sm text-charcoal-brown">
          {new Date(validation.timestamp).toLocaleString()}
        </span>
      </td>
      <td className="py-3 pr-4">
        <span className={`${getIndicatorClass(validation.indicator)} inline-block px-2 py-1 rounded text-xs font-medium`}>
          {validation.indicator}
        </span>
      </td>
      <td className="py-3 pr-4">
        <span className={getActionBadgeClass(validation.action_label)}>
          {validation.action_label}
        </span>
      </td>
      <td className="py-3 pr-4">
        <span className="text-sm text-charcoal-brown">
          {validation.violations.length > 0 ? validation.violations.length : '—'}
        </span>
      </td>
      <td className="py-3">
        <span className="text-sm text-carbon-black font-mono">
          {validation.divergence_score.toFixed(4)}
        </span>
      </td>
    </tr>
  );
};
