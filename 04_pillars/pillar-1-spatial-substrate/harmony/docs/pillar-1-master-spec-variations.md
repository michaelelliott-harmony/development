# Pillar 1 — Master Spec Variations (v0.1.3)

> **Purpose:** Living record of everything Pillar 1 has resolved, added, or clarified for inclusion in a future master spec revision (Reading B — comprehensive contribution).
>
> **Pillar:** 1 — Spatial Substrate
> **Last Updated:** 2026-04-10 (v0.1.3 update)
> **Status:** Living document
> **Supersedes:** v0.1.2 version of this file

---

## Change Summary for This Version

v0.1.3 adds five substantive new contributions from Sessions 2 and 3, closes V1.0 Gate 3, and resolves ADR numbering drift. No earlier content is removed; this document grows additively.

---

## Section 1 — Gap Register Items Resolved

### Gap 3 — Temporal Versioning (closed at schema layer, v0.1.2)

See v0.1.2 entry. Unchanged in v0.1.3. ADR-007 (renumbered from ADR-009).

### Gap 5 — Named-Entity Resolution (closed at substrate layer, v0.1.2)

See v0.1.2 entry. Unchanged in v0.1.3. ADR-008 (renumbered from ADR-010).

### Gap 4 — Federation (preserved, v0.1.2)

See v0.1.2 entry. Unchanged in v0.1.3.

### Original Agent Analysis Gate 3 — Identity Generation Method *(new in v0.1.3)*

**Status:** Closed by ADR-011.

**Resolution:** The cell, entity, and alias registration sequences are now formally locked. Cell registration is idempotent against geometry (compute `cell_key` first, idempotent return if already registered). Entity registration is purely random (Pillar 2 handles deduplication). Alias registration surfaces collisions to the caller rather than silently resolving them.

**What the master spec should say:** "Cell registration in Harmony is idempotent against geometry: the same geometric input always produces the same `cell_id`. Entity registration is not idempotent at the identity layer; deduplication is a Pillar 2 ingestion responsibility."

**Reference:** ADR-011 — Gate 3 Closure.

---

## Section 2 — Schema Additions and Reserved Fields

### Cell Records (v0.1.3 — now the current version)

| Field | Status | Owner | Purpose |
|---|---|---|---|
| `canonical_id`, `cell_key` | Active | Pillar 1 | Identity core (v0.1.1) |
| `human_alias`, `alias_namespace`, `friendly_name` | Active | Pillar 1 | Identity layers (v0.1.1) |
| `semantic_labels` | Active | Pillar 4 | AI-generated tags |
| `cube_face` | **Active (new v0.1.3)** | Pillar 1 | Which cube face (0–5) |
| `face_grid_u`, `face_grid_v` | **Active (new v0.1.3)** | Pillar 1 | UV grid coordinates on the face |
| `edge_length_m` | **Active (new v0.1.3)** | Pillar 1 | Actual computed edge length |
| `area_m2` | **Active (new v0.1.3)** | Pillar 1 | Actual computed area |
| `distortion_factor` | **Active (new v0.1.3)** | Pillar 1 | Gnomonic UV-space distortion |
| `centroid_ecef` | **Active (new v0.1.3)** | Pillar 1 | Cell centroid in ECEF |
| `centroid_geodetic` | **Active (new v0.1.3)** | Pillar 1 | Cell centroid in WGS84 lat/lon/alt |
| `adjacent_cell_keys` | **Active (new v0.1.3)** | Pillar 1 | Precomputed edge-adjacency |
| `known_names` | Reserved (indexed) | Pillar 5 reads | NER primitives (v0.1.2) |
| `valid_from`, `valid_to`, `version_of`, `temporal_status` | Reserved | Pillar 4 | Temporal (v0.1.2) |
| `fidelity_coverage`, `lod_availability`, `asset_bundle_count`, `references.asset_bundles` | Reserved | Pillar 2 | Dual fidelity (v0.1.2) |

