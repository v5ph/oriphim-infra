# Oriphim SaaS Infra Edge Case Priority Register

Purpose: prioritized edge-case inventory for the current end-to-end architecture.

Priority scale:
- P4: Lowest priority
- P3: Low-medium priority
- P2: Medium priority
- P1: High priority
- P0: Top priority

Ordering below is from least priority to top priority.

---

## P4 - Lowest Priority

These issues matter, but they are least likely to cause immediate security, compliance, or capital-loss events.

### UX / Operational Friction
- Per-IP rate limit punishes NAT'ed enterprise users unfairly.
- Health endpoint returns green while downstream storage degraded.
- Mixed HTTP/HTTPS health checks fail due to strict redirect policy.
- High-cardinality labels explode metrics storage.
- Alert thresholds too sensitive cause alert fatigue and ignored incidents.
- Metrics scrape failure interpreted as zero risk.
- CORS allowlist mismatch between Origin and Host behind reverse proxies.
- Preflight OPTIONS requests rate-limited or blocked incorrectly.
- Request ID collision under high concurrency.
- Simulation IDs collide on high-throughput runs.
- Drift/alarm suppression during deploy is never re-enabled.
- Sandbox market latency differs too much from production path.
- Policy timeline omits short-lived block events due to coarse sampling.

### Reporting / Export / Evidence Quality
- PDF export times out on large audit windows.
- Compliance export PDF generated with formatting issues on large ledgers.
- Replay data gaps produce unrealistic smooth PnL.
- Corporate actions in replay are not adjusted correctly.
- Drift/anomaly counters reset unexpectedly on long runs.
- Health check only probes process, not dependencies.

### Non-Critical Runtime Edge Cases
- Large headers trigger 431/400 and bypass structured exception formatting.
- Security headers overwritten by upstream proxy.
- Multiple proxies produce comma-separated IP chains parsed incorrectly.
- IPv6 and IPv4 treated as distinct identities for the same caller.
- Burst traffic across many IPs bypasses simple per-IP quotas.
- Time sync drift across hosts breaks event chronology in logs and traces.

---

## P3 - Low-Medium Priority

These can degrade reliability or produce misleading behavior, but usually do not directly create an immediate loss or hard compliance incident.

### Validation / Async Workflow Reliability
- Same payload yields different verdict across v1, v2, and v3.
- Confidence or severity score becomes NaN, negative, or greater than expected bounds.
- Drift indicator computed on empty or sparse history.
- Action reason missing while decision is MODIFY or BLOCK.
- Async intent accepted but worker queue unavailable.
- Intent status stuck in pending due to crash between state transitions.
- Duplicate intent IDs on retry without idempotency key.
- Simulation report stored before all policy events are finalized.
- Random seed not fixed, making simulation non-reproducible.
- Out-of-order events in replay stream alter policy outcomes.
- Strategy uses future leak from simulation metadata.

### Identity / Access Edge Cases
- Duplicate tenant names with Unicode confusables.
- Tenant creation race causes duplicate logical tenants.
- User created without tenant binding due to partial transaction.
- Role change race during active request authorization check.
- Tenant admin deletes last admin account and causes lockout.
- Identity audit entries logged without actor context for service-to-service calls.

### Broker / Adapter Reliability
- Exchange maintenance windows return non-standard error formats.
- Broker sandbox and production credentials are mixed in environment.
- Broker clock mismatch breaks nonce or signature validation.
- Symbol mapping mismatch such as BTCUSD vs XBTUSD.
- Decimal precision truncation changes order values unexpectedly.
- Circuit breaker opens globally when only one broker is degraded.

### Persistence / Runtime
- WAL checkpoint stalls cause latency spikes.
- JSON columns store incompatible schema versions.
- Backup restore loses indexes or foreign key enforcement.
- Migration order mismatch in multi-instance deploy.
- Dependency update changes tokenizer or model behavior silently.

---

## P2 - Medium Priority

These create meaningful reliability, auditability, or policy-integrity risk and can become severe under load or during incidents.

### Gateway / Security Robustness
- X-Forwarded-For spoofing causes wrong client IP for rate limiting.
- HTTPS enforcement loops when TLS terminates at load balancer.
- Missing or duplicated request IDs across async tasks and retries.
- Slowloris or partial body requests exhaust worker slots.
- Chunked transfer with malformed boundaries bypasses body validators.
- Clock skew between nodes causes inconsistent JWT expiry behavior.
- Password reset or login brute-force distributed across IP pools evades per-IP limits.

### Auth / Session / Key Management
- API key generated but not returned due to response failure, leaving an orphaned valid secret.
- API key revoke eventual consistency delay allows short post-revoke use.
- Logout on one device invalidates all sessions unexpectedly, or not at all.
- Expired access token accepted due to leeway misconfiguration.
- nbf token claims fail under negative clock skew.
- JWT refresh replay from two devices simultaneously.

### Observability / Auditability
- Request ID missing in background worker logs.
- Audit events arrive out of order under async pipelines.
- Tracing sampling drops rare but critical BLOCK paths.
- Log redaction misses secrets in nested JSON.
- Compliance evidence cannot be reconstructed end-to-end from stored artifacts.

### Trade Guard / Policy Integrity
- Z-score anomaly detector is unstable with very small sample sizes.
- Dynamic kill switch flip-flops from noisy indicators.
- Restricted instrument list update is delayed in in-memory cache.
- Capital allocation constraints double-count across strategies.
- Pre-trade decision lookup returns stale decision after policy version update.
- Manual override lacks reason code or immutable audit context.

