# HARMONY — Pillar 2: Data Ingestion Pipeline
## Project Management Brief | Version 1.0
**Date:** April 19, 2026
**Pillar Status:** Pre-Build
**Priority:** Critical Path
**Estimated Total Sessions:** 8–10
**Estimated Total Tokens:** 1.2M–1.8M
**Estimated Calendar Duration:** 5–6 weeks
**Hard Dependencies:** Pillar 1 — Spatial Substrate (complete)

---

## 1. Pillar Summary for PM Agent

Pillar 2 is the Data Ingestion Pipeline — the system that takes real-world geospatial data (cadastral boundaries, zoning layers, building footprints, road networks) and writes it into the Harmony Cell registry as structured, validated, fidelity-classified entities. It is the first consumer of everything Pillar 1 built and the prerequisite for every downstream pillar. Without it, Harmony is an empty grid. With it, cells contain the physical world.

The pillar has seven milestones across three phases. Milestones 1–4 build the pipeline components independently. Milestone 5 wires them together for the first end-to-end ingestion. Milestone 6 proves multi-dataset coexistence. Milestone 7 (added by Dr. Voss) connects the pipeline to live NSW Planning Portal permit feeds, enabling real-time cell state transitions that keep the map current.

The pillar scores 830/1000 on agent completability (83%). Human involvement is concentrated at dataset sourcing, entity extraction thresholds, domain knowledge for Australian cadastral data, CRS edge case review, and approval of ADR-015 and the temporal field migration.

---

## 2. Build Phases

### Phase 1: Pipeline Foundation
**Objective:** Build and test each pipeline component independently — source adapters, CRS normalisation, geometry validation, dataset manifests, entity extraction with deduplication, and cell assignment.
**Start Condition:** Pillar 1 complete (confirmed). At least one Central Coast dataset sourced and accessible.
**End Condition / Milestone:** All six pipeline components pass independent unit tests. Manifests are written for at least two real datasets.
**Deliverables:**
- Data profiler tool
- Source adapters (GeoJSON, Shapefile, GeoPackage)
- CRS normalisation service with GDA2020 → WGS84 validation
- Geometry validator with quarantine model
- Dataset manifest schema, validator, and example manifests
- Entity extractor with hybrid deduplication engine
- Cell assignment engine with geometry-adaptive resolution selection

**Sessions in this phase:**

| Session | Objective | Estimated Tokens | Estimated Duration | Inputs Required | Output |
|---|---|---|---|---|---|
| Session 01 | Project scaffolding, data profiler, source adapters (M1) | 80k–120k | 2–3 hours | Central Coast test datasets (GeoJSON + Shapefile) | Profiler and adapter modules with tests |
| Session 02 | CRS normalisation service (M2) | 60k–100k | 2–3 hours | GDA2020 test dataset, known reference coordinates | Normalisation module with coordinate validation tests |
| Session 03 | Geometry validator and quarantine model (M3) | 80k–120k | 2–3 hours | Deliberately corrupted test geometries | Validator and quarantine modules with test suite |
| Session 04 | Manifest system, entity extractor, dedup engine (M4) | 100k–150k | 3–4 hours | Real dataset column schemas for attribute mapping | Manifest schema, extractor, dedup engine with tests |
| Session 05 | Cell assignment engine (M4–5 bridge) | 80k–120k | 2–3 hours | Pillar 1 derive.py module, API access | Cell assignment module with multi-cell spanning tests |

---

### Phase 2: End-to-End Integration
**Objective:** Wire all components into a working pipeline, ingest the first complete Central Coast dataset, build the dataset registry, and prove multi-dataset coexistence.
**Start Condition:** All Phase 1 components pass independent tests. At least two Central Coast datasets sourced.
**End Condition / Milestone:** Three datasets (zoning, buildings, roads) ingested into the same cell region. Dataset registry records all runs with full provenance. Re-ingestion produces identical results.
**Deliverables:**
- Pipeline runner (CLI: `harmony-ingest run <manifest>`)
- Dataset registry (SQLite) with provenance tracking
- First complete Central Coast dataset ingested end-to-end
- Three-dataset multi-source ingestion validated
- Ingestion run reports

**Sessions in this phase:**

| Session | Objective | Estimated Tokens | Estimated Duration | Inputs Required | Output |
|---|---|---|---|---|---|
| Session 06 | Pipeline wiring, dataset registry, first end-to-end ingestion (M5) | 120k–180k | 3–5 hours | Pillar 1 API running, Central Coast zoning dataset | Working pipeline, dataset registry, first ingested dataset |
| Session 07 | Multi-dataset ingestion and dedup validation (M6) | 100k–150k | 3–4 hours | Building footprints and road network datasets | Three-dataset ingestion verified, dedup exercised |

