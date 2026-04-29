# ADR-024: Geospatial Standards Compliance — ISO 19115 / 19157 / 19111 / OGC

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-29 |
| **Acceptance Date** | 2026-04-29 |
| **Author** | Dr. Mara Voss (Principal Architect), responding to standards brief by Dr. Kofi Boateng (CGO) |
| **Accepted By** | Dr. Mara Voss (Principal Architect) — implementation ADR, within authority per AUTHORITY_MATRIX |
| **Supersedes** | None |
| **Related ADRs** | ADR-007 (Temporal Versioning), ADR-016 (Temporal Trigger Architecture), ADR-018 (Data Tier Model), ADR-020 (CRS Normalisation Strategy), ADR-022 (Rendering Asset Format and Data Contract) |
| **Pillar** | Cross-pillar — schema changes in Pillars 1 and 2; mapping rules for Pillar 3 export layer |
| **Migration Gate** | Schema migrations (STD-V01, STD-V02, STD-V03) require Mikey approval before execution. |

---

## 1. Context

Dr. Kofi Boateng's geospatial standards review (April 2026) identified five
gaps between Harmony's current schema and the ISO/OGC standards required for
interoperability with government spatial data infrastructure, particularly
ANZLIC-profile metadata and OGC API Features responses.

The five gaps are:

| ID | Standard | Gap |
|---|---|---|
| STD-V01 | ISO 19115 / ANZLIC | `source` field is a flat string; needs structured lineage object |
| STD-V02 | ISO 19157 | No `data_quality` object on records |
| STD-V03 | ISO 19111 | No CRS authority/code declaration on cell geometry records |
| STD-V04 | ISO 19115 | `canonical_id` not mapped as `fileIdentifier` in metadata exports |
| STD-V05 | OGC API Connected Systems v1.0 | `valid_from` population is recommended, not mandatory |

All five must be resolved before Sprint 2 writes production data. Four require
schema additions; one (STD-V04) is a mapping rule with no schema change.

This ADR records the binding architectural decisions for all five gaps in a
single document. Each decision references the existing ADR that governs the
affected schema area.

---

## 2. Decision

### 2.1 STD-V01 — Structured Lineage Object (ISO 19115 / ANZLIC)

**Decision:** Replace the flat provenance fields on entity and cell-populating
records with a structured `source_lineage` JSONB object carrying seven
sub-fields per ISO 19115 lineage requirements.

**Schema — `source_lineage` object:**

```json
{
  "source_lineage": {
    "source_dataset_id": "string — NOT NULL — identifier of the source dataset (e.g. 'dcdb_lots', 'epi_land_zoning')",
    "source_dataset_date": "date — NULLABLE — publication or vintage date of the source dataset",
    "source_organisation": "string — NOT NULL — organisation that published the source data (e.g. 'nsw_spatial_services')",
    "source_licence": "string — NOT NULL — SPDX licence identifier or licence URL (e.g. 'CC-BY-4.0')",
    "process_steps": [
      {
        "step_name": "string — processing step identifier",
        "step_description": "string — what this step did",
        "step_datetime": "datetime — when this step executed"
      }
    ],
    "processing_organisation": "string — NOT NULL — organisation that ran the processing pipeline (default: 'harmony')",
    "processing_date": "datetime — NOT NULL — when the ingestion pipeline processed this record"
  }
}
```

**Migration from existing flat fields:**

| Existing Field | Maps To | Action |
|---|---|---|
| `source_authority` | `source_lineage.source_organisation` | Consolidated |
| `source_dataset` | `source_lineage.source_dataset_id` | Consolidated |
| `observation_date` | `source_lineage.source_dataset_date` | Consolidated |
| `ingested_at` | `source_lineage.processing_date` | Consolidated |
| *(new)* | `source_lineage.source_licence` | Added |
| *(new)* | `source_lineage.process_steps[]` | Added |
| *(new)* | `source_lineage.processing_organisation` | Added |

The original flat fields (`source_authority`, `source_dataset`,
`source_feature_id`, `observation_date`) remain on the entity base schema
during the migration window. Once all ingestion adapters emit `source_lineage`,
the flat fields are deprecated. `source_feature_id` remains a top-level field
— it identifies the feature within the source, not the source itself.

