# ADR-011 — Gate 3 Closure: Identity Generation Order

> **Status:** Accepted — Closes V1.0 Gate 3
> **Date:** 2026-04-10
> **Pillar:** 1 — Spatial Substrate
> **Milestone:** 3 (closes before Milestone 4 / Alias System)
> **Deciders:** Builder Agent 1 (Architecture Lead), confirmed by Mikey (Founder/PM)
> **Closes:** Original Agent Analysis Gate 3 — "Identity encoding / token generation method"

---

## Context

Gate 3 is one of the eight open decision gates from the original `harmony-agent-analysis.md`. Its scope, as originally framed, was: *what is the exact method by which Harmony generates its identity tokens?*

By the time of Session 3, most of Gate 3's substance had already been resolved in pieces, but never in one place. The Session 3 brief flagged this as blocking Session 4 (Alias System), because the alias layer mints canonical IDs at scale and needs a locked answer on generation order.

This ADR consolidates the decisions, confirms the registration order, and formally closes Gate 3.

---

## What Was Already Decided

Prior to this ADR, the following were already locked:

- **Canonical ID formats** — `hc_[a-z0-9]{9}$` for cells, `ent_[a-z]{3}_[a-z0-9]{6}$` for entities. Locked in `id_generation_rules.md` §2.
- **Token alphabet** — Crockford Base32, excluding `i`, `l`, `o`, `u`. Locked in §3.
- **Randomness source** — CSPRNG only (`secrets.token_bytes`, `crypto.randomBytes`, `OsRng`). Locked in §6.
- **Collision handling** — database `UNIQUE` constraint plus application check. Maximum 3 regeneration attempts before escalation. Locked in §7.
- **Cell key derivation** — BLAKE3 → 80 bits → 16 Crockford Base32 characters. Locked in Session 2 (ADR-003) and Session 2 D3.

Gate 3 was not blocked on any of these. It was blocked on the **interaction between them** at registration time.

---

## Decision

### 1. Cell Registration Order

```
1. Caller provides geometry G and resolution level L
2. Compute cell_key = derive_cell_key(G, L)   [deterministic, no DB access]
3. Query registry for existing record with cell_key
   3a. If found → return existing canonical_id (idempotent path)
   3b. If not found → continue
4. Generate candidate canonical_id via CSPRNG
5. Attempt atomic INSERT with (canonical_id, cell_key, ...)
   5a. On UNIQUE violation for canonical_id → regenerate, retry (max 3)
   5b. On UNIQUE violation for cell_key → another writer inserted concurrently;
       re-query step 3 and return that writer's canonical_id (preserves idempotency)
   5c. On success → return canonical_id
6. If 3 retries exhaust → escalate as P0 incident
```

The critical property is **idempotency against geometry**: the same `(G, L)` input always produces the same `cell_id`, regardless of how many times registration is called or how many writers are concurrent. This property is guaranteed by computing `cell_key` first and using the database's `UNIQUE` constraint on `cell_key` as the concurrency boundary.

### 2. Entity Registration Order

```
1. Caller provides object_type "entity" and subtype S
2. Validate S is in registered entity subtype list
3. Generate candidate token via CSPRNG
4. Assemble: ent_{S}_{token}
5. Attempt atomic INSERT
6. On UNIQUE collision → regenerate (max 3)
7. On success → return canonical_id
```

Entity IDs are **not idempotent against geometry**. Registering the same building twice produces two distinct entity IDs. Deduplication is the responsibility of the ingestion pipeline (Pillar 2), not the identity layer. This decision was confirmed by Mikey in the Gate 3 resolution session: entity idempotency is kept out of the identity layer to avoid forcing early schema commitments about what constitutes a "natural key" across heterogeneous ingestion sources.

### 3. Alias Registration Order

