# Rust Optimization (Future Phase)

**Status:** Scaffolded but not integrated  
**Current Implementation:** Python (production-ready)  
**Rust Status:** Optional optimization for Phase 2

---

## What's Here

This directory contains three Rust crates designed to optimize performance IF needed in the future:

- **watcher_embedding/** - ONNX-based embeddings (10-13x faster)
- **watcher_constraints/** - Fast constraint validation (3-5x faster)
- **watcher_drift/** - Vectorized drift detection (3x faster)

## Setup (One-Time)

The Rust crates need to be organized into this directory. Run the appropriate script:

**Windows:**
```bash
.\organize-crates.bat
```

**macOS/Linux:**
```bash
bash organize-crates.sh
```

This moves the three Rust crates from the root directory into this folder.

## Important: No Effect on Current Code

**The Rust implementation has ZERO impact on the running system.**

The Python implementation in `app/core/` is fully independent and handles all validation.

Rust crates are:
- ✅ Scaffolded and ready to build
- ✅ Fully documented
- ✅ Complete with unit tests
- ❌ NOT integrated into the main codebase
- ❌ NOT called by anything

## When to Build This

Build Rust modules only IF:
- Customers report latency > 100ms under production load
- Throughput hits >100 req/s and CPU becomes bottleneck
- Production data shows need for optimization

Don't build Rust if:
- MVP is shipping (use Python) ← **Current status**
- Customers are happy with 200ms validation
- Infrastructure costs are acceptable

## Documentation

Three consolidated guides in this directory:

1. **OVERVIEW.md** - Strategy, architecture, when to build
2. **IMPLEMENTATION.md** - How to build, step-by-step instructions
3. **REFERENCE.md** - Quick lookup, troubleshooting, checklist
4. **FILE_ORGANIZATION.md** - What files changed, consolidation details

## Build Timeline (If Needed)

If you decide to build Rust modules: 8-12 days from start to production.

Follow `IMPLEMENTATION.md` step-by-step.

## Project Structure

```
rust-future/
├─ README.md (this file)
├─ OVERVIEW.md (strategy & architecture)
├─ IMPLEMENTATION.md (build instructions)
├─ REFERENCE.md (quick lookup & troubleshooting)
│
├─ watcher_embedding/
│  ├─ Cargo.toml
│  ├─ build.rs
│  └─ src/ (lib.rs, model.rs, embedding.rs)
│
├─ watcher_constraints/
│  ├─ Cargo.toml
│  └─ src/ (lib.rs, executor.rs, parser.rs)
│
└─ watcher_drift/
   ├─ Cargo.toml
   └─ src/ (lib.rs, detector.rs)
```

---

**TL;DR:** Archive of future optimization. Not used today. Keep it for when you need the speed.

See parent README.md for current implementation status.
