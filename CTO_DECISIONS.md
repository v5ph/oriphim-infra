# ORIPHIM WATCHER PROTOCOL — CTO ARCHITECTURAL DECISIONS
Date: February 15, 2026
Decision Authority: CTO (Final — No Revisits)

═══════════════════════════════════════════════════════════════════════════════════════

## DECISION 1: TOPOLOGY — SDK-FIRST WITH OPTIONAL SIDECAR

**RULING: We are an SDK with optional Kubernetes sidecar for high-security environments.**

### Rationale:
- **Proxy = Non-Starter**: Banks will NEVER give us their SSL private keys. Period.
- **Sidecar-Only = Adoption Killer**: Doubles infrastructure complexity, scares away early adopters.
- **SDK = Control + Trust**: Client keeps keys, we provide the validation layer as imported code.

### Implementation:
```
Primary Mode: Python/Node/Go SDK
├─ Client imports: from oriphim import WatcherClient
├─ Client configures: watcher = WatcherClient(api_key="...")
├─ Client wraps LLM calls: watcher.validate(agent_output)
└─ Watcher returns: ALLOW/REVIEW/BLOCK + signed token

Enterprise Mode: Kubernetes Sidecar (Premium)
├─ Deploys as sidecar container in same pod as agent
├─ Intercepts localhost traffic (no SSL issues)
├─ Zero code changes for client (transparent proxy)
└─ Pricing: 3x base tier (infrastructure overhead justified)
```

### SSL Handling:
- SDK mode: Client owns TLS termination. We never see unencrypted traffic.
- Sidecar mode: Localhost proxy (127.0.0.1) = no TLS needed for inter-pod communication.
- Cloud SaaS API: Standard HTTPS to api.oriphim.com (our certs, not theirs).

### Decision Lock:
✓ Build Python SDK first (wraps existing /v3/intent endpoints)
✓ Sidecar ships in Q2 2026 (Kubernetes manifest + Docker image)
✗ Pure proxy mode = REJECTED (SSL trust model is broken)

---

## DECISION 2: FULFILLMENT HAND-OFF — SIGNED TOKEN MODEL (SCENARIO B+)

**RULING: We validate and issue a cryptographically signed approval token. Client executes the call.**

### Rationale:
- **Passthrough (Scenario A) = SPoF**: If OpenAI is down, Oriphim looks down. Unacceptable.
- **Token Without Enforcement = Bypassable**: Client can ignore the hash. Worthless.
- **Signed Token = Accountability**: Cryptographic proof that validation passed. Auditable.

### Flow:
```
1. Client → POST /v3/intent (agent_id, intent, samples)
2. Oriphim → Parallel validation (200ms max)
3. Oriphim → Returns signed JWT:
   {
     "request_id": "uuid-1234",
     "status": "APPROVED",
     "token": "eyJ0eXAiOi...",  ← Signed with our private key
     "expires_at": "2026-02-15T14:35:08Z",  ← 5min TTL
     "agent_id": "agent_biotech_A7",
     "action": "ALLOW"
   }
4. Client → Sends request to LLM with Oriphim-Token header
5. [Optional] LLM provider → Calls POST /v3/verify-token to validate signature
```

### Enforcement Strategy:
- **For Oriphim-Controlled Agents**: We refuse to execute without valid token.
- **For Client-Controlled Agents**: Token in audit log. If bypassed = contract violation + alert.
- **For LLM Providers (Future)**: Partner with OpenAI/Anthropic to reject unsigned requests.

### Uptime Separation:
- Oriphim SLA: 99.9% (validation layer)
- LLM Provider SLA: Their problem (OpenAI/Claude/etc.)
- Client sees two distinct failure modes (validation fail vs execution fail)

