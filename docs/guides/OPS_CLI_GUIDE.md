# ORIPHIM OPERATIONS: SERVER-SIDE CLI GUIDE

**Version:** 2.0  
**Date:** March 1, 2026  
**Interface:** `make` commands → Backend REST API  
**No UI:** All operations via terminal

---

## OVERVIEW

All operational tasks are performed via `make` commands that invoke backend REST API routes exposed by `../../app/main.py` and `../../app/routes/onboarding.py`.

**Architecture:**
- **Backend:** FastAPI `/ops/*` routes with RBAC
- **CLI:** Python scripts in `scripts/ops_cli/`  
- **Interface:** Makefile targets
- **Security:** Bearer token authentication
- **Audit:** Immutable logs in SQLite database

---

## PREREQUISITES

### 1. Python Environment
```bash
python --version  # Requires 3.10+
pip install -e .  # Install dependencies
```

### 2. Backend Server Running
```bash
uvicorn app.main:app --reload
# Server at http://localhost:8000
```

### 3. Operator Credentials
Set environment variables for authentication:
```bash
export ORIPHIM_ACTOR_ID="founder@oriphim.com"
export ORIPHIM_ACTOR_ROLE="ops-admin"
export ORIPHIM_TENANT_ID="test-tenant-001"
export ORIPHIM_API_KEY="your-api-key-here"
```

---

## CORE OPERATIONS

### Testing Workflows

#### Tier 1: Quick Test (1 minute)
```bash
make test-quick
```
**What it does:**
- Python version check (3.10+)
- Dependency verification
- Syntax validation
- Database connectivity
- API health check

**Expected output:**
```
✓ Python 3.10.14 detected
✓ Dependencies installed
✓ Syntax validation passed (47 files)
✓ Database connected
✓ API health: GREEN
────────────────────────────────
✓ TIER 1 PASSED in 58 seconds
```

#### Tier 2: Full Test (5 minutes)
```bash
make test-full
```
**What it does:**
- All Tier 1 checks
- 42 unit tests (pytest suite)
- Integration tests
- API endpoint validation

**Environment variables required:**
- `DEMO_TENANT_ID`
- `DEMO_API_KEY`

#### Tier 3: Load Test (10 minutes)
```bash
make test-load CONCURRENCY=50 DURATION=60
```
**Parameters:**
- `CONCURRENCY`: Simultaneous users (default: 50)
- `DURATION`: Test duration in seconds (default: 60)

**Metrics tracked:**
- Requests per second (target: 100+)
- P95 latency (target: < 100ms)
- Error rate (target: < 0.1%)

#### Tier 4: CI/CD Status
```bash
make test-cicd
```
Shows recent GitHub Actions workflow runs.

#### Run All Tiers Sequentially
```bash
make test-all
```
Executes Tier 1 → 2 → 3 in sequence.

---

### Deployment Operations

#### Check Current Deployment
```bash
make deploy-status
```
Shows:
- Current version
- Traffic distribution (canary %)
- Deployment timestamp

#### Canary Deployment (Progressive Rollout)
```bash
make deploy-canary RING=10 REASON="Post-test deployment"
make deploy-canary RING=25 REASON="Metrics healthy, proceeding"
make deploy-canary RING=50 REASON="Continuing rollout"
make deploy-canary RING=100 REASON="Final promotion"
```
**Safety:** 10-minute hold between steps (configurable).

#### Emergency Rollback
```bash
make deploy-rollback REASON="Critical bug detected"
```
Instantly reverts all traffic to previous stable version (~5 seconds).

---

### Incident Response

#### List Active Incidents
```bash
make incidents-list
```
Shows RED-first sorted incidents with:
- Severity (RED/YELLOW/BLUE)
- Detection timestamp
- Affected resources
- Violation count

#### Rewind System State
```bash
make incident-rewind ID=incident-uuid REASON="Constraint violation regression"
```
Rolls back to previous known-good state.

#### Export Evidence Bundle
```bash
make incident-export ID=incident-uuid
```
Generates PDF with:
- Incident timeline
- Audit events
- Metrics snapshots
- Deployment history

---

### Tenant Management

#### Create New Tenant
```bash
make tenant-create NAME="Acme Corp Investments"
```
Creates tenant with unique `tenant_id`.

#### List All Tenants
```bash
make tenant-list
```

#### Add User to Tenant
```bash
make user-add TENANT=tenant-uuid \
  EMAIL=alice@acme.com \
  ROLE=ops-analyst
```

**Available roles:**
- `ops-admin` - Full access
- `ops-approver` - Request & approve
- `ops-analyst` - View & request
- `viewer` - Read-only

