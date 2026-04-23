# ADR-014 — Pillar 1 Stage 1 Completion

> **Status:** Accepted
> **Date:** 2026-04-19
> **Pillar:** 1 — Spatial Substrate
> **Milestone:** 6 — End-to-End Test
> **Supersedes:** —
> **Superseded by:** —
> **Relates to:** ADR-001 through ADR-013 (the full Pillar 1 ADR chain)

---

## 1. Context

Sessions 1 through 5 built the identity substrate: schemas (ADR-001, ADR-004, ADR-010), cell geometry and derivation (ADR-002, ADR-003), adjacency (ADR-005), aliases (ADR-006, ADR-012), temporal-versioning reservations (ADR-007), named-entity boundaries (ADR-008), agent-layer groundwork (ADR-009), identity-generation order (ADR-011), and the REST API (ADR-013). Session 5B closed out three latent issues.

This ADR records the decision that Pillar 1 Stage 1 is complete and captures the state of the system at the close of Milestone 6.

---

## 2. Decision

**Pillar 1 Stage 1 of the Harmony Spatial Operating System is complete.** Every non-negotiable acceptance criterion from `pillar-1-spatial-substrate-stage1-brief.md §9` has been validated end-to-end via the HTTP API. The scorecard is at `harmony/docs/PILLAR_1_STAGE_1_ACCEPTANCE.md`.

### 2.1 Acceptance Criteria Status

| # | Criterion | Status |
|---|---|---|
| AC1 | Alias resolves to canonical ID | **PASS** |
| AC2 | Canonical ID resolves to full metadata | **PASS** |
| AC3 | Cell has BOTH canonical ID and deterministic cell_key | **PASS** |
| AC4 | Entity links to primary and secondary cells | **PASS** |
| AC5 | Alias can change without breaking canonical identity | **PASS** |
| AC6 | Lifecycle states are enforced | **PASS** |
| AC7 | Namespace collisions are handled | **PASS** |
| AC8 | Registry acts as single source of truth | **PASS** |

### 2.2 Cumulative Test Count

| Suite | Tests |
|---|---:|
| Cell-key derivation (Session 2) | 60 |
| Alias service (Session 4) | 62 |
| API integration (Sessions 5, 5B) | 25 |
| End-to-end HTTP acceptance (Session 6) | 10 |
| **Total** | **157** |

All 157 tests pass. No skipped, no xfail, no pre-existing failures.

---

## 3. What This Unlocks

- **Pillar 2 (Data Ingestion).** The HTTP registration path is stable. Ingestion pipelines can stream cell and entity records through `POST /cells` and `POST /entities` without a Python dependency on the registry package. Entity deduplication is Pillar 2's responsibility by design (ADR-013 §D3).
- **Pillar 3 (Rendering).** Adjacency ring queries at depth 1–3 are available for LOD prefetch. The 8k ring invariant (`cell_adjacency_spec.md §4.1`) is now CI-pinned.
- **Pillar 4 (Temporal Versioning).** The reserved columns (`valid_from`, `valid_to`, `version_of`, `temporal_status`) are in the schema. Adding `?as_of=...` query parameters to existing read endpoints will be purely additive when ADR-007 is activated.
- **Pillar 5 (Interaction / Conversational Spatial Agent).** The alias → canonical → entity → cell chain resolves bidirectionally over HTTP. The three-layer agent model (ADR-009) is implementable on top of this contract.
- **SDK codegen.** The OpenAPI document at `/openapi.json` is the canonical machine-readable API. TypeScript, Go, or Swift clients can be generated directly.

---

## 4. Explicitly Out of Scope

The following items are intentionally not in Stage 1 and are deferred to later milestones or a Stage 2 if one is chartered:

- **Authentication and authorisation.** ADR-013 §D5 captured the structural readiness — adding auth later is additive, not a breaking change.
- **Async database driver.** Current psycopg2 blocking calls under FastAPI's thread-pool are sufficient for pilot scale. Moving to asyncpg is a capacity concern, not a correctness one.
- **Bulk endpoints and pagination.** No consumer needs them yet.
- **Package distribution refactor.** The `_bootstrap.py` sys.path shim is explicitly transitional (ADR-013 §D7). A single `pyproject.toml` that ships the registry, alias, cell-key, and api modules as one installable distribution is a cleanup, not a feature.
- **`GET /cells/{id}/entities` inverse index.** Not needed for Session 6 acceptance; Pillar 2 or a future ADR can add it.
- **Auto-generation HTTP endpoint.** `alias_service.auto_generate_alias()` exists and is tested, but is not exposed via a dedicated route. Manual assignment works fine for the pilot.
- **Pillar 3 framework selection.** The rendering layer's engine (Three.js, Unity, bespoke WebGPU, etc.) is deliberately not decided in Pillar 1.
- **Temporal versioning activation.** The columns exist; the logic is Pillar 4's.
- **Sample-data alias format relaxation.** If Pillar 2 needs alphanumeric suffixes in aliases (e.g. CC-D01), that is a spec amendment, not a Pillar 1 change.

---

## 5. Risk Note — Antimeridian ULP Drift

The antimeridian cell_key derivation (lat=0, lon=180) exhibits a one-ULP floating-point difference between Python 3.14 and the environment in which Vector 3 was originally documented. Session 5B investigated, confirmed the algorithm is unchanged, and updated the test vector and spec to match current production.

This is **not** a correctness failure — within any single Python/libm environment, derivation remains deterministic. But cross-environment bit-identity is only guaranteed for the two other test vectors. For global deployments where multiple independent systems compute cell_keys for antipodal points, a future hardening task should either pin a specific libm or snap pre-hash coordinates to a coarser precision. For the Central Coast pilot it is a non-issue.

---

## 6. Recommendation

**Activate Pillar 2 (Data Ingestion) as the next sequential build.** Per the project's build plan, Pillar 2 is the natural consumer of the Pillar 1 API and will both exercise the contract at scale and surface any latent issues (entity dedup, bulk throughput, ingestion retries) before they block downstream pillars.

If a Pillar 1 Stage 2 is ever chartered — covering auth, async, bulk endpoints, and the inverse-index endpoint — it should be parallel to Pillar 2 work, not ahead of it. None of the deferred items block Pillar 2.

---

## 7. Consequences

**Positive:**
- A documented, stable HTTP contract covering identity, aliases, entities, and adjacency.
- 157 tests pinning the invariants in CI — regressions surface immediately.
- Every pillar downstream has a clean integration surface.

**Neutral:**
- The sys.path bootstrap, manual alias binding, and absence of auth are all explicitly deferred. They do not block Pillar 2.

**Negative:**
- None at the Stage 1 scope. The deferred items are known and ADR-referenced.

---

*ADR-014 — accepted 2026-04-19, closing Pillar 1 Stage 1.*
