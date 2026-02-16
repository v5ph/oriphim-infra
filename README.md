# Watcher Protocal (v1.0 "Sentinel")

High-speed headless API that intercepts AI agent outputs and validates them against hard constraints.

## Quickstart

Install dependencies:

- `pip install -e .`

Run API:

- `uvicorn app.main:app --reload`

## Endpoint

`POST /v1/validate`

### Example request

```json
{
  "samples": ["path A", "path A", "path B"],
  "physics": {"energy_in": 100, "energy_out": 90},
  "financial": {"proposed_loss": -5000},
  "metrics": {"pressure": 101325, "leverage_ratio": 4.2}
}
```

### Example response (OK)

```json
{
  "status": "OK",
  "entropy_score": 0.9183,
  "violations": []
}
```

### Example response (403)

```json
{
  "detail": {
    "status": "Logic Violation",
    "entropy_score": 0.5,
    "violations": ["Conservation of Energy violated"]
  }
}
```

### Example response (424)

```json
{
  "detail": {
    "status": "Logic Violation",
    "entropy_score": 0.2,
    "violations": ["Leverage ratio exceeds hard limit"]
  }
}
```

## Constraint Wrapper

Use `constraint_wrapper` to protect any LLM call. If `validation_request` is provided, it enforces entropy and hard constraints before returning.

## Semantic Embeddings

The hallucination detector uses `all-MiniLM-L6-v2` to compare meaning, not just word counts. Pairwise cosine distance across three responses is averaged into a 0–1 divergence score.

## Testing

Run the hallucination trap test suite:

```bash
pip install -e ".[dev]"
pytest tests/
```

10 test cases prove the system catches perpetual motion, negative temperatures, extreme leverage, and semantically similar but physically impossible claims.

## Live LLM Testing (ChatGPT Integration)

### Demo Mode (No API Required)

See Watcher Protocal catch hallucinations with pre-recorded ChatGPT responses:

```bash
python test_demo.py
```

Tests perpetual motion, 50x leverage trading, and FTL communication claims.

### Free Local LLM Testing (Ollama, LM Studio, or Hugging Face)

Test against real open-source LLMs running locally—**completely free and private**.

#### Option 1: Ollama (Easiest)

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

#### Option 3: Hugging Face Transformers (CPU/GPU)

```bash
pip install transformers torch
export BACKEND=huggingface
python test_local_llm.py
```

### Live Mode (Requires OpenAI API)

Test against real ChatGPT outputs:

```bash
export OPENAI_API_KEY="sk-..."
pip install -e ".[test-llm]"
python test_live_llm.py
```

**Note:** If you get a 429 quota error, check your OpenAI billing at https://platform.openai.com/account/billing/overview

---
PLANNED TECH STACK:

**Current + Production‑ready Tech Stack (with Supabase)**

**Core**
- Python 3.10+
- FastAPI (API)
- Pydantic v2 (validation)
- Uvicorn (ASGI server)

**AI Validation**
- sentence-transformers (all‑MiniLM‑L6‑v2)
- NumPy + SciPy

**Database**
- Supabase Postgres (primary DB)
- Supabase Auth (JWT, RBAC/RLS)
- Alembic (migrations)

**Caching / Queues**
- Redis (cache + rate limits)
- Celery or RQ (async jobs)

**Observability**
- OpenTelemetry (tracing)
- Prometheus + Grafana (metrics)
- Sentry (errors)

**Security**
- API key + JWT auth
- Rate limiting (Redis)
- Secret manager (Supabase Vault/Cloud secret manager)
- Dependency scanning (pip‑audit/Snyk)

**Infra / CI**
- Docker
- CI/CD (GitHub Actions)
- IaC (Terraform)
- Load balancer + autoscaling

**Testing**
- pytest + httpx
- contract tests for API
- load tests (k6/Locust)
