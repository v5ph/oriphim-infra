# ORIPHIM CLIENT INTEGRATION GUIDE
**Production-Ready Integration Patterns for AI Safety Middleware**

## ARCHITECTURAL REVIEW

### Design Philosophy
Oriphim is **headless middleware** - it has NO user interface. Clients integrate via:
1. **REST API** (7 core endpoints)
2. **SDK libraries** (Python, TypeScript, Go planned)
3. **Webhook callbacks** (for async validation notifications)
4. **CLI tools** (for operations/monitoring)

### Client Integration Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                  CLIENT APPLICATIONS                        │
│  (Trading Bot, Risk Dashboard, Agent Framework)             │
└──────────────┬──────────────────────────────────────────────┘
               │
               │ Integration Options:
               │
    ┌──────────┼──────────┬──────────────┬─────────────┐
    │          │          │              │             │
    ▼          ▼          ▼              ▼             ▼
┌──────┐  ┌──────┐  ┌──────────┐  ┌──────────┐  ┌────────┐
│HTTP  │  │Python│  │TypeScript│  │Webhooks  │  │ CLI    │
│API   │  │SDK   │  │SDK       │  │(async)   │  │Tools   │
└──┬───┘  └──┬───┘  └────┬─────┘  └─────┬────┘  └───┬────┘
   │         │           │              │           │
   └─────────┴───────────┴──────────────┴───────────┘
                         │
              ┌──────────▼──────────┐
              │  ORIPHIM WATCHER    │
              │  (FastAPI Backend)  │
              └─────────────────────┘
```

---

## 1. DIRECT REST API INTEGRATION

### Use Case
- **Quick prototyping**
- **Non-Python clients** (Java, C#, Go, etc.)
- **Serverless functions** (AWS Lambda, Cloudflare Workers)

### Synchronous Validation (Simple)
```python
import requests

# Step 1: Validate AI output
payload = {
    "samples": [
        "Buy 100 shares of AAPL",
        "Purchase 100 AAPL shares",
        "Execute buy order: 100 AAPL"
    ],
    "financial": {
        "proposed_loss": -5000  # Risk of losing $5k
    },
    "metrics": {
        "leverage_ratio": 3.0  # 3x leverage
    }
}

response = requests.post(
    "http://localhost:8000/v2/validate",
    json=payload,
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    timeout=2.0  # Critical: Set timeout
)

# Step 2: Check indicator (GREEN/YELLOW/RED)
if response.status_code == 200:
    result = response.json()
    indicator = result["indicator"]  # GREEN, YELLOW, or RED
    
    if indicator == "GREEN":
        print("✓ Safe to execute")
        # Execute trade
    elif indicator == "YELLOW":
        print("⚠ Manual review recommended")
        # Route to human
    else:  # RED
        print("✗ BLOCKED - High risk")
        # Do NOT execute
        
elif response.status_code == 424:
    # CRITICAL: Hard constraint violated
    print("✗ 424 SENTINEL - Immediate block")
    # Log incident, trigger alert
    
else:
    print(f"Error: {response.status_code}")
```

### Asynchronous Validation (High-Throughput)
```python
import requests
import time

# Step 1: Submit intent to queue
intent = {
    "agent_id": "trading-bot-001",
    "intent": "Execute trade",
    "samples": ["Buy 100 AAPL"] * 3,
    "financial": {"proposed_loss": -5000},
    "state_snapshot": {
        "system_prompt": "You are a trading bot",
        "context": {"portfolio_value": 1000000},
        "variables": {"position_count": 5}
    }
}

submit = requests.post(
    "http://localhost:8000/v3/intent",
    json=intent,
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)

request_id = submit.json()["request_id"]

# Step 2: Poll for result (non-blocking)
for _ in range(20):  # Max 2 seconds
    status = requests.get(
        f"http://localhost:8000/v3/intent/{request_id}",
        headers={"Authorization": "Bearer YOUR_API_KEY"}
    )
    
    if status.status_code == 200:
        result = status.json()
        
        if result["status_code"] == 424:
            print("✗ BLOCKED")
            # Rewind agent to last safe state
            rewind = requests.post(
                f"http://localhost:8000/v3/rewind/{intent['agent_id']}",
                headers={"Authorization": "Bearer YOUR_API_KEY"}
            )
            snapshot = rewind.json()
            # Restore agent state from snapshot
            break
        else:
            print("✓ Validated")
            break
    
    elif status.status_code == 202:
        # Still pending
        time.sleep(0.1)
        continue
    else:
        print(f"Error: {status.status_code}")
        break