### Decision Lock:
✓ JWT signing with RS256 (private key rotates monthly)
✓ Token expiry: 5 minutes (prevents replay attacks)
✓ Verification endpoint: POST /v3/verify-token (for LLM partners)
✗ Passthrough mode = REJECTED (we don't own their uptime)

---

## DECISION 3: CUSTOM WORKFLOW INJECTION — DECLARATIVE YAML + WEBHOOK ESCAPE HATCH

**RULING: Clients define rules via YAML constraints. Complex logic = webhook callback to their service.**

### Rationale:
- **Code Upload = Security Nightmare**: Arbitrary Python/JS execution in our infra. Hell no.
- **Email-to-Update = Too Slow**: Kills self-service. Non-starter.
- **UI-Based DSL = Still Too Slow**: Forces non-technical users into our workflow.
- **YAML = Declarative + Safe**: No code execution. Easy to version control. Auditable.

### Configuration Protocol:
```yaml
# Client uploads: agent_biotech_A7.yaml
constraints:
  - name: "mass_balance"
    type: "physical"
    rule: "mass_in == mass_out"
    tolerance: 0.01
    severity: "critical"
  
  - name: "proprietary_trade_limit"
    type: "webhook"
    url: "https://internal.hedgefund.com/validate-trade"
    method: "POST"
    timeout_ms: 100
    headers:
      Authorization: "Bearer their-secret-key"
    payload:
      trade_size: "{{ agent.output.trade_size }}"
      symbol: "{{ agent.output.symbol }}"
    expect:
      status: 200
      body.approved: true
```

### Webhook Contract:
```
Client's internal service receives:
POST https://internal.hedgefund.com/validate-trade
Body: { "trade_size": 15000000, "symbol": "AAPL" }

Client responds:
{ "approved": false, "reason": "Exceeds daily position limit" }

Oriphim action:
→ BLOCK execution + log reason to audit trail
```

### Update Mechanism:
- Client pushes YAML to: POST /v3/config/{agent_id}
- Stored in DB, versioned (Git-style diffs)
- Takes effect immediately (no deploy needed)
- Rollback: POST /v3/config/{agent_id}/revert?version=42

### Decision Lock:
✓ YAML schema validation (JSON Schema enforced)
✓ Webhook timeout: 100ms max (fail fast)
✓ Sandbox: No shell commands, no file I/O, no network access (except webhook)
✗ Python/JS code execution = REJECTED (too risky)

---

## DECISION 4: LATENCY BUDGET — 50MS SYNC + 200MS ASYNC WITH CIRCUIT BREAKER

**RULING: Max 50ms overhead for critical path. Fail closed with circuit breaker escape valve.**

### Latency Budget:
```
Critical Path (Sync Validation):
├─ Semantic divergence check:     20ms  (embedding model)
├─ Hard constraint validation:     15ms  (PhysicalValidator)
├─ Confidence scoring:              5ms  (simple math)
├─ Response serialization:          5ms  (JSON encode)
└─ Network overhead:                5ms  (client ↔ Oriphim)
TOTAL:                             50ms  ← SLA guarantee

Parallel Path (Async Deep Validation):
├─ Rough draft simulation:        150ms  (background task)
├─ Drift detection:                30ms  (Z-score calculation)
├─ Severity weighting:             10ms  (violation analysis)
└─ Audit log write:                10ms  (DB insert)
TOTAL:                            200ms  ← Best effort, not blocking
```

### Timeout Handling:
```
Scenario 1: Parallel validation completes in <200ms
→ Result: Full metrics available immediately
→ Action: ALLOW/REVIEW/BLOCK based on complete data

Scenario 2: Parallel validation exceeds 200ms
→ Result: Latency guard triggers
→ Action: Return CAUTION status + run validation in background
→ Client behavior: Configurable (strict mode vs performance mode)

Scenario 3: Parallel validation hangs (>5 seconds)
→ Result: Task killed, marked as TIMEOUT
→ Action: Fail closed (BLOCK) + alert ops team
→ Fallback: Circuit breaker opens after 10% failure rate
```

### Circuit Breaker Logic:
```python
if failure_rate_last_60s > 0.10:  # 10% failures in 1 min
    circuit_state = "OPEN"
    action = "FAIL_OPEN"  # Allow requests through
    alert = "CRITICAL: Watcher validation degraded"
    
if circuit_state == "OPEN" and time_elapsed > 60s:
    circuit_state = "HALF_OPEN"
    # Test next 10 requests
    if success_rate > 0.90:
        circuit_state = "CLOSED"  # Resume normal operation
```

### Client Configuration:
```yaml
# Client specifies failure mode in SDK init:
watcher = WatcherClient(
    api_key="...",
    mode="strict",  # Options: strict | balanced | performance
)

Modes:
- strict:      Fail closed always (BLOCK on timeout)
- balanced:    Circuit breaker (fail closed → fail open after threshold)
- performance: Fail open on timeout (log + allow, async validation continues)
```

### High-Frequency Trading Exception:
For HFT clients (sub-10ms requirements):
- Option 1: Async-only mode (validate after execution, post-hoc audit)
- Option 2: Local SDK validation (no network call, pre-cached rules)
- Option 3: Don't use Oriphim (we're not built for HFT, be honest)

### Decision Lock:
✓ 50ms SLA for sync validation (99th percentile)
✓ 200ms latency guard with CAUTION fallback
✓ Circuit breaker: 10% failure rate in 60s window
✓ Client-configurable: strict/balanced/performance modes
✗ Zero-latency mode = IMPOSSIBLE (physics exists)

═══════════════════════════════════════════════════════════════════════════════════════

## IMPLEMENTATION ROADMAP (Feb 22 Launch)

### Day 1-2 (Feb 15-16): SDK Development
- [ ] Python SDK wrapper for /v3/intent + /v3/intent/{uuid}
- [ ] JWT signing for approval tokens (RS256)
- [ ] Circuit breaker implementation in middleware

### Day 3-4 (Feb 17-18): YAML Config System
- [ ] YAML parser for constraint definitions
- [ ] Webhook executor with 100ms timeout
- [ ] POST /v3/config/{agent_id} endpoint

### Day 5-6 (Feb 19-20): Latency Optimization
- [ ] Profile sync validation (target <50ms)
- [ ] Add metrics: p50, p95, p99 latency
- [ ] Circuit breaker testing under load

### Day 7 (Feb 21): Documentation + Demo Prep
- [ ] SDK quickstart guide
- [ ] YAML constraint examples
- [ ] Demo video: 424 block → JWT token → rewind

### Day 8 (Feb 22): LAUNCH
- [ ] SDK published to PyPI
- [ ] API docs live at docs.oriphim.com
- [ ] Email sequence: SDK integration guide

═══════════════════════════════════════════════════════════════════════════════════════

## REJECTED ALTERNATIVES (DO NOT REVISIT)

❌ Pure Proxy Mode → SSL trust model broken
❌ Passthrough Execution → Creates SPoF for client uptime
❌ Code Upload for Custom Rules → Security nightmare
❌ Zero-Latency Validation → Violates laws of physics
❌ "Support All Topologies" → Spreads team too thin, ships nothing

═══════════════════════════════════════════════════════════════════════════════════════

These decisions are FINAL. No committee reviews. No "let's revisit in Q2."
Ship the SDK. Launch on Feb 22. Iterate based on customer feedback.

— FOUNDER, Oriphim
