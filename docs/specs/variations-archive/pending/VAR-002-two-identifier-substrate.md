# VAR-002 — Two-Identifier Substrate (cell_id vs cell_key)
> Harmony Variation File | Status: PENDING
> Raised: 2026-04-13 | Applied: —

---

## Header

| Field | Value |
|---|---|
| **VAR ID** | VAR-002 |
| **Status** | `PENDING` |
| **Priority** | `HIGH` |
| **Raised by** | Mikey |
| **Date raised** | 2026-04-13 |
| **Date applied** | — |
| **Applied in version** | — |
| **Related ADR** | ADR-004 |
| **Raised in chat** | Pillar 1 Spatial Substrate build sessions, April 2026 |

---

## Decision Summary

Every cell carries both an opaque immutable canonical ID (cell_id) and a deterministic derivable substrate key (cell_key). This resolves the fundamental "stability vs reproducibility" tension in any spatial substrate. The canonical ID never changes and is the reference for all cross-system lookups. The cell key can be recomputed from spatial parameters and is used for substrate-level operations like neighbour discovery.

---

## Sections Affected in Master Spec

- Pillar I — Spatial Substrate

---

## Change Detail

### Pillar I — Spatial Substrate

**Current text:**
```
The V1.0 spec mentions "HCID identity model" but does not distinguish between the two identifier types.
```

**Add as a new subsection within Pillar I:**
```
Every Harmony Cell carries two identifiers. The canonical ID (`cell_id`) is an opaque, immutable identifier assigned at creation — it is the permanent address used by all systems. The cell key (`cell_key`) is a deterministic key derivable from the cell's spatial parameters (level, position) — it enables substrate-level operations such as neighbour lookup, parent/child traversal, and spatial joins without requiring a registry round-trip. This dual-identifier design resolves the stability-vs-reproducibility tension inherent in any spatial indexing system.
```

**Reason for change:**
This is one of the most consequential architectural decisions in Pillar 1 and is not reflected in V1.0.

---

## Conflicts or Dependencies

- [ ] None identified

---

## Open Questions (if any)

- [ ] None

---

## Changelog

| Date | Action | Notes |
|---|---|---|
| 2026-04-13 | Created | Extracted from Pillar 1 variations document |
