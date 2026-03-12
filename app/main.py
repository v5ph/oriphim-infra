from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from app.models import (
    ValidationRequest,
    ValidationResponse,
    AgentIntentRequest,
    IntentAck,
    ParallelValidationStatus,
    RewindResponse,
    PreTradeRequest,
    PreTradeResponse,
    TradeOrder,
    SimulationRequest,
    SimulationResponse,
    SimulationSummary,
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
    verify_runtime_audit_chain,
    insert_execution_decision,
    get_execution_decision,
    insert_simulation_run,
    get_simulation_run,
    reserve_pre_trade_frequency_slot,
)
from app.core.trade_guard import evaluate_pre_trade
from app.core.simulation import run_policy_simulation
from app.core.compliance import map_violations_to_articles
from app.core.pdf_export import generate_audit_pdf
from app.core.security import get_security_headers, init_security, SecurityConfigError
from app.core.entropy import load_embedding_model
from app.routes.onboarding import get_current_tenant, require_permission, router as onboarding_router
from uuid import uuid4
import json
import os
import logging
from collections import defaultdict
import time

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

# Simple in-memory rate limiting (for production, use Redis)
_rate_limit_store: defaultdict = defaultdict(list)
_RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    logger.info("Starting Watcher Protocol application...")
    
    # Pre-warm embedding model to avoid cold start
    try:
        load_embedding_model()
    except Exception as e:
        logger.warning(f"Failed to pre-warm embedding model: {e}")
    
    logger.info("Application startup complete")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Structured error responses for unhandled exceptions."""
    logger.error(
        "Unhandled exception on %s (request_id=%s)",
        request.url.path,
        getattr(request.state, "request_id", "unknown"),
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal error occurred.",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


# Configure CORS for dashboard frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        os.getenv("DASHBOARD_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize security subsystem
try:
    init_security()
    logger.info("Security subsystem initialized")
except SecurityConfigError as e:
    environment = os.getenv("APP_ENV", "development").lower()
    allow_insecure_startup = os.getenv("ALLOW_INSECURE_STARTUP", "false").lower() == "true"
    if allow_insecure_startup and environment in {"development", "dev", "local", "test"}:
        logger.warning(f"Security configuration incomplete: {e}")
        logger.warning("ALLOW_INSECURE_STARTUP enabled for non-production environment")
    else:
        raise RuntimeError(f"Security configuration incomplete: {e}") from e

# Include onboarding routes
app.include_router(onboarding_router)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple in-memory rate limiting (per IP address).
    
    For production: migrate to Redis with sliding window.
    Limits: {_RATE_LIMIT_REQUESTS} requests per {_RATE_LIMIT_WINDOW_SECONDS}s per IP.
    """
    # Skip rate limiting for health checks
    if request.url.path in ["/v2/health", "/health"]:
        return await call_next(request)
    
    # Get client IP (considering proxy headers)
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.client.host if request.client else "unknown"
    
    now = time.time()
    cutoff = now - _RATE_LIMIT_WINDOW_SECONDS
    
    # Clean old requests and check limit
    _rate_limit_store[client_ip] = [t for t in _rate_limit_store[client_ip] if t > cutoff]
    
    if len(_rate_limit_store[client_ip]) >= _RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate Limit Exceeded",
                "message": f"Maximum {_RATE_LIMIT_REQUESTS} requests per {_RATE_LIMIT_WINDOW_SECONDS}s",
                "retry_after": int(_RATE_LIMIT_WINDOW_SECONDS)
            },
            headers={"Retry-After": str(_RATE_LIMIT_WINDOW_SECONDS)}
        )
    
    # Record this request
    _rate_limit_store[client_ip].append(now)
    
    return await call_next(request)


