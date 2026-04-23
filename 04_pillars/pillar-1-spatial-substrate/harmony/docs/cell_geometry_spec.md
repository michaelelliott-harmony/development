# Harmony Spatial Operating System — Pillar I — Spatial Substrate
# Cell Geometry Specification

> **Version:** 1.0  
> **Status:** Accepted  
> **Date:** April 2026  
> **Scope:** Defines the geometric structure, hierarchy, addressing format, and coverage guarantees of the Harmony Cell System.  
> **Governing Documents:** HARMONY_MASTER_SPEC_V1.0.md, pillar-1-spatial-substrate-stage1-brief.md

---

## 1. Design Mandate

The Harmony Cell System is a custom, purpose-built spatial addressing architecture. It is not an adaptation or wrapper around any existing spatial index. H3, S2, DGGRID, and all existing open-source spatial index libraries are excluded by architectural decision. The cell geometry, hierarchy, and addressing logic are Harmony-proprietary infrastructure, designed from first principles to serve all three North Stars simultaneously.

---

## 2. Cell Shape — Gnomonic Cube Projection

### 2.1 Shape Definition

A Harmony Cell is a quadrilateral defined by the gnomonic projection of the WGS84 reference ellipsoid onto the six faces of an enclosing cube, then recursively subdivided using a regular grid on each face.

At each resolution level, every cube face is divided into a regular grid of N × N cells, where N = 4^r and r is the resolution level. Each cell on the cube face is a square in the projected UV coordinate space. When projected back onto the ellipsoid surface, the cell boundary is a curved quadrilateral.

### 2.2 Why This Shape

The requirements that constrain the choice of cell shape are:

**Seamless global coverage with no gaps and no overlaps.** The six faces of the enclosing cube tile the sphere exactly. Every point on the Earth's surface falls on exactly one cube face (with deterministic tie-breaking at edges and corners). Within each face, the regular grid partitions the face without gaps or overlaps.

**Hierarchical containment.** Each cell at level r subdivides cleanly into exactly 16 child cells at level r+1 (a 4×4 grid within the parent). Every child cell is fully contained within its parent. There are no partial containment or boundary-spanning issues within a single face.

**Deterministic centroid computation.** Given a coordinate and a resolution level, the containing cell and its centroid can be computed in O(1) arithmetic operations with no lookup tables or iterative searches.

**Compatibility with the two-identifier model (cell_id + cell_key).** The cell_key derivation algorithm requires a deterministic, reproducible centroid from which to derive the BLAKE3 hash. The gnomonic cube projection provides this.

### 2.3 Alternatives Considered and Rejected

**Hexagonal grids (H3-style):** Cannot tile hierarchically — hexagonal subdivision leaves gaps or requires pentagonal fill cells. Excluded by architectural decision.

**Icosahedral grids (DGGRID/S2-style):** S2 uses a quadtree on cube faces similar to this system but is excluded as an external dependency. DGGRID uses different tiling approaches with more complex face topology. Both are existing libraries excluded by decision.

**Latitude-longitude grids:** Degenerate at the poles (cell area approaches zero) and create singularities at the antimeridian. Unsuitable for a system that must provide uniform coverage.

**Triangular subdivision:** Produces irregular cell shapes that complicate centroid computation and do not naturally align with quadtree hierarchy.

---

## 3. Hierarchy — Resolution Levels 0 Through 12

### 3.1 Subdivision Rule

Each resolution level subdivides the prior level by a factor of 4 in each axis (16 children per cell). At resolution level r, each of the 6 cube faces contains 4^r × 4^r cells, giving a total of 6 × 16^r cells globally.

### 3.2 Resolution Table

The cell edge length at each level is approximate, calculated for cells near the centre of a cube face (minimum gnomonic distortion). The formula is: edge ≈ R × 2 / 4^r, where R = 6,371,000 m (mean Earth radius).

| Level | Grid per Face | Total Cells | Approx Edge (face centre) | Approx Area (face centre) | Use Case |
|-------|--------------|-------------|--------------------------|--------------------------|----------|
| 0 | 1 × 1 | 6 | ~12,742 km | Planetary | Global partitioning |
| 1 | 4 × 4 | 96 | ~3,186 km | Continental | Continental regions |
| 2 | 16 × 16 | 1,536 | ~796 km | Sub-continental | Large geographic regions |
| 3 | 64 × 64 | 24,576 | ~199 km | Regional | State/province scale |
| 4 | 256 × 256 | 393,216 | ~49.8 km | District | Metropolitan areas |
| 5 | 1,024 × 1,024 | 6,291,456 | ~12.4 km | Municipal | Suburbs, townships |
| 6 | 4,096 × 4,096 | 100,663,296 | ~3.1 km | Neighbourhood | City blocks, precincts |
| 7 | 16,384 × 16,384 | ~1.6 billion | ~777 m | Block | Individual street blocks |
| 8 | 65,536 × 65,536 | ~25.8 billion | ~194 m | Parcel | Property parcels, buildings |
| 9 | 262,144 × 262,144 | ~412 billion | ~48.6 m | Structure | Individual structures |
| 10 | 1,048,576 × 1,048,576 | ~6.6 trillion | ~12.2 m | Room | Indoor spaces, zones |
| 11 | 4,194,304 × 4,194,304 | ~105 trillion | ~3.0 m | Feature | Structural features, furniture |
| 12 | 16,777,216 × 16,777,216 | ~1.7 quadrillion | ~0.76 m | Sub-metre | Robotic navigation, SLAM anchors |

