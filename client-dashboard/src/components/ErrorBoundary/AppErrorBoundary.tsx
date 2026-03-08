import React from 'react';

interface AppErrorBoundaryProps {
  children: React.ReactNode;
}

interface AppErrorBoundaryState {
  hasError: boolean;
}

export class AppErrorBoundary extends React.Component<
  AppErrorBoundaryProps,
  AppErrorBoundaryState
> {
  public constructor(props: AppErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  public static getDerivedStateFromError(): AppErrorBoundaryState {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('Unhandled UI error:', error, errorInfo);
  }

  public render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-floral-white flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-white border border-charcoal-brown/20 rounded-lg p-6 text-center">
            <h1 className="text-xl font-semibold text-blood-red mb-2">Unexpected error</h1>
            <p className="text-charcoal-brown mb-4">
              The dashboard encountered an unexpected issue. Reload the page to continue.
            </p>
            <button
              type="button"
              className="btn-primary px-4 py-2 rounded"
              onClick={() => window.location.reload()}
            >
              Reload Dashboard
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
