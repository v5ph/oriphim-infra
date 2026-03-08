import React from 'react';
import { DashboardLayout } from './DashboardLayout';
import { StatusDashboard } from '@components/Status';
import { RecentValidations } from '@components/Validations';
import { IncidentPanel } from '@components/Incidents';
import { AuditLogViewer } from '@components/Audit';
import { OnboardingConsole } from '@components/Onboarding';
import { IntegrationWizard } from '@components/Integration';

export const Dashboard: React.FC = () => {
  return (
    <DashboardLayout>
      <StatusDashboard />
      <RecentValidations />
      <IncidentPanel />
      <AuditLogViewer />
      <OnboardingConsole />
      <IntegrationWizard />
    </DashboardLayout>
  );
};
