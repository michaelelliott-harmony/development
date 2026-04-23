# VAR-003 — Bitemporal Versioning Schema Commitment
> Harmony Variation File | Status: PENDING
> Raised: 2026-04-13 | Applied: —

---

## Header

| Field | Value |
|---|---|
| **VAR ID** | VAR-003 |
| **Status** | `PENDING` |
| **Priority** | `STANDARD` |
| **Raised by** | Mikey |
| **Date raised** | 2026-04-13 |
| **Date applied** | — |
| **Applied in version** | — |
| **Related ADR** | ADR-009 |
| **Raised in chat** | Pillar 1 Spatial Substrate build sessions, April 2026 |

---

## Decision Summary

Pillar 1 has adopted a bitemporal versioning model at the schema layer. Four reserved fields have been added to cell and entity schemas: `valid_from`, `valid_to`, `version_of`, `temporal_status`. The schema distinguishes system time (created_at/updated_at) from valid time (valid_from/valid_to). Active implementation is deferred to Pillar 4. The schema is forward-compatible — Pillar 4 can activate temporal versioning without breaking changes.

---

## Sections Affected in Master Spec

- Pillar I — Spatial Substrate
- Pillar IV — Spatial Knowledge Layer
- Gap Register (Gap 3)

---

## Change Detail

### Pillar I — Spatial Substrate

**Current text:**
```
Cell schemas and HCID structures must be confirmed capable of supporting temporal versioning without breaking changes before ingestion begins at scale.
```

**Replace with:**
```
Pillar 1 commits to bitemporal versioning at the schema layer. The schema distinguishes system time (`created_at`/`updated_at`) from valid time (`valid_from`/`valid_to`), and supports version chains via `version_of` and `temporal_status`. Four reserved fields are present in cell and entity schemas. Pillar 4 owns active implementation. See ADR-009.
```

**Reason for change:**
Gap 3 is resolved at the schema layer. The master spec should reflect this commitment.

---

### Pillar IV — Spatial Knowledge Layer

**Current text:**
```
[General description of Pillar IV's role]
```

**Add:**
```
Temporal versioning is reserved at the substrate layer (Pillar I) and active implementation is owned by Pillar IV. The substrate's bitemporal model (ADR-009) provides the schema foundation; Pillar IV activates the version chain logic, query semantics, and historical state retrieval.
```

**Reason for change:**
Clarifies the boundary between substrate commitment and Pillar 4 activation.

---

### Gap Register — Gap 3

**Current status:**
```
[Open]
```

**Update to:**
```
Closed at substrate layer — schema confirmed bitemporal-ready. Awaiting Pillar 4 activation. See ADR-009.
```

**Reason for change:**
Gap 3 is resolved at the schema layer. The master spec should reflect this.

---

## Conflicts or Dependencies

- [ ] Pillar 4 must activate — the schema is ready but inert until then.

---

## Open Questions (if any)

- [ ] None

---

## Changelog

| Date | Action | Notes |
|---|---|---|
| 2026-04-13 | Created | Extracted from Pillar 1 variations document |
