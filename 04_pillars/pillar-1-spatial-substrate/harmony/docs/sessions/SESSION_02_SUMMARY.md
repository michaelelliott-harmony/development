# Harmony Spatial Operating System — Pillar I — Spatial Substrate
# Session 02 Summary: Cell Key Derivation Module

> **Date:** 2026-04-10  
> **Session Type:** Technical Build  
> **Active Pillar:** Pillar 1 — Spatial Substrate  
> **Active Milestone:** Milestone 2 — Cell Key Derivation  
> **Builder Agent:** Spatial Substrate Engineer (Builder Agent 4)  
> **Schema Version Affected:** v0.1.2 (unchanged — this session implements, does not amend schema)

---

## Summary

Designed and implemented the complete Cell Key Derivation Module — the foundational spatial addressing component of the Harmony Cell System. Produced five deliverables: geometry specification, derivation specification, Python implementation, 60-test unit test suite, and ADR-003 (originally numbered ADR-004). All three spec test vectors pass. The module is deterministic, handles poles and antimeridian without special-casing, and supports all 13 resolution levels (0–12) from planetary to sub-metre.

---

## Files Produced

| # | File | Path |
|---|------|------|
| 1 | Cell Geometry Specification | `harmony/docs/cell_geometry_spec.md` |
| 2 | Cell Key Derivation Specification | `harmony/docs/cell_key_derivation_spec.md` |
| 3 | Cell Key Derivation Module (Python) | `harmony/packages/cell-key/src/derive.py` |
| 4 | Unit Test Suite | `harmony/packages/cell-key/tests/test_derive.py` |
| 5 | ADR-003: Cell Key Derivation Architecture | `harmony/docs/adr/ADR-003-cell-key-derivation.md` |
| 6 | This session summary | `harmony/docs/sessions/SESSION_02_SUMMARY.md` |

All paths are relative to `pillar-1-spatial-substrate/`.

---

## Test Vectors — Final Cell Keys

| Vector | Input | Cell Key |
|--------|-------|----------|
| 1 — Central Coast NSW (Gosford) | lat=-33.42, lon=151.34, r=8, region=cc | `hsam:r08:cc:g2f39nh7keq4h9f0` |
| 2 — North Pole | lat=90.0, lon=0.0, r=8, region=gbl | `hsam:r08:gbl:6kmmz1fbpj8sg3ba` |
| 3 — Antimeridian (Equator) | lat=0.0, lon=180.0, r=8, region=gbl | `hsam:r08:gbl:r4cdvsyrqj9yp7cg` |

Test suite: **60 tests, 60 passed, 0 failed.**

---

## Decisions Made During Implementation

The following decisions were not explicitly covered by the session brief and were resolved during implementation. All are flagged for human review.

### D1 — Cell Shape: Gnomonic Cube Projection (not specified in brief)

**Decision:** Cells are defined by gnomonic projection of the ellipsoid onto six cube faces with recursive 4×4 grid subdivision per level.

**Rationale:** The brief specified seamless global coverage, no gaps/overlaps, no singularities, hierarchical containment, and deterministic centroids. The gnomonic cube projection satisfies all five. Hexagonal grids cannot subdivide hierarchically. Lat-lon grids degenerate at poles. Triangular grids produce irregular shapes.

**Flag:** This is the most consequential decision of the session. It defines the geometry for the entire Harmony Cell System. Mikey should confirm that the gnomonic distortion (cells up to 2.3× larger at cube face corners vs centres) is acceptable.

### D2 — Subdivision Factor: 4× per Axis (16 children per cell)

**Decision:** Each resolution level divides each axis by 4, giving 16 children per parent cell and 4^r × 4^r grid cells per cube face at level r.

**Rationale:** This produces exactly 13 levels (0–12) spanning planetary to sub-metre, matching the brief's specification. A 2× factor (standard quadtree) would require 24 levels for sub-metre. A 4× factor provides a cleaner, more compact level numbering while maintaining the quadtree property (each 4× step is equivalent to two 2× steps).

**Flag:** Low risk — this is a mathematical convenience. The number of children per cell (16) is larger than typical quadtrees (4). Confirm this is acceptable for LOD streaming in Pillar 3.

### D3 — Hash Fragment Length: 16 Characters (80 bits)

**Decision:** The BLAKE3 output is truncated to 10 bytes (80 bits) and encoded as 16 Crockford Base32 characters. The original spec example used 5 characters (~25 bits).

**Rationale:** 25 bits provides only ~33 million possible values per (resolution, region) partition. At Level 12 for the Central Coast pilot region alone (~2.9 billion cells), collisions would be near-certain. 80 bits provides birthday-bound collision probability of ~3.5 × 10^-6 at Level 12 for Central Coast — negligible.

