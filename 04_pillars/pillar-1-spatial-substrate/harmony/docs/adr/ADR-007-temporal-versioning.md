# ADR-007 — Temporal Versioning Model

> **Status:** Accepted (reserved fields, design intent locked, implementation deferred)
> **Date:** 2026-04-10
> **Pillar:** 1 — Spatial Substrate
> **Milestone:** 1 Amendment (v0.1.2)
> **Deciders:** Builder Agent 1 (Architecture Lead)
> **Schema Version Affected:** 0.1.2
> **Closes:** Master Spec V1.0 Gap 3
> **Related:** ADR-001 (Layered Identity)

---

## Context

The physical world changes. Buildings are demolished and rebuilt. Parcels are subdivided. Roads are rerouted. Coastlines shift. Vegetation is cleared and replanted. The Harmony Spatial Knowledge Layer (Pillar 4) and the Spatial Knowledge Interface (Pillar 5, V1.0 North Star III) both depend on being able to ask: *what existed at this place at this time?*

V1.0 Gap 3 makes this an explicit requirement: **cell schemas and HCID structures must be confirmed capable of supporting temporal versioning without breaking changes before ingestion begins at scale.**

This is the kind of requirement that sounds optional until ingestion runs, at which point it becomes structurally impossible to add later without rewriting every record. The decision must be made — at least at the schema level — in Pillar 1, even though the active implementation lives in Pillar 4.

The motivating scenario from the V1.0 update discussion:

> *A building is demolished and rebuilt on the same parcel. The user asks the Conversational Spatial Agent: "What was here before the new tower went up?" The system needs to retrieve the historical building, render it (or at least describe it accurately), and place it in temporal context — without that historical building's record having been overwritten or deleted.*

This implies four capabilities the schema must support without breaking changes:

1. A record can be marked as no-longer-current without being deleted or retired
2. A new record can declare itself as a temporal successor to an old one
3. Each record can carry real-world validity timestamps independent of its registry creation timestamp
4. Queries can ask "what was the state of this place at time T" and get answers

---

## Decision

Harmony adopts a **bitemporal versioning model** at the schema level. Cell and entity records carry four reserved temporal fields in v0.1.2:

| Field | Type | Purpose |
|---|---|---|
| `valid_from` | timestamp / null | When this version became valid in the real world |
| `valid_to` | timestamp / null | When this version ceased to be valid in the real world |
| `version_of` | canonical_id / null | If this is a new version of an existing object, the canonical ID of the prior version |
| `temporal_status` | enum / null | One of `current`, `historical`, `superseded`, `projected` |

### What "bitemporal" means here

The schema distinguishes two timelines:

1. **System time** — when the registry knows about something. Captured in `created_at` and `updated_at`. Already in v0.1.1.
2. **Valid time** — when something is true in the real world. Captured in `valid_from` and `valid_to`. New in v0.1.2 (reserved).

A record can be created in the registry today (`created_at = 2026-04-10`) describing a building that existed from 1880 to 1972 (`valid_from = 1880-01-01`, `valid_to = 1972-12-31`, `temporal_status = historical`). The two timelines are independent.

### Status field separation

The new `temporal_status` is **distinct** from the existing lifecycle `status` field (§5 of identity-schema.md). They describe different things:

| Field | Describes | Example values |
|---|---|---|
| `status` | The **registry lifecycle** of the record | `pending`, `active`, `deprecated`, `retired` |
| `temporal_status` | The **temporal version** the record represents | `current`, `historical`, `superseded`, `projected` |

A record can be `status: active, temporal_status: historical` — meaning the record is fully resolvable in the registry, but it represents a historical version of the object. This is the normal state for a demolished building whose record is preserved for historical queries.

### Version chains

When a building is demolished and a new building is constructed on the same parcel, the system has a choice:

**Option A — Same canonical_id, version chain:** Treat the new building as a new version of the old one. Set `version_of` on the new record pointing to the old, mark the old record `temporal_status: superseded`. Use this when there is meaningful continuity (same legal entity, same parcel registration, same address).

