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


def _compute_action_label(status_code: int, action: str, severity_overall: float, confidence_score: float) -> tuple[str, str]:
    """Compute CRO-friendly action_label and action_reason for single-line decisions.
    
    Returns (action_label: str, action_reason: str)
    """
    if status_code == 424:
        return ("BLOCK", "Constraint violation prevents execution (424 Sentinel)")
    elif action == "BLOCK":
        return ("BLOCK", "Critical violation detected; manual review required")
    elif action == "REVIEW":
        risk = "high" if confidence_score < 0.5 else "moderate"
        return ("REVIEW", f"Requires manual review due to {risk} confidence ({confidence_score:.2f})")
    elif action == "CAUTION":
        return ("CAUTION", f"Latency guard triggered ({LATENCY_GUARD_SECONDS*1000:.0f}ms); process continues with flag")
    else:  # ALLOW
        return ("ALLOW", f"Safe to execute (confidence={confidence_score:.2f})")


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
    """Parallel validation with 424 as IMMEDIATE SYNCHRONOUS CONTROL PATH.
    
    FINTECH-FIRST DESIGN:
    1. 424 triggers instantly (not deferred)
    2. Rewind snapshot capture is ATOMIC with validation
    3. Compliance Forge entry written synchronously
    4. Action label + reason computed server-side for CRO clarity
    """
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

    # ====== DETERMINISTIC ENFORCEMENT: 424 = IMMEDIATE SYNC CONTROL PATH ======
    # On 424: capture snapshot + log audit event BEFORE returning
    if status_code == 424:
        # 1. Snapshot capture (for Agent Rewind)
        if request.state_snapshot:
            insert_state_snapshot(
                agent_id=request.agent_id,
                request_id=request_id,
                system_prompt=request.state_snapshot.system_prompt,
                context=request.state_snapshot.context,
                variables=request.state_snapshot.variables,
                valid=False,  # Mark as invalid state pre-424
            )
        
        # 2. Compliance Forge entry (regulatory articles + chain-of-thought)
        articles = map_violations_to_articles(violations)
        insert_audit_event(
            request_id=request_id,
            agent_id=request.agent_id,
            event_type="EXECUTION_BLOCKED_424",  # Explicit 424 marker
            violations=violations,
            regulatory_articles=articles,
            message=(
                f"Execution BLOCKED (424 Sentinel). Constraint violations: {'; '.join(violations)}. "
                f"Context reset flag: {context_reset}. Regulatory articles: {', '.join(articles)}"
            ),
        )
    # On ALLOW: capture valid snapshot for rewind capability
    elif action == "ALLOW" and request.state_snapshot:
        insert_state_snapshot(
            agent_id=request.agent_id,
            request_id=request_id,
            system_prompt=request.state_snapshot.system_prompt,
            context=request.state_snapshot.context,
            variables=request.state_snapshot.variables,
            valid=True,
        )

    # Compute action_label and action_reason for CRO UI
    action_label, action_reason = _compute_action_label(
        status_code, action, severity["overall"], confidence.score
    )

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

    return {
        "request_id": request_id,
        "status_code": status_code,
        "action": action,
        "action_label": action_label,
        "action_reason": action_reason,
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
