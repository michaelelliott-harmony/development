# ADR-017 — Pillar 1 Stage 2 Implementation Decisions

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-20 |
| **Pillar** | Pillar 1 — Spatial Substrate, Stage 2 |
| **Author** | Marcus Webb, Tech Lead (Spatial Engineer) |
| **Task ID** | p1-stage2-20260420 |
| **Covers** | ADR-015 implementation decisions not specified by the design ADR |
| **Supersedes** | None |
| **Related ADRs** | ADR-015 (design), ADR-003 (cell key derivation), ADR-005 (adjacency), ADR-013 (API layer) |

---

## 0. Number Reconciliation

The session brief (`docs/dispatch/dispatch-p1-stage2-20260420/04-adr-summary.md`)
names the implementation ADR as `ADR-016`. The repository's
`docs/adr/ADR_INDEX.md` (v2.0, 2026-04-21) has already allocated ADR-016 to
"Temporal Trigger Architecture — Permit Feed Integration" (Pillar 2, Draft)
and lists ADR-017 as the next available number.

Following the ADR Index — the governing sequence — this implementation ADR
is numbered **ADR-017**. The dispatch's reference to ADR-016 is treated as
a stale pointer (dispatch authored pre-reorganisation). The session report
flags this explicitly.

---

## 1. Context

ADR-015 is the design ADR. It specifies *what* Stage 2 builds:
volumetric cell key format, altitude fields, vertical adjacency, schema
migration v0.1.3 → v0.2.0.

ADR-017 documents the *how* — the implementation choices that are not
pre-specified by ADR-015, the session brief, or existing ADRs.

---

## 2. Decision

### 2.1 Volumetric Module Placement

New module: `harmony/packages/cell-key/src/volumetric.py`.

Rationale: the cell-key package already owns the deterministic key derivation
contract (ADR-003). Volumetric key format is a syntactic extension of the
surface key format — it belongs with its sibling. The module imports nothing
from the registry or API layers; it is pure computation.

Functions exposed:

- `derive_volumetric_cell_key(surface_cell_key, alt_min, alt_max) -> str`
- `parse_volumetric_cell_key(cell_key) -> dict`
- `is_volumetric_key(cell_key) -> bool`
- `format_altitude(value_m) -> str`
- `validate_altitude_range(alt_min, alt_max) -> None` (raises ValueError)

### 2.2 Altitude Formatting

Altitude values in the cell key are formatted with exactly **one decimal
place** using Python's standard `f"{value:.1f}"`. Negative values carry the
minus prefix (`-45.0`). Zero is `0.0`, not `-0.0`.

This format is:

- Round-trip stable through the parser for any float with a representable
  tenths value. Inputs are quantised to the nearest 0.1m on ingest.
- Lexically sortable at one decimal precision, which is good enough for
  debugging and unnecessary for correctness (the database index carries
  the numeric value).
- Free of scientific notation, which would break the regex.

Altitudes outside the legal range are rejected before formatting.

### 2.3 Altitude Regex

The altitude fragment in the cell key matches the regex:

    -?[0-9]+\.[0-9]

(anchored as `v` + alt_min + `-` + alt_max at the appropriate place). The
parser uses a non-greedy split that first splits on the trailing `:v`, then
the first unescaped `-` that follows a digit and precedes a digit. Because
the first altitude may be negative, the parser consumes the optional
leading minus separately from the range dash.

The full volumetric key regex is:

    ^hsam:r[0-9]{2}:[a-z]{2,8}:[0-9a-hjkmnp-tv-z]{16}:v-?[0-9]+\.[0-9]--?[0-9]+\.[0-9]$

