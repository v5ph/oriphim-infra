import React, { useState } from 'react';
import { KeyGenerationModal } from './KeyGenerationModal';

interface APIKey {
  key_id: string;
  scope: string;
  created_at: string;
  expires_at: string;
  last_used?: string;
}

export const APIKeyManager: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleKeyGenerated = (apiKey: string) => {
    const newKey: APIKey = {
      key_id: apiKey.substring(0, 16) + '...',
      scope: 'read:validations',
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),
    };

    setApiKeys((prev) => [newKey, ...prev]);
  };

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-bold text-carbon-black">API Key Management</h3>
        <button
          onClick={() => setIsModalOpen(true)}
          className="btn-primary px-4 py-2 rounded font-medium"
        >
          + Generate New Key
        </button>
      </div>

      {apiKeys.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-subtle">
                <th className="text-left py-3 px-4 text-sm font-medium text-charcoal-brown">Key ID</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-charcoal-brown">Scope</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-charcoal-brown">Created</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-charcoal-brown">Expires</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-charcoal-brown">Last Used</th>
              </tr>
            </thead>
            <tbody>
              {apiKeys.map((key, idx) => (
                <tr key={idx} className="border-b border-subtle hover:bg-floral-white">
                  <td className="py-3 px-4 font-mono text-xs text-charcoal-brown">{key.key_id}</td>
                  <td className="py-3 px-4">
                    <span className="badge-allow text-xs">{key.scope}</span>
                  </td>
                  <td className="py-3 px-4 text-sm text-charcoal-brown">
                    {new Date(key.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4 text-sm text-charcoal-brown">
                    {new Date(key.expires_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4 text-sm text-charcoal-brown">
                    {key.last_used ? new Date(key.last_used).toLocaleDateString() : 'Never'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 text-charcoal-brown">
          No API keys generated yet. Click "Generate New Key" to create one.
        </div>
      )}

      <KeyGenerationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onKeyGenerated={handleKeyGenerated}
      />
    </div>
  );
};
