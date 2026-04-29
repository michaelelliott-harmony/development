# Harmony P2 — Data Ingestion Pipeline Brief V2.0
## Sections 4–6: Build-Critical Content (Markdown Edition)

> **Source:** `HARMONY_P2_DATA_INGESTION_PIPELINE_BRIEF_V2_0.docx`  
> **Converted:** 2026-04-29 by Marcus Webb for agent consumption  
> **Scope:** Sections 4, 5, and 6 only — Data Contract, Branch B Audit, Sprint AC tables  
> **Full document:** See `.docx` for Sections 1–3 and 7–9

---

## Section 4 — The Data Contract: Cell and Entity Record Schema

Every record written by Pillar 2 must conform to this contract. Fields marked **New in V2.0** were not present in the V1.1 brief.

---

### 4.1 Cell Record — Required Fields at Ingestion

| Field | Type | Source | New in V2.0 |
|---|---|---|---|
| `cell_key` | string | Derived deterministically via BLAKE3 from geometry | No |
| `canonical_id` | string | System-assigned UUID. Maps to ISO 19115 `fileIdentifier` (STD-V04) | No |
| `geometry_inferred` | boolean | `true` when geometry is procedurally generated, not captured. Atomically forces `splat_pending` (ADR-022) | No |
| `geometry_source_url` | string, nullable | URL of source geometry where captured. Null for inferred geometry | No |
| `fidelity_coverage` | jsonb | Structured object with `photorealistic` and `schematic` slots. Each carries `status`, `source_tier` (1–4, nullable), `confidence`, `timestamp` | No |
| `source` | jsonb — lineage object | Structured lineage: `source_dataset_id`, `source_dataset_date`, `source_organisation`, `source_licence`, `process_steps[]`, `processing_organisation`, `processing_date` (STD-V01) | **YES — V2.0** |
| `data_quality` | jsonb | Quality declaration: `completeness_percent` (nullable int), `positional_accuracy_metres` (nullable float), `last_validated` (nullable datetime). ISO 19157. (STD-V02) | **YES — V2.0** |
| `crs_authority` | string, default `'EPSG'` | CRS authority registry. Always EPSG for Harmony standard operation (STD-V03) | **YES — V2.0** |
| `crs_code` | integer, default `4326` | EPSG code for the CRS. 4326 = WGS84. 7843 = GDA2020 (STD-V03) | **YES — V2.0** |
| `field_descriptors` | jsonb, empty at activation | Typed container reserved for HCI physical field sensing. Types: `visual_radiance`, `acoustic`, `thermal`, `electromagnetic`. **Must not be populated at ingestion** (ADR-017, ADR-023) | **YES — V2.0** |
| `valid_from` | timestamp | **Mandatory** where source dataset carries a feature date. Source-specific mappings in manifest (STD-V05) | No — but now **MANDATORY** |

---

### 4.2 Entity Record — Required Fields

| Field | Type | Rule | Changed in V2.0 |
|---|---|---|---|
| `entity_type` | string | One of: `cadastral_lot`, `zoning_area`, `building`, `road_segment` | No |
| `source_tier` | integer | 1–4. Write-once. System-assigned. Never 0. (ADR-019) | No |
| `provenance_hash` | string | SHA-256 of source record. Immutable after write. | No |
| `known_names` | array of strings | **MANDATORY.** An entity with available source names and empty `known_names` is a validation failure, not a warning. (HCI-V05, Sprint 2 AC-R5) | **YES — now MANDATORY** |
| `dedup_key` | string | `PCO_REF_KEY` for `zoning_area`. `LAM_ID` is permanently retired and must not appear in any code or schema. | No — but PCO_REF_KEY confirmed |

---

### 4.3 Temporal Field Mappings by Source Dataset

Per STD-V05, `valid_from` is mandatory where the source carries a feature date. The following mappings apply to all four Central Coast datasets:

| Source Dataset | Source Date Field | Maps To | Temporal Status |
|---|---|---|---|
| NSW Valuer General Cadastral | `SURVEY_DATE` or `LODGEMENT_DATE` | `valid_from` | As recorded |
| NSW Planning Portal (zoning) | `DETERMINATION_DATE` | `valid_from` | As recorded |
| OpenStreetMap Buildings | Dataset extraction timestamp | `valid_from` | `inferred` — dataset-level, not feature-level |
| OpenStreetMap Roads | Dataset extraction timestamp | `valid_from` | `inferred` — dataset-level, not feature-level |
| Procedurally generated | Ingestion run timestamp | `valid_from` | `temporal_status = inferred` |

---

## Section 5 — Pre-Sprint 1: Branch B Compliance Audit

This section defines the mandatory pre-Sprint 1 step. Before any new code is written, Dr. Adeyemi must audit the existing Branch B implementation against the current ADR set and produce a gap report.

---

### 5.1 Branch B Contents (Confirmed by Claude Code Audit — April 29, 2026)

