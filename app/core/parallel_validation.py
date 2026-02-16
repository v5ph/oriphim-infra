from __future__ import annotations

import time
from typing import Dict, Any, List

from app.core.constraints import check_logic
from app.core.entropy import hallucination_divergence
from app.core.confidence import calculate_confidence
from app.core.severity import calculate_violation_severity, calculate_overall_severity_score
from app.core.drift import request_history
from app.core.compliance import map_violations_to_articles
from app.core.storage import insert_validation_result, insert_audit_event, insert_state_snapshot
from app.models import AgentIntentRequest


LATENCY_GUARD_SECONDS = 0.2


def _build_severity(violations: List[str]) -> Dict[str, Any]:
    details = [calculate_violation_severity(v, 0.0) for v in violations]
    overall = calculate_overall_severity_score(details)
    return {
        "details": [
            {
                "name": d.violation,
                "severity_pct": d.severity_pct,
                "weight": d.weight,
                "impact_description": d.impact_description,
            }
            for d in details
        ],
        "overall": overall,
    }


def run_parallel_validation(request_id: str, request: AgentIntentRequest) -> Dict[str, Any]:
    start = time.perf_counter()

    entropy_score = hallucination_divergence(request.samples)
    violations = check_logic(request)

    confidence = calculate_confidence(entropy_score, violations)
    severity = _build_severity(violations)

    request_history.record(entropy_score, len(violations))
    drift = request_history.detect_drift(entropy_score)

    elapsed = time.perf_counter() - start
    latency_ms = elapsed * 1000.0

    context_reset = False
    if elapsed > LATENCY_GUARD_SECONDS:
        action = "CAUTION"
        status_code = 202
        recommendation = "Latency guard triggered; caution flagged for downstream review."
    elif violations or entropy_score > 0.4:
        if severity["overall"] >= 3.0:
            action = "BLOCK"
            status_code = 424
            context_reset = True
            recommendation = (
                severity["details"][0]["impact_description"]
                if severity["details"]
                else "Critical violation detected"
            )
        else:
            action = "REVIEW"
            status_code = 400
            recommendation = f"Manual review recommended. Confidence: {confidence.risk_level}"
    else:
        action = "ALLOW"
        status_code = 200
        recommendation = "Safe to execute"

    insert_validation_result(
        request_id=request_id,
        status_code=status_code,
        action=action,
        divergence_score=entropy_score,
        violations=violations,
        confidence={
            "score": confidence.score,
            "risk_level": confidence.risk_level,
            "explanation": confidence.explanation,
        },
        severity=severity,
        drift={
            "detected": drift.detected,
            "z_score": drift.z_score,
            "historical_mean": drift.historical_mean,
            "current_value": drift.current_value,
            "explanation": drift.explanation,
        },
        recommendation=recommendation,
        context_reset=context_reset,
        latency_ms=latency_ms,
    )

    if request.state_snapshot and action == "ALLOW":
        insert_state_snapshot(
            agent_id=request.agent_id,
            request_id=request_id,
            system_prompt=request.state_snapshot.system_prompt,
            context=request.state_snapshot.context,
            variables=request.state_snapshot.variables,
            valid=True,
        )

    if status_code == 424:
        articles = map_violations_to_articles(violations)
        insert_audit_event(
            request_id=request_id,
            agent_id=request.agent_id,
            event_type="EXECUTION_BLOCKED",
            violations=violations,
            regulatory_articles=articles,
            message=(
                "Execution blocked due to constraint violation: "
                + "; ".join(violations)
                + ". Context reset required."
            ),
        )

    return {
        "request_id": request_id,
        "status_code": status_code,
        "action": action,
        "divergence_score": entropy_score,
        "violations": violations,
        "confidence": {
            "score": confidence.score,
            "risk_level": confidence.risk_level,
            "explanation": confidence.explanation,
        },
        "severity": severity,
        "drift": {
            "detected": drift.detected,
            "z_score": drift.z_score,
            "historical_mean": drift.historical_mean,
            "current_value": drift.current_value,
            "explanation": drift.explanation,
        },
        "recommendation": recommendation,
        "context_reset": context_reset,
        "latency_ms": latency_ms,
    }