```

---

## 2. PYTHON SDK (RECOMMENDED)

### Installation
```bash
pip install oriphim-client
```

### Basic Usage
```python
from oriphim import OriphimClient

# Initialize client
client = OriphimClient(
    base_url="https://api.oriphim.com",
    api_key="your-api-key",
    tenant_id="your-tenant-id"
)

# Validate AI output
result = client.validate(
    samples=["AI output 1", "AI output 2", "AI output 3"],
    financial={"proposed_loss": -5000},
    metrics={"leverage_ratio": 3.0}
)

# Check result
if result.indicator == "GREEN":
    print("Safe to execute")
elif result.indicator == "YELLOW":
    print("Review recommended")
else:  # RED
    print("BLOCKED")
    print(f"Violations: {result.violations}")
```

### Advanced: Async Validation with Callbacks
```python
from oriphim import OriphimClient

client = OriphimClient(api_key="...")

# Submit intent (non-blocking)
request_id = client.submit_intent(
    agent_id="bot-001",
    intent="Execute trade",
    samples=["Buy 100 AAPL"] * 3,
    financial={"proposed_loss": -5000},
    state_snapshot={
        "system_prompt": "Trading bot",
        "context": {"portfolio": 1000000}
    }
)

# Option 1: Poll for result
result = client.wait_for_result(request_id, timeout=2.0)

# Option 2: Register callback (webhook)
client.register_webhook(
    url="https://your-app.com/webhooks/oriphim",
    events=["validation.completed", "validation.blocked"]
)
```

### Batch Validation
```python
# Validate 100 trades in parallel
requests = []
for i in range(100):
    req_id = client.submit_intent(
        agent_id=f"bot-{i}",
        intent=f"Trade {i}",
        samples=[f"Execute trade {i}"] * 3
    )
    requests.append(req_id)

# Wait for all results
results = client.wait_for_batch(requests, timeout=5.0)

# Filter blocked trades
blocked = [r for r in results if r.status_code == 424]
print(f"Blocked {len(blocked)}/{len(results)} trades")
```

---

## 3. TYPESCRIPT/JAVASCRIPT SDK

### Installation
```bash
npm install @oriphim/client
# or
yarn add @oriphim/client
```

### Node.js Example
```typescript
import { OriphimClient } from '@oriphim/client';

const client = new OriphimClient({
  baseUrl: 'https://api.oriphim.com',
  apiKey: process.env.ORIPHIM_API_KEY,
  tenantId: process.env.TENANT_ID
});

// Validate AI output
async function validateTrade(aiOutput: string[]) {
  const result = await client.validate({
    samples: aiOutput,
    financial: { proposedLoss: -5000 },
    metrics: { leverageRatio: 3.0 }
  });
  
  switch (result.indicator) {
    case 'GREEN':
      console.log('✓ Safe to execute');
      return true;
    case 'YELLOW':
      console.log('⚠ Review recommended');
      return await manualReview();
    case 'RED':
      console.log('✗ BLOCKED');
      return false;
  }
}

// Usage in trading bot
const aiResponses = await callGPT4("Should I buy AAPL?");
const safe = await validateTrade(aiResponses);

if (safe) {
  await executeTrade();
}
```

### React Dashboard Example
```typescript
import { useOriphim } from '@oriphim/react';

function RiskDashboard() {
  const { health, loading } = useOriphim({
    pollInterval: 2000  // Poll every 2 seconds
  });
  
  return (
    <div className="dashboard">
      <h1>System Health</h1>
      <StatusIndicator 
        status={health?.indicator} 
        color={getColor(health?.indicator)}
      />
      <p>Violation Rate: {health?.recent_violation_rate}%</p>
      <p>Avg Divergence: {health?.recent_divergence_avg}</p>
    </div>
  );
}

