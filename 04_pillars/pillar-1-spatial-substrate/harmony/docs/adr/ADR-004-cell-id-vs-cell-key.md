# ADR-004 — `cell_id` vs `cell_key`

> **Status:** Accepted
> **Date:** 2026-04-07
> **Pillar:** 1 — Spatial Substrate
> **Milestone:** 1 — Identity Schema Lock
> **Deciders:** Agent 1 (Architecture Lead), Agent 4 (Spatial Substrate Engineer)
> **Schema Version Affected:** 0.1.1
> **Related:** ADR-001 (Layered Identity)

---

## Context

Cells are the foundational unit of the Harmony Spatial Substrate. Every cell needs an identifier. The question is: what kind?

Two competing requirements pull in opposite directions.

**Requirement A — Identity Stability.** A cell needs an identifier that never changes, never depends on the cell's contents, and serves as a reliable foreign key for every other system in Harmony. This argues for an opaque, randomly-generated identifier like a UUID.

**Requirement B — Deterministic Reproducibility.** Ingestion pipelines, rendering systems, and debugging tools all need to compute "what cell does this geometry belong to?" without consulting a database. If the answer requires a registry lookup, the substrate becomes a bottleneck for every spatial operation in the system. This argues for a deterministic identifier that any process can derive from geometry alone.

These requirements cannot be served by the same identifier:

- A random UUID is stable but cannot be derived from geometry
- A deterministic hash of geometry can be derived but is not stable (any geometry refinement changes the ID)

The naive workaround — "just use the deterministic hash as the ID" — fails the moment a cell's geometry is corrected, snapped to a finer grid, or migrated to a different indexing scheme. Every reference in the system would silently break.

The opposite workaround — "always look up cells through the registry" — turns the registry into a global hot path. Every ingestion job, every rendering frame, every spatial join would block on a network call.

---

## Decision

**Every cell carries both an identifier and a key.**

| Field | Type | Stable? | Derivable? | Used As |
|---|---|---|---|---|
| `cell_id` | Opaque token (`hc_4fj9k2x7m`) | Yes | No | Foreign key, primary identifier |
| `cell_key` | Deterministic string (`hsam:r08:cc:a91f2`) | Yes (per geometry+level) | Yes | Spatial joins, debugging, idempotency |

Both fields are **mandatory** on every cell record. Neither is optional. A cell without a `cell_key` is rejected at write time. A cell without a `cell_id` cannot exist by definition.

The relationship between the two:

- **`cell_id` is the primary key.** All foreign keys in Harmony reference `cell_id`, never `cell_key`.
- **`cell_key` is a unique secondary index.** Two cells with the same geometry and resolution must have the same `cell_key`. The registry enforces uniqueness on `cell_key`.
- **`cell_key` makes registration idempotent.** Re-registering the same geometry returns the existing `cell_id`.
- **`cell_key` is debuggable.** Engineers can look at a `cell_key` and immediately see the resolution and region. Engineers cannot do that with `cell_id`.

When the underlying spatial indexing scheme changes (the open question H3 vs custom in the master spec), the `cell_key` format may need to evolve. The `cell_id` does not change. This isolates the substrate change from the rest of the system.

---

## Consequences

### Positive

- **Substrate operations are registry-free.** A pipeline can compute `cell_key` from raw geometry, batch-lookup the corresponding `cell_id` once, and then operate locally.
- **Idempotent ingestion.** Re-running an ingestion job produces the same cell IDs without duplicates, because the registry deduplicates on `cell_key`.
- **Debugging is dramatically easier.** A `cell_key` like `hsam:r08:cc:a91f2` tells you the resolution and region at a glance. An opaque `hc_` ID does not.
- **Substrate evolution is isolated.** Changing the indexing scheme is a `cell_key` migration. References (which use `cell_id`) are untouched.
- **Spatial joins are fast.** Two datasets joined on `cell_key` need no registry calls.

### Negative

- **Two fields per cell.** Storage and validation cost is real. Mitigated by the fact that both fields are short.
- **Two failure modes.** A bug in `cell_key` derivation produces silent duplication. A bug in `cell_id` generation produces collision errors. Both must be tested independently.
- **Determinism is a hard constraint.** Every implementation of `cell_key` derivation must produce byte-identical results. This requires careful handling of floating-point geometry, snap-to-grid, and hash function selection. See `id_generation_rules.md` §4.2.
- **Region codes are required.** `cell_key` includes a region segment, which requires a registered region table. The fallback `gbl` exists but is logged as a warning.

### Neutral

- A future migration to a different hash function or indexing scheme is possible without breaking external references — only `cell_key` values change.

---

## Alternatives Considered

### A. `cell_id` Only (No Key)

Use only an opaque `hc_` identifier. Spatial joins go through the registry.

**Rejected because:** the registry becomes a single point of contention for every spatial operation. Performance and reliability both suffer. Idempotent ingestion becomes impossible without per-job state.

### B. `cell_key` Only (No ID)

Use only the deterministic key. Drop the opaque identifier.

**Rejected because:** when the indexing scheme evolves, every foreign key in the system breaks. There is no path forward without a full migration of every dataset, every entity reference, and every external system that has ever stored a cell reference.

### C. `cell_id` is the Hash of Geometry

Make the canonical ID itself deterministic.

**Rejected because:** this is identical to "key only" with extra steps. Refining a cell's geometry produces a new canonical ID, breaking everything that referenced the old one.

### D. Defer the Key Until Pillar 2

Build cells with only an ID for v0.1.1 and add the key later when ingestion needs it.

**Rejected because:** retrofitting `cell_key` onto existing cells requires deciding what to do with cells whose original geometry has been lost or refined. There is no clean migration. The brief explicitly locks `cell_key` into Milestone 1 for this reason.

---

## Implementation Notes

- The `cell_key` derivation algorithm is defined in `id_generation_rules.md` §4.2. It is canonical: any implementation that diverges produces silently incompatible data and is a P0 bug.
- `cell_key` is a UNIQUE constraint in the `cell_metadata` table.
- The Cell Key Derivation Module (Component 3.5 in the brief) is owned by Agent 4.
- Test vectors for determinism live in `id_generation_rules.md` §10.

---

*ADR-004 — Locked*
