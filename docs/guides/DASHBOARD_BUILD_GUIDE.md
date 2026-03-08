# ORIPHIM DASHBOARD BUILD GUIDE
## Validation Control Center (Option A)

**Version:** 1.0  
**Date:** March 4, 2026  
**Estimated Build Time:** 7-10 days (full implementation)  
**Tech Stack:** React 18, TypeScript, Tailwind CSS, Vite  
**Target Users:** CTOs, Chief Risk Officers, Operations Teams

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Setup](#project-setup)
4. [Color Palette Configuration](#color-palette-configuration)
5. [Directory Structure](#directory-structure)
6. [Component Development](#component-development)
7. [Implementation Checklist](#implementation-checklist)
8. [Testing & Deployment](#testing--deployment)

---

## OVERVIEW

The Validation Control Center is a **lightweight, signal-focused web dashboard** that provides real-time visibility into Oriphim's validation system. It prioritizes:

- **Risk visibility**: See blocks (424s), violations, and drift instantly
- **Decision speed**: Traffic-light status + core metrics in 2 seconds
- **Traceability**: Click to drill-down into validation evidence
- **Compliance**: Immutable audit logs with hash chain verification
- **Operational simplicity**: No unnecessary UI, clear action buttons

### Design Principles

1. **Clarity over aesthetics** - Information hierarchy matters more than visual polish
2. **Signal over noise** - Every element must communicate risk or decision-critical data
3. **Speed over features** - CRO should understand system status in <3 seconds
4. **Traceable decisions** - Every block/allow decision links to evidence
5. **Accessible compliance** - Audit logs and exports for regulatory review

---

## ARCHITECTURE

### High-Level Flow

```
┌─ Browser (React SPA) ────────────────────────────────────────┐
│                                                                │
│  ┌─ Auth Layer ──────────┐                                   │
│  │ Login with API key →  │                                   │
│  │ Exchange for JWT      │                                   │
│  │ (via /auth/login)     │                                   │
│  └───────────┬───────────┘                                   │
│              │                                                │
│  ┌───────────▼─────────────────────────────────────┐         │
│  │ Dashboard (Protected Routes)                    │         │
│  │                                                 │         │
│  │ ┌─ Navigation ──────────────────────────────┐  │         │
│  │ │ [Status] [Validations] [Incidents]        │  │         │
│  │ │ [Audit] [Setup] [Integrations]            │  │         │
│  │ └───────────────────────────────────────────┘  │         │
│  │                                                 │         │
│  │ ┌─ Active Page (State) ─────────────────────┐  │         │
│  │ │ Real-time updates via polling/WebSocket   │  │         │
│  │ └───────────┬─────────────────────────────┘   │         │
│  └─────────────┼──────────────────────────────────┘         │
│                │                                              │
│                └─► FastAPI Backend                           │
│                    │                                          │
│                    ├─ /v2/health (poll every 2s)            │
│                    ├─ /v3/intent/{id} (validation results)  │
│                    ├─ /v1/onboarding/audit-log              │
│                    ├─ /v3/rewind/{agent_id}                 │
│                    └─ /v1/onboarding/auth/* (JWT mgmt)      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Component Tree

```
App
├── useAuth (JWT context)
├── AuthGuard
│   └── Dashboard
│       ├── Navigation
│       ├── StatusDashboard
│       │   ├── TrafficLightIndicator
│       │   ├── MetricsGrid
│       │   └── HistoricalChart
│       ├── RecentValidations
│       │   ├── ValidationTable
│       │   ├── ValidationRow (expandable)
│       │   └── ValidationDetailModal
│       ├── IncidentPanel
│       │   ├── BlockedAgentList
│       │   └── RewindModal
│       ├── AuditLogViewer
│       │   ├── AuditEventList
│       │   ├── ChainVerificationBadge
│       │   └── EventDetailCollapsible
│       ├── OnboardingConsole
│       │   ├── TenantSetupForm
│       │   ├── UserManagementTable
│       │   ├── APIKeyManager
│       │   └── KeyGenerationModal
│       └── IntegrationWizard
│           ├── PatternSelector
│           ├── LanguageSelector
│           ├── CodeGenerator
│           └── TestWorkspace
```

---

## PROJECT SETUP

### Step 1: Initialize React + TypeScript Project

```bash
# Create new Vite project in dashboard subdirectory
cd /path/to/oriphim-infra
mkdir -p client-dashboard
cd client-dashboard

# Initialize with Vite template (React + TypeScript)
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install

# Install additional libraries
npm install -D tailwindcss postcss autoprefixer
npm install axios zustand js-cookie
npm install lucide-react @radix-ui/react-dialog
npm install recharts  # For historical charts

# Initialize Tailwind
npx tailwindcss init -p
```

### Step 2: Create Environment Configuration

Create `.env.example`:
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_POLLING_INTERVAL_MS=2000
VITE_HEALTH_CHECK_INTERVAL_MS=2000
VITE_AUTH_TOKEN_STORAGE_KEY=oriphim_access_token
VITE_REFRESH_TOKEN_STORAGE_KEY=oriphim_refresh_token
```

Create `.env.local` (for development):
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_POLLING_INTERVAL_MS=2000
VITE_HEALTH_CHECK_INTERVAL_MS=2000
```

---

## COLOR PALETTE CONFIGURATION

### Step 3: Tailwind Configuration

Edit `tailwind.config.js`:

```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'floral-white': '#F9F6EE',
        'carbon-black': '#1E1E1D',
        'blood-red': '#8B0000',
        'deep-crimson': '#981515',
        'space-indigo': '#353956',
        'charcoal-brown': '#414535',
      },
      backgroundColor: {
        'primary': '#F9F6EE',
        'secondary': '#FFFFFF',
        'accent': '#8B0000',
        'danger-bg': '#FEE8E8',
      },
      textColor: {
        'primary': '#1E1E1D',
        'secondary': '#414535',
        'accent': '#8B0000',
      },
      borderColor: {
        'primary': '#414535',
        'subtle': '#E5E5E5',
      },
    },
  },
  plugins: [],
}
```

### Step 4: Global Styles

Create `src/styles/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --floral-white: #F9F6EE;
  --carbon-black: #1E1E1D;
  --blood-red: #8B0000;
  --deep-crimson: #981515;
  --space-indigo: #353956;
  --charcoal-brown: #414535;
}

html, body {
  background-color: var(--floral-white);
  color: var(--carbon-black);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

/* Traffic Light Indicators */
.status-green {
  @apply text-green-700 bg-green-50 border-green-200;
}

.status-yellow {
  @apply text-yellow-700 bg-yellow-50 border-yellow-200;
}

.status-red {
  @apply text-red-700 bg-red-50 border-red-200;
  background-color: #FEE8E8;
  border-color: #8B0000;
  color: #8B0000;
}

/* Action Buttons */
.btn-primary {
  @apply bg-blood-red hover:bg-deep-crimson text-floral-white;
}

.btn-secondary {
  @apply border border-charcoal-brown hover:bg-charcoal-brown/5;
}

/* Card Styling */
.card {
  @apply bg-white border border-charcoal-brown/10 rounded-lg p-6;
}

/* Status Badge */
.badge-allow {
  @apply bg-green-100 text-green-800 px-3 py-1 rounded text-sm;
}

.badge-review {
  @apply bg-yellow-100 text-yellow-800 px-3 py-1 rounded text-sm;
}

.badge-block {
  @apply bg-red-100 text-blood-red px-3 py-1 rounded text-sm;
  background-color: #FEE8E8;
}
```

---

## DIRECTORY STRUCTURE

### Step 5: Create Project Structure

```bash
client-dashboard/
├── src/
│   ├── components/
│   │   ├── Auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── AuthProvider.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── Dashboard/
│   │   │   ├── Navigation.tsx
│   │   │   ├── DashboardLayout.tsx
│   │   │   └── index.tsx
│   │   ├── Status/
│   │   │   ├── TrafficLightIndicator.tsx
│   │   │   ├── MetricsCard.tsx
│   │   │   ├── MetricsGrid.tsx
│   │   │   ├── HistoricalChart.tsx
│   │   │   └── StatusDashboard.tsx
│   │   ├── Validations/
│   │   │   ├── ValidationTable.tsx
│   │   │   ├── ValidationRow.tsx
│   │   │   ├── ValidationDetailModal.tsx
│   │   │   └── RecentValidations.tsx
│   │   ├── Incidents/
│   │   │   ├── IncidentList.tsx
│   │   │   ├── RewindModal.tsx
│   │   │   └── IncidentPanel.tsx
│   │   ├── Audit/
│   │   │   ├── AuditEventList.tsx
│   │   │   ├── AuditEventCollapsible.tsx
│   │   │   ├── ChainVerificationBadge.tsx
│   │   │   └── AuditLogViewer.tsx
│   │   ├── Onboarding/
│   │   │   ├── TenantSetupForm.tsx
│   │   │   ├── UserManagementTable.tsx
│   │   │   ├── APIKeyManager.tsx
│   │   │   ├── KeyGenerationModal.tsx
│   │   │   └── OnboardingConsole.tsx
│   │   ├── Integration/
│   │   │   ├── PatternSelector.tsx
│   │   │   ├── LanguageSelector.tsx
│   │   │   ├── CodeGenerator.tsx
│   │   │   ├── TestWorkspace.tsx
│   │   │   └── IntegrationWizard.tsx
│   │   └── Common/
│   │       ├── Button.tsx
│   │       ├── Modal.tsx
│   │       ├── Table.tsx
│   │       ├── Badge.tsx
│   │       └── LoadingSpinner.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useHealth.ts
│   │   ├── useValidations.ts
│   │   ├── useAuditLog.ts
│   │   └── useAPI.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   ├── health.ts
│   │   ├── validation.ts
│   │   ├── incident.ts
│   │   ├── audit.ts
│   │   └── onboarding.ts
│   ├── store/
│   │   ├── authStore.ts
│   │   ├── healthStore.ts
│   │   └── validationStore.ts
│   ├── types/
│   │   ├── health.ts
│   │   ├── validation.ts
│   │   ├── incident.ts
│   │   ├── audit.ts
│   │   └── auth.ts
│   ├── styles/
│   │   ├── globals.css
│   │   └── components.css
│   ├── App.tsx
│   └── main.tsx
├── public/
├── index.html
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── vite.config.ts
├── package.json
└── .env.example
```

---

## COMPONENT DEVELOPMENT

### Step 6: Core Types

Create `src/types/index.ts`:

```typescript
// Authentication
export interface LoginCredentials {
  api_key: string;
  user_agent?: string;
  ip_address?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthUser {
  user_id: string;
  tenant_id: string;
  scope: string;
  email?: string;
}

// Health Metrics
export type IndicatorStatus = 'GREEN' | 'YELLOW' | 'RED';

export interface HealthMetrics {
  uptime_requests: number;
  recent_divergence_avg: number;
  recent_violation_rate: number;
  drift_detected: boolean;
  last_critical_violation: string | null;
  status: 'HEALTHY' | 'DEGRADED' | 'CRITICAL';
  indicator: IndicatorStatus;
}

// Validation Results
export type ActionLabel = 'ALLOW' | 'REVIEW' | 'BLOCK' | 'CAUTION';

export interface ValidationMetrics {
  request_id: string | null;
  timestamp: string;
  status_code: number;
  divergence_score: number;
  violations: string[];
  confidence: {
    score: number;
    risk_level: string;
    explanation: string;
  };
  violation_severities: Array<{
    name: string;
    severity_pct: number;
    weight: number;
    impact_description: string;
  }>;
  overall_severity_score: number | null;
  drift: {
    detected: boolean;
    z_score: number;
    historical_mean: number;
    current_value: number;
    explanation: string;
  };
  indicator: IndicatorStatus;
  action_label: ActionLabel;
  action_reason: string;
  action: string;
  recommendation: string;
  context_reset?: boolean;
  latency_ms?: number;
}

// Audit Log
export interface AuditEvent {
  audit_id: number;
  request_id: string;
  agent_id: string | null;
  event_type: string;
  violations: string[];
  regulatory_articles: string[];
  message: string;
  prev_hash: string;
  chain_hash: string;
  created_at: string;
}

export interface AuditLogResponse {
  tenant_id: string;
  event_count: number;
  events: AuditEvent[];
  chain_verified: boolean;
}

// Incident / Rewind
export interface RewindResponse {
  agent_id: string;
  snapshot_id: number | null;
  restored: boolean;
  restored_at: string | null;
  system_prompt: string | null;
  context: Record<string, any> | null;
  variables: Record<string, any> | null;
}
```

### Step 7: API Service Layer

Create `src/services/api.ts`:

```typescript
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class APIClient {
  private client: AxiosInstance;

  constructor(accessToken?: string) {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
        ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
      },
    });

    // Auto-attach token to subsequent requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('oriphim_access_token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle token expiration
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          const refreshToken = localStorage.getItem('oriphim_refresh_token');
          if (refreshToken) {
            try {
              const response = await axios.post(`${API_BASE_URL}/v1/onboarding/auth/refresh`, {
                refresh_token: refreshToken,
              });
              localStorage.setItem('oriphim_access_token', response.data.access_token);
              return this.client(error.config);
            } catch (e) {
              localStorage.removeItem('oriphim_access_token');
              localStorage.removeItem('oriphim_refresh_token');
              window.location.href = '/login';
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Health endpoints
  async getHealth() {
    return this.client.get('/v2/health');
  }

  // Validation endpoints
  async getValidationStatus(requestId: string) {
    return this.client.get(`/v3/intent/${requestId}`);
  }

  // Incident endpoints
  async rewindAgent(agentId: string) {
    return this.client.post(`/v3/rewind/${agentId}`);
  }

  // Audit endpoints
  async getAuditLog(tenantId: string, daysBack: number = 90) {
    return this.client.get(`/v1/onboarding/tenants/${tenantId}/audit-log`, {
      params: { days_back: daysBack },
    });
  }

  async verifyAuditChain(tenantId: string) {
    return this.client.get(`/v1/onboarding/tenants/${tenantId}/audit-log/verify`);
  }

  // Auth endpoints
  async login(apiKey: string) {
    return axios.post(`${API_BASE_URL}/v1/onboarding/auth/login`, {
      api_key: apiKey,
      user_agent: navigator.userAgent,
      ip_address: await this.getClientIP(),
    });
  }

  async logout() {
    return this.client.post('/v1/onboarding/auth/logout');
  }

  async verifyToken() {
    return this.client.get('/v1/onboarding/auth/verify');
  }

  // Onboarding endpoints
  async createTenant(orgName: string, domain: string, supportTier: string) {
    return this.client.post('/v1/onboarding/tenants', {
      org_name: orgName,
      domain: domain,
      support_tier: supportTier,
    });
  }

  async createUser(tenantId: string, email: string, role: string) {
    return this.client.post(`/v1/onboarding/tenants/${tenantId}/users`, {
      email: email,
      role: role,
    });
  }

  async generateAPIKey(tenantId: string, scope: string, expiresInDays: number = 90) {
    return this.client.post(`/v1/onboarding/tenants/${tenantId}/api-keys`, {
      scope: scope,
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
```

### Step 8: Authentication Context

Create `src/hooks/useAuth.ts`:

```typescript
import { create } from 'zustand';
import APIClient from '../services/api';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: { user_id: string; tenant_id: string; scope: string } | null;
  isLoading: boolean;
  error: string | null;

  login: (apiKey: string) => Promise<void>;
  logout: () => Promise<void>;
  restoreSession: () => Promise<boolean>;
  setError: (error: string | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: localStorage.getItem('oriphim_access_token'),
  refreshToken: localStorage.getItem('oriphim_refresh_token'),
  user: null,
  isLoading: false,
  error: null,

  login: async (apiKey: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await APIClient.prototype.login(apiKey);
      const { access_token, refresh_token } = response.data;

      localStorage.setItem('oriphim_access_token', access_token);
      localStorage.setItem('oriphim_refresh_token', refresh_token);

      const client = new APIClient(access_token);
      const verified = await client.verifyToken();

      set({
        accessToken: access_token,
        refreshToken: refresh_token,
        user: verified.data,
        isLoading: false,
      });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Login failed',
        isLoading: false,
      });
      throw err;
    }
  },

  logout: async () => {
    try {
      const client = new APIClient();
      await client.logout();
    } catch (err) {
      console.error('Logout failed:', err);
    } finally {
      localStorage.removeItem('oriphim_access_token');
      localStorage.removeItem('oriphim_refresh_token');
      set({ accessToken: null, refreshToken: null, user: null });
    }
  },

  restoreSession: async () => {
    const token = localStorage.getItem('oriphim_access_token');
    if (!token) return false;

    try {
      const client = new APIClient(token);
      const verified = await client.verifyToken();
      set({ user: verified.data, accessToken: token });
      return true;
    } catch (err) {
      localStorage.removeItem('oriphim_access_token');
      localStorage.removeItem('oriphim_refresh_token');
      return false;
    }
  },

  setError: (error: string | null) => set({ error }),
}));

export const useAuth = () => useAuthStore();
```

### Step 9: Health Polling Hook

Create `src/hooks/useHealth.ts`:

```typescript
import { useEffect, useState } from 'react';
import APIClient from '../services/api';
import { HealthMetrics } from '../types';

export const useHealth = (pollIntervalMs: number = 2000) => {
  const [health, setHealth] = useState<HealthMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      setLoading(true);
      try {
        const client = new APIClient();
        const response = await client.getHealth();
        setHealth(response.data);
        setError(null);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchHealth();

    // Set up polling
    const interval = setInterval(fetchHealth, pollIntervalMs);

    return () => clearInterval(interval);
  }, [pollIntervalMs]);

  return { health, loading, error };
};
```

### Step 10: Traffic Light Component

Create `src/components/Status/TrafficLightIndicator.tsx`:

```typescript
import React from 'react';
import { IndicatorStatus } from '../../types';

interface TrafficLightProps {
  status: IndicatorStatus;
  size?: 'sm' | 'md' | 'lg';
}

export const TrafficLightIndicator: React.FC<TrafficLightProps> = ({ status, size = 'lg' }) => {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-16 h-16',
    lg: 'w-24 h-24',
  };

  const statusClasses = {
    GREEN: 'bg-green-500 shadow-green-500/50',
    YELLOW: 'bg-yellow-500 shadow-yellow-500/50',
    RED: 'bg-blood-red shadow-blood-red/50',
  };

  const labelClasses = {
    GREEN: 'text-green-700',
    YELLOW: 'text-yellow-700',
    RED: 'text-blood-red',
  };

  return (
    <div className="flex flex-col items-center gap-3">
      <div
        className={`${sizeClasses[size]} rounded-full ${statusClasses[status]} shadow-lg animate-pulse`}
      />
      <span className={`text-lg font-bold ${labelClasses[status]}`}>
        {status}
      </span>
    </div>
  );
};
```

### Step 11: Status Dashboard Page

Create `src/components/Status/StatusDashboard.tsx`:

```typescript
import React from 'react';
import { useHealth } from '../../hooks/useHealth';
import { TrafficLightIndicator } from './TrafficLightIndicator';
import { MetricsGrid } from './MetricsGrid';
import { HistoricalChart } from './HistoricalChart';