| File / Module | Lines | Scope |
|---|---|---|
| `harmony/pipelines/adapters/` (base, arcgis_rest, file, osm) | ~800 | M1 — four of five adapters (no WFS) |
| `harmony/pipelines/normalise.py` | 299 | M2 — CRS normalisation |
| `harmony/pipelines/validate.py` | 376 | M3 — geometry validation |
| `harmony/pipelines/quarantine.py` | 190 | M3 — quarantine |
| `harmony/pipelines/cell_key.py` + `assign.py` | 457 | M3/M5 — cell assignment |
| `harmony/pipelines/extract.py` | 346 | M4 — entity extraction |
| `harmony/pipelines/dedup.py` | 252 | M4 — deduplication |
| `harmony/pipelines/manifest.py` | 270 | M4 — manifest system |
| `harmony/pipelines/registry.py` | 247 | M5 — entity/cell registry interface |
| `harmony/pipelines/runner.py` | 411 | M5 — end-to-end orchestrator |
| `harmony/pipelines/multi_runner.py` | 288 | M6 — multi-dataset runner |
| `harmony/pipelines/p1_client.py` | 157 | Pillar 1 API client |
| `manifests/` (4 yaml files) | ~80 | Central Coast datasets defined |
| `PM/sessions/` (3 session reports) | — | Sprint 1, M3–M5, Sprint 2 M6 complete |
| **TOTAL** | **~7,126 lines** | M1 through M6 |

> **Note:** Branch A (`origin/claude/p2-m1-source-adapters`) also exists with M1–M3 and the `harmony-ingest` CLI packaging (`setup.py`). Branch B does not have `setup.py`. The CLI entry point must be harvested from Branch A or rewritten if Branch B is used as the base.

---

### 5.2 The Audit Checklist

Dr. Adeyemi checks Branch B against each of the following before Sprint 1 dispatches:

| Check | What to Look For | Gap Level |
|---|---|---|
| ADR-022 A1 | Tier 4 fidelity exclusion CHECK constraints present on `photorealistic` and `schematic` slots? | Critical if missing |
| ADR-022 A2 | `source_tier` range enforced as 1–4 (not 0–4) throughout? Fidelity `source_tier` nullable? | Major if missing |
| ADR-022 A3 | Dual `source_tier` semantics documented? Fidelity tier cannot be lower than provenance tier? | Major if missing |
| ADR-022 A4 | `lod_chain` minimum cardinality >= 1 enforced? | Moderate if missing |
| STD-V01 | `source` field is structured lineage object (not a string)? | Critical if missing |
| STD-V02 | `data_quality` object present on cell records? | Critical if missing |
| STD-V03 | `crs_authority` and `crs_code` fields present on geometry record? | Major if missing |
| STD-V05 | `valid_from` population mandatory where source carries feature date? Temporal mappings in manifests? | Major if missing |
| ADR-023 | `field_descriptors` column reserved on cell schema? Empty at ingestion? | Major if missing |
| `known_names` | Mandatory enforcement active? Validation failure (not warning) for empty `known_names` where source names available? | Major if missing |
| `PCO_REF_KEY` | `LAM_ID` completely absent from code? `PCO_REF_KEY` used as `zoning_area` dedup key? | Moderate (already fixed in entity schemas) |
| M7 reconciliation | Does Branch B `adapters/base.py` conflict with main's `temporal/adapter.py`? Is a shared `BaseAdapter` needed? | Assess only |
| CLI packaging | No `setup.py` in Branch B. Confirm `harmony-ingest` CLI can be brought from Branch A. | Required for Sprint 1 completion |

---

### 5.3 Audit Outcomes

The audit produces one of three rulings:

- **Option A:** Branch B is the Sprint 1 baseline — patch the identified gaps, add missing fields, merge.
- **Option B:** Branch B logic is sound but structure needs reorganisation — cherry-pick modules into a fresh Sprint 1 branch.
- **Option C:** Branch B has structural conflicts with the current ADR set — archive it and build Sprint 1 fresh against the full V2.0 data contract.

Dr. Adeyemi makes the recommendation. Marcus routes to Dr. Voss if Option C requires an architectural ruling.

> **Current ruling (per AGENTS.md, April 29, 2026):** Audit in progress. Ruling pending.

---

## Section 6 — Sprint Structure and Acceptance Criteria

---

### 6.1 Pre-Sprint 1 — Branch B Audit

**Owner:** Dr. Adeyemi  
**Output:** Gap report at `PM/sessions/2026-04-29-branch-b-audit.md`  
**Decision:** Option A, B, or C ruling  
**Estimated duration:** One session

---

### 6.2 Sprint 1 — Foundation Pipeline (M1, M2, M3)

**Dispatches after:** Branch B audit complete, ADR-020 and ADR-021 accepted by Dr. Voss.

