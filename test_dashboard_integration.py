#!/usr/bin/env python3
"""
Dashboard Integration Test
Shows what data a dashboard UI would consume from /v2/validate and /v2/health endpoints.
"""

import json
from app.models import ValidationRequest, PhysicsPayload, FinancialPayload
from app.core.entropy import hallucination_divergence
from app.core.constraints import check_logic
from app.core.confidence import calculate_confidence
from app.core.severity import calculate_violation_severity, calculate_overall_severity_score
from app.core.drift import request_history
from datetime import datetime


def demo_scenario(title: str, samples: list[str], request: ValidationRequest):
    """Simulate a validation and show dashboard-ready output."""
    print("\n" + "="*80)
    print(f"SCENARIO: {title}")
    print("="*80)
    
    # Core validation
    entropy_score = hallucination_divergence(samples)
    violations = check_logic(request)
    
    # Feature 1: Confidence
    confidence = calculate_confidence(entropy_score, violations)
    
    # Feature 2: Severity
    violation_severities = [
        calculate_violation_severity(v, 0.0) for v in violations
    ]
    overall_severity = calculate_overall_severity_score(violation_severities)
    
    # Feature 3: Drift
    request_history.record(entropy_score, len(violations))
    drift = request_history.detect_drift(entropy_score)
    
    # Determine action
    if violations or entropy_score > 0.4:
        if overall_severity >= 3.0:
            action = "BLOCK"
            status_code = 424
        else:
            action = "REVIEW"
            status_code = 400
    else:
        action = "ALLOW"
        status_code = 200
    
    # Output for dashboard
    dashboard_payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "status_code": status_code,
        "action": action,
        "metrics": {
            "divergence_score": round(entropy_score, 3),
            "confidence": {
                "score": confidence.score,
                "risk_level": confidence.risk_level,
                "explanation": confidence.explanation,
            },
            "violations": {
                "count": len(violations),
                "list": violations,
                "severities": [
                    {
                        "name": v.violation,
                        "severity_pct": round(v.severity_pct, 1),
                        "weight": v.weight,
                        "impact": v.impact_description,
                    }
                    for v in violation_severities
                ],
                "overall_severity": round(overall_severity, 2) if violation_severities else 0.0,
            },
            "drift": {
                "detected": drift.detected,
                "z_score": round(drift.z_score, 2),
                "historical_mean": round(drift.historical_mean, 3),
                "explanation": drift.explanation,
            },
        },
    }
    
    print(json.dumps(dashboard_payload, indent=2))
    return dashboard_payload


def main():
    print("\n" + "="*80)
    print("ADVANCED WATCHER PROTOCAL: DASHBOARD INTEGRATION TEST")
    print("="*80)
    
    # Scenario 1: Clean request (no issues)
    demo_scenario(
        "Clean Request (No Issues)",
        ["Result: 50m/s velocity", "Result: 50m/s velocity", "Result: 50m/s velocity"],
        ValidationRequest(
            samples=["Result: 50m/s velocity", "Result: 50m/s velocity", "Result: 50m/s velocity"],
            physics=PhysicsPayload(energy_in=100, energy_out=100),
        ),
    )
    
    # Scenario 2: High divergence (different answers)
    demo_scenario(
        "High Divergence (Unstable Reasoning)",
        [
            "The answer is definitely yes, quantum entanglement allows FTL.",
            "No way, relativity forbids FTL communication.",
            "Maybe with wormholes? Unclear.",
        ],
        ValidationRequest(
            samples=[
                "The answer is definitely yes, quantum entanglement allows FTL.",
                "No way, relativity forbids FTL communication.",
                "Maybe with wormholes? Unclear.",
            ],
        ),
    )
    
    # Scenario 3: Minor constraint violation
    demo_scenario(
        "Minor Violation (Leverage 11x)",
        ["Use 11x leverage for modest gains", "Use 11x leverage for modest gains", "Use 11x leverage"],
        ValidationRequest(
            samples=["Use 11x leverage for modest gains", "Use 11x leverage for modest gains", "Use 11x leverage"],
            metrics={"leverage_ratio": 11.0},
        ),
    )
    
    # Scenario 4: Critical violation (Leverage 50x)
    demo_scenario(
        "Critical Violation (Leverage 50x)",
        ["Use 50x leverage to maximize", "Use 50x leverage to maximize", "Use 50x leverage"],
        ValidationRequest(
            samples=["Use 50x leverage to maximize", "Use 50x leverage to maximize", "Use 50x leverage"],
            metrics={"leverage_ratio": 50.0},
        ),
    )
    
    # Scenario 5: Perpetual motion (Energy violation)
    demo_scenario(
        "Energy Conservation Violation",
        [
            "Design outputs 150J from 100J input via vacuum extraction",
            "Design outputs 150J from 100J input via resonance",
            "Design outputs 150J from 100J input using quantum effects",
        ],
        ValidationRequest(
            samples=[
                "Design outputs 150J from 100J input via vacuum extraction",
                "Design outputs 150J from 100J input via resonance",
                "Design outputs 150J from 100J input using quantum effects",
            ],
            physics=PhysicsPayload(energy_in=100, energy_out=150),
        ),
    )
    
    print("\n" + "="*80)
    print("HISTORY SUMMARY (Last 5 Requests)")
    print("="*80)
    stats = request_history.get_stats()
    print(f"Total requests: {stats['count']}")
    print(f"Avg divergence: {stats['mean']:.3f}")
    print(f"Std dev: {stats['std_dev']:.3f}")
    print("\nDashboard can now display:")
    print("- Traffic trends (divergence over time)")
    print("- Health status (HEALTHY/DEGRADED/CRITICAL)")
    print("- Anomalies (drift detection alerts)")
    print("- Risk heatmap (by severity level)")


if __name__ == "__main__":
    main()
