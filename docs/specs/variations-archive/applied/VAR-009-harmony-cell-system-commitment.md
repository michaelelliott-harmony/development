# VAR-009 — Harmony Cell System Commitment (Custom Spatial Indexing)
> Harmony Variation File | Status: APPLIED
> Raised: 2026-04-13 | Applied: 2026-04-13

---

## Header

| Field | Value |
|---|---|
| **VAR ID** | VAR-009 |
| **Status** | `APPLIED` |
| **Priority** | `HIGH` |
| **Raised by** | Mikey |
| **Date raised** | 2026-04-13 |
| **Date applied** | 2026-04-13 |
| **Applied in version** | V1.0.1 |
| **Related ADR** | ADR-004 (cell_key derivation), ADR-001 (identity model) |
| **Raised in chat** | Spec governance session, April 2026 — confirming that the Harmony Cell System is the committed spatial indexing layer |

---

## Decision Summary

> Harmony has committed to building its own spatial indexing system — the Harmony Cell System — rather than adopting an existing open-source solution such as Uber's H3 or Google's S2. This is not a future decision; it is the architectural path already underway. The HCID identity model, hierarchical cell structure, cell_key derivation rules, local ENU coordinate frames, and entity occupancy model are all implementations of this commitment. The "H3 vs custom" framing that appears in V0.1's open questions and the Pillar 1 variations document should be retired and replaced with an explicit statement that the decision has been made.

---

## Sections Affected in Master Spec

- Section 8 — Open Specifications / Unresolved Areas (V0.1 carryover)
- Pillar I — Spatial Substrate
- Section 7 — Build Sequence (implicitly — no longer waiting on this decision)

---

## Change Detail

### Section 8 — Open Specifications / Unresolved Areas

**Current text:**
```
| Spatial Index Choice | H3 vs custom system |
```

**Replace with / Add:**
```
| Spatial Index Choice | RESOLVED — The Harmony Cell System is the committed custom spatial indexing layer. H3, S2, and other existing open-source solutions were evaluated and set aside. The Harmony Cell System provides purpose-built hierarchical indexing, deterministic cell key derivation, local coordinate frame attachment, and entity occupancy semantics that no general-purpose library offers. |
```

**Reason for change:**
The decision to build custom was made before V0.1 and has been implemented through Pillar 1's entire Milestone 1 body of work. The spec should not carry language suggesting this is still open.

---

### Pillar I — Spatial Substrate

**Current text:**
```
The Harmony Cell System remains the correct foundation. The HCID identity model, hierarchical cell structure, local ENU coordinate frames, and entity occupancy model are all carried forward without modification.
```

**Replace with / Add:**
```
The Harmony Cell System is the committed custom spatial indexing layer for the project. Existing open-source solutions (Uber H3, Google S2) were evaluated and set aside — they are general-purpose hexagonal or quadrilateral tiling systems designed for analytics and proximity queries, not for the requirements Harmony places on its substrate: seamless continuous-LOD rendering (North Star I), machine-speed spatial reference frames for autonomous navigation (North Star II), and stable entity-bearing identity that supports temporal versioning and named-entity resolution.

The HCID identity model, hierarchical cell structure, cell_key derivation, local ENU coordinate frames, and entity occupancy model are all implementations of this commitment. The Harmony Cell System is not a wrapper around an existing library — it is a purpose-built spatial substrate.
```

**Reason for change:**
The master spec should make explicit that the custom indexing decision has been made and articulate why, so that future sessions and agents do not re-open the question.

---

## Conflicts or Dependencies

- [ ] The "Cell Granularity — Optimal sizing across levels" open question in V0.1 Section 8 remains genuinely open — this VAR does not close it. Metric edge lengths per resolution level are still to be determined in a later Pillar 1 milestone.
- [ ] The cell_key derivation rules (ADR-004) define how keys are computed but the underlying spatial tiling geometry (e.g., hexagonal vs quadrilateral, orientation, aperture) is an implementation detail within the Harmony Cell System and may warrant its own ADR when Milestone 2 geometry work begins.

---

## Open Questions (if any)

- [ ] None — the decision is made. Implementation details remain for future milestones.

---

## Changelog

| Date | Action | Notes |
|---|---|---|
| 2026-04-13 | Created | Formalising the Harmony Cell System as the committed custom spatial indexing layer; retiring the "H3 vs custom" open question |