function getColor(indicator: string) {
  switch (indicator) {
    case 'GREEN': return '#00FF00';
    case 'YELLOW': return '#FFFF00';
    case 'RED': return '#FF0000';
    default: return '#808080';
  }
}
```

---

## 4. WEBHOOK INTEGRATION (ASYNC NOTIFICATIONS)

### Use Case
- **Event-driven architectures**
- **Slack/Discord notifications** on 424 blocks
- **Real-time dashboards** without polling

### Setup Webhook Endpoint
```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhooks/oriphim")
async def handle_oriphim_webhook(request: Request):
    """Receives validation results from Oriphim"""
    payload = await request.json()
    
    event_type = payload["event_type"]
    
    if event_type == "validation.blocked":
        # Critical: 424 triggered
        request_id = payload["request_id"]
        agent_id = payload["agent_id"]
        violations = payload["violations"]
        
        # Send Slack alert
        await send_slack_alert(
            channel="#risk-alerts",
            message=f"🚨 Agent {agent_id} blocked: {violations}"
        )
        
        # Auto-rewind agent
        await rewind_agent(agent_id)
        
    elif event_type == "validation.completed":
        # Normal validation completed
        print(f"Validation complete: {payload['request_id']}")
    
    return {"status": "received"}
```

### Register Webhook with Oriphim
```python
# One-time setup
import requests

requests.post(
    "http://localhost:8000/v1/onboarding/webhooks",
    json={
        "url": "https://your-app.com/webhooks/oriphim",
        "events": ["validation.blocked", "validation.completed"],
        "secret": "webhook-signing-secret"  # For signature verification
    },
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)
```

### Webhook Payload Schema
```json
{
  "event_type": "validation.blocked",
  "timestamp": "2026-03-03T10:30:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "trading-bot-001",
  "status_code": 424,
  "violations": [
    "Balance invariant breached: energy_out (150) > energy_in (100)"
  ],
  "divergence_score": 0.62,
  "confidence": {
    "score": 0.38,
    "risk_level": "HIGH"
  },
  "action": "BLOCK"
}
```

---

## 5. DOCKER COMPOSE DEPLOYMENT (ONE-CLICK START)

### docker-compose.yml
```yaml
version: '3.8'

services:
  oriphim:
    image: oriphim/watcher:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_ENCRYPTION_KEY=${DB_ENCRYPTION_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET}
      - ENFORCE_HTTPS=false  # Set true in production
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/v2/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  # Optional: Prometheus monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
  
  # Optional: Grafana dashboards
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards

volumes:
  prometheus_data:
  grafana_data:
```

### Quick Start
```bash
# 1. Clone client template
git clone https://github.com/oriphim/client-template.git
cd client-template

# 2. Generate environment
python scripts/generate_env.py

# 3. Start services
docker-compose up -d

# 4. Verify health
curl http://localhost:8000/v2/health

# 5. Create tenant
make tenant-create NAME="Your Company" DOMAIN=yourcompany.com

# 6. Get API key
make key-generate TENANT=<tenant-id> SCOPE=admin

# 7. Test validation
curl -X POST http://localhost:8000/v2/validate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "samples": ["test1", "test2", "test3"],
    "financial": {"proposed_loss": -5000}
  }'
```

---

## 6. INTEGRATION PATTERNS BY USE CASE

### Pattern A: Trading Bot (High-Frequency)
**Requirement:** Validate 1000+ trades/day with <1ms latency overhead

```python
from oriphim import OriphimClient
import asyncio

client = OriphimClient(api_key="...")

async def execute_trade_with_validation(trade: dict):
    """Async pattern: Validation runs in background"""
    
    # Step 1: Get AI recommendation
    ai_output = await call_llm(trade["signal"])
    
    # Step 2: Submit for async validation (non-blocking)
    request_id = await client.submit_intent_async(
        agent_id="hft-bot-001",
        intent=f"Execute {trade['symbol']}",
        samples=ai_output,
        financial={"proposed_loss": trade["risk"]},
        state_snapshot={"context": trade}
    )
    
    # Step 3: Execute trade immediately (validation runs in parallel)
    await execute_trade(trade)
    
    # Step 4: Check validation result asynchronously
    result = await client.wait_for_result(request_id, timeout=0.5)
    
    # Step 5: If blocked, reverse trade
    if result.status_code == 424:
        await reverse_trade(trade)
        await rewind_agent(result.agent_id)