export const StatusDashboard: React.FC = () => {
  const { health, loading, error } = useHealth();

  if (loading && !health) {
    return <div className="p-8 text-center">Loading system status...</div>;
  }

  if (error && !health) {
    return (
      <div className="p-8 bg-red-50 text-blood-red border border-blood-red rounded">
        Error loading health metrics: {error}
      </div>
    );
  }

  if (!health) {
    return <div className="p-8 text-center">No health data available</div>;
  }

  return (
    <div className="space-y-8 p-8">
      {/* Traffic Light Status */}
      <section className="card flex justify-center">
        <TrafficLightIndicator status={health.indicator} size="lg" />
      </section>

      {/* Metrics Grid */}
      <section>
        <h2 className="text-2xl font-bold mb-4 text-carbon-black">System Metrics</h2>
        <MetricsGrid health={health} />
      </section>

      {/* Historical Chart */}
      <section>
        <h2 className="text-2xl font-bold mb-4 text-carbon-black">Last 24 Hours</h2>
        <div className="card">
          <HistoricalChart health={health} />
        </div>
      </section>

      {/* Status Summary */}
      <section className="card">
        <h3 className="text-lg font-bold text-carbon-black mb-2">Status Summary</h3>
        <p className="text-charcoal-brown">
          System is currently <strong>{health.status}</strong>. 
          {health.indicator === 'RED' && (
            <> Review active incidents immediately.</>
          )}
          {health.indicator === 'YELLOW' && (
            <> Monitor system for escalation.</>
          )}
          {health.indicator === 'GREEN' && (
            <> All systems operating normally.</>
          )}
        </p>
      </section>
    </div>
  );
};
```

### Step 12: Validations Table

Create `src/components/Validations/RecentValidations.tsx`:

```typescript
import React, { useEffect, useState } from 'react';
import { ValidationMetrics } from '../../types';
import APIClient from '../../services/api';
import { ValidationTable } from './ValidationTable';

