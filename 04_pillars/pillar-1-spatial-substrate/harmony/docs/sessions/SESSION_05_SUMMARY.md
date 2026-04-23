# Harmony Spatial Operating System — Pillar I — Spatial Substrate
# Session 05 Summary: REST API Layer

> **Date:** 2026-04-19
> **Session Type:** Technical Build
> **Active Pillar:** Pillar 1 — Spatial Substrate
> **Active Milestone:** Milestone 5 — API Layer
> **Builder Agent:** Spatial Substrate Engineer (Builder Agent 4)
> **Schema Version Affected:** 0.1.3 (no schema changes; API on top of existing schema)

---

## Summary

Built the complete REST API layer exposing the Identity Registry and Alias services as HTTP endpoints. The API is a thin FastAPI shell over the existing `registry.py` and `alias_service.py` modules — no duplication of business logic. Ten deliverables across FastAPI app, three route modules, Pydantic models, connection pool, dev seed script, integration tests (22, all green), ADR-013, ADR index update, session summary, and PM report. Total test count across Sessions 2–5 is 143 passing, 1 pre-existing cell-key failure unrelated to this session.

---

## Files Produced

| # | Deliverable | Path |
|---|-------------|------|
| 1 | FastAPI Application | `harmony/services/api/main.py` |
| 2 | Cell Endpoints | `harmony/services/api/routes/cells.py` |
| 3 | Entity Endpoints | `harmony/services/api/routes/entities.py` |
| 4 | Alias & Namespace Endpoints | `harmony/services/api/routes/aliases.py` |
| 5 | Pydantic Models | `harmony/services/api/models.py` |
| 6 | Database Connection Pool | `harmony/services/api/database.py` |
| 7 | Error Envelope Helper | `harmony/services/api/errors.py` |
| 8 | Import Path Bootstrap | `harmony/services/api/_bootstrap.py` |
| 9 | Seed Script | `harmony/scripts/seed_dev.py` |
| 10 | Test Suite (22 tests) | `harmony/services/api/tests/test_api.py` + `conftest.py` |
| 11 | ADR-013 API Layer Architecture | `harmony/docs/adr/ADR-013-api-layer-architecture.md` |
| 12 | ADR Index (updated) | `harmony/docs/ADR_INDEX.md` |
| 13 | Session Summary (this file) | `harmony/docs/sessions/SESSION_05_SUMMARY.md` |
| 14 | PM Session Report | `PM/sessions/2026-04-19-pillar-1-session-5-api-layer.md` |

All paths are relative to `pillar-1-spatial-substrate/`.

---

## Endpoints Exposed

| Method | Path | Purpose | Status codes |
|---|---|---|---|
| GET | `/health` | Health + DB connectivity | 200 |
| POST | `/cells` | Register a cell (idempotent on cell_key) | 201 new / 200 exists / 400 / 422 |
| GET | `/resolve/cell/{canonical_id}` | Resolve cell by canonical_id | 200 / 404 |
| GET | `/resolve/cell-key/{cell_key}` | Resolve cell by cell_key | 200 / 400 / 404 |
| GET | `/cells/{cell_key}/adjacency?depth=1\|2\|3` | Adjacency ring at depth | 200 / 400 / 404 |
| POST | `/entities` | Register an entity | 201 / 400 |
| GET | `/resolve/entity/{canonical_id}` | Resolve entity by canonical_id | 200 / 404 |
| GET | `/resolve/alias?alias=...&namespace=...` | Resolve alias (namespace required) | 200 / 400 / 404 |
| POST | `/aliases` | Bind alias to canonical_id | 201 / 400 / 404 / 409 |
| POST | `/aliases/retire` | Retire active alias | 200 / 404 |
| POST | `/namespaces` | Register a new namespace | 201 / 400 / 409 |
| GET | `/docs`, `/openapi.json` | Auto-generated OpenAPI UI + schema | 200 |

---

## Verification Results

### Step 1 — Server starts

```
uvicorn harmony.services.api.main:app --host 127.0.0.1 --port 8000
```
INFO: Uvicorn running on http://127.0.0.1:8000. Lifespan event logs confirm pool initialisation.

### Step 2 — /docs loads and lists all endpoints

```
GET /docs           → 200 (Swagger UI HTML)
GET /openapi.json   → 200 (18394 bytes)
```
All 13 routes present in the OpenAPI document, tagged by domain (cells, entities, aliases, system).

### Step 3 — Seed script output

