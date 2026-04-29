# COWORK PROMPT — Pillar 2: Data Ingestion Pipeline Build

Copy everything below this line and paste directly into CoWork.

---

## Mission

You are building the Harmony Data Ingestion Pipeline — the system that connects to live geospatial data sources, translates external data into Harmony semantics, and writes validated entities into the Harmony Cell registry. This is Pillar 2 of the Harmony Spatial Operating System, and it is the single prerequisite for every downstream pillar (Rendering, Knowledge, Interaction).

When this build is complete, the Harmony Cell registry — which was shipped empty in Pillar 1 — will contain real-world entities (zoning areas, cadastral lots, buildings, roads) for the Central Coast NSW pilot region, drawn from live government APIs and OpenStreetMap, with temporal triggers connected to the NSW Planning Portal's permit feeds.

## Your Governing Documents

Read ALL of the following before writing any code. These are your source of truth. Where they conflict with any earlier planning notes, these documents take precedence.

**Architecture and specification:**
- `master-spec-v1_0_1.md` — the Harmony Master Specification V1.0. Defines the three North Stars, five-pillar structure, agent architecture, and Gap Register. Every design decision must be evaluated against all three North Stars simultaneously.

**Pillar 2 build instructions:**
- `HARMONY_P2_DATA_INGESTION_PIPELINE_BRIEF_V2_0.docx` — the authoritative Pillar Brief. Contains resolved decisions, tools and technologies, inter-pillar interfaces, and the complete CoWork task sequence (Tasks 1–11). Section 3 defines the programmatic-first data sourcing strategy with four adapter types. Section 8 contains your task list — including the full Milestone 7 specification with deliverables (D1–D8), acceptance criteria (AC1–AC8), and constraints, all inline. Follow the tasks in order.

**Pillar 1 handoff:**
- `PILLAR_2_HANDOFF_BRIEF.md` — complete context transfer from Pillar 1. Contains the API contract (12 endpoints), schema version (v0.1.3), reserved fields, ADR index (ADR-001 through ADR-014), and known constraints. Read Section 3 (API Contract) carefully — this is the interface you write to.

**ADR for Milestone 7:**
- `ADR-015-temporal-trigger-architecture.md` — the architecture decision record for permit feed integration. Contains the cell state machine, temporal field population rules, fidelity coverage structure, address-to-cell resolution hierarchy, error handling rules, event-sourced model, and multi-jurisdiction adapter pattern. Review this during Task 10. If it has been accepted by Mikey (status changed from Draft to Accepted), proceed with Milestone 7. If it is still in Draft status, flag this as a blocker and do not execute the temporal field migration.

**Entity schemas:**
- `HARMONY_P2_ENTITY_SCHEMAS.md` — defines the four MVP entity types: `zoning_area`, `cadastral_lot`, `building`, `road_segment`. Contains complete attribute mappings from source fields to Harmony fields, dedup strategies per entity type, `known_names` population rules, and OSM-specific processing notes. Use these schemas when building the Entity Extractor (Task 6) and the dataset manifests (Task 5).

**PM and reporting:**
- `HARMONY_DASHBOARD_UPDATE_PROTOCOL_V1_0.docx` — defines the session report format and HARMONY UPDATE line format. Follow this protocol for all session reports.
- `HARMONY_P2_DATA_INGESTION_PIPELINE_PM_BRIEF_V1.0.md` — project management context including phases, sprints, and milestone definitions.

**Pillar 1 technical files (for API integration):**
Read these to understand the Pillar 1 API you are writing to:
- `identity-schema.md` (v0.1.3) — cell and entity schema definitions
- `id_generation_rules.md` — how canonical IDs are generated
- `alias_namespace_rules.md` — how aliases and namespaces work
- `ADR_INDEX.md` — complete index of architecture decisions ADR-001 through ADR-014

**Endpoint validation results (if available):**
- `validation/endpoint_validation_summary.json` — produced by a prior Claude Code session. Contains confirmed endpoint URLs, field schemas, feature counts, and any issues discovered. Use this to inform adapter implementation. If this file does not exist, the adapters should still be built against the documented endpoints but should include robust error handling for unexpected responses.

## Central Coast Pilot Bounding Box

All programmatic data queries use this geographic extent (WGS84 / EPSG:4326):

```
South: -33.55
North: -33.15
West: 151.15
East: 151.75
```

## Data Sources

The pipeline connects to four data sources. Each source has a dedicated adapter type:

| Dataset | Source | Adapter Type | Endpoint |
|---|---|---|---|
| Land Zoning | NSW Planning Portal | ArcGIS REST | `mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/EPI_Primary_Planning_Layers/MapServer` |
| Cadastral Lots | NSW Spatial Services | WFS | `maps.six.nsw.gov.au/arcgis/services/public/NSW_Cadastre/MapServer/WFSServer` |
| Buildings | OpenStreetMap | Overpass API | `overpass-api.de/api/interpreter` |
| Roads | OpenStreetMap | Overpass API | `overpass-api.de/api/interpreter` |

A fifth source — the NSW Planning Portal DA/CDC/PCC APIs — is used in Milestone 7 for permit feed integration. See ADR-015 and Task 11 in the Pillar Brief for endpoint details and architecture.

