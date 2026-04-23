# Harmony Spatial Operating System — Pillar I — Spatial Substrate
# Session 03 Summary: Cell Adjacency, Extended Schema, Database, Registry Service

> **Date:** 2026-04-10  
> **Session Type:** Technical Build  
> **Active Pillar:** Pillar 1 — Spatial Substrate  
> **Active Milestone:** Milestone 3 — Cell Adjacency & Identity Registry  
> **Builder Agent:** Spatial Substrate Engineer (Builder Agent 4)  
> **Schema Version Affected:** v0.1.3 (extends v0.1.2 with spatial geometry and adjacency fields)

---

## Summary

Designed and implemented the complete Cell Adjacency Model, Extended Cell Schema, PostgreSQL Database Schema, Identity Registry Service, and Sample Central Coast Dataset. Produced seven deliverables across five functional areas. The adjacency model defines all 24 directed boundary transitions for the gnomonic cube projection, verified by mutual adjacency tests across all 6 faces at Level 0 and boundary cells at Level 8. The registry service supports idempotent cell registration, entity anchoring, alias resolution, and adjacency ring queries. Session 2's 60-test suite remains fully green.

---

## Files Produced

| # | File | Path |
|---|------|------|
| 1 | Cell Adjacency Specification | `harmony/docs/cell_adjacency_spec.md` |
| 2 | Extended Cell Identity Schema (JSON) | `harmony/docs/cell_identity_schema.json` |
| 3 | Database Schema (canonical) | `harmony/db/identity_registry_schema.sql` |
| 4 | Database Migration (idempotent) | `harmony/db/migrations/001_initial_schema.sql` |
| 5 | Identity Registry Service (Python) | `harmony/packages/registry/src/registry.py` |
| 6 | Sample Central Coast Dataset | `harmony/data/sample-central-coast-records.json` |
| 7 | This session summary | `harmony/docs/sessions/SESSION_03_SUMMARY.md` |

All paths are relative to `pillar-1-spatial-substrate/`.

---

## Sample Central Coast Dataset — Cell Keys

| # | Description | Level | Cell Key |
|---|-------------|-------|----------|
| 1 | Planetary face (–X) | 0 | `hsam:r00:gbl:czvtf6fgxvptcxjv` |
| 2 | Gosford district | 4 | `hsam:r04:cc:yfme2b4kb7j69717` |
| 3 | Gosford CBD neighbourhood | 6 | `hsam:r06:cc:za6bzq7gfknrzd5z` |
| 4 | Gosford waterfront (test vector 1) | 8 | `hsam:r08:cc:g2f39nh7keq4h9f0` |
| 5 | Terrigal Beach feature | 10 | `hsam:r10:cc:dpya1spfwh11mf83` |

Record 4 matches Session 2 test vector 1 exactly, confirming cross-session consistency.

---

## Verification Results

### Session 2 Test Suite

**60 tests, 60 passed, 0 failed.** No regressions.

### Adjacency Mutual Symmetry

Tested all 24 directed boundary transitions at Level 0 (6 faces × 4 directions) and all 4 boundary cells at Level 8 on Face 1:

- **Level 0:** 24/24 mutual adjacency verified — every neighbour's neighbour list contains the original cell.
- **Level 8 boundary:** 16/16 mutual adjacency verified — inter-face transitions at all 4 edges of Face 1 confirmed symmetric.

### Cell Key Consistency

The Level 8 Gosford cell key in the sample dataset (`hsam:r08:cc:g2f39nh7keq4h9f0`) matches Session 2 test vector 1 exactly, confirming that the adjacency/registry code path produces identical cell keys to the standalone derivation module.

---

## Decisions Made During Implementation

### D1 — Adjacency Symmetry Is Directional, Not Oppositional

**Decision:** When cell A's +u neighbour is cell B (across a face boundary), cell B's neighbour that maps back to A may be in any direction (-u, +u, +v, or -v), not necessarily the opposite direction. This is because coordinate axes remap at face boundaries.

