# ADR-021 — Geometry Quarantine Lifecycle

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-23 |
| **Deciders** | Dr. Mara Voss (Principal Architect), Mikey (founder) |
| **Pillar** | 2 — Data Ingestion Pipeline (Milestone 3) |
| **Related ADRs** | ADR-019 (Tier Enforcement), ADR-020 (CRS Normalisation Strategy), ADR-007 (Temporal Versioning) |

---

## Context

The Pillar 2 ingestion pipeline processes real-world geospatial data.
Real-world geospatial data is rarely clean: self-intersecting polygons,
orphaned rings, degenerate edges, out-of-CRS-bounds coordinates,
zero-area polygons, and schema-level attribute anomalies are routine.

A pipeline that treats every anomaly as a hard failure stops on first
bad record — unacceptable for batches of tens of thousands of features
where one bad polygon could abort an entire dataset load. A pipeline
that silently discards bad records loses audit trail — we cannot later
prove what we ingested or what we rejected, and we cannot repair a
corrupted input without re-running from source.

The pipeline needs a third state: records that **cannot enter the
substrate safely but must not be lost**. This ADR defines that state
and its lifecycle.

---

## Decision

### 1. Quarantine is a separate partition, not a flag

Quarantined records are written to a **separate physical partition**
(`cell_metadata_quarantine` and `entity_table_quarantine`), not to the
main tables with an `is_quarantined` flag.

**Why a partition, not a flag:**

- Every query on the main tables is implicitly "non-quarantined" — no
  WHERE clause is needed, no query can accidentally include quarantined
  data. Reviews of hundreds of Pillar 1 queries for a flag predicate are
  unnecessary because the predicate does not exist.
- Quarantine capacity planning is independent of production capacity.
- The quarantine partition can be on a different storage tier with
  different retention and backup characteristics without affecting
  production IO.
- Moving a record between partitions is an explicit operation — visible
  in audit logs, gated on approval where appropriate.

### 2. Six reason codes

Every quarantined record carries a single `quarantine_reason` value
from the following closed set. No free-text; no ambiguity.

| Code | Meaning | Typical trigger |
|---|---|---|
| `Q1_GEOMETRY_INVALID` | Self-intersecting, orphaned ring, non-simple, or otherwise topologically invalid | Shapely/GEOS validation failure |
| `Q2_GEOMETRY_DEGENERATE` | Zero area, zero length, collapsed to point, or below minimum-feature-size threshold | Feature-size filter |
| `Q3_CRS_OUT_OF_BOUNDS` | Coordinates fall outside the declared source CRS's valid range after transform attempt | ADR-020 transform error |
| `Q4_SCHEMA_VIOLATION` | Required attribute missing, type coercion failed, enum value unknown | Manifest validator failure |
| `Q5_PROVENANCE_INCOMPLETE` | Source manifest missing a required provenance field (tier, source_id, source_crs, etc.) | ADR-019 enforcement |
| `Q6_DUPLICATE_UNRESOLVED` | Candidate duplicate of existing record with confidence below auto-merge threshold and above auto-reject threshold | Pillar 2 dedup engine |

Each code is documented with an example payload and a typical remediation
path in the Pillar 2 operations runbook.

### 3. Quarantined records are invisible to consumers

- The Pillar 1 HTTP API **never** returns quarantined records. No flag,
  no parameter, no admin mode. If a consumer needs to inspect
  quarantine, it uses a separate quarantine-review API gated on CISO-
  approved role.
- Quarantined records **do not participate in** cell adjacency,
  parent/child hierarchy, alias resolution, or any derivative index.
  They are an append-only inbox for review, not a shadow registry.
- `cell_metadata_quarantine` rows carry the would-be `cell_key` (if
  derivable) for operator context, but this key is not registered in
  `cell_metadata` and cannot be resolved through any normal path.

### 4. 90-day retention

Quarantined records are retained for **90 days** from ingestion
timestamp. After 90 days:

- Records that have not been reviewed are **hard-deleted** from the
  quarantine partition. A permanent audit-log entry records the deletion
  with the full record content hashed (not the content itself) so the
  existence of the quarantined record is provable without retaining the
  potentially-problematic payload indefinitely.
- Records that have been **manually reviewed and rejected** are deleted
  immediately on rejection, with the same audit-log treatment.
- Records that have been **reviewed and released** (rare — requires
  CISO approval) are removed from quarantine and written to the main
  partition via the normal ingestion path, with full provenance
  metadata preserved and `quarantine_release_event` noted.

The 90-day window is calibrated to give operators time to receive,
diagnose, and request upstream corrections without accumulating
unbounded quarantine debt. Extending retention is gated on CISO
approval per-incident.

### 5. Pipeline continues on quarantine

When a record quarantines, the pipeline **does not abort**. The
batch continues processing the remaining records. At batch end, the
ingestion run report records:

- Total input records
- Records written to main partition
- Records written to quarantine (by reason code)
- Deduplication merges

This is the operational difference between quarantine and error. An
error aborts the batch. A quarantine is a normal, expected outcome
for a minority of records in any real-world dataset.

---

## Consequences

**Positive:**

- Batch-scale ingestion is robust to real-world data messiness without
  silent data loss.
- Quarantine invisibility means the substrate's correctness guarantees
  are never weakened by "has a flag been checked" questions.
- Six-way reason taxonomy makes operator triage tractable — each code
  has a known remediation path.
- 90-day retention bounds the review cost and the storage cost.

**Negative:**

- Two partitions per record type add schema surface area. Migrations
  that change cell/entity shape must touch both.
- Quarantine release (rare but possible) requires the record to be
  re-written through the main ingestion path to guarantee it satisfies
  all ADR-019 tier enforcement checks. This is deliberate but not free.

**Neutral:**

- Quarantine is not a bug tracker. It is an inbox. Operators review,
  decide, and clear. Long-running issues with a source are tracked in
  the dataset registry and the Pillar 2 runbook, not in quarantine
  retention.

---

## Alternatives Considered

**Alt 1: `is_quarantined` flag column on main tables.** Rejected. Every
Pillar 1 query and every downstream pillar's query would need a
`WHERE is_quarantined = FALSE` predicate. Missing one is silent and
corrupting. The separate-partition approach is defensively simpler.

**Alt 2: Drop bad records; log only.** Rejected. Auditability requires
keeping the problematic record long enough to diagnose. A log entry is
not a record — it cannot be re-examined, re-parsed, or released if the
diagnosis reveals the record was actually fine.

**Alt 3: Indefinite quarantine retention.** Rejected. Unbounded
retention of problematic payloads is a privacy and legal liability —
quarantined payloads may include licensing-violating data, PII, or
export-controlled content that the ingestion refusal specifically
identified. 90 days is the calibrated window.

**Alt 4: Single reason code with free-text detail.** Rejected. Free-text
reason codes do not aggregate. Six closed codes allow dashboard
aggregation, reason-code SLOs, and per-reason remediation runbooks.

---

## Implementation Constraints

1. `cell_metadata_quarantine` and `entity_table_quarantine` are created
   in the same migration that lands the Pillar 2 ingestion path. Schema
   shape mirrors the main tables plus `quarantine_reason`,
   `quarantine_timestamp`, and (optionally) `operator_review_notes`.
2. Quarantine-review API is separate from the Pillar 1 resolution API
   and lives under a distinct route prefix (`/quarantine/`) with its
   own auth scope.
3. The 90-day retention job is a 90-DAY deliverable (per ADR-018 /
   Security Foundation tracking). Manual cleanup is acceptable during
   the first operational quarter.
4. Quarantine release requires CISO approval and produces a matched
   audit-log pair: one entry for the quarantine write, one for the
   release.
5. Quarantined records **never** count toward tier coverage metrics
   or the knowledge-density score (ADR-018).

---

*ADR-021 — Accepted — 2026-04-29*