# Execute 1000 trades in parallel
trades = get_pending_trades()
await asyncio.gather(*[execute_trade_with_validation(t) for t in trades])
```

**Latency Profile:**
- Trade execution: T=0ms (no wait)
- Validation: T=50-100ms (runs in background)
- Reversal (if blocked): T=150-200ms (rare event)

### Pattern B: Risk Dashboard (Real-Time Monitoring)
**Requirement:** Display system health with 2-second refresh

```typescript
// React/Next.js example
import { useQuery } from 'react-query';

function RiskDashboard() {
  const { data: health } = useQuery(
    'health',
    () => fetch('/api/oriphim/health').then(r => r.json()),
    { refetchInterval: 2000 }  // Poll every 2 seconds
  );
  
  return (
    <div className="grid grid-cols-3 gap-4">
      <Card>
        <h2>System Status</h2>
        <StatusLight color={health?.indicator} />
        <p>{health?.status}</p>
      </Card>
      
      <Card>
        <h2>Violation Rate</h2>
        <Gauge value={health?.recent_violation_rate} max={1.0} />
        <p>{(health?.recent_violation_rate * 100).toFixed(1)}%</p>
      </Card>
      
      <Card>
        <h2>Avg Divergence</h2>
        <Chart data={health?.divergence_history} />
      </Card>
    </div>
  );
}
```

### Pattern C: Compliance Reporting (Weekly Export)
**Requirement:** Generate PDF audit reports for regulators

```python
from oriphim import OriphimClient
from datetime import datetime, timedelta

client = OriphimClient(api_key="...")

# Generate weekly compliance report
def generate_weekly_report():
    """Exports all audited validations for the week"""
    
    # Export compliance ledger as PDF
    pdf_bytes = client.export_compliance(
        agent_id=None,  # All agents
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now()
    )
    
    # Save to file
    filename = f"compliance-{datetime.now().strftime('%Y%m%d')}.pdf"
    with open(filename, 'wb') as f:
        f.write(pdf_bytes)
    
    # Upload to S3 for archival
    s3.upload_file(filename, 'compliance-reports', filename)
    
    print(f"Report saved: {filename}")

# Schedule with cron: 0 0 * * 1 (Every Monday at midnight)
```

### Pattern D: Incident Response (Auto-Rewind)
**Requirement:** Automatically rewind agent on 424 block

```python
from oriphim import OriphimClient

client = OriphimClient(api_key="...")

def handle_424_block(event: dict):
    """Webhook handler for validation.blocked events"""
    
    agent_id = event["agent_id"]
    violations = event["violations"]
    
    print(f"🚨 Agent {agent_id} blocked: {violations}")
    
    # Step 1: Rewind to last valid state
    snapshot = client.rewind_agent(agent_id)
    
    if snapshot.restored:
        print(f"✓ Agent restored to snapshot {snapshot.snapshot_id}")
        print(f"  System prompt: {snapshot.system_prompt}")
        print(f"  Context: {snapshot.context}")
        
        # Step 2: Notify team
        send_slack_alert(
            channel="#ai-incidents",
            message=f"Agent {agent_id} auto-rewound after violation"
        )
        
        # Step 3: Log incident
        log_incident(agent_id, violations, snapshot)
    else:
        print(f"✗ No valid snapshot found for {agent_id}")
        # Escalate to human
        page_oncall_engineer(agent_id)
