# VAR-005 — Federation-Compatible Identity Format
> Harmony Variation File | Status: PENDING
> Raised: 2026-04-13 | Applied: —

---

## Header

| Field | Value |
|---|---|
| **VAR ID** | VAR-005 |
| **Status** | `PENDING` |
| **Priority** | `STANDARD` |
| **Raised by** | Mikey |
| **Date raised** | 2026-04-13 |
| **Date applied** | — |
| **Applied in version** | — |
| **Related ADR** | ADR-001 (Federation Note) |
| **Raised in chat** | Pillar 1 Spatial Substrate build sessions, April 2026 |

---

## Decision Summary

The canonical ID format carries no embedded operator, region, or jurisdiction, making it deliberately federation-compatible. "Single source of truth" refers to the logical registry, not a centralised deployment. The current deployment is centralised, but the identity format and registry contract are compatible with a federated, multi-issuer model.

---

## Sections Affected in Master Spec

- Pillar I — Spatial Substrate
- Gap Register (Gap 4)

---

## Change Detail

### Pillar I — Spatial Substrate

**Current text:**
```
[Identity format section in V1.0]
```

**Add:**
```
The Identity Registry is the logical single source of truth. The canonical ID format carries no embedded operator, region, or jurisdiction — it is deliberately federation-compatible. The current deployment model is centralised, but the identity format and registry contract support a future federated, multi-issuer model. Federation, when introduced, lives in the deployment topology, not in the identity format. See ADR-001 federation note.
```

**Reason for change:**
Gap 4 asked that the identity model not foreclose federation — this confirms it hasn't.

---

### Gap Register — Gap 4

**Current status:**
```
[Deferred]
```

**Update to:**
```
Preserved — federation not foreclosed. The canonical ID format is confirmed federation-compatible. Identity carries no embedded operator or jurisdiction. Formal federation architecture deferred. See ADR-001 federation note.
```

**Reason for change:**
Gap 4 asked that the identity model not foreclose federation — this confirms it hasn't.

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
