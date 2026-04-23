# ADR-006 — Alias Namespace Model

> **Status:** Accepted
> **Date:** 2026-04-07
> **Pillar:** 1 — Spatial Substrate
> **Milestone:** 1 — Identity Schema Lock
> **Deciders:** Agent 1 (Architecture Lead), Agent 3 (Alias Systems Engineer)
> **Schema Version Affected:** 0.1.1
> **Related:** ADR-001 (Layered Identity)

---

## Context

ADR-001 establishes that human-friendly aliases (e.g. `CC-421`) live in their own identity layer, separate from canonical IDs. Aliases exist so people can talk about cells, parcels, and entities without typing opaque tokens.

This raises an immediate question: **what happens when two regions both want to call something `CC-421`?**

A real example: "Central Coast" exists in NSW Australia, in California, in Queensland, and in several other places. If aliases are globally unique, the first region to register `CC-` claims the prefix forever, and every other region needs an awkward suffix. Worse, the first region's claim is visible everywhere — `CC-421` resolving to a NSW cell in a Queensland UI is actively confusing.

If aliases are not unique at all, the system can't resolve them — `CC-421` becomes ambiguous and the resolution layer either guesses (dangerous) or returns multiple results (forces every consumer to disambiguate).

The general problem is that aliases live in a flat global string space by default, but the meaning of an alias is intrinsically scoped to a context. The model needs to make that scope explicit.

---

## Decision

Aliases live in **hierarchical dotted namespaces**. The unit of identity at the alias layer is the tuple `(alias, namespace)`, not the alias alone.

### Namespace Format

```
<country>.<state>.<region>.<object_class>[.<sub_class>]
```

Examples:

```
au.nsw.central_coast.cells
au.nsw.central_coast.cells.coastal
au.qld.cairns_coast.cells
us.ca.monterey.cells
```

### Resolution Rules

1. **Every alias resolution call must specify a namespace.** The Alias Resolution Service never guesses. Calls without a namespace return `400 Bad Request`.
2. **Aliases are unique within a namespace.** Active aliases collide locally and the registry rejects duplicates.
3. **Aliases may repeat across namespaces.** `CC-421` in `au.nsw.central_coast.cells` and `CC-421` in `au.qld.cairns_coast.cells` are two distinct bindings to two distinct canonical IDs.
4. **Namespaces are hierarchical but not inherited.** A cell registered in `au.nsw.central_coast.cells` is NOT automatically resolvable in `au.nsw.central_coast.cells.coastal`. Each namespace is independent.
5. **Namespaces are registered.** Creating a new namespace requires a registry entry. This prevents typo-namespaces from silently shadowing real ones.

### Reserved Top-Level Segments

| Segment | Purpose |
|---|---|
| `global` | Cross-region objects |
| `system` | Internal Harmony objects |
| `test` | Test fixtures — never resolvable in production |

### Database Enforcement

Uniqueness is enforced with a partial unique constraint:

```sql
UNIQUE (alias, alias_namespace) WHERE status = 'active'
```

This allows the same `(alias, namespace)` tuple to appear multiple times in history (one active, several retired) without violating the constraint.

---

## Consequences

### Positive

- **Regional autonomy.** Every region picks its own prefixes without negotiating globally. Central Coast NSW and Central Coast California both use `CC-` happily.
- **Resolution is unambiguous.** Given a namespace, an active alias resolves to exactly one canonical ID. No guessing, no multiple-result responses.
- **Failure modes are loud.** Calling without a namespace fails fast at the API layer, surfacing the problem before it causes silent misresolution.
- **Migration is local.** Renaming a namespace affects only that namespace's aliases. Other regions are untouched.
- **Reserved segments protect critical use cases.** `test` aliases can never accidentally resolve in production because the namespace itself is non-resolvable there.

### Negative

- **Every consumer must know its namespace.** Services must either be configured with a default namespace or pass one explicitly. This is documentation and onboarding work.
- **Cross-namespace queries are harder.** "Find me CC-421 anywhere" requires iterating namespaces. Mitigated by the fact that this is rarely the actual user need — usually the user knows what region they're in.
- **Namespace proliferation risk.** Without governance, teams will create namespaces for every minor distinction. Mitigated by requiring namespace registration.
- **Hierarchical naming is verbose.** `au.nsw.central_coast.cells` is a lot to type compared to `cells`. Mitigated by per-service default namespaces.

### Neutral

- Aliases remain mutable and namespaced. Canonical IDs remain immutable and global. The two layers stay independent, consistent with ADR-001.

---

## Alternatives Considered

### A. Global Flat Namespace

All aliases live in one global string space. First-come-first-served.

**Rejected because:** the first region to use `CC-` permanently claims it. This is hostile to expansion and creates real confusion when the system serves multiple regions.

### B. Implicit Namespace from Context

Infer the namespace from the calling user's location, the dataset being queried, or the cell's coordinates.

**Rejected because:** implicit context is the source of every painful resolution bug. A user querying from California about a NSW dataset would silently get the wrong cell. The system should never guess at identity.

### C. Prefix-as-Namespace

Use the alias prefix itself as the namespace identifier. `CC-421` is implicitly namespaced by `CC`.

**Rejected because:** prefixes collide too. Two regions both wanting `CC-` is the original problem this ADR exists to solve.

### D. UUID-Style Aliases

Make aliases globally unique by including enough entropy: `cc-421-au-nsw-central-coast`.

**Rejected because:** at that point the alias is no longer human-friendly. The whole purpose of the alias layer is short, memorable references.

### E. Defer Namespace Decision

Ship with global aliases for v0.1.1 and add namespaces in a later migration.

**Rejected because:** every alias minted under the global model would need to be migrated, every API contract would need to break, and every consumer would need to learn the new model. This is the kind of foundational decision that has to be right at v0.1.1 or it costs years to fix.

---

## Implementation Notes

- Full alias rules are in `alias_namespace_rules.md`.
- The partial unique constraint is part of the `alias_table` definition in `identity_registry_schema.sql` (Milestone 2 deliverable).
- The Alias Resolution Service exposes resolution at `GET /resolve/alias?alias=...&namespace=...` (see brief §5).
- The 180-day grace period for alias reuse is enforced in the resolution service, not the database.

---

*ADR-006 — Locked*
