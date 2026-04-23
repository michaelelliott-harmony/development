# 03 — Pillar State
## Current Build State | April 2026

---

## Pillar 1 — Spatial Substrate

### Stage 1: COMPLETE
- 8/8 acceptance criteria pass
- 157 tests across four suites
- 14 ADRs locked (ADR-001 through ADR-015)
- 12 HTTP endpoints with OpenAPI documentation
- Schema v0.1.3 locked
- Source tree: 04_pillars/pillar-1-spatial-substrate/harmony/

### Stage 2: YOU ARE BUILDING THIS
ADR-015 accepted. Deliverables:
- altitude_min_m, altitude_max_m fields
- vertical_subdivision_level, vertical_parent_cell_id,
  vertical_child_cell_ids fields
- Volumetric cell key format with altitude suffix
- Surface cell keys: unchanged (backward compatible)
- Vertical adjacency: up/down neighbours
- Schema migration: v0.1.3 to v0.2.0
- New test suite: test_p1_stage2_acceptance.py

**Forward compatibility constraint (Gap 7):**
Stage 2 must confirm that the v0.2.0 schema and volumetric cell key
format do not foreclose the 4D temporal model. Reserve the @ separator
for temporal suffix. Confirm in your output report.

---

## Pillar 2 — Data Ingestion Pipeline
Status: Active — build commencing in parallel.

---

## Gap Register (relevant to Stage 2)

| Gap | Status |
|---|---|
| Gap 7 — Dimensional Compatibility | Open — YOU must close it for 3D→4D |
| Gap 1 — Rendering Philosophy | Open — Pillar 3 |
| Gap 2 — Machine Query Latency | Open — pre-Pillar 4 |

---

## Next Available ADR: ADR-016

ADR-016 is yours to produce. It documents Stage 2 implementation
decisions before any code is written.
