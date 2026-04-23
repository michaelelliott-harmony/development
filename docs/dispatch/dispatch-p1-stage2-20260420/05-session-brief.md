# 05 — Session Brief
## Pillar 1 Stage 2: Volumetric Cell Extension
## Task ID: p1-stage2-20260420
## Issued by: Dr. Mara Voss, Principal Architect

---

## What Has Been Built

Pillar 1 Stage 1 is complete. The Harmony Cell System currently models
the Earth's surface as a 2D tessellation — gnomonic cube projection,
12-level hierarchy, surface cells only. Every cell has a canonical ID,
a deterministic cell key, and precomputed lateral adjacency.

Current cell key format:
  hsam:r{resolution}:{region}:{16-char-base32-hash}

All cells are surface cells. No altitude fields exist. Adjacency is
lateral only. Schema version: v0.1.3.

The source tree is at:
  04_pillars/pillar-1-spatial-substrate/harmony/

---

## What This Session Must Deliver

Extend the Harmony Cell System to support 3D volumetric cells.

By the end of this session:
- Schema supports altitude fields (null for surface, populated for
  volumetric)
- Surface cells can be vertically subdivided into volumetric children
- Volumetric cells have distinct cell key format with altitude suffix
- Adjacency extends to include up/down neighbours for volumetric cells
- Migration v0.1.3 to v0.2.0 produced (not executed)
- Full Stage 1 test suite continues to pass without modification
- New test suite covers volumetric cell behaviour
- ADR-016 produced before any code is written

---

## Technical Specification

### Schema Changes (v0.1.3 → v0.2.0)

Add to the cells table. All fields nullable — surface cells carry null:

  altitude_min_m              FLOAT DEFAULT NULL
  altitude_max_m              FLOAT DEFAULT NULL
  vertical_subdivision_level  INTEGER DEFAULT NULL
  vertical_parent_cell_id     TEXT DEFAULT NULL
  vertical_child_cell_ids     JSONB DEFAULT NULL
  is_volumetric               BOOLEAN DEFAULT FALSE NOT NULL

is_volumetric is the discriminator. Never null. False for all existing
cells.

Altitude validation rules:
- altitude_min_m must be less than altitude_max_m when both present
- Minimum band thickness: 0.5m (reject thinner)
- Below -11,000m: reject as out_of_range
- Above 1,000m: accept but flag aviation_domain: true
- Surface cell: both altitude fields must be null
- Volumetric cell: both altitude fields must be populated

### Volumetric Cell Key Format

Surface (UNCHANGED):
  hsam:r{resolution}:{region}:{16-char-hash}

Volumetric (Stage 2 addition):
  hsam:r{resolution}:{region}:{16-char-hash}:v{alt_min}-{alt_max}

alt_min and alt_max in metres, one decimal place, standard minus prefix
for negatives.

Examples:
  hsam:r08:cc:3J7KPQM4NV2X9F5R:v0.0-3.5      ground floor
  hsam:r08:cc:3J7KPQM4NV2X9F5R:v3.5-7.0      first floor
  hsam:r08:cc:3J7KPQM4NV2X9F5R:v-45.0-0.0    underwater
  hsam:r08:cc:3J7KPQM4NV2X9F5R:v30.0-100.0   UAV corridor

Key determinism rule: same (surface_cell_key, alt_min, alt_max) always
produces same volumetric key.

Forward-compatibility: reserve @ separator for temporal suffix.
Do not implement — reserve only. Confirm in output report.

### Vertical Adjacency

Volumetric cells have:
- 4 lateral edge-neighbours (same altitude band, existing boundary
  transition table)
- 1 vertical up-neighbour (cell in same column where alt_min equals
  this cell's alt_max)
- 1 vertical down-neighbour (cell in same column where alt_max equals
  this cell's alt_min)

Null vertical neighbour = adjacent band not yet registered. Not an error.

Store in new field vertical_adjacent_cell_keys (JSONB):
  { "up": "cell_key_or_null", "down": "cell_key_or_null" }

Surface cells do not carry this field.

### API Extensions Required

POST /cells/register
  Accept optional altitude fields. Validate and register as volumetric
  if present. Unchanged behaviour for surface cells.

GET /cells/{key}
  Return full record including altitude and vertical adjacency.

GET /cells/{key}/adjacency
  For volumetric cells, extend response:
  {
    "lateral": [...existing...],
    "vertical": { "up": "key_or_null", "down": "key_or_null" }
  }
  Surface cell responses: unchanged, no vertical key added.

### Required Tests

File: tests/test_p1_stage2_acceptance.py

Registration tests:
- Surface cell registers with null altitude (backward compat)
- Volumetric cell registers with valid altitude range
- Rejects altitude_min >= altitude_max
- Rejects band thickness < 0.5m
- Rejects altitude below -11,000m
- Volumetric cell key format is correct
- Same altitude inputs always produce same key (determinism × 3)

Adjacency tests:
- Surface cell adjacency returns lateral only (no vertical key)
- Volumetric cell adjacency returns lateral + vertical structure
- Vertical up-neighbour null when adjacent band not registered
- Vertical down-neighbour resolves correctly when adjacent band exists
- Cross-cube-face lateral adjacency works for volumetric cells

Integration tests:
- Register surface cell, subdivide into 3 floor bands, verify
  parent-child relationships
- Full vertical column: underwater + surface + UAV corridor bands
- Confirm all Stage 1 acceptance criteria still pass

Coverage target: 90% on the new volumetric module.

---

## Acceptance Criteria

All binary. Session is not complete until all pass.

AC1  All Stage 1 tests pass without modification
AC2  Surface cells register and resolve identically to Stage 1
AC3  Volumetric cell registers with correct altitude fields
AC4  Volumetric cell key format matches pattern
AC5  Cell key derivation is deterministic (same inputs × 3 = identical)
AC6  Altitude validation rejects invalid ranges
AC7  Vertical adjacency resolves correctly
AC8  Surface cell adjacency endpoint unchanged (no vertical key)
AC9  Migration file has up and down functions
AC10 v0.2.0 schema forward-compatible with temporal suffix confirmed
     in output report

---

## Constraints

Must not:
- Execute the migration — produce it only. Requires Mikey's approval.
- Add temporal fields — Pillar 4
- Add confidence fields — Pillar 4
- Modify the lateral adjacency algorithm — extend, do not replace
- Change the surface cell key format in any way
- Add endpoints beyond those listed above

ADR-016 must be produced before any code is written.

---

## What This Unlocks

Pillar 2 can ingest vertical data — building heights, floor counts,
bathymetric depths — rather than discarding it at CRS normalisation.

Pillar 3 has a 3D LOD tree to traverse. The Earth-to-floor continuous
zoom becomes architecturally possible.

North Star II extends to GPS-denied environments in all three
dimensions. Drones, ground robots, submarines — same substrate.

The dimensional moat deepens. 3D delivered before 4D design begins.