**Scope:** Entity records and cell-populating records. NOT asset bundle records
— asset bundles already carry their own provenance via ADR-022 (`geometry_source_hash`,
`encoding_format`, `encoding_version`).

**Compatibility with HCI-V03 (`references.asset_bundles`):** No conflict.
`source_lineage` describes data provenance (where did this data come from?).
`references.asset_bundles` describes rendering representations (what geometry
assets exist?). These are orthogonal concerns at different locations in the
schema. The lineage object does not touch the asset bundle reference array.

**Compatibility with ADR-018 / ADR-019:** The tier enforcement fields
(`source_tier`, `source_id`, `confidence`, `provenance_hash`) remain
top-level. `source_lineage` extends provenance metadata; it does not
replace tier classification. `provenance_hash` computation (ADR-019) must
be updated to include the full `source_lineage` object in the canonicalised
tuple.

### 2.2 STD-V02 — Data Quality Object (ISO 19157)

**Decision:** Add a `data_quality` object to the **asset bundle record**,
not the cell record.

**Schema — `data_quality` object on asset bundles:**

```json
{
  "data_quality": {
    "completeness_percent": "integer or null — 0–100 — percentage of expected features present in this representation",
    "positional_accuracy_metres": "float or null — estimated positional accuracy of this representation in metres",
    "last_validated": "datetime or null — when this quality assessment was last performed"
  }
}
```

All three sub-fields are nullable. A null value means "not assessed" —
distinct from zero.

**Why asset bundle, not cell:**

1. Data quality describes the captured representation, not the physical
   spatial region. A cell is a container; quality is a property of what
   was captured about it.
2. Different representations of the same cell have different quality
   characteristics. A Tier 1 LiDAR bundle at 0.1m accuracy and a Tier 3
   ML-inferred bundle at 5m accuracy coexist on the same cell. Cell-level
   quality would force a premature and lossy aggregation.
3. ADR-022 established asset bundles as the carrier for per-representation
   metadata (fidelity states, source tier, confidence). `data_quality` is
   the same category of metadata.
4. The entity base schema already carries `positional_accuracy_m` per
   entity — this is the entity-level quality signal. The asset bundle
   `data_quality` is the representation-level quality signal.

**Cell-level quality derivation:** If a consumer requires a cell-level
quality summary, it is computed at read time from the quality metrics of
the cell's asset bundles. No cell-level storage is needed.

**Compatibility with ADR-022:** Additive. The `data_quality` object is
added alongside the existing `fidelity_coverage` object on the asset
bundle schema. No existing fields are modified.

### 2.3 STD-V03 — CRS Authority and Code (ISO 19111)

**Decision:** Add `crs_authority` (string, default `"EPSG"`) and
`crs_code` (integer, default `4326`) to the cell geometry record. A full
ISO 19111 CRS object is not required.

**Schema — two fields on cell geometry records:**

| Field | Type | Default | Nullable | Purpose |
|---|---|---|---|---|
| `crs_authority` | TEXT | `'EPSG'` | NOT NULL | CRS registry authority |
| `crs_code` | INTEGER | `4326` | NOT NULL | CRS code within the authority registry |

**Why not a full ISO 19111 CRS object:**

1. Harmony is a single-CRS system. ADR-020 established WGS84 (EPSG:4326)
   as the canonical and only stored CRS. The authority+code pair is the
   ISO-compliant compact representation for a well-known CRS.
2. The local ENU (East-North-Up) frame is derived at runtime from the cell
   centroid (`centroid_ecef`). It is not a registered CRS — it has no EPSG
   code, no datum definition independent of the cell position. It cannot
   be meaningfully described by a static CRS declaration on the record.
3. A full CRS object (datum, ellipsoid, prime meridian, coordinate system
   axes) can be reconstructed by any consumer from the EPSG registry using
   the authority+code pair. Embedding it adds ~500 bytes per record for
   information that is both static and universally available.

