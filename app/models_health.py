"""
Health and validation data models
Structured metrics for health monitoring and validation results
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class IndicatorStatus(str, Enum):
    """System health indicator (GREEN/YELLOW/RED). Computed server-side."""
    GREEN = "GREEN"      # action=ALLOW, confidence >= 0.8
    YELLOW = "YELLOW"    # action=REVIEW, 0.5 <= confidence < 0.8
    RED = "RED"          # action=BLOCK, confidence < 0.5 OR status=424


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
    """Complete validation result with all advanced metrics.
    
    PRIMARY CONTRACT FOR CRO:
    - indicator (GREEN/YELLOW/RED) is the single source of truth
    - action_label explicitly states the decision
    - action_reason explains it in one line
    All detail fields are subordinate to these three fields.
    """
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
    
    # CRO-FIRST INTERFACE (server-side computed)
    indicator: IndicatorStatus  # GREEN/YELLOW/RED
    action_label: str           # "ALLOW", "REVIEW", "BLOCK"
    action_reason: str          # Single-line CRO-friendly explanation
    
    # Summary for dashboard
    action: str  # "ALLOW", "REVIEW", "BLOCK"
    recommendation: str
    context_reset: Optional[bool] = None
    latency_ms: Optional[float] = None


class HealthMetrics(BaseModel):
    """System health metrics.
    
    Indicator (GREEN/YELLOW/RED) is derived from:
    - violation_rate
    - drift_detected
    - last_critical_violation
    """
    uptime_requests: int
    recent_divergence_avg: float
    recent_violation_rate: float
    drift_detected: bool
    last_critical_violation: Optional[str]
    status: str  # "HEALTHY", "DEGRADED", "CRITICAL"
    indicator: IndicatorStatus  # GREEN/YELLOW/RED