| AC | Acceptance Criterion |
|---|---|
| M1-AC1 | Five source adapters operational: GeoPackage/Shapefile/GeoJSON (file), ArcGIS REST, Overpass/OSM |
| M1-AC2 | `harmony-ingest` CLI functional via `setup.py` entry point |
| M1-AC3 | Manifests present for all four Central Coast datasets |
| M1-AC4 | Live endpoint validation: NSW Planning Portal (3,866 features), NSW Spatial Services (133,943 features), OSM buildings (47,319), OSM roads (32,712) |
| M2-AC1 | GDA2020 and GDA94 to WGS84 via NTv2 grid. `always_xy=True` confirmed. |
| M2-AC2 | `source_crs` preserved on output record. `crs_authority` and `crs_code` fields populated (STD-V03) |
| M2-AC3 | Gosford CBD reference point (lon=151.3428, lat=−33.4271) transformation verified |
| M3-AC1 | Seven validation checks in order. Auto-repair for minor issues with 1% area delta guard on `buffer(0)` |
| M3-AC2 | Quarantine partition active with six reason codes (Q1–Q4). 90-day retention per ADR-021 |
| M3-AC3 | `ValidationReport` includes `threshold_exceeded` flag. Default quarantine rate threshold: 5% |

---

### 6.3 Sprint 2 — Entity Extraction and Cell Assignment (M4, M5)

**Dispatches after:** ADR-018, 019, 022 accepted; ADR-023 finalised (S1–S4 answered by Dr. Voss); ADR-017 accepted.

| AC | Acceptance Criterion |
|---|---|
| M4-AC1 | Entity extraction for all four entity types: `cadastral_lot`, `zoning_area`, `building`, `road_segment` |
| M4-AC2 | `PCO_REF_KEY` used as `zoning_area` dedup key. No reference to `LAM_ID` in any code. |
| M4-AC3 | `known_names` populated as MANDATORY. Entity with available source names and empty `known_names` fails validation. |
| M4-AC4 | `source` field is structured lineage object per STD-V01. All seven sub-fields present. |
| M4-AC5 | `data_quality` object present on all cell records. `completeness_percent`, `positional_accuracy_metres`, `last_validated` populated where known. Nullable where not (STD-V02). |
| M4-AC6 | `source_tier` assigned as 1–4. Never 0. Write-once. Tier 4 entities cannot have fidelity `status = available` (ADR-022 A1). |
| M4-AC7 | `field_descriptors` present on cell records. Empty jsonb. Must not be populated at ingestion (ADR-023/ADR-017). |
| M4-AC8 | `valid_from` populated for all entities where source carries a feature date. Temporal mappings from Section 4.3 applied (STD-V05). |
| M5-AC1 | Cell assignment correct for polygon, line, and point geometries at appropriate LOD levels. |
| M5-AC2 | All writes via Pillar 1 HTTP API. No direct database access. |
| M5-AC3 | Idempotency verified: re-ingestion of same dataset produces zero new entities. |
| AC-R1 | A registered cell with geometry produces a retrievable asset bundle record keyed by `cell_key` and `fidelity_class`. |
| AC-R2 | Asset bundle record contains: `format=glTF`, `compression=Draco`, `lod_level`, `captured_at`, `source`. |
| AC-R3 | `geometry_inferred` flag correctly set: `true` for procedural, `false` for captured. |
| AC-R4 | No asset bundle stored with bounding-box or zoom-level key. All bundles keyed by `cell_key`. |
| AC-R5 | Every ingested entity with a human-readable name has a populated `known_names` field *(duplicate of M4-AC3 — intentional)*. |
| AC-R6 | `fidelity_coverage.photorealistic.status` is set to `splat_pending` for all procedurally generated cells. |

---

### 6.4 Sprint 3 — Full-Scale Central Coast Ingestion (M6)

**Dispatches after:** M1 through M5 complete with all acceptance criteria passing. Branch B audit resolved.

| AC | Acceptance Criterion |
|---|---|
| M6-AC1 | All four datasets ingested at full Central Coast scale: ~217,840 total features |
| M6-AC2 | Multi-source coexistence: cells carrying entities from 2+ source types present and queryable |
| M6-AC3 | `fidelity_coverage` populated on all cells: `structural.status = available`, `photorealistic.status = pending` |
| M6-AC4 | `known_names` coverage >= 90% per entity type |
| M6-AC5 | Idempotency: re-run of zoning dataset produces zero new entities |
| M6-AC6 | ADR-022 compliance verified across all ingested records: `source_tier` 1–4, no Tier 4 available fidelity |
| M6-AC7 | STD-V01 lineage objects present on all records. STD-V02 `data_quality` populated where source metadata available. |
| M6-AC8 | Performance: throughput measured and reported (features/second at each pipeline stage) |

---

*Harmony Spatial Operating System · Pillar 2 Data Ingestion Pipeline Brief V2.0 · April 2026 · Confidential*
