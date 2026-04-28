# Harmony — Decision Log
## Append-only. Never edit or delete existing entries.
## Add new entries at the bottom.

This log captures architectural decisions made between formal spec versions.
Every session that produces an architectural decision appends an entry here.
When a new spec version is compiled, entries are marked with the version
that incorporated them.

---

## Entry Format

### DEC-{NNN} | {YYYY-MM-DD} | {Pillar or Area}
**Decision:** What was decided.
**Impact:** What this changes in the architecture or build plan.
**ADR:** ADR-{NNN} if applicable, or "None — logged here only"
**Status:** Accepted | Pending Review
**Spec version:** V{N}.{N}.{N} if incorporated, or "Pending V1.2.0"

---

## Entries

### DEC-001 | 2026-04-13 | Pillar 1 — Spatial Substrate
**Decision:** Formalised six-layer identity model: Canonical ID, Cell Key, Human Alias (namespaced, e.g. `CC-421`), Friendly Name, Known Names (indexed), Semantic Labels. Governing principle: "Canonical IDs are for truth. Aliases are for people. Semantic labels are for intelligence."
**Impact:** Replaces V1.0's conceptual "stable identity" language with the formally articulated layered model that Pillar 1 has built against.
**ADR:** ADR-001 — Layered Identity Model
**Status:** Accepted
**Spec version:** V1.0.1
**Source:** Master_Spec_Variations/variations/applied/VAR-001-layered-identity-model.md

---

### DEC-002 | 2026-04-13 | Pillar 1 — Spatial Substrate
**Decision:** Every cell carries both an opaque immutable canonical ID (`cell_id`) and a deterministic derivable substrate key (`cell_key`). The canonical ID never changes and is the reference for cross-system lookups; the cell key can be recomputed from spatial parameters and is used for substrate-level operations such as neighbour discovery.
**Impact:** Resolves the stability-vs-reproducibility tension in the spatial substrate.
**ADR:** ADR-004 — `cell_id` vs `cell_key` Dual-Identifier Principle
**Status:** Accepted
**Spec version:** V1.0.1
**Source:** Master_Spec_Variations/variations/applied/VAR-002-two-identifier-substrate.md

---

### DEC-003 | 2026-04-13 | Pillar 1 — Spatial Substrate (Schema)
**Decision:** Bitemporal versioning adopted at the schema layer. Four reserved fields added to cell and entity schemas: `valid_from`, `valid_to`, `version_of`, `temporal_status`. System time (`created_at`/`updated_at`) distinguished from valid time. Active implementation deferred to Pillar 4.
**Impact:** Schema is forward-compatible — Pillar 4 can activate temporal versioning without breaking changes.
**ADR:** ADR-007 — Temporal Versioning
**Status:** Accepted
**Spec version:** V1.0.1
**Source:** Master_Spec_Variations/variations/applied/VAR-003-bitemporal-versioning.md

---

### DEC-004 | 2026-04-13 | Pillar 1 — Identity Resolution
**Decision:** The Identity Registry exposes name-lookup primitives (exact and fuzzy lookup, multi-name via `known_names`, ranked candidate returns with confidence scores, context-filtered lookup). Full natural-language resolution (pronouns, paraphrase, conversational state) is composed by the Conversational Spatial Agent (Class III), combining Pillar 1 primitives, Pillar 4 semantic search, and Pillar 5 conversational context.
**Impact:** Formal boundary between substrate-level naming and runtime-level language understanding.
**ADR:** ADR-008 — Named-Entity Resolution Boundary
**Status:** Accepted
**Spec version:** V1.0.1
**Source:** Master_Spec_Variations/variations/applied/VAR-004-named-entity-resolution.md

---

