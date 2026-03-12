import React, { useState } from 'react';
import APIClient from '@/lib/services/api';

interface TenantFormData {
  org_name: string;
  domain: string;
  support_tier: string;
}

export const TenantSetupForm: React.FC = () => {
  const [formData, setFormData] = useState<TenantFormData>({
    org_name: '',
    domain: '',
    support_tier: 'standard',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!formData.org_name.trim()) {
      setError('Organization name is required');
      return;
    }

    if (!formData.domain.trim()) {
      setError('Domain is required');
      return;
    }

    const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$/;
    if (!domainRegex.test(formData.domain)) {
      setError('Invalid domain format (e.g., example.com)');
      return;
    }

    setIsSubmitting(true);

    try {
      const client = new APIClient();
      const response = await client.createTenant(
        formData.org_name,
        formData.domain,
        formData.support_tier
      );

      setSuccess(`Tenant created successfully! Tenant ID: ${response.data.tenant_id}`);
      setFormData({ org_name: '', domain: '', support_tier: 'standard' });
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Failed to create tenant. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof TenantFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="card">
      <h3 className="text-xl font-bold text-carbon-black mb-4">Create New Tenant</h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="org-name" className="block text-sm font-medium text-charcoal-brown mb-2">
            Organization Name *
          </label>
          <input
            id="org-name"
            type="text"
            value={formData.org_name}
            onChange={(e) => handleChange('org_name', e.target.value)}
            className="w-full border border-subtle rounded px-3 py-2 text-carbon-black focus:outline-none focus:ring-2 focus:ring-charcoal-brown"
            placeholder="Acme Corporation"
            required
            disabled={isSubmitting}
          />
        </div>

        <div>
          <label htmlFor="domain" className="block text-sm font-medium text-charcoal-brown mb-2">
            Domain *
          </label>
          <input
            id="domain"
            type="text"
            value={formData.domain}
            onChange={(e) => handleChange('domain', e.target.value)}
            className="w-full border border-subtle rounded px-3 py-2 text-carbon-black focus:outline-none focus:ring-2 focus:ring-charcoal-brown"
            placeholder="acme.com"
            required
            disabled={isSubmitting}
          />
        </div>

        <div>
          <label htmlFor="support-tier" className="block text-sm font-medium text-charcoal-brown mb-2">
            Support Tier *
          </label>
          <select
            id="support-tier"
            value={formData.support_tier}
            onChange={(e) => handleChange('support_tier', e.target.value)}
            className="w-full border border-subtle rounded px-3 py-2 text-carbon-black focus:outline-none focus:ring-2 focus:ring-charcoal-brown"
            disabled={isSubmitting}
          >
            <option value="standard">Standard</option>
            <option value="premium">Premium</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>

        {error && (
          <div className="bg-red-50 border border-blood-red rounded p-3">
            <p className="text-sm text-blood-red">{error}</p>
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-500 rounded p-3">
            <p className="text-sm text-green-700">{success}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="btn-primary px-6 py-2 rounded font-medium disabled:opacity-50 flex items-center gap-2"
        >
          {isSubmitting && (
            <div className="animate-spin h-4 w-4 border-2 border-floral-white border-t-transparent rounded-full" />
          )}
          {isSubmitting ? 'Creating...' : 'Create Tenant'}
        </button>
      </form>
    </div>
  );
};
