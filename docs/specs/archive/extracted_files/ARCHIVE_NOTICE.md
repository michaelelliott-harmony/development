# ⚠️ Archive Notice — Pre-v0.1.3 ADR Numbering

**Filed:** 2026-04-26 by Priya Kapoor (File Systems Architect)

---

## What This Folder Contains

These files were extracted from the Harmony master spec zip during the
2026-04-21 repository reorganisation. They represent the Milestone 1
v0.1.2 amendment pack as it existed **before the v0.1.3 numbering merge**,
which resolved a collision between two parallel ADR sequences (architecture
track and build track).

See `README.md` in this folder for the full pack index.

---

## ⚠️ ADR Numbers Here Do Not Match the Canonical Sequence

Four ADR files in this folder use **pre-reorganisation numbers** that now
map to *different* ADRs in the canonical sequence. Do not use these
filenames to resolve an ADR by number.

| File in This Folder | Pre-v0.1.3 Number | Canonical ADR | Canonical Title |
|---------------------|-------------------|---------------|-----------------|
| `ADR-001-layered-identity.md` | ADR-001 | ADR-001 | Layered Identity Model *(unchanged)* |
| `ADR-004-cell-id-vs-cell-key.md` | ADR-004 | ADR-004 | `cell_id` vs `cell_key` Dual-Identifier Principle *(unchanged)* |
| `ADR-008-alias-namespace-model.md` | ADR-008 (old) | **ADR-006** | Alias Namespace Model |
| `ADR-009-temporal-versioning.md` | ADR-009 (old) | **ADR-007** | Temporal Versioning Model |
| `ADR-010-named-entity-resolution-boundary.md` | ADR-010 (old) | **ADR-008** | Named-Entity Resolution Boundary |
| `ADR-011-three-layer-agent-model.md` | ADR-011 (old) | **ADR-009** | Three-Layer Agent Model |

The four highlighted files use numbers that now belong to **different**
canonical ADRs:
- Canonical ADR-008 = Named-Entity Resolution Boundary
- Canonical ADR-009 = Three-Layer Agent Model
- Canonical ADR-010 = Spatial Geometry Schema Extension (v0.1.3)
- Canonical ADR-011 = Gate 3 Closure — Identity Generation Order

---

## Canonical Index

The authoritative ADR index covering all 22 ADRs (ADR-001 through ADR-022)
is at: **`docs/adr/ADR_INDEX.md`**

Canonical ADR files live at:
- ADR-001, ADR-003, ADR-004, ADR-006–ADR-014: `04_pillars/pillar-1-spatial-substrate/harmony/docs/adr/`
- ADR-002, ADR-005, ADR-015–ADR-022: `docs/adr/`