@app.middleware("http")
async def https_enforcement_middleware(request: Request, call_next):
    """Enforce HTTPS in production environments (runs first to ensure headers on redirects)."""
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
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses (runs after HTTPS enforcement)."""
    response = await call_next(request)
    
    # Apply security headers
    security_headers = get_security_headers()
    for header, value in security_headers.items():
        response.headers[header] = value
    
    return response


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
    timestamp = datetime.now(timezone.utc)
    entropy_score = hallucination_divergence(request.samples)
    violations = check_logic(request)
    
    # Feature 1: Confidence scoring
    confidence = calculate_confidence(entropy_score, violations)
    
    # Feature 2: Severity-weighted violations
    violation_severity_objects = [
        calculate_violation_severity(v, 0.0) for v in violations
    ]
    # Convert ViolationSeverity to ViolationDetail for response
    violation_severities = [
        ViolationDetail(
            name=vs.violation,
            severity_pct=vs.severity_pct,
            weight=vs.weight,
            impact_description=vs.impact_description,
        )
        for vs in violation_severity_objects
    ]
    overall_severity = calculate_overall_severity_score(violation_severity_objects)
    
    # Feature 3: Drift detection
    request_history.record(entropy_score, len(violations))
    drift = request_history.detect_drift(entropy_score)
    
    # Determine action and status code
    if violations or entropy_score > 0.4:
        if overall_severity >= 3.0:
            action = "BLOCK"
            status_code = 424
            recommendation = f"CRITICAL: {violation_severity_objects[0].impact_description if violation_severity_objects else 'High divergence'}"
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
            tenant_id=None,
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


@app.get("/v2/health")
def health_metrics() -> Response:
    """
    System health endpoint for monitoring and operations.
    Provides aggregated metrics about recent behavior.
    
    PRIMARY CONTRACT: indicator (GREEN/YELLOW/RED) is single source of truth for CRO.
    CRO polls every 2 seconds for real-time status.
    
    Returns 503 Service Unavailable when status is CRITICAL.
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
    
    metrics = HealthMetrics(
        uptime_requests=stats["count"],
        recent_divergence_avg=round(recent_divergence_avg, 3),
        recent_violation_rate=round(violation_rate, 3),
        drift_detected=False,  # Would check global drift state
        last_critical_violation=None,  # Would track from history
        status=status,
        indicator=indicator,
    )
    
    # Return 503 when system is CRITICAL (alerts monitoring systems)
    if status == "CRITICAL":
        return JSONResponse(
            status_code=503,
            content=metrics.model_dump()
        )
    
    return JSONResponse(
        status_code=200,
        content=metrics.model_dump()
    )


@app.post("/v3/intent", response_model=IntentAck)
def submit_intent(
    request: AgentIntentRequest,
    background_tasks: BackgroundTasks,
    current_tenant: str = Depends(get_current_tenant),
    _: bool = Depends(require_permission("validate")),
) -> IntentAck:
    if request.tenant_id and request.tenant_id != current_tenant:
        raise HTTPException(status_code=403, detail="Cannot submit intents for another tenant")

    request = request.model_copy(update={"tenant_id": current_tenant})
    request_id = str(uuid4())
    insert_request(
        request_id=request_id,
        agent_id=request.agent_id,
        intent=request.intent,
        desired_state=request.desired_state,
        samples=request.samples,
        payload=request.model_dump(),
        tenant_id=current_tenant,
    )
    background_tasks.add_task(run_parallel_validation, request_id, request)
    return IntentAck(
        request_id=request_id,
        status="PENDING",
        received_at=datetime.utcnow().isoformat(),
    )