**Option B — Separate canonical_ids, no chain:** Treat the new building as a fundamentally different object. Mark the old record `temporal_status: historical` with a `valid_to` timestamp. Create the new record fresh with `valid_from` and `temporal_status: current`. Use this when there is no meaningful continuity (different owners, different use, completely different structure).

The choice is a **Pillar 4 / domain-knowledge decision**, not a Pillar 1 schema decision. Pillar 1 supports both patterns. Pillar 4 will codify when each applies.

### Reserved status for v0.1.2

These fields are **reserved**, not active, in v0.1.2. The registry rejects writes to them with `403 Reserved` until Pillar 4 formally activates them. The fields exist now solely to ensure forward-compatibility.

This is a deliberate choice: locking the field names, types, and semantics in v0.1.2 means Pillar 4 can activate them without a breaking schema change. Every cell and entity record written in v0.1.2 carries the reserved fields as `null`, and when Pillar 4 lands, those nulls are interpreted as "always-current, no temporal versioning applied yet."

---

## Consequences

### Positive

- **Forward-compatible.** Pillar 4 can implement temporal versioning without a breaking change. Records written today will work transparently when temporal becomes active.
- **Scenario-complete.** The bitemporal model handles every realistic scenario the team has surfaced — demolitions, rebuilds, subdivisions, projections, historical reconstructions.
- **Honours Gap 3.** The V1.0 requirement is satisfied at the schema level before ingestion begins at scale.
- **Decoupled from lifecycle.** Keeping `status` and `temporal_status` separate avoids the trap of overloading the lifecycle field, which is what every system that conflates them eventually regrets.
- **Supports the Knowledge Interface.** North Star III's "the world transforms around the answer" requires historical state. This schema makes that possible.

### Negative

- **Four extra fields per record.** Storage cost is real but small. Mitigated by the fact that they are nullable and most records will carry nulls until Pillar 4 lands.
- **Cognitive complexity.** Developers must understand the difference between `status` and `temporal_status`. Mitigated by clear documentation and the fact that v0.1.2 doesn't actually require anyone to use temporal_status yet.
- **Reserved fields look load-bearing.** Future readers may try to write to them. Mitigated by `403 Reserved` enforcement at the registry layer.
- **Pillar 4 is committed to bitemporal.** Once these field names and semantics are locked, Pillar 4 must build a temporal engine that matches them. This forecloses some alternative temporal models.

### Neutral

- The model is influenced by SQL:2011 bitemporal tables and event-sourcing patterns. It is well-trodden ground.

---

## Alternatives Considered

### A. Single Timestamp Model

Just `as_of` and call it done.

**Rejected because:** it conflates system time with valid time. A building demolished in 1972 but added to the registry in 2026 cannot be represented correctly with a single timestamp.

### B. Temporal as a Separate Table

Keep cells flat in v0.1.2. Add a `cell_versions` table later that holds all historical versions, with current cells as a view.

**Rejected because:** it requires Pillar 4 to migrate data, and it creates two sources of truth (the cells table and the cell_versions table). The bitemporal-on-the-record model has been industry-validated for decades.

### C. Defer All Temporal Decisions

Don't reserve fields. Let Pillar 4 design temporal from scratch.

**Rejected because:** this is exactly the failure mode V1.0 Gap 3 was created to prevent. By the time Pillar 4 lands, ingestion may have already populated millions of records, and adding temporal fields after the fact is a breaking migration.

### D. Use a Dedicated Time-Series Database

Push all temporal state to InfluxDB or similar.

**Rejected because:** time-series databases are optimised for high-frequency numeric metrics, not for versioning structured records with relationships. The wrong tool for this job.

---

## Implementation Notes

- The fields are reserved in `cell_identity_schema.json` and `entity_identity_schema.json` as of v0.1.2.
- The registry must reject writes to these fields until Pillar 4 sends a formal activation signal (mechanism TBD by Pillar 4).
- The reading-side query API for temporal queries (e.g. `?as_of=1995-06-01`) is reserved in the resolution service spec.
- When Pillar 4 activates temporal versioning, it must produce its own ADR documenting the activation and any refinements to the model defined here.

---

*ADR-007 — Locked at the schema layer; implementation deferred to Pillar 4*
