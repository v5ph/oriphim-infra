# Repository Organization Blueprint

## Goal
Keep runtime code stable while enforcing predictable placement for product code, operations tooling, and generated artifacts.

## Canonical Top-Level Layout

- `app/` — backend runtime service only
  - `core/` domain logic
  - `routes/` API surface
- `client-dashboard/` — frontend application (see [ORGANIZATION.md](../../client-dashboard/ORGANIZATION.md) for internal structure)
- `client-sdk/` — SDKs and client libraries
- `tests/` — backend test suites (`integration/`, `e2e/`, `performance/`)
- `scripts/` — automation and CLI tooling
  - `ops_cli/` operations commands
  - `setup/` bootstrap utilities
  - `manual_tests/` ad-hoc scripts
- `operations/` — runbooks and operational procedures
- `docs/` — architecture, guides, and reports
- Root infra files only: `Dockerfile`, `docker-compose.yml`, `Makefile`, `pyproject.toml`, `README.md`

## Placement Rules (Enforced)

1. Generated output must never be committed:
   - coverage (`.coverage`, `htmlcov/`)
   - package metadata (`*.egg-info/`)
   - runtime databases and scratch files (`:memory:`, `*.db`)
   - ad-hoc logs (`*.log`)
2. Product docs live under `docs/` only.
3. Root directory should contain only platform entrypoints and infrastructure config.
4. Test artifacts must be written under ignored paths, never repo root.

## Ownership Model

- Backend platform: `app/`, `tests/`, `scripts/ops_cli/`
- Frontend: `client-dashboard/`
- Developer experience / setup: `scripts/setup/`, `Makefile`, `generate_env.py`
- Architecture and process: `docs/`, `operations/`

## Migration Waves

### Wave 1 — Safe Declutter (No Runtime Impact)
- Remove generated artifacts from git tracking.
- Fix stale README/doc links.
- Keep empty operational directories with `.gitkeep` only when needed.

### Wave 2 — Structure Normalization
- Consolidate stray/duplicate docs into `docs/guides/` and `docs/reports/`.
- Standardize naming and remove temporary files.

### Wave 3 — Boundary Hardening
- Add CI checks that block generated artifacts and root clutter regressions.
- Add pre-commit checks for naming/path policy.

## Acceptance Criteria

- No generated artifacts tracked by git.
- Root contains only source domains and infra entry files.
- Every README link resolves.
- New contributor can locate API, dashboard, tests, and docs in under 30 seconds.