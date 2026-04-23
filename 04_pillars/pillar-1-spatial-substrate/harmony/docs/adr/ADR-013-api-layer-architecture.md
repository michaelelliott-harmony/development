# ADR-013 — API Layer Architecture

> **Status:** Accepted
> **Date:** 2026-04-19
> **Pillar:** 1 — Spatial Substrate
> **Milestone:** 5 — API Layer
> **Supersedes:** —
> **Superseded by:** —
> **Relates to:** ADR-001 (Layered Identity), ADR-004 (cell_id vs cell_key), ADR-006 (Alias Namespace Model), ADR-012 (Alias Generation Architecture)

---

## 1. Context

Sessions 2–4 delivered the Identity Registry and Alias services as Python libraries with direct database access. For those services to be consumed by the other Harmony pillars (Visual Fidelity, Data Ingestion, Rendering, Temporal Versioning, Interaction), a language-neutral network interface is required. This ADR records the decisions made in Session 5 when wrapping those services in a REST API.

---

## 2. Decisions

### D1 — FastAPI as the framework

**Chosen:** FastAPI 0.136 over Flask/Starlette/bare-ASGI.

**Why:**

- Pydantic v2 integration gives us model-driven validation that enforces the same regexes defined in `cell_identity_schema.json` and `alias_namespace_rules.md`. One source of truth, one contract.
- Auto-generated OpenAPI schema at `/docs` and `/openapi.json` — consumers (other pillars, SDKs, agents) can code against a published contract without hand-written docs drifting.
- Async-capable without forcing async everywhere. The registry services remain synchronous psycopg2 calls; FastAPI wraps them in a thread pool.
- Dependency-injection primitives make it easy to add auth middleware later (see D5).

**Alternatives rejected:** Flask (no native OpenAPI, no first-class Pydantic), bare Starlette (no request-body validation convenience), gRPC (HTTP/JSON is the lower-friction default for Milestone 5; gRPC remains a future option for inter-pillar links).

---

### D2 — Endpoint naming: verb-free, resource-first

The URL shape is:

```
POST /cells                          POST /entities                POST /namespaces
POST /aliases                        POST /aliases/retire
GET  /resolve/cell/{canonical_id}    GET  /resolve/cell-key/{cell_key}
GET  /resolve/entity/{canonical_id}  GET  /resolve/alias?alias=...&namespace=...
GET  /cells/{cell_key}/adjacency?depth={1|2|3}
GET  /health
```

**Why:** Three conventions, deliberately:

1. **Collections are pluralised nouns** (`/cells`, `/entities`, `/aliases`, `/namespaces`). POST to the collection registers a member.
2. **Resolution uses a `/resolve/` prefix** rather than overloading the collection URL. The alias rules spec (§7.1) uses `GET /resolve/alias?...` literally — keeping `/resolve/` in the URL preserves that traceability. It also makes clear that `GET /cells/{id}` is not yet defined (nor needed) — all reads go through `/resolve/`.
3. **Non-idempotent lifecycle ops use an action verb** (`/aliases/retire`). RFC 7231 sub-resource style is preferred over query-string verbs or PATCH-with-body-semantics, because retirement is a semantic state change the client is explicitly requesting, not a generic attribute edit.

**Why `/resolve/cell-key/{key}`** separately from `/resolve/cell/{id}`: The `cell_key` and `canonical_id` are both primary identifiers but serve different purposes (ADR-004). Two endpoints document this distinction clearly and avoid the ambiguity of a single polymorphic route.

---

### D3 — Idempotent vs non-idempotent endpoints and status codes

| Endpoint | Idempotent? | Success codes |
|---|---|---|
| `POST /cells` | Yes — cell_key is deterministic | `201 Created` new / `200 OK` exists |
| `POST /entities` | No — entity_id is randomly generated per call | `201 Created` only |
| `POST /namespaces` | No — second call returns `409 Conflict` | `201 Created` only |
| `POST /aliases` | Yes within (canonical_id, alias, namespace) triplet | `201 Created` / `409 Conflict` |
| `POST /aliases/retire` | Yes — second call on a retired alias returns `404` | `200 OK` |
| `GET /resolve/*`, `/health`, `/adjacency` | Yes — safe reads | `200 OK` |

**Why:**

- Cells are idempotent because the cell_key is deterministic (Session 2 — derived from centroid geometry). Re-registration returning 200 is safe and the correct REST semantics (RFC 7231 §4.3.3 and §6.3).
- Entities are explicitly not idempotent against content. "The same building registered twice produces two entity IDs" (Session 3 decision D3 and registry.py:815). Deduplication is the responsibility of the ingestion pipeline (Pillar 2), not the API. POST `/entities` always returns 201 on success.
- Aliases are the tuple `(alias, namespace, canonical_id)` — re-binding the exact triplet is idempotent; binding a different canonical_id to an already-active tuple is `409` per `alias_namespace_rules.md §5.3`.

---

### D4 — Error response format

Every error returns the same envelope:

```json
{ "error": "<machine_code>", "detail": "<human_readable>" }
```

**Why:**

- Consumers can branch on `error` without parsing free-text `detail`.
- One format for all status codes; no special case for validation errors vs NotFound.
- Internal state is never exposed. No stack traces, no SQL fragments, no connection strings. Known exceptions (`AliasConflictError`, `ValueError` from the registry) are translated into envelopes with generic wording.
- The `500` path logs the exception server-side but returns `"internal_server_error"` / `"Unexpected server error"` — no leakage.

Status-code discipline follows the brief:
- `200` successful retrieval or idempotent registration
- `201` new creation
- `400` malformed input, missing required parameter, depth out of range
- `404` object not found, namespace not registered, alias not in namespace
- `409` conflict on a constraint the caller can resolve (already active, grace period)
- `422` Pydantic body validation failure (schema mismatch) — caller should fix the request shape
- `500` genuine server error

