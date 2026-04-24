# Harmony ADR Index — Canonical Sequence

> **Version:** 2.0
> **Status:** Authoritative after 2026-04-21 reorganisation
> **Date:** 2026-04-21
> **Purpose:** Single canonical sequence of Architecture Decision Records
> for the Harmony project.

---

## Canonical Sequence

| # | Title | Status | File |
|---|---|---|---|
| ADR-001 | Layered Identity Model | Accepted | `ADR-001-layered-identity.md` — authoritative copy resides inside nested source tree at `04_pillars/pillar-1-spatial-substrate/harmony/docs/adr/ADR-001-layered-identity.md` |
| ADR-002 | Gnomonic Cube Projection | Stub — To be extracted | `ADR-002-gnomonic-cube-projection.md` |
| ADR-003 | Cell Key Derivation Architecture | Accepted | `ADR-003-cell-key-derivation.md` — authoritative copy in nested source tree |
| ADR-004 | `cell_id` vs `cell_key` Dual-Identifier Principle | Accepted | `ADR-004-cell-id-vs-cell-key.md` — authoritative copy in nested source tree |
| ADR-005 | Cell Adjacency Model | Stub — To be extracted | `ADR-005-cell-adjacency-model.md` |
| ADR-006 | Alias Namespace Model | Accepted | `ADR-006-alias-namespace-model.md` — authoritative copy in nested source tree |
| ADR-007 | Temporal Versioning | Accepted | `ADR-007-temporal-versioning.md` — authoritative copy in nested source tree |
| ADR-008 | Named-Entity Resolution Boundary | Accepted | `ADR-008-named-entity-resolution-boundary.md` — authoritative copy in nested source tree |
| ADR-009 | Three-Layer Agent Model | Accepted | `ADR-009-three-layer-agent-model.md` — authoritative copy in nested source tree |
| ADR-010 | Spatial Geometry Schema Extension (v0.1.3) | Accepted | `ADR-010-spatial-geometry-schema-extension.md` — authoritative copy in nested source tree |
| ADR-011 | Gate 3 Closure — Identity Generation Order | Accepted | `ADR-011-gate-3-closure-identity-generation-order.md` — authoritative copy in nested source tree |
| ADR-012 | Alias Generation Architecture | Accepted | `ADR-012-alias-generation-architecture.md` — authoritative copy in nested source tree |
| ADR-013 | API Layer Architecture (FastAPI) | Accepted | `ADR-013-api-layer-architecture.md` — authoritative copy in nested source tree |
| ADR-014 | Pillar 1 Stage 1 Completion | Accepted | `ADR-014-pillar-1-stage-1-completion.md` — authoritative copy in nested source tree |
| ADR-015 | Adaptive Volumetric Cell Extension | Accepted | `ADR-015-adaptive-volumetric-cell-extension.md` (populated 2026-04-20 by p1-stage2 dispatch) |
| ADR-016 | Temporal Trigger Architecture — Permit Feed Integration | Accepted | `ADR-016-temporal-trigger-architecture.md` (renumbered from ADR-015 during reorganisation) |
| ADR-017 | Pillar 1 Stage 2 Implementation Decisions | Accepted | `ADR-017-pillar-1-stage-2-implementation.md` |
| ADR-018 | Data Tier Model and Provenance Hierarchy | Proposed | `ADR-018-data-tier-model-and-provenance-hierarchy.md` |
| ADR-019 | Tier Enforcement Architecture | Proposed | `ADR-019-tier-enforcement-architecture.md` |
| ADR-020 | CRS Normalisation Strategy | Proposed | `ADR-020-crs-normalisation-strategy.md` |
| ADR-021 | Geometry Quarantine Lifecycle | Proposed | `ADR-021-geometry-quarantine-lifecycle.md` |
| ADR-022 | Rendering Asset Format and Data Contract | Proposed | `ADR-022-rendering-asset-format-and-data-contract.md` |

---

## Why ADRs 001, 003, 004, 006–014 Are Not Physically Here

During the 2026-04-21 reorganisation the nested source tree at
`04_pillars/pillar-1-spatial-substrate/harmony/` was designated
untouchable per safety boundary rules. The authoritative ADR files
for ADR-001, ADR-003, ADR-004, ADR-006 through ADR-014 remain inside
`harmony/docs/adr/` and are referenced from this index.

When the nested source tree is promoted to the repo root (future
work), the ADRs will move to `docs/adr/` alongside the stubs and
ADR-016 currently here.

---

## Next Available Number

ADR-023.

> Note: ADR-017 was allocated to the Stage 2 implementation ADR even though
> the Stage 2 dispatch brief (`docs/dispatch/dispatch-p1-stage2-20260420/`)
> named it ADR-016. That dispatch was authored before the 2026-04-21
> reorganisation renumbered the Pillar 2 temporal-trigger ADR to ADR-016.
> Stage 2 followed the index, not the stale dispatch reference.

Builder Agents producing new ADRs must:

1. Check this index for the next available number
2. Use the next integer — no parallel sequences
3. Update this index with the new entry

---

## History

- **2026-04-10** — ADR_INDEX v1.0 established canonical sequence at
  v0.1.3 merge (in nested source tree)
- **2026-04-20** — ADR-015 populated from stub (Stage 2 dispatch);
  ADR-017 added for Stage 2 implementation decisions
- **2026-04-23** — ADR-018 entry added (Proposed — content pending);
  pillar-2 docs filed at `04_pillars/pillar-2-data-ingestion/docs/`;
  zip's pre-reorg ADR-015 draft archived at
  `docs/adr/variations-archive/ADR-015-temporal-trigger-draft-pre-reorg.md`
- **2026-04-21** — ADR_INDEX v2.0 authored at repo root during
  reorganisation. Stubs created for ADR-002, ADR-005, ADR-015. Pillar-2
  ADR-015 (temporal trigger) renumbered to ADR-016 to reserve ADR-015
  for adaptive volumetric cell extension per V1.1.0 spec.