**Compatibility with ADR-020:** Complementary. ADR-020 governs source CRS
tracking and transformation metadata on ingested records. STD-V03 governs
the CRS declaration on the stored (post-transformation) cell geometry.
ADR-020 tells you where the data came from; STD-V03 tells export consumers
what CRS the stored geometry is in.

**Engineering cost:** Near zero, as identified in the standards brief. Two
columns with defaults. No logic changes.

### 2.4 STD-V04 — canonical_id as ISO 19115 fileIdentifier

**Decision:** Map `canonical_id` to ISO 19115 `fileIdentifier` in all
metadata exports and OGC API Features responses. This is a **mapping rule**
— no new schema fields are required.

**Mapping rule:**

| Harmony Field | ISO 19115 Field | Context |
|---|---|---|
| `canonical_id` | `fileIdentifier` | Metadata exports (ISO 19139 XML, ANZLIC profile) |
| `canonical_id` | `id` | OGC API Features responses (GeoJSON `id` property) |

**Implementation scope:** Export layer and API response serialisation only.
No changes to the cell identity schema, the entity schema, or any internal
data structures. The mapping is applied at the point where Harmony data
crosses the system boundary into an ISO or OGC format.

**Compatibility:** No schema impact. `canonical_id` already satisfies the
`fileIdentifier` contract — it is a globally unique, immutable string
identifier. The mapping is semantically correct.

### 2.5 STD-V05 — valid_from Mandatory Population

**Decision:** Elevate `valid_from` population from recommended to mandatory
on **entity records** where the source dataset carries a feature date.
Cell-level `valid_from` remains governed by ADR-016.

**Boundary clarification:**

| Record Type | `valid_from` Owner | Population Rule | Governing ADR |
|---|---|---|---|
| Entity record | Pillar 2 (ingestion) | Mandatory when source carries a feature date (`observation_date`, `createdate`, `start_date`). Set to the source feature date. Null only when source provides no date. | ADR-024 (this ADR) |
| Cell record | Pillar 4 (temporal trigger) | Set on `change_confirmed` transition to the occupation certificate date. Never set at ingestion time. | ADR-016 §2.4 |

**Validation rule:** The ingestion pipeline must enforce a CHECK: if the
source dataset manifest declares that the dataset carries per-feature dates,
then `valid_from` on every ingested entity record must be non-null. Records
with null `valid_from` from a date-carrying dataset are routed to quarantine
(ADR-021, reason code `Q4_SCHEMA_VIOLATION`).

**Source datasets without feature dates:** When the source dataset does not
carry per-feature dates (e.g., OSM roads — no per-feature capture dates),
`valid_from` remains null. The mandate applies only when the data exists
and was not populated.

