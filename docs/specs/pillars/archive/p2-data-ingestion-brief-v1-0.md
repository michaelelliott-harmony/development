# HARMONY — Pillar 2: Data Ingestion Pipeline
## Pillar Brief | Version 1.0
**Status:** Ready for Build
**Date:** April 19, 2026
**North Stars Served:** I, II, III — all three
**Depends On:** Pillar 1 (Spatial Substrate — complete)
**Depended On By:** Pillar 3 (Rendering Interface), Pillar 4 (Spatial Knowledge Layer), Pillar 5 (Interaction Layer)

---

## 1. Purpose

**One-sentence statement of this pillar's role in the Harmony platform:**
All external data is translated into Harmony semantics at ingestion — raw coordinates, GIS layers, and external datasets never reach the rendering or intelligence layers in their original form.

**What this pillar makes possible for the platform that would not exist without it:**
Pillar 1 gives Harmony an empty grid of addressable cells. Pillar 2 fills those cells with the physical world. Without it, there is nothing to render (Pillar 3), nothing to reason about (Pillar 4), nothing to navigate through (Pillar 5), and no data for autonomous systems to localise against (Class II Navigation Agents). Pillar 2 also establishes Harmony's relationship with the real world's data ecosystem — including live permit feeds that keep cell state current — transforming Harmony from a static snapshot into a living map that refreshes on a real-world event schedule rather than a satellite capture schedule.

**The single most important thing this pillar must get right:**
The cell package format — the internal structure of what a populated Harmony Cell actually contains after ingestion, including fidelity classification, temporal metadata, provenance, and trust indicators. If this format is wrong, every consumer breaks. If it is right and extensible, everything downstream works and keeps working.

---

## 2. North Star Obligations

### North Star I — The Seamless World

**This pillar's contribution:**
Ingested data must support continuous LOD streaming, not discrete tile-level loading. Geometry must be stored at the correct resolution level in the cell hierarchy so the renderer can traverse the LOD tree smoothly. Rendering assets must be referenced in a way that supports progressive loading. The cell package format must not force the renderer into a tile-switching model.

**Failure condition — what design choice would make this North Star undeliverable:**
If Pillar 2 writes entities at a single fixed resolution level and stores geometry as monolithic blobs, the renderer cannot do continuous LOD — it is forced to load everything at one level or nothing. The geometry-adaptive resolution assignment and the reference-based cell package with fidelity-typed slots are the structural safeguards against this failure.

### North Star II — The GPS-Free Spatial Substrate

**This pillar's contribution:**
Structural geometry at sub-metre fidelity — precise building footprints, traversable corridors, obstacle maps, vertical clearance data. This is the data that Class II Navigation Agents consume for autonomous decision-making. Pillar 2 must ingest it, validate its accuracy, tag it with a fidelity class and positional accuracy metadata, and store it in a way that navigation agents can query at machine timescales.

**Failure condition:**
If Pillar 2 treats all geometry as equal — no fidelity classification, no accuracy metadata, no distinction between "good enough for a human to see on a map" and "accurate enough for a drone to navigate by" — then Navigation Agents cannot trust any of it. The dual fidelity architecture with per-slot accuracy metadata is the safeguard. Additionally, the cell state machine introduced in Milestone 7 allows Navigation Agents to treat cells in `change_in_progress` status with reduced confidence.

### North Star III — The Spatial Knowledge Interface

**This pillar's contribution:**
Semantically rich entities that the Conversational Spatial Agent can resolve and reason about. When a user asks "what's being built near Terrigal Beach?", the system needs entities with names, types, attributes, temporal state, and cell bindings that the AI can find and ground spatially. Pillar 2 is where those entities first enter the system. Milestone 7's temporal trigger layer enables the system to answer "is this still under construction?" with authority derived from official permit records rather than stale satellite imagery.

**Failure condition:**
If Pillar 2 ingests geometry without attributes — just shapes on a grid, no names, no types, no zoning codes, no property metadata — then Pillar 4 has nothing to build intelligence from, and the Conversational Spatial Agent can find cells but cannot say anything meaningful about them. If `known_names` is not populated at ingestion, Pillar 5 cannot resolve natural language references to real places.