#### Generate API Key
```bash
make key-generate TENANT=tenant-uuid SCOPE=admin
```
**Scopes:**
- `admin` - Full access
- `validate-only` - Validation endpoints only
- `read-metrics` - Read-only metrics

**⚠️ Key displayed once only - save immediately**

#### Revoke API Key
```bash
make key-revoke KEY=key-uuid REASON="Suspected compromise"
```
Requires dual-approval (ops-approver requests, ops-admin approves).

---

### Monitoring

#### System Health Check
```bash
make health-check
```
Returns GREEN/YELLOW/RED indicator with:
- Uptime requests
- Violation rate
- P95 latency
- Drift detection status

**Example output:**
```
[bold green]GREEN[/bold green]

System Health Metrics
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Metric              ┃ Value    ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ Uptime Requests     │ 1247     │
│ Violation Rate      │ 0.12%    │
│ P95 Latency         │ 45.3 ms  │
│ Drift Detected      │ False    │
└─────────────────────┴──────────┘
```

#### Mission Control Summary
```bash
make metrics-summary
```
Complete operational status overview.

#### Audit Trail Export
```bash
make audit-trail DAYS=7
```
Last 7 days of operator actions (immutable log).

---

## IMPLEMENTATION DETAILS

### How Make Commands Work

Every `make` target invokes a Python script in `scripts/ops_cli/` that:
1. Reads environment variables for authentication
2. Calls backend REST API at `http://localhost:8000/ops/*`
3. Formats and displays response

**Example: `make health-check`**
```makefile
.PHONY: health-check
health-check:  ## System health (GREEN/YELLOW/RED)
	@python scripts/ops_cli/health.py
```

**scripts/ops_cli/health.py:**
```python
import httpx
from rich.console import Console

BACKEND = "http://localhost:8000"
HEADERS = {
    "X-Actor-Id": os.getenv("ORIPHIM_ACTOR_ID"),
    "X-Actor-Role": os.getenv("ORIPHIM_ACTOR_ROLE"),
}

resp = httpx.get(f"{BACKEND}/ops/mission/summary", headers=HEADERS)
data = resp.json()

console = Console()
indicator = data.get("health_indicator", "UNKNOWN")
console.print(f"[bold {color}]{indicator}[/bold {color}]")
```

---

## BACKEND API REFERENCE

All operations map to REST endpoints:

| Make Command | Backend Endpoint | Method |
|--------------|------------------|--------|
| `make test-quick` | `/ops/tests/runs` | POST |
| `make test-full` | `/ops/tests/runs` | POST |
| `make test-load` | `/ops/tests/runs` | POST |
| `make deploy-canary` | `/ops/deployments/promote` | POST |
| `make deploy-rollback` | `/ops/deployments/rollback` | POST |
| `make deploy-status` | `/ops/deployments/current` | GET |
| `make incidents-list` | `/ops/incidents` | GET |
| `make incident-rewind` | `/ops/incidents/{id}/rewind` | POST |
| `make tenant-create` | `/v1/onboarding/tenants` | POST |
| `make tenant-list` | `/v1/onboarding/tenants` | GET |
| `make user-add` | `/v1/onboarding/tenants/{id}/users` | POST |
| `make key-generate` | `/v1/onboarding/tenants/{id}/keys` | POST |
| `make key-revoke` | `/v1/onboarding/keys/{id}/revoke` | POST |
| `make health-check` | `/ops/mission/summary` | GET |
| `make audit-trail` | `/ops/audit` | GET |

**API Documentation:** http://localhost:8000/docs

---

## SECURITY & RBAC

### Role Permissions

| Role | Execute Tests | Deploy | Revoke Keys | Approve | View Audit |
|------|--------------|--------|-------------|---------|------------|
| **ops-admin** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **ops-approver** | ✓ | Request only | Request only | ✓ | ✓ |
| **ops-analyst** | ✓ | ✗ | ✗ | ✗ | ✓ |
| **viewer** | ✗ | ✗ | ✗ | ✗ | ✓ (limited) |

### Dual-Approval Workflow

Sensitive actions require two people:

**Actions requiring approval:**
- `deploy_promote`
- `deploy_rollback`
- `key_revoke`
- `incident_rewind`

**Flow:**
1. **Requester** (ops-approver): `make deploy-canary ...`
2. System creates approval request (status: `pending_approval`)
3. **Approver** (ops-admin): Reviews and approves/rejects
4. System executes action if approved

### Rate Limiting

