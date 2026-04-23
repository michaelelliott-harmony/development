# ADR-019 — Tier Enforcement Architecture

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | 2026-04-23 |
| **Deciders** | Dr. Mara Voss (Principal Architect), Mikey (founder) |
| **Pillar** | 2 — Data Ingestion Pipeline |
| **Related ADRs** | ADR-018 (Data Tier Model and Provenance Hierarchy), ADR-007 (Temporal Versioning), ADR-010 (Spatial Geometry Schema Extension) |

---

## Context

ADR-018 establishes the four-tier data model (Tier 1 Authoritative, Tier 2
Open Authoritative, Tier 3 ML-Derived/Commercial, Tier 4 Generated
Knowledge) and commits the substrate to carrying `source_tier`,
`source_id`, and `confidence` on every cell element.

ADR-018 is the policy. This ADR is the enforcement mechanism. Without
explicit enforcement at the write path, tier metadata drifts — agents can
forget to populate it, downstream consumers can mutate it, and Tier 4
content can leak into structural fidelity slots. Each of these failures
is silent and compounds over time, making retroactive detection
expensive.

The question this ADR resolves: how does Harmony guarantee, at the
schema and ingestion-path level, that every record is correctly tier-
tagged, tamper-evident, and that Tier 4 generated knowledge can never
occupy a structural or photorealistic fidelity slot?

---

## Decision

### 1. Tier tags are system-assigned and write-once

- `source_tier`, `source_id`, and `confidence` are populated **only** by
  the ingestion pipeline at the moment of first write. No agent or API
  consumer sets them directly.
- Once written, the triple is **immutable**. There is no update path.
  Corrections flow through **supersession** — a new record with a new
  canonical ID, the prior record marked `superseded` via the ADR-007
  temporal fields.
- The ingestion adapter that produced the record is the authority on its
  own tier assignment. The pipeline verifies the adapter is registered
  and tier-authorised before accepting the write.

### 2. Provenance hash: SHA-256, signed by the ingesting agent

Every record carries a `provenance_hash` column containing a SHA-256
hash of the canonicalised provenance tuple:

```
SHA-256(source_tier || source_id || source_record_id || ingesting_agent_id || ingestion_timestamp)
```

The hash is computed by the ingestion pipeline, stored alongside the
record, and recorded in the ingestion-run audit log. Any mutation of any
component field invalidates the hash and is detectable via a batch
integrity scan.

The hash is not a substitute for the ADR-007 temporal version_of
chain — it complements it. Temporal fields prove *when* a record
changed; the provenance hash proves *from where and by whom* it
originally came.

### 3. Tier 4 CHECK constraint — hard firewall on structural fidelity

A database CHECK constraint, enforced at the cell-and-entity schema
level, prevents Tier 4 generated knowledge from ever occupying a
structural or photorealistic fidelity slot:

```sql
CHECK (
    source_tier != 4
    OR (
        structural_fidelity_class IS NULL
        AND structural_fidelity_score IS NULL
        AND structural_fidelity_source IS NULL
    )
)
```

Equivalent constraints apply to the photorealistic fidelity fields once
Pillar 3 defines them. The constraint is additive to the application-
layer safety firewall described in ADR-018 — belt and braces.

### 4. Default read-path filter

The substrate read API defaults every query to `source_tier <= 3`.
Autonomous consumers receive no Tier 4 content unless they pass an
explicit `include_generated_knowledge = true` flag and the query path
explicitly does not touch structural or photorealistic fidelity fields.
This is enforced in the Pillar 4 machine query interface.

### 5. Integrity verification

A nightly job recomputes `provenance_hash` for a rolling sample of
records (1% stratified by tier) and compares against the stored value.
Any mismatch triggers an immediate CISO-routed incident — it indicates
either a bug in the hash computation, a silent mutation of a component
field, or a compromise.

---

## Consequences

**Positive:**

- Tier assignment becomes a property of the write, not a convention.
  Consumers cannot forge it, retag it, or silently mutate it.
- Tier 4 cannot contaminate safety-critical fidelity slots by any code
  path — the constraint is declarative and impossible to bypass without
  a schema migration that itself is gated on approval.
- `provenance_hash` is cheap to compute (SHA-256 on a short string),
  cheap to store (32 bytes), and gives tamper-evidence for free.
- Aligns cleanly with the append-only bitemporal model from ADR-007 —
  corrections are supersessions, not mutations.

**Negative:**

- Every ingestion adapter must participate in the tier-authorisation
  registry and must emit the canonical provenance tuple. One new piece
  of coordination per source.
- The CHECK constraint means any future extension of the fidelity
  schema (new fidelity classes, new source kinds) needs a coordinated
  migration to extend the constraint — it is not trivially forward-
  compatible for new fidelity dimensions.

**Neutral:**

- MVP ingests Tier 1 only; the enforcement mechanism is fully wired
  from day one even though Tier 2/3/4 are not yet in the pipeline.
  Carrying the enforcement from the start is the whole point — it
  costs almost nothing now and is nearly impossible to retrofit later.

---

## Alternatives Considered

**Alt 1: Application-layer tier check only (no DB constraint).** Rejected.
A single bug in the write path can let Tier 4 reach a structural slot,
and the resulting corruption is silent. The DB constraint is the only
layer that cannot be bypassed by an application-code mistake.

**Alt 2: Mutable tier tags with an audit trail.** Rejected. Audit trails
tell you *when* something changed. They don't prevent an upstream
consumer from silently retagging Tier 3 content as Tier 1 and having
downstream systems treat it with unearned authority. Immutability is
cheaper than forensic investigation.

**Alt 3: Per-record signature instead of SHA-256 of provenance tuple.**
Deferred, not rejected. Full record signing is on the ADR-018 roadmap
(SP-II.4, marked `[RESERVED]`). SHA-256 of the provenance tuple is the
interim control — it detects tampering of the tier-critical fields
without requiring the signing infrastructure to be live.

---

## Implementation Constraints

1. Tier authorisation registry must exist before the first Pillar 2
   ingestion adapter is registered. Owner: Dr. Voss + Elena.
2. CHECK constraint must land in the same migration that adds the
   tier/provenance columns to `cell_metadata` and the equivalent entity
   table — not a follow-up. Co-shipping prevents a window where Tier 4
   writes could succeed.
3. Nightly integrity job is a 90-day deliverable (per ADR-018 tracking).
   Manual spot-checks are acceptable during MVP.
4. The read-path filter default is the responsibility of the Pillar 4
   machine query layer — Pillar 2 carries the metadata; Pillar 4 honours
   the default.

---

*ADR-019 — Proposed — 2026-04-23*
