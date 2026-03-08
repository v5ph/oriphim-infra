import axios from 'axios';
import type { AxiosInstance } from 'axios';
import { env } from '@config/env';
import {
  AUTH_ENDPOINTS,
  TENANT_ENDPOINTS,
  VALIDATION_ENDPOINTS,
} from '@lib/constants/endpoints';
import { STORAGE_KEYS } from '@lib/constants/storage';
import { getStorageItem, removeStorageItem, setStorageItem } from '@lib/utils/storage';

const API_BASE_URL = env.apiBaseUrl;

export class APIClient {
  private client: AxiosInstance;

  constructor(accessToken?: string) {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: env.apiTimeoutMs,
      headers: {
        'Content-Type': 'application/json',
        ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
      },
    });

    this.client.interceptors.request.use((config) => {
      const token = getStorageItem(STORAGE_KEYS.accessToken);
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          const refreshToken = getStorageItem(STORAGE_KEYS.refreshToken);
          if (refreshToken) {
            try {
              const response = await axios.post(`${API_BASE_URL}${AUTH_ENDPOINTS.refresh}`, {
                refresh_token: refreshToken,
              });
              setStorageItem(STORAGE_KEYS.accessToken, response.data.access_token);
              return this.client(error.config);
            } catch {
              removeStorageItem(STORAGE_KEYS.accessToken);
              removeStorageItem(STORAGE_KEYS.refreshToken);
              window.location.href = '/login';
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  async getHealth() {
    return this.client.get(VALIDATION_ENDPOINTS.health);
  }

  async getValidationStatus(requestId: string) {
    return this.client.get(VALIDATION_ENDPOINTS.validationStatus(requestId));
  }

  async rewindAgent(agentId: string) {
    return this.client.post(VALIDATION_ENDPOINTS.rewindAgent(agentId));
  }

  async getAuditLog(tenantId: string, daysBack: number = 90) {
    return this.client.get(TENANT_ENDPOINTS.auditLog(tenantId), {
      params: { days_back: daysBack },
    });
  }

  async verifyAuditChain(tenantId: string) {
    return this.client.get(TENANT_ENDPOINTS.verifyAuditLog(tenantId));
  }

  async login(apiKey: string) {
    return axios.post(`${API_BASE_URL}${AUTH_ENDPOINTS.login}`, {
      api_key: apiKey,
      user_agent: navigator.userAgent,
      ip_address: await this.getClientIP(),
    });
  }

  async logout() {
    return this.client.post(AUTH_ENDPOINTS.logout);
  }

  async verifyToken() {
    return this.client.get(AUTH_ENDPOINTS.verify);
  }

  async createTenant(orgName: string, domain: string, supportTier: string) {
    return this.client.post(TENANT_ENDPOINTS.createTenant, {
      org_name: orgName,
      domain,
      support_tier: supportTier,
    });
  }

  async createUser(tenantId: string, email: string, role: string) {
    return this.client.post(TENANT_ENDPOINTS.createUser(tenantId), {
      email,
      role,
    });
  }

  async generateAPIKey(tenantId: string, scope: string, expiresInDays: number = 90) {
    return this.client.post(TENANT_ENDPOINTS.createApiKey(tenantId), {
      scope,
      expires_in_days: expiresInDays,
    });
  }

  private async getClientIP(): Promise<string> {
    try {
      const response = await axios.get('https://api.ipify.org?format=json');
      return response.data.ip;
    } catch {
      return 'unknown';
    }
  }
}

export default APIClient;
