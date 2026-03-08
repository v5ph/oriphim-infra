import React from 'react';
import { Navigation } from './Navigation';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-primary">
      <Navigation />
      {children}
    </div>
  );
};
