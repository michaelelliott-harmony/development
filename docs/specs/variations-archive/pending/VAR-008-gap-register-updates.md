# VAR-008 — Gap Register Status Updates
> Harmony Variation File | Status: PENDING
> Raised: 2026-04-13 | Applied: —

---

## Header

| Field | Value |
|---|---|
| **VAR ID** | VAR-008 |
| **Status** | `PENDING` |
| **Priority** | `STANDARD` |
| **Raised by** | Mikey |
| **Date raised** | 2026-04-13 |
| **Date applied** | — |
| **Applied in version** | — |
| **Related ADR** | ADR-009, ADR-010, ADR-001 |
| **Raised in chat** | Pillar 1 Spatial Substrate build sessions, April 2026 |

---

## Decision Summary

Three gaps in the V1.0 Gap Register have had their status changed by Pillar 1's work. Gap 3 (Temporal Memory) is closed at the substrate layer, awaiting Pillar 4 activation. Gap 5 (LLM Integration / Named-Entity Resolution) is closed at the substrate layer, awaiting Pillar 5 activation. Gap 4 (Sovereignty/Federation) is preserved — the identity format is confirmed federation-compatible. Gaps 1, 2, and 6 remain open and unaffected.

---

## Sections Affected in Master Spec

- Gap Register

---

## Change Detail

### Gap Register — Gap 3 (Temporal Memory)

**Current status:**
```
[Open]
```

**Update to:**
```
Closed at substrate layer — bitemporal schema confirmed. Awaiting Pillar 4 activation. See ADR-009.
```

**Reason for change:**
Gap 3 is resolved at the schema layer; the master spec should reflect the current state of resolution.

---

### Gap Register — Gap 4 (Sovereignty/Federation)

**Current status:**
```
[Deferred]
```

**Update to:**
```
Preserved — identity format confirmed federation-compatible. No embedded operator or jurisdiction. See ADR-001 federation note.
```

**Reason for change:**
Gap 4 asked that the identity model not foreclose federation — this confirms it hasn't.

---

### Gap Register — Gap 5 (LLM Integration / Named-Entity Resolution)

**Current status:**
```
[Deferred]
```

**Update to:**
```
Closed at substrate layer — Identity Registry name-lookup primitives delivered. Full resolution awaits Pillar 5. See ADR-010.
```

**Reason for change:**
Gap 5 is resolved at the substrate layer; the architectural boundary between pillars is now explicit.

---

### Gap Register — Gaps 1, 2, 6

**Current status:**
```
[Open / other status]
```

**Update:**
```
No change.
```

**Reason for change:**
These gaps remain open and unaffected by Pillar 1's work.

---

## Conflicts or Dependencies

- [ ] This VAR overlaps with VAR-003, VAR-004, and VAR-005 which each touch a specific gap. When applying, the Spec Updater should reconcile to avoid duplication.

---

## Open Questions (if any)

- [ ] None

---

## Changelog

| Date | Action | Notes |
|---|---|---|
| 2026-04-13 | Created | Extracted from Pillar 1 variations document |
