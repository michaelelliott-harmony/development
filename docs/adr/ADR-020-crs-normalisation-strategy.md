# ADR-020 — CRS Normalisation Strategy

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-23 |
| **Deciders** | Dr. Mara Voss (Principal Architect), Mikey (founder) |
| **Pillar** | 2 — Data Ingestion Pipeline (Milestone 2) |
| **Related ADRs** | ADR-002 (Gnomonic Cube Projection), ADR-003 (Cell Key Derivation), ADR-010 (Spatial Geometry Schema Extension) |

---

## Context

The Harmony Cell System is WGS84-native: every cell key derivation, every
centroid, every adjacency calculation assumes geographic coordinates on
the WGS84 ellipsoid (ADR-002, ADR-003). Real-world geospatial data does
not arrive in WGS84. It arrives in national grids, local projections,
and legacy datums with varying degrees of declared accuracy.

The Central Coast MVP receives data principally in GDA2020 (Geocentric
Datum of Australia 2020) and legacy GDA94. Federal datasets sometimes
use MGA zones (Map Grid of Australia). Some council datasets arrive in
CRS-unspecified CSV with no formal metadata. Treating any of these as
WGS84 without conversion introduces systematic errors of 1–2 metres
(GDA2020↔WGS84 at modern epoch) to hundreds of metres (GDA94 untreated).

At r10 resolution (parcel/building scale), a 1-metre error is the
difference between a building being in one cell or an adjacent one. That
is not tolerable for a substrate whose foundational guarantee is
"same physical location always produces the same Harmony address."

This ADR establishes the canonical CRS, the normalisation rules, and the
metadata every ingested geometry must carry.

---

## Decision

### 1. Canonical CRS: WGS84, EPSG:4326

All geometries stored in the Harmony Cell registry are in **WGS84
(EPSG:4326)**. No exceptions. This is the only CRS the cell derivation
pipeline (`derive.py`, `registry.py`) accepts.

Cells, centroids, adjacency, and cell-key derivation inputs are all in
WGS84. The decision is final, not negotiable, and not per-dataset.

### 2. Every ingested geometry declares `source_crs`

The ingestion manifest schema (Pillar 2 Milestone 4) requires a
`source_crs` field on every dataset. The field is an EPSG code or a
full WKT string. Ingestion **refuses** any dataset without a declared
source CRS — there is no auto-detect path.

Accepted declarations for the Central Coast MVP include:

- `EPSG:4326` — WGS84 (passthrough)
- `EPSG:7844` — GDA2020
- `EPSG:4283` — GDA94
- `EPSG:28355` / `EPSG:28356` — MGA zones 55 / 56
- Full WKT strings for exotic local projections

Unknown or unparseable declarations are a **refuse**, not a warning.
This is a deliberate trip wire for dataset quality.

### 3. `source_crs` is preserved on every record

The `source_crs` of the ingested dataset is recorded on every resulting
cell-populating record and every entity record. This is not cosmetic:

- It enables future re-projection if the source CRS definition is
  refined (rare but not unheard of — GDA94 → GDA2020 is exactly this).
- It supports export pipelines that need to re-emit data in the source
  CRS for interop.
- It makes CRS-related corrections auditable — a systematic bias in a
  source CRS transformation can be scoped and corrected by source,
  not by a cell-by-cell audit.

Column: `source_crs TEXT NOT NULL` on every ingested record. Not
nullable — even passthrough WGS84 ingestion records `EPSG:4326`.

### 4. `crs_transform_epoch` timestamp

