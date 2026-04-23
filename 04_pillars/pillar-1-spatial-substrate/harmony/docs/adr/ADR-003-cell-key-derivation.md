# Harmony Spatial Operating System — Pillar I — Spatial Substrate

# ADR-003: Cell Key Derivation Architecture

| Field | Value |
|-------|-------|
| **Title** | Cell Key Derivation Architecture |
| **Status** | Accepted |
| **Date** | April 2026 |
| **Deciders** | Mikey (Founder/PM), Architecture Lead (Builder Agent 1) |
| **Supersedes** | ADR-004-cell-id-vs-cell-key.md (extends, does not replace) |

---

## Context

The Harmony Cell System requires every cell to carry a deterministic, reproducible spatial address — the `cell_key` — alongside its opaque canonical identifier (`cell_id`). ADR-004 (cell-id-vs-cell-key) established that both identifiers are mandatory and that the cell_key must be derivable from geometry alone. This ADR specifies how that derivation works.

The core tension is between three competing requirements:

1. **Determinism.** Two independent systems processing the same geometry must produce the same cell_key without any shared state, network calls, or database lookups. This enables registry-free substrate operations and idempotent ingestion.

2. **Global coverage without special cases.** The derivation must handle every point on the Earth's surface — including the poles, the antimeridian, and equatorial regions — with the same algorithm. No special-case code, no boundary wrapping, no degenerate cells.

3. **Human readability.** A developer must be able to look at a cell_key and immediately identify the resolution level, the approximate geographic region, and the namespace — without tooling.

The Harmony Master Specification V1.0 establishes that the Spatial Substrate serves all three North Stars. The cell_key derivation must be correct enough for sub-metre robotic navigation (North Star II), efficient enough for real-time rendering LOD selection (North Star I), and stable enough for the Spatial Knowledge Interface to reference over time (North Star III).

---

## Decision

### 1. Custom Spatial Addressing System

The Harmony Cell System uses a purpose-built gnomonic cube projection with recursive grid subdivision. H3, S2, DGGRID, and all existing open-source spatial index libraries are excluded. The cell geometry, hierarchy, and addressing logic are Harmony-proprietary infrastructure.

**Rationale:** Existing spatial indices carry design constraints that do not align with all three North Stars. H3 uses hexagonal tiling that cannot subdivide hierarchically without fill cells. S2 is a mature library but introduces an external dependency with its own versioning, release cadence, and design decisions that Harmony cannot control. Both are optimised for database indexing, not for continuous LOD rendering or robotic navigation. A custom system allows Harmony to optimise for all three use cases simultaneously from the foundation up.

### 2. Gnomonic Cube Projection

The Earth's surface is tiled by projecting the WGS84 ellipsoid onto the six faces of an enclosing cube via gnomonic (central) projection. Each face is recursively subdivided into a regular grid. At resolution level r, each face contains 4^r × 4^r cells, giving 6 × 16^r cells globally.

This provides 13 resolution levels (0–12) ranging from planetary scale to sub-metre (approximately 0.76 m cell edges at Level 12 near cube face centres).

### 3. ECEF Coordinate Frame for Derivation

Cell key derivation operates in ECEF (Earth-Centered Earth-Fixed) coordinates. The cell centroid is computed as an ECEF point on the WGS84 ellipsoid surface. This was chosen over geodetic coordinates because ECEF provides a uniform three-dimensional coordinate space with no singularities at the poles or antimeridian.

### 4. ENU Local Frames Inside Cells

All geometry within a cell is expressed in ENU (East-North-Up) local coordinates, with the origin at the cell centroid. The transition from global to local is a deterministic affine transformation (ECEF → ENU at the centroid). This provides a flat, human-intuitive coordinate space for all in-cell operations — rendering, collision detection, entity positioning.

The cell_key is derived in ECEF. Everything inside the cell reasons in ENU. These operate at different layers and are complementary, not competing.

### 5. BLAKE3 Hashing

The cell_key hash fragment is produced by feeding the ECEF centroid coordinates (as IEEE 754 doubles, little-endian) and the resolution level into BLAKE3, then encoding the first 80 bits (10 bytes) as Crockford Base32 (16 characters).

BLAKE3 was chosen for: deterministic output across all platforms, cryptographic collision resistance, public-domain licensing (CC0), high performance, and a single canonical implementation.

### 6. Cell Key Format

```
hsam:r{level:02d}:{region_code}:{hash_fragment}
```