---

### Phase 3: Temporal Trigger Layer
**Objective:** Connect the pipeline to the NSW Planning Portal permit feeds. Implement the cell state machine. Activate the bitemporal schema fields. Prove that cell state transitions are driven by real-world permit events with correct temporal semantics.
**Start Condition:** Phase 2 complete (M5 and M6 pass). ADR-015 drafted and accepted by Mikey. NSW Planning Portal API endpoint validated.
**End Condition / Milestone:** All 8 acceptance criteria from Dr. Voss's Milestone 7 specification pass. Temporal fields active. Permit feed connected. Gosford DA fixture resolves correctly.
**Deliverables:**
- ADR-015: Temporal Trigger Architecture (accepted)
- NSW Planning Portal adapter (implementing generic PermitSourceAdapter interface)
- Permit-to-cell resolver (spatial intersection + address fallback)
- Cell state transition service (idempotent, audit-logged)
- Temporal field activation migration (up + down, requires Mikey approval)
- Fidelity reset logic (photorealistic → pending on change_confirmed)
- Full test suite including Gosford DA integration test

**Sessions in this phase:**

| Session | Objective | Estimated Tokens | Estimated Duration | Inputs Required | Output |
|---|---|---|---|---|---|
| Session 08 | ADR-015 drafting | 40k–60k | 1–2 hours | Dr. Voss M7 spec, Pillar 1 ADR-007 | ADR-015 draft flagged for Mikey approval |
| Session 09 | Permit adapter, resolver, state transition service (M7) | 120k–180k | 3–5 hours | Validated NSW Planning Portal API, ADR-015 accepted | Temporal trigger subsystem with test suite |
| Session 10 | Migration, fidelity reset, integration testing, acceptance (M7) | 100k–150k | 3–4 hours | Mikey approval of migration | All 8 AC pass, session report with HARMONY UPDATE |

---

## 3. Sprint Allocation

| Sprint | Phase(s) | Key Activities | Milestone | Dependencies |
|---|---|---|---|---|
| Sprint 1 (Weeks 1–2) | Phase 1 | Sessions 01–03: Adapters, CRS normalisation, geometry validation | M1, M2, M3 | Central Coast datasets sourced |
| Sprint 2 (Weeks 3–4) | Phase 1 → Phase 2 | Sessions 04–06: Manifests, entity extraction, dedup, cell assignment, first end-to-end ingestion | M4, M5 | Pillar 1 API running |
| Sprint 3 (Weeks 5–6) | Phase 2 → Phase 3 | Sessions 07–08: Multi-dataset ingestion, ADR-015 drafting | M6, ADR-015 draft | Three datasets available |
| Sprint 4 (Weeks 7–8) | Phase 3 | Sessions 09–10: Temporal trigger layer build, integration, acceptance | M7 | ADR-015 accepted, NSW API validated, migration approved |

**Note:** Sprint 4 may compress to 1 week if ADR-015 approval and NSW API validation happen promptly. The 5–6 week estimate assumes normal approval cadence.

---

## 4. Dependency Map

### Blocking Dependencies (this pillar cannot start without these)

| Dependency | Type | Owner | Status |
|---|---|---|---|
| Pillar 1 — Spatial Substrate complete | Pillar | Pillar 1 team | **Resolved** — all 6 milestones done, 8/8 AC pass |
| Pillar 1 HTTP API operational | Pillar | Pillar 1 team | **Resolved** — 12 endpoints, OpenAPI docs, tested |
| Central Coast NSW datasets sourced | External | Mikey | **Pending** — at least one dataset needed before Session 01 |

### Soft Dependencies (this pillar is constrained but not blocked without these)

| Dependency | Impact if Missing | Workaround |
|---|---|---|
| NSW Planning Portal API validated | Milestone 7 build delayed; Sessions 09–10 cannot start | Use mock/recorded API responses for adapter development; validate API in parallel before Session 09 |
| Building footprints dataset | Multi-dataset test in M6 uses only two datasets instead of three | Use any available second dataset type; building footprints are preferred but not mandatory for M6 |
| Road network dataset | Multi-dataset test incomplete | Same as above — any third dataset type validates multi-source coexistence |

### Downstream Impact (what this pillar blocks)

