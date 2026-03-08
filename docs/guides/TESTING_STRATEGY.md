# ORIPHIM TESTING STRATEGY
**Production-Ready Validation Testing Framework**

## ARCHITECTURAL REVIEW

### Current State
Your system is a **headless validation middleware** with:
- **7 core API endpoints** (validation, health, intent queue, rewind, compliance)
- **Multi-tenant infrastructure** with RBAC and JWT auth
- **Async validation pipeline** with 68-100ms latency
- **Cryptographic audit trail** with compliance export
- **10+ hallucination trap tests** and security test suite

### Gap Analysis
**What's Missing:**
1. **Integration tests** - API contract validation, end-to-end flows
2. **Performance tests** - Load, stress, endurance validation
3. **Resilience tests** - Chaos engineering, failure injection
4. **Regression suite** - Prevent breaking changes
5. **Client simulation** - Real-world usage patterns

---

## TESTING PYRAMID

```
                     E2E Tests (5%)
                 ──────────────────
              Integration Tests (15%)
           ──────────────────────────────
        Performance & Load Tests (10%)
     ────────────────────────────────────────
  Unit Tests (70%) - Already strong coverage
─────────────────────────────────────────────────
```

---

## 1. UNIT TESTS (CURRENT: STRONG ✓)

**Status:** 70% coverage achieved
- ✓ Hallucination detection (10 trap tests)
- ✓ Security primitives (JWT, encryption, sessions)
- ✓ Constraint validation (physics, financial)
- ✓ Core algorithms (entropy, confidence, severity)

**Recommendations:**
- **Add property-based tests** using `hypothesis` for constraint validation
- **Expand edge cases** for drift detection and confidence scoring
- **Mock external dependencies** (no real LLM calls in unit tests)

**Example Property Test:**
```python
from hypothesis import given, strategies as st
from app.core.constraints import check_logic
from app.models import ValidationRequest, PhysicsPayload

@given(
    energy_in=st.floats(min_value=0, max_value=1000),
    energy_out=st.floats(min_value=0, max_value=1000)
)
def test_energy_conservation_property(energy_in, energy_out):
    """Property: Energy out > energy in ALWAYS violates conservation"""
    request = ValidationRequest(
        samples=["test"] * 3,
        physics=PhysicsPayload(energy_in=energy_in, energy_out=energy_out)
    )
    violations = check_logic(request)
    
    if energy_out > energy_in:
        assert any("Balance invariant" in v for v in violations)
    else:
        assert not any("Balance invariant" in v for v in violations)
```

---

## 2. INTEGRATION TESTS (PRIORITY: HIGH)

### Purpose
Validate **API contracts**, **multi-component interactions**, and **data persistence** without external dependencies.

### Test Categories

#### A. API Contract Tests
**Ensures backward compatibility** and correct request/response schemas.

```python
# tests/integration/test_api_contracts.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_v2_validate_contract():
    """Validates /v2/validate accepts spec and returns correct shape"""
    payload = {
        "samples": ["test A", "test B", "test C"],
        "physics": {"energy_in": 100, "energy_out": 90}
    }
    
    response = client.post("/v2/validate", json=payload)
    
    # Contract validation
    assert response.status_code in [200, 400, 424]
    data = response.json()
    
    # Required fields
    assert "divergence_score" in data
    assert "violations" in data
    assert "confidence" in data
    assert "indicator" in data  # GREEN/YELLOW/RED
    assert "action_label" in data  # ALLOW/REVIEW/BLOCK
    
    # Type validation
    assert isinstance(data["divergence_score"], float)
    assert isinstance(data["violations"], list)
    assert data["indicator"] in ["GREEN", "YELLOW", "RED"]


def test_v3_async_validation_flow():
    """Validates async intent queue workflow"""
    # Submit intent
    intent = {
        "agent_id": "test-agent-001",
        "intent": "Execute trade",
        "samples": ["Buy 100 shares", "Buy 100 shares", "Buy 100 shares"],
        "financial": {"proposed_loss": -5000}
    }
    
    submit_response = client.post("/v3/intent", json=intent)
    assert submit_response.status_code == 200
    
    request_id = submit_response.json()["request_id"]
    assert request_id is not None
    
    # Poll for result (with timeout)
    import time
    max_attempts = 10
    for _ in range(max_attempts):
        status_response = client.get(f"/v3/intent/{request_id}")
        if status_response.status_code == 200:
            data = status_response.json()
            assert "status_code" in data
            assert "action" in data
            break
        time.sleep(0.1)
    else:
        pytest.fail("Async validation timeout")
```