| Action Type | Limit | Window |
|-------------|-------|--------|
| deploy_promote | 5/min | 60 seconds |
| deploy_rollback | 5/min | 60 seconds |
| key_revoke | 10/min | 60 seconds |
| test_run | 20/min | 60 seconds |

---

## TROUBLESHOOTING

### "Missing or invalid Authorization header"
**Cause:** Environment variables not set.  
**Fix:**
```bash
export ORIPHIM_API_KEY="your-api-key"
# Verify:
echo $ORIPHIM_API_KEY
```

### "Backend server not responding"
**Cause:** FastAPI server not running.  
**Fix:**
```bash
# Terminal 1: Start backend
uvicorn app.main:app --reload

# Terminal 2: Run make commands
make health-check
```

### "Rate limit exceeded"
**Cause:** Too many operations in short time.  
**Fix:** Wait 60 seconds before retrying.

### "Insufficient operator role"
**Cause:** Your role lacks permissions.  
**Fix:** Contact ops-admin to change your role:
```bash
make user-modify USER=your-uuid ROLE=ops-approver
```

---

## BEST PRACTICES

### Pre-Deployment Checklist
- [ ] `make test-quick` passed (last 5 min)
- [ ] `make test-full` passed (all 42 tests)
- [ ] `make test-load` passed (RPS > 100, P95 < 100ms)
- [ ] `make health-check` returns GREEN
- [ ] No RED incidents: `make incidents-list`
- [ ] Rollback plan documented
- [ ] On-call engineer notified

### Incident Response Workflow
1. **Detect:** `make health-check` returns RED
2. **List:** `make incidents-list` (find incident UUID)
3. **Review:** Check audit trail: `make audit-trail DAYS=1`
4. **Contain:** `make incident-rewind ID=uuid REASON="..."` if needed
5. **Export:** `make incident-export ID=uuid`
6. **Postmortem:** Use exported PDF as evidence

### Monitoring Cadence
```bash
# Continuous monitoring (cron job)
*/5 * * * * cd /path/to/oriphim-infra && make health-check
```

---

## COMPARISON TO PREVIOUS UI

| Task | UI Workflow (Deprecated) | CLI Workflow (Current) |
|------|-------------------------|------------------------|
| **Quick Test** | Browser → Testing Workbench → Tier 1 → Run Now | `make test-quick` |
| **Canary Deploy** | Browser → Deployments → Promote → Fill Form → Request Approval | `make deploy-canary RING=25` |
| **Health Check** | Browser → Mission Control → View Status Cards | `make health-check` |
| **Incident Response** | Browser → Validation & Incidents → Click Incident → Follow Playbook | `make incidents-list && make incident-rewind ID=...` |
| **Tenant Creation** | Browser → Tenants & Access → Create Tenant → Fill Form | `make tenant-create NAME="Acme"` |

**Benefits of CLI:**
- **Faster:** No browser startup, instant execution
- **Scriptable:** Chain commands in bash scripts
- **Version-controlled:** Makefile in git
- **Automation-ready:** CI/CD pipelines, cron jobs
- **Lower complexity:** No React/Vite/TypeScript dependencies

---

## QUICK REFERENCE

### Most Common Commands
```bash
# Daily operations
make health-check           # System status
make test                   # Unit tests
make test-integration       # Integration tests
make tenant-list            # List tenants

# Emergency
make server-stop            # Stop backend server
make reset-db               # Reset local databases

# Weekly tasks
make test-all               # Full validation suite
make audit-trail TENANT=<id> API_KEY=<key>
```

### Environment Setup (One-Time)
```bash
# Add to ~/.bashrc or ~/.zshrc
export ORIPHIM_ACTOR_ID="your.email@oriphim.com"
export ORIPHIM_ACTOR_ROLE="ops-admin"
export ORIPHIM_TENANT_ID="tenant_550e8400"
export ORIPHIM_API_KEY="oriphim_sk_..."

# Reload shell
source ~/.bashrc
```

### Help
```bash
make help     # List all commands with descriptions
make          # Same as make help
```

---

## NEXT STEPS

1. **Configure environment:** Set `ORIPHIM_*` variables
2. **Start backend:** `uvicorn app.main:app --reload`
3. **Verify setup:** `make health-check`
4. **Run first test:** `make test`
5. **Explore commands:** `make help`

For backend API details, see:
- API docs: http://localhost:8000/docs
- Source: [app/routes/onboarding.py](../../app/routes/onboarding.py)
- Models: [app/models.py](../../app/models.py)

---

**Document Version:** 1.0  
**Last Updated:** March 1, 2026  
**Maintainer:** Founder/CTO  
**Related:** [REPO_ORGANIZATION.md](../architecture/REPO_ORGANIZATION.md)