Every normalised geometry carries a `crs_transform_epoch TIMESTAMPTZ`
recording the **moment the transformation was applied**, not the
temporal validity of the data (that is ADR-007's domain).

This matters because geodetic transformations are not time-invariant.
ITRF-based datums drift with plate motion; GDA2020 is fixed to the
Australian plate as of a reference epoch and the relationship to WGS84
evolves. Recording the transform epoch means Harmony can later identify
which records were transformed under which version of the transformation
pipeline and re-process them if needed.

Column: `crs_transform_epoch TIMESTAMPTZ NOT NULL` on every ingested
record. Populated by the ingestion pipeline at the moment of transform.

### 5. GDA2020 → WGS84 uses NTv2 grid shift, not a Helmert transformation

This is the operational detail that determines correctness.

**Decision:** GDA2020 → WGS84 transformations use the **NTv2 grid shift
file** published by Geoscience Australia, not a 7-parameter Helmert
transformation.

The Helmert transformation is a linear approximation — it carries a
residual error of up to ~0.2 m across Australia that varies by location.
The NTv2 grid file applies a location-specific correction derived from a
dense network of control points; residual error at the cell centroid
scale is sub-centimetre.

**Operationally:**

- The `proj` library (PROJ 9+) is used for all transformations.
- The NTv2 grid file (`GDA94_GDA2020_conformal.gsb` or the vendor's
  current equivalent) is packaged with the ingestion container image —
  it is not fetched at runtime. Fetching grid files over the network at
  ingestion time is a reliability and tamper vector. The file is
  checksummed and recorded in the ingestion manifest registry.
- For source CRSes where a grid shift is unavailable (rare — some local
  legacy projections), Helmert is the acceptable fallback and the
  `transformation_method` column records this.

### 6. Columns added to every ingested record

| Column | Type | Null? | Purpose |
|---|---|---|---|
| `source_crs` | TEXT | NOT NULL | EPSG code or full WKT, as declared in the dataset manifest |
| `crs_transform_epoch` | TIMESTAMPTZ | NOT NULL | When the transform was applied |
| `transformation_method` | TEXT | NOT NULL | `ntv2_grid`, `helmert_7param`, `passthrough`, `wkt_custom` |
| `transformation_grid_id` | TEXT | NULL | SHA-256 of the NTv2 grid file (when used), else null |

---

## Consequences

**Positive:**

- Cell key determinism holds across all ingestion paths because every
  coordinate is WGS84 before it touches `derive_cell_key`.
- Reprocessing is tractable: records carry enough metadata to be
  re-transformed if the transformation pipeline is updated.
- The refuse-on-missing-CRS policy catches low-quality datasets at the
  gate, before they corrupt the substrate.

**Negative:**

- The NTv2 grid file is a ~3 MB binary dependency carried in the
  ingestion container. Updates follow Geoscience Australia's release
  cadence.
- Datasets with no declared CRS — common in small-council exports —
  require manual CRS assertion by an operator before ingestion. This
  is a human cost but a safety feature.

**Neutral:**

- This ADR covers transformation to WGS84. Harmony does not emit in
  arbitrary CRSes today. A future export interface (post-MVP) will re-
  project from WGS84 on demand; the `source_crs` field preserves the
  option to re-emit in the original projection for interop.

---

## Alternatives Considered

**Alt 1: Store geometries in their native CRS; transform on read.**
Rejected. Cell key derivation is the core of the substrate and must be
deterministic. Running transformation on the read path would mean a
cell's derived key could change as the transformation library evolves —
violating the substrate's foundational guarantee.

**Alt 2: Auto-detect CRS when not declared.** Rejected. CRS detection
from coordinate ranges is unreliable and probabilistic. A dataset that
auto-detects as GDA94 when it is actually GDA2020 is silently wrong by
1–2 metres — below human review threshold and disastrous for a parcel-
scale substrate. Refuse-by-default is the correct posture.

**Alt 3: Helmert transformation everywhere — uniform pipeline.**
Rejected. The 0.2 m residual is below the r10 cell edge length but
well above the r12 edge length. Building Harmony on a transformation
with known systematic error makes no sense when a grid-shift file that
eliminates it is freely available and a 3 MB dependency.

---

## Implementation Constraints

1. Ingestion refuses datasets without a declared `source_crs`. Manifest
   validator must enforce this in M4.
2. NTv2 grid file is bundled with the ingestion image. CI checks the
   file SHA-256 against the expected value; mismatch fails the build.
3. `transformation_method = 'passthrough'` is only valid when
   `source_crs = 'EPSG:4326'`. Enforced as a CHECK constraint.
4. `crs_transform_epoch` is set at transform time, never backdated.
5. Any transformation error (out-of-bounds coordinate, invalid grid
   cell, etc.) refuses the record and routes it to the quarantine
   partition (ADR-021).

---

*ADR-020 — Accepted — 2026-04-29*
