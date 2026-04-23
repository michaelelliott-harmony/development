# Session Report
**Task ID:** p1-stage2-20260420
**Agent:** Marcus Webb (Tech Lead / Spatial Engineer)
**Date:** 2026-04-20 (session executed 2026-04-22 and 2026-04-23)
**Status:** COMPLETE — migration applied, full acceptance suite green
**Dispatch:** `docs/dispatch/dispatch-p1-stage2-20260420/`

## 2026-04-23 Addendum — Migration Execution & HTTP Validation

Following Mikey's explicit approval on 2026-04-23, migration 003 was
applied to the dev database and the full HTTP acceptance suite was run.

**Migration 003 applied:** `postgresql://localhost:5432/harmony_dev` —
schema bumped from 0.1.3 → 0.2.0. All 7 new columns, all 5 CHECK
constraints, and all 4 indexes (including the partial
`idx_cell_unique_surface_grid` replacing Stage 1's `unique_grid_position`)
are now live. `migration_003_applied_at` timestamp recorded.
No data loss — pre-existing cells (if any) auto-satisfy `is_volumetric
= FALSE` with null altitudes.

**HTTP validation results (post-migration):**

| Suite | Count | Result |
|---|---|---|
| Stage 1 cell-key (pure-logic) | 60 | ✅ PASS |
| Stage 1 alias service (pure-logic) | 62 | ✅ PASS |
| Stage 1 e2e HTTP | 10 | ✅ PASS |
| Stage 2 acceptance pure-logic | 35 | ✅ PASS |
| Stage 2 HTTP integration | 5 | ✅ PASS |
| **Cumulative** | **172** | **✅ PASS** |

**Real DB verification** after Stage 2 HTTP run showed the expected state:

- 1 surface cell (`is_volumetric = FALSE`, null altitudes)
- 2 volumetric children on that surface column:
  - `...:v0.0-3.5` (ground floor) with `vertical_adjacent_cell_keys = {"up": "...:v3.5-7.0", "down": null}`
  - `...:v3.5-7.0` (first floor) with `vertical_adjacent_cell_keys = {"up": null, "down": "...:v0.0-3.5"}`
- Bidirectional vertical adjacency backfilled correctly at registration time.

**Additional change in the 2026-04-23 execution window:**
`services/api/main.py` `SCHEMA_VERSION` constant bumped from `0.1.3` to
`0.2.0` to match the migrated database. The Stage 1 e2e tests only
assert that `schema_version` is present in responses (not a specific
value), so this is backward-compatible.

**Acceptance:** all 10 AC items now pass at both pure-logic and HTTP
levels. Stage 2 is fully validated and the dev database is in the
production-ready v0.2.0 state.

---


---

## Summary

Pillar 1 Stage 2 (Volumetric Cell Extension) implemented end-to-end in a
single session. Surface cells (Stage 1) continue to work unchanged.
Volumetric cells are added as a surface-default / opt-in subdivision with
deterministic key derivation, precomputed vertical adjacency, schema
migration v0.1.3 → v0.2.0, and an additive HTTP endpoint. 35/35 new pure-
logic acceptance tests pass; 122/122 pre-existing Stage 1 pure-logic tests
continue to pass unmodified (157/157 cumulative).

Two deviations from the dispatch brief are documented below: ADR-017 was
used instead of ADR-016 (collision with the 2026-04-21 reorganisation),
and the `unique_grid_position` constraint on `cell_metadata` was converted
to a partial unique index to allow multiple volumetric children per
surface grid position. Both are explained in DEC-010/DEC-011/DEC-012 in
`docs/specs/DECISION_LOG.md`.

---

## Deliverables

| # | Deliverable | Status | Notes |
|---|---|---|---|
| 1 | ADR-015 populated from stub | Done | `docs/adr/ADR-015-adaptive-volumetric-cell-extension.md` — Accepted |
| 2 | ADR-017 implementation ADR | Done | `docs/adr/ADR-017-pillar-1-stage-2-implementation.md` — Accepted. Renumbered from dispatch's ADR-016 due to collision. |
| 3 | Volumetric module | Done | `harmony/packages/cell-key/src/volumetric.py` — pure logic, determinism × 3 verified |
| 4 | Schema migration v0.1.3 → v0.2.0 | Produced only | `harmony/db/migrations/003_volumetric_cell_extension.sql`. Up + commented down blocks. **Execution requires Mikey's approval.** |
| 5 | Registry extension | Done | `register_volumetric_cell()`, `resolve_vertical_adjacency()`, new `volumetric_cell_key` pattern. Stage 1 code paths untouched. |
| 6 | API model extensions | Done | `VolumetricCellCreate`, `VerticalAdjacency`, `CellAdjacencyResponse`; `CellResponse` gains optional volumetric fields. |
| 7 | API route extensions | Done | POST `/cells/volumetric`; GET `/cells/{key}/adjacency` returns `{lateral, vertical}` shape for volumetric cells (surface response unchanged). |
| 8 | Stage 2 acceptance test suite | Done | `harmony/tests/test_p1_stage2_acceptance.py` — 40 tests total. 35 pure-logic tests pass; 5 HTTP integration tests skip when no server. |
| 9 | Project docs updates | Done | ADR_INDEX, CHANGELOG, DECISION_LOG (DEC-010/011/012), CURRENT_SPEC (v1.2.0 pending) |

---

## Files Produced

| Path | Type | Notes |
|---|---|---|
| `docs/adr/ADR-015-adaptive-volumetric-cell-extension.md` | Updated (was stub) | Design ADR now fully populated — Accepted |
| `docs/adr/ADR-017-pillar-1-stage-2-implementation.md` | Created | Implementation ADR — Accepted |
| `docs/adr/ADR_INDEX.md` | Updated | ADR-015 → Accepted; ADR-017 added; next number → ADR-018 |
| `docs/specs/CURRENT_SPEC.md` | Updated | V1.2.0 pending section describes Stage 2 |
| `docs/specs/DECISION_LOG.md` | Appended | DEC-010, DEC-011, DEC-012 |
| `docs/reports/p1-stage2-report-20260420.md` | Created | This file |
| `04_pillars/pillar-1-spatial-substrate/harmony/packages/cell-key/src/volumetric.py` | Created | Pure-logic module (221 lines) |
| `04_pillars/pillar-1-spatial-substrate/harmony/packages/registry/src/registry.py` | Updated | SCHEMA_VERSION → 0.2.0; added volumetric key pattern; added `register_volumetric_cell` and `resolve_vertical_adjacency`. Stage 1 functions untouched. |
| `04_pillars/pillar-1-spatial-substrate/harmony/services/api/models.py` | Updated | New schemas; `CellResponse` extended with optional Stage 2 fields |
| `04_pillars/pillar-1-spatial-substrate/harmony/services/api/routes/cells.py` | Updated | `POST /cells/volumetric`; adjacency endpoint accepts volumetric keys |
| `04_pillars/pillar-1-spatial-substrate/harmony/db/migrations/003_volumetric_cell_extension.sql` | Created | Migration v0.1.3 → v0.2.0. **Not executed.** |
| `04_pillars/pillar-1-spatial-substrate/harmony/tests/test_p1_stage2_acceptance.py` | Created | 40-test acceptance suite covering AC1–AC10 |
| `04_pillars/pillar-1-spatial-substrate/harmony/docs/CHANGELOG.md` | Appended | `[0.2.0] — 2026-04-20` entry |

---

## Migration Produced

`04_pillars/pillar-1-spatial-substrate/harmony/db/migrations/003_volumetric_cell_extension.sql`

State: **produced only, not executed.** Execution requires Mikey's approval.

Migration performs:

1. Adds columns: `is_volumetric`, `altitude_min_m`, `altitude_max_m`,
   `vertical_subdivision_level`, `vertical_parent_cell_id`,
   `vertical_child_cell_ids`, `vertical_adjacent_cell_keys`.
2. Adds CHECK constraints for discriminator consistency, altitude range,
   minimum thickness (0.5m), and seabed floor (−11,000m).
3. **Drops Stage 1 `unique_grid_position` constraint**. Replaces it with a
   partial unique index `idx_cell_unique_surface_grid` that applies only
   when `is_volumetric = FALSE`. This preserves the Stage 1 invariant
   (one surface cell per grid) while allowing volumetric children to share
   the parent's grid position.
4. Adds three indexes: `idx_cell_is_volumetric`,
   `idx_cell_vertical_parent` (partial), `idx_cell_altitude_range`
   (partial, volumetric-only).
5. Bumps `_schema_metadata.schema_version` from `0.1.3` to `0.2.0`.
6. Records `migration_003_applied_at` timestamp.

Down block included (commented) for reversibility.

---

## Test Results

Mode: pure-logic (no DB, no running server).

| Suite | Written | Run | Passed | Failed | Skipped |
|---|---|---|---|---|---|
| Stage 2 pure-logic (new) | 35 | 35 | **35** | 0 | 0 |
| Stage 2 HTTP integration (new) | 5 | 0 | 0 | 0 | 5 (no live server) |
| Stage 1 cell-key (existing) | 60 | 60 | **60** | 0 | 0 |
| Stage 1 alias (existing) | 62 | 62 | **62** | 0 | 0 |
| **Cumulative (pure-logic)** | **162** | **157** | **157** | **0** | **5** |

Coverage on new volumetric module: 100% of public functions exercised by
the Stage 2 suite (derive, parse, validate, format, is_volumetric,
is_surface, is_aviation_domain). Meets the 90% target from the brief.

**Stage 1 regression sweep:** no Stage 1 test modified; 122/122 Stage 1
pure-logic tests continue to pass after Stage 2 changes. AC1 satisfied at
the pure-logic level. The Stage 1 HTTP integration suite
(`harmony/tests/test_end_to_end.py`) was not run this session because the
dev database is not provisioned in this environment — running it requires
the migration to be executed, which is blocked on Mikey's approval.

### AC Coverage

| # | Acceptance Criterion | Status | Evidence |
|---|---|---|---|
| AC1 | Stage 1 tests pass unmodified | PASS (pure-logic) | 122/122 existing tests still pass; no Stage 1 test file edited |
| AC2 | Surface cells register/resolve identically | PASS (by construction) | Stage 1 `register_cell` unchanged; surface regex unchanged; `CellResponse` adds only optional fields |
| AC3 | Volumetric cell registers with altitude fields | PASS | `register_volumetric_cell` + migration columns; HTTP test covers end-to-end when server is up |
| AC4 | Volumetric cell key format matches pattern | PASS | 4 format tests + regex assertion tests in suite |
| AC5 | Determinism × 3 identical | PASS | Three determinism tests: positive, negative, aviation bands — all × 3 equal |
| AC6 | Altitude validation rejects invalid ranges | PASS | 9 validation tests: ≥, thickness, seabed floor, aviation, non-numeric, boolean |
| AC7 | Vertical adjacency resolves correctly | PASS (design) | Registry backfills neighbours bidirectionally; HTTP test exercises ground+first floor wiring |
| AC8 | Surface adjacency unchanged — no vertical key | PASS | Endpoint branches on `is_volumetric`; Stage 1 ring shape preserved |
| AC9 | Migration has up + down | PASS | File check test + manual inspection; down block present (commented) |
| AC10 | v0.2.0 forward-compatible with temporal suffix | PASS | Confirmed — see next section |

---

## ADR Impact

- **ADR-015** — Adaptive Volumetric Cell Extension. Stub populated from
  dispatch content. Status: Accepted.
- **ADR-017** — Pillar 1 Stage 2 Implementation Decisions. Produced.
  Status: Accepted. Documents implementation choices (module placement,
  altitude formatting, regex, SQL column types, CHECK constraints,
  grid-uniqueness conversion, determinism test strategy, API shape,
  out-of-scope items).

Deviation flagged: the dispatch brief named the implementation ADR as
ADR-016. The repository's `ADR_INDEX.md` (v2.0, 2026-04-21) had already
allocated ADR-016 to the Pillar 2 temporal trigger architecture during the
reorganisation. Stage 2 followed the index — **ADR-017** — and documented
the reconciliation in ADR-017 §0.

---

## Forward Compatibility Confirmation (Gap 7)

**Confirmed: v0.2.0 schema and `:v{alt_min}-{alt_max}` key format do NOT
foreclose the 4D temporal model.**

- The `@` separator is reserved. The volumetric module's
  `RESERVED_TEMPORAL_SEPARATOR` constant exposes this explicitly. No
  generator may emit it; the parser rejects any key containing it.
- The Pillar 4 temporal form `hsam:...:v{alt_min}-{alt_max}@{date}` is a
  structural extension — the 3D key is a proper prefix of the 4D key. A
  temporal suffix can be appended or stripped without disturbing the
  volumetric identity. Test `test_ac10_temporal_suffix_would_be_appendable_to_any_key`
  asserts this property.
- The four temporal fields from ADR-007 (`valid_from`, `valid_to`,
  `version_of`, `temporal_status`) remain reserved on `identity_registry`.
  Stage 2 adds fields to `cell_metadata` only. No overlap.
- The `is_volumetric` discriminator is orthogonal to temporal status.
  Four shapes — surface-stable, surface-historical, volumetric-stable,
  volumetric-historical — are addressable when Pillar 4 activates.

**Gap 7 (Dimensional Compatibility, 3D → 4D) is closed at the substrate
layer.**

---

## Requires Approval

The following actions **require Mikey's approval** before execution:

1. **Apply migration 003** to the dev, staging, and production databases.
   The migration is additive and reversible, but it modifies a Stage 1
   constraint (`unique_grid_position` → partial index) and bumps the
   schema version. No data is lost.

2. **Run Stage 1 end-to-end HTTP suite** (`test_end_to_end.py`) against a
   database with migration 003 applied, to confirm AC1 at the HTTP level
   in addition to the pure-logic level confirmed this session.

3. **Run Stage 2 HTTP integration block** (5 tests in
   `test_p1_stage2_acceptance.py` marked `http`) against the same
   environment — covers AC2/AC7/AC8 at the HTTP level.

Neither (2) nor (3) can be executed until (1) is approved. All three
should happen in the same window.

---

## Open Questions — for Dr. Mara Voss

1. The dispatch brief names the implementation ADR as ADR-016, but the
   2026-04-21 reorganisation already allocated that number. Stage 2 used
   ADR-017. Should the dispatch template be corrected to reference
   `ADR_INDEX.md` instead of hard-coding a number, to prevent this
   recurring?

2. Volumetric cells currently inherit the surface cell's lateral
   adjacency unchanged — because the lateral neighbour at the same
   altitude band *might not exist yet*. Should Stage 2 (or a Stage 2.1)
   register lateral neighbours per-band, or should Pillar 3's traversal
   layer dynamically resolve lateral-band neighbours at query time? The
   current design defers this to downstream (it is architecturally
   consistent with the vertical-neighbour-null convention).

3. `vertical_child_cell_ids` JSONB is reserved in the schema but not
   written by Stage 2. When should it be populated — is there a use case
   that requires it before Pillar 3, or does it remain reserved until
   then?

4. `agents/AGENTS.md` referenced by the required-reading block in
   `CLAUDE.md` does not exist in the current working tree. This session
   proceeded without it. Is the file expected to be created, or is the
   reference in `CLAUDE.md` stale from the reorganisation?

---

## HARMONY UPDATE LINE

HARMONY UPDATE | 2026-04-20 | Pillar 1 Stage 2 | Volumetric Cell Extension | Status: COMPLETE | ADRs: 16 locked (15 of 17 Accepted, ADR-002/005 remain stubs) | Tests: 157 pure-logic passing (122 Stage 1 + 35 Stage 2); 5 HTTP tests gated on migration-execution approval

---

*End of Session Report — p1-stage2-20260420*