---

## 3. Resolved Decisions

| # | Decision | Resolution | Rationale |
|---|----------|-----------|-----------|
| 1 | Cell package internal structure | Reference-based package. Cell record in the registry stays lightweight (metadata, entity refs, fidelity coverage flags). Actual geometry and rendering assets live in a separate asset store keyed by cell_key and fidelity class. | Aligns with reserved `asset_bundle_count` and `references.asset_bundles` fields. Large photogrammetric meshes and LiDAR point clouds should not live in PostgreSQL rows. The cell record stays fast to query at machine timescales. |
| 2 | Entity deduplication strategy | Hybrid: source-system ID matching preferred, spatial proximity fallback. Match on source-system IDs first (e.g., NSW lot/DP numbers for parcels); where unavailable, fall back to spatial proximity with type-aware configurable thresholds. Low-confidence matches flagged for human review. | Australian cadastral data carries lot/DP numbers as excellent natural keys. Building footprints rarely have stable cross-source IDs, requiring spatial fallback. Confidence scoring avoids silent false positives in dense urban geometry. |
| 3 | Geometry-to-cell mapping semantics | Primary cell + spanning list. Primary cell computed by centroid (polygons) or midpoint (linear features). Secondary cells are all additional intersecting cells. | Already supported by Pillar 1 entity schema (`primary_cell_id` + `secondary_cell_ids`). Centroid provides deterministic, reproducible primary assignment. |
| 4 | Dataset manifest format | YAML, validated against a JSON Schema. Includes: source path/URL, declared CRS, target entity type, attribute mapping, target resolution level, fidelity class, dedup strategy override, source-specific preprocessing flags. | Human-readable, easy to version-control, supports comments. JSON Schema validation ensures manifest correctness before pipeline runs. |
| 5 | Dual fidelity field structure (`fidelity_coverage`) | Two-slot model: `structural` and `photorealistic`. Each slot carries `status` (available / pending / unavailable), `source` (authority name), and `captured_at` (observation date). Defined in Dr. Voss's Milestone 7 specification. | Resolved by Dr. Voss in the Milestone 7 spec. The photorealistic slot resets to `pending` on `change_confirmed` events, signalling Pillar 3 that visual data is stale without attempting inline correction. |
| 6 | Resolution level assignment strategy | Geometry-adaptive with manifest default as floor. Pipeline computes appropriate level based on entity bounding box size against the 12-level hierarchy. Manifest provides a minimum level ("never assign above r06 for zoning polygons") rather than a hard target. | Avoids both the inaccuracy of fixed-level assignment and the complexity of multi-level duplication. Validated against known distortion factors (cells at cube-face corners are ~2.3× larger than at centres). |
| 7 | Error handling philosophy | Quarantine model. Failed features written to `quarantine/` output with full error context. Pipeline continues. Ingestion run report includes quarantine counts and summaries. Dataset with >5% quarantined features triggers warning requiring human review. | Avoids both silent data loss (skip model) and pipeline fragility (halt model). Standard pattern for production data pipelines. |
| 8 | Known names population at ingestion | Pillar 2 populates `known_names` where source data includes place names, street names, property names, or other human-readable identifiers. | Low-cost addition that significantly accelerates Pillar 5's ability to resolve natural language references. Gap 5 (named-entity resolution) is closed at the substrate layer — `known_names` index is ready. |
| 9 | Pipeline orchestration | Lightweight custom Python CLI for MVP. Deferred Airflow/Prefect until dataset count exceeds manual management threshold (~20+ datasets on scheduled ingestion). | Airflow and Prefect introduce deployment infrastructure that is premature for the current stage. A `harmony-ingest` CLI with structured JSON logging is sufficient and dramatically simpler. |
| 10 | Temporal trigger architecture (ADR-015) | Pull-based polling of NSW Planning Portal ePlanning API. Daily minimum poll frequency, hourly for high-activity areas. Cell state machine: stable → change_expected → change_in_progress → change_confirmed. `valid_from` set from completion certificate date, not ingestion timestamp. | Defined by Dr. Voss in the Milestone 7 specification. Pull model is universally reliable; push model to be evaluated in ADR-015 as an alternative and adopted if NSW Planning Portal supports webhooks. |
| 11 | Temporal field activation timing | Activated in Milestone 7 via a migration with up and down functions. Migration requires Mikey's approval before execution. ADR-015 must be accepted before migration runs. | Bitemporal fields were reserved in Pillar 1 (ADR-007) specifically for this purpose. Activation is gated on the ADR and approval to maintain decision-gate discipline. |