Every component is human-readable: the namespace (`hsam`), the resolution level (`r08`), the geographic region (`cc`), and a unique hash fingerprint. A developer can parse this with their eyes.

---

## Alternatives Considered

### H3 (Uber)

Hexagonal hierarchical spatial index. Rejected because: (a) hexagons cannot subdivide into hexagons — H3 uses a mixed hex/pentagon tiling with aperture-7 subdivision, creating non-uniform cell sizes; (b) H3 is optimised for database indexing, not continuous LOD rendering; (c) external dependency with its own release cadence; (d) excluded by architectural decision.

### S2 (Google)

Hilbert curve on cube faces. Rejected because: (a) S2 cell IDs are opaque 64-bit integers — not human-readable; (b) S2's Hilbert curve ordering is optimised for spatial locality in database queries, not for hierarchical LOD streaming; (c) external dependency; (d) excluded by architectural decision.

### Latitude-Longitude Grid Hashing

Hash lat/lon directly into a cell address. Rejected because: (a) latitude-longitude grids degenerate at the poles (cell area → 0 as latitude → ±90°); (b) the antimeridian creates a discontinuity (179.9° and -179.9° are adjacent but numerically distant); (c) cell sizes vary dramatically with latitude.

### Geohash

Base32-encoded interleaved lat/lon bits. Rejected for the same reasons as lat-lon grids, plus: geohash cells have non-uniform aspect ratios, and the Z-order curve produces poor spatial locality compared to Hilbert or cube-face approaches.

---

## Consequences

### Positive

- **Registry-free derivation.** Any system with coordinates and a resolution level can derive the cell_key independently, without database access. This enables offline ingestion, edge computing, and distributed processing.
- **Idempotent ingestion.** Re-processing the same geometry always produces the same cell_key, which resolves to the same cell_id in the registry. No duplicate cells.
- **Seamless global coverage.** The cube projection handles poles, antimeridian, and equatorial regions with zero special-case code. Verified by test vectors.
- **Human-readable addresses.** Developers can inspect cell keys in logs, databases, and URLs without tooling.
- **North Star I alignment.** The hierarchical grid directly supports continuous LOD — parent cells provide coarse geometry, children provide detail. No tile switching.
- **North Star II alignment.** Sub-metre resolution at Level 12 provides the granularity needed for robotic navigation and SLAM anchoring.
- **North Star III alignment.** Stable, deterministic cell addresses allow the Spatial Knowledge Interface to reference locations over time without breakage.
- **No external dependencies.** The spatial indexing logic is fully owned, versioned, and controlled by Harmony.

### Negative

- **Gnomonic distortion.** Cells near cube face edges and corners are up to 2.3× larger (linearly) than cells near face centres at the same resolution. This is a documented property, not a bug, but it means "Level 8 ≈ 194 m" is an approximation that varies by position. Worst case at corners: ~446 m at Level 8.
- **Custom implementation burden.** No existing library to lean on. Every part of the spatial logic must be implemented, tested, and maintained by Harmony.
- **BLAKE3 dependency.** The derivation requires BLAKE3, which is not in the Python standard library. This is a single, well-maintained, public-domain dependency.
- **Geocentric vs. geodetic latitude approximation.** The cube face projection operates on geocentric direction vectors, not geodetic normals. The centroid conversion includes a geocentric-to-geodetic correction, but the cell boundary is defined in the projected space, not on the ellipsoid. For cell sizes above ~1 m, this introduces no practical error.
- **80-bit hash fragment.** At very high resolution (Level 12) over very large regions, hash collisions become theoretically possible. Mitigated by granular region codes and registry-side collision detection.

### Neutral

- The resolution parameter is a runtime input, not a compile-time constant. Adding levels beyond 12 requires only a constant change.
- Region codes are an input parameter. The coordinate-to-region mapping is maintained separately.

---

## North Star Alignment

| North Star | How This Decision Serves It |
|-----------|---------------------------|
| **I — The Seamless World** | Hierarchical grid with 16× subdivision per level maps directly to continuous LOD streaming. Parent cells hold coarse geometry; children refine. The rendering engine traverses the tree, not a tile index. |
| **II — GPS-Free Spatial Substrate** | Sub-metre cells (Level 12, ~0.76 m) provide the granularity for SLAM anchoring. Deterministic cell keys enable autonomous systems to derive spatial addresses without network access. |
| **III — Spatial Knowledge Interface** | Stable, reproducible cell keys give the Interaction Layer permanent spatial references that survive alias changes, geometry refinements, and registry migrations. |

---

*End of ADR-003*
