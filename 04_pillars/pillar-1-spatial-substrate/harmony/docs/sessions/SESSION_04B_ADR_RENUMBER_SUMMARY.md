# Harmony Spatial Operating System — Pillar I — Spatial Substrate
# Session 04B Summary: ADR Renumbering — Canonical Sequence Merge

> **Date:** 2026-04-18  
> **Session Type:** Housekeeping  
> **Active Pillar:** Pillar 1 — Spatial Substrate  
> **Scope:** File renames and cross-reference updates only. No architectural, schema, or code logic changes.

---

## Summary

Merged the parallel architecture-track and build-track ADR numbering sequences into a single canonical sequence per `ADR_INDEX.md`. Renamed 5 ADR files, updated internal headers and footers in all renamed files, and swept the entire project for stale cross-references. Also placed the v0.1.3 bookkeeping pack (ADR-010, ADR-011, ADR_INDEX, CHANGELOG, pillar-1-master-spec-variations, id_generation_rules patch) into the project, applied the id_generation_rules v0.1.3 patch, and updated the CHANGELOG with Session 4 outputs.

---

## Files Renamed

| Old Name | New Name (Canonical) | Meaning |
|----------|---------------------|---------|
| `ADR-004-cell-key-derivation.md` | `ADR-003-cell-key-derivation.md` | Cell key derivation algorithm |
| `ADR-008-alias-namespace-model.md` | `ADR-006-alias-namespace-model.md` | Alias namespace model |
| `ADR-009-temporal-versioning.md` | `ADR-007-temporal-versioning.md` | Temporal versioning |
| `ADR-010-named-entity-resolution-boundary.md` | `ADR-008-named-entity-resolution-boundary.md` | Named-entity resolution boundary |
| `ADR-011-three-layer-agent-model.md` | `ADR-009-three-layer-agent-model.md` | Three-layer agent model |

Files that kept their number (no rename): ADR-001, ADR-004 (cell_id vs cell_key), ADR-010 (spatial geometry), ADR-011 (Gate 3 closure), ADR-012 (alias generation).

ADR-002 (gnomonic cube projection) and ADR-005 (cell adjacency model) are noted as follow-up extractions per ADR_INDEX.md.

---

## Internal Headers Updated

Each renamed file had its title line and footer updated to match the new number:

| File | Old Title | New Title |
|------|-----------|-----------|
| ADR-003 | `# ADR-004: Cell Key Derivation...` | `# ADR-003: Cell Key Derivation...` |
| ADR-006 | `# ADR-008 — Alias Namespace...` | `# ADR-006 — Alias Namespace...` |
| ADR-007 | `# ADR-009 — Temporal Versioning...` | `# ADR-007 — Temporal Versioning...` |
| ADR-008 | `# ADR-010 — Named-Entity...` | `# ADR-008 — Named-Entity...` |
| ADR-009 | `# ADR-011 — Three-Layer...` | `# ADR-009 — Three-Layer...` |

Footer "Locked" lines updated in all five files. ADR-009 also had an internal self-reference ("ADR-011") updated to "ADR-009" in the Alternatives Considered section.

---

## Cross-References Updated

| File | Old Reference | New Reference | Context |
|------|--------------|---------------|---------|
| `ADR-012-alias-generation-architecture.md` | ADR-008 (×3) | ADR-006 | Alias namespace model |
| `SESSION_04_SUMMARY.md` | ADR-008 (×2) | ADR-006 | Alias namespace model |
| `SESSION_04_SUMMARY.md` | ADR-009 | ADR-007 | Temporal versioning |
| `SESSION_04_SUMMARY.md` | ADR-011 | ADR-009 | Three-layer agent model |
| `PM session report` | ADR-008 (×2) | ADR-006 | Alias namespace model |
| `PM session report` | ADR-009 | ADR-007 | Temporal versioning |
| `PM session report` | ADR-011 | ADR-009 | Three-layer agent model |
| `alias_service.py` | ADR-008 | ADR-006 | Module header comment |
| `002_alias_namespace_registry.sql` | ADR-008 | ADR-006 | File header comment |
| `identity_registry_schema.sql` | ADR-009 | ADR-007 | Reserved temporal fields comment |
| `cell_adjacency_spec.md` | ADR-004-cell-key-derivation | ADR-003-cell-key-derivation | Governing documents |
| `ADR-001-layered-identity.md` | ADR-009 | ADR-007 | Temporal versioning reference |
| `ADR-001-layered-identity.md` | ADR-010 | ADR-008 | NER boundary reference |
| `cell_identity_schema.json` | ADR-009 (×4) | ADR-007 | Reserved temporal field descriptions |
| `cell_identity_schema.json` | ADR-010 | ADR-008 | Reserved known_names description |
| `SESSION_03_SUMMARY.md` | ADR-010 | ADR-008 | Conversational Spatial Agent reference |
| `SESSION_02_SUMMARY.md` | ADR-004 (derivation refs) | ADR-003 | Cell key derivation ADR |
| `ADR-003-cell-key-derivation.md` | "End of ADR-004" | "End of ADR-003" | Footer |

