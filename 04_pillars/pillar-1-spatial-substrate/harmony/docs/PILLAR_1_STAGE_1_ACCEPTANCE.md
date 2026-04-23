# Pillar 1 — Stage 1 Acceptance Scorecard

> **Date:** 2026-04-19
> **Session:** 6 — End-to-End Acceptance Test (Milestone 6)
> **Schema Version:** 0.1.3
> **Status:** **PASS — All criteria met.**

---

## Summary

Pillar 1 Stage 1 of the Harmony Spatial Operating System is complete. Every non-negotiable acceptance criterion from `pillar-1-spatial-substrate-stage1-brief.md §9` has been validated against the live HTTP API by the end-to-end test suite at `harmony/tests/test_end_to_end.py`.

The test suite uses HTTP only — no internal Python imports — so the results prove the system works as an external consumer would experience it, including the full stack: FastAPI router, Pydantic validation, error-envelope middleware, psycopg2 connection pool, and PostgreSQL schema.

---

## Acceptance Criteria

| # | Criterion | Status | Test | Evidence |
|---|---|---|---|---|
| AC1 | Alias resolves to canonical ID | **PASS** | Test 4, Test 5 | `GET /resolve/alias?alias=TE-1&namespace=au.nsw.central_coast.e2e_<uuid>` returns `canonical_id` matching the bound cell. `alias_status: "active"`. Regex `^[A-Z]{2,4}-[0-9]{1,6}$` enforced. |
| AC2 | Canonical ID resolves to full metadata | **PASS** | Test 5, Test 9 | `GET /resolve/cell/{canonical_id}` returns every field in the canonical record structure (identity-schema.md §6.1): `canonical_id`, `cell_key`, geometry (edge_length_m, area_m2, distortion_factor), centroids (ECEF + geodetic), `adjacent_cell_keys`, `friendly_name`, `semantic_labels`, lifecycle `status`, `schema_version`, timestamps. |
| AC3 | Cell has BOTH canonical ID and deterministic `cell_key` | **PASS** | Test 1, Test 2 | Response contains both. `canonical_id` matches `^hc_[a-z0-9]{9}$`, `cell_key` matches `^hsam:r[0-9]{2}:[a-z]{2,8}:[0-9a-hjkmnp-tv-z]{16}$`. Re-registering the same geometry returns `200 OK` with identical `canonical_id` and `cell_key`. |
| AC4 | Entity links to primary and secondary cells | **PASS** | Test 3 | Building anchored to L8, parcel to L6, road to L4 with L6+L8 as `secondary_cell_ids`. Every referenced cell resolves via `GET /resolve/cell/{id}`. |
| AC5 | Alias can change without breaking canonical identity | **PASS** | Test 6 | Bound `TE-999` as a second alias on the L8 cell, retired `TE-3`. Retired alias returns `404` on active resolve; new alias resolves to the same `canonical_id`; cell record bytewise unchanged. |
| AC6 | Lifecycle states are enforced | **PASS** | Test 7 | Every registered cell returns `status: "active"`. Attempting to register an entity referencing a non-existent (but format-valid) cell_id returns `400 invalid_entity` — referential integrity is enforced. |
| AC7 | Namespace collisions are handled | **PASS** | Test 8 | Re-binding `TE-1` to a DIFFERENT canonical_id in the same namespace returns `409 alias_conflict` per alias_namespace_rules.md §5.3. Binding `TE-1` in a fresh namespace returns `201 Created`. Both aliases resolve to their respective (distinct) canonical_ids — cross-namespace independence. |
| AC8 | Registry acts as single source of truth | **PASS** | Test 9 | The L4 cell was resolved via three paths — `GET /resolve/cell/{id}`, `GET /resolve/cell-key/{key}`, and through its alias `TE-1` — and all three returned identical records across 15+ fields. |

---

## Additional Validation (not a §9 criterion, but non-negotiable per the locked spec)

