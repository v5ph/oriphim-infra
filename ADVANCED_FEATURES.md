# Advanced Watcher Protocal Features

## Launch-Ready Demo Roadmap (Watcher Protocol)

### Phase 1: The "Watcher" Gateway Interceptor

**Objective:** Capture the agent’s intent before it reaches production.

**Logic:** Implement a FastAPI middleware that intercepts every outgoing request from an agentic workflow.

**Unique Identifier:** Every agentic call must be wrapped in a request object assigned a UUID in Supabase to track its lifecycle from proposal to execution.

**Parallelism:** The Watcher does not wait for a full simulation; it forks the request into a parallel validation stream using Redis and Celery to minimize impact on primary workflow latency.

---

### Phase 2: Parallel Simulation ("Rough Draft" Logic)

**Objective:** Run a lightweight mathematical sanity check without full simulation overhead.

**Rough Draft Simulation:** Use Simplified Symbolic Logic (e.g., mass balance for Biotech or VaR limits for Finance).

**Discrepancy Detection:** Use `PhysicalValidator` and `entropy.py` to compare the agent’s desired state vs a computed safe state.

**Latency Guard:** If simulation exceeds 200 ms, default to a "Caution" flag rather than a hard block to preserve blitz speed.

---

### Phase 3: The 424 Sentinel & Logic Reset

**Objective:** Stop the agent immediately on drift or physical violations.

**424 Trigger:** If the math fails, emit HTTP 424 (Execution Blocked).

**Memory Clear:** Trigger a "Context Reset" signal to purge hallucinated working memory and pull a clean state from the log.

**Incident Logging:** Write every 424 event to the Supabase audit log, including the violated law (e.g., "Violation of Law of Physical Invariance").

---

### Phase 4: Agent Rewind (State Version Control)

**Objective:** Roll back an agent to its last known valid state.

**State Change Log:** Store a versioned snapshot of system prompt + context + variable state after every successful execution.

**Rewind Mechanism:** Provide a one-click restore to the last T−1 state that passed Oriphim validation.

---

### Phase 5: Compliance Ledger (2026 Regulatory Proof)

**Objective:** Generate audit-ready evidence for EU AI Act and California SB 243 compliance.

**Chain-of-Thought Storage:** Store the agent’s internal reasoning steps alongside Oriphim validation steps.

**Standardized Forms:** Map validation failures to regulatory articles (e.g., EU AI Act Article 12 for record-keeping).

**Tamper-Proofing:** Use Supabase Row Level Security to prevent audit log modification post-write.

---

## Dashboard UX Alignment (Live Flight Recorder)

| Feature | Dashboard UI Component | UX Logic |
| --- | --- | --- |
| Watcher Stream | Live "Intent" Feed | Shows every agentic proposal as a pending card in real time. |
| Validation Status | Health Pulse (Green/Red) | Turns red and vibrates the UI when a 424 is emitted. |
| Rough Draft Sim | Logic Comparison View | Side-by-side view: "What Agent wants" vs "What Physics allows." |
| Agent Rewind | Timeline Slider | Visual history of state changes with one-click reset to last safe point. |
| Compliance Ledger | "Export for Auditor" Button | One-click PDF generation for EU/CA regulatory standards. |

---

## Feature 1: Confidence Scoring with Uncertainty Quantification

**Endpoint:** `POST /v2/validate`

**What it does:**
Instead of binary pass/fail, provides a 0–1 confidence score with risk level.

**Why it works:**
- Divergence 0.39 vs 0.41 are vastly different (barely safe vs barely dangerous)
- Operators need to see confidence intervals, not hard thresholds
- Enables "soft rejections" for borderline cases requiring manual review

**Logic:**
```
confidence = 1.0 - divergence - (0.15 × num_violations)
risk_level = GREEN (≥0.8) | YELLOW (0.5–0.8) | RED (<0.5)
```

**Dashboard example:**
```json
{
  "confidence": {
    "score": 0.65,
    "risk_level": "YELLOW",
    "explanation": "Moderate confidence. Manual review recommended."
  }
}
```

---

## Feature 2: Severity-Weighted Constraint Violations