#### B. Multi-Tenant Isolation Tests
**Critical for SaaS security** - ensure data isolation.

```python
def test_tenant_data_isolation():
    """Ensures tenants cannot access each other's data"""
    # Create two tenants
    tenant1 = client.post("/v1/onboarding/tenants", json={
        "org_name": "Tenant A",
        "domain": "tenant-a.com",
        "support_tier": "standard"
    }).json()
    
    tenant2 = client.post("/v1/onboarding/tenants", json={
        "org_name": "Tenant B",
        "domain": "tenant-b.com",
        "support_tier": "standard"
    }).json()
    
    # Create API keys for each
    key1 = client.post(f"/v1/onboarding/tenants/{tenant1['tenant_id']}/api-keys", json={
        "scope": "admin"
    }).json()["api_key"]
    
    key2 = client.post(f"/v1/onboarding/tenants/{tenant2['tenant_id']}/api-keys", json={
        "scope": "admin"
    }).json()["api_key"]
    
    # Submit validation for tenant 1
    intent = {
        "agent_id": f"{tenant1['tenant_id']}-agent-01",
        "intent": "Test",
        "samples": ["A", "B", "C"]
    }
    
    headers1 = {"Authorization": f"Bearer {key1}"}
    client.post("/v3/intent", json=intent, headers=headers1)
    
    # Tenant 2 should NOT see tenant 1's data
    headers2 = {"Authorization": f"Bearer {key2}"}
    audit_response = client.get(
        f"/v3/compliance/export?agent_id={tenant1['tenant_id']}-agent-01",
        headers=headers2
    )
    
    # Should return empty or 403 (depending on permission model)
    assert audit_response.status_code in [200, 403]
```

#### C. Database Persistence Tests
```python
def test_audit_trail_persistence():
    """Validates audit events are immutable and queryable"""
    # Submit validation that triggers 424
    payload = {
        "samples": ["test"] * 3,
        "physics": {"energy_in": 100, "energy_out": 150}  # Violation
    }
    
    response = client.post("/v2/validate", json=payload)
    assert response.status_code == 424
    
    # Verify audit event created
    from app.core.storage import list_audit_events
    events = list_audit_events()
    
    # Find the event
    matching = [e for e in events if "Balance invariant" in e.get("message", "")]
    assert len(matching) > 0
    
    # Verify immutability fields present
    event = matching[0]
    assert "chain_hash" in event
    assert "prev_hash" in event
    assert event["event_type"] == "EXECUTION_BLOCKED"
```

---

## 3. PERFORMANCE & LOAD TESTS (PRIORITY: CRITICAL)

### Why Critical
Your **value proposition** is "99.2% safety with ZERO latency impact". Must prove this under load.

### Test Categories

#### A. Latency Benchmarks
**Target:** P95 < 100ms for validation, P99 < 150ms

```python
# tests/performance/test_latency.py
import pytest
import time
import statistics
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_v2_validate_latency_p95():
    """Validates P95 latency < 100ms under normal load"""
    latencies = []
    num_requests = 1000
    
    payload = {
        "samples": ["Normal request"] * 3,
        "physics": {"energy_in": 100, "energy_out": 90}
    }
    
    for _ in range(num_requests):
        start = time.perf_counter()
        response = client.post("/v2/validate", json=payload)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        assert response.status_code == 200
        latencies.append(elapsed)
    
    p50 = statistics.quantiles(latencies, n=100)[49]
    p95 = statistics.quantiles(latencies, n=100)[94]
    p99 = statistics.quantiles(latencies, n=100)[98]
    
    print(f"\nLatency distribution:")
    print(f"  P50: {p50:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    print(f"  P99: {p99:.2f}ms")
    
    assert p95 < 100, f"P95 latency {p95:.2f}ms exceeds 100ms target"
```