| Dependent Pillar | What It Needs From This Pillar | When It Needs It |
|---|---|---|
| Pillar 3 — Rendering Interface | Populated cells with geometry and fidelity_coverage metadata to render | Before Pillar 3 can render real data (Pillar 3 M2+) |
| Pillar 4 — Spatial Knowledge Layer | Entities with attributes, provenance, and active temporal fields | Before Pillar 4 can build entity graph or activate bitemporal queries |
| Pillar 5 — Interaction Layer | Populated known_names for entity resolution; cell_status for conversational currency | Before Pillar 5 can resolve natural language references or answer "is this still under construction?" |

---

## 5. Token Budget

| Session Type | Typical Token Range | Frequency | Notes |
|---|---|---|---|
| ADR drafting session | 40k–60k | 1 session (ADR-015) | Lower token intensity, high reasoning load |
| Component build session | 60k–120k | 5 sessions (S01–S05) | Moderate — individual modules with tests |
| Integration build session | 100k–180k | 3 sessions (S06, S09, S10) | Higher — wiring components, API integration, complex tests |
| Multi-dataset validation session | 80k–150k | 1 session (S07) | Moderate — running pipelines, validating outputs |
| **Total estimated for this pillar** | **1.2M–1.8M** | **8–10 sessions** | Consistent with original agent analysis estimate |

---

## 6. Milestones

| Milestone | Description | Target Sprint | Success Criteria | Dependent On |
|---|---|---|---|---|
| M1 — Source Adapters | GeoJSON, Shapefile, GeoPackage adapters reading real data | Sprint 1 | CLI reads Central Coast dataset and prints feature counts and sample geometries | Central Coast dataset sourced |
| M2 — CRS Normalisation | All inputs normalised to WGS84 with coordinate validation | Sprint 1 | GDA2020 shapefile correctly reprojected; before/after coordinates match expected values | M1 |
| M3 — Geometry Validation | Quarantine-model validator with structured error reporting | Sprint 1 | Corrupted test dataset caught, fixable issues auto-repaired, quarantine report produced | M1 |
| M4 — Manifests and Entity Extraction | Manifest system, entity extractor, dedup engine | Sprint 2 | Valid manifests for two real datasets. Entities extracted with correct attribute mapping. Dedup detects test duplicates. | M2, M3 |
| M5 — End-to-End Ingestion | First complete dataset through the full pipeline into Harmony Cells | Sprint 2 | Central Coast zoning data ingested. Cells populated via API. Entities registered. Registry records run. Re-ingestion produces identical results. `fidelity_coverage.structural` populated. | M4 |
| M6 — Multi-Dataset Ingestion | Three datasets coexisting in the same cell region | Sprint 3 | Zoning, buildings, and roads ingested. Multi-source entities coexist. Dedup exercised across datasets. Comprehensive ingestion report produced. | M5 |
| M7 — Temporal Trigger Layer | Permit feed connected; cell state transitions live; bitemporal fields active | Sprint 4 | All 8 AC from Dr. Voss's specification pass (AC1–AC8). ADR-015 accepted. Migration approved and executed. Gosford DA fixture resolves correctly. | M6, ADR-015 accepted, NSW API validated, migration approved |

---

## 7. Risks and Blockers

| # | Risk or Blocker | Probability | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| 1 | Central Coast datasets not sourced before Sprint 1 | Medium | High — blocks all build | Identify datasets now. NSW Spatial Services open data portal is the primary source. Mikey to confirm or delegate. | Mikey |
| 2 | NSW Planning Portal API unavailable or structured differently than expected | Medium | High — blocks M7 | Validate endpoint before Sprint 4. Build adapter against recorded responses if live API is unavailable. | Builder Agent (with Mikey escalation) |
| 3 | Entity deduplication false positives in dense areas | Medium | Medium — data quality degradation | Confidence scoring + human review queue for low-confidence matches. Tune thresholds after first real ingestion run. | Builder Agent |
| 4 | CRS detection failures on council datasets | Medium | Low — single datasets affected | Refuse-by-default with manifest overrides. Test against real data in M2 to discover failure modes early. | Builder Agent |
| 5 | Temporal field migration breaks existing Pillar 1 data | Low | High — substrate corruption | Migration has up and down functions. Tested against dev database before production. Requires Mikey approval. | Builder Agent + Mikey |
| 6 | Performance bottleneck on large dataset cell assignment | Low | Medium — slow ingestion | Defer optimisation until M6. Profile first. Vectorise with GeoPandas/NumPy if needed. | Builder Agent |
| 7 | ADR-015 approval delayed | Low | Medium — M7 blocked | Draft ADR early in Sprint 3. Flag to Mikey with clear approval deadline. | Mikey |
| 8 | Pillar 1 API requires extension for permit-to-cell queries | Low | Medium — M7 design change | Flag as gap and request API extension. Do not bypass API with direct DB writes. | Builder Agent + Pillar 1 |