### 3.3 Gnomonic Distortion

Because the gnomonic projection distorts area away from the face centre, cells near cube face edges and corners are larger than cells near face centres at the same resolution level. The maximum distortion factor occurs at the cube face corners (where UV coordinates approach ±1 on both axes):

- **Area distortion at corner:** (1 + u² + v²)^(3/2) where u = v = 1 → factor of 3^(3/2) ≈ 5.2×
- **Linear distortion at corner:** approximately √5.2 ≈ 2.3×

At Level 12, cells near face corners have edge lengths of approximately 0.76 m × 2.3 ≈ 1.75 m. At Level 12 near face centres, cells are approximately 0.76 m — sub-metre as required by North Star II (GPS-free spatial substrate for robotic navigation).

This distortion is a known, documented property. It does not compromise the system's guarantees: every cell has a unique, deterministic centroid and a deterministic cell_key regardless of its position on the cube face.

### 3.4 Parent-Child Containment

At resolution level r, a cell occupies grid position (i, j) on face f. Its 16 children at level r+1 occupy positions (4i + di, 4j + dj) for di, dj in {0, 1, 2, 3}. This is a strict containment: every child cell falls entirely within its parent's UV boundary. There is no partial containment.

---

## 4. Addressing Format — The Cell Key

### 4.1 Format Definition

Every Harmony Cell is addressed by a deterministic string called the **cell_key**, formatted as:

```
hsam:r{level:02d}:{region_code}:{hash_fragment}
```

**Example:** `hsam:r08:cc:g2f39nh7keq4h9f0`

### 4.2 Component Breakdown

| Component | Encoding | Description |
|-----------|----------|-------------|
| `hsam` | Fixed UTF-8 string | Harmony Spatial Address Model namespace. Identifies this as a Harmony cell key (not an H3 index, not an S2 cell ID, not a lat-lon pair). |
| `r{level:02d}` | "r" + zero-padded 2-digit integer | Resolution level, 00–12. A developer can read the resolution directly: `r08` = Level 8 (~194 m cells at face centre). |
| `{region_code}` | Lowercase alphabetic string | Harmony region identifier. Segments the hash space and provides human-readable geographic context. Examples: `cc` (Central Coast NSW), `gbl` (global/fallback). |
| `{hash_fragment}` | 16 characters, Crockford Base32 | Truncated BLAKE3 hash of the cell's ECEF centroid coordinates. 80 bits of collision-resistant fingerprint. |

### 4.3 Human Readability

A developer can parse a cell_key without any tooling or database lookup:

- `hsam:` → This is a Harmony spatial address.
- `r08:` → Resolution level 8 (~194 m cells).
- `cc:` → Central Coast NSW region.
- `g2f39nh7keq4h9f0` → Unique cell fingerprint within this resolution and region.

### 4.4 Crockford Base32 Alphabet

The hash fragment uses the Crockford Base32 alphabet (lowercase):

```
0123456789abcdefghjkmnpqrstvwxyz
```

This is the standard Base32 alphabet with four confusable characters excluded: `i`, `l`, `o`, `u`. This prevents misreading in logs, URLs, and printed output.

### 4.5 Hash Fragment Length

The hash fragment is 16 characters of Crockford Base32, encoding 80 bits (10 bytes) of BLAKE3 output. At 80 bits, the birthday-bound collision probability for k cells within a single (resolution, region) bucket is approximately k² / 2^81. For the Central Coast pilot region at Level 8 (~72,000 cells), the collision probability is approximately 1.5 × 10^-14 — negligible. See the Cell Key Derivation Specification for collision analysis at higher resolutions and the collision policy.

---

## 5. Cube Face Assignment

### 5.1 Face Numbering

The six cube faces are numbered 0–5, assigned by the dominant axis of the ECEF direction vector:

| Face | Name | Condition | UV Mapping |
|------|------|-----------|------------|
| 0 | +X | \|x\| ≥ \|y\| and \|x\| ≥ \|z\| and x ≥ 0 | u = y/\|x\|, v = z/\|x\| |
| 1 | -X | \|x\| ≥ \|y\| and \|x\| ≥ \|z\| and x < 0 | u = y/\|x\|, v = z/\|x\| |
| 2 | +Y | \|y\| > \|x\| and \|y\| ≥ \|z\| and y ≥ 0 | u = x/\|y\|, v = z/\|y\| |
| 3 | -Y | \|y\| > \|x\| and \|y\| ≥ \|z\| and y < 0 | u = x/\|y\|, v = z/\|y\| |
| 4 | +Z | \|z\| > \|x\| and \|z\| > \|y\| and z ≥ 0 | u = x/\|z\|, v = y/\|z\| |
| 5 | -Z | \|z\| > \|x\| and \|z\| > \|y\| and z < 0 | u = x/\|z\|, v = y/\|z\| |