### Entity Records (unchanged in v0.1.3)

Same as v0.1.2. Spatial geometry fields do not apply to entities — entities reference cells via `primary_cell_id` and inherit geometric context from the bound cell.

**What the master spec should say:** The master spec's identity table should describe cells as carrying both identity fields (canonical_id, alias, etc.) and substrate-level spatial fields (cube face, UV grid, geometry, adjacency). The full field list lives in `cell_identity_schema.json` v0.1.3.

---

## Section 3 — New Concepts Introduced

### 3.1 The Layered Identity Model *(unchanged, v0.1.1)*
### 3.2 cell_id vs cell_key — Two-Identifier Substrate *(unchanged, v0.1.1)*
### 3.3 The Three-Layer Agent Model *(unchanged, v0.1.2)*
### 3.4 Bitemporal Versioning at the Substrate Layer *(unchanged, v0.1.2)*
### 3.5 The Resolution Primitives Boundary *(unchanged, v0.1.2)*
### 3.6 Federation-Compatible Identity Format *(unchanged, v0.1.2)*

### 3.7 Gnomonic Cube Projection as the Spatial Foundation *(new in v0.1.3)*

The Harmony Cell System is implemented as a gnomonic projection of the WGS84 ellipsoid onto a cube, with each face recursively subdivided into a 4×4 grid at each resolution level. The hierarchy has **12 levels** (r00–r11), from planetary to sub-metre. This is the decision that made every other Pillar 1 substrate decision tractable — hexagonal grids cannot subdivide hierarchically, lat-lon grids degenerate at poles, and triangular grids produce irregular shapes.

**Accepted cost:** up to ~2.3× size variation between face corners and face centres. The system does not normalise cell sizes; it stores actual computed geometry per cell.

**Reference:** ADR-002 (to be extracted from `cell_geometry_spec.md`), Session 2 decisions D1, D2, D4, D5.

**What the master spec should say:** Add to Pillar I as a foundational substrate decision. "The Harmony Cell System uses a gnomonic cube projection with 4×4 recursive subdivision across 12 resolution levels. Gnomonic distortion is accepted as a tradeoff for hierarchical, deterministic, singularity-free global coverage."

### 3.8 The Cell Adjacency Model *(new in v0.1.3)*