---

## ADR-004 Disambiguation Log

The old "ADR-004" appeared in two different documents with different meanings:

| Location | Context | Resolution |
|----------|---------|------------|
| `id_generation_rules.md` lines 105, 171 | "See ADR-004 for the full rationale" — about why cells have both cell_id and cell_key | **Left as ADR-004** (dual-identifier principle) |
| `ADR-003-cell-key-derivation.md` line 11 | "Supersedes ADR-004-cell-id-vs-cell-key.md" | **Left as ADR-004** (correct reference to dual-identifier ADR) |
| `ADR-003-cell-key-derivation.md` line 17 | "ADR-004 (cell-id-vs-cell-key) established that both identifiers are mandatory" | **Left as ADR-004** (correct) |
| `SESSION_02_SUMMARY.md` line 116 | "ADR-004-cell-id-vs-cell-key.md (original)" | **Left as ADR-004** (correct reference to dual-identifier ADR) |
| `SESSION_02_SUMMARY.md` lines 15, 27, 108, 110 | "ADR-004: Cell Key Derivation Architecture" | **Changed to ADR-003** (cell key derivation) |
| `cell_adjacency_spec.md` line 8 | "ADR-004-cell-key-derivation.md" | **Changed to ADR-003** (cell key derivation) |
| `pillar-1-master-spec-variations.md` line 186 | "cell_id vs cell_key | ADR-004" | **Left as ADR-004** (correct, in v0.1.3 pack using canonical numbers) |

No ambiguous cases remained unresolved. Every ADR-004 reference was identifiable from context.

---

## Files Not Updated (Intentionally)

These files use old ADR numbers but are reference/historical documents that should not be modified:

- `extracted_files/*` — Original v0.1.2 architecture-track source files
- `BUILD_PLAN_V1.0.md` — Original build plan from before renumbering
- `PM_BRIEF_V1.0.md` — Original PM brief
- `pillar-1-spatial-substrate-stage1-brief.md` — Original stage-1 brief
- `ADR_INDEX.md` — Uses old numbers in the "Old #" column deliberately
- `id_generation_rules_v0.1.3_patch.md` — Patch instructions referencing old numbers

---

## Additional Bookkeeping Completed

1. **v0.1.3 bookkeeping pack placed** — ADR-010, ADR-011 (gate-3-closure), ADR_INDEX.md, CHANGELOG.md, pillar-1-master-spec-variations.md, id_generation_rules_v0.1.3_patch.md all placed in `harmony/docs/` and `harmony/docs/adr/`.
2. **id_generation_rules.md patched to v0.1.3** — All 7 edits applied: cell key regex (16-char hash), resolution table (12 levels), §11 open items (Gate 3 closure), ADR cross-references.
3. **CHANGELOG updated** — Added `[0.1.3-s4]` entry for Session 4 alias system deliverables.
4. **ADR_INDEX updated** — ADR-012 (Alias Generation Architecture) added to canonical sequence.

---

## Verification

| Check | Result |
|-------|--------|
| ADR files in project | 10 (001, 003, 004, 006–012) |
| All internal headers match filename | Yes |
| All internal footers match | Yes |
| Stale ADR-008 (alias namespace) in active files | 0 |
| Stale ADR-009 (temporal) in active files | 0 |
| Stale ADR-010 (NER boundary) in active files | 0 |
| Stale ADR-011 (three-layer agent) in active files | 0 |
| Ambiguous ADR-004 references unresolved | 0 |
| Tests passing | 122/122 |

---

*End of Session 04B Summary*