### Simulation / Analysis
- Massive scenario matrices exhaust memory or CPU.
- Policy trigger simulation omits transient trigger windows.
- Drawdown path modeling diverges from actual execution chronology.

### Storage / Evidence Durability
- DB file corruption after abrupt container shutdown.
- Auto-vacuum or retention policy purges records needed for compliance.
- Disk-full condition causes silent partial writes.
- Snapshot and audit rows are committed in separate transactions, producing inconsistent evidence.

### Ops / Delivery
- Docker Compose startup order allows API to start before migrations finish.
- Blue/green deploy with mixed policy versions alters decisions across requests.
- Different environment values between API and workers create policy split-brain.
- Multi-tenant noisy neighbor behavior impacts latency and policy accuracy.
- Backpressure is not propagated, causing queue buildup and cascading timeouts.

---

## P1 - High Priority

These can directly lead to materially wrong decisions, missing controls, or incorrect system state under real market conditions.

### Trade Guard / Financial Control Failures
- Max daily loss is computed in the wrong timezone or day boundary.
- Position size checks ignore pending or unsettled orders.
- Leverage limits are calculated with stale market prices.
- Trading frequency cap races when parallel orders arrive in the same millisecond.
- MODIFY decision produces an invalid order due to tick size or min lot rules.
- Policy conflict exists between ALLOW and BLOCK without deterministic precedence.
- Decision persistence succeeds but response fails; client retries and duplicates.
- Partial fills breach limits after initial ALLOW.
- Broker rejects modified order and fallback accidentally executes the original order.

### Validation / State Recovery
- Rewind restores snapshot from the wrong tenant or wrong agent.
- Rewind target snapshot is corrupted or schema-mismatched.
- Non-deterministic model behavior makes audit replay fail reproducibility.
- Validation request with oversized payload bypasses the normal guard path.

### Broker / Execution
- Broker ACK times out but order was actually accepted, leaving unknown execution state.
- Cancel/replace race leads to overfilled position.
- Partial broker outage causes asymmetric multi-leg execution.
- Webhook callback authenticity is not verified.
- External execution retries happen without strong idempotency protection.

### Persistence / Multi-Tenant Integrity
- SQLite write-lock contention under concurrent API writes breaks decision durability.
- Tenant data leakage via one missing WHERE tenant_id path.
- Hash-chain immutability breaks due to out-of-band row updates.
- SQLCipher key rotation without a controlled rekey plan causes downtime or inaccessible data.

### Ops / Runtime
- Daylight savings transition breaks daily-loss reset logic.
- Leap-second or time anomaly breaks expiry and replay ordering.
- Env var missing defaults the service into insecure mode.
- Test fixtures are reused in a production-like environment by mistake.

---

## P0 - Top Priority

These are the most critical edge cases because they can cause unauthorized execution, irreversible capital loss, cross-tenant breach, compliance failure, or a broken chain of evidence.

### Unauthorized Execution / Exactly-Once Failures
- Exactly-once semantics are missing across validate -> decide -> execute.
- Retry on network error duplicates a real trade without an idempotency token.
- Partial failure occurs between audit write and external side effect.
- Inconsistent policy version is used across a single request lifecycle.
- External broker state and internal decision state diverge with no safe reconciliation.
- Unknown-state execution is treated as failed and resubmitted.

### Cross-Tenant / Security / Access Control
- Cross-tenant object ID guessing leaks metadata through timing or error differences.
- Compliance export PDF is generated for an unauthorized tenant.
- Tenant-scoping safeguards are missing in CLI admin commands.
- Error responses leak internal rule names, stack traces, or sensitive details.
- Secrets appear in build logs or container inspect output.
- API key hash comparison is not constant-time.

### Compliance / Audit Immutability
- Identity audit chain breaks on rollback or restore operations.
- Audit chain is not preserved consistently across restores, migrations, or replay.
- Immutable audit evidence cannot prove end-to-end sequence of validate, decide, and execute.
- Out-of-band database mutation invalidates evidence without detection.

### Hard Financial Risk Controls
- Dynamic kill switch fails to trigger when required.
- Restricted instrument checks are bypassed due to stale cache or symbol mapping issues.
- Capital allocation limits fail across strategies or accounts and allow overexposure.
- Daily loss guard resets incorrectly and permits continued trading after breach.
- Frequency, leverage, and position-size controls can all be bypassed by concurrency races.
- Policy engine allows original order execution after a MODIFY or REVIEW path fails.

### Recovery / Security Boundary Failures
- Rewind restores an invalid but internally trusted snapshot and resumes trading from it.
- Broker sandbox and production environments are crossed and live orders are sent unintentionally.
- Service-to-service actors perform privileged actions without auditable identity.
- Distributed brute-force or replay behavior bypasses simple per-IP or per-session protections.

---

## Suggested Testing Order

### Phase 1 - Must Test First
- P0 exactly-once execution paths
- P0 tenant isolation and unauthorized export/access paths
- P0 audit-chain integrity and evidence reconstruction
- P0 kill switch, restricted instruments, and capital guard bypass cases
- P1 concurrency races in pre-trade controls
- P1 broker unknown-state and cancel/replace flows

### Phase 2 - Next
- P2 auth/session/key lifecycle race conditions
- P2 async intent and worker crash recovery
- P2 disk-full, lock contention, and transaction consistency
- P2 observability gaps that block incident response

### Phase 3 - Last
- P3 simulation realism and reporting drift
- P3 lower-impact broker mapping and ops edge cases
- P4 UX, reporting scalability, and metrics quality issues 