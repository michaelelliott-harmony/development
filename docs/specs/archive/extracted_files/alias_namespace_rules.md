# Harmony Alias Namespace Rules

> **Version:** 0.1.1
> **Status:** Locked — Milestone 1
> **Pillar:** 1 — Spatial Substrate
> **Owner:** Agent 3 — Alias Systems Engineer

---

## 1. Purpose

Aliases exist so that humans can refer to objects without typing canonical IDs. They are intentionally separate from canonical identity (see ADR-001) and intentionally namespaced to prevent collisions across regions, datasets, and object types (see ADR-008).

This document defines:

- The shape of an alias
- The shape of a namespace
- Collision rules
- Lifecycle rules
- Resolution rules

---

## 2. Alias Format

```
Format:  <prefix>-<number>
Regex:   ^[A-Z]{2,4}-[0-9]{1,6}$
Example: CC-421
```

| Component | Meaning |
|---|---|
| Prefix | 2–4 uppercase letters identifying the dataset or region |
| Separator | A single hyphen `-` |
| Number | A 1–6 digit positive integer |

Aliases are case-sensitive in storage (always uppercase prefix, plain digits) but case-insensitive in lookup (`cc-421` resolves the same as `CC-421`).

Aliases MAY be reassigned over time, but only after the previous binding has been retired (see §6).

---

## 3. Namespace Format

```
Format:  <country>.<state>.<region>.<object_class>
Regex:   ^[a-z]{2,4}(\.[a-z0-9_]{2,32}){2,5}$
Example: au.nsw.central_coast.cells
```

Namespaces are dotted, lowercase, and hierarchical. Each segment is `[a-z0-9_]{2,32}`.

The conventional structure is:

| Segment | Example | Notes |
|---|---|---|
| Country (ISO 3166-1 alpha-2) | `au` | Required |
| State / region | `nsw` | Required |
| Locality | `central_coast` | Required |
| Object class | `cells` | Required — pluralised noun |
| Sub-class (optional) | `coastal` | Optional refinement |

Other top-level segments are reserved:

| Segment | Use |
|---|---|
| `global` | Cross-region objects |
| `system` | Internal Harmony objects |
| `test` | Test fixtures only — never resolvable in production |

---

## 4. The (alias, namespace) Tuple

The unit of identity at the alias layer is the **tuple** `(alias, namespace)`, not the alias alone.

```
("CC-421", "au.nsw.central_coast.cells")  →  hc_4fj9k2x7m
("CC-421", "au.qld.cairns_coast.cells")   →  hc_8m3k1p2z9   ← different cell, same alias
```

Two records may share an alias if they live in different namespaces. They may NOT share an alias within the same namespace at the same time. See ADR-008.

This means every alias resolution call MUST specify a namespace, either explicitly or via a default registered for the calling service.

---

## 5. Collision Rules

### 5.1 Within a namespace

Within a single namespace, an active alias resolves to exactly one canonical ID. The database enforces this with a partial unique constraint:

```sql
UNIQUE (alias, alias_namespace) WHERE status = 'active'
```

### 5.2 Across namespaces

The same alias string may be active in multiple namespaces simultaneously. This is intentional — `CC-421` is meaningful inside Central Coast and not expected to be globally unique.

### 5.3 Collision attempts

Attempting to register an alias that is already active in the same namespace returns `409 Conflict`. The caller must either choose a different alias or retire the existing one first.

---

## 6. Lifecycle

Aliases follow a simpler lifecycle than canonical IDs:

```
   ┌────────┐  bind   ┌────────┐  retire  ┌─────────┐
   │  free  │ ──────► │ active │ ───────► │ retired │
   └────────┘         └────────┘          └─────────┘
        ▲                                       │
        └───────────────────────────────────────┘
                       reuse (after grace period)
```

| State | Resolvable? | Notes |
|---|---|---|
| `free` | No | Alias has never been used in this namespace |
| `active` | Yes | The current binding |
| `retired` | Only via historical lookup | The previous binding |

**Reassignment rule:** A retired alias MAY be reused after a grace period of **180 days**. This grace period exists to prevent stale references in cached UIs and external systems from silently resolving to a different object.

The grace period is enforced by the Alias Resolution Service. An attempt to reuse a retired alias before 180 days have elapsed returns `409 Conflict`.

---

## 7. Resolution Behaviour

### 7.1 Successful resolution

```
GET /resolve/alias?alias=CC-421&namespace=au.nsw.central_coast.cells

200 OK
{
  "canonical_id": "hc_4fj9k2x7m",
  "alias_status": "active"
}
```

### 7.2 Retired alias

```
GET /resolve/alias?alias=CC-421&namespace=au.nsw.central_coast.cells&include_retired=true

200 OK
{
  "canonical_id": "hc_4fj9k2x7m",
  "alias_status": "retired",
  "retired_at": "2025-11-01T00:00:00Z",
  "successor": null
}
```

Without `include_retired=true`, retired aliases return `404 Not Found`.

### 7.3 Unknown alias

```
GET /resolve/alias?alias=ZZ-999&namespace=au.nsw.central_coast.cells

404 Not Found
{
  "error": "alias_not_found",
  "alias": "ZZ-999",
  "namespace": "au.nsw.central_coast.cells"
}
```

### 7.4 Missing namespace

```
GET /resolve/alias?alias=CC-421

400 Bad Request
{
  "error": "namespace_required",
  "hint": "Aliases are not unique without a namespace. Provide ?namespace=..."
}
```

The Alias Resolution Service NEVER guesses a namespace. If a default is needed, it must be registered per-service, not inferred from the alias.

---

## 8. Reserved Prefixes

The following alias prefixes are reserved and MUST NOT be used in production namespaces:

| Prefix | Reserved for |
|---|---|
| `TEST` | Test fixtures |
| `DEMO` | Demonstration data |
| `TMP` | Temporary objects |
| `SYS` | Internal Harmony objects |

---

## 9. Generation Conventions

Aliases may be auto-generated or assigned manually.

**Auto-generation** uses a per-namespace counter:

```
namespace: au.nsw.central_coast.cells
prefix:    CC
next:      422  →  alias = CC-422
```

The counter is held in the registry, incremented atomically, and never decremented. Retiring an alias does NOT decrement the counter.

**Manual assignment** is allowed for legacy migrations and human-curated datasets, subject to the format and collision rules above.

---

## 10. What Aliases Are NOT For

Aliases are a usability layer. They are NOT:

- A persistence layer (use `canonical_id`)
- A security boundary (anyone who can resolve a canonical ID can resolve its aliases)
- A semantic descriptor (use `friendly_name` or `semantic_labels`)
- A version identifier (use `schema_version` and successor chains)
- A globally unique identifier (they are unique only within a namespace)

Any service treating an alias as a stable system reference is a bug.

---

## 11. Open Items

Deferred to later milestones:

- Alias permissions (who can mint, who can retire) — needs the access control layer
- Alias internationalisation (non-Latin prefixes) — not blocking, revisit when needed
- Bulk alias migration tooling — Milestone 3+

---

*End of alias_namespace_rules.md — locked for Milestone 1*