```
Connected to API at http://localhost:8000 — {'status': 'ok', 'schema_version': '0.1.3', 'database': 'connected'}
Registering namespaces
  registered namespace cc.au.nsw.cc (prefix=CC)
  registered namespace au.nsw.central_coast.entities (prefix=EN)
Registering cells
  cell hsam:r00:gbl:czvtf6fgxvptcxjv -> hc_hd7n7p9wr (verified)
  cell hsam:r04:cc:yfme2b4kb7j69717 -> hc_yv26wy8vg (verified)
  cell hsam:r06:cc:za6bzq7gfknrzd5z -> hc_cexq82p2t (verified)
  cell hsam:r08:cc:g2f39nh7keq4h9f0 -> hc_8xsrd97we (verified)
  cell hsam:r10:cc:dpya1spfwh11mf83 -> hc_de26vckn2 (verified)
Registering entities
  entity ent_bld_k3f9m2 -> ent_bld_cv69ma (verified)
  bound alias ENT-1 -> ent_bld_cv69ma
  entity ent_prc_h7w4n1 -> ent_prc_6sh3tv (verified)
  bound alias ENT-2 -> ent_prc_6sh3tv
  entity ent_rod_b2c8v5 -> ent_rod_t127rt (verified)
  bound alias ENT-3 -> ent_rod_t127rt

Seed complete — 5 cells + 3 entities registered.
```

All 5 cells and 3 entities loaded and round-tripped through resolve endpoints. Three cell aliases in the sample file (`CC-D01`, `CC-N042`, `CC-T1089`) were correctly rejected with `422 validation_error` because they contain letters in the number segment — the locked alias regex is `^[A-Z]{2,4}-[0-9]{1,6}$` (digits only after the hyphen). The entity aliases (`ENT-1`, `ENT-2`, `ENT-3`) bound successfully. See §"Open Items" below for the sample-data fix-up follow-up.

### Step 4 — pytest output

```
harmony/services/api/tests/test_api.py    22 passed  (new)
harmony/packages/alias/tests/test_...     62 passed  (Session 4, no regressions)
harmony/packages/cell-key/tests/test_...  59 passed, 1 failed (Session 2, pre-existing)

Total: 143 passed, 1 failed (pre-existing)
```

### Step 5 — Manual curl

```
$ curl -s http://localhost:8000/resolve/cell-key/hsam:r08:cc:g2f39nh7keq4h9f0 | jq .canonical_id
"hc_8xsrd97we"

$ curl -s http://localhost:8000/resolve/cell-key/hsam:r08:cc:g2f39nh7keq4h9f0 | jq .friendly_name
"Gosford Waterfront Cell"
```

The Level 8 Gosford waterfront cell resolves with all fields present — cell_key, canonical_id, centroid ECEF and geodetic, 4 adjacent cell keys, distortion factor, created_at/updated_at timestamps, semantic_labels, status.

### Step 6 — Regression check

Session 4 alias service suite: **62/62 pass.**
Session 2 cell-key suite: **59/60 pass** — one failure (`test_vector_3_antimeridian`) is pre-existing and unrelated to this session. `derive.py` and `test_derive.py` both date from 2026-04-10 and were not modified in Session 5. Flagged for follow-up in the PM report.

---

## Schema & Spec Compliance

| Requirement | Source | Status |
|---|---|---|
| Health check returns `{"status": "ok", "schema_version": "0.1.3"}` | Brief §D1 | Pass — plus `database: connected` |
| POST /cells idempotent on cell_key | Brief §D2 | Pass (test_register_cell_is_idempotent) |
| 201 new vs 200 idempotent on POST /cells | Brief §D2 | Pass |
| GET /resolve/cell/{id} → 404 on missing | Brief §D2 | Pass |
| GET /resolve/cell-key/{key} → 404 on missing | Brief §D2 | Pass |
| Adjacency depth 1/2/3 valid, 4 returns 400 | Brief §D2 | Pass (8, 16, 24 cells respectively) |
| POST /entities anchored to existing cell | Brief §D3 | Pass |
| POST /entities with missing cell errors | Brief §D3 | Pass (400 invalid_entity) |
| GET /resolve/alias requires namespace | alias_namespace_rules §7.4 | Pass (400 namespace_required) |
| POST /aliases → 409 on duplicate active | alias_namespace_rules §5.3 | Pass |
| POST /aliases/retire → 200, 404 on missing | Brief §D4 | Pass |
| POST /namespaces → 201 / 409 | Brief §D4 | Pass |
| Error envelope `{error, detail}` | Brief API §4 | Pass (all error paths) |
| No internal state leaked in errors | Brief API | Pass (500 returns generic) |
| Stateless, no cookies, no sessions | Brief API | Pass |
| OpenAPI metadata (title, version, description) | Brief API | Pass |