---

## 8. PM Agent Instructions

This section is the direct instruction for the PM Agent building the master plan and Gantt chart.

**Add this pillar to the master Gantt chart with the following parameters:**

- Pillar name: Pillar 2 — Data Ingestion Pipeline
- Start sprint: Sprint 3 (overall project) — immediately follows Pillar 1 completion
- End sprint: Sprint 6 (overall project) — 4 sprints / ~8 weeks including approval gates
- Total duration: 5–6 weeks (may compress to 5 if approvals are prompt)
- Colour code: Teal
- Critical path: Yes

**Flag the following dependencies as blockers in the Gantt chart:**

- Pillar 1 complete → Pillar 2 start (resolved)
- Central Coast datasets sourced → Sprint 1 start (pending — Mikey action)
- ADR-015 accepted → Milestone 7 start (pending — produced in Sprint 3, approved before Sprint 4)
- Mikey approval of temporal field migration → M7 completion (pending)
- NSW Planning Portal API validated → M7 build start (pending)

**Schedule the following milestones as Gantt markers:**

| Marker | Target Sprint | Description |
|---|---|---|
| M1–M3 | Sprint 1 | Pipeline components operational (adapters, CRS, validator) |
| M4–M5 | Sprint 2 | First end-to-end ingestion complete |
| M6 | Sprint 3 | Multi-dataset ingestion validated |
| ADR-015 | Sprint 3 | Temporal trigger architecture accepted |
| M7 | Sprint 4 | Temporal trigger layer live — Pillar 2 complete |

**Token budget note for scheduling:**
This pillar requires approximately 1.2M–1.8M tokens across 8–10 sessions. Integration sessions (S06, S09, S10) are the most token-intensive at 100k–180k each. These should not be scheduled on the same day as high-token sessions from other pillars. ADR-015 drafting (S08) is lower intensity and can share a day with other work if needed.

**Dashboard update on Pillar 2 completion:**
When all seven milestones pass, produce the following update lines:

```
HARMONY UPDATE │ Pillar 2 │ Milestone 1 — CRS normalisation pipeline │ Status: Done │ Tool: CoWork
HARMONY UPDATE │ Pillar 2 │ Milestone 2 — Geometry validation suite │ Status: Done │ Tool: CoWork
HARMONY UPDATE │ Pillar 2 │ Milestone 3 — Geometry → cell mapping engine │ Status: Done │ Tool: CoWork
HARMONY UPDATE │ Pillar 2 │ Milestone 4 — Entity extraction scripts │ Status: Done │ Tool: Code
HARMONY UPDATE │ Pillar 2 │ Milestone 5 — Dataset registration service │ Status: Done │ Tool: Code
HARMONY UPDATE │ Pillar 2 │ Milestone 6 — Central Coast pilot pipeline │ Status: Done │ Tool: CoWork
HARMONY UPDATE │ Pillar 2 │ Milestone 7 — Temporal trigger layer │ Status: Done │ Tool: CoWork
HARMONY DECISION │ Gate 9 — ADR-015 Temporal trigger architecture │ Status: Resolved
```

---

## 9. Human Decision Gates — Pillar 2 Summary

For Mikey's reference, these are the points where human input is required during the Pillar 2 build. They are concentrated, not distributed.

| # | Decision / Action | When | Estimated Time | Blocks |
|---|---|---|---|---|
| 1 | Source and confirm Central Coast datasets (cadastral, zoning, buildings, roads) | Before Sprint 1 | 1–2 hours | All milestones |
| 2 | Review entity extraction thresholds (what counts as a building vs a structure) | During Sprint 2, before M5 | 30 minutes | M5 entity extraction |
| 3 | Review and accept ADR-015 (Temporal Trigger Architecture) | Sprint 3 | 30–60 minutes | M7 |
| 4 | Approve temporal field migration execution | Sprint 4 | 15 minutes | M7 completion |
| 5 | Review any low-confidence dedup matches flagged during ingestion | After M6 | 30 minutes | Data quality sign-off |

**Total estimated human decision time: 3–4 hours across the full 5–6 week build.**

---

*HARMONY Pillar 2 — Data Ingestion Pipeline PM Brief V1.0 — April 2026*
