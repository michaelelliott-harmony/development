# Pillar 1 — Spatial Substrate — Change Log

> All notable changes to the Pillar 1 deliverables are recorded here.
> Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions.
> Versioning follows the schema_version field used in the Identity Registry.

---

## [0.2.0] — 2026-04-20

**Theme:** Pillar 1 Stage 2 — Volumetric Cell Extension. 3D addressing
from seabed to sky. Surface cells unchanged; volumetric cells are an
additive, opt-in subdivision.

### Added

- **`harmony/packages/cell-key/src/volumetric.py`** — Pure-logic module:
  deterministic volumetric key derivation, parsing, altitude validation,
  surface/volumetric discriminators. Reserves `@` separator for future
  temporal suffix (Pillar 4).
- **`harmony/db/migrations/003_volumetric_cell_extension.sql`** — Migration
  v0.1.3 → v0.2.0. Adds altitude fields, vertical adjacency JSONB,
  `is_volumetric` discriminator, CHECK constraints, partial unique index
  replacing Stage 1 `unique_grid_position`. Down block included.
  **Produced only — execution requires Mikey's approval.**
- **`harmony/tests/test_p1_stage2_acceptance.py`** — 40-test Stage 2
  acceptance suite (35 pure-logic + 5 HTTP integration). All 35
  pure-logic tests pass.
- **POST /cells/volumetric** endpoint — register a volumetric child of an
  existing surface cell.
- **ADR-015** — Populated from stub via Stage 2 dispatch (Accepted).
- **ADR-017** — Pillar 1 Stage 2 Implementation Decisions (Accepted).

### Changed

- **`harmony/packages/registry/src/registry.py`** — Added
  `volumetric_cell_key` regex, `register_volumetric_cell()`,
  `resolve_vertical_adjacency()`. Schema version bumped to 0.2.0.
  Stage 1 code paths untouched.
- **`harmony/services/api/models.py`** — Added `VolumetricCellCreate`,
  `VerticalAdjacency`, `CellAdjacencyResponse`. `CellResponse` extended
  with optional volumetric fields (surface responses unchanged).
- **`harmony/services/api/routes/cells.py`** — Adjacency endpoint returns
  Stage 2 `{lateral, vertical}` shape for volumetric cells; Stage 1 ring
  shape for surface cells (unchanged). New POST /cells/volumetric route.

### Test State

- Stage 1 cell-key suite: 60/60 pass (unchanged)
- Stage 1 alias suite: 62/62 pass (unchanged)
- Stage 2 acceptance suite: 35/35 pure-logic tests pass
  (5 HTTP tests require server + migration applied)
- **Cumulative: 157/157 pass** in pure-logic mode
  (was 122 Stage 1 + 35 new Stage 2)

### Forward Compatibility

v0.2.0 schema and volumetric key format confirmed **non-foreclosing** for
the 4D temporal model. Reserved `@` separator. Temporal fields from
ADR-007 remain reserved. Gap 7 closed at the substrate layer.

---

## [0.1.3-s4] — 2026-04-18

**Theme:** Alias System build (Session 4). Counter-based alias generation, namespace handling, alias lifecycle with 180-day grace period, registry integration, sample entity records, and ADR-012.

### Added

- **`harmony/packages/alias/src/alias_service.py`** — Complete alias service: format validation, namespace validation, counter-based auto-generation, alias binding (7-step registration order), retirement, resolution, history queries. 785 lines.
- **`harmony/db/migrations/002_alias_namespace_registry.sql`** — Creates `alias_namespace_registry` table for per-namespace atomic counters. Replaces full UNIQUE constraint on `alias_table` with partial unique index (`WHERE status = 'active'`). Adds case-insensitive lookup index.
- **`harmony/packages/alias/tests/test_alias_service.py`** — 62-test suite across 11 test classes. All pass.
- **ADR-012** — Alias Generation Architecture. Documents counter-based alias generation, registration order, and alternatives considered.
- **3 sample entity records** — Building, parcel, and road segment in `au.nsw.central_coast.entities`, added to `sample-central-coast-records.json`.
- **Session 4 summary** — `harmony/docs/sessions/SESSION_04_SUMMARY.md`
- **PM session report** — `PM/sessions/2026-04-18-pillar-1-session-4-alias-system.md`

### Changed

- **`harmony/db/identity_registry_schema.sql`** — Added `alias_namespace_registry` table (Table 5). Replaced full UNIQUE constraint on `alias_table` with partial unique index. Renumbered `entity_table` from Table 4 to Table 6.
- **`harmony/packages/registry/src/registry.py`** — Added `auto_alias_namespace` parameter to `register_cell()` and `register_entity()`. Updated alias handling to support both manual and auto-generated aliases.
- **`harmony/data/sample-central-coast-records.json`** — Extended from 5 cell records to 8 records (5 cells + 3 entities with aliases).
- **`id_generation_rules.md`** — Patched to v0.1.3: cell key regex updated to 16-char hash, resolution table updated to 12 levels (r00–r11), Gate 3 closure referenced, ADR cross-references updated to canonical numbering.
- **ADR rename map applied** — Architecture-track and build-track ADRs merged into canonical sequence per `ADR_INDEX.md`. All ADRs now in `harmony/docs/adr/` under canonical numbers.

### Corrections

- **Namespace format** — Session 3 sample data used `cc.au.nsw.cc` namespaces. Corrected to country-first `au.nsw.central_coast.cells` per locked `alias_namespace_rules.md`.
- **Three-segment namespace validity** — Two tests initially asserted 3-segment namespaces were invalid. The locked regex `{2,5}` permits them. Tests corrected.

