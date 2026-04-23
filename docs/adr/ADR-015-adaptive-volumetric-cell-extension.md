# ADR-015 — Adaptive Volumetric Cell Extension

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-20 |
| **Pillar** | Pillar 1 — Spatial Substrate |
| **Author** | Dr. Mara Voss, Principal Architect |
| **Populated from dispatch** | `docs/dispatch/dispatch-p1-stage2-20260420/` — 2026-04-22 |
| **Supersedes stub** | Yes — replaces 2026-04-21 stub |
| **Related ADRs** | ADR-003 (Cell Key Derivation), ADR-005 (Cell Adjacency), ADR-007 (Temporal Versioning), ADR-010 (Spatial Geometry Schema), ADR-017 (Stage 2 Implementation) |

---

## 1. Context

The Harmony Cell System as shipped in Pillar 1 Stage 1 models the Earth as a
2D gnomonic-cube tessellation: 6 cube faces, 12 resolution levels, deterministic
BLAKE3-derived cell keys, precomputed lateral adjacency. Every cell is a
surface cell — there is no altitude dimension.

V1.1.0 of the master specification introduces the full three-dimensional
addressing requirement: underwater (to -11,000m), surface, buildings (floors),
and aviation corridors (above 1,000m). The substrate must handle all of these
in one coherent cell hierarchy without breaking the Stage 1 contract.

The governing constraint of the dimensional architecture is that each
activated dimension must be forward-compatible with the next. Stage 2 activates
3D; it must not foreclose 4D (temporal versioning — Pillar 4, already reserved
at the schema level by ADR-007).

---

## 2. Decision

### 2.1 Surface-Default, Volumetric-Opt-In

A cell is **surface** by default. Surface cells represent the full vertical
column above their geographic footprint (null altitude). A cell becomes
**volumetric** only when vertical subdivision is explicitly registered —
driven by the presence of known structure (buildings, bathymetric layers,
airspace corridors).

A discriminator `is_volumetric BOOLEAN NOT NULL DEFAULT FALSE` is added to
`cell_metadata`. Existing Stage 1 cells are all surface; the migration sets
this discriminator to `false` for every existing row.

### 2.2 Altitude Field Set

Six nullable fields are added to `cell_metadata`:

| Field | Type | Purpose |
|---|---|---|
| `altitude_min_m` | DOUBLE PRECISION | Lower bound of band (metres, WGS84 ellipsoid reference) |
| `altitude_max_m` | DOUBLE PRECISION | Upper bound of band |
| `vertical_subdivision_level` | INTEGER | Ordinal of this band within its parent surface column |
| `vertical_parent_cell_id` | TEXT | Canonical ID of the surface cell this band belongs to |
| `vertical_child_cell_ids` | JSONB | Array of canonical IDs of further subdivisions (reserved — not written by Stage 2) |
| `vertical_adjacent_cell_keys` | JSONB | `{"up": key-or-null, "down": key-or-null}` |

Rules:

- Surface cell: all six fields NULL.
- Volumetric cell: `altitude_min_m`, `altitude_max_m`, `vertical_subdivision_level`,
  `vertical_parent_cell_id`, `vertical_adjacent_cell_keys` populated.
- `is_volumetric` is **never null** and distinguishes the two shapes.

### 2.3 Volumetric Cell Key Format

Surface cell keys are **unchanged** from Stage 1:

    hsam:r{resolution}:{region}:{16-char-hash}

Volumetric cell keys extend the surface key with an altitude suffix:

    hsam:r{resolution}:{region}:{16-char-hash}:v{alt_min}-{alt_max}

Altitude values are in metres, one decimal place, standard minus prefix for
negatives. Examples:

    hsam:r08:cc:3j7kpqm4nv2x9f5r:v0.0-3.5        # ground floor
    hsam:r08:cc:3j7kpqm4nv2x9f5r:v3.5-7.0        # first floor
    hsam:r08:cc:3j7kpqm4nv2x9f5r:v-45.0-0.0      # underwater
    hsam:r08:cc:3j7kpqm4nv2x9f5r:v30.0-100.0     # UAV corridor

