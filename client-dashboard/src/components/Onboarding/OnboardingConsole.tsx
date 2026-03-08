import React from 'react';
import { TenantSetupForm } from './TenantSetupForm';
import { UserManagementTable } from './UserManagementTable';
import { APIKeyManager } from './APIKeyManager';

export const OnboardingConsole: React.FC = () => {
  return (
    <div className="space-y-6 p-8">
      <div>
        <h2 className="text-2xl font-bold text-carbon-black mb-2">Onboarding Console</h2>
        <p className="text-sm text-charcoal-brown">
          Configure tenants, manage users, and generate API keys for integration.
        </p>
      </div>

      <TenantSetupForm />
      <UserManagementTable />
      <APIKeyManager />
    </div>
  );
};