---

## Key Decisions (full detail in ADR-013)

1. **FastAPI** for framework — Pydantic-driven validation, auto-OpenAPI, easy async path later.
2. **Resource-first URLs** — `/cells`, `/entities`, `/aliases`, `/namespaces`; resolution via `/resolve/*`; retire as sub-resource `/aliases/retire`.
3. **Idempotency policy.** Cells are idempotent on cell_key; entities are deliberately not (Pillar 2 owns dedup); aliases are idempotent on the full `(canonical_id, alias, namespace)` triplet.
4. **Error envelope** `{"error", "detail"}` is uniform across all non-200 responses. Unhandled exceptions return a generic 500 — never stack traces.
5. **Auth is out of scope** for v0.1.3 but the structure accepts a middleware layer without breaking changes.
6. **Connection pooling** via `psycopg2.ThreadedConnectionPool` — no ORM. The registry's raw SQL remains the source of truth.
7. **Registry modules imported, not duplicated.** `_bootstrap.py` adds the three package `src/` dirs to `sys.path`; routes import `registry`, `alias_service`, `derive` as top-level names. Transitional shim — proper packaging deferred.
8. **Namespace required on alias resolve** is enforced at the route layer *before* the service layer runs, matching `alias_namespace_rules.md §7.4`.

---

## What Is Now Unlocked

1. **Milestone 5 Acceptance:** Every API contract listed in the brief is implemented and tested.
2. **Session 6 end-to-end acceptance test** (alias → canonical → entity → cell) can now run entirely over HTTP.
3. **Cross-pillar integration** — Pillars 2, 3, 4, 5 can consume identity services without a Python dependency on `harmony.packages.registry`.
4. **SDK codegen** — the OpenAPI document supports TypeScript/Go/Swift codegen for pillar-specific client libraries.
5. **Dev seeding is a one-line command** (`python harmony/scripts/seed_dev.py`) once the server is up.

---

## Open Items Carried Forward

1. **Pre-existing Session 2 cell-key test failure** (`test_vector_3_antimeridian`). derive.py and test_derive.py both unmodified in this session. Either the derivation changed between Sessions 2 and 3 without updating the vector, or the vector was miscomputed originally. Needs a short investigation in a follow-up session.
2. **Invalid aliases in sample data** — `CC-D01`, `CC-N042`, `CC-T1089` don't match the locked alias regex (letters after the hyphen). The sample cells register fine; only the alias bind fails. Fix the JSON fixture to use `CC-1`, `CC-42`, `CC-421`, etc.
3. **Package distribution** — sys.path bootstrapping is a shim. A single installable distribution would let the API, tests, and seed script drop the path hack. Low urgency, high cleanliness.
4. **Auth layer** — token-based identity, mint/retire authorisation, rate limiting. Deferred per ADR-013 §D5.
5. **Async PG driver** (asyncpg) for higher concurrency under load. Not needed for pilot scale.
6. **Bulk endpoints** and **pagination** — deferred until a consumer needs them.

---

## Cross-Pillar Implications

- **Pillar 2 (Ingestion):** Can POST to `/cells` and `/entities` from ingestion pipelines. Entity dedup remains Pillar 2's responsibility (D3 of this ADR).
- **Pillar 3 (Rendering):** Can GET `/resolve/cell-key/{key}` and `/cells/{key}/adjacency?depth=2` for LOD prefetch without a direct Python dependency.
- **Pillar 4 (Temporal):** The API currently exposes the present-time view. Adding `?as_of=...` query parameters is additive; ADR-007's reserved columns support this.
- **Pillar 5 (Agents):** Agent sessions must carry a default namespace for `GET /resolve/alias` calls — the API never guesses per ADR-013 §D8.

---

## Environment Snapshot

```
Python:       3.14.3 (venv at pillar-1-spatial-substrate/.venv)
FastAPI:      0.136.0
Pydantic:     2.13.2
psycopg2:     2.9.11
PostgreSQL:   16.13 (Homebrew, :5432)
Database:     harmony_dev
Migrations:   001_initial_schema.sql + 002_alias_namespace_registry.sql applied
HARMONY_DB_URL: postgresql://localhost:5432/harmony_dev
```

---

*End of Session 05 Summary*
