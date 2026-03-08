import React, { useState } from 'react';
import type { ValidationMetrics } from '@/types';
import { ValidationRow } from './ValidationRow';
import { ValidationDetailModal } from './ValidationDetailModal';

interface ValidationTableProps {
  validations: ValidationMetrics[];
}

export const ValidationTable: React.FC<ValidationTableProps> = ({ validations }) => {
  const [selectedValidation, setSelectedValidation] = useState<ValidationMetrics | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleRowClick = (validation: ValidationMetrics) => {
    setSelectedValidation(validation);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedValidation(null);
  };

  if (validations.length === 0) {
    return <div className="text-charcoal-brown">No recent validations.</div>;
  }

  return (
    <>
      <div className="overflow-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left border-b border-subtle">
              <th className="py-2 pr-4">Request ID</th>
              <th className="py-2 pr-4">Timestamp</th>
              <th className="py-2 pr-4">Indicator</th>
              <th className="py-2 pr-4">Action</th>
              <th className="py-2 pr-4">Violations</th>
              <th className="py-2 pr-4">Divergence</th>
            </tr>
          </thead>
          <tbody>
            {validations.map((validation, idx) => (
              <ValidationRow
                key={`${validation.request_id}-${validation.timestamp}-${idx}`}
                validation={validation}
                onClick={() => handleRowClick(validation)}
              />
            ))}
          </tbody>
        </table>
      </div>

      <ValidationDetailModal
        validation={selectedValidation}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </>
  );
};