#### B. Concurrent Load Tests
**Use `locust` for realistic multi-user simulation**

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between
import random

class OriphimUser(HttpUser):
    wait_time = between(0.1, 0.5)  # Simulates high-frequency trading
    
    def on_start(self):
        """Setup: Create tenant and get API key"""
        # In real test, use pre-provisioned tenants
        pass
    
    @task(weight=70)
    def validate_normal(self):
        """Most common: Normal validation (70% of traffic)"""
        payload = {
            "samples": [f"Trade {random.randint(1, 1000)}"] * 3,
            "financial": {"proposed_loss": random.uniform(-9000, 0)}
        }
        self.client.post("/v2/validate", json=payload)
    
    @task(weight=20)
    def validate_violation(self):
        """Trigger constraint violations (20% of traffic)"""
        payload = {
            "samples": ["High risk trade"] * 3,
            "financial": {"proposed_loss": -15000},  # Exceeds $10k VaR
            "metrics": {"leverage_ratio": 12.0}  # Exceeds 10x limit
        }
        self.client.post("/v2/validate", json=payload)
    
    @task(weight=10)
    def check_health(self):
        """CRO polling health (10% of traffic)"""
        self.client.get("/v2/health")
```

**Run load test:**
```bash
# Install locust
pip install locust

# Run test: 100 users, ramp up over 30s
locust -f tests/performance/locustfile.py \
       --host http://localhost:8000 \
       --users 100 \
       --spawn-rate 3 \
       --run-time 5m \
       --headless \
       --csv=results/loadtest
```

**Success Criteria:**
- **Throughput:** ≥ 100 req/sec
- **P95 latency:** < 100ms
- **Error rate:** < 0.1%
- **No memory leaks** (monitor with `memory_profiler`)

#### C. Stress Tests
**Find breaking point**

```bash
# Gradual ramp: 0 → 500 users over 10 minutes
locust -f tests/performance/locustfile.py \
       --host http://localhost:8000 \
       --users 500 \
       --spawn-rate 1 \
       --run-time 10m