```

---

## 7. CLIENT SDKs (IMPLEMENTATION)

### Python SDK Architecture
```
oriphim-client/
├── oriphim/
│   ├── __init__.py
│   ├── client.py         # Main OriphimClient class
│   ├── models.py         # Pydantic models for requests/responses
│   ├── async_client.py   # AsyncOriphimClient (aiohttp)
│   ├── webhooks.py       # Webhook signature verification
│   └── exceptions.py     # Custom exceptions
├── tests/
│   ├── test_client.py
│   ├── test_async.py
│   └── test_webhooks.py
├── examples/
│   ├── basic_usage.py
│   ├── async_batch.py
│   └── webhooks_handler.py
├── pyproject.toml
└── README.md
```

### TypeScript SDK Architecture
```
@oriphim/client/
├── src/
│   ├── index.ts          # Main exports
│   ├── client.ts         # OriphimClient class
│   ├── types.ts          # TypeScript interfaces
│   ├── async.ts          # Promise-based async client
│   └── webhooks.ts       # Webhook helpers
├── tests/
│   ├── client.test.ts
│   └── webhooks.test.ts
├── examples/
│   ├── nodejs/
│   │   └── basic.ts
│   ├── react/
│   │   └── dashboard.tsx
│   └── nextjs/
│       └── api-route.ts
├── package.json
└── README.md
```

---

## 8. POSTMAN COLLECTION (QUICK TESTING)

### Import Collection
```bash
# Download Postman collection
curl -O https://api.oriphim.com/postman/collection.json

# Import into Postman
# File > Import > collection.json
```

### Collection Structure
```
Oriphim API
├── Authentication
│   ├── Login (Get JWT)
│   ├── Refresh Token
│   └── Logout
├── Validation
│   ├── POST /v2/validate (Sync)
│   ├── POST /v3/intent (Async Submit)
│   └── GET /v3/intent/:request_id (Check Status)
├── Monitoring
│   ├── GET /v2/health
│   └── GET /v3/compliance/export
├── Agent Management
│   └── POST /v3/rewind/:agent_id
└── Onboarding
    ├── POST /v1/onboarding/tenants
    ├── POST /v1/onboarding/tenants/:id/users
    └── POST /v1/onboarding/tenants/:id/api-keys
```

### Environment Variables
```json
{
  "base_url": "http://localhost:8000",
  "api_key": "{{api_key}}",
  "tenant_id": "{{tenant_id}}"
}
```

---

## 9. CLIENT INTEGRATION CHECKLIST

### Pre-Integration
- [ ] Read whitepaper and architecture docs
- [ ] Understand 424 Sentinel protocol
- [ ] Define validation trigger points in your application
- [ ] Identify critical constraints (financial limits, physics invariants)

### Setup
- [ ] Deploy Oriphim (Docker Compose or hosted)
- [ ] Create tenant via `/v1/onboarding/tenants`
- [ ] Create admin user
- [ ] Generate API key with appropriate scope
- [ ] Test connection: `curl /v2/health`

### Development
- [ ] Install SDK (`pip install oriphim-client` or `npm install @oriphim/client`)
- [ ] Implement validation wrapper around LLM calls
- [ ] Add error handling for 424, 400, 503 responses
- [ ] Implement agent state snapshots
- [ ] Set up webhook endpoint for async notifications

### Testing
- [ ] Unit test validation integration
- [ ] Test 424 block scenario
- [ ] Test agent rewind functionality
- [ ] Load test with realistic traffic
- [ ] Verify latency overhead < 1ms

### Production
- [ ] Enable HTTPS (`ENFORCE_HTTPS=true`)
- [ ] Rotate API keys quarterly
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure alerts (Slack/PagerDuty on 424)
- [ ] Schedule weekly compliance exports
- [ ] Document incident response runbook

---

## 10. MULTITENANCY & COLLABORATION

### Scenario: Multiple Teams Sharing Oriphim
```
Company: Acme Trading
├── Tenant: acme-trading.com
│   ├── Team: Algorithmic Trading
│   │   ├── User: trader1@acme.com (role: analyst)
│   │   ├── User: trader2@acme.com (role: analyst)
│   │   └── API Key: algo-trading-key (scope: validate-only)
│   ├── Team: Risk Management
│   │   ├── User: risk@acme.com (role: risk-officer)
│   │   └── API Key: risk-dashboard-key (scope: read-metrics)
│   └── Team: Operations
│       ├── User: ops@acme.com (role: admin)
│       └── API Key: ops-cli-key (scope: admin)
```

### Creating Sub-Teams
```python
# Create tenant
tenant = client.create_tenant(
    org_name="Acme Trading",
    domain="acme-trading.com",
    support_tier="enterprise"
)

