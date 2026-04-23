# ADR-001 — Layered Identity Model

> **Status:** Accepted (amended v0.1.2 with federation note)
> **Date:** 2026-04-07 (original) · 2026-04-10 (federation amendment)
> **Pillar:** 1 — Spatial Substrate
> **Milestone:** 1 — Identity Schema Lock
> **Deciders:** Builder Agent 1 (Architecture Lead), reviewed by Builder PM/QA Agent
> **Schema Version Affected:** 0.1.1 (original), 0.1.2 (federation note)

---

## Context

Every addressable object in the Harmony Spatial Operating System needs an identifier. The naive approach is one identifier per object: a single string that humans read, systems store, and APIs return.

This collapses under any of the following pressures, all of which apply to Harmony:

1. **Humans want short, memorable references** like `CC-421`. Systems want stable, opaque references that never change. These two requirements are mutually exclusive — short human-friendly strings are scarce, contested, and frequently renamed.

2. **Spatial objects need a deterministic key** that any pipeline can compute from geometry without consulting a database. A random opaque ID cannot serve this purpose because it isn't derivable.

3. **AI systems want descriptive labels** like "high-growth coastal residential zone" that can change as understanding evolves. These labels are not unique, not authoritative, and not suitable as references.

4. **UX surfaces want display names** that read naturally in sentences: "Coastline North Cell". These are not unique either.

5. **External systems will eventually need contract anchors** for blockchain attestation. These have their own format and lifecycle constraints.

A single-identifier system forces every consumer to compromise. Worse, when one consumer's needs change (e.g. a region is renamed), the change cascades into every system that stored that identifier.

---

## Decision

Harmony adopts a **layered identity model** with five distinct layers (six in v0.1.2 with the addition of `known_names`), each owned by a different concern and each with its own mutability rules.

| Layer | Purpose | Mutability | Resolvable? |
|---|---|---|---|
| **Canonical ID** | System truth | Immutable | Yes — primary key |
| **Cell Key** | Substrate truth (cells only) | Immutable, derivable | Yes — secondary index |
| **Human Alias** | Usability | Mutable, namespaced | Yes — within namespace |
| **Friendly Name** | UX display | Mutable | No |
| **Known Names** *(v0.1.2)* | Named-entity resolution | Mutable, multi-valued | Returns ranked candidates |
| **Semantic Labels** | AI / context | Mutable, multi-valued | No |

The layers are **strictly ordered**: when two layers disagree, the higher layer wins. Aliases never override canonical IDs. Friendly names never override aliases. Semantic labels are never authoritative.

The Identity Registry is the single source of truth for the mapping between layers. No service may maintain its own private mapping.

A future sixth layer — **Contract Anchor** — is reserved for blockchain attestation but is out of scope for v0.1.2. Its prefix (`ca_`) is reserved to prevent collisions.

---

## Federation Note (added in v0.1.2)

The phrase "single source of truth" used in this ADR and throughout the identity schema refers to the **logical** registry — the canonical, authoritative source of identity for the Harmony system. It does not commit Harmony to a centralised, single-operator implementation.

The canonical ID format is deliberately compatible with a federated, multi-issuer identity model. Specifically:

- Canonical IDs are opaque and carry no embedded operator, region, or jurisdiction information
- The prefix (`hc_`, `ent_`, etc.) declares object type, not issuer
- The token alphabet (Crockford Base32) is ASCII-safe and URL-safe across any infrastructure
- The generation rules use a CSPRNG, which is implementable identically across operators
- The registry contract (resolve, register, lifecycle) describes a *logical* interface, not a deployment topology

Should Harmony's sovereignty and trust architecture (V1.0 Gap 4) ultimately favour a federated approach — multiple issuers, cross-issuer resolution, jurisdictional partitioning — the identity layer can support it without breaking changes. The work to enable federation would live in the registry deployment topology, not in the canonical ID format.

This note exists to ensure the federation option remains open, consistent with V1.0 Gap 4's "deferred but must not be foreclosed" status. No code change is implied by this note. It is a clarification of intent only.

---

## Consequences

### Positive

- **Renames are cheap.** Changing an alias or friendly name is a single registry update with no cascading effects, because no other system stores those values as references.
- **References are stable.** Foreign keys between records are always canonical IDs, so the reference graph never breaks when humans rename things.
- **Ambiguity is local.** Aliases can collide across namespaces without causing system-wide problems, because the resolution layer always disambiguates.
- **AI labels are non-destructive.** Pillar 4 can attach, change, and remove semantic labels freely without touching identity.
- **Contract anchors fit later.** The reserved prefix means we can introduce blockchain identity in a future milestone without schema migration.
- **Federation remains possible.** The canonical ID format does not foreclose a federated model.

### Negative

- **More fields per record.** A cell record carries five identity-related fields instead of one (six in v0.1.2). Storage cost is real but small (~150–200 bytes/record).
- **Resolution cost.** Looking up an object by alias requires a registry round-trip. Mitigated by aggressive caching at the Alias Resolution Service.
- **Discipline required.** Developers must remember to store canonical IDs as references, not aliases. Enforced by linting and code review.
- **Documentation burden.** Every consumer needs to understand the difference between layers. Mitigated by `identity-schema.md` and the pinned principle.

### Neutral

- The system can be reduced to a flat single-identifier model by ignoring all layers except canonical_id. The layered model is opt-in for consumers that need it.

---

## Alternatives Considered

### A. Single Identifier (UUID Everywhere)

Use a UUID as the only identifier. Aliases and friendly names live in metadata, not in their own resolution layer.

**Rejected because:** there's no resolution path for human-typed references. Every UI would need to implement its own alias-to-UUID lookup, with no consistency across surfaces.

### B. Semantic IDs Only

Use meaningful identifiers like `cc-coastline-north-cell-08`.

**Rejected because:** these IDs change when the meaning changes, breaking every reference. This is the failure mode that motivated the whole layered approach.

### C. Two Layers (Canonical + Display)

Canonical ID plus a single mutable display name. No aliases, no semantic labels, no cell keys.

**Rejected because:** it conflates display names with references (people *will* type `Coastline North Cell` somewhere) and provides no path for the deterministic substrate key that ingestion pipelines require.

### D. Defer the Decision

Build the system with one identifier and refactor later.

**Rejected because:** identity is structural. Every record, foreign key, API contract, and migration depends on the identity model. Refactoring identity post-hoc has historically been the most expensive change in any data platform.

---

## Implementation Notes

- See `identity-schema.md` for the full schema.
- See `id_generation_rules.md` §2 for canonical ID formats.
- See `alias_namespace_rules.md` for the alias layer.
- The cell key layer is covered separately in ADR-004.
- Temporal versioning is covered in ADR-007 (renumbered from ADR-009).
- Named-entity resolution is covered in ADR-008 (renumbered from ADR-010).
- The federation note above clarifies but does not change the technical decision.

---

*ADR-001 — Locked, federation amendment v0.1.2 applied*
