
Here's a comprehensive breakdown of **35 edge cases** found across the repository:

---

## Critical (6)

| # | File | Issue |
|---|------|-------|
| 1 | `app/core/storage.py:46` | SQL injection via unescaped encryption key in PRAGMA statement |
| 2 | `app/core/storage.py:406-421` | Race condition — snapshot cache read/delete unprotected by lock |
| 3 | `app/core/entropy.py:136` | Embedding cache cleared entirely (not LRU) + no lock = race condition & latency spike |
| 4 | `app/routes/onboarding.py:184` | `GET /tenants` has **no authentication** — any user can enumerate all tenants |
| 5 | `app/routes/onboarding.py:248` | Bootstrap mode checks user count only — race condition allows privilege escalation to admin |
| 6 | `app/core/onboarding.py:641` | API key validation is O(n) bcrypt — 1000 keys = 1000 slow hashes per request (DoS) |

---

## High (8)

| # | File | Issue |
|---|------|-------|
| 7 | `app/core/security.py:260` | Missing `scope` key in JWT refresh → `KeyError` |
| 8 | `app/core/onboarding.py:670` | Lock acquired inside read loop — key revocation not immediately effective |
| 9 | `app/core/entropy.py:43` | Exactly-3-samples enforced inside function, not at Pydantic level — raises `ValueError` not HTTP error |
| 10 | `app/core/storage.py:296-301` | `WHERE agent_id = NULL` never matches (SQL NULL semantics) — audit chain breaks for `None` agents |
| 11 | `app/core/security.py:524` | `SESSION_TIMEOUT_MINUTES` uses cached module constant, not live env var |
| 12 | `scripts/ops_cli/tenants.py:29,53` | Hard-coded 5s timeout; inconsistent with `keys.py` |
| 13 | `app/core/storage.py:94-172` | No `try/except/finally` around schema creation — connection leak on failure |
| 14 | `app/core/drift.py:93` | Zero std_dev check is correct but fragile — removal would cause division by zero |

---

## Medium (11)

| # | File | Issue |
|---|------|-------|
| 15 | `app/models.py:14` | `samples: List[str]` — no `min_items` constraint |
| 16 | `app/routes/onboarding.py:56` | `domain` field has no `max_length` |
| 17 | `app/core/onboarding.py:674` | `usage_count` INTEGER could theoretically overflow |
| 18 | `app/models.py:21-25` | No size limit on `context`/`variables` dicts — OOM DoS vector |
| 19 | `app/main.py:110-143` | Middleware order: HTTPS enforcement runs after security headers — headers missing on redirects |
| 20 | `app/core/onboarding.py:846` | Audit log query fetches unlimited rows — OOM on large tenants |
| 21 | `app/main.py:313` | `GET /v2/health` always returns **200 OK** even when status is `CRITICAL` |
| 22 | `app/main.py:393` | `rewind_agent` can't distinguish "no snapshot" from "DB error" — both return `200 restored=False` |
| 23 | `app/core/entropy.py:61` | Entropy score silently clamped to `[0,1]` — hides calculation bugs |
| 24 | `app/core/security.py:308` | Token blacklist grows forever — `cleanup_blacklist()` is a no-op (`return 0`) |
| 25 | `app/core/constraints.py:33` | Metrics dict allows unlimited keys — O(n) validation DoS |

---

## Low (10)

| # | File | Issue |
|---|------|-------|
| 26 | `app/core/drift.py:32` | Welford `count` serialization edge case |
| 27 | `app/core/security.py:145` | `additional_claims` can overwrite standard JWT fields (`exp`, `sub`) |
| 28 | `app/core/pdf_export.py:38` | Lines silently truncated at 140 chars — audit data hidden |
| 29 | `app/main.py:213,369` | Naive `utcnow()` timestamps without timezone info |
| 30 | `app/core/wrapper.py:9-31` | Constraint wrapper never used — dead code |
| 31 | `app/core/parallel_validation.py:19` | Unknown action strings fall through to `ALLOW` |
| 32 | `app/core/storage.py:252` | Minor: explicit index check (PKs are auto-indexed, not a real issue) |
| 33 | `app/main.py:176` | Internal errors return unstructured 500 responses |
| 34 | Multiple | No application-level rate limiting |
| 35 | `app/core/entropy.py:101` | Embedding model downloaded on first request — cold start timeout |

---

## Top Priority Fixes

1. **`storage.py:46`** — Validate/escape encryption key before PRAGMA
2. **`onboarding.py:184`** — Add auth to `GET /tenants`
3. **`onboarding.py:641`** — Replace O(n) bcrypt loop with indexed lookup
4. **`entropy.py:136`** — Add lock + LRU eviction to embedding cache
5. **`storage.py:406,420`** — Protect snapshot cache with lock
6. **`onboarding.py:248`** — Validate `tenant_id` existence in bootstrap
7. **`security.py:308`** — Implement actual blacklist cleanup
8. **`main.py:313`** — Return `503` when health status is `CRITICAL`
9. **`storage.py:298`** — Fix `WHERE agent_id = NULL` → `IS NULL`
10. **`main.py:110-143`** — Reorder middleware so HTTPS check runs first
