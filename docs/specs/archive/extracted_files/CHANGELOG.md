# Pillar 1 — Spatial Substrate — Change Log

> All notable changes to the Pillar 1 deliverables are recorded here.
> Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions.
> Versioning follows the schema_version field used in the Identity Registry.

---

## [0.1.2] — 2026-04-10

**Theme:** First amendment under Harmony Master Spec V1.0 — closes Gaps 1–5 at the schema layer, formalises the three-layer agent model, and introduces the PM infrastructure.

### Added

- **ADR-009** — Temporal versioning model. Establishes that every cell and entity record can carry temporal validity, version chains, and successor relationships. (Closes Gap 3.)
- **ADR-010** — Named-entity resolution boundary. Establishes that the Identity Registry exposes resolution *primitives* (exact match, fuzzy match, multi-name lookup) but does not own natural-language resolution itself. (Closes Gap 5.)
- **ADR-011** — Three-layer agent model. Formalises the distinction between Builder Agents (build-time), Runtime Agent Classes I/II/III (deployed infrastructure), and Digital Team Members (customer-facing).
- **`pillar-1-master-spec-variations.md`** — Running record of everything Pillar 1 has resolved that should fold into a future master spec revision. Reading B format (comprehensive, not just deltas).
- **`PM/`** folder — Project Management infrastructure: folder spec, session report template, Project Manager Agent brief, first session report.

### Changed

- **`identity-schema.md`** — Version bumped to 0.1.2. Added §6.2 (temporal fields), §7 update (navigation profile note), §8 update (multi-name support), §12 update (Pillar 3 forward-compatibility note), §14 (federation clarification).
- **`cell_identity_schema.json`** — Schema version constant bumped to `0.1.2`. New reserved fields added (see Reserved below).
- **`entity_identity_schema.json`** — Schema version constant bumped to `0.1.2`. New reserved fields added (see Reserved below).
- **`id_generation_rules.md`** — Version bumped to 0.1.2. §11 (Open Items) updated with cross-references to new ADRs.
- **`ADR-001-layered-identity.md`** — Federation note added: "single source of truth" refers to the *logical* registry, not a centralised commitment. The canonical ID format remains compatible with a federated multi-issuer model. (Preserves Gap 4.)
- **`README.md`** — Acceptance criteria checklist updated to reflect v0.1.2 deliverables.

### Reserved (added but not active in v0.1.2)

These fields exist in the schema as forward-compatibility hooks. Writes to reserved fields are rejected by the registry until the owning pillar formally activates them.

**On cell records:**
- `valid_from` (timestamp, nullable) — Reserved for temporal versioning. Owned by Pillar 4.
- `valid_to` (timestamp, nullable) — Reserved for temporal versioning. Owned by Pillar 4.
- `version_of` (canonical_id, nullable) — Reserved for version chains. Owned by Pillar 4.
- `temporal_status` (enum, nullable) — Reserved for temporal lifecycle. Owned by Pillar 4.
- `known_names` (array of strings) — Reserved for named-entity resolution. Owned by Pillar 5 via Pillar 1's primitives.
- `fidelity_coverage` (object, nullable) — Reserved for dual fidelity. Owned by Pillar 2.
- `lod_availability` (object, nullable) — Reserved for dual fidelity. Owned by Pillar 2.
- `asset_bundle_count` (integer, default 0) — Reserved for dual fidelity. Owned by Pillar 2.
- `references.asset_bundles` (array, default empty) — Reserved for dual fidelity. Owned by Pillar 2.

**On entity records:**
- `valid_from`, `valid_to`, `version_of`, `temporal_status` — same semantics as cell records.
- `known_names` — same semantics as cell records.

### Deprecated

- None.

### Removed

- None.

### Decision Notes

- Pillar 3 framework selection (Gap 1) is **not** addressed in this pack. It is being handled in a separate dedicated chat where full rendering context is maintained. Pillar 1 has confirmed it has no hard dependency on this decision.
- Scrum Master Agent — described in earlier discussion as "to be developed." Decision made to defer indefinitely. Under sequential pillar execution, the Project Manager Agent absorbs the responsibilities that would have justified a separate Scrum Master role.

---

## [0.1.1] — 2026-04-07

**Theme:** Initial Milestone 1 (Identity Schema Lock) deliverables under the Stage 1 Implementation Brief.

### Added

- **`identity-schema.md`** — Locked layered identity model: canonical ID, cell key, human alias, friendly name, semantic labels.
- **`id_generation_rules.md`** — Deterministic rules for generating canonical IDs and cell keys. Crockford Base32 alphabet. BLAKE3 cell key derivation.
- **`alias_namespace_rules.md`** — Hierarchical dotted alias namespaces. (alias, namespace) tuple as the unit of identity at the alias layer.
- **`cell_identity_schema.json`** — JSON Schema for cell records.
- **`entity_identity_schema.json`** — JSON Schema for entity records.
- **`ADR-001`** — Layered identity model.
- **`ADR-004`** — `cell_id` vs `cell_key`. Both fields mandatory on every cell.
- **`ADR-008`** — Alias namespace model.
- **`README.md`** — Pack index and acceptance criteria checklist.

### Source

- Stage 1 Implementation Brief v0.1.1 (`pillar-1-spatial-substrate-stage1-brief.md`).
- Harmony Master Specification v0.1 (`harmony_master_spec_v0.1.md`).

---

*End of CHANGELOG.md*
