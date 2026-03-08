import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '@/styles/globals.css';
import App from '@/App';
import { AuthProvider } from '@components/Auth';
import { AppErrorBoundary } from '@components/ErrorBoundary';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppErrorBoundary>
      <AuthProvider>
        <App />
      </AuthProvider>
    </AppErrorBoundary>
  </StrictMode>
);