The substrate supports sub-millisecond lateral adjacency lookup via precomputed `adjacent_cell_keys`. Adjacency is defined in two classes (edge and vertex). At cube face boundaries, coordinate axes remap — adjacency is symmetric in the *reachability* sense (A is in B's neighbour set), not in direction. A complete boundary transition table covers all 24 directed face-edge transitions.

**Standard API primitive:** `get_adjacency_ring(cell_key, depth)` returns all cells within N lateral steps. Ring 1 = 8 cells, Ring 2 = 24 cells, Ring 3 = 48 cells (for cells not on a face boundary).

**Reference:** ADR-005 (build-track, Session 3).

**What the master spec should say:** Add to Pillar I as a substrate obligation. "The substrate precomputes lateral adjacency at registration time. The rendering engine and autonomous navigation agents both consume adjacency rings as a pre-fetch primitive."

### 3.9 Predictive LOD as a Substrate Obligation *(new in v0.1.3)*

Predictive LOD — the capability to pre-fetch cells the rendering engine will need next based on camera trajectory and movement — is a substrate-level concern, not a rendering-layer feature. The substrate must expose fast adjacency so that predictive pre-fetch is feasible at rendering frame rate.

**Reference:** Session 3 brief, new architectural requirement.

**What the master spec should say:** Add to Pillar I obligations under V1.0 North Star I. "The substrate must support predictive LOD pre-fetch at rendering frame rate. This elevates adjacency from a convenience to a substrate-level contract."

### 3.10 Idempotent Cell Registration *(new in v0.1.3)*

Registering the same cell geometry twice always returns the same `cell_id`. This is enforced at the database level via the `UNIQUE` constraint on `cell_key`. Entity registration is deliberately *not* idempotent — see ADR-011.

**Reference:** ADR-011 — Gate 3 Closure.

**What the master spec should say:** Add to the Pillar I section. "Cells are idempotent at the identity layer. Entities are not. This asymmetry is intentional."

---

## Section 4 — Open Items Pillar 1 Surfaced But Doesn't Own

### 4.1 Pillar 3 Framework Decision (V1.0 Gap 1) *(unchanged, separate chat)*
### 4.2 Machine Query Latency Target (V1.0 Gap 2) *(unchanged)*
### 4.3 Active Temporal Implementation *(unchanged — Pillar 4 owns)*
### 4.4 Active Dual Fidelity Implementation *(unchanged — Pillar 2 owns)*
### 4.5 Conversational Spatial Agent Resolution Flow *(unchanged — Pillar 5 owns)*
### 4.6 Local Coordinate Frames (ECEF vs ENU) *(still open, later Pillar 1 milestone)*

### 4.7 Pillar 3 Downstream Dependencies *(new in v0.1.3)*

When the Pillar 3 chat begins formal brief-building, the following substrate commitments must be carried into the Pillar 3 brief:

- 12-level LOD hierarchy with 16-child (4×4) fan-out
- `get_adjacency_ring(cell_key, depth)` as a required substrate API
- Cube face addressing primitives (`cube_face`, `face_grid_u`, `face_grid_v`)
- Precomputed adjacency, never runtime-computed, at rendering frame rate

### 4.8 Pillar 2 Downstream Dependencies *(new in v0.1.3)*

- Entity deduplication is Pillar 2's responsibility
- The `compute_cell_geometry` and `compute_adjacent_cell_keys` functions in the registry enable distributed ingestion
- Dual fidelity fields are reserved at the substrate layer; Pillar 2 activates them

---

## Section 5 — Recommended Changes to the Next Master Spec Revision

### Pillar I (Spatial Substrate)

- Add the gnomonic cube projection as a foundational substrate decision (§3.7)
- Add the 12-level LOD hierarchy with 16-child fan-out
- Add the cell adjacency model as a substrate obligation (§3.8)
- Add predictive LOD as a substrate obligation under North Star I (§3.9)
- Add idempotent cell registration as a substrate guarantee (§3.10)
- Add the v0.1.3 active fields to the cell record summary
- Reference ADRs 002, 003, 005, 010, 011 as substrate-layer decisions

### Pillar III (Rendering Interface)

- Reference the substrate dependencies listed in §4.7
- Note that predictive LOD is enabled by substrate adjacency, not built independently

### Pillar II (Data Ingestion Pipeline)

- Note Pillar 2's role in entity deduplication (§4.8)
- Reference the distributed ingestion primitives

### Gap Register section

- Mark original Agent Analysis Gate 3 as **closed** (new in v0.1.3)
- Other Gap statuses unchanged from v0.1.2

### ADR Appendix

- Use the canonical ADR sequence from `ADR_INDEX.md`

---

## Appendix — Cross-Reference Index (Updated for v0.1.3)

| Concept | Source |
|---|---|
| Layered identity | ADR-001, identity-schema.md §3 |
| Cell geometry (gnomonic cube) | ADR-002, cell_geometry_spec.md |
| Cell key derivation | ADR-003, cell_key_derivation_spec.md |
| cell_id vs cell_key | ADR-004 |
| Cell adjacency | ADR-005, cell_adjacency_spec.md |
| Alias namespaces | ADR-006, alias_namespace_rules.md |
| Temporal versioning | ADR-007 |
| Named-entity resolution | ADR-008 |
| Three-layer agent model | ADR-009 |
| Spatial geometry schema extension | ADR-010, cell_identity_schema.json v0.1.3 |
| Gate 3 closure / generation order | ADR-011 |
| Federation compatibility | ADR-001 federation note |

---

*Pillar 1 — Master Spec Variations v0.1.3 — Living Document*
