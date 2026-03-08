import React, { useState } from 'react';
import type { RewindResponse } from '@/types';
import APIClient from '@services/api';

interface RewindModalProps {
  agentId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (response: RewindResponse) => void;
}

export const RewindModal: React.FC<RewindModalProps> = ({
  agentId,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [isRewinding, setIsRewinding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rewindResult, setRewindResult] = useState<RewindResponse | null>(null);

  if (!isOpen || !agentId) {
    return null;
  }

  const handleConfirmRewind = async () => {
    setIsRewinding(true);
    setError(null);

    try {
      const client = new APIClient();
      const response = await client.rewindAgent(agentId);
      setRewindResult(response.data);

      if (onSuccess) {
        onSuccess(response.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Rewind operation failed');
    } finally {
      setIsRewinding(false);
    }
  };

  const handleClose = () => {
    setRewindResult(null);
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-carbon-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full m-4">
        <div className="border-b border-subtle p-6">
          <h2 className="text-2xl font-bold text-carbon-black">
            {rewindResult ? 'Rewind Complete' : 'Confirm Agent Rewind'}
          </h2>
        </div>

        <div className="p-6 space-y-4">
          {!rewindResult && !error && (
            <>
              <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
                <p className="text-sm text-yellow-800 font-medium">
                  Warning: This action will restore the agent to its last known safe state.
                </p>
              </div>

              <div className="space-y-2">
                <p className="text-charcoal-brown">Agent ID:</p>
                <p className="font-mono text-carbon-black bg-floral-white px-3 py-2 rounded">
                  {agentId}
                </p>
              </div>

              <div className="bg-floral-white rounded p-4">
                <p className="text-sm text-charcoal-brown">
                  This will:
                </p>
                <ul className="mt-2 space-y-1 text-sm text-carbon-black">
                  <li>• Restore the agent's system prompt from the last snapshot</li>
                  <li>• Reset the conversation context and variables</li>
                  <li>• Clear any accumulated violations</li>
                  <li>• Create an audit log entry for this action</li>
                </ul>
              </div>
            </>
          )}

          {error && (
            <div className="bg-red-50 border border-blood-red rounded p-4">
              <p className="text-sm font-medium text-blood-red mb-1">Rewind Failed</p>
              <p className="text-sm text-charcoal-brown">{error}</p>
            </div>
          )}

          {rewindResult && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded p-4">
                <p className="text-sm font-medium text-green-800">
                  {rewindResult.restored ? 'Agent successfully restored' : 'Rewind completed'}
                </p>
              </div>

              <div className="space-y-3">
                <div>
                  <p className="text-sm text-charcoal-brown">Agent ID</p>
                  <p className="font-mono text-carbon-black">{rewindResult.agent_id}</p>
                </div>

                {rewindResult.snapshot_id !== null && (
                  <div>
                    <p className="text-sm text-charcoal-brown">Snapshot ID</p>
                    <p className="font-mono text-carbon-black">{rewindResult.snapshot_id}</p>
                  </div>
                )}

                {rewindResult.restored_at && (
                  <div>
                    <p className="text-sm text-charcoal-brown">Restored At</p>
                    <p className="text-carbon-black">
                      {new Date(rewindResult.restored_at).toLocaleString()}
                    </p>
                  </div>
                )}

                {rewindResult.system_prompt && (
                  <div>
                    <p className="text-sm text-charcoal-brown mb-1">System Prompt</p>
                    <div className="bg-floral-white rounded p-3 max-h-40 overflow-auto">
                      <p className="text-sm text-carbon-black font-mono whitespace-pre-wrap">
                        {rewindResult.system_prompt}
                      </p>
                    </div>
                  </div>
                )}

                {rewindResult.context && Object.keys(rewindResult.context).length > 0 && (
                  <div>
                    <p className="text-sm text-charcoal-brown mb-1">Context</p>
                    <div className="bg-floral-white rounded p-3 max-h-40 overflow-auto">
                      <pre className="text-xs text-carbon-black">
                        {JSON.stringify(rewindResult.context, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-subtle p-6 flex justify-end gap-3">
          {!rewindResult && (
            <>
              <button
                onClick={handleClose}
                disabled={isRewinding}
                className="btn-secondary px-6 py-2 rounded font-medium disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmRewind}
                disabled={isRewinding}
                className="btn-primary px-6 py-2 rounded font-medium disabled:opacity-50 flex items-center gap-2"
              >
                {isRewinding && (
                  <div className="animate-spin h-4 w-4 border-2 border-floral-white border-t-transparent rounded-full" />
                )}
                {isRewinding ? 'Rewinding...' : 'Confirm Rewind'}
              </button>
            </>
          )}
          {rewindResult && (
            <button
              onClick={handleClose}
              className="btn-primary px-6 py-2 rounded font-medium"
            >
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