**Determinism rule:** the same (surface_cell_key, alt_min, alt_max) tuple
always produces the same volumetric key. The suffix is a pure function of its
inputs; no randomness, no timestamps.

### 2.4 Reserved Temporal Separator (Forward Compatibility)

The `@` character is **reserved** as the temporal suffix separator. When
Pillar 4 activates temporal versioning, the full key form will be:

    hsam:r{resolution}:{region}:{16-char-hash}:v{alt_min}-{alt_max}@{date}

Stage 2 does **not** implement the temporal suffix. It only reserves the
separator. Parsers must reject `@` in a volumetric suffix; generators must
never emit it. The `v{}` and `@{}` fragments are orthogonal — the @-suffix
can be appended or stripped without disturbing the altitude band identity.
This is what preserves 3D→4D forward compatibility at the key format level.

### 2.5 Altitude Validation Rules

| Rule | Behaviour |
|---|---|
| `altitude_min_m < altitude_max_m` | Required. Reject otherwise. |
| Band thickness `alt_max - alt_min >= 0.5m` | Required. Reject thinner bands. |
| `altitude_min_m >= -11,000m` | Required. Reject as `out_of_range` below this. |
| `altitude_max_m > 1,000m` | Accept. Flag `aviation_domain: true` in response metadata. |
| Surface cell | Both altitude fields must be NULL. |
| Volumetric cell | Both altitude fields must be populated. |

Altitude is in metres relative to the WGS84 ellipsoid. Bathymetric depth
is represented as a negative altitude.

### 2.6 Vertical Adjacency

Volumetric cells carry:

- **4 lateral edge-neighbours** — same altitude band on adjacent surface cells.
  Uses the 24-entry boundary transition table from ADR-005 unchanged.
- **1 vertical up-neighbour** — same surface column, band whose `alt_min`
  equals this cell's `alt_max`.
- **1 vertical down-neighbour** — same surface column, band whose `alt_max`
  equals this cell's `alt_min`.

A null vertical neighbour means the adjacent band is not yet registered. That
is not an error state — it is the expected condition for the top and bottom
bands of any partially-populated vertical stack.

Storage: `vertical_adjacent_cell_keys` JSONB with shape
`{"up": "cell_key_or_null", "down": "cell_key_or_null"}`.

Surface cells do not carry this field. The lateral adjacency field
(`adjacent_cell_keys`) is unchanged for surface cells.

### 2.7 Schema Migration v0.1.3 → v0.2.0

Migration `003_volumetric_cell_extension.sql` adds the altitude field set,
the discriminator, and the vertical adjacency field. It is:

- Additive only. No column drops, no column type changes.
- Idempotent. Uses `IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`.
- Backward compatible. All existing cells automatically satisfy the new
  schema with `is_volumetric = false` and all altitude fields NULL.
- Produced, not executed. Execution requires Mikey's approval per the
  Harmony safety policy.
- Has a matching `down` function that reverses the changes.

### 2.8 API Surface

The Pillar 1 HTTP contract gains three additive extensions — no breaking
changes:

- `POST /cells` accepts optional altitude fields. Present → register as
  volumetric. Absent → surface, unchanged behaviour.
- `GET /resolve/cell-key/{key}` returns the altitude fields and vertical
  adjacency when the key is volumetric; unchanged shape for surface cells.
- `GET /cells/{key}/adjacency` returns `{"lateral": [...], "vertical": {...}}`
  for volumetric cells. Surface cell responses are unchanged (no vertical
  field added).

No new endpoints. The 12-endpoint surface from ADR-013 is preserved.

---

## 3. Consequences

### What This Enables

- **Pillar 2** can ingest vertical data — building heights, floor counts,
  bathymetric depths — instead of discarding it at CRS normalisation.
