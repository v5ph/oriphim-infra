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

export interface RewindResponse {
  agent_id: string;
  snapshot_id: number | null;
  restored: boolean;
  restored_at: string | null;
  system_prompt: string | null;
  context: Record<string, unknown> | null;
  variables: Record<string, unknown> | null;
}