A file adapter is also built for reading local GeoJSON, Shapefile, and GeoPackage files — used for bulk downloads, test fixtures, and as a fallback if any API is unavailable.

## Build Sequence

Execute the tasks defined in Section 8 of `HARMONY_P2_DATA_INGESTION_PIPELINE_BRIEF_V2_0.docx`, Tasks 1 through 11, in order. Each task includes a description, expected outputs, save locations, and success conditions.

**Summary of tasks:**

1. **Project scaffolding and data profiler** — create the `harmony/pipelines/` package structure and a profiling tool that works against both files and API endpoints
2. **Source adapter layer (M1)** — four adapters: file, WFS, ArcGIS REST, OSM Overpass. All implement the same `read(source_config) → iterator` interface
3. **CRS normalisation service (M2)** — reproject GDA2020/GDA94 to WGS84, pass-through for already-WGS84 data (OSM), coordinate range validation
4. **Geometry validator (M3)** — quarantine model with auto-repair for trivial issues, structured error reporting
5. **Dataset manifest system (M4)** — YAML manifests with `source_type` field, JSON Schema validation, four working manifests for Central Coast datasets
6. **Entity extractor and dedup engine (M4–5)** — attribute mapping per entity schema, hybrid dedup (source ID + spatial proximity), `known_names` population
7. **Cell assignment engine (M5)** — geometry-adaptive resolution, primary cell by centroid/midpoint, secondary cells for spanning entities
8. **End-to-end pipeline and dataset registry (M5–6)** — wire all components, SQLite registry, first complete ingestion from live API
9. **Multi-dataset ingestion (M6)** — all four datasets ingested, multi-source coexistence validated
10. **ADR-015 review (M7 prerequisite)** — review the draft ADR, finalise if needed, flag for approval
11. **Temporal trigger layer (M7)** — permit adapter, cell state transitions, temporal field migration, fidelity reset logic, Gosford DA test fixture

## Critical Rules

1. **Do not bypass the Pillar 1 API.** All cell and entity registration goes through the HTTP API defined in the handoff brief. No direct database writes.

2. **Do not execute the temporal field migration without Mikey's approval.** Flag it as `requires_approval: true` in your session output. If ADR-015 has not been accepted, do not proceed with Milestone 7 schema changes.

3. **Do not store API credentials.** All endpoints used in the MVP are public. If any endpoint requires authentication, document the requirement and use the file adapter as a fallback.

4. **Respect rate limits.** Overpass API: minimum 5 seconds between requests. ArcGIS REST: handle pagination with `resultOffset`. WFS: standard OGC query patterns.

5. **Every entity must carry provenance.** `source_authority`, `source_dataset`, `source_feature_id`, `positional_accuracy_m`, and `observation_date` are required on every entity. No anonymous data.

6. **Quarantine, don't discard.** Failed features go to `quarantine/` with full error context. The pipeline continues. Never silently drop records.

7. **known_names must be populated at ingestion** wherever the source carries human-readable identifiers (place names, street names, road names, property labels). This directly enables Pillar 5's entity resolution.

8. **fidelity_coverage.structural must be populated** on all cells after ingestion. `fidelity_coverage.photorealistic.status` should be set to `pending` (no photorealistic data is available in the MVP).

9. **All adapters implement the same interface.** `read(source_config) → iterator of raw features`. The pipeline does not know or care which adapter type produced the features.

10. **Follow the Milestone 7 specification in Task 11 exactly.** All 8 acceptance criteria (AC1–AC8) must pass. No partial credit. The deliverables, constraints, and acceptance criteria are defined inline in Task 11 of the Pillar Brief.

## Session Reporting

On completion of each session, produce a session report following the format in `HARMONY_DASHBOARD_UPDATE_PROTOCOL_V1_0.docx`. Save to `PM/sessions/YYYY-MM-DD-pillar-2-session-{n}.md`.

Include HARMONY UPDATE lines for each milestone completed:

```
HARMONY UPDATE │ Pillar 2 │ Milestone {n} — {description} │ Status: Done │ Tool: CoWork
```

Flag any decisions that arose during execution that were not covered by the governing documents. Flag any ambiguities that required assumptions. Flag any items requiring Mikey's review or approval.

## Five Non-Negotiables (from Master Spec V1.0)

These apply to all work across all pillars. Do not violate any of them:

1. **No tile-based rendering.** The cell system is not a tile pyramid. Do not produce output that assumes tile-based consumption.
2. **Mandatory cell_key.** Every cell must have a deterministic, reproducible cell_key derived from the Pillar 1 derivation logic.
3. **Temporal versioning from day one.** Every entity carries `ingested_at`, `schema_version`, and placeholders for `valid_from` / `valid_to` even if unused in the MVP.
4. **Dual fidelity ingestion.** The cell package format carries both structural and photorealistic slots. Both exist even if one is empty.
5. **No agent execution before decision gates are resolved.** ADR-015 must be accepted before Milestone 7 schema changes.

## Start Here

Begin by reading the governing documents listed above. Then execute Task 1 (Project Scaffolding and Data Profiler). Proceed through the task list in order. If you encounter a blocker, document it clearly in your session report and proceed to the next non-blocked task.
