# Harmony ADR Index — Canonical Sequence

> **Version:** 1.0
> **Status:** Authoritative after v0.1.3 merge
> **Date:** 2026-04-10
> **Purpose:** Single canonical sequence of Architecture Decision Records across the entire Pillar 1 build. Replaces the parallel architecture-track and build-track numbering that existed before v0.1.3.

---

## Why This Exists

Prior to v0.1.3, two parallel ADR sequences were accumulating:

- **Architecture track** (this Claude Chat) — produced ADR-001, 004, 008, 009, 010, 011
- **Build track** (CoWork Sessions 2 and 3) — produced ADR-004 and ADR-005 under its own numbering

Both sequences claimed "ADR-004" as a different document. This was resolved in v0.1.3 by merging into a single canonical sequence. This file is the authoritative index. When any document references an ADR by number, it refers to the number in the **New #** column below.

---

## Canonical Sequence

| New # | Title | Source | Old # / Location | Status |
|---|---|---|---|---|
| ADR-001 | Layered Identity Model | Architecture track | ADR-001 | Accepted (federation note v0.1.2) |
| ADR-002 | Cell Geometry — Gnomonic Cube Projection | Build track (Session 2) | — (was in `cell_geometry_spec.md` only) | To be extracted as a standalone ADR |
| ADR-003 | Cell Key Derivation Architecture | Build track (Session 2) | ADR-004-build | Accepted |
| ADR-004 | `cell_id` vs `cell_key` Dual-Identifier Principle | Architecture track | ADR-004-arch | Accepted |
| ADR-005 | Cell Adjacency Model | Build track (Session 3) | ADR-005-build | Accepted |
| ADR-006 | Alias Namespace Model | Architecture track | ADR-008 | Accepted |
| ADR-007 | Temporal Versioning | Architecture track | ADR-009 | Accepted (reserved at schema layer) |
| ADR-008 | Named-Entity Resolution Boundary | Architecture track | ADR-010 | Accepted |
| ADR-009 | Three-Layer Agent Model | Architecture track | ADR-011 | Accepted |
| ADR-010 | Spatial Geometry Schema Extension (v0.1.3) | New — logs Session 3 schema changes | — | Accepted |
| ADR-011 | Gate 3 Closure — Identity Generation Order | New — closes V1.0 Gate 3 | — | Accepted |
| ADR-012 | Alias Generation Architecture | Build track (Session 4) | — | Accepted |
| ADR-013 | API Layer Architecture (FastAPI) | Build track (Session 5) | — | Accepted |
| ADR-014 | Pillar 1 Stage 1 Completion | Build track (Session 6) | — | Accepted |

---

## Rename Map — Apply to Build-Track Files

The build-track files currently exist under the old numbering. Rename them as follows:

```
harmony/docs/adr/ADR-004-cell-key-derivation.md  →  ADR-003-cell-key-derivation.md
harmony/docs/adr/ADR-005-cell-adjacency-model.md →  ADR-005-cell-adjacency-model.md  (unchanged number)
```

ADR-005-cell-adjacency-model.md keeps its number because it happens to land on ADR-005 in the canonical sequence as well.

ADR-002 (Cell Geometry) does not yet exist as a standalone file — its content currently lives inside `cell_geometry_spec.md`. A short extraction exercise is recommended: produce a proper ADR-002 summarising the decision, referencing the full spec. This is a low-priority follow-up.

---

## Rename Map — Apply to Architecture-Track Files

The architecture-track files from the v0.1.2 pack should be renamed on upload to the project:

```
ADR-001-layered-identity.md                    →  ADR-001-layered-identity.md          (unchanged)
ADR-004-cell-id-vs-cell-key.md                 →  ADR-004-cell-id-vs-cell-key.md       (unchanged)
ADR-008-alias-namespace-model.md               →  ADR-006-alias-namespace-model.md
ADR-009-temporal-versioning.md                 →  ADR-007-temporal-versioning.md
ADR-010-named-entity-resolution-boundary.md    →  ADR-008-named-entity-resolution-boundary.md
ADR-011-three-layer-agent-model.md             →  ADR-009-three-layer-agent-model.md
```

Inside each renamed file, update any internal cross-references (e.g. "See ADR-009" → "See ADR-007" if referring to temporal versioning).

---

## Cross-Reference Update Checklist

After renaming, the following documents reference ADRs by number and must have their references updated:

- `identity-schema.md` — references ADR-001, 004, 009, 010 → update to ADR-001, 004, 007, 008
- `id_generation_rules.md` — references ADR-009, 010 → update to ADR-007, 008
- `CHANGELOG.md` — references all ADRs → update throughout
- `pillar-1-master-spec-variations.md` — references ADRs throughout → update
- `alias_namespace_rules.md` — references ADR-008 → update to ADR-006
- `PM/agents/project-manager-agent-brief.md` — no ADR references
- `PM/sessions/*.md` — references ADRs → update

The v0.1.3 versions of `identity-schema.md`, `id_generation_rules.md`, `CHANGELOG.md`, and `pillar-1-master-spec-variations.md` produced alongside this index already use the new numbering.

---

## Going Forward

All future ADRs — from both this architecture-track chat and any build-track CoWork sessions — will be numbered in a single shared sequence. The next available number is ADR-015. There is one canonical ADR namespace for Pillar 1.

Builder Agents producing new ADRs must:

1. Check this index for the next available number
2. Use the next integer — no parallel sequences
3. Update this index with the new entry

This is a light-weight governance discipline that prevents the numbering collision from recurring.

---

*ADR Index — canonical sequence established at v0.1.3*
