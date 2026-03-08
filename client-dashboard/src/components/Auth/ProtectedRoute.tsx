import React from 'react';
import { useAuth } from '@hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { accessToken } = useAuth();

  if (!accessToken) {
    return <div className="p-8 text-center">Authentication required.</div>;
  }

  return <>{children}</>;
};
