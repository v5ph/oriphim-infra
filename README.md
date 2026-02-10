# Oriphim V-Layer (v1.0 "Sentinel")

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
  "financial": {"proposed_loss": -5000}
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

## Constraint Wrapper

Use `constraint_wrapper` to protect any LLM call. If `validation_request` is provided, it enforces entropy and hard constraints before returning.
