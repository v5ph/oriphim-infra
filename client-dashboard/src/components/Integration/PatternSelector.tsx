import React from 'react';

export type IntegrationPattern = 'sync' | 'async' | 'webhook';

interface PatternSelectorProps {
  selected: IntegrationPattern;
  onChange: (pattern: IntegrationPattern) => void;
}

export const PatternSelector: React.FC<PatternSelectorProps> = ({ selected, onChange }) => {
  const patterns: Array<{
    value: IntegrationPattern;
    label: string;
    description: string;
  }> = [
    {
      value: 'sync',
      label: 'Synchronous',
      description: 'Block until validation completes. Best for real-time decisions.',
    },
    {
      value: 'async',
      label: 'Asynchronous',
      description: 'Poll for results. Best for batch processing and background jobs.',
    },
    {
      value: 'webhook',
      label: 'Webhook',
      description: 'Receive callback when validation completes. Best for event-driven workflows.',
    },
  ];

  return (
    <div className="card">
      <h3 className="text-lg font-bold text-carbon-black mb-4">Integration Pattern</h3>
      <div className="space-y-3">
        {patterns.map((pattern) => (
          <label
            key={pattern.value}
            className="flex items-start gap-3 p-4 border border-subtle rounded hover:bg-floral-white cursor-pointer transition-colors"
          >
            <input
              type="radio"
              name="pattern"
              value={pattern.value}
              checked={selected === pattern.value}
              onChange={() => onChange(pattern.value)}
              className="mt-1 w-4 h-4 text-blood-red focus:ring-blood-red"
            />
            <div className="flex-1">
              <div className="font-medium text-carbon-black">{pattern.label}</div>
              <div className="text-sm text-charcoal-brown mt-1">{pattern.description}</div>
            </div>
          </label>
        ))}
      </div>
    </div>
  );
};
