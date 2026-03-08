import APIClient from './api';

const client = new APIClient();

export const createTenant = (orgName: string, domain: string, supportTier: string) =>
  client.createTenant(orgName, domain, supportTier);

export const createUser = (tenantId: string, email: string, role: string) =>
  client.createUser(tenantId, email, role);

export const generateAPIKey = (tenantId: string, scope: string, expiresInDays: number) =>
  client.generateAPIKey(tenantId, scope, expiresInDays);
