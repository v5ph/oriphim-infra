from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.models import (
    ValidationRequest,
    ValidationResponse,
    AgentIntentRequest,
    IntentAck,
    ParallelValidationStatus,
    RewindResponse,
)
from app.models_health import (
    ValidationMetrics,
    HealthMetrics,
    ConfidenceMetrics,
    ViolationDetail,
    DriftMetrics,
    IndicatorStatus,
)
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
from app.core.security import get_security_headers, init_security, SecurityConfigError
from app.routes.onboarding import router as onboarding_router
from datetime import datetime
from uuid import uuid4
import json
import os
import logging

logger = logging.getLogger(__name__)


def _compute_indicator(status_code: int, confidence_score: float, severity_overall: float) -> IndicatorStatus:
    """Compute GREEN/YELLOW/RED validation indicator.
    
    Traffic-light logic:
    - RED: 424, confidence < 0.5, or severity >= 3.0
    - YELLOW: 0.5 <= confidence < 0.8 or severity 1.5-3.0
    - GREEN: confidence >= 0.8 and status 200
    """
    if status_code == 424:
        return IndicatorStatus.RED
    if confidence_score < 0.5:
        return IndicatorStatus.RED
    if severity_overall >= 3.0:
        return IndicatorStatus.RED
    if confidence_score < 0.8 or (severity_overall >= 1.5):
        return IndicatorStatus.YELLOW
    if status_code == 200 and confidence_score >= 0.8:
        return IndicatorStatus.GREEN
    return IndicatorStatus.YELLOW  # Default to yellow if unclear


def _compute_health_indicator(violation_rate: float, drift_detected: bool) -> IndicatorStatus:
    """Compute system health indicator.
    
    - RED: violation_rate > 0.5 OR drift_detected
    - YELLOW: 0.3 < violation_rate <= 0.5
    - GREEN: violation_rate <= 0.3 AND NOT drift_detected
    """
    if violation_rate > 0.5 or drift_detected:
        return IndicatorStatus.RED
    if violation_rate > 0.3:
        return IndicatorStatus.YELLOW
    return IndicatorStatus.GREEN

app = FastAPI(title="Watcher Protocal", version="2.0")

# Initialize security subsystem
try:
    init_security()
    logger.info("Security subsystem initialized")
except SecurityConfigError as e:
    logger.warning(f"Security configuration incomplete: {e}")
    logger.warning("Some security features disabled. Configure .env for production.")

# Include onboarding routes
app.include_router(onboarding_router)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Apply security headers
    security_headers = get_security_headers()
    for header, value in security_headers.items():
        response.headers[header] = value
    
    return response


@app.middleware("http")
async def https_enforcement_middleware(request: Request, call_next):
    """Enforce HTTPS in production environments."""
    enforce_https = os.getenv("ENFORCE_HTTPS", "false").lower() == "true"
    
    if enforce_https:
        # Check if request came via HTTPS
        # Note: Behind reverse proxy, check X-Forwarded-Proto header
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
        scheme = forwarded_proto or request.url.scheme
        
        if scheme != "https":
            # Redirect to HTTPS
            https_url = str(request.url).replace("http://", "https://", 1)
            return JSONResponse(
                status_code=301,
                content={"detail": "Redirecting to HTTPS"},
                headers={"Location": https_url}
            )
    
    return await call_next(request)


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
    Returns validation results with health indicator.
    
    Returns indicator (GREEN/YELLOW/RED) + action_label for decision support.
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

    # Compute indicator and action_label for CRO clarity
    indicator = _compute_indicator(status_code, confidence.score, overall_severity)
    action_label = {
        "ALLOW": "ALLOW",
        "REVIEW": "REVIEW",
        "BLOCK": "BLOCK",
    }.get(action, "REVIEW")
    action_reason = {
        "ALLOW": f"Safe to execute (confidence={confidence.score:.2f})",
        "REVIEW": f"Requires review: {confidence.risk_level} confidence ({confidence.score:.2f})",
        "BLOCK": f"Execution blocked: {'; '.join(violations) if violations else 'High divergence'}",
    }.get(action, "Unknown decision")

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
        indicator=indicator,
        action_label=action_label,
        action_reason=action_reason,
        action=action,
        recommendation=recommendation,
        context_reset=context_reset,
    )


@app.get("/v2/health", response_model=HealthMetrics)
def health_metrics() -> HealthMetrics:
    """
    System health endpoint for monitoring and operations.
    Provides aggregated metrics about recent behavior.
    
    PRIMARY CONTRACT: indicator (GREEN/YELLOW/RED) is single source of truth for CRO.
    CRO polls every 2 seconds for real-time status.
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
    
    # Compute indicator for CRO (primary interface)
    indicator = _compute_health_indicator(violation_rate, False)  # drift_detected would be global flag
    
    return HealthMetrics(
        uptime_requests=stats["count"],
        recent_divergence_avg=round(recent_divergence_avg, 3),
        recent_violation_rate=round(violation_rate, 3),
        drift_detected=False,  # Would check global drift state
        last_critical_violation=None,  # Would track from history
        status=status,
        indicator=indicator,
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