Tie-breaking: when two or more absolute components are equal, the axis with the lowest index (X < Y < Z) wins. This is deterministic and produces consistent assignments at cube edges and corners.

### 5.2 UV Coordinate Space

On each face, u and v range over [-1, 1]. The point (u=0, v=0) is the face centre — the point on the sphere directly along the face's dominant axis direction. The corners (u=±1, v=±1) correspond to the cube edges shared with adjacent faces.

### 5.3 Inverse Projection

The inverse mapping from (face, u, v) back to a unit-sphere direction is:

| Face | Direction Vector (before normalisation) |
|------|---------------------------------------|
| 0 (+X) | (1, u, v) |
| 1 (-X) | (-1, u, v) |
| 2 (+Y) | (u, 1, v) |
| 3 (-Y) | (u, -1, v) |
| 4 (+Z) | (u, v, 1) |
| 5 (-Z) | (u, v, -1) |

The direction vector is normalised to unit length before conversion to geodetic coordinates.

---

## 6. Coverage Guarantees

### 6.1 Poles

The poles are handled naturally by the cube projection. The north pole (z dominant, positive) falls on Face 4 (+Z) at approximately (u=0, v=0). The south pole falls on Face 5 (-Z) at approximately (u=0, v=0). There is no singularity, no degenerate cell, and no special-case logic. Polar cells are slightly distorted (like all cells away from face centres) but fully valid.

### 6.2 Antimeridian

The antimeridian (180°E / 180°W) is not a boundary in the cube projection. A point at longitude 180° on the equator falls on Face 1 (-X) at (u≈0, v≈0). Points near the antimeridian fall on whichever cube face their ECEF direction vector maps to. There is no wrap-around, no discontinuity, and no special-case logic.

### 6.3 Equatorial Regions

The equator runs through Faces 0 (+X), 1 (-X), 2 (+Y), and 3 (-Y). Cells near the equator and near face centres have the lowest distortion in the system — these are the "best case" cells in terms of shape regularity.

### 6.4 Face Boundaries

Points on cube face boundaries (where two faces meet) are assigned to one face by the deterministic tie-breaking rule in Section 5.1. A point that falls exactly on the boundary between Face 0 and Face 2 (where |x| = |y|) is assigned to Face 0 (X wins ties over Y). This means every point on the sphere maps to exactly one face, one grid cell, and one cell_key. There are no orphan points.

---

## 7. Coordinate Frame Relationship

### 7.1 ECEF for Cell Key Derivation

Cell keys are derived from ECEF coordinates. The cell centroid is computed as an ECEF point on the WGS84 ellipsoid surface (altitude = 0). This is the input to the BLAKE3 hash. See the Cell Key Derivation Specification for the full algorithm.

### 7.2 ENU for Cell-Internal Geometry

All geometry, entity positions, and structural data within a cell are expressed in the cell's local ENU (East-North-Up) frame, with the origin at the cell centroid. The ENU frame is a tangent-plane approximation that is highly accurate for the cell sizes used in Harmony (sub-200 m at Level 8 and below).

### 7.3 Transition Rule

Global to Local: ECEF → ENU at the cell centroid.
Local to Global: ENU → ECEF (inverse rotation and translation).

This is a deterministic, well-defined affine transformation. The cell_key is derived in ECEF. Everything inside the cell reasons in ENU.

---

## 8. Constraints and Future-Proofing

### 8.1 Resolution as Runtime Parameter

The resolution level is a runtime input, not a compile-time constant. Adding resolution levels beyond 12 (for sub-centimetre applications) requires no code changes to the derivation module — only an update to the MAX_RESOLUTION constant and the resolution table.

### 8.2 Region Codes

Region codes are an input parameter to the derivation algorithm. The mapping from coordinates to region codes is maintained as a separate lookup — it is not part of the cell geometry or derivation logic. This decouples regional governance from spatial mathematics.

### 8.3 Compatibility with Future Pillars

The cell geometry is designed to support:
- **Pillar II (Data Ingestion):** Dual-fidelity data attaches to cells at appropriate resolution levels.
- **Pillar III (Rendering):** The hierarchical structure supports continuous LOD streaming — parent cells provide coarse geometry, children provide detail.
- **Pillar IV (Spatial Knowledge):** Temporal versioning attaches to cell identity, not cell geometry.
- **Pillar V (Interaction):** Named-entity resolution resolves to cells via the Identity Registry.

---

*End of Cell Geometry Specification*
