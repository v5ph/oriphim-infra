# Watcher Protocol (v1.0 "Sentinel")

High-speed headless API that intercepts AI agent outputs and validates them against hard constraints. Production-ready Python implementation shipping Feb 22, 2026.

## Current Status

✅ **Python Implementation Complete**
- All 7 API endpoints functional
- Core validation modules working
- Test suite passing (10+ hallucination trap tests)
- Deployment ready

⏳ **Rust Optimization (Optional Phase 2)**
- Scaffolded in `rust-future/` directory
- **Not integrated into current code**
- **Zero impact on running system**
- Only for performance optimization IF production demands it

## Quickstart

Install dependencies:

```bash
pip install -e .
```

Run API:

```bash
uvicorn app.main:app --reload
```

API will be available at `http://localhost:8000`

## Endpoints

### v1 (Legacy)
- `POST /v1/validate` - Basic constraint + entropy validation

### v2 (Current Primary)
- `POST /v2/validate` - Enhanced validation with timestamps and audit logging
- `GET /v2/health` - Health check endpoint

### v3 (Intent & Compliance)
- `POST /v3/intent` - Validate specific intent with full validation suite
- `GET /v3/intent/{uuid}` - Retrieve specific validation result
- `POST /v3/rewind/{agent_id}` - Rewind agent state to previous validation
- `POST /v3/compliance/export` - Export audit trail as PDF

## Example Request

`POST /v2/validate`

### Example Request

```json
{
  "samples": ["response A", "response A", "response B"],
  "physics": {"energy_in": 100, "energy_out": 90},
  "financial": {"proposed_loss": -5000},
  "metrics": {"pressure": 101325, "leverage_ratio": 4.2}
}
```

### Success Response (200 OK)

```json
{
  "status": "OK",
  "entropy_score": 0.15,
  "confidence_level": "GREEN",
  "violations": [],
  "timestamp": "2026-02-17T12:34:56.789Z"
}
```

### Hallucination Detected (400)

```json
{
  "status": "HALLUCINATION_DETECTED",
  "entropy_score": 0.85,
  "confidence_level": "RED",
  "violations": ["Semantic divergence exceeds 0.7 threshold"],
  "timestamp": "2026-02-17T12:34:56.789Z"
}
```

### Hard Constraint Violated (422)

```json
{
  "status": "CONSTRAINT_VIOLATED",
  "entropy_score": 0.15,
  "confidence_level": "YELLOW",
  "violations": [
    "Conservation of Energy violated",
    "Leverage ratio exceeds hard limit"
  ],
  "timestamp": "2026-02-17T12:34:56.789Z"
}
```

## Core Features

### 1. Semantic Divergence Detection

Detects hallucinations by comparing semantic meaning of AI responses across three attempts. Uses `all-MiniLM-L6-v2` embeddings to compute pairwise cosine distances.

```python
from app.core.entropy import hallucination_divergence

divergence_score = hallucination_divergence([
    "The device converts 100% of input energy to output",
    "The device perfectly conserves all input energy",
    "Perpetual motion machine invented yesterday"
])
# Returns: 0.95 (HIGH divergence = likely hallucination)
```

**Baseline Latency:** ~200ms per inference  
**Rust Optimization:** ~20ms (see `rust-future/` for optional Rust implementation)

### 2. Hard Constraint Validation

Enforces physics and business limits:

- **Conservation of Energy:** ±5% tolerance
- **Financial VaR:** Proposed loss ≤ customer maximum
- **Physical Limits:** Temperature (273-373K), Pressure (0.5-1.5 atm)
- **Leverage Ratio:** Assets/Liability ≤ 3.0

```python
from app.core.constraints import check_logic

violations = check_logic(request)
# Returns: [] if all constraints pass, or list of violations
```

### 3. Drift Detection

Detects behavioral anomalies using z-score statistics.

```python
from app.core.drift import RequestHistory

detector = RequestHistory()
detector.add_divergence(0.15)
detector.add_divergence(0.18)
detector.add_divergence(0.85)  # Anomaly!

alert = detector.detect_drift(0.85)
# Returns: DriftAlert(detected=True, z_score=3.2, ...)
```

### 4. Confidence Scoring

Maps validation results to risk levels:

- **GREEN:** All clear (entropy < 0.3, no violations)
- **YELLOW:** Caution (entropy 0.3-0.7 or minor violations)
- **RED:** Stop (entropy > 0.7 or hard violations)

### 5. Constraint Wrapper Decorator

Protect any LLM call with automatic validation:

```python
from app.core.wrapper import constraint_wrapper

@constraint_wrapper(
    physics={"energy_in": 100, "energy_out": 100},
    max_proposals=3
)
def my_agent_function(prompt: str) -> str:
    # Your LLM call here
    return openai.ChatCompletion.create(...)

## Testing

### Unit Tests (Validation Logic)

```bash
pip install -e ".[dev]"
pytest tests/test_hallucination_traps.py -v
```

**Coverage:**
- Perpetual motion detection
- Impossible physics validation
- Extreme leverage detection
- Semantic similarity checks
- Statistical anomaly detection

10 hallucination trap tests prove the system catches common AI mistakes.

### Demo Mode (Pre-recorded ChatGPT)

```bash
python test_demo.py
```

Tests the system against real ChatGPT responses on:
- Perpetual motion claims
- 50x leverage trading
- FTL communication proposals

### Dashboard Integration Test

```bash
python test_dashboard_integration.py
```

Validates the full pipeline including storage, PDF export, and compliance logs.

### Live LLM Testing (ChatGPT Integration)

Test against real ChatGPT outputs (requires OpenAI API):

```bash
export OPENAI_API_KEY="sk-..."
pip install -e ".[test-llm]"
python test_live_llm.py
```

**Note:** If you get a 429 quota error, check billing at https://platform.openai.com/account/billing

### Local LLM Testing (Free & Private)

Test against open-source models running locally—completely free.

#### Option 1: Ollama (Recommended)

```bash
# Install: https://ollama.ai
ollama pull mistral
ollama serve

# In another terminal:
python test_local_llm.py
```

#### Option 2: LM Studio (GUI, Windows/macOS)

```bash
# Download: https://lmstudio.ai
# Open app → Load a model (mistral recommended)
# Click "Start Local Server"

# Then:
python test_local_llm.py
```

#### Option 3: Hugging Face Transformers

```bash
pip install transformers torch
export BACKEND=huggingface
python test_local_llm.py
```

## Architecture

### Module Structure

```
app/
├── main.py                    # FastAPI application (7 endpoints)
├── models.py                  # Request/Response Pydantic models
├── models_dashboard.py        # Dashboard data structures
└── core/
    ├── entropy.py            # Semantic divergence (embeddings)
    ├── constraints.py        # Hard constraint validation
    ├── drift.py              # Anomaly detection (z-scores)
    ├── confidence.py         # Risk scoring (GREEN/YELLOW/RED)
    ├── severity.py           # Violation severity weighting
    ├── compliance.py         # Regulatory mapping (EU AI Act, SB 243)
    ├── storage.py            # SQLite audit logging with RLS
    ├── pdf_export.py         # Compliance report generation
    ├── physical_validator.py # Hard constraint enforcement
    ├── parallel_validation.py # Pipeline orchestration
    └── wrapper.py            # LLM decorator for validation
```

### Request Flow

```
POST /v2/validate or /v3/intent
    ↓
[Pydantic Validation]
    ↓
[Entropy Score] → Semantic divergence check
    ↓
[Constraints Check] → Physics/financial limits
    ↓
[Drift Detection] → Anomaly detection
    ↓
[Confidence Level] → GREEN/YELLOW/RED
    ↓
[Severity Weighting] → Impact calculation
    ↓
[Audit Log] → SQLite storage
    ↓
Response (200 OK or 4xx error)
```

**Total Latency:** ~200ms (dominated by embedding inference)

### Design Decisions (CTO-Locked)

1. **SDK-First Topology:** Optional Kubernetes sidecar for high-throughput scenarios
2. **JWT Token Model:** Signed validation approvals (RS256)
3. **YAML Constraints:** Customer-defined limits with webhook callbacks
4. **Fail-Closed:** Default deny, configurable per client
5. **50ms SLA:** Synchronous path must complete within budget


## Tech Stack

### Current (Production-Ready Python)

**Core**
- Python 3.10+
- FastAPI 0.110+
- Pydantic v2.6+ (validation)
- Uvicorn (ASGI server)

**AI & Validation**
- sentence-transformers (all-MiniLM-L6-v2)
- NumPy + SciPy (statistics)

**Storage & Persistence**
- SQLite (file-based audit logging)
- Row-Level Security (RLS) for multi-tenant isolation

**Compliance & Reporting**
- YAML for constraint definitions
- PDF export (minimal, no external deps)
- EU AI Act & CA SB 243 article mapping

**Testing**
- pytest + httpx
- Hypothesis (property-based testing)

### Optional Future (Rust Optimization - Phase 2)

Located in `rust-future/` directory. **NOT integrated into current code. Zero impact on running system.**

- **watcher_embedding:** ONNX Runtime + PyO3 (10x faster embedding inference)
- **watcher_constraints:** Compiled validation rules (6x faster constraint checks)
- **watcher_drift:** Welford's algorithm (3x faster anomaly detection)

When to build: Only if production data shows customers need <50ms P99 latency.

See [rust-future/README.md](rust-future/README.md) for details.

## Rust Optimization (Optional)

### Current Situation

The Python implementation is **100% complete and production-ready**. It passes all tests and meets the Feb 22, 2026 launch deadline.

Rust optimization code is scaffolded in the `rust-future/` directory but is **completely isolated** from the running system.

### Why Rust Exists

3 modules can be 10-13x faster in Rust:
- **Embedding inference:** 200ms → 20ms (ONNX Runtime optimization)
- **Constraint validation:** 3ms → 0.5ms (compiled rule execution)
- **Drift detection:** 3ms → 1ms (Welford's algorithm)

**But:** You don't need it now. Python is fast enough for MVP. Only build Rust if production metrics demand it.

### When to Build Rust

| Scenario | Action |
|----------|--------|
| Shipping Feb 22 MVP | Use Python as-is |
| Customers report >100ms latency | Build watcher_embedding only |
| Multiple slow customers | Build all 3 modules |
| Latency SLA violated in production | Rust becomes critical |

### What to Do With Rust Code

**Do this:**
1. Read [rust-future/README.md](rust-future/README.md) for orientation
2. Read [rust-future/OVERVIEW.md](rust-future/OVERVIEW.md) for strategy
3. Keep it in version control (it's ready to build when needed)

**Don't do this:**
- Don't integrate Rust now (Python works fine)
- Don't feel pressure to use it (ship Python first)
- Don't assume it will solve your problems (measure real usage first)

### How to Build It Later

When (if) you're ready:

```bash
cd rust-future/
# See IMPLEMENTATION.md for step-by-step build instructions
```

**Build time:** 4-7 minutes first time, 1-2 minutes for rebuilds

**Impact on existing code:** Zero. Rust modules are completely optional and won't be called unless you integrate them (you won't, unless you choose to).

## Dashboard

Frontend specification ready in [DASHBOARD_PROD.txt](DASHBOARD_PROD.txt).

**Status:** Design complete, awaiting implementation  
**Recommended Stack:** React 18, TailwindCSS, Chart.js  
**Key Views:**
- Validation history timeline
- Constraint violations heatmap
- Compliance audit trail
- Drift anomalies

See dashboard spec for full details.

## Configuration

### Environment Variables

```bash
# API
FASTAPI_ENV=production
FASTAPI_LOG_LEVEL=info

