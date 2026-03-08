# ORIPHIM QUICK START - TESTING & CLIENT INTEGRATION

**Goal:** Get from zero to validated production integration in 30 minutes

---

## SETUP (5 minutes)

### 1. Install Dependencies
```bash
# Core dependencies
pip install -e .

# Testing dependencies
pip install pytest pytest-cov locust

# Verify installation
python -c "from app.main import app; print('✓ App imports successfully')"
```

### 2. Initialize Environment
```bash
# Generate secure environment
python scripts/setup/generate_env.py

# Initialize databases
python -c "from app.core.storage import init_db; from app.core.onboarding import init_onboarding_db; init_db(); init_onboarding_db()"

# Verify setup
make health-check
```

---

## TESTING (10 minutes)

### 1. Unit Tests
```bash
# Run existing tests (should pass)
make test

# Expected output:
# =================== test session starts ===================
# collected 20 items
# tests/test_hallucination_traps.py ............ [ 60%]
# tests/test_security_phase1.py ............ [100%]
# =================== 20 passed in 8.3s ====================
```

### 2. Integration Tests (NEW)
```bash
# Test API contracts
make test-integration

# Expected: 15+ tests pass
# Tests: /v2/validate, /v3/intent, /v3/rewind, /v2/health, multi-tenant isolation
```

### 3. End-to-End Tests (NEW)
```bash
# Test complete workflows
make test-e2e

# Expected: 5 scenarios pass
# Scenarios: Trading bot lifecycle, multi-tenant, HFT, incident response
```

### 4. Performance Tests (NEW)
```bash
# Start server
make server-start

# Run load test (1 minute, 50 concurrent users)
make test-performance

# Expected results:
# - P95 latency: <100ms
# - Throughput: >100 req/s
# - Error rate: <0.1%
```

### 5. Full Test Suite
```bash
# Run all tests with coverage
make test-all

# Generates: htmlcov/index.html (open in browser)
# Expected coverage: 80%+
```

---

## CLIENT INTEGRATION (10 minutes)

### Option A: Docker (Recommended for Quick Start)
```bash
# Start all services
make docker-up

# Wait 10 seconds for initialization

# Verify services
curl http://localhost:8000/v2/health

# View in browser:
# - Oriphim API: http://localhost:8000/docs (Swagger UI)
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

### Option B: Local Development
```bash
# Start server
make server-start

# In another terminal, verify
curl http://localhost:8000/v2/health | python -m json.tool
```

---

## SDK USAGE (5 minutes)

### 1. Create Tenant & Get API Key
```bash
# Create tenant
TENANT_RESPONSE=$(curl -X POST http://localhost:8000/v1/onboarding/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "org_name": "Test Corp",
    "domain": "testcorp.com",
    "support_tier": "premium"
  }')

TENANT_ID=$(echo $TENANT_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['tenant_id'])")

# Create user
USER_RESPONSE=$(curl -X POST http://localhost:8000/v1/onboarding/tenants/$TENANT_ID/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@testcorp.com",
    "role": "admin"
  }')

USER_ID=$(echo $USER_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['user_id'])")

# Generate API key
KEY_RESPONSE=$(curl -X POST http://localhost:8000/v1/onboarding/tenants/$TENANT_ID/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "admin",
    "expires_in_days": 90
  }')

API_KEY=$(echo $KEY_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['api_key'])")

echo "API Key: $API_KEY"
export ORIPHIM_API_KEY=$API_KEY
```

### 2. Test SDK Examples
```bash
# Set environment
export ORIPHIM_API_URL=http://localhost:8000
export ORIPHIM_API_KEY=<your-key-from-above>

# Run basic example
python client-sdk/python/examples/basic_usage.py

# Expected output:
# ===============================================================
# System Health: GREEN
# Status: HEALTHY
# ===============================================================
# Example 1: Basic Validation
# Indicator: GREEN
# Confidence: 0.95 (LOW)
# Action: ALLOW
# Reason: Safe to execute (confidence=0.95)
# ✓ Safe to execute
```

### 3. Test Async Example
```bash
python client-sdk/python/examples/async_usage.py

# Expected output:
# ===============================================================
# Example 1: Async Validation
# Submitted request: 550e8400-e29b-41d4-a716-446655440000
# Status: 200
# Action: ALLOW
# Latency: 68.34ms
```

---

## INTEGRATION TESTING (Real Client)

### Python Integration
```python
# test_client_integration.py
from oriphim import OriphimClient
import os

client = OriphimClient(
    base_url=os.getenv("ORIPHIM_API_URL"),
    api_key=os.getenv("ORIPHIM_API_KEY")
)

# Test 1: Validate AI output
result = client.validate(
    samples=[
        "Buy 100 shares of AAPL",
        "Purchase 100 AAPL shares",
        "Execute buy order: 100 AAPL"
    ],
    financial={"proposed_loss": -5000}
)