The split between `400` and `422` is deliberate: `422` means the request failed shape validation at the Pydantic layer before any business logic ran; `400` means the request was well-shaped but semantically invalid.

---

### D5 — Authentication is deferred but shaped for

v0.1.3 explicitly excludes auth. The scope note in the brief permits this. The endpoint structure is designed so that adding auth later is additive, not a breaking change:

- All endpoints are stateless, cookie-free, session-free. Nothing leaks identity through ambient state.
- Every endpoint accepts request headers only as FastAPI parameters; no global header magic.
- The route modules (`cells.py`, `entities.py`, `aliases.py`) each take a `APIRouter` — a FastAPI dependency `Depends(get_current_principal)` can be added to a router globally or per-route when auth lands.
- The error envelope already has an `error` code slot — `"auth_required"`, `"forbidden"`, `"token_expired"` codes can slot in cleanly alongside `"alias_not_found"`.

Authorisation for alias mint/retire (the open item from `alias_namespace_rules.md §11`) is not in this ADR's scope but the placeholder is structurally compatible.

---

### D6 — Connection pooling via psycopg2 ThreadedConnectionPool

The API layer does not introduce an ORM. The registry (`registry.py`) and alias service (`alias_service.py`) already use raw SQL via psycopg2 — that's the source of truth. The API adds only a pool wrapper (`database.py`):

- `ThreadedConnectionPool(minconn=1, maxconn=10)` — safe under FastAPI's default thread-pool executor for sync endpoints.
- Context manager `get_connection()` yields a pooled connection and auto-rolls-back on exception before returning the connection to the pool.
- Connection string is read from `HARMONY_DB_URL` — the same env var the CLI scripts use — no second config surface.

**Why not SQLAlchemy:** The existing services already hand-wrote SQL tuned to the schema (partial unique indexes, `UPDATE ... RETURNING` for atomic counters, ARRAY types). Adding an ORM would invert the source of truth. The API layer stays a thin shell.

---

### D7 — Registry and alias modules are imported, not duplicated

The registry, alias, and cell-key packages live at `harmony/packages/{registry,alias,cell-key}/src/`. Rather than copying them into the API tree, the API layer prepends their `src/` directories to `sys.path` in a small `_bootstrap.py` module. Routes import `registry`, `alias_service`, and `derive` as top-level names.

**Why:** Duplicating the registry code would create two sources of truth. Packaging them properly (pyproject.toml + editable install) is the right long-term answer but would require a refactor of the existing test layouts (which also use sys.path manipulation). The `_bootstrap.py` approach ships the API in-scope for Session 5 without perturbing the existing packages.

**Flag:** A future session should collapse the three sub-packages into a single installable distribution (`pip install -e .`). The sys.path approach is a transitional shim.

---

### D8 — Namespace required on alias resolve

`alias_namespace_rules.md §7.4` is explicit: the service never guesses a namespace. The API enforces this by making `namespace` a required query parameter on `GET /resolve/alias`. Omitting it returns `400 namespace_required` before the service layer is touched.

**Why record as a decision:** To make it harder to accidentally relax later. Any future "smart default namespace" feature must go through an explicit new endpoint or an explicit per-service config contract — not a silent fallback on this endpoint.

---

## 3. Consequences

**Positive:**

- Other pillars can consume identity services over HTTP without a Python dependency on `harmony.packages.registry`.
- The OpenAPI document at `/openapi.json` becomes the canonical machine-readable API contract — SDK codegen for TypeScript, Go, Swift etc. is now trivial.
- Validation is centralised: one Pydantic model mirrors one JSON-schema pattern. A regex change in the locked spec is a one-line change in `models.py`.
- Error envelopes are uniform — callers don't have to handle three different error shapes.

**Negative / trade-offs:**

- Registry imports rely on sys.path manipulation (D7). This is explicitly a transitional shim. Any future packaging refactor needs to update both the registry/alias test suites and the API `_bootstrap.py`.
- The `/entities` POST is intentionally non-idempotent. Clients that retry on network failure must handle the possibility of duplicate entity records at the ingestion layer (Pillar 2).
- No rate limiting, no auth, no CSRF — correct for v0.1.3 but must be in place before any non-local deployment.
- FastAPI's thread-pool execution for sync handlers introduces a ~10–20 request-per-worker ceiling under psycopg2's blocking calls. For the Central Coast pilot this is fine; global scale requires async Postgres drivers (asyncpg) in a future milestone.

---

## 4. Verification

- 22 integration tests pass against a live PostgreSQL instance (`harmony/services/api/tests/test_api.py`).
- The 62 alias-service tests (Session 4) and 59 of the 60 cell-key tests (Session 2) continue to pass; the one failing vector is pre-existing and unrelated to this session.
- The seed script (`harmony/scripts/seed_dev.py`) successfully round-trips all 5 cells and all 3 entities through the API.
- `GET /docs` and `GET /openapi.json` render and are internally consistent with the route definitions.

---

## 5. Open Items

- Packaging: pull the three sub-packages into a single `pip install`-able distribution.
- Auth layer: token-based identity, mint/retire authorisation, rate limiting.
- Async database driver (asyncpg) for higher concurrency once traffic justifies it.
- Bulk endpoints (`POST /cells/bulk`, `POST /aliases/bulk`) for ingestion pipelines.
- Pagination on `GET /cells` and `GET /aliases` list endpoints (not yet exposed — deferred).

---

*ADR-013 — accepted 2026-04-19, Pillar 1 Session 5.*