**Flag:** This changes the cell_key string length from the illustrative example. The key `hsam:r08:cc:g2f39nh7keq4h9f0` is 33 characters (vs the spec example's 22). Confirm this length is acceptable for database columns, URLs, and log output.

### D4 — Geocentric-to-Geodetic Latitude Correction

**Decision:** The cube face projection operates on geocentric direction vectors. When computing the ECEF centroid from the grid cell centre, a geocentric-to-geodetic latitude correction is applied: `geodetic_lat = atan2(tan(geocentric_lat), (1 - e²))`.

**Rationale:** Without this correction, the ECEF centroid would not lie on the WGS84 ellipsoid surface. The correction ensures the centroid is a valid ECEF point at altitude 0, which is required for the hash input.

**Flag:** This is a standard geodetic transformation. No review needed unless someone disputes the formula.

### D5 — Cube Face Tie-Breaking: X beats Y beats Z

**Decision:** When a point's direction vector has two or more axis components with equal absolute values (e.g., on a cube edge), the lowest-index axis wins (X > Y > Z).

**Rationale:** Determinism requires that every point maps to exactly one face. The tie-breaking rule is arbitrary but must be consistent. "Lowest index wins" is the simplest rule.

**Flag:** Low risk. Only affects points on exact cube-face boundaries, which are geometrically rare.

---

## Ambiguities Encountered and Resolution

### A1 — Hash Fragment Length (see D3 above)

The brief and spec examples used `a91f2` (5 characters). The collision analysis showed this was insufficient. Resolved by increasing to 16 characters (80 bits) with documented rationale.

### A2 — Inverse Cube Face Projection for Negative Faces

Initial implementation had a sign error in the inverse projection for negative cube faces (-X, -Y, -Z). Detected via roundtrip verification (project → grid snap → inverse project → compare). Corrected before any deliverables were finalized. The forward projection divides by |dominant axis|, so the inverse for negative faces must produce (dominant = -1, u, v), not (dominant = -1, -u, -v).

### A3 — Level 0 Grid Behaviour

At Level 0, 4^0 = 1, meaning one cell per face. The grid snap reduces to i=0, j=0 and the centroid is the face centre. This is handled as a special case in the snapping logic (no floor/clamp needed).

---

## ADR-003 Consistency Check

ADR-003 (Cell Key Derivation Architecture, originally ADR-004) is consistent with:

- **HARMONY_MASTER_SPEC_V1.0.md:** Serves all three North Stars. Custom spatial system (no H3/S2). Sub-metre resolution for North Star II. Hierarchical structure for North Star I continuous LOD. Stable addresses for North Star III.

- **pillar-1-spatial-substrate-stage1-brief.md:** Implements cell_key derivation as specified. ECEF hashing, BLAKE3, Crockford Base32 encoding. Deterministic output. The format `hsam:r{level}:{region}:{hash}` matches the brief. The hash fragment length was increased from the illustrative example (documented in D3 above).

- **ADR-004-cell-id-vs-cell-key.md (original):** This new ADR extends the original. The dual-identifier model (cell_id + cell_key) is preserved. cell_key is derived from geometry, cell_id is opaque and stable. Both are mandatory on every cell record. No contradictions.

- **id_generation_rules.md:** The cell_key format matches the specified `hsam:r<level>:<region>:<hash>`. The BLAKE3 derivation from geometry snapping → centroid → hash is implemented as specified. Crockford Base32 encoding matches.

---

## What Is Now Unlocked for Session 3

With the Cell Key Derivation Module complete and tested, the following are now unblocked:

1. **Identity Registry Service (CRUD):** The registry can now accept cell registrations that include a computed cell_key. The `derive_cell_key` function provides the input for the cell_key column.

2. **Idempotent Cell Registration:** The registry can detect re-registration of the same geometry by computing the cell_key and checking the UNIQUE index. If the key already exists, return the existing cell_id.

3. **Sample Central Coast Data:** The derivation module can generate cell_keys for any coordinate in the Central Coast pilot region at any resolution level.

4. **Cell Key Validation:** The `parse_cell_key` function enables the API layer to validate incoming cell_keys without database lookups.

5. **Database Schema Finalization:** The DDL for `cell_metadata.cell_key` can now be specified as `TEXT UNIQUE NOT NULL` with a known format and validation regex.

---

## Cross-Pillar Implications

- **Pillar III (Rendering):** The 16-child-per-cell hierarchy (4×4 per level) affects LOD tree traversal. The rendering engine will walk this tree structure. Confirm that 16 children per node is acceptable for the rendering pipeline.

- **Pillar II (Data Ingestion):** Ingestion pipelines can now derive cell_keys for incoming data independently, without registry access. This enables distributed ingestion.

---

*End of Session 02 Summary*