(the double dash `--` is "range separator, then optional minus sign for
the upper bound" — it is legal.)

### 2.4 SQL Column Types

| Field | PostgreSQL type | Rationale |
|---|---|---|
| `altitude_min_m` | DOUBLE PRECISION | Matches existing `centroid_ecef_*` type. IEEE 754 is overkill for 0.1m precision but consistent with the rest of the schema. |
| `altitude_max_m` | DOUBLE PRECISION | As above. |
| `vertical_subdivision_level` | INTEGER | Small non-negative counter. |
| `vertical_parent_cell_id` | TEXT | Matches `parent_cell_id` type exactly. |
| `vertical_child_cell_ids` | JSONB | Array of canonical IDs; JSONB for queryable indexing. |
| `is_volumetric` | BOOLEAN NOT NULL DEFAULT FALSE | Discriminator. Never null. |
| `vertical_adjacent_cell_keys` | JSONB | Two-key dict. JSONB, not a dedicated table, because entries are 1-to-1 with the cell row and always retrieved together. |

No PostGIS-specific types are required for Stage 2. The altitude
representation is a scalar — geometry remains 2D at the cell level.

### 2.5 CHECK Constraints

The migration adds the following constraints, all tolerant of surface rows:

- `CHECK (NOT is_volumetric OR (altitude_min_m IS NOT NULL AND altitude_max_m IS NOT NULL))`
- `CHECK (altitude_min_m IS NULL OR altitude_min_m >= -11000.0)`
- `CHECK (altitude_min_m IS NULL OR altitude_max_m IS NULL OR altitude_max_m - altitude_min_m >= 0.5)`
- `CHECK (is_volumetric OR (altitude_min_m IS NULL AND altitude_max_m IS NULL))`

These mirror the Python validation in `volumetric.validate_altitude_range`
but are enforced at the storage layer as defence in depth.

### 2.5a Grid Uniqueness — Partial Index

Stage 1 enforces `UNIQUE (cube_face, resolution_level, face_grid_u,
face_grid_v)` on `cell_metadata` — one surface cell per grid position.
Stage 2 needs to register multiple volumetric children that share the
parent's grid position.

Migration 003 replaces the Stage 1 constraint with a **partial unique
index** that applies only to surface rows:

    CREATE UNIQUE INDEX idx_cell_unique_surface_grid
        ON cell_metadata (cube_face, resolution_level, face_grid_u, face_grid_v)
        WHERE is_volumetric = FALSE;

This preserves the Stage 1 invariant ("one surface cell per grid position")
while permitting any number of volumetric children to share a grid address.
The Stage 2 volumetric cell insert reuses the parent surface cell's grid
position verbatim — no synthetic offsets, no parallel registry tables.

### 2.6 Determinism Test Strategy

The determinism requirement (same inputs → same key, forever) is tested by
calling `derive_volumetric_cell_key` three times with identical inputs and
asserting string equality. Three calls catches non-determinism from
randomness, iteration order, or floating-point reformatting. More than three
is defensive without new signal.

### 2.7 Cell Key Regex — Registry Update

The existing `PATTERNS["cell_key"]` in `registry.py` matches only surface
keys. A new `PATTERNS["volumetric_cell_key"]` is added. The existing pattern
is **not** modified — that would cause Stage 1 resolution paths to accept
volumetric keys as surface keys, a silent bug. The registry gains an
explicit dispatcher: parse the key, decide surface vs volumetric, route to
the correct handler.

### 2.8 API Request Shape

`POST /cells` gains three optional fields on `CellCreate`:

- `altitude_min_m: Optional[float]`
- `altitude_max_m: Optional[float]`
- `vertical_parent_cell_id: Optional[str]` (the canonical ID of the surface
  cell being subdivided — required when altitude fields are present)

All three must be absent (surface) or all three present (volumetric). The
validator rejects mixed forms with HTTP 400 `invalid_altitude_range`.

The volumetric cell key is **derived server-side** from the surface key
implied by `vertical_parent_cell_id` + altitude range. Clients that wish to
assert a specific `cell_key` may still pass one; the server verifies it
matches the derivation result.

### 2.9 What Stage 2 Does Not Implement

Per the scope boundary in the dispatch:

- No temporal `@{date}` suffix. Only the `@` separator is reserved.
- No confidence scoring.
- No spatial type rules (Pillar 5).
- No modification of the lateral adjacency algorithm.
- No new HTTP endpoints beyond the three extensions listed.
- No execution of the migration. Execution requires Mikey's approval.

---

## 3. Consequences

- Two shapes of cell now flow through the registry and the API: surface
  (Stage 1) and volumetric (Stage 2). The discriminator (`is_volumetric`)
  and the explicit cell-key regex split keep them unambiguous.
- The volumetric module adds ~200 lines of pure-logic Python. It can be
  exercised without a database.
- The migration file adds columns and CHECK constraints only. No data
  transformation — existing rows are compatible by construction.
- Forward compatibility with Pillar 4 temporal activation is preserved by
  the reserved `@` separator and untouched temporal fields.

---

## 4. Forward Compatibility Confirmation (Gap 7)

Confirmed by construction. See ADR-015 §6 and the session report.

---

*ADR-017 — Accepted — 2026-04-20*