**Compatibility with Pillar 4:** No conflict. Entity-level `valid_from`
(when was this feature captured/created?) and cell-level `valid_from`
(when was the cell's physical reality last confirmed changed?) are
semantically distinct. They answer different temporal questions on
different record types. Pillar 4's temporal ownership model (ADR-016)
is unaffected.

---

## 3. Consequences

### Positive

1. **ISO 19115 compliance.** Structured lineage and `fileIdentifier`
   mapping satisfy ANZLIC metadata profile requirements for Australian
   government data interchange.
2. **ISO 19157 compliance.** Data quality metrics on asset bundles enable
   quality-aware rendering and consumer filtering.
3. **ISO 19111 compliance.** CRS declaration on stored geometry removes
   ambiguity for export consumers.
4. **OGC API compatibility.** `valid_from` mandate and `canonical_id`→`id`
   mapping enable compliant OGC API Features responses.
5. **Licence tracking.** `source_licence` closes a provenance gap — Harmony
   can now assert the licence basis for every piece of data it holds.
6. **Reproducible processing chain.** `process_steps[]` enables full
   lineage reconstruction from source to stored record.

### Negative

1. **Schema migration required.** STD-V01, STD-V02, and STD-V03 require
   additive schema migrations. These are produced, not executed — Mikey
   gate applies.
2. **Ingestion adapter changes.** Every Pillar 2 adapter must emit
   `source_lineage` and populate `valid_from` where mandated. This is
   incremental work on existing adapters, not a rewrite.
3. **Provenance hash update.** ADR-019's `provenance_hash` computation
   must include the `source_lineage` object. Existing hashes for records
   ingested before this change remain valid — they were computed under the
   prior provenance schema.
4. **Transition period.** During migration, both flat fields and
   `source_lineage` coexist. The flat fields are deprecated once all
   adapters are updated.

### Neutral

1. STD-V04 requires no schema change — export layer only.
2. STD-V03 fields are static defaults — no runtime logic changes.
3. STD-V05's quarantine rule for missing `valid_from` uses the existing
   quarantine infrastructure (ADR-021) with existing reason code
   `Q4_SCHEMA_VIOLATION`.

---

## 4. Alternatives Considered

### Alt-A: Lineage as Flat Fields (Reject STD-V01 Structured Object)

Add the three missing fields (`source_licence`, `process_steps`,
`processing_organisation`) as top-level columns alongside the existing
flat provenance fields.

**Rejected.** Seven provenance fields at the top level creates schema
sprawl and obscures the logical grouping. A structured JSONB object
is cleaner, aligns with ISO 19115's lineage model, and is extensible
without migration (additional sub-fields can be added within the JSON
structure).

### Alt-B: Data Quality on Cell Record

Place `data_quality` on `cell_metadata` instead of on asset bundles.

**Rejected.** Described in Section 2.2. Cell-level quality is an
aggregation of representation-level quality. Storing it on the cell
creates a synchronisation obligation and loses per-representation
granularity. Quality belongs where the representation lives.

### Alt-C: Full ISO 19111 CRS Object

Embed a complete CRS definition (datum, ellipsoid, prime meridian,
coordinate system axes) on every cell record.

**Rejected.** Described in Section 2.3. For a single-CRS system,
the authority+code compact form is the ISO-compliant representation.
The full object adds ~500 bytes per record of static, universally
available information. The local ENU frame cannot be expressed as a
static CRS object — it is derived from the cell centroid at runtime.

### Alt-D: valid_from Mandatory on Cell Records

Apply STD-V05's mandate to both entity and cell records.

**Rejected.** Cell-level `valid_from` is governed by ADR-016's temporal
trigger architecture. It reflects real-world change confirmed by official
permit records, not source dataset capture dates. Mandating population at
ingestion would conflict with Pillar 4's temporal ownership model and
would produce semantically incorrect values (ingestion time masquerading
as reality time — the exact failure mode ADR-016 was designed to prevent).

---

## 5. Implementation Constraints

1. **Schema migrations are produced, not executed.** Mikey gate applies
   to all three migrations (STD-V01, STD-V02, STD-V03).
2. **STD-V01 flat-field deprecation is deferred.** The original flat
   provenance fields are not removed until all adapters emit
   `source_lineage`. No adapter is broken by the addition of
   `source_lineage`.
3. **STD-V04 mapping is implemented in the export/API serialisation
   layer.** It must not modify internal data structures.
4. **STD-V05 quarantine rule requires the source dataset manifest to
   declare whether it carries per-feature dates.** The manifest schema
   (Pillar 2 M4) must include a `carries_feature_dates: boolean` field.
5. **`provenance_hash` (ADR-019) must be versioned.** Hashes computed
   before and after `source_lineage` adoption use different input tuples.
   The hash includes a version prefix to distinguish them.

---

## 6. Standards Reference

| Gap ID | Standard | Reference |
|---|---|---|
| STD-V01 | ISO 19115:2014 | Metadata — Lineage (B.2.4.2) |
| STD-V02 | ISO 19157:2013 | Geographic information — Data quality |
| STD-V03 | ISO 19111:2019 | Geographic information — Referencing by coordinates |
| STD-V04 | ISO 19115:2014 | Metadata — fileIdentifier (B.2.1) |
| STD-V05 | OGC API — Connected Systems v1.0 | Temporal properties on features |

---

## 7. Review Date

2026-06-01 — Prior to Pillar 2 Sprint 2 production data writes.

---

*ADR-024 — Geospatial Standards Compliance — Accepted April 29, 2026*
