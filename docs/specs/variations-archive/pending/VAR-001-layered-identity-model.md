# VAR-001 — Layered Identity Model
> Harmony Variation File | Status: PENDING
> Raised: 2026-04-13 | Applied: —

---

## Header

| Field | Value |
|---|---|
| **VAR ID** | VAR-001 |
| **Status** | `PENDING` |
| **Priority** | `HIGH` |
| **Raised by** | Mikey |
| **Date raised** | 2026-04-13 |
| **Date applied** | — |
| **Applied in version** | — |
| **Related ADR** | ADR-001 |
| **Raised in chat** | Pillar 1 Spatial Substrate build sessions, April 2026 |

---

## Decision Summary

The identity system uses a six-layer model: Canonical ID, Human Alias, Alias Namespace, Friendly Name, Known Names, and Semantic Labels. The governing principle is: "Canonical IDs are for truth. Aliases are for people. Semantic labels are for intelligence." This replaces the conceptual "stable identity" language in V1.0 with a formally articulated layered model.

---

## Sections Affected in Master Spec

- Pillar I — Spatial Substrate

---

## Change Detail

### Pillar I — Spatial Substrate

**Current text:**
```
Unchanged from V0.1. The Harmony Cell System remains the correct foundation. The HCID identity model, hierarchical cell structure, local ENU coordinate frames, and entity occupancy model are all carried forward without modification.
```

**Add after the existing Pillar I text:**
```
The identity system is formally structured as a six-layer model. Layer 1: Canonical ID — immutable opaque identifier, the source of truth. Layer 2: Cell Key — deterministic, derivable substrate key for spatial reproducibility. Layer 3: Human Alias — namespaced human-friendly address (e.g. CC-421). Layer 4: Friendly Name — free-text display name. Layer 5: Known Names — indexed name variants for entity resolution primitives. Layer 6: Semantic Labels — AI-generated descriptive tags. The governing principle: Canonical IDs are for truth. Aliases are for people. Semantic labels are for intelligence.
```

**Reason for change:**
V1.0 mentions 'stable identity' but does not articulate the layered model that Pillar 1 has now formally adopted and built against.

---

## Conflicts or Dependencies

- [ ] May interact with any future Pillar 5 decisions on how semantic labels are generated.

---

## Open Questions (if any)

- [ ] None

---

## Changelog

| Date | Action | Notes |
|---|---|---|
| 2026-04-13 | Created | Extracted from Pillar 1 variations document |
