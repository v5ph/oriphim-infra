import React, { useState } from 'react';
import { useAuth } from '@hooks/useAuth';

export const LoginForm: React.FC = () => {
  const { login, isLoading, error, setError } = useAuth();
  const [apiKey, setApiKey] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!apiKey.trim()) {
      setError('API key is required');
      return;
    }

    try {
      await login(apiKey);
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-primary flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white border border-slate-200 rounded-lg p-8 shadow-lg">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-primary mb-2">Oriphim</h1>
            <p className="text-secondary">Validation Control Center</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="api-key" className="block text-sm font-medium text-secondary mb-2">
                API Key
              </label>
              <input
                id="api-key"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="input-field w-full px-4 py-3 font-mono text-sm"
                placeholder="Enter your API key"
                disabled={isLoading}
                autoComplete="off"
              />
            </div>

            {error && (
              <div className="alert-danger rounded-lg">
                <p className="text-sm text-danger-700">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary px-6 py-3 rounded-lg font-medium disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoading && (
                <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
              )}
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-secondary">
            <p>Need an API key?</p>
            <p className="mt-1">Contact your administrator or visit the onboarding console.</p>
          </div>
        </div>

        <div className="mt-4 text-center text-xs text-secondary">
          <p>Oriphim Validation Control Center v1.0</p>
          <p className="mt-1">Production-ready validation system</p>
        </div>
      </div>
    </div>
  );
};