### Test State

- Session 2 cell-key suite: 60/60 pass
- Session 4 alias suite: 62/62 pass
- **Cumulative: 122/122 pass**

---

## [0.1.3] — 2026-04-10

**Theme:** Integration of Session 2 and Session 3 build-track outputs with the architecture-track v0.1.2 pack. Schema extended with spatial geometry and adjacency. ADR sequences merged into one canonical numbering. Gate 3 formally closed.

### Added

- **ADR-002 (canonical)** — Cell Geometry, Gnomonic Cube Projection. *(Existing in `cell_geometry_spec.md`; formal ADR extraction is a low-priority follow-up.)*
- **ADR-003 (canonical)** — Cell Key Derivation Architecture. *(Session 2 build-track, renamed from build-track ADR-004.)*
- **ADR-005 (canonical)** — Cell Adjacency Model. *(Session 3 build-track.)*
- **ADR-010** — Spatial Geometry Schema Extension (v0.1.3). Formally documents the new geometric, cube-face addressing, and adjacency fields added to the cell schema.
- **ADR-011** — Gate 3 Closure: Identity Generation Order. Closes V1.0 Gate 3 and locks the cell, entity, and alias registration sequences.
- **`ADR_INDEX.md`** — Canonical ADR sequence. Single source of truth for ADR numbering going forward.

### Changed

- **`identity-schema.md`** — Version bumped 0.1.2 → 0.1.3. New §6.3 documents Session 3 active geometric and adjacency fields. Cross-references updated to canonical ADR numbers.
- **`cell_identity_schema.json`** — Version 0.1.2 → 0.1.3. Active fields added: `cube_face`, `face_grid_u`, `face_grid_v`, `edge_length_m`, `area_m2`, `distortion_factor`, `centroid_ecef`, `centroid_geodetic`, `adjacent_cell_keys`. Cell key regex updated from 5-char to 16-char hash. *(Authoritative v0.1.3 schema is the one produced in Session 3.)*
- **`id_generation_rules.md`** — Version 0.1.2 → 0.1.3. §4.1 regex updated to 16-char hash. §4.4 resolution table updated from 16 levels (r00–r15) to 12 levels (r00–r11), per Session 2 D2. §11 updated to reference Gate 3 closure.
- **`pillar-1-master-spec-variations.md`** — Sections 1, 2, 3, and 5 updated with Session 2 and Session 3 contributions and v0.1.3 schema additions.
- **ADR renumbering** — Architecture-track ADRs 008, 009, 010, 011 renamed to ADR-006, 007, 008, 009 respectively. Build-track ADR-004 renamed to ADR-003. See `ADR_INDEX.md` for the full rename map.

### Active (promoted from Reserved)

These fields were reserved in v0.1.2 and are now **active** in v0.1.3, populated by Session 3's registry service:

- *(None — the v0.1.2 reserved fields remain reserved. The v0.1.3 additions are new active fields, not promotions.)*

### Reserved (unchanged from v0.1.2)

All v0.1.2 reserved fields remain reserved and awaiting activation:

- `valid_from`, `valid_to`, `version_of`, `temporal_status` (Pillar 4)
- `known_names` (Pillar 5 reads; Pillar 1 indexes)
- `fidelity_coverage`, `lod_availability`, `asset_bundle_count`, `references.asset_bundles` (Pillar 2)

### Decisions Closed

- **V1.0 Gate 3** — Identity encoding / token generation method. Closed by ADR-011. Remaining open gates: 1, 2, 4, 6.
- **Session 2 D1** (gnomonic distortion acceptable), **D2** (4×4 subdivision, 12 levels), **D3** (16-char hash), **D4** (geodetic correction), **D5** (cube face tie-breaking) — all confirmed and carried into v0.1.3.
- **Session 3 D1** (adjacency symmetry is reachability, not direction reversal), **D2** (edge adjacency stored, vertex computed), **D3** (schema v0.1.3 bump), **D4** (cell_key regex production form), **D5** (sample dataset scope) — all confirmed.

### Decision Notes

- **Entity idempotency remains caller-responsibility (Pillar 2).** Confirmed by Mikey during Gate 3 closure. Entity canonical IDs are purely random; the same building registered twice produces two distinct entity IDs. Pillar 2 handles deduplication via source-system keys.
- **Pillar 3 downstream dependency.** 16-child-per-cell LOD hierarchy at 12 levels, and `get_adjacency_ring()` as a required substrate primitive, must be carried into the Pillar 3 brief when that chat produces its own deliverables.

---

## [0.1.2] — 2026-04-10

*(Full entry preserved from the prior CHANGELOG. See the v0.1.2 pack for details.)*

**Theme:** First amendment under Harmony Master Spec V1.0 — closes Gaps 1–5 at the schema layer, formalises the three-layer agent model, and introduces the PM infrastructure.

Key additions: ADR-007 (Temporal Versioning), ADR-008 (Named-Entity Resolution Boundary), ADR-009 (Three-Layer Agent Model), `pillar-1-master-spec-variations.md`, `PM/` folder.

---

## [0.1.1] — 2026-04-07

*(Full entry preserved from the prior CHANGELOG.)*

**Theme:** Initial Milestone 1 (Identity Schema Lock) deliverables under the Stage 1 Implementation Brief.

Key additions: layered identity model, `cell_id` vs `cell_key` dual-identifier principle, alias namespace model, ADRs 001, 003, 004, 006 (renumbered).

---

*End of CHANGELOG.md*