@app.get("/v3/intent/{request_id}", response_model=ParallelValidationStatus)
def get_intent_status(
    request_id: str,
    current_tenant: str = Depends(get_current_tenant),
    _: bool = Depends(require_permission("read_results")),
):
    result = get_validation_result(request_id, tenant_id=current_tenant)
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
def rewind_agent(
    agent_id: str,
    current_tenant: str = Depends(get_current_tenant),
    _: bool = Depends(require_permission("read_results")),
) -> RewindResponse:
    try:
        snapshot = get_latest_valid_snapshot(agent_id, current_tenant)
        if snapshot is None:
            # No snapshot found (agent never saved state)
            return RewindResponse(
                agent_id=agent_id,
                snapshot_id=None,
                restored=False,
                restored_at=None,
                system_prompt=None,
                context=None,
                variables=None,
            )
    except Exception as e:
        # Database error or other failure
        logger.error(f"Failed to retrieve snapshot for {agent_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve snapshot: {str(e)}"
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
def export_compliance_ledger(
    agent_id: str | None = None,
    current_tenant: str = Depends(get_current_tenant),
    _: bool = Depends(require_permission("view_audit")),
):
    if not verify_runtime_audit_chain(current_tenant):
        raise HTTPException(status_code=409, detail="Runtime audit chain verification failed")

    events = list_audit_events(tenant_id=current_tenant, agent_id=agent_id)
    pdf_bytes = generate_audit_pdf("Oriphim Compliance Ledger", events)
    export_id = str(uuid4())
    headers = {
        "Content-Disposition": f"attachment; filename=compliance-ledger-{export_id}.pdf"
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@app.post("/v4/execution/pre-trade", response_model=PreTradeResponse)
def enforce_pre_trade_policy(
    request: PreTradeRequest,
    current_tenant: str = Depends(get_current_tenant),
    _: bool = Depends(require_permission("validate")),
) -> PreTradeResponse:
    if request.tenant_id != current_tenant:
        raise HTTPException(status_code=403, detail="Cannot evaluate pre-trade policy for another tenant")

    decision_id = str(uuid4())
    reservation_count = reserve_pre_trade_frequency_slot(
        tenant_id=request.tenant_id,
        agent_id=request.agent_id,
        idempotency_key=request.idempotency_key,
    )
    effective_account = request.account.model_copy(
        update={
            "orders_last_minute": max(request.account.orders_last_minute, max(reservation_count - 1, 0))
        }
    )

    result = evaluate_pre_trade(
        order=request.order,
        account=effective_account,
        policy=request.policy,
    )

    modified_order_model = None
    if result["modified_order"] is not None:
        modified_order_model = TradeOrder(**result["modified_order"])

    try:
        stored_decision = insert_execution_decision(
            decision_id=decision_id,
            tenant_id=request.tenant_id,
            agent_id=request.agent_id,
            decision=result["decision"],
            reason=result["reason"],
            triggered_controls=result["triggered_controls"],
            order=request.order.model_dump(),
            account=effective_account.model_dump(mode="json"),
            policy=request.policy.model_dump(),
            modified_order=result["modified_order"],
            idempotency_key=request.idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if stored_decision["modified_order"] is not None:
        modified_order_model = TradeOrder(**stored_decision["modified_order"])

    return PreTradeResponse(
        decision_id=stored_decision["decision_id"],
        decision=stored_decision["decision"],
        reason=stored_decision["reason"],
        triggered_controls=stored_decision["triggered_controls"],
        modified_order=modified_order_model,
        created_at=stored_decision["created_at"],
    )


@app.get("/v4/execution/pre-trade/{decision_id}")
def get_pre_trade_decision(
    decision_id: str,
    current_tenant: str = Depends(get_current_tenant),
    _: bool = Depends(require_permission("read_results")),
):
    decision = get_execution_decision(decision_id, current_tenant)
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@app.post("/v4/simulation/run", response_model=SimulationResponse)
def run_simulation(
    request: SimulationRequest,
    current_tenant: str = Depends(get_current_tenant),
    _: bool = Depends(require_permission("validate")),
) -> SimulationResponse:
    if request.tenant_id != current_tenant:
        raise HTTPException(status_code=403, detail="Cannot run simulations for another tenant")

    simulation_id = str(uuid4())

    simulation = run_policy_simulation(request)

    try:
        stored_simulation = insert_simulation_run(
            simulation_id=simulation_id,
            tenant_id=request.tenant_id,
            strategy_name=request.strategy_name,
            request_payload=request.model_dump(),
            summary=simulation["summary"],
            policy_blocks=simulation["policy_blocks"],
            timeline=simulation["timeline"],
            idempotency_key=request.idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return SimulationResponse(
        simulation_id=stored_simulation["simulation_id"],
        tenant_id=stored_simulation["tenant_id"],
        strategy_name=stored_simulation["strategy_name"],
        summary=SimulationSummary(**stored_simulation["summary"]),
        policy_blocks=stored_simulation["policy_blocks"],
        created_at=stored_simulation["created_at"],
    )


@app.get("/v4/simulation/{simulation_id}")
def get_simulation(
    simulation_id: str,
    current_tenant: str = Depends(get_current_tenant),
    _: bool = Depends(require_permission("read_results")),
):
    simulation = get_simulation_run(simulation_id, current_tenant)
    if simulation is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return simulation