---

## 4. Tools and Technologies

| Tool / Technology | Role in This Pillar | Status | Notes |
|---|---|---|---|
| Python 3.11+ | Primary pipeline language | Confirmed | Lingua franca of geospatial tooling; all required libraries available |
| GDAL/OGR (via Fiona, Rasterio) | Source format I/O — Shapefile, GeoJSON, GeoPackage, GeoTIFF, KML, FlatGeobuf | Confirmed | Industry standard; no serious alternative for format breadth |
| Shapely (via GEOS) | Geometry operations, validation, spatial predicates | Confirmed | No meaningful alternative in the Python ecosystem |
| PyProj (via PROJ) | CRS transformation and detection | Confirmed | Definitive coordinate transformation library |
| GeoPandas | Batch spatial operations during pipeline processing | Confirmed | Convenience layer built on Shapely/Fiona/PyProj; not a hard dependency |
| DuckDB | Analytical queries during pipeline internals | Confirmed | Lighter than PostgreSQL for intermediate pipeline work |
| PostgreSQL + PostGIS | Cell and entity store (via Pillar 1 HTTP API) | Confirmed | Pillar 2 writes via HTTP, not direct DB access |
| Docker | Pipeline containerisation with pinned GDAL version | Confirmed | Non-optional — GDAL has complex build/version dependencies |
| JSON Schema | Manifest validation | Confirmed | Validates YAML manifests before pipeline execution |
| Pydantic | Internal data validation and typed models | Confirmed | Python data validation for pipeline stage contracts |
| NSW Planning Portal API | Permit feed for Milestone 7 temporal triggers | Confirmed (pending endpoint validation) | Public API, no auth required. Needs manual verification of endpoint availability and field structure before M7 build |

---

## 5. Inter-Pillar Interfaces

### Inputs This Pillar Receives

| From Pillar | What Is Received | Format / Protocol | When Needed |
|---|---|---|---|
| Pillar 1 — Spatial Substrate | Cell registration API | HTTP REST — POST /cells (JSON) | Available now — all milestones |
| Pillar 1 — Spatial Substrate | Entity registration API | HTTP REST — POST /entities (JSON) | Available now — from Milestone 4 |
| Pillar 1 — Spatial Substrate | Alias and namespace management | HTTP REST — POST /namespaces, POST /aliases, GET /resolve/alias | Available now — from Milestone 4 |
| Pillar 1 — Spatial Substrate | Cell key derivation logic | Python module — derive.py | Available now — used for pre-computing cell assignments |
| Pillar 1 — Spatial Substrate | Adjacency ring queries | HTTP REST — GET /cells/{cell_key}/adjacency | Available now — used for spatial join validation |
| External — NSW Spatial Services | Cadastral boundaries, zoning layers, building footprints, road network | Shapefile, GeoJSON, GeoPackage via NSW open data portal | Required from Milestone 1 |
| External — NSW Planning Portal | Development applications, construction certificates, occupation certificates | HTTP REST — ePlanning Spatial Viewer API (GeoJSON) | Required from Milestone 7 |

### Outputs This Pillar Exposes

