import React, { useEffect, useState } from 'react';
import { Dashboard } from '@components/Dashboard';
import { LoginForm } from '@components/Auth';
import { useAuth } from '@hooks/useAuth';

const App: React.FC = () => {
  const { user, restoreSession } = useAuth();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const init = async () => {
      try {
        await Promise.race([
          restoreSession(),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Session restore timeout')), 3000)
          ),
        ]);
      } catch (error) {
        console.warn('Session restore failed:', error);
      } finally {
        setIsLoading(false);
      }
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-primary flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-brand-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-secondary">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginForm />;
  }

  return <Dashboard />;
};

export default App;