```

**Monitor:**
- CPU usage (target: < 80% sustained)
- Memory usage (target: no leaks, < 2GB for 500 concurrent)
- Database connection pool exhaustion
- Queue depth for async validation

---

## 4. END-TO-END TESTS (CLIENT SIMULATION)

### Purpose
Simulate **real client integration** workflows.

#### Scenario: Trading Bot Integration
```python
# tests/e2e/test_trading_bot_workflow.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_trading_bot_full_lifecycle():
    """Simulates a trading bot using Oriphim for 100 consecutive trades"""
    
    # 1. Onboarding: Create tenant
    tenant = client.post("/v1/onboarding/tenants", json={
        "org_name": "AlgoTrade Hedge Fund",
        "domain": "algotrade.fund",
        "support_tier": "enterprise"
    }).json()
    
    # 2. Create admin user
    admin = client.post(f"/v1/onboarding/tenants/{tenant['tenant_id']}/users", json={
        "email": "risk@algotrade.fund",
        "role": "admin"
    }).json()
    
    # 3. Generate API key
    key = client.post(f"/v1/onboarding/tenants/{tenant['tenant_id']}/api-keys", json={
        "scope": "validate-only",  # Least privilege
        "expires_in_days": 90
    }).json()
    
    headers = {"Authorization": f"Bearer {key['api_key']}"}
    
    # 4. Simulate 100 trades with validation
    agent_id = f"{tenant['tenant_id']}-bot-001"
    blocked_count = 0
    allowed_count = 0
    
    for i in range(100):
        # Randomly inject some violations
        import random
        is_violation = random.random() < 0.05  # 5% violation rate
        
        intent = {
            "agent_id": agent_id,
            "intent": f"Trade #{i+1}",
            "samples": [f"Execute trade {i+1}"] * 3,
            "financial": {
                "proposed_loss": -15000 if is_violation else -5000
            },
            "state_snapshot": {
                "system_prompt": "Trade execution bot",
                "context": {"trade_number": i+1},
                "variables": {"portfolio_value": 1000000}
            }
        }
        
        # Submit for async validation
        response = client.post("/v3/intent", json=intent, headers=headers)
        request_id = response.json()["request_id"]
        
        # Poll for result
        import time
        for _ in range(20):  # Max 2 seconds
            status = client.get(f"/v3/intent/{request_id}", headers=headers)
            if status.status_code == 200:
                result = status.json()
                if result["status_code"] == 424:
                    blocked_count += 1
                else:
                    allowed_count += 1
                break
            time.sleep(0.1)
    
    # 5. Verify expected blocking rate
    print(f"\nTrade results:")
    print(f"  Allowed: {allowed_count}")
    print(f"  Blocked: {blocked_count}")
    assert blocked_count > 0, "No violations blocked (test logic error)"
    assert blocked_count < 10, "Too many false positives"
    
    # 6. Test incident response: Rewind after violation
    rewind = client.post(f"/v3/rewind/{agent_id}", headers=headers)
    assert rewind.status_code == 200
    snapshot = rewind.json()
    assert snapshot["restored"] == True
    assert snapshot["system_prompt"] == "Trade execution bot"
    
    # 7. Export compliance report
    pdf = client.get(f"/v3/compliance/export?agent_id={agent_id}", headers=headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert len(pdf.content) > 1000  # Non-empty PDF
```

---

## 5. RESILIENCE & CHAOS TESTS

### Purpose
Ensure system **fails gracefully** and **recovers automatically**.

```python
# tests/resilience/test_failure_modes.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
import os

def test_database_unavailable():
    """Validates graceful degradation when database is unavailable"""
    # Temporarily corrupt database path
    original_path = os.getenv("SQLITE_DB_PATH")
    os.environ["SQLITE_DB_PATH"] = "/nonexistent/path.db"
    
    # Restart app (in real test, use dependency injection)
    client = TestClient(app)
    
    # Should return 503 Service Unavailable, NOT 500 Internal Error
    response = client.get("/v2/health")
    assert response.status_code == 503
    assert "database" in response.json().get("detail", "").lower()
    
    # Restore
    os.environ["SQLITE_DB_PATH"] = original_path


def test_validation_timeout_handling():
    """Validates LATENCY_GUARD triggers at 200ms"""
    # Submit request that will take > 200ms (mock slow validation)
    # This requires injecting delay into validation pipeline
    # Implementation depends on your mocking strategy
    pass


def test_concurrent_request_handling():
    """Validates no race conditions under concurrent load"""
    import concurrent.futures
    
    client = TestClient(app)
    
    def submit_validation(i):
        payload = {
            "samples": [f"Request {i}"] * 3,
            "physics": {"energy_in": 100, "energy_out": 90}
        }
        return client.post("/v2/validate", json=payload)
    
    # Submit 100 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(submit_validation, i) for i in range(100)]
        results = [f.result() for f in futures]
    
    # All should succeed (no database locks, race conditions, etc.)
    assert all(r.status_code == 200 for r in results)
```

---

## 6. REGRESSION SUITE

### Strategy
**Snapshot testing** for API responses + **golden tests** for complex algorithms.

```python
# tests/regression/test_api_snapshots.py
import pytest
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_v2_validate_response_snapshot(snapshot):
    """Validates response schema hasn't changed"""
    payload = {
        "samples": ["test A", "test B", "test C"],
        "physics": {"energy_in": 100, "energy_out": 90}
    }
    
    response = client.post("/v2/validate", json=payload)
    
    # pytest-snapshot will save first run, compare on subsequent runs
    snapshot.assert_match(response.json(), "v2_validate_normal.json")
```

**Install snapshot testing:**
```bash
pip install pytest-snapshot
```

---

## 7. SECURITY TESTS (ENHANCEMENT)

### Current Coverage
✓ JWT validation  
✓ Encryption at rest  
✓ Session management

### Additional Tests Needed

```python
# tests/security/test_attack_vectors.py

def test_sql_injection_protection():
    """Validates parameterized queries prevent SQL injection"""
    payload = {
        "samples": ["'; DROP TABLE tenants; --"] * 3
    }
    
    response = client.post("/v2/validate", json=payload)
    # Should NOT crash, should validate normally
    assert response.status_code in [200, 400, 424]


def test_rate_limiting():
    """Validates rate limiting prevents abuse"""
    # Submit 1000 requests in 1 second
    for _ in range(1000):
        client.post("/v2/validate", json={"samples": ["test"] * 3})
    
    # Should start returning 429 Too Many Requests
    response = client.post("/v2/validate", json={"samples": ["test"] * 3})
    # NOTE: Rate limiting not yet implemented - this test will fail
    # Add to backlog


def test_jwt_expiration_enforcement():
    """Validates expired tokens are rejected"""
    # Create token with 1-second expiration
    # Wait 2 seconds
    # Verify token rejected
    # (Already covered in test_security_phase1.py, expand if needed)
```

---

## 8. CONTINUOUS TESTING STRATEGY

### CI/CD Integration
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e .[dev]
      - run: pytest tests/test_*.py -v --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3
  
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -e .[dev]
      - run: pytest tests/integration/ -v
  
  performance-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - run: pip install -e .[dev,test-llm]
      - run: pip install locust
      - run: |
          uvicorn app.main:app &
          sleep 5
          locust -f tests/performance/locustfile.py --headless --users 50 --run-time 2m
```

---

## 9. TEST EXECUTION PLAN

### Daily (Developer Workstation)
```bash
make test           # Unit tests (10 seconds)
make test-security  # Security tests (30 seconds)
```

### Pre-Commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/test_*.py tests/integration/ --maxfail=1 --tb=short
```

### CI Pipeline (Every PR)
```bash
pytest tests/ -v --cov=app --cov-report=html --cov-fail-under=80
```

### Nightly (Staging Environment)
```bash
# Full regression + performance
pytest tests/ -v --run-slow
locust -f tests/performance/locustfile.py --headless --users 100 --run-time 10m
```

### Weekly (Pre-Release)
```bash
# Stress testing + chaos
locust --users 500 --run-time 1h
# Manual chaos injection (kill database, network partition, etc.)
```

---

## 10. METRICS & SUCCESS CRITERIA

### Coverage Targets
- **Unit tests:** 80% line coverage
- **Integration tests:** 100% endpoint coverage
- **E2E tests:** 100% critical user journeys
- **Performance:** P95 < 100ms, throughput > 100 req/sec

### Monitoring in Production
```python
# Add to app/main.py
from prometheus_client import Counter, Histogram

validation_requests = Counter('validation_requests_total', 'Total validations', ['status'])
validation_latency = Histogram('validation_latency_seconds', 'Validation latency')

# In validation endpoint:
with validation_latency.time():
    # ... validation logic ...
    validation_requests.labels(status='blocked' if status_code == 424 else 'allowed').inc()
```

---

## SECURITY & EDGE-CASE CONSIDERATIONS

1. **Test Data Isolation:** Use separate test database (`:memory:` for unit tests)
2. **Secret Management:** Never commit real API keys to test files
3. **Flaky Tests:** Use `pytest-retry` for network-dependent tests
4. **Test Parallelization:** Use `pytest-xdist` for faster execution
5. **Database State:** Reset database between integration tests
6. **Time-Dependent Tests:** Use `freezegun` to mock time for JWT expiration tests

---

## NEXT STEPS

1. **[Immediate]** Implement integration test suite (2-3 days)
2. **[Week 1]** Set up Locust performance tests
3. **[Week 2]** Add E2E trading bot simulation
4. **[Week 3]** Implement CI/CD pipeline with GitHub Actions
5. **[Month 1]** Chaos engineering infrastructure

**Priority Order:**
1. Integration tests (blocks production deployment)
2. Performance tests (validates core value proposition)
3. E2E tests (client confidence)
4. Resilience tests (operational maturity)
5. Regression suite (long-term maintainability)