| To Pillar | What Is Delivered | Format / Protocol | When Available |
|---|---|---|---|
| Pillar 3 — Rendering | Populated cell packages with renderable geometry, fidelity_coverage metadata, cell_status for re-capture prioritisation | Cell records via Pillar 1 registry + asset bundle references | From Milestone 5 (structural); fidelity_coverage from Milestone 7 |
| Pillar 4 — Knowledge Layer | Entities with attributes, provenance, temporal markers (valid_from, valid_to, version_of, temporal_status) | Entity records via Pillar 1 registry | From Milestone 5 (entities); temporal fields from Milestone 7 |
| Pillar 4 — Knowledge Layer | Dataset lineage and version history | Dataset registry (Pillar 2 internal, queryable) | From Milestone 6 |
| Pillar 5 — Interaction Layer | Populated known_names for entity resolution | Entity attribute written at ingestion via Pillar 1 API | From Milestone 5 |
| Pillar 5 — Interaction Layer | Cell temporal state for conversational currency queries | cell_status field on cell records | From Milestone 7 |
| Reagent — Application Layer | Development activity alerts, neighbourhood change tracking | Cell state transitions surfaced via Pillar 4 queries | From Milestone 7 |

---

## 6. Open Decisions (Deferred)

| # | Decision | Why Deferred | Constraint on Early Build | Target Resolution |
|---|----------|-------------|--------------------------|------------------|
| 1 | `lod_availability` field structure | This field describes how rendered LOD levels map to available data — it is a Pillar 3 consumption concern, not a Pillar 2 production concern | Pillar 2 must not write to this field or define its structure; leave it reserved | Pre-Pillar 3 build (ADR-016) |
| 2 | `asset_bundles` reference format | The typed pointer format for external asset bundles depends on the asset storage system chosen, which is a Pillar 3 architecture decision | Pillar 2 populates `asset_bundle_count` as a denormalised integer count; the reference format is defined when the storage system is chosen | Pre-Pillar 3 build (ADR-016) |
| 3 | Push vs pull model for permit feeds | Dr. Voss defaults to pull (polling), which universally works. Push (webhooks) may be available from some jurisdictions and would be more responsive | ADR-015 must document the evaluation. Build the pull adapter first; add push support as a non-breaking enhancement if available | ADR-015 drafting phase |
| 4 | Multi-jurisdiction permit adapter architecture | The NSWPlanningPortalAdapter should implement a generic PermitSourceAdapter interface for future jurisdictions (QLD, VIC, etc.) | Design the adapter as a pluggable interface from day one. Do not hard-code NSW-specific logic into the state transition service | Milestone 7 design phase |
| 5 | Cell state lifecycle completion | What happens after `change_confirmed` when re-ingestion of structural data occurs? Should there be a `re_ingested` status that returns the cell to `stable`? | Do not add a fifth status value now. Document this as a known gap in ADR-015. The `change_confirmed → stable` transition on successful re-ingestion can be added as a Pillar 4 or future Pillar 2 enhancement | Post-Milestone 7 |
| 6 | Raster and 3D mesh ingestion | Current milestones cover vector formats only. LiDAR (LAS/LAZ), photogrammetric meshes, and GeoTIFF ingestion are required for full dual fidelity | Source adapters must be designed as pluggable per-format modules. Do not couple the pipeline architecture to vector-only assumptions | Post-Pillar 2 MVP or Pillar 3 integration phase |

---

## 7. CoWork Build Instructions

This section is the direct instruction set for CoWork. Write it as if speaking to an agentic system that will execute without further clarification.

**Session objective:**
Build the Harmony Data Ingestion Pipeline — a production-grade system that reads external geospatial data, normalises it to WGS84, validates geometry, maps entities to Harmony Cells at appropriate resolution levels, registers them via the Pillar 1 HTTP API, catalogues all ingestion runs with full provenance, and connects to the NSW Planning Portal to trigger cell state transitions from real-world permit events.

**Input files to read before beginning:**

- `Project Context/master-spec-v1.0.1.md` — governing specification
- `Project Context/HARMONY_P2_DATA_INGESTION_PIPELINE_BRIEF_V1.0.md` — this document
- `Project Context/PILLAR_2_HANDOFF_BRIEF.md` — complete Pillar 1 context transfer
- `Project Context/HARMONY_P2_M7_SPEC.docx` — Dr. Voss's Milestone 7 specification (authoritative)
- `Project Context/HARMONY_DASHBOARD_UPDATE_PROTOCOL_V1.0.docx` — reporting protocol
- Pillar 1 files: `identity-schema.md` (v0.1.3), `id_generation_rules.md`, `alias_namespace_rules.md`, `ADR_INDEX.md`