```
1. Caller provides canonical_id, alias string, alias_namespace
2. Validate alias matches format regex
3. Validate namespace is registered
4. Attempt atomic INSERT into alias_table with partial unique constraint
   UNIQUE (alias, alias_namespace) WHERE status = 'active'
5. On collision → return 409 Conflict (do not regenerate; alias was caller-provided)
6. On success → return bound tuple
```

Aliases are not generated randomly by the registry — they are either caller-provided or auto-generated from a per-namespace counter (see `alias_namespace_rules.md` §9). Collisions are returned as errors, not retried, because an alias collision is a caller-visible conflict, not a system-level coincidence.

### 4. Reserved Object Type Registration

`dataset`, `state`, and `contract_anchor` canonical IDs follow the entity pattern (purely random tokens, no geometric derivation, no idempotency). Their registration order is identical to entities, with the appropriate prefix. Registration of these types is blocked until the owning pillar formally activates them.

---

## Consequences

### Positive

- **Gate 3 is formally closed.** Session 4 can begin without ambiguity on registration semantics.
- **Idempotency is guaranteed where it matters** (cells) and correctly not attempted where it doesn't (entities).
- **Concurrency is handled explicitly.** The two UNIQUE constraints (on `canonical_id` and on `cell_key`) are the concurrency boundary. No race conditions in the registration path.
- **The distinction is documented.** Future readers understand why cells and entities have different registration semantics.

### Negative

- **Entity deduplication is pushed to Pillar 2.** This is a real burden on ingestion pipelines, which must track source-system identifiers and detect re-ingestion. Acceptable because Pillar 2 has the domain context (source system, record timestamps) that entity identity lacks.
- **Alias collisions are caller-visible.** Callers must handle `409 Conflict` and choose an alternative. Acceptable because aliases are human-readable and collisions should be surfaced, not silently resolved.

### Neutral

- None of these decisions change the schema. They formalise behaviour that was already implied.

---

## Alternatives Considered

### A. Compute `cell_id` Deterministically from Geometry

Make cell canonical IDs themselves a hash of geometry. No random token.

**Rejected because:** this conflates the dual-identifier principle in ADR-004. If `cell_id` were derived from geometry, any geometry refinement would break every foreign key that ever referenced the old cell. The whole reason `cell_id` and `cell_key` are separate is to decouple stability from reproducibility.

### B. Natural-Key Entity Idempotency

Require every entity registration to include a natural key (e.g. source-system ID + source-system name) and make entity registration idempotent against that natural key.

**Rejected because:** natural keys across ingestion sources are messy. A building may exist in cadastral data, satellite derivation, and manual entry simultaneously, with no shared identifier. Forcing the identity layer to normalise these would require domain knowledge it doesn't have. Pillar 2 is the correct owner.

### C. Defer Gate 3 Further

Keep the gate open until Pillar 2 begins.

**Rejected because:** Session 4 (Alias System) cannot proceed without the alias registration order being locked, and the alias registration order depends on the cell registration order. The gate must close now.

---

## Implementation Notes

- The registration logic is already implemented in `harmony/packages/registry/src/registry.py` (Session 3). This ADR codifies the design; it does not require code changes.
- The `UNIQUE` constraint on `cell_metadata.cell_key` is the concurrency boundary for cell idempotency.
- The `UNIQUE` constraint on `identity_registry.canonical_id` is the collision boundary for all canonical IDs.
- Session 4 must implement the alias namespace counter (`alias_namespace_rules.md` §9) as part of the Alias System milestone.

---

## Gate 3 — Formally Closed

As of this ADR, **V1.0 Gate 3 (Identity encoding / token generation method) is closed.** The open gate list for Pillar 1 reduces to:

- Gate 1 — Rendering framework (Pillar 3, separate chat)
- Gate 2 — Machine query latency target (reserved at schema layer; target value pending pre-Pillar-4)
- Gate 4 — Sovereignty and trust (preserved, federation-compatible)
- Gate 6 — Commercial model for machine substrate (non-blocking)

Gates 5, 7, 8 are closed or deferred per prior ADRs.

---

*ADR-011 — Locked*
