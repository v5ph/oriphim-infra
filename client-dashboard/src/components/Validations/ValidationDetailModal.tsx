import React from 'react';
import type { ValidationMetrics } from '@/types';

interface ValidationDetailModalProps {
  validation: ValidationMetrics | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ValidationDetailModal: React.FC<ValidationDetailModalProps> = ({
  validation,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !validation) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-carbon-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto m-4">
        <div className="sticky top-0 bg-white border-b border-subtle p-6 flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-carbon-black">Validation Details</h2>
            <p className="text-sm text-charcoal-brown mt-1">
              Request ID: {validation.request_id || 'N/A'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-charcoal-brown hover:text-carbon-black text-2xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="p-6 space-y-6">
          <section className="card">
            <h3 className="text-lg font-bold text-carbon-black mb-3">Decision</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-charcoal-brown">Action</p>
                <span className={`badge-${validation.action_label.toLowerCase()}`}>
                  {validation.action_label}
                </span>
              </div>
              <div>
                <p className="text-sm text-charcoal-brown">Indicator</p>
                <span className={`status-${validation.indicator.toLowerCase()} inline-block px-3 py-1 rounded text-sm font-medium`}>
                  {validation.indicator}
                </span>
              </div>
              <div className="col-span-2">
                <p className="text-sm text-charcoal-brown">Reason</p>
                <p className="text-carbon-black mt-1">{validation.action_reason}</p>
              </div>
              <div className="col-span-2">
                <p className="text-sm text-charcoal-brown">Recommendation</p>
                <p className="text-carbon-black mt-1">{validation.recommendation}</p>
              </div>
            </div>
          </section>

          <section className="card">
            <h3 className="text-lg font-bold text-carbon-black mb-3">Confidence Analysis</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-charcoal-brown">Confidence Score</span>
                <span className="font-bold text-carbon-black">{validation.confidence.score.toFixed(4)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-charcoal-brown">Risk Level</span>
                <span className="font-bold text-carbon-black">{validation.confidence.risk_level}</span>
              </div>
              <div>
                <p className="text-sm text-charcoal-brown mb-1">Explanation</p>
                <p className="text-carbon-black">{validation.confidence.explanation}</p>
              </div>
            </div>
          </section>

          {validation.violations.length > 0 && (
            <section className="card">
              <h3 className="text-lg font-bold text-carbon-black mb-3">Violations</h3>
              <ul className="space-y-1">
                {validation.violations.map((violation, idx) => (
                  <li key={idx} className="text-blood-red">
                    • {violation}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {validation.violation_severities.length > 0 && (
            <section className="card">
              <h3 className="text-lg font-bold text-carbon-black mb-3">Severity Analysis</h3>
              <div className="space-y-3">
                {validation.violation_severities.map((sev, idx) => (
                  <div key={idx} className="border-l-4 border-blood-red pl-3">
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-medium text-carbon-black">{sev.name}</span>
                      <span className="text-sm text-charcoal-brown">
                        {sev.severity_pct.toFixed(1)}% (weight: {sev.weight.toFixed(2)})
                      </span>
                    </div>
                    <p className="text-sm text-charcoal-brown">{sev.impact_description}</p>
                  </div>
                ))}
                {validation.overall_severity_score !== null && (
                  <div className="pt-2 border-t border-subtle">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-carbon-black">Overall Severity</span>
                      <span className="font-bold text-blood-red">
                        {validation.overall_severity_score.toFixed(2)}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          <section className="card">
            <h3 className="text-lg font-bold text-carbon-black mb-3">Drift Detection</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-charcoal-brown">Detected</span>
                <span className={`font-bold ${validation.drift.detected ? 'text-blood-red' : 'text-green-700'}`}>
                  {validation.drift.detected ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-charcoal-brown">Z-Score</span>
                <span className="font-mono text-carbon-black">{validation.drift.z_score.toFixed(4)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-charcoal-brown">Historical Mean</span>
                <span className="font-mono text-carbon-black">{validation.drift.historical_mean.toFixed(4)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-charcoal-brown">Current Value</span>
                <span className="font-mono text-carbon-black">{validation.drift.current_value.toFixed(4)}</span>
              </div>
              <div>
                <p className="text-sm text-charcoal-brown mb-1">Explanation</p>
                <p className="text-carbon-black">{validation.drift.explanation}</p>
              </div>
            </div>
          </section>

          <section className="card">
            <h3 className="text-lg font-bold text-carbon-black mb-3">Metadata</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-charcoal-brown">Timestamp</p>
                <p className="text-carbon-black font-mono text-sm">{validation.timestamp}</p>
              </div>
              <div>
                <p className="text-sm text-charcoal-brown">Status Code</p>
                <p className="text-carbon-black font-mono">{validation.status_code}</p>
              </div>
              <div>
                <p className="text-sm text-charcoal-brown">Divergence Score</p>
                <p className="text-carbon-black font-mono">{validation.divergence_score.toFixed(6)}</p>
              </div>
              {validation.latency_ms && (
                <div>
                  <p className="text-sm text-charcoal-brown">Latency</p>
                  <p className="text-carbon-black font-mono">{validation.latency_ms}ms</p>
                </div>
              )}
              {validation.context_reset !== undefined && (
                <div>
                  <p className="text-sm text-charcoal-brown">Context Reset</p>
                  <p className="text-carbon-black">{validation.context_reset ? 'Yes' : 'No'}</p>
                </div>
              )}
            </div>
          </section>
        </div>

        <div className="sticky bottom-0 bg-white border-t border-subtle p-6">
          <button
            onClick={onClose}
            className="btn-primary px-6 py-2 rounded font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