**Tasks to execute, in order:**

---

**Task 1: Project Scaffolding and Data Profiler**

- Description: Create the Pillar 2 project structure. Build a data profiling tool that inspects a geospatial file and produces a structured report: feature count, attribute names and types, CRS detection, geometry type distribution, bounding box, coordinate range checks, and a sample of the first 5 features.
- Output: `harmony/pipelines/` package structure; `harmony/pipelines/profiler.py`; CLI command `harmony-ingest profile <file>`
- Save to: `harmony/pipelines/`
- Success condition: Running `harmony-ingest profile` against a GeoJSON and a Shapefile produces correct structured JSON reports

---

**Task 2: Source Adapter Layer (Milestone 1)**

- Description: Build format-specific source adapters for GeoJSON, Shapefile, and GeoPackage. Each adapter implements a common interface: `read(source_path) → iterator of raw features`. Adapters know nothing about Harmony — they only know their format. Include format auto-detection from file extension.
- Output: `harmony/pipelines/adapters/geojson.py`, `shapefile.py`, `geopackage.py`, `base.py` (interface); test suite
- Save to: `harmony/pipelines/adapters/`
- Success condition: All three adapters read a real Central Coast dataset file and emit raw features as a stream. CLI command `harmony-ingest read <file>` prints feature counts and sample geometries.

---

**Task 3: CRS Normalisation Service (Milestone 2)**

- Description: Build the CRS normalisation service. Takes raw features in any declared CRS and reprojects to WGS84. Handles missing CRS declarations through configurable fallback rules defined in the dataset manifest. Includes coordinate range validation (lat must be -90 to 90, lng -180 to 180 post-normalisation).
- Output: `harmony/pipelines/normalise.py`; test suite validating GDA2020 → WGS84 transformation against known reference points
- Save to: `harmony/pipelines/`
- Success condition: A GDA2020 / MGA Zone 56 shapefile is correctly reprojected to WGS84. Before/after coordinate comparison matches expected values within tolerance. Missing CRS triggers configurable fallback or rejection.

---

**Task 4: Geometry Validator (Milestone 3)**

- Description: Build the geometry validation service with a defined set of checks: self-intersection detection, invalid ring closure, zero-area polygons, duplicate vertices, points outside valid coordinate bounds, geometry type mismatches against the manifest schema. Implement the quarantine model — failed features written to `quarantine/` with full error context; pipeline continues. Trivially fixable issues (e.g., unclosed rings) are auto-repaired with a log entry.
- Output: `harmony/pipelines/validate.py`; `harmony/pipelines/quarantine.py`; validation report JSON format; test suite using deliberately broken geometries
- Save to: `harmony/pipelines/`
- Success condition: Running validation against a deliberately corrupted test dataset catches all expected issues, auto-repairs fixable ones, quarantines the rest, and produces a structured validation report. Pipeline continues after quarantine.

---

**Task 5: Dataset Manifest System (Milestone 4)**

- Description: Define the YAML manifest schema and build a manifest validator. Produce working manifests for at least two real Central Coast datasets (cadastral boundaries and zoning layers). The manifest includes: source path/URL, declared CRS (or "detect"), target entity type, attribute mapping (source column → Harmony field), target resolution level (default/floor), fidelity class, dedup strategy override, and source-specific preprocessing flags.
- Output: `harmony/pipelines/manifest.py` (schema and validator); `harmony/pipelines/manifests/` directory with example manifests; JSON Schema file for manifest validation
- Save to: `harmony/pipelines/`
- Success condition: Manifest validator accepts valid manifests and rejects invalid ones with clear error messages. Two real-dataset manifests are complete and valid.

---

**Task 6: Entity Extractor and Deduplication Engine (Milestone 4–5)**

