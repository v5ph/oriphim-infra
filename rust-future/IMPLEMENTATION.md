# Rust Implementation Guide

**For when you're ready to build. Not needed before then.**

---

## Prerequisites

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install maturin (Python build tool for Rust)
pip install maturin

# Verify
rustc --version
cargo --version
maturin --version
```

---

## Building Step-by-Step

### Step 1: Build watcher_embedding

```bash
cd rust-future/watcher_embedding

# Check compilation
cargo check

# Build release
cargo build --release

# Run tests
cargo test

# Install as Python module
maturin develop --release

# Test import
python -c "from watcher_embedding import compute_divergence_pyo3; print('✓ OK')"
```

### Step 2: Build watcher_constraints

```bash
cd ../watcher_constraints

cargo check
cargo build --release
cargo test
maturin develop --release

python -c "from watcher_constraints import validate_constraints; print('✓ OK')"
```

### Step 3: Build watcher_drift

```bash
cd ../watcher_drift

cargo check
cargo build --release
cargo test
maturin develop --release

python -c "from watcher_drift import detect_drift; print('✓ OK')"
```

---

## Integration into Python

Once Rust modules are built, update the Python wrappers:

### Update app/core/entropy.py

```python
# At top of file
try:
    from watcher_embedding import compute_divergence_pyo3
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    print("⚠️ Rust embeddings not available, using Python")

# In hallucination_divergence function
def hallucination_divergence(responses: List[str]) -> float:
    if len(responses) != 3:
        raise ValueError("expects exactly 3 responses")
    
    if all(not r.strip() for r in responses):
        return 0.0
    if any(not r.strip() for r in responses) and any(r.strip() for r in responses):
        return 1.0
    
    # Use Rust if available
    if RUST_AVAILABLE:
        try:
            return float(compute_divergence_pyo3(responses))
        except Exception as e:
            print(f"⚠️ Rust failed: {e}, using Python")
    
    # Fallback to Python
    model = _get_embedding_model()
    embeddings = model.encode(responses, normalize_embeddings=True)
    cos_01 = float(np.dot(embeddings[0], embeddings[1]))
    cos_02 = float(np.dot(embeddings[0], embeddings[2]))
    cos_12 = float(np.dot(embeddings[1], embeddings[2]))
    avg_cos = (cos_01 + cos_02 + cos_12) / 3.0
    score = (1.0 - avg_cos) / 2.0
    return float(min(max(score, 0.0), 1.0))
```

### Update app/core/constraints.py

```python
# At top of file
try:
    from watcher_constraints import validate_constraints as rust_validate
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False

# In check_logic function
def check_logic(request: ValidationRequest | _RequestLike) -> List[str]:
    # Try Rust first
    if RUST_AVAILABLE:
        try:
            metrics_dict = dict(request.metrics.items()) if request.metrics else None
            return rust_validate(
                physics_energy_in=request.physics.energy_in if request.physics else None,
                physics_energy_out=request.physics.energy_out if request.physics else None,
                financial_proposed_loss=request.financial.proposed_loss if request.financial else None,
                metrics=metrics_dict
            )
        except Exception as e:
            print(f"⚠️ Rust failed: {e}, using Python")
    
    # Python implementation (keep existing code)
    ...
```

### Update app/core/drift.py

```python
# At top of file
try:
    from watcher_drift import detect_drift as rust_detect_drift
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False

# In detect_drift method
def detect_drift(self, current_divergence: float) -> DriftAlert:
    # Try Rust first
    if RUST_AVAILABLE and self.divergence_history:
        try:
            detected, z_score, mean, current, explanation = rust_detect_drift(
                historical_data=list(self.divergence_history),
                current_value=current_divergence,
                threshold=2.5
            )
            return DriftAlert(
                detected=detected,
                z_score=z_score,
                historical_mean=mean,
                current_value=current_divergence,
                explanation=explanation
            )
        except Exception as e:
            print(f"⚠️ Rust failed: {e}, using Python")
    
    # Python implementation (keep existing code)
    ...
```

---

## Testing

```bash
# Run full test suite
pytest test_demo.py -v
pytest tests/test_hallucination_traps.py -v

# Run Rust tests
cargo test --all

# Test integration
python -c "
from app.core.entropy import hallucination_divergence
samples = ['test', 'test', 'different']
score = hallucination_divergence(samples)
print(f'Divergence: {score:.3f}')
"
```

---

## Benchmarking

```bash
# Create benchmark script
cat > benchmark.py << 'EOF'
import time
from app.core.entropy import hallucination_divergence

samples = [
    "This is a test message about embeddings",
    "This is a test message about embeddings",
    "Completely different topic"
]

# Warmup
for _ in range(3):
    hallucination_divergence(samples)

# Benchmark
start = time.perf_counter()
for _ in range(100):
    hallucination_divergence(samples)
end = time.perf_counter()

avg_ms = (end - start) / 100 * 1000
print(f"Average latency: {avg_ms:.2f}ms")
print(f"Expected with Rust: 15-25ms")
print(f"Expected with Python: 150-200ms")
EOF

python benchmark.py
```

---

## Troubleshooting

### ONNX Model Issues

```bash
# If model download fails, set cache directory
export WATCHER_MODEL_CACHE=$HOME/.models

# Pre-download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Point Rust build to cached model
export ORT_MODELS=$HOME/.models
cargo build --release
```

### Windows Build Fails

```bash
# Install Visual Studio Build Tools
# Or use WSL for build

# In WSL:
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
cargo build --release
```

### Import Fails at Runtime

```bash
# Check if module was installed
python -m pip show watcher-embedding

# Check Python path
python -c "import sys; print(sys.path)"

# Try rebuilding
cd rust-future/watcher_embedding
maturin develop --release
```

### Rust Tests Fail

```bash
# See detailed error
cargo test -- --nocapture

# Check for dependency issues
cargo update

# Full rebuild
cargo clean
cargo build --release
```

---

## Performance Expectations

| Operation | Python | Rust | Speedup |
|-----------|--------|------|---------|
| Embedding | 200ms | 20ms | 10x |
| Constraints | 3ms | 0.5ms | 6x |
| Drift | 3ms | 1ms | 3x |
| **Total** | **200ms** | **50ms** | **4x** |

These are estimates. Actual performance depends on:
- Hardware (CPU cores, RAM)
- Load (concurrent requests)
- Model size (embedding dimensions)
- Data volume (constraint complexity)

---

## Rollback Plan

If Rust integration causes issues:

```python
# Remove Rust imports
try:
    from watcher_embedding import compute_divergence_pyo3
except ImportError:
    pass  # Falls back to Python

# System still works completely
```

**No breaking changes. Zero downtime. Easy rollback.**

---

## Next Steps

1. Read OVERVIEW.md for when to build
2. Check this file (IMPLEMENTATION.md) for build instructions
3. Use REFERENCE.md for quick lookup
4. Ship Python first. Build Rust only if data demands it.

---

**Remember:** Ship Python MVP first. Measure real usage. Build Rust only if customers need it.
