# VAR-006 — Three-Layer Agent Model
> Harmony Variation File | Status: APPLIED
> Raised: 2026-04-13 | Applied: 2026-04-13

---

## Header

| Field | Value |
|---|---|
| **VAR ID** | VAR-006 |
| **Status** | `APPLIED` |
| **Priority** | `STANDARD` |
| **Raised by** | Mikey |
| **Date raised** | 2026-04-13 |
| **Date applied** | 2026-04-13 |
| **Applied in version** | V1.0.1 |
| **Related ADR** | ADR-011 |
| **Raised in chat** | Pillar 1 Spatial Substrate build sessions, April 2026 |

---

## Decision Summary

The agent model is formally structured into three layers: Builder Agents (build phase, engineering work — the agents building Harmony itself), Runtime Agent Classes I/II/III (V1.0's existing classes — production infrastructure), and Digital Team Members (production, customer-facing agents that interact with end users). V1.0 already defines the Runtime Agent Classes. This variation adds the surrounding layers.

---

## Sections Affected in Master Spec

- Agent Architecture

---

## Change Detail

### Agent Architecture

**Current text:**
```
The Agent Architecture section defines Class I, II, III agents.
```

**Add as a new subsection before the existing agent classes:**
```
The Harmony agent model operates across three layers. **Builder Agents** operate during the build phase — they are the engineering agents (one per pillar) responsible for architecture, schema, and implementation. Builder Agents are temporary; they exist to construct the system. **Runtime Agent Classes (I, II, III)** are the production infrastructure agents defined below — they operate the spatial substrate, serve navigation queries, and bridge conversational AI with spatial experience. **Digital Team Members** are the customer-facing agents that interact with end users through the application layer (e.g., Reagent). This three-layer model is documented in ADR-011.
```

**Reason for change:**
V1.0 defines runtime agents but does not formalise the full three-layer model that governs Harmony's agent architecture from build through to production.

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