- Description: Build the entity extraction module that converts validated, normalised geometries into Harmony entities according to the dataset manifest's attribute mapping. Implement the hybrid deduplication engine: source-system ID matching first (lot/DP numbers for parcels), spatial proximity fallback with type-aware configurable thresholds, confidence scoring, and low-confidence match flagging for human review. Populate `known_names` from source attributes where place names, street names, or property names are present.
- Output: `harmony/pipelines/extract.py`; `harmony/pipelines/dedup.py`; dedup configuration schema; test suite
- Save to: `harmony/pipelines/`
- Success condition: Entities are extracted with correct attribute mapping. Duplicate detection correctly identifies duplicates by source ID and by spatial proximity. Low-confidence matches are flagged. `known_names` is populated where applicable.

---

**Task 7: Cell Assignment Engine (Milestone 5)**

- Description: Build the geometry-to-cell mapping engine. For each entity, compute the appropriate resolution level using geometry-adaptive assignment (bounding box size against 12-level hierarchy, manifest default as floor). Compute primary cell by centroid (polygons) or midpoint (linear features). Compute secondary cells (all additional intersecting cells). Register cells and entities via the Pillar 1 HTTP API. Ensure cell registration is idempotent.
- Output: `harmony/pipelines/assign.py`; integration with Pillar 1 `derive.py` for cell key computation; test suite including multi-cell spanning scenarios
- Save to: `harmony/pipelines/`
- Success condition: A zoning polygon correctly maps to cells at the geometry-adaptive resolution level. A large polygon spanning multiple cells produces correct primary + secondary cell list. Cell registration is idempotent. Entity registration calls Pillar 1 API successfully.

---

**Task 8: End-to-End Pipeline and Dataset Registry (Milestones 5–6)**

- Description: Wire all components into a single pipeline: `read → normalise → validate → extract → assign → register`. Build the dataset registry (SQLite for MVP) that records: dataset manifests, ingestion run history, source file checksums, entity counts, validation reports, quarantine summaries, provenance chains, and version lineage. Build the `harmony-ingest run <manifest>` CLI command. Ingest the first complete Central Coast dataset (cadastral or zoning) end-to-end. Populate `fidelity_coverage.structural` on all cells.
- Output: `harmony/pipelines/runner.py`; `harmony/pipelines/registry.py`; SQLite schema; CLI integration; ingestion run report format
- Save to: `harmony/pipelines/`
- Success condition: Running `harmony-ingest run manifests/central-coast-zoning.yaml` ingests the complete dataset. Cells are populated in the Pillar 1 registry. Entities are registered with correct attributes and cell bindings. Dataset registry records the full run with provenance. Re-ingestion produces identical results (idempotency). `fidelity_coverage.structural` is populated on all affected cells.

---

**Task 9: Multi-Dataset Ingestion (Milestone 6)**

- Description: Ingest three datasets of different types (zoning polygons, building footprints, road centrelines) into the same cell region. Validate that entities from different sources coexist correctly within cells. Exercise deduplication across datasets. Produce a comprehensive ingestion report covering all three datasets.
- Output: Three dataset manifests; multi-dataset ingestion test; ingestion report
- Save to: `harmony/pipelines/manifests/`
- Success condition: All three datasets ingest successfully. Entities from different sources coexist within cells without collision. Deduplication correctly handles any overlapping entities. Cell packages contain multi-source entities queryable by source.

---

**Task 10: ADR-015 Drafting (Milestone 7 prerequisite)**

- Description: Draft ADR-015: Temporal Trigger Architecture — Permit Feed Integration. Following the brief defined in Dr. Voss's Milestone 7 specification. The ADR must address: the permit source and polling strategy, the address-to-cell resolution logic, the cell state machine (stable → change_expected → change_in_progress → change_confirmed), the `valid_from` population rule (completion certificate date, not ingestion timestamp), push vs pull evaluation, single-source vs multi-source architecture, event-sourced vs snapshot-updated cell state. The ADR must be reviewed and accepted by Mikey before any schema changes are written.
- Output: `docs/adr/ADR-015-temporal-trigger-architecture.md`
- Save to: `docs/adr/`
- Success condition: ADR-015 follows the established format (Context, Decision, Consequences, Alternatives Considered). All items from Dr. Voss's ADR brief are addressed. ADR is flagged as `requires_approval: true` in session output.

