import React, { useEffect, useState } from 'react';
import type { AuditLogResponse } from '@/types';
import APIClient from '@/lib/services/api';
import { useAuth } from '@hooks/useAuth';
import { AuditEventList } from './AuditEventList';
import { ChainVerificationBadge } from './ChainVerificationBadge';

export const AuditLogViewer: React.FC = () => {
  const { user } = useAuth();
  const [auditLog, setAuditLog] = useState<AuditLogResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [daysBack, setDaysBack] = useState(30);
  const [isVerifying, setIsVerifying] = useState(false);
  const [chainVerified, setChainVerified] = useState<boolean | null>(null);

  useEffect(() => {
    if (!user?.tenant_id) return;

    const fetchAuditLog = async () => {
      setLoading(true);
      setError(null);

      try {
        const client = new APIClient();
        const response = await client.getAuditLog(user.tenant_id, daysBack);
        setAuditLog(response.data);
        setChainVerified(response.data.chain_verified);
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to load audit log');
      } finally {
        setLoading(false);
      }
    };

    fetchAuditLog();
  }, [user?.tenant_id, daysBack]);

  const handleVerifyChain = async () => {
    if (!user?.tenant_id) return;

    setIsVerifying(true);
    try {
      const client = new APIClient();
      const response = await client.verifyAuditChain(user.tenant_id);
      setChainVerified(response.data.chain_verified);
    } catch (err: any) {
      console.error('Chain verification failed:', err);
      setChainVerified(false);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleExportCSV = () => {
    if (!auditLog) return;

    const headers = [
      'Audit ID',
      'Request ID',
      'Agent ID',
      'Event Type',
      'Message',
      'Violations',
      'Regulatory Articles',
      'Created At',
      'Chain Hash',
      'Prev Hash',
    ];

    const rows = auditLog.events.map((event) => [
      event.audit_id,
      event.request_id,
      event.agent_id || '',
      event.event_type,
      event.message.replace(/"/g, '""'),
      event.violations.join('; '),
      event.regulatory_articles.join('; '),
      event.created_at,
      event.chain_hash,
      event.prev_hash,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `audit-log-${user?.tenant_id}-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  const handleExportPDF = () => {
    if (!auditLog) return;

    const printWindow = window.open('', '', 'width=800,height=600');
    if (!printWindow) return;

    const htmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Audit Log - ${user?.tenant_id}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #1E1E1D; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #E5E5E5; padding: 8px; text-align: left; font-size: 12px; }
            th { background-color: #F9F6EE; }
            .header { margin-bottom: 20px; }
            .status { color: ${chainVerified ? '#22C55E' : '#8B0000'}; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Audit Log Report</h1>
            <p><strong>Tenant ID:</strong> ${auditLog.tenant_id}</p>
            <p><strong>Event Count:</strong> ${auditLog.event_count}</p>
            <p><strong>Chain Status:</strong> <span class="status">${chainVerified ? 'Verified' : 'Broken'}</span></p>
            <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
          </div>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Event Type</th>
                <th>Message</th>
                <th>Violations</th>
                <th>Created At</th>
              </tr>
            </thead>
            <tbody>
              ${auditLog.events
                .map(
                  (event) => `
                <tr>
                  <td>${event.audit_id}</td>
                  <td>${event.event_type}</td>
                  <td>${event.message}</td>
                  <td>${event.violations.join(', ')}</td>
                  <td>${new Date(event.created_at).toLocaleString()}</td>
                </tr>
              `
                )
                .join('')}
            </tbody>
          </table>
        </body>
      </html>
    `;

    printWindow.document.write(htmlContent);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 250);
  };

  if (!user?.tenant_id) {
    return (
      <div className="p-8 text-center text-charcoal-brown">
        Please log in to view audit logs.
      </div>
    );
  }

  return (
    <div className="space-y-6 p-8">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-carbon-black">Audit Log</h2>
          <p className="text-sm text-charcoal-brown mt-1">
            Tenant: {user.tenant_id}
          </p>
        </div>
        {chainVerified !== null && (
          <ChainVerificationBadge
            verified={chainVerified}
            isLoading={isVerifying}
            onVerify={handleVerifyChain}
          />
        )}
      </div>

      <div className="card">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label htmlFor="date-range-select" className="block text-sm text-charcoal-brown mb-2">
              Date Range (days back)
            </label>
            <select
              id="date-range-select"
              value={daysBack}
              onChange={(e) => setDaysBack(Number(e.target.value))}
              className="w-full border border-subtle rounded px-3 py-2 text-carbon-black"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
              <option value={180}>Last 6 months</option>
              <option value={365}>Last year</option>
            </select>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleExportCSV}
              disabled={!auditLog || auditLog.events.length === 0}
              className="btn-secondary px-4 py-2 rounded font-medium disabled:opacity-50"
            >
              Export CSV
            </button>
            <button
              onClick={handleExportPDF}
              disabled={!auditLog || auditLog.events.length === 0}
              className="btn-secondary px-4 py-2 rounded font-medium disabled:opacity-50"
            >
              Export PDF
            </button>
          </div>
        </div>

        {auditLog && (
          <div className="mt-4 text-sm text-charcoal-brown">
            Showing {auditLog.event_count} event{auditLog.event_count !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin h-8 w-8 border-4 border-charcoal-brown border-t-transparent rounded-full" />
          <p className="mt-2 text-charcoal-brown">Loading audit log...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-blood-red rounded p-4">
          <p className="text-sm font-medium text-blood-red mb-1">Error</p>
          <p className="text-sm text-charcoal-brown">{error}</p>
        </div>
      )}

      {auditLog && !loading && (
        <div className="card">
          <AuditEventList events={auditLog.events} />
        </div>
      )}
    </div>
  );
};