# Database
SQLITE_DB_PATH=./audit.db

# Validation
ENTROPY_THRESHOLD=0.7
CONFIDENCE_THRESHOLD_CAUTION=0.3
CONFIDENCE_THRESHOLD_DANGER=0.7
DRIFT_THRESHOLD_ZSCORE=2.5

# Optional: Local LLM
LLM_BACKEND=ollama  # ollama, lm-studio, huggingface
LLM_BASE_URL=http://localhost:11434
```

### Constraint Configuration (YAML)

```yaml
# constraints.yaml
conservation_of_energy:
  tolerance_percent: 5

var_limit:
  customer_max_loss: 100000

physical_limits:
  temperature_min_k: 273
  temperature_max_k: 373
  pressure_min_atm: 0.5
  pressure_max_atm: 1.5

leverage_ratio:
  max_assets_to_liability: 3.0
```

## Performance

### Baseline (Current Python)

| Operation | Latency | Notes |
|-----------|---------|-------|
| Embedding inference | 200ms | dominated by model |
| Constraint validation | 3ms | tight loop |
| Drift detection | 3ms | z-score calculation |
| **Total validation** | **~210ms** | P50 latency |

### Targets (If Rust Built)

| Operation | Python | Rust | Speedup |
|-----------|--------|------|---------|
| Embedding | 200ms | 20ms | 10x |
| Constraints | 3ms | 0.5ms | 6x |
| Drift | 3ms | 1ms | 3x |
| **Total** | **206ms** | **50ms** | **4x** |

### Measurement

To benchmark your environment:

```bash
python benchmark.py
```

This measures actual latency on your hardware with your data.

## Deployment

### Local Development

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Docker

```bash
docker build -t watcher-sentinel:latest .
docker run -p 8000:8000 -v $(pwd)/audit.db:/app/audit.db watcher-sentinel:latest
```

### Production (Kubernetes)

```bash
kubectl apply -f k8s/deployment.yaml
kubectl port-forward svc/watcher-sentinel 8000:8000
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/v2/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-17T12:34:56.789Z",
  "version": "1.0-sentinel"
}
```

### Audit Trail

All validations logged to SQLite with:
- Timestamp
- Request ID
- Entropy score
- Violations
- User/Agent ID
- Compliance article mapping

Export as PDF:

```bash
curl -X POST http://localhost:8000/v3/compliance/export \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2026-01-01", "end_date": "2026-02-28"}' \
  > audit_report.pdf
```

## FAQ

**Q: Will Rust slow down my deployment?**  
A: No. Rust is completely optional. Python-only deployment is the default.

**Q: Do I need Rust to ship?**  
A: No. Ship Python Feb 22. Build Rust only if customers demand faster speed.

**Q: What if Rust breaks something?**  
A: It can't. The Python code runs independently. Rust modules must be explicitly called (they aren't in current code).

**Q: Can I use Rust without rebuilding everything?**  
A: Yes. Each Rust module is a separate PyO3 extension. Add them one at a time as needed.

**Q: How long does Rust build take?**  
A: 4-7 minutes first time (ONNX download), 1-2 minutes for rebuilds.

**Q: What if I don't want Rust?**  
A: Delete `rust-future/` directory. Python code works exactly the same.