---

**Task 11: Temporal Trigger Layer (Milestone 7)**

- Description: Following Dr. Voss's authoritative Milestone 7 specification, build the temporal trigger subsystem. This includes: (D2) NSW Planning Portal adapter that polls the ePlanning API and normalises permit records; (D3) permit-to-cell resolver using spatial intersection at r10 with address fallback; (D4) cell state transition service implementing the event-to-transition mapping table — idempotent, with audit logging; (D5) temporal field activation migration with up and down functions — requires Mikey's approval before execution; (D6) fidelity reset logic that sets `photorealistic.status = pending` on `change_confirmed` events; (D7) full test suite including the Gosford DA fixture. The adapter must implement a generic `PermitSourceAdapter` interface for future multi-jurisdiction support.
- Output: `harmony/pipelines/temporal/adapter.py`, `resolver.py`, `transitions.py`; migration file; test suite; session progress report with HARMONY UPDATE line
- Save to: `harmony/pipelines/temporal/`
- Success condition: All 8 acceptance criteria from Dr. Voss's specification pass — AC1 through AC8 as defined in Section 6 of HARMONY_P2_M7_SPEC.docx. No partial credit.

---

**On completion:**
Produce a session summary saved as `PM/sessions/YYYY-MM-DD-pillar-2-completion.md` confirming what was created, where each file was saved, and flagging any ambiguities or decisions that arose during execution that require human review before the next session. Include HARMONY UPDATE lines for all seven milestones.

---

## 8. Gaps and Risks

| # | Gap or Risk | Impact | Mitigation |
|---|---|---|---|
| 1 | NSW Planning Portal API endpoint not validated | Milestone 7 build blocked if API structure differs from spec assumptions | Manual verification of endpoint availability, field structure, and Central Coast LGA coverage before M7 build begins. 30-minute task. |
| 2 | Entity deduplication false positives in dense urban geometry | Duplicate entities in cells; data quality degradation for all downstream consumers | Confidence scoring on all dedup matches. Low-confidence matches flagged for human review. Type-aware thresholds (buildings require closer proximity than parcels). |
| 3 | Schema drift between Pillar 2 entity model and Pillar 4 requirements | Re-ingestion required if Pillar 4 needs entity attributes not captured during initial ingestion | Freeze entity schema for MVP entity types before Milestone 5. Version the schema explicitly. Design attribute mapping as additive (new attributes can be added without breaking existing records). |
| 4 | CRS detection failures on real-world council datasets | Pipeline rejects valid data due to missing or incorrect CRS metadata | Refuse-by-default with explicit per-dataset overrides in manifest. Test against three real council datasets in Milestone 2 to discover failure modes early. |
| 5 | Performance on first large dataset ingestion | Cell assignment for million-feature datasets slow if implemented naively | Defer optimisation until Milestone 6 multi-dataset test. Profile and vectorise (NumPy/GeoPandas batch operations) only if measured latency exceeds acceptable threshold. |
| 6 | Cell state machine edge case: change_confirmed with no re-ingestion | Cell sits indefinitely with stale structural data and photorealistic marked as pending | Document as known gap in ADR-015. The transition from `change_confirmed` back to `stable` on successful re-ingestion is a post-M7 enhancement. |
| 7 | GDAL version inconsistency across development environments | Different GDAL versions produce subtly different geometry outputs | Docker container with pinned GDAL version from day one. All pipeline execution runs inside the container. |
| 8 | Dual fidelity MVP limitation: no photorealistic data source for Central Coast yet | Milestone 5–6 can only exercise structural fidelity path | Acceptable for MVP. Schema and pipeline architecture carry both slots from day one. `fidelity_coverage.photorealistic.status = pending` is the honest representation. First photorealistic data expected during Pillar 3 integration. |

---

*HARMONY Pillar 2 — Data Ingestion Pipeline Brief V1.0 — April 2026*