**Rationale:** The gnomonic cube projection maps each face's UV axes differently. Face 1's +u axis and Face 3's -u axis both point toward the same cube edge (x=-1, y=-1). This means their boundary cells are mutual neighbours through their respective -u edges. The adjacency invariant is "mutual reachability" (A is in B's neighbour set), not "direction reversal" (A's +u → B implies B's -u → A).

**Flag:** This is a consequence of the cube geometry and UV mapping, not a design choice. The spec documents this as invariant 1 in §7. No review needed.

### D2 — Edge Adjacency Stored, Vertex Adjacency Computed

**Decision:** The database stores only 4 edge-adjacent cell_keys per cell. Vertex adjacency (8 total neighbours) and adjacency rings are computed at runtime.

**Rationale:** Edge adjacency is O(1) to store and O(1) to look up. Vertex adjacency can be derived from edge adjacency via the boundary transition table in O(1). Storing all 8 neighbours would add 4 redundant entries per cell with no performance benefit for the common LOD prefetch case.

**Flag:** Low risk. If ring-2 prefetch proves to be a hot path, consider denormalising to 8 neighbours. Measure before changing.

### D3 — Schema Version Bump to 0.1.3

**Decision:** The extended schema is versioned 0.1.3. It extends v0.1.2 with new required fields (cube_face, face_grid_u, face_grid_v, edge_length_m, area_m2, distortion_factor, centroid_ecef, centroid_geodetic, adjacent_cell_keys). All v0.1.2 fields are preserved unchanged.

**Rationale:** The v0.1.2 schema did not include spatial geometry or adjacency fields. These are required for the registry to function as specified in the stage 1 brief. Adding them as required fields is a breaking change from v0.1.2 records, hence a minor version bump.

**Flag:** Any existing v0.1.2 records would need migration. Since no production data exists yet, this is a no-op.

### D4 — Cell Key Regex Updated for 16-Character Hash

**Decision:** The cell_key regex in the JSON schema and validation code was updated from the v0.1.2 illustrative pattern (`[a-z0-9]{5}$`) to the production pattern (`[0-9a-hjkmnp-tv-z]{16}$`), matching Session 2 decision D3.

**Rationale:** Session 2 increased the hash fragment from 5 characters to 16 characters (80 bits) based on collision analysis. The v0.1.2 id_generation_rules.md still references the old 5-char format. The updated regex accurately validates production cell keys.

**Flag:** The id_generation_rules.md source document (in files.zip) still contains the old regex. This should be updated in a future schema amendment to reflect the Session 2 decision. The new regex in this session's deliverables is authoritative.

### D5 — Deliverable 5 Truncation Handling

**Decision:** The Session 3 brief for Deliverable 5 was truncated at "Include one record at Level 6 (neighbourhood". The sample dataset includes 5 records at levels 0, 4, 6, 8, and 10, covering the full range from planetary to room scale within the Central Coast pilot region.

**Rationale:** The five levels provide representative coverage: one global (Level 0), three Central Coast levels matching the brief's visible intent (district, neighbourhood, parcel), and one fine-resolution record (Level 10) demonstrating sub-20m cells. Level 8 reuses Session 2's test vector 1 for cross-session verification.

**Flag:** If Mikey intended additional specific records (e.g., entities, Level 12 cells, or cells at specific landmarks), these can be added in a follow-up.

---

## Ambiguities Encountered and Resolution

### A1 — Inter-Face Vertex Adjacency at Cube Corners

At cube corners, three faces meet. A cell's diagonal neighbour at a corner is on the third face (neither of the two edge-neighbour faces). The spec defines the resolution algorithm (§3.3, §3.4) using a two-step path through an intermediate face. The implementation in the registry service uses iterative single-step resolution via `_resolve_neighbour_offset`, which handles this case correctly by stepping through each axis independently.

### A2 — Distortion Factor Computation

