import React, { useState } from 'react';
import { PatternSelector } from './PatternSelector';
import type { IntegrationPattern } from './PatternSelector';
import { LanguageSelector } from './LanguageSelector';
import type { ProgrammingLanguage } from './LanguageSelector';
import { CodeGenerator } from './CodeGenerator';
import { TestWorkspace } from './TestWorkspace';
import { useAuth } from '@hooks/useAuth';

export const IntegrationWizard: React.FC = () => {
  const { user } = useAuth();
  const [pattern, setPattern] = useState<IntegrationPattern>('sync');
  const [language, setLanguage] = useState<ProgrammingLanguage>('python');

  return (
    <div className="space-y-6 p-8">
      <div>
        <h2 className="text-2xl font-bold text-carbon-black mb-2">Integration Wizard</h2>
        <p className="text-sm text-charcoal-brown">
          Generate code snippets and test API endpoints. Choose your integration pattern and
          programming language to get started.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PatternSelector selected={pattern} onChange={setPattern} />
        <LanguageSelector selected={language} onChange={setLanguage} />
      </div>

      <CodeGenerator
        pattern={pattern}
        language={language}
        apiKey={user?.tenant_id ? `oriphim_${user.tenant_id}_${Date.now()}` : undefined}
      />

      <TestWorkspace />

      <div className="card bg-floral-white border-2 border-charcoal-brown/20">
        <h3 className="text-lg font-bold text-carbon-black mb-2">Integration Checklist</h3>
        <ul className="space-y-2 text-sm text-charcoal-brown">
          <li className="flex items-start gap-2">
            <span className="text-blood-red font-bold mt-1">1.</span>
            <span>
              <strong>Generate API Key:</strong> Navigate to Onboarding Console to create a new API
              key with appropriate scope.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blood-red font-bold mt-1">2.</span>
            <span>
              <strong>Copy Code:</strong> Use the generated code snippet above and replace
              placeholder API key with your actual key.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blood-red font-bold mt-1">3.</span>
            <span>
              <strong>Test Locally:</strong> Use the API Test Workspace above to verify endpoints
              before deploying to production.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blood-red font-bold mt-1">4.</span>
            <span>
              <strong>Monitor:</strong> Check Status Dashboard for validation metrics and Incident
              Panel for blocked requests.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blood-red font-bold mt-1">5.</span>
            <span>
              <strong>Audit:</strong> Review Audit Log for compliance and regulatory reporting.
            </span>
          </li>
        </ul>
      </div>
    </div>
  );
};