| # | Rule | Status | Test | Evidence |
|---|---|---|---|---|
| X1 | Alias resolve without namespace returns 400 (`alias_namespace_rules.md §7.4`) | **PASS** | Test 10 | `GET /resolve/alias?alias=TE-1` (no namespace) returns `400 namespace_required`. |
| X2 | Adjacency ring size = 8k for non-boundary cells (`cell_adjacency_spec.md §4.1`) | **PASS** | Test 5 (ring-1 = 8) | The L8 Gosford waterfront cell is 8290 grid cells from the nearest face edge; its ring-1 returns exactly 8 cell_keys. |

---

## Test Count

| Suite | Tests | Pillar 1 Session |
|---|---:|---|
| Cell-key derivation | 60 | Session 2 |
| Alias service | 62 | Session 4 |
| API integration (with 8k ring guard) | 25 | Sessions 5, 5B |
| End-to-end acceptance (HTTP-only) | 10 | Session 6 |
| **Total** | **157** | **All passing** |

Zero failing tests across the full Pillar 1 Stage 1 code base.

---

## Evidence Artefacts

- Test file (HTTP-only): `harmony/tests/test_end_to_end.py`
- Test setup: `harmony/tests/conftest.py` (session-scoped DB truncation via psql)
- Run command: `pytest harmony -v`
- Full server log during the acceptance run: server started, health check green (`database: connected`, `schema_version: 0.1.3`), 10 e2e tests passed, 25 API tests passed, 62 alias tests passed, 60 cell-key tests passed.

---

## Design Notes (for future pillars)

1. **Cell → Entity direction is not a public API endpoint today.** The canonical direction is entity → cell (every entity carries `primary_cell_id` and `secondary_cell_ids[]`). Test 5 validates the bidirectional chain by resolving from alias → cell and then verifying every entity we registered points back to that cell. Pillar 2 (Ingestion) or a future query endpoint can add the inverse lookup as needed.

2. **Idempotent cell POST returns existing record unchanged.** By design, re-posting a cell with new `friendly_name` / `semantic_labels` does NOT update the metadata. This is the correct REST semantic for an idempotent create (RFC 7231). If metadata updates are needed, a future `PATCH /cells/{id}` endpoint should be introduced.

3. **Manual alias binding uses the namespace's prefix convention.** Auto-generation via the counter is exposed in `alias_service.auto_generate_alias()` but not in the HTTP API. Session 6 uses manual assignment (`TE-1`, `TE-2`, `TE-3`) which also validates correctly.

---

## What This Unlocks

- **Pillar 2 (Data Ingestion)** — HTTP-based registration of cells and entities is live. Pipelines can stream records through `POST /cells` and `POST /entities` without a Python dependency.
- **Pillar 3 (Rendering)** — Adjacency prefetch via `GET /cells/{cell_key}/adjacency?depth={1,2,3}` is available for LOD streaming.
- **Pillar 4 (Temporal Versioning)** — Reserved columns (`valid_from`, `valid_to`, `version_of`, `temporal_status`) are in the schema, ready for activation.
- **Pillar 5 (Interaction / Agents)** — The alias → canonical → entity → cell chain works end-to-end, making the Conversational Spatial Agent (ADR-009) implementable.

---

## Explicitly Out of Scope

(not part of Stage 1, tracked for later)

- Authentication / authorisation
- Async database driver (asyncpg)
- Bulk endpoints and pagination
- Package distribution refactor (remove sys.path shim)
- Pillar 3 framework selection
- Temporal versioning activation
- Auto-generation endpoint for alias counter
- `GET /cells/{id}/entities` inverse-index endpoint

---

## Verdict

**Pillar 1 Stage 1 is complete.** Every acceptance criterion passed. The identity substrate is operational as a stable HTTP contract. Pillar 2 is unblocked.

---

*Scorecard signed off by Session 6 acceptance run — 2026-04-19.*