assert result.indicator in ["GREEN", "YELLOW", "RED"]
print(f"✓ Test 1 passed: {result.indicator}")

# Test 2: Trigger violation
result = client.validate(
    samples=["Risky trade"] * 3,
    financial={"proposed_loss": -15000}  # Exceeds $10k VaR
)

assert len(result.violations) > 0
print(f"✓ Test 2 passed: Blocked with {len(result.violations)} violations")

# Test 3: Agent rewind
request_id = client.submit_intent(
    agent_id="test-agent-001",
    intent="Test operation",
    samples=["Normal"] * 3,
    state_snapshot={
        "system_prompt": "Test state",
        "context": {},
        "variables": {}
    }
)

validation = client.wait_for_result(request_id)
snapshot = client.rewind_agent("test-agent-001")

assert snapshot.restored == True
print(f"✓ Test 3 passed: Agent restored")

print("\n✓ All integration tests passed")
```

Run:
```bash
python test_client_integration.py
```

---

## PRODUCTION DEPLOYMENT (Bonus)

### 1. Docker Compose (Staging)
```bash
# Edit .env for production secrets
cp .env .env.production
# Edit .env.production:
#   DATABASE_ENCRYPTION_KEY=<64-char-hex>
#   JWT_SECRET_KEY=<secure-random>
#   ENFORCE_HTTPS=true

# Deploy
docker-compose --env-file .env.production up -d

# Monitor
docker-compose logs -f
```

### 2. Health Check
```bash
# Automated health check (every 30s)
watch -n 30 'curl -s http://localhost:8000/v2/health | jq ".indicator"'

# Expected: GREEN
```

### 3. Load Testing (Before Production)
```bash
# Run 5-minute load test with 100 users
locust -f tests/performance/locustfile.py \
       --host http://localhost:8000 \
       --users 100 \
       --spawn-rate 10 \
       --run-time 5m \
       --headless \
       --csv=results/loadtest

# Review results
cat results/loadtest_stats.csv
```

---

## VERIFICATION CHECKLIST

### Testing ✓
- [ ] Unit tests pass (`make test`)
- [ ] Integration tests pass (`make test-integration`)
- [ ] E2E tests pass (`make test-e2e`)
- [ ] Performance tests pass (`make test-performance`)
- [ ] Coverage >80% (`make test-all`)

### Deployment ✓
- [ ] Docker Compose works (`make docker-up`)
- [ ] Health check returns GREEN
- [ ] All 3 services running (Oriphim, Prometheus, Grafana)

### Client Integration ✓
- [ ] SDK examples run without errors
- [ ] Can create tenant/user/API key
- [ ] Can validate AI outputs
- [ ] Can trigger 424 blocks
- [ ] Can rewind agent state
- [ ] Can export compliance PDF

### Production Readiness ✓
- [ ] HTTPS enabled (`ENFORCE_HTTPS=true`)
- [ ] Secrets in environment (not hardcoded)
- [ ] Database encrypted
- [ ] JWT tokens working
- [ ] Load test: P95 <100ms
- [ ] Load test: Error rate <0.1%

---

## TROUBLESHOOTING

### "ImportError: No module named 'app'"
```bash
pip install -e .
```

### "Connection refused"
```bash
# Check if server running
ps aux | grep uvicorn

# Start server
make server-start

# Or with Docker
make docker-up
```

### "API key invalid"
```bash
# Regenerate key
make key-generate TENANT=<tenant-id> USER=<user-id> SCOPE=admin

# Set environment
export ORIPHIM_API_KEY=<new-key>
```

### "Tests fail with database errors"
```bash
# Remove old database
rm .watcher_demo.db

# Reinitialize
python -c "from app.core.storage import init_db; from app.core.onboarding import init_onboarding_db; init_db(); init_onboarding_db()"
```

### "Performance test shows high latency"
```bash
# Check system resources
top

# Reduce concurrent users
locust -f tests/performance/locustfile.py --users 10 --run-time 1m

# Check if validation is slow (add debugging)
```

---

## NEXT STEPS

1. **Read the docs:**
   - [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - Complete testing guide
   - [CLIENT_INTEGRATION.md](./CLIENT_INTEGRATION.md) - Integration patterns
   - [TESTING_CLIENT_SUMMARY.md](./TESTING_CLIENT_SUMMARY.md) - Executive summary

2. **Customize SDK examples:**
   - Add your specific constraints
   - Integrate with your LLM
   - Add your business logic

3. **Set up CI/CD:**
   - See TESTING_STRATEGY.md section 8
   - GitHub Actions template included

4. **Production deployment:**
   - Kubernetes manifest (coming soon)
   - Multi-region setup (see CLIENT_INTEGRATION.md)

---

## SUPPORT

- **Documentation:** `docs/guides/`
- **Examples:** `client-sdk/python/examples/`
- **Tests:** Run `make test-all` to see all test patterns

---

**Total time:** 30 minutes ✓

**Status:** Production-ready testing and client integration infrastructure complete
