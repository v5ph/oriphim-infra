import React from 'react';

export const BackendUnavailable: React.FC = () => {
  const handleRetry = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-primary flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-lg shadow-lg p-8 border border-slate-200">
          <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 rounded-full bg-danger-100">
            <svg
              className="w-8 h-8 text-danger-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>

          <h1 className="text-2xl font-bold text-center text-primary mb-2">
            Backend Unavailable
          </h1>

          <p className="text-center text-secondary mb-6">
            Unable to connect to the API server at{' '}
            <code className="code-inline">localhost:8000</code>
          </p>

          <div className="bg-slate-50 rounded-md p-4 mb-6">
            <p className="text-sm text-slate-700 font-semibold mb-2">
              To start the backend:
            </p>
            <pre className="text-xs bg-slate-900 text-slate-50 rounded p-3 overflow-x-auto font-mono">
              cd oriphim-infra{'\n'}
              docker-compose up -d{'\n'}
              # or{'\n'}
              make run
            </pre>
          </div>

          <button
            onClick={handleRetry}
            className="btn-primary w-full py-3 rounded-lg"
          >
            Retry Connection
          </button>

          <p className="text-xs text-center text-slate-500 mt-4">
            Ensure the API is running and accessible at the configured endpoint
          </p>
        </div>
      </div>
    </div>
  );
};
