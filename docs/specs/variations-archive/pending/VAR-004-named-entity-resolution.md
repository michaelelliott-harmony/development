# VAR-004 — Named-Entity Resolution Boundary
> Harmony Variation File | Status: PENDING
> Raised: 2026-04-13 | Applied: —

---

## Header

| Field | Value |
|---|---|
| **VAR ID** | VAR-004 |
| **Status** | `PENDING` |
| **Priority** | `STANDARD` |
| **Raised by** | Mikey |
| **Date raised** | 2026-04-13 |
| **Date applied** | — |
| **Applied in version** | — |
| **Related ADR** | ADR-010 |
| **Raised in chat** | Pillar 1 Spatial Substrate build sessions, April 2026 |

---

## Decision Summary

The Identity Registry exposes name-lookup primitives (exact and fuzzy name lookup, multi-name attachment via `known_names`, ranked candidate returns with confidence scores, context-filtered lookup). Full natural-language resolution (pronouns, descriptive paraphrases, conversational state) is composed by the Conversational Spatial Agent (Class III) using Pillar 1's primitives, Pillar 4's semantic search, and Pillar 5's conversational context. The boundary is deliberate: each layer does what it is good at.

---

## Sections Affected in Master Spec

- Pillar V — Interaction Layer
- Gap Register (Gap 5)

---

## Change Detail

### Pillar V — Interaction Layer

**Current text:**
```
[Describes the semantic extraction pipeline generally]
```

**Add:**
```
The Conversational Spatial Agent (Class III) composes full natural-language entity resolution from three sources: Pillar 1's Identity Registry name-lookup primitives (exact match, fuzzy match, known_names index), Pillar 4's semantic search, and Pillar 5's own conversational state and context. The Identity Registry is not responsible for natural-language resolution — it provides the indexed primitives. The boundary is deliberate and documented in ADR-010.
```

**Reason for change:**
Gap 5 is resolved at the substrate layer and the architectural boundary between pillars needs to be explicit.

---

### Gap Register — Gap 5

**Current status:**
```
[Deferred]
```

**Update to:**
```
Closed at substrate layer — Identity Registry primitives delivered. Full natural-language resolution awaits Pillar 5 activation. See ADR-010.
```

**Reason for change:**
Gap 5 is resolved at the substrate layer and the architectural boundary between pillars needs to be explicit.

---

## Conflicts or Dependencies

- [ ] Pillar 5 must implement the composition layer.

---

## Open Questions (if any)

- [ ] None

---

## Changelog

| Date | Action | Notes |
|---|---|---|
| 2026-04-13 | Created | Extracted from Pillar 1 variations document |
