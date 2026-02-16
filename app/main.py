from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse
from app.models import (
    ValidationRequest,
    ValidationResponse,
    AgentIntentRequest,
    IntentAck,
    ParallelValidationStatus,
    RewindResponse,
)
from app.models_dashboard import ValidationMetrics, HealthMetrics, ConfidenceMetrics, ViolationDetail, DriftMetrics
from app.core.entropy import hallucination_divergence
from app.core.constraints import check_logic
from app.core.confidence import calculate_confidence
from app.core.severity import calculate_violation_severity, calculate_overall_severity_score
from app.core.drift import request_history
from app.core.parallel_validation import run_parallel_validation
from app.core.storage import (
    insert_request,
    get_validation_result,
    get_latest_valid_snapshot,
    list_audit_events,
    insert_audit_event,
)
from app.core.compliance import map_violations_to_articles
from app.core.pdf_export import generate_audit_pdf
from datetime import datetime
from uuid import uuid4
import json

app = FastAPI(title="Watcher Protocal", version="2.0")


@app.middleware("http")
async def watcher_gateway_middleware(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id

    if request.method in {"POST", "PUT", "PATCH"}:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body_bytes = await request.body()
            if body_bytes:
                try:
                    payload = json.loads(body_bytes.decode("utf-8"))
                except json.JSONDecodeError:
                    payload = None
                if isinstance(payload, dict) and "agent_id" in payload:
                    insert_request(
                        request_id=request_id,
                        agent_id=payload.get("agent_id"),
                        intent=payload.get("intent"),
                        desired_state=payload.get("desired_state"),
                        samples=payload.get("samples", []),
                        payload=payload,
                    )
            request._body = body_bytes

    response = await call_next(request)
    response.headers["X-Watcher-Request-Id"] = request_id
    return response


@app.post("/v1/validate", response_model=ValidationResponse)
def validate(request: ValidationRequest) -> ValidationResponse:
    entropy_score = hallucination_divergence(request.samples)
    violations = check_logic(request)

    if entropy_score > 0.4 or violations:
        status_code = 424 if violations else 403
        raise HTTPException(
            status_code=status_code,
            detail={
                "status": "Failed Dependency" if status_code == 424 else "Logic Violation",
                "reason": (
                    f"Hard constraint violated: {'; '.join(violations)}"
                    if violations
                    else f"Semantic divergence too high (score={entropy_score:.3f})"
                ),
                "entropy_score": entropy_score,
                "violations": violations,
                "context_reset": True if status_code == 424 else False,
            },
        )

    return ValidationResponse(
        status="OK",
        entropy_score=entropy_score,
        violations=[],
    )


@app.post("/v2/validate", response_model=ValidationMetrics)
def validate_advanced(request: ValidationRequest) -> ValidationMetrics:
    """
    Advanced validation endpoint with confidence, severity, and drift detection.
    Designed for dashboard consumption.
    """
    timestamp = datetime.utcnow()
    entropy_score = hallucination_divergence(request.samples)
    violations = check_logic(request)
    
    # Feature 1: Confidence scoring
    confidence = calculate_confidence(entropy_score, violations)
    
    # Feature 2: Severity-weighted violations
    violation_severities = [
        calculate_violation_severity(v, 0.0) for v in violations
    ]
    overall_severity = calculate_overall_severity_score(violation_severities)
    
    # Feature 3: Drift detection
    request_history.record(entropy_score, len(violations))
    drift = request_history.detect_drift(entropy_score)
    
    # Determine action and status code
    if violations or entropy_score > 0.4:
        if overall_severity >= 3.0:
            action = "BLOCK"
            status_code = 424
            recommendation = f"CRITICAL: {violation_severities[0].impact_description if violation_severities else 'High divergence'}"
        else:
            action = "REVIEW"
            status_code = 400
            recommendation = f"Manual review recommended. Confidence: {confidence.risk_level}"
    else:
        action = "ALLOW"
        status_code = 200
        recommendation = "Safe to execute"
    
    context_reset = False
    if status_code == 424:
        context_reset = True
        articles = map_violations_to_articles(violations)
        insert_audit_event(
            request_id="inline",
            agent_id=None,
            event_type="EXECUTION_BLOCKED",
            violations=violations,
            regulatory_articles=articles,
            message=(
                "Execution blocked via /v2/validate: "
                + "; ".join(violations)
            ),
        )

    return ValidationMetrics(
        request_id=None,
        timestamp=timestamp,
        status_code=status_code,
        divergence_score=entropy_score,
        violations=violations,
        confidence=ConfidenceMetrics(
            score=confidence.score,
            risk_level=confidence.risk_level,
            explanation=confidence.explanation,
        ),
        violation_severities=violation_severities,
        overall_severity_score=overall_severity if violation_severities else None,
        drift=DriftMetrics(
            detected=drift.detected,
            z_score=drift.z_score,
            historical_mean=drift.historical_mean,
            current_value=drift.current_value,
            explanation=drift.explanation,
        ),
        action=action,
        recommendation=recommendation,
        context_reset=context_reset,
    )


@app.get("/v2/health", response_model=HealthMetrics)
def health_metrics() -> HealthMetrics:
    """
    System health endpoint for dashboard.
    Provides aggregated metrics about recent behavior.
    """
    stats = request_history.get_stats()
    
    recent_divergence_avg = stats["mean"]
    violation_rate = (
        sum(request_history.violation_counts) / len(request_history.violation_counts)
        if request_history.violation_counts
        else 0.0
    )
    
    # Determine overall status
    if recent_divergence_avg > 0.5 or violation_rate > 0.5:
        status = "CRITICAL"
    elif recent_divergence_avg > 0.35 or violation_rate > 0.3:
        status = "DEGRADED"
    else:
        status = "HEALTHY"
    
    return HealthMetrics(
        uptime_requests=stats["count"],
        recent_divergence_avg=round(recent_divergence_avg, 3),
        recent_violation_rate=round(violation_rate, 3),
        drift_detected=False,  # Would check global drift state
        last_critical_violation=None,  # Would track from history
        status=status,
    )


@app.post("/v3/intent", response_model=IntentAck)
def submit_intent(request: AgentIntentRequest, background_tasks: BackgroundTasks) -> IntentAck:
    request_id = str(uuid4())
    insert_request(
        request_id=request_id,
        agent_id=request.agent_id,
        intent=request.intent,
        desired_state=request.desired_state,
        samples=request.samples,
        payload=request.model_dump(),
    )
    background_tasks.add_task(run_parallel_validation, request_id, request)
    return IntentAck(
        request_id=request_id,
        status="PENDING",
        received_at=datetime.utcnow().isoformat(),
    )


@app.get("/v3/intent/{request_id}", response_model=ParallelValidationStatus)
def get_intent_status(request_id: str):
    result = get_validation_result(request_id)
    if result is None:
        return JSONResponse(
            status_code=202,
            content={"request_id": request_id, "status": "PENDING"},
        )
    return ParallelValidationStatus(
        request_id=request_id,
        status_code=result["status_code"],
        action=result["action"],
        divergence_score=result["divergence_score"],
        violations=result["violations"],
        recommendation=result["recommendation"],
        context_reset=result["context_reset"],
        latency_ms=result["latency_ms"],
        created_at=result["created_at"],
    )


@app.post("/v3/rewind/{agent_id}", response_model=RewindResponse)
def rewind_agent(agent_id: str) -> RewindResponse:
    snapshot = get_latest_valid_snapshot(agent_id)
    if snapshot is None:
        return RewindResponse(
            agent_id=agent_id,
            snapshot_id=None,
            restored=False,
            restored_at=None,
            system_prompt=None,
            context=None,
            variables=None,
        )
    return RewindResponse(
        agent_id=agent_id,
        snapshot_id=snapshot["snapshot_id"],
        restored=True,
        restored_at=datetime.utcnow().isoformat(),
        system_prompt=snapshot["system_prompt"],
        context=snapshot["context"],
        variables=snapshot["variables"],
    )


@app.get("/v3/compliance/export")
def export_compliance_ledger(agent_id: str | None = None):
    events = list_audit_events(agent_id=agent_id)
    pdf_bytes = generate_audit_pdf("Oriphim Compliance Ledger", events)
    export_id = str(uuid4())
    headers = {
        "Content-Disposition": f"attachment; filename=compliance-ledger-{export_id}.pdf"
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

