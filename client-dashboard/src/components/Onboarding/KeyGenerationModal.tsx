import React, { useState } from 'react';
import APIClient from '@services/api';
import { useAuth } from '@hooks/useAuth';

interface KeyGenerationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onKeyGenerated: (apiKey: string) => void;
}

interface KeyFormData {
  scope: string;
  expiresInDays: number;
}

export const KeyGenerationModal: React.FC<KeyGenerationModalProps> = ({
  isOpen,
  onClose,
  onKeyGenerated,
}) => {
  const { user: authUser } = useAuth();
  const [formData, setFormData] = useState<KeyFormData>({
    scope: 'read:validations',
    expiresInDays: 90,
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    if (!authUser?.tenant_id) {
      setError('No tenant ID found. Please log in.');
      return;
    }

    setError(null);
    setIsGenerating(true);

    try {
      const client = new APIClient();
      const response = await client.generateAPIKey(
        authUser.tenant_id,
        formData.scope,
        formData.expiresInDays
      );

      const apiKey = response.data.api_key;
      setGeneratedKey(apiKey);
      onKeyGenerated(apiKey);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Failed to generate API key. Please try again.'
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = async () => {
    if (!generatedKey) return;

    try {
      await navigator.clipboard.writeText(generatedKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      setError('Failed to copy to clipboard');
    }
  };

  const handleClose = () => {
    setGeneratedKey(null);
    setError(null);
    setCopied(false);
    setFormData({ scope: 'read:validations', expiresInDays: 90 });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-carbon-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-floral-white rounded-lg max-w-lg w-full p-6 space-y-4">
        <div className="flex justify-between items-start">
          <h3 className="text-xl font-bold text-carbon-black">Generate API Key</h3>
          <button
            onClick={handleClose}
            className="text-charcoal-brown hover:text-carbon-black text-2xl leading-none"
          >
            &times;
          </button>
        </div>

        {!generatedKey ? (
          <>
            <div className="space-y-4">
              <div>
                <label htmlFor="key-scope" className="block text-sm font-medium text-charcoal-brown mb-2">
                  Scope *
                </label>
                <select
                  id="key-scope"
                  value={formData.scope}
                  onChange={(e) => setFormData((prev) => ({ ...prev, scope: e.target.value }))}
                  className="w-full border border-subtle rounded px-3 py-2 text-carbon-black focus:outline-none focus:ring-2 focus:ring-charcoal-brown"
                  disabled={isGenerating}
                >
                  <option value="read:validations">Read Validations</option>
                  <option value="write:validations">Write Validations</option>
                  <option value="read:audit">Read Audit Log</option>
                  <option value="admin">Admin (Full Access)</option>
                </select>
              </div>

              <div>
                <label htmlFor="key-expiry" className="block text-sm font-medium text-charcoal-brown mb-2">
                  Expiration (days) *
                </label>
                <input
                  id="key-expiry"
                  type="number"
                  value={formData.expiresInDays}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, expiresInDays: parseInt(e.target.value, 10) }))
                  }
                  min={1}
                  max={365}
                  className="w-full border border-subtle rounded px-3 py-2 text-carbon-black focus:outline-none focus:ring-2 focus:ring-charcoal-brown"
                  disabled={isGenerating}
                />
                <p className="text-xs text-charcoal-brown mt-1">Min: 1 day, Max: 365 days</p>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-blood-red rounded p-3">
                <p className="text-sm text-blood-red">{error}</p>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="btn-primary px-6 py-2 rounded font-medium disabled:opacity-50 flex items-center gap-2"
              >
                {isGenerating && (
                  <div className="animate-spin h-4 w-4 border-2 border-floral-white border-t-transparent rounded-full" />
                )}
                {isGenerating ? 'Generating...' : 'Generate Key'}
              </button>
              <button onClick={handleClose} className="btn-secondary px-6 py-2 rounded font-medium">
                Cancel
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-500 rounded p-4">
                <p className="text-sm text-green-700 mb-2 font-medium">
                  API Key Generated Successfully!
                </p>
                <p className="text-xs text-charcoal-brown mb-3">
                  Copy this key now. For security reasons, it will not be shown again.
                </p>
                <div className="bg-white border border-subtle rounded p-3 font-mono text-sm break-all">
                  {generatedKey}
                </div>
              </div>

              <button
                onClick={handleCopy}
                className="btn-primary px-6 py-2 rounded font-medium w-full"
              >
                {copied ? 'Copied!' : 'Copy to Clipboard'}
              </button>
            </div>

            <button onClick={handleClose} className="btn-secondary px-6 py-2 rounded font-medium w-full">
              Close
            </button>
          </>
        )}
      </div>
    </div>
  );
};
