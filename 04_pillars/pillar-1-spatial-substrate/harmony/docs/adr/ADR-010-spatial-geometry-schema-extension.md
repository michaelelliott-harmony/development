# ADR-010 — Spatial Geometry Schema Extension (v0.1.3)

> **Status:** Accepted
> **Date:** 2026-04-10
> **Pillar:** 1 — Spatial Substrate
> **Milestone:** 3 — Cell Adjacency & Identity Registry
> **Deciders:** Builder Agent 4 (Spatial Substrate Engineer), reviewed by Architecture Lead
> **Schema Version Affected:** 0.1.2 → 0.1.3
> **Related:** ADR-002 (Cell Geometry), ADR-003 (Cell Key Derivation), ADR-005 (Cell Adjacency Model)

---

## Context

The v0.1.2 schema locked the identity layer. It did not carry explicit spatial geometry for cells — geometry was treated as something that lived outside the identity record. Session 2 and Session 3 of the build made it clear this was insufficient.

Three forces drove the need to extend the cell schema in v0.1.3:

**1. Gnomonic cube projection distortion (Session 2 D1).** The cube projection causes cell size to vary by up to ~2.3× between face corners and face centres. If resolution level alone is used to infer cell size, downstream systems (rendering, ingestion, analytics) will consistently miscalculate area, density, and spatial statistics. Every cell must store its actual computed geometry.

**2. Cube face addressing (Session 3 adjacency model).** Each cell lives on a specific face of the gnomonic cube, at specific UV grid coordinates. These fields are not metadata — they are the primary key under which adjacency is computed. Without them, the adjacency model cannot be applied from a database query alone.

**3. Precomputed adjacency for predictive LOD (Session 3 new requirement).** The rendering engine requires sub-millisecond lookup of a cell's neighbours to enable predictive pre-fetch. Computing adjacency at query time — even with a fast algorithm — is too slow at rendering frame rate. Adjacency must be computed once at cell registration and stored.

The v0.1.2 schema, with its reserved fidelity fields but no active geometry fields, could not support any of the three.

---

## Decision

Extend the cell schema to v0.1.3 with the following fields. All are **active**, not reserved. Writes are enforced at registration time.

### Geometric Fields

| Field | Type | Purpose |
|---|---|---|
| `edge_length_m` | number | Actual computed edge length in metres on the ellipsoid surface |
| `area_m2` | number | Actual computed area in square metres |
| `distortion_factor` | number | Ratio of this cell's UV-space distortion to the face-centre ideal |
| `centroid_ecef` | array[3] | Cell centroid in ECEF coordinates |
| `centroid_geodetic` | array[3] | Cell centroid in WGS84 geodetic (lat, lon, alt) |

### Cube Face Addressing Fields

| Field | Type | Purpose |
|---|---|---|
| `cube_face` | integer (0–5) | Which of the six cube faces this cell sits on |
| `face_grid_u` | integer | U coordinate on the cube face grid |
| `face_grid_v` | integer | V coordinate on the cube face grid |

### Adjacency Field

| Field | Type | Purpose |
|---|---|---|
| `adjacent_cell_keys` | array of strings | Precomputed cell_keys of all edge-adjacent neighbours. For cells not on a face boundary, this is 4 entries (edge adjacency; vertex adjacency is computed at runtime per Session 3 D2). For face-boundary cells, some entries reference cells on adjacent faces. |

### Schema Versioning

Version bumps from `0.1.2` to `0.1.3`. This is a minor version bump because the change is additive at the field level — no existing field is renamed, retyped, or removed. However, the new fields are **required** at registration, which makes v0.1.2 records technically incompatible. Since no v0.1.2 records were ever committed to a production registry, the migration cost is zero.

---

## Consequences

### Positive

- **Rendering can pre-fetch at frame rate.** `get_adjacency_ring()` returns in O(ring depth) time from precomputed data.
- **Ingestion can compute cell metadata independently.** The functions `compute_cell_geometry` and `compute_adjacent_cell_keys` operate without database access, enabling distributed ingestion pipelines.
- **Spatial analytics are correct.** Area and edge length are stored, not inferred. Downstream statistics honour actual cell size.
- **Adjacency is auditable.** Stored neighbours can be tested for symmetry across the entire registry, which Session 3 did at Level 0 (24/24) and Level 8 boundaries (16/16).
- **Cube face boundaries are resolved.** No blind spots in the predictive LOD model. The seamless world is unseamed at face transitions.

### Negative

- **Larger cell records.** Adding ~10 fields per cell increases storage. At 1 billion cells, the overhead is still manageable (order of ~200 GB of metadata), but it is real.
- **Registration is heavier.** Every cell registration now computes geometry and adjacency, which takes milliseconds rather than microseconds. Acceptable because registration is rare relative to read queries.
- **Schema migration if adjacency model evolves.** If the cube geometry or adjacency algorithm ever changes, every cell's `adjacent_cell_keys` must be recomputed. Acceptable because the cube projection is a durable architectural commitment (ADR-002).
- **Edge adjacency only.** Vertex adjacency (the diagonal 4 neighbours) is computed at runtime per Session 3 D2. If ring-2 pre-fetch becomes a hot path, this may need revisiting.

### Neutral

- The reserved fidelity fields from v0.1.2 (`fidelity_coverage`, `lod_availability`, `asset_bundle_count`, `references.asset_bundles`) remain reserved. Pillar 2 still owns their activation.
- Temporal fields from ADR-007 remain reserved.
- `known_names` from ADR-008 remains reserved.

---

## Alternatives Considered

### A. Keep Geometry Out of the Identity Record

Let cells carry only identity fields; put geometry in a separate `cell_geometry` table joined at query time.

**Rejected because:** every rendering frame needs geometry. A join at frame rate is unacceptable. The registry is optimised for read patterns, and that means denormalising the fields the reads need.

### B. Compute Adjacency at Query Time

Store `cube_face`, `face_grid_u`, `face_grid_v` but not `adjacent_cell_keys`. Compute neighbours on demand from the boundary transition table.

**Rejected because:** while the algorithm is fast (O(1) per neighbour), the cumulative cost at ring-3 pre-fetch (48 cells) is tens of microseconds. The predictive LOD system calls this dozens of times per second. Storing neighbours pre-computed turns it into a single indexed read.

### C. Store All 8 Neighbours (Edge + Vertex)

Extend `adjacent_cell_keys` to 8 entries, denormalising vertex adjacency.

**Rejected — for now.** Session 3 D2 argues that vertex adjacency is cheaply computable from edge adjacency. Storing 8 would double the adjacency storage cost with no measured benefit. Revisit if ring-2 becomes a documented bottleneck.

### D. Defer to Pillar 3

Let the rendering engine maintain its own adjacency cache.

**Rejected because:** Pillar 2 ingestion also needs adjacency for spatial joins, and Pillar 4 analytics will too. Pushing it into Pillar 3 creates a cache that all other pillars must rebuild. The substrate is the right layer.

---

## Implementation Notes

- The full field list is locked in `cell_identity_schema.json` (v0.1.3).
- The database DDL for these fields is in `harmony/db/identity_registry_schema.sql`.
- The registration logic that computes and stores these fields is in `harmony/packages/registry/src/registry.py`.
- The regex for `cell_key` was updated from the v0.1.2 placeholder (5-char hash) to the production form (16-char hash) as part of this schema bump — see ADR-003 and Session 2 D3.
- The LOD hierarchy is confirmed at 12 levels (0–12), per Session 2 D2. The v0.1.2 `id_generation_rules.md` §4.4 table (which showed up to r15) is superseded.

---

*ADR-010 — Locked*
