# Rust Reference & Quick Commands

**Quick lookup when building Rust optimization. Three modules explained.**

---

## Quick Command Cheat Sheet

```bash
# Check if Rust is ready
ls rust-future/watcher_*

# Build all three modules
cd rust-future/watcher_embedding && cargo build --release && maturin develop --release
cd ../watcher_constraints && cargo build --release && maturin develop --release
cd ../watcher_drift && cargo build --release && maturin develop --release

# Test integration
pytest test_demo.py::test_validation_async -v

# Benchmark before/after
python benchmark.py  # See times
```

---

## The Three Modules Explained

### 1. watcher_embedding (Biggest Speedup: 10x)

**What:** Semantic divergence detection using embeddings  
**Current:** 200ms per request (Python + sentence-transformers)  
**Rust:** 20ms per request (ONNX Runtime with optimized tokenization)  
**Why:** Embedding inference is the bottleneck. Rust + ONNX = same accuracy, 10x faster.

**Replaces:**
```python
# app/core/entropy.py
hallucination_divergence(responses: List[str]) -> float
```

**Files:**
- `rust-future/watcher_embedding/src/model.rs` - ONNX model loader (lazy-loaded, cached)
- `rust-future/watcher_embedding/src/embedding.rs` - Encoding logic with cosine similarity
- `rust-future/watcher_embedding/src/lib.rs` - PyO3 binding `compute_divergence_pyo3()`

**Key Code:**
```rust
// Loads model once, reuses for all requests
static EMBEDDING_MODEL: Lazy<EmbeddingModel> = ...

// Tokenizes and encodes in parallel
pub fn encode_batch(texts: Vec<String>) -> Vec<Vec<f32>> {
    texts.par_iter()
        .map(|text| tokenize_and_encode(text))
        .collect()
}

// Fast cosine similarity (SIMD-friendly)
pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    dot_product(a, b) / (norm(a) * norm(b))
}
```

**Dependency Tree:**
- `ort` = ONNX Runtime (C++ underneath, Rust bindings)
- `tokenizers` = HuggingFace fast tokenizer
- `ndarray` = Numerical arrays for SIMD
- `rayon` = Parallel iterator (optional)

---

### 2. watcher_constraints (Medium Speedup: 6x)

**What:** Hard constraint validation  
**Current:** 3ms per request (Python with loops)  
**Rust:** 0.5ms per request (Compiled validation rules)  
**Why:** Physics checks are repetitive. Rust compiles them, parallelizes if needed.

**Replaces:**
```python
# app/core/constraints.py
check_logic(request: ValidationRequest) -> List[str]
```

**Files:**
- `rust-future/watcher_constraints/src/executor.rs` - Core validation logic
- `rust-future/watcher_constraints/src/lib.rs` - PyO3 binding `validate_constraints()`

**Key Rules:**
1. **Conservation of Energy:** energy_in == energy_out ± 5%
2. **VaR Limit:** proposed_loss <= customer_max_loss_percent
3. **Temperature Range:** 273K to 373K
4. **Pressure Range:** 0.5 to 1.5 atm
5. **Leverage Ratio:** assets / liability <= 3.0

**Key Code:**
```rust
pub fn check_logic(metrics: &Metrics) -> Vec<String> {
    let mut violations = Vec::new();
    
    // Each check is a dedicated function (inlined by compiler)
    if !check_energy(metrics) {
        violations.push("Conservation of energy violated".to_string());
    }
    if !check_var(metrics) {
        violations.push("VaR limit exceeded".to_string());
    }
    // ... more checks
    
    violations
}
```

**Optional Parallelization:**
```rust
use rayon::prelude::*;

// If checking 1000 metrics in a batch
pub fn check_batch(batch: Vec<Metrics>) -> Vec<Vec<String>> {
    batch.par_iter()
        .map(|m| check_logic(m))
        .collect()
}
```

**Dependency Tree:**
- `serde` = JSON serialization (if needed)
- `rayon` = Parallelization (optional, only for batches)

---

### 3. watcher_drift (Small Speedup: 3x)