**What it does:**
Rates violations by magnitude, not just occurrence.

**Why it works:**
- Leverage 11x (1% over limit) ≠ Leverage 100x (900% over limit)
- Enables triage: which violations need immediate action?
- Supports graduated responses (warn vs block)

**Logic:**
```
severity_pct = (|actual - limit| / limit) × 100%
weight = 1.0 (minor: <25%) | 2.0 (medium: 25-100%) | 4.0 (critical: >100%)
overall_severity = mean(weights)
```

**Dashboard example:**
```json
{
  "violation_severities": [
    {
      "name": "leverage_ratio",
      "severity_pct": 400.0,
      "weight": 4.0,
      "impact": "Critical violation: 400.0% over limit"
    }
  ],
  "overall_severity_score": 4.0
}
```

---

## Feature 3: Drift Detection & Historical Pattern Analysis

**Endpoint:** `GET /v2/health`

**What it does:**
Detects when LLM behavior shifts unexpectedly compared to historical patterns.

**Why it works:**
- LLMs degrade or change due to fine-tuning
- Same prompt should produce consistent divergence patterns
- Z-score > 2.5 flags anomalies (>2.5σ from normal)
- Enables proactive alerts before damage occurs

**Logic:**
```
z_score = (current_divergence - historical_mean) / std_dev
if |z_score| > 2.5: DRIFT DETECTED
```

**Dashboard example:**
```json
{
  "drift": {
    "detected": true,
    "z_score": 3.2,
    "historical_mean": 0.15,
    "current_value": 0.58,
    "explanation": "Drift detected! Model behavior has shifted significantly."
  }
}
```

---

## Dashboard-Ready Endpoints

### `/v2/validate` - Advanced Validation
Returns: `ValidationMetrics` (all three features)
```json
{
  "timestamp": "2026-02-13T12:34:56",
  "status_code": 424,
  "action": "BLOCK",
  "divergence_score": 0.42,
  "confidence": {...},
  "violation_severities": [...],
  "overall_severity_score": 3.5,
  "drift": {...},
  "recommendation": "CRITICAL: Leverage ratio 500% over limit"
}
```

### `/v2/health` - System Health
Returns: `HealthMetrics`
```json
{
  "uptime_requests": 247,
  "recent_divergence_avg": 0.22,
  "recent_violation_rate": 0.18,
  "drift_detected": false,
  "status": "HEALTHY"
}
```

---

## How to Wire a Dashboard

1. **Real-time updates:** Call `/v2/validate` on every AI output, stream results to UI
2. **Health monitoring:** Poll `/v2/health` every 5 seconds for dashboard status bar
3. **Charts:**
   - Divergence over time (divergence_score)
   - Risk distribution (confidence.risk_level breakdown)
   - Severity heatmap (violation_severities grouped by weight)
   - Drift timeline (historical_mean ± std_dev)
4. **Alerts:** Trigger when:
   - `action == "BLOCK"` → Stop execution, notify ops
   - `drift.detected == true` → Model degradation alert
   - `overall_severity_score > 3.0` → Critical risk alert

---

## Example Dashboard Widgets

```
┌─────────────────────────────────┐
│ WATCHER PROTOCAL CONTROL PANEL  │
├─────────────────────────────────┤
│                                 │
│ Status: HEALTHY ✓               │
│ Recent Divergence: 0.22         │
│ Violation Rate: 18%             │
│ Drift Alert: None               │
│                                 │
├─────────────────────────────────┤
│ Last 5 Requests:                │
│ ✓ ALLOW (conf: 0.92, GREEN)    │
│ ⚠ REVIEW (conf: 0.65, YELLOW)  │
│ ✓ ALLOW (conf: 0.88, GREEN)    │
│ ✗ BLOCK (sev: 4.0, CRITICAL)   │
│ ✓ ALLOW (conf: 0.85, GREEN)    │
│                                 │
├─────────────────────────────────┤
│ Severity Breakdown:              │
│ Critical: 2 │████  | 40%        │
│ Medium:   1 │██    | 20%        │
│ Minor:    2 │████  | 40%        │
│                                 │
└─────────────────────────────────┘
```
