import React, { useEffect, useState } from 'react';
import type { ValidationMetrics } from '@/types';
import { IncidentList } from './IncidentList';
import { RewindModal } from './RewindModal';

export const IncidentPanel: React.FC = () => {
  const [incidents, setIncidents] = useState<ValidationMetrics[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [isRewindModalOpen, setIsRewindModalOpen] = useState(false);

  useEffect(() => {
    const fetchIncidents = async () => {
      setLoading(true);
      try {
        setIncidents([]);
      } catch (err) {
        console.error('Failed to fetch incidents:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchIncidents();
    const interval = setInterval(fetchIncidents, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleRewindClick = (agentId: string) => {
    setSelectedAgentId(agentId);
    setIsRewindModalOpen(true);
  };

  const handleRewindSuccess = () => {
    setIncidents((prev) =>
      prev.filter((inc) => inc.request_id !== selectedAgentId)
    );
  };

  const handleCloseModal = () => {
    setIsRewindModalOpen(false);
    setSelectedAgentId(null);
  };

  if (loading && incidents.length === 0) {
    return <div className="p-8 text-center">Loading incidents...</div>;
  }

  return (
    <div className="space-y-4 p-8">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-carbon-black">Active Incidents</h2>
        {incidents.length > 0 && (
          <span className="bg-blood-red text-floral-white px-3 py-1 rounded-full text-sm font-bold">
            {incidents.length}
          </span>
        )}
      </div>

      <div className="card">
        <IncidentList incidents={incidents} onRewind={handleRewindClick} />
      </div>

      <RewindModal
        agentId={selectedAgentId}
        isOpen={isRewindModalOpen}
        onClose={handleCloseModal}
        onSuccess={handleRewindSuccess}
      />
    </div>
  );
};