**What:** Statistical drift detection using z-scores  
**Current:** 3ms per request (Python with deque + statistics)  
**Rust:** 1ms per request (Welford's algorithm, single-pass)  
**Why:** Welford's algorithm is mathematically more efficient than keeping full history.

**Replaces:**
```python
# app/core/drift.py
RequestHistory.detect_drift(current_divergence: float) -> DriftAlert
```

**Files:**
- `rust-future/watcher_drift/src/detector.rs` - Drift detection logic
- `rust-future/watcher_drift/src/lib.rs` - PyO3 binding `detect_drift()`

**Key Algorithm:**
```rust
// Welford's online algorithm - computes mean and variance in ONE pass
pub struct DriftDetector {
    count: u32,
    mean: f64,
    m2: f64,  // Sum of squared differences
}

impl DriftDetector {
    pub fn update(&mut self, x: f64) {
        self.count += 1;
        let delta = x - self.mean;
        self.mean += delta / (self.count as f64);
        let delta2 = x - self.mean;
        self.m2 += delta * delta2;
    }
    
    pub fn variance(&self) -> f64 {
        if self.count < 2 { 0.0 } else { self.m2 / (self.count - 1) as f64 }
    }
    
    pub fn z_score(&self, x: f64) -> f64 {
        (x - self.mean) / self.variance().sqrt()
    }
}

// Detects drift if |z_score| > threshold (2.5 = 98.8% confidence)
pub fn detect_drift(history: &[f64], current: f64, threshold: f64) -> (bool, f64) {
    let z = compute_z_score(history, current);
    (z.abs() > threshold, z)
}
```

**Dependency Tree:**
- Only stdlib (no external dependencies)
- Ultra-lightweight and fast

---

## When to Build (Decision Matrix)

| Scenario | Action | Timeline |
|----------|--------|----------|
| MVP launch Feb 22 | **SKIP Rust** - Python is ready now | N/A |
| Customer says "too slow" (>100ms) | Build watcher_embedding only | 2-3 days |
| Multiple slow customers | Build all 3 modules | 8-12 days |
| Latency SLA violated in production | Rust becomes business critical | Immediate |
| Dashboard shows 50ms P99 latency | Rust optional optimization | Post-MVP |

---

## Integration Checklist

- [ ] Rust toolchain installed (`rustc --version`)
- [ ] Maturin installed (`maturin --version`)
- [ ] All 3 crates build without errors
- [ ] All tests pass (`cargo test --all`)
- [ ] Python imports work (`python -c "from watcher_embedding import ...`)
- [ ] Existing Python tests still pass (`pytest tests/ -v`)
- [ ] No latency regressions (benchmark.py)
- [ ] Rollback plan is clear (see IMPLEMENTATION.md)

---

## Success Criteria

### Embedding Module
- ✓ Produces identical results to Python (cosine similarity)
- ✓ Passes all entropy tests
- ✓ 10x faster than Python baseline
- ✓ Handles 1000s of requests without memory leak

### Constraints Module
- ✓ All 5 rules produce same results as Python
- ✓ Passes all constraint tests
- ✓ 6x faster than Python
- ✓ Handles invalid input gracefully

### Drift Module
- ✓ Z-scores match Welford's algorithm
- ✓ Passes all drift tests
- ✓ 3x faster than Python
- ✓ Detects anomalies within 1 request

---

## File Locations

```
rust-future/
├── watcher_embedding/
│   ├── Cargo.toml          # Dependencies + metadata
│   ├── build.rs            # Build script (ONNX model download)
│   └── src/
│       ├── lib.rs          # PyO3 bindings
│       ├── model.rs        # ONNX model loader
│       └── embedding.rs    # Encoding + similarity
├── watcher_constraints/
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs          # PyO3 bindings
│       └── executor.rs     # 5 constraint checks
├── watcher_drift/
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs          # PyO3 bindings
│       └── detector.rs     # Welford's algorithm
├── README.md               # Start here
├── OVERVIEW.md             # Why build (strategic)
├── IMPLEMENTATION.md       # How to build (step-by-step)
└── REFERENCE.md            # This file (quick lookup)
```

---

## Dependency Summary

### watcher_embedding
- `pyo3` v0.20.x - Python bindings
- `ort` v1.19.x - ONNX Runtime
- `tokenizers` v0.15.x - HuggingFace tokenizer
- `ndarray` v0.16.x - Numeric arrays
- `once_cell` - Lazy static initialization
- Optional: `rayon` v1.8.x - Parallelization

### watcher_constraints
- `pyo3` v0.20.x
- Optional: `serde` v1.0 - JSON
- Optional: `rayon` v1.8.x - Batch parallelization

### watcher_drift
- `pyo3` v0.20.x
- **Zero other dependencies** (stdlib only)

---

## Estimated Build Time

```
watcher_embedding (first time):  3-5 min (ONNX download + compile)
watcher_constraints:              30-60 sec
watcher_drift:                    10-15 sec
---
Total:                            4-7 minutes first time
Re-builds:                        1-2 minutes
```

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `error: ONNX model not found` | First build, model downloads | Wait 2-3 min, retry |
| `pyo3 version mismatch` | Rust pyo3 ≠ Python pyo3 version | `pip install pyo3 --upgrade` |
| `undefined reference to ONNX` | ONNX Runtime not installed | `cargo update` |
| `ImportError: cannot import` | Maturin not run | `maturin develop --release` |
| `test failed: assertion` | Python ≠ Rust results | Check tolerance in test |

---

## Performance Targets vs. Reality

| Module | Target | Realistic | Variance |
|--------|--------|-----------|----------|
| Embedding | 10x faster | 8-12x | Hardware-dependent |
| Constraints | 6x faster | 5-8x | Compiler optimization |
| Drift | 3x faster | 2-4x | Algorithm difference |

**Key insight:** Rust is fast, but not magic. Measure actual performance in your production environment.

---

## Next: Full Build Guide

See **IMPLEMENTATION.md** for:
- Detailed step-by-step build instructions
- Integration code patterns
- Testing and benchmarking
- Rollback procedures
