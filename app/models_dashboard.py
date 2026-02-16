"""
Dashboard-ready data models
Structured responses for UI consumption
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ConfidenceMetrics(BaseModel):
    score: float
    risk_level: str
    explanation: str


class ViolationDetail(BaseModel):
    name: str
    severity_pct: float
    weight: float
    impact_description: str


class DriftMetrics(BaseModel):
    detected: bool
    z_score: float
    historical_mean: float
    current_value: float
    explanation: str


class ValidationMetrics(BaseModel):
    """Complete validation result with all advanced metrics."""
    request_id: Optional[str] = None
    timestamp: datetime
    status_code: int
    divergence_score: float
    violations: List[str]
    
    # Advanced metrics
    confidence: ConfidenceMetrics
    violation_severities: List[ViolationDetail]
    overall_severity_score: Optional[float]
    drift: DriftMetrics
    
    # Summary for dashboard
    action: str  # "ALLOW", "REVIEW", "BLOCK"
    recommendation: str
    context_reset: Optional[bool] = None
    latency_ms: Optional[float] = None


class HealthMetrics(BaseModel):
    """System health for dashboard."""
    uptime_requests: int
    recent_divergence_avg: float
    recent_violation_rate: float
    drift_detected: bool
    last_critical_violation: Optional[str]
    status: str  # "HEALTHY", "DEGRADED", "CRITICAL"