### DEC-005 | 2026-04-13 | Pillar 1 — Identity Format
**Decision:** Canonical ID format carries no embedded operator, region, or jurisdiction — deliberately federation-compatible. "Single source of truth" refers to the logical registry, not a centralised deployment. Current deployment is centralised but the format and registry contract support a federated, multi-issuer model.
**Impact:** Preserves Gap 4 (Sovereignty/Federation) as an implementation choice, not an identity-format constraint.
**ADR:** None — logged here only
**Status:** Accepted
**Spec version:** V1.0.1
**Source:** Master_Spec_Variations/variations/applied/VAR-005-federation-compatible-identity.md

---

### DEC-006 | 2026-04-13 | Agent Model
**Decision:** Agent model structured into three layers: Builder Agents (build-phase engineering), Runtime Agent Classes I/II/III (V1.0's production infrastructure), and Digital Team Members (production, customer-facing agents). V1.0 already defined the Runtime Agent Classes; this variation adds the surrounding layers.
**Impact:** Clarifies the separation between the agents building Harmony and the agents Harmony will deploy.
**ADR:** ADR-009 — Three-Layer Agent Model
**Status:** Accepted
**Spec version:** V1.0.1
**Source:** Master_Spec_Variations/variations/applied/VAR-006-three-layer-agent-model.md

---

### DEC-007 | 2026-04-13 | Pillar 1 — Schema
**Decision:** Cell and entity record schemas expanded in v0.1.2. Cell records now include: `canonical_id`, `cell_key`, `human_alias`, `alias_namespace`, `friendly_name`, `known_names` (reserved, indexed), `semantic_labels`, `valid_from`/`valid_to` (reserved), `version_of` (reserved), `temporal_status` (reserved), `fidelity_coverage`, `lod_availability`, `asset_bundle_count`, `references.asset_bundles` (all reserved for Pillar 2). Entity records include: `canonical_id` with embedded subtype, `entity_subtype`, `human_alias`/`alias_namespace`, `friendly_name`, `known_names` (reserved), `semantic_labels`, temporal fields (reserved), `references.primary_cell_id`, `references.secondary_cell_ids`.
**Impact:** Substrate schema is now Pillar 2/4/5 ready via reserved fields.
**ADR:** None directly — schema-level embodiment of ADR-001/004/007/008
**Status:** Accepted
**Spec version:** V1.0.1
**Source:** Master_Spec_Variations/variations/applied/VAR-007-schema-field-additions.md

---

### DEC-008 | 2026-04-13 | Gap Register
**Decision:** Gap 3 (Temporal Memory) closed at the substrate layer, awaiting Pillar 4 activation. Gap 5 (LLM Integration / Named-Entity Resolution) closed at the substrate layer, awaiting Pillar 5 activation. Gap 4 (Sovereignty/Federation) preserved — identity format confirmed federation-compatible. Gaps 1, 2, and 6 remain open and unaffected.
**Impact:** V1.0 Gap Register updated to reflect Pillar 1's progress.
**ADR:** None — logged here only
**Status:** Accepted
**Spec version:** V1.0.1
**Source:** Master_Spec_Variations/variations/applied/VAR-008-gap-register-updates.md

---

### DEC-009 | 2026-04-13 | Pillar 1 — Spatial Indexing
**Decision:** Harmony has committed to building its own spatial indexing system — the Harmony Cell System — rather than adopting an existing open-source solution such as Uber's H3 or Google's S2. The HCID identity model, hierarchical cell structure, `cell_key` derivation rules, local ENU coordinate frames, and entity occupancy model are all implementations of this commitment. The "H3 vs custom" framing in V0.1's open questions is retired.
**Impact:** Closes the long-running H3-vs-custom question. All future spatial work assumes Harmony Cell System.
**ADR:** ADR-002 (stub) — Gnomonic Cube Projection; ADR-003 — Cell Key Derivation Architecture
**Status:** Accepted
**Spec version:** V1.0.1
**Source:** Master_Spec_Variations/variations/applied/VAR-009-harmony-cell-system-commitment.md

---

### DEC-010 | 2026-04-20 | Pillar 1 Stage 2 — Spatial Substrate (Volumetric)
**Decision:** Adaptive Volumetric Cell Extension formally populated from
dispatch `p1-stage2-20260420`. Surface-default / volumetric-opt-in model.
Surface cell key format unchanged. Volumetric key adds `:v{alt_min}-{alt_max}`
suffix. Altitude validation range [-11,000m, aviation]. Band thickness
≥ 0.5m. Vertical adjacency precomputed at registration as
`{"up": key-or-null, "down": key-or-null}`.
**Impact:** Pillar 1 gains 3D addressing; schema bumps v0.1.3 → v0.2.0.
Pillar 2 can now ingest vertical data. Pillar 3 gains a 3D LOD tree.
Gap 7 (Dimensional Compatibility 3D → 4D) closed at the substrate layer.
**ADR:** ADR-015 — Adaptive Volumetric Cell Extension
**Status:** Accepted
**Spec version:** Pending V1.2.0

---

### DEC-011 | 2026-04-20 | Pillar 1 Stage 2 — Implementation
**Decision:** Stage 2 implementation ADR numbered **ADR-017** (not ADR-016
as named in the dispatch brief). ADR-016 is already allocated to the
Pillar 2 temporal trigger architecture per the 2026-04-21 reorganisation.
The dispatch brief predated the reorganisation; the canonical ADR_INDEX
is authoritative. Grid-uniqueness constraint on `cell_metadata` replaced
with a partial unique index applying only to surface rows, permitting
volumetric children to share the parent's grid position.
**Impact:** ADR numbering aligns with post-reorg index. Migration 003
modifies the Stage 1 UNIQUE(grid) constraint (drop + partial-index
recreate) — additive at the schema level but a behavioural change for any
consumer that relied on the Stage 1 constraint name `unique_grid_position`.
**ADR:** ADR-017 — Pillar 1 Stage 2 Implementation Decisions
**Status:** Accepted
**Spec version:** Pending V1.2.0

---

### DEC-012 | 2026-04-20 | Pillar 1 Stage 2 — Forward Compatibility
**Decision:** Confirmed that v0.2.0 schema and volumetric cell key format
do NOT foreclose the 4D temporal model. The `@` separator is reserved for
future temporal suffix and forbidden from appearing in any Stage 2 key.
The four temporal fields from ADR-007 (`valid_from`, `valid_to`,
`version_of`, `temporal_status`) remain reserved on `identity_registry`
untouched by Stage 2. `is_volumetric` discriminator is orthogonal to
temporal status — all four shapes (surface-stable, surface-historical,
volumetric-stable, volumetric-historical) are addressable when Pillar 4
activates.
**Impact:** Gap 7 closes at the substrate layer. Pillar 4 temporal
activation can proceed without breaking the volumetric key format or
the v0.2.0 schema.
**ADR:** ADR-015 §6, ADR-017 §4
**Status:** Accepted
**Spec version:** Pending V1.2.0

---

### DEC-013 | 2026-04-23 | Pillar 2 — Tier Enforcement
**Decision:** Tier tags (`source_tier`, `source_id`, `confidence`) are
system-assigned and write-once; corrections flow through supersession,
not mutation. Every record carries a `provenance_hash` = SHA-256 of the
canonicalised provenance tuple. A database CHECK constraint prevents
Tier 4 generated knowledge from ever occupying a structural fidelity
slot: `CHECK (source_tier != 4 OR (structural_fidelity_class IS NULL
AND structural_fidelity_score IS NULL AND structural_fidelity_source IS
NULL))`. Read-path default filter is `source_tier <= 3`. Nightly
integrity scan recomputes and verifies provenance hashes on a rolling
1% stratified sample.
**Impact:** Closes the enforcement gap left open by ADR-018. Tier
assignment becomes un-forgeable and Tier 4 contamination of safety-
critical fidelity slots becomes impossible via any code path. Every
Pillar 2 ingestion adapter must participate in the tier-authorisation
registry and emit the canonical provenance tuple.
**ADR:** ADR-019 — Tier Enforcement Architecture
**Status:** Proposed
**Spec version:** Pending V1.2.0

---

### DEC-014 | 2026-04-23 | Pillar 2 — CRS Normalisation
**Decision:** Canonical CRS is WGS84 (EPSG:4326); all geometries stored
in the Harmony Cell registry are WGS84. Every ingested geometry must
declare `source_crs` — no auto-detect, no default; missing declaration
is a refuse. Every record preserves its `source_crs` plus a
`crs_transform_epoch` timestamp (moment of transformation) and a
`transformation_method` enum. GDA2020 → WGS84 conversions use the
**NTv2 grid shift file** (PROJ 9+ with `GDA94_GDA2020_conformal.gsb`
bundled in the ingestion container and SHA-256-verified), **not** a
7-parameter Helmert transformation — residual error at cell-centroid
scale is sub-centimetre vs ~0.2m for Helmert.
**Impact:** Cell-key determinism holds across all ingestion paths.
Reprocessing is tractable — records carry enough metadata to be
re-transformed if the transformation pipeline evolves. NTv2 grid file
becomes a packaged dependency with CI-verified checksum.
**ADR:** ADR-020 — CRS Normalisation Strategy
**Status:** Proposed
**Spec version:** Pending V1.2.0

---

### DEC-015 | 2026-04-23 | Pillar 2 — Geometry Quarantine
**Decision:** Quarantine is a **separate physical partition**
(`cell_metadata_quarantine`, `entity_table_quarantine`), not a flag on
the main tables. Quarantined records are **invisible** to all Pillar 1
read paths and do not participate in adjacency, hierarchy, or alias
resolution — they live in an append-only review inbox. Every
quarantined record carries one of six closed reason codes
(`Q1_GEOMETRY_INVALID`, `Q2_GEOMETRY_DEGENERATE`, `Q3_CRS_OUT_OF_BOUNDS`,
`Q4_SCHEMA_VIOLATION`, `Q5_PROVENANCE_INCOMPLETE`,
`Q6_DUPLICATE_UNRESOLVED`). 90-day retention — unreviewed records
hard-deleted after 90 days with an audit-log entry retaining a content
hash. Pipeline continues on quarantine — batch does not abort; ingestion
report tallies main-vs-quarantine counts by reason.
**Impact:** Batch-scale ingestion is robust to real-world data
messiness without silent data loss. Substrate correctness guarantees
are never weakened by "was the flag checked" questions — the predicate
does not exist. Quarantine-review API is separate from the main
resolution API with distinct auth scope.
**ADR:** ADR-021 — Geometry Quarantine Lifecycle
**Status:** Proposed
**Spec version:** Pending V1.2.0

---

### DEC-016 | 2026-04-24 | Pillar 3 — Rendering Asset Format

**Decision:** Rendering pipeline adopts **glTF 2.0** (ISO/IEC 40588) as
canonical 3D asset format. All geometry must use **Draco compression
level 7** with 14-bit vertex quantization and 10-bit normal quantization.
Asset bundle schema includes nullable `geometry_source_url`, required
`geometry_inferred` boolean, and `fidelity_coverage` structure with three
valid states: `available`, `pending`, `splat_pending`. When
`geometry_inferred = true`, schema-level CHECK constraint atomically
enforces `fidelity_coverage.photorealistic.status = 'splat_pending'`.
Human-facing geometry delivery target: <100ms (provisional, contingent
on benchmarking).

**Impact:** Gap 1 (Asset Encoding) formally closed. Gap 2 (Rendering
Performance) partially closed with 100ms target accepted as design goal.
All Pillar 2 ingestion adapters must emit glTF+Draco. Pillar 3 rendering
clients must respect fidelity states when deciding to render. Schema
migration required: add `geometry_inferred` boolean, `fidelity_coverage`
JSON structure, and CHECK constraint to `asset_bundles` table.

**ADR:** ADR-022 — Rendering Asset Format and Data Contract

**Status:** Proposed

**Spec version:** Pending V1.2.0

---

### DEC-017 | 2026-04-26 | Pillar 1 — API Extension

**Decision:** Added `PATCH /cells/{cell_key}/fidelity` endpoint to the
Pillar 1 API. Purpose-built, narrow endpoint with full-replacement semantics
on `cell_metadata.fidelity_coverage` JSONB column. Dr. Voss Option B —
not a general metadata PATCH. Validation enforced at the API layer:
(a) both `structural` and `photorealistic` objects required; (b) `status`
restricted to defined enum values; (c) `status=available` requires non-null
`source`; (d) Tier 4 exclusion (`source_tier=4` cannot have `status=available`)
enforced in API validation layer since no new DB migration is required or
permitted without Mikey's gate. The `fidelity_coverage` JSONB column already
existed on `cell_metadata` (reserved in Stage 1 schema). No migration needed.

**Impact:** Pillar 2 ingestion pipeline can now write fidelity coverage data
to the correct long-term location (cell records) rather than the interim
entity-metadata workaround. Dr. Adeyemi's pipeline should migrate from the
entity-metadata interim to `PATCH /cells/{cell_key}/fidelity`.

**ADR:** None — implementation decision covered by existing ADR-022 (Tier 4
exclusion), ADR-013 (API Layer Architecture). No new ADR required.

**Status:** Accepted

**Spec version:** Pending V1.2.0

---

### DEC-018 | 2026-04-27 | Team Structure / Pillar 3
**Decision:** Activate Chief Rendering Architect role; assign
Dr. Lin Park persona as binding authority on Pillar 3 (Rendering
Interface) and the Live Substrate Service.
**Impact:** Adds a fourth named architectural authority to the
project (peer to Voss, Boateng, Webb). Authority Matrix updated.
Live Substrate Service now has a named owner. Cesium partnership
track (WS-A) gains a binding rendering authority for architectural
compatibility review.
**ADR:** N/A — team structure decision, not architecture decision
**Status:** Accepted
**Spec version:** Pending V1.2.0

---

### DEC-019 | 2026-04-28 | Pillar 1 — API Extension

**Decision:** Added `PATCH /cells/{cell_key}/status` endpoint to the Pillar 1
API. Purpose-built, narrow endpoint with full-replacement semantics on
`cell_metadata.cell_status`. Dr. Voss Option B — not a general metadata PATCH.
Validation enforced at the API layer: `cell_status` restricted to four values
defined by the ADR-016 §2.3 state machine (`stable`, `change_expected`,
`change_in_progress`, `change_confirmed`); extra fields forbidden (`extra="forbid"`);
invalid values return 422. Idempotent — same value applied twice produces the
same result. The `cell_status` column is introduced by the M7 migration
(`m7_temporal_field_activation.py`, schema v0.2.0→v0.3.0), which is produced but
requires Mikey's approval gate before execution in production.

**Impact:** Pillar 2 temporal trigger transition service can now update
`cell_status` on individual cells via the Pillar 1 API contract, driving the
ADR-016 §2.3 state machine. The endpoint is live once M7 migration is executed.
No schema change is introduced by this endpoint itself — it writes to a column
added by the already-produced M7 migration.

**ADR:** ADR-016 §2.3 (state machine values), ADR-013 (API layer architecture).
No new ADR required — covered by existing decisions.

**Status:** Accepted

**Spec version:** Pending V1.2.0

---

## Unprocessed Content

A set of variation files existed under `Master_Spec_Variations/variations/pending/`
during the 2026-04-21 reorganisation. They carry the same VAR-001..VAR-009
titles as the applied entries above and appear to be earlier drafts. They
have been archived without DEC conversion to
`docs/specs/variations-archive/pending/` and remain unprocessed. If any
decision in the pending copies differs from its applied counterpart,
create a new DEC entry at the bottom of this log.