- **Pillar 3** gains a traversable 3D LOD tree. Earth-to-floor seamless zoom
  becomes architecturally possible (North Star I).
- **North Star II** extends to GPS-denied environments in all three
  dimensions: drones, ground robots, submarines on one substrate.
- The dimensional moat deepens — 3D is delivered before 4D design begins.

### What This Costs

- Cell count for densely populated vertical stacks (e.g. a 50-storey tower)
  grows linearly with subdivision level. Adaptive subdivision (only where
  structure exists) keeps this bounded.
- Integration tests must cover surface-only and volumetric-only paths as
  two shapes of the same endpoint. Mitigated by the discriminator.
- Schema version bump to v0.2.0 is a coordination point across all pillars
  that read the cell schema. Mitigated by the fields being additive and
  null-default for all existing rows.

### What This Does Not Do

- Does not change the surface cell key format in any way.
- Does not populate temporal fields (`valid_from`, `valid_to`,
  `version_of`, `temporal_status`) — still reserved for Pillar 4.
- Does not implement the `@{date}` temporal suffix — only reserves the `@`
  separator.
- Does not add confidence scoring or spatial type rules — those are Pillar 4
  and Pillar 5 respectively.
- Does not modify the lateral adjacency algorithm — vertical adjacency is a
  separate, additive mechanism.

---

## 4. Alternatives Considered

### Alternative A: Embedded Altitude in the 16-Char Hash

Include altitude in the BLAKE3 hash input so the hash itself encodes 3D.

Rejected: breaks backward compatibility — surface cells would need rehashing,
and the 16-char hash is already space-optimised for the 2D tessellation.
Collisions between surface and volumetric cells become possible.

### Alternative B: Full 3D Cube Tessellation

Replace the 2D cube-face grid with a 3D voxel grid from the start.

Rejected: would require rebuilding the entire cell hierarchy, invalidating
all Stage 1 cells, and imposing a uniform vertical resolution that is
wasteful for empty airspace and underwater volumes where structure is sparse.

### Alternative C: Separate Volumetric Registry (Parallel Table)

Put volumetric cells in a new table, leaving `cell_metadata` untouched.

Rejected: introduces two sources of truth for cell identity. Lateral
adjacency queries would have to cross tables. Surface cells and volumetric
cells in the same column share identity semantics — they belong in one
table with a discriminator.

### Alternative D: Altitude-as-Metadata (No Key Change)

Store altitude only in the row, don't extend the key format.

Rejected: violates the deterministic-key principle of ADR-003. Two
volumetric cells in the same surface column would share a cell_key. The
key-is-the-name invariant must hold in 3D as it does in 2D.

---

## 5. Implementation Constraints

1. Stage 1 tests must pass unmodified. Any regression blocks the build.
2. Volumetric cell key derivation must be deterministic × ∞ — same inputs,
   same output, forever.
3. Migration produced only; never executed without Mikey's approval.
4. Parsers must reject any `@` token in a volumetric key. Generators must
   never emit one.
5. Vertical adjacency lookup is database-resolved — not recomputed on the
   fly. The `vertical_adjacent_cell_keys` JSONB is updated on neighbour
   registration.

---

## 6. Forward Compatibility Confirmation

The Stage 2 schema and cell key format **do not foreclose 4D temporal
versioning**:

- The `@` separator is reserved and unused — a temporal suffix can be
  appended to any volumetric key without parser ambiguity.
- The four temporal fields from ADR-007 (`valid_from`, `valid_to`,
  `version_of`, `temporal_status`) remain on `identity_registry` untouched.
  Stage 2 adds to `cell_metadata` only.
- The `is_volumetric` discriminator is orthogonal to temporal status. A cell
  can be surface-stable, surface-historical, volumetric-stable, or
  volumetric-historical — all four shapes are addressable.

Gap 7 (Dimensional Compatibility, 3D → 4D) is closed at the substrate layer
by Stage 2.

---

*ADR-015 — Accepted — 2026-04-20*
