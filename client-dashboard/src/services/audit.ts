import APIClient from './api';

const client = new APIClient();

export const getAuditLog = (tenantId: string, daysBack: number) => client.getAuditLog(tenantId, daysBack);
export const verifyAuditChain = (tenantId: string) => client.verifyAuditChain(tenantId);
