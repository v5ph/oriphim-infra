import React, { useState } from 'react';
import APIClient from '@services/api';

interface TestRequest {
  endpoint: string;
  method: string;
  body: string;
}

export const TestWorkspace: React.FC = () => {
  const [request, setRequest] = useState<TestRequest>({
    endpoint: '/v2/health',
    method: 'GET',
    body: '',
  });
  const [response, setResponse] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const endpoints = [
    { value: '/v2/health', label: 'GET /v2/health - System health' },
    { value: '/v3/intent', label: 'POST /v3/intent - Validate intent' },
    { value: '/v3/rewind/{agent_id}', label: 'POST /v3/rewind/{agent_id} - Rewind agent' },
  ];

  const handleTest = async () => {
    setIsLoading(true);
    setError(null);
    setResponse('');

    try {
      const client = new APIClient();
      let result;

      const endpoint = request.endpoint.replace('{agent_id}', 'test-agent-123');

      if (request.method === 'GET') {
        if (endpoint === '/v2/health') {
          result = await client.getHealth();
        } else {
          throw new Error('Unsupported GET endpoint');
        }
      } else if (request.method === 'POST') {
        if (endpoint.startsWith('/v3/intent')) {
          result = { data: { message: 'Intent validation submitted', request_id: 'demo-123' } };
        } else if (endpoint.startsWith('/v3/rewind/')) {
          const agentId = endpoint.split('/').pop() || 'test-agent-123';
          result = await client.rewindAgent(agentId);
        } else {
          throw new Error('Unsupported POST endpoint');
        }
      } else {
        throw new Error('Unsupported HTTP method');
      }

      setResponse(JSON.stringify(result.data, null, 2));
    } catch (err: any) {
      if (err instanceof SyntaxError) {
        setError('Invalid JSON in request body');
      } else {
        setError(
          err.response?.data?.detail ||
          err.message ||
          'Request failed. Check your input and try again.'
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <h3 className="text-lg font-bold text-carbon-black mb-4">API Test Workspace</h3>

      <div className="space-y-4">
        <div>
          <label htmlFor="test-endpoint" className="block text-sm font-medium text-charcoal-brown mb-2">
            Endpoint
          </label>
          <select
            id="test-endpoint"
            value={request.endpoint}
            onChange={(e) => {
              const newEndpoint = e.target.value;
              const newMethod = newEndpoint === '/v2/health' ? 'GET' : 'POST';
              setRequest((prev) => ({ ...prev, endpoint: newEndpoint, method: newMethod }));
              setResponse('');
              setError(null);
            }}
            className="w-full border border-subtle rounded px-3 py-2 text-carbon-black font-mono text-sm"
          >
            {endpoints.map((ep) => (
              <option key={ep.value} value={ep.value}>
                {ep.label}
              </option>
            ))}
          </select>
        </div>

        {request.method === 'POST' && (
          <div>
            <label htmlFor="test-body" className="block text-sm font-medium text-charcoal-brown mb-2">
              Request Body (JSON)
            </label>
            <textarea
              id="test-body"
              value={request.body}
              onChange={(e) => setRequest((prev) => ({ ...prev, body: e.target.value }))}
              className="w-full border border-subtle rounded px-3 py-2 text-carbon-black font-mono text-sm h-32"
              placeholder={`{
  "agent_id": "agent-123",
  "user_prompt": "Transfer $1000",
  "context": {},
  "variables": {}
}`}
            />
          </div>
        )}

        <button
          onClick={handleTest}
          disabled={isLoading}
          className="btn-primary px-6 py-2 rounded font-medium disabled:opacity-50 flex items-center gap-2"
        >
          {isLoading && (
            <div className="animate-spin h-4 w-4 border-2 border-floral-white border-t-transparent rounded-full" />
          )}
          {isLoading ? 'Sending...' : 'Send Request'}
        </button>

        {error && (
          <div className="bg-red-50 border border-blood-red rounded p-4">
            <p className="text-sm font-medium text-blood-red mb-1">Error</p>
            <p className="text-sm text-charcoal-brown">{error}</p>
          </div>
        )}

        {response && (
          <div>
            <p className="text-sm font-medium text-charcoal-brown mb-2">Response</p>
            <div className="bg-carbon-black rounded-lg p-4 overflow-x-auto">
              <pre className="text-sm text-floral-white font-mono">
                <code>{response}</code>
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
