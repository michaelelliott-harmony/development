# ADR Summary — Binding Decisions for Sprint 1

The following ADRs and Decision Log entries govern this sprint.
Read the full documents for authoritative detail. This is a summary of
what is directly relevant to your modifications.

---

## ADR-018 — Data Tier Model and Provenance Hierarchy

- Source tiers are **1–4 only**. Tier 0 does not exist.
- Tier 1 = field survey / direct measurement
- Tier 2 = published authoritative reference (e.g. NSW government data, OSM)
- Tier 3 = derived / computed
- Tier 4 = synthetic / AI-generated
- `source_tier` is system-assigned and write-once

---

## ADR-019 — Tier Enforcement Architecture

- Tier 4 cannot occupy a structural fidelity slot
- CHECK constraint: `source_tier != 4 OR (structural fidelity fields are NULL)`
- Every adapter must participate in tier authorisation and emit the canonical provenance tuple
- Nightly integrity scan verifies provenance hashes

---

## ADR-020 — CRS Normalisation Strategy

- Canonical CRS: WGS84 (EPSG:4326)
- `source_crs` must be declared — no auto-detect, no default; missing = refuse
- GDA2020→WGS84 via NTv2 grid shift (GDA94_GDA2020_conformal.gsb)
- Every record carries: `source_crs`, `crs_transform_epoch`, `transformation_method`

---

## ADR-021 — Geometry Quarantine Lifecycle

- Quarantine is a separate physical partition, not a flag
- Six reason codes: Q1_GEOMETRY_INVALID, Q2_GEOMETRY_DEGENERATE, Q3_CRS_OUT_OF_BOUNDS, Q4_SCHEMA_VIOLATION, Q5_PROVENANCE_INCOMPLETE, Q6_DUPLICATE_UNRESOLVED
- 90-day retention with hard-delete and audit-log entry
- Pipeline continues on quarantine — batches do not abort

---

## ADR-022 — Rendering Asset Format and Data Contract

Key points for Sprint 1:

**Tier range:** Source tiers are 1–4. Tier 0 does not exist. Tier 4 cannot
be `available` in photorealistic or structural fidelity.

**data_quality object:** Lives on the **asset bundle record**, NOT the cell
record. Three nullable sub-fields: `completeness_percent`, `positional_accuracy_metres`,
`last_validated`. (Dr. Voss ruling — DEC-020.)

**field_descriptors:** Must be present as an **empty JSONB object** on the
cell payload at ingestion time. It must NOT be populated at ingestion.
(ADR-023 / ADR-017 constraint.)

**fidelity_coverage structure:**
```json
{
  "photorealistic": {"status": "pending|available|splat_pending", "source_tier": 1-4 or null, "confidence": 0.0-1.0, "timestamp": "ISO8601"},
  "structural":     {"status": "pending|available|splat_pending", "source_tier": 1-4 or null, "confidence": 0.0-1.0, "timestamp": "ISO8601"}
}
```

**geometry_inferred = true → photorealistic.status MUST be "splat_pending"** (schema-level constraint).

---

## ADR-024 — Geospatial Standards Compliance

This ADR resolves five gaps (STD-V01 through STD-V05). All five apply to
your modifications.

### STD-V01 (ISO 19115) — source_lineage JSONB object

Replace flat `source` field on entity and cell-populating records with a
structured `source_lineage` JSONB object containing **seven sub-fields**:

```json
{
  "source_lineage": {
    "source_dataset_id":       "string — NOT NULL",
    "source_dataset_date":     "date — NULLABLE",
    "source_organisation":     "string — NOT NULL",
    "source_licence":          "string — NOT NULL (SPDX identifier, e.g. 'CC-BY-4.0')",
    "process_steps": [
      {
        "step_name":        "string",
        "step_description": "string",
        "step_datetime":    "datetime"
      }
    ],
    "processing_organisation": "string — NOT NULL (default: 'harmony')",
    "processing_date":         "datetime — NOT NULL"
  }
}
```

**Migration note:** The old flat fields (`source_authority`, `source_dataset`,
`observation_date`, `ingested_at`) map into this object per ADR-024 §2.1.
During the migration window both flat fields and `source_lineage` coexist.
You are adding `source_lineage` — not removing flat fields yet.

### STD-V02 (ISO 19157) — data_quality on asset bundle

`data_quality` goes on **asset bundle records**, not cell records.
Dr. Voss ruling is explicit. Implementation point: `runner.py` when building
the asset bundle record. Do NOT put `data_quality` on cell records.

### STD-V03 (ISO 19111) — CRS fields on geometry records

Add `crs_authority` (TEXT, default `'EPSG'`) and `crs_code` (INTEGER, default
`4326`) to cell geometry records. Implementation point: `normalise.py`.

### STD-V04 — canonical_id as fileIdentifier

Mapping rule only — export/serialisation layer, not this sprint. No code
change required from you.

### STD-V05 (OGC) — valid_from mandatory where source carries feature date

`valid_from` on entity records is **mandatory** when the source dataset carries
a per-feature date. Records with missing `valid_from` from a date-carrying
dataset → quarantine (Q4_SCHEMA_VIOLATION). Null is only permitted when the
source dataset genuinely provides no per-feature dates.

The source dataset manifest must declare `carries_feature_dates: boolean`.

---

## DEC-021 — Terminology: `structural` not `schematic`

The geometry fidelity slot is named `structural` throughout. Never use
`schematic`. This is enforced across all ADRs, tests, and code.

---

## DEC-017 — PATCH /cells/{cell_key}/fidelity Endpoint

The fidelity PATCH endpoint is live in Pillar 1 as of the last sprint.
The fidelity hook in `runner.py` (currently commented out) **should be
wired in** when the cell is registered. The commented `self._p1.patch_cell_fidelity(...)` block in `runner.py` is your implementation target.
Confirm `p1_client.py` exposes `patch_cell_fidelity` or implement it.

---

## DEC-013 / DEC-014

- `source_tier` is system-assigned, write-once, non-mutable
- `source_crs` must always be explicitly declared by adapters