The distortion factor is defined as `sqrt(1 + u_c² + v_c²)` where (u_c, v_c) is the cell centroid in UV space. This approximates the linear stretch of the gnomonic projection. At face centres (u=v=0), the factor is exactly 1.0. At corners (u=v=1), it is sqrt(3) ≈ 1.732. The cell_geometry_spec.md quotes "~2.3×" for linear distortion — this is the stretch factor for edge length on the ellipsoid surface, which includes both the gnomonic distortion and the Jacobian of the cube-to-sphere mapping. The stored `distortion_factor` is the UV-space gnomonic component only. The `edge_length_m` field incorporates the full distortion.

### A3 — Region Code for Cross-Face Adjacent Cells

When computing adjacent cell_keys for a cell near a face boundary, the neighbouring cell may be on a different cube face that spans a different geographic region. The current implementation uses the source cell's region_code for all neighbours. This is acceptable for the Central Coast pilot (all cells are on Face 1), but may need revision for global deployments where adjacent cells cross region boundaries.

---

## Consistency Check

### Against HARMONY_MASTER_SPEC_V1.0.md

- **North Star I (Seamless World):** Lateral adjacency enables predictive LOD prefetch. Combined with parent-child hierarchy, the rendering engine can now prefetch both vertically (zoom) and laterally (movement).
- **North Star II (GPS-Free Substrate):** Adjacency ring computation at sub-metre resolutions (Level 12) enables autonomous systems to traverse the cell grid without GPS.
- **North Star III (Spatial Knowledge Interface):** The registry service provides the resolve_canonical, resolve_alias, and resolve_cell_key operations needed by the Interaction Layer.

### Against pillar-1-spatial-substrate-stage1-brief.md

- **Database model:** All 4 tables (identity_registry, cell_metadata, alias_table, entity_table) implemented as specified, with additional columns for spatial geometry and adjacency.
- **Registry service:** Implements register_cell (idempotent), register_entity, resolve_canonical, resolve_alias per the brief's API contracts.
- **Sample data:** 5 Central Coast cells at varying resolution levels.

### Against Session 02 Deliverables

- Cell key derivation produces identical results (test vector 1 verified).
- 60/60 Session 2 tests pass without modification.
- The boundary transition table is consistent with the cube face UV mapping and inverse projection from derive.py.

---

## What Is Now Unlocked for Session 4

1. **Alias System (Milestone 3):** The alias_table and registry.resolve_alias() are in place. Session 4 can implement alias generation rules, namespace handling, and ambiguity resolution.

2. **Cell Identity Integration (Milestone 4):** The cell_id + cell_key linkage is implemented. Sample Central Coast cells demonstrate the full flow from coordinates → cell_key → registered cell with adjacency.

3. **API Layer (Milestone 5):** The registry service provides the backend operations that the REST API layer will expose. Session 5 can wrap these in HTTP endpoints.

4. **Adjacency-Based LOD Prefetch:** The rendering engine (Pillar 3) can now query a cell's neighbours at any resolution and compute adjacency rings for movement prediction.

5. **Distributed Ingestion:** The compute_adjacent_cell_keys function operates without database access, enabling ingestion pipelines to compute adjacency independently.

---

## Cross-Pillar Implications

- **Pillar II (Data Ingestion):** Ingestion pipelines can now compute full cell metadata (geometry, adjacency, cell_key) independently of the registry, then register idempotently. The compute_cell_geometry and compute_adjacent_cell_keys functions in the registry module support this.

- **Pillar III (Rendering):** The 4-direction edge adjacency stored per cell enables O(1) neighbour lookup for LOD prefetch. Ring computation for k=1..3 is O(k). The renderer should request ring-1 for current movement direction and ring-2 for aggressive prefetch.

- **Pillar V (Interaction):** The resolve_alias and resolve_cell_key functions provide the resolution primitives needed by the Conversational Spatial Agent (ADR-008).

---

*End of Session 03 Summary*