export const RecentValidations: React.FC = () => {
  const [validations, setValidations] = useState<ValidationMetrics[]>([]);
  const [loading, setLoading] = useState(false);

  // In production, you'd poll /v3/intent endpoints or use WebSocket
  // This is a placeholder structure
  useEffect(() => {
    const fetchValidations = async () => {
      setLoading(true);
      try {
        // Placeholder: fetch would come from a backend endpoint
        // that aggregates recent validation results
        setValidations([]);
      } catch (err) {
        console.error('Failed to fetch validations:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchValidations();
    const interval = setInterval(fetchValidations, 5000); // Poll every 5s

    return () => clearInterval(interval);
  }, []);

  if (loading && validations.length === 0) {
    return <div className="p-8 text-center">Loading validations...</div>;
  }

  return (
    <div className="space-y-4 p-8">
      <h2 className="text-2xl font-bold text-carbon-black">Recent Validations</h2>
      <div className="card">
        <ValidationTable validations={validations} />
      </div>
    </div>
  );
};
```

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Foundation (Days 1-2)
- [ ] React + TypeScript project initialized
- [ ] Tailwind CSS configured with custom color palette
- [ ] API client service layer created
- [ ] Authentication flow implemented (login, JWT refresh, logout)
- [ ] Type definitions for all API responses
- [ ] Environment configuration (.env setup)

### Phase 2: Core Components (Days 3-4)
- [ ] TrafficLightIndicator component
- [ ] MetricsGrid component (displays health metrics)
- [ ] StatusDashboard page
- [ ] Hooks for API polling (useHealth, useValidations)
- [ ] Zustand store for auth state management

### Phase 3: Validations & Incidents (Days 5-6)
- [ ] ValidationTable component
- [ ] ValidationDetailModal (drill-down view)
- [ ] IncidentPanel (shows 424 blocks)
- [ ] RewindModal (confirm agent rewind)
- [ ] Integration with `/v3/rewind/{agent_id}` endpoint

### Phase 4: Audit & Compliance (Day 7)
- [ ] AuditEventList component
- [ ] ChainVerificationBadge (shows hash chain integrity)
- [ ] AuditLogViewer page
- [ ] Date range filtering
- [ ] Export to CSV/PDF

### Phase 5: Onboarding Console (Days 8-9)
- [ ] TenantSetupForm
- [ ] UserManagementTable
- [ ] APIKeyManager
- [ ] KeyGenerationModal (with copy-to-clipboard)
- [ ] Integration with onboarding endpoints

### Phase 6: Integration Wizard (Day 10)
- [ ] PatternSelector (sync/async/webhook)
- [ ] LanguageSelector (Python/TypeScript/cURL)
- [ ] CodeGenerator (populate with client's API key)
- [ ] TestWorkspace (live API explorer)

### Post-Launch: Refinements
- [ ] WebSocket support for real-time updates (instead of polling)
- [ ] Dark mode toggle (optional)
- [ ] Mobile-responsive design
- [ ] Performance optimization (virtualization for large tables)

---

## TESTING & DEPLOYMENT

### Step 13: Local Testing

```bash
# Start backend
cd /path/to/oriphim-infra
uvicorn app.main:app --reload

# In another terminal, start dashboard dev server
cd client-dashboard
npm run dev

# Visit http://localhost:5173
```

### Step 14: Docker Integration

Create `client-dashboard/Dockerfile`:

```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Runtime stage
FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

Add to main `docker-compose.yml`:

```yaml
dashboard:
  build:
    context: ./client-dashboard
    dockerfile: Dockerfile
  ports:
    - "3000:3000"
  environment:
    - VITE_API_BASE_URL=http://oriphim:8000
  depends_on:
    - oriphim
  networks:
    - oriphim-network
```

### Step 15: Production Deployment

```bash
# Build for production
npm run build

# Output goes to dist/ directory
# Deploy to:
# - Vercel (zero-config)
# - Netlify (zero-config)
# - AWS S3 + CloudFront
# - Your own nginx/Apache server

# Example: Deploy to Vercel
npm install -g vercel
vercel deploy --prod
```

---

## TESTING CHECKLIST

### Unit Tests (Optional but recommended)

```bash
npm install -D vitest @testing-library/react
```

Example test structure:

```typescript
// src/components/Status/TrafficLightIndicator.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TrafficLightIndicator } from './TrafficLightIndicator';

describe('TrafficLightIndicator', () => {
  it('renders GREEN status', () => {
    render(<TrafficLightIndicator status="GREEN" />);
    expect(screen.getByText('GREEN')).toBeInTheDocument();
  });

  it('renders RED status with blood-red color', () => {
    const { container } = render(<TrafficLightIndicator status="RED" />);
    const indicator = container.querySelector('[class*="bg-blood-red"]');
    expect(indicator).toBeInTheDocument();
  });
});
```

---

## KEY DESIGN DECISIONS

### Why This Architecture?

1. **Zustand for state management** - Minimal boilerplate, no context hell
2. **Axios for HTTP** - Simple retry/interceptor logic for auth token refresh
3. **Tailwind CSS** - Utility-first makes color changes trivial
4. **Vite** - Fast dev server, optimal production builds
5. **Client-side polling** - Simple, no backend WebSocket complexity (add later if needed)

### Security Considerations

1. **Never store API keys in localStorage** - Use access tokens only
2. **Refresh token rotation** - 401 triggers automatic refresh
3. **CORS-safe** - Backend should set `Access-Control-Allow-Origin` for dashboard domain
4. **Audit every action** - Modal confirmations for sensitive ops (rewind, key generation)
5. **XSS protection** - React escapes by default, never use `dangerouslySetInnerHTML`

---

## TROUBLESHOOTING

### "CORS errors when calling backend"

**Solution:** Add to FastAPI backend (`app/main.py`):

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        os.getenv("DASHBOARD_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### "401 Unauthorized on every request"

**Solution:** Ensure token interceptor is working:

```typescript
// In APIClient constructor, verify request includes Authorization header
console.log('Authorization:', config.headers?.Authorization);
```

### "Color palette looks wrong"

**Solution:** Clear Tailwind cache:

```bash
rm -rf node_modules/.vite
npm run dev
```

---

## NEXT STEPS

1. **Start Phase 1** - Project setup and authentication
2. **Build incrementally** - One page per day, test before moving on
3. **Use the ASCII mockups** - They're your HTML structure blueprint
4. **Get user feedback early** - Show drafts to operations team after Phase 2
5. **Plan for real-time** - After launch, add WebSocket support for sub-second updates

---

**Document Version:** 1.0  
**Last Updated:** March 4, 2026  
**Estimated full build time:** 7-10 days with one developer  
**Maintenance burden:** ~2 hours/week for updates + bug fixes