# Create team members
trader1 = client.create_user(
    tenant_id=tenant.id,
    email="trader1@acme.com",
    role="analyst"
)

risk_officer = client.create_user(
    tenant_id=tenant.id,
    email="risk@acme.com",
    role="risk-officer"
)

admin = client.create_user(
    tenant_id=tenant.id,
    email="ops@acme.com",
    role="admin"
)

# Generate scoped API keys
algo_key = client.generate_api_key(
    tenant_id=tenant.id,
    user_id=trader1.id,
    scope="validate-only"  # Can ONLY call /v2/validate
)

risk_key = client.generate_api_key(
    tenant_id=tenant.id,
    user_id=risk_officer.id,
    scope="read-metrics"  # Can view health/audit, NOT execute
)

admin_key = client.generate_api_key(
    tenant_id=tenant.id,
    user_id=admin.id,
    scope="admin"  # Full access
)
```

---

## 11. ADDING NEW ENDPOINTS (INTEGRATION PLAYBOOK)

### Backend-to-Client Contract Steps
When adding a new backend endpoint, keep client integration deterministic by applying this order:

1. **Define response contract first** (status codes + payload schema).
2. **Add typed model** in client types (`src/types/*` or SDK dataclass/interface).
3. **Add API wrapper method** in client service (`services/api.ts` or SDK client).
4. **Add UI hook/domain adapter** so components consume typed results only.
5. **Add quality-gate coverage** for success and failure paths.

### Dashboard Pattern (TypeScript)
```typescript
// 1) types/domain.ts
export interface NewEndpointResponse {
  id: string;
  status: 'ok' | 'warning' | 'error';
  message: string;
}

// 2) services/api.ts
async getNewEndpoint(resourceId: string) {
  return this.client.get<NewEndpointResponse>(`/v1/new-endpoint/${resourceId}`);
}

// 3) hooks/useNewEndpoint.ts
const response = await client.getNewEndpoint(resourceId);
setState(response.data);
```

### Error Handling Contract
- **4xx (input/auth issues):** show actionable message, no automatic retry.
- **5xx (server instability):** fallback UI + bounded retry with backoff.
- **Timeout/network failures:** mark degraded state, allow manual retry.
- **Never silently swallow errors:** log structured context for triage.

### Minimum Validation Checklist for New Endpoints
- Endpoint has request/response schema tests.
- SDK/service wrapper has success + error-path test.
- UI consumer has loading + error + empty-state rendering.
- Docs are updated if the endpoint introduces new env flags.

---

## SECURITY & EDGE-CASE CONSIDERATIONS

1. **API Key Rotation:** Implement quarterly rotation, never hardcode keys
2. **Rate Limiting:** Plan for 429 responses when rate limits added
3. **Webhook Signature Verification:** Always verify webhook signatures to prevent spoofing
4. **Timeout Handling:** Set aggressive timeouts (1-2s) for validation calls
5. **Retry Logic:** Implement exponential backoff for 503 Service Unavailable
6. **Circuit Breaker:** If Oriphim is down, decide: fail-open (risky) or fail-closed (safe)
7. **State Snapshot Size:** Keep snapshots < 10KB to avoid performance degradation
8. **Multitenancy Isolation:** Never share API keys across tenants

---

## NEXT STEPS

### Week 1: Proof of Concept
1. Deploy Oriphim locally via Docker Compose
2. Integrate `/v2/validate` into one AI workflow
3. Test 424 blocking with intentional violation
4. Verify agent rewind works

### Week 2: Production Pilot
1. Deploy to staging environment
2. Integrate async validation (`/v3/intent`)
3. Set up webhook endpoint
4. Load test with realistic traffic
5. Configure monitoring dashboards

### Week 3: Full Rollout
1. Deploy to production
2. Enable HTTPS enforcement
3. Set up quarterly key rotation
4. Train team on incident response
5. Schedule weekly compliance exports

**Priority Integration Pattern:**
- **Day 1:** Direct REST API (no SDK needed)
- **Week 1:** Python SDK for production integration
- **Month 1:** TypeScript SDK for dashboards
- **Month 2:** Webhook-driven event architecture
