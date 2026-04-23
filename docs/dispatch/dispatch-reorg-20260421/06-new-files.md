# 06_NEW_FILES.md
## Files to Create From Scratch

---

## File 1: docs/specs/CURRENT_SPEC.md

Create this file exactly as written below.

```markdown
# Harmony — Current Specification Pointer

This file is the stable pointer to the current master specification.
CLAUDE.md always references this file, never a versioned filename directly.
Update this file when a new spec version is published.

---

## Current Version

**File:** `harmony-master-spec-v1-1-0.md`
**Version:** 1.1.0
**Status:** Active
**Supersedes:** V1.0.1
**Date:** April 2026

## Summary of Current Version

Pillar 1 Stage 1 complete (8/8 acceptance, 157 tests, 14 ADRs).
Adaptive Volumetric Cell Extension adopted (ADR-015).
Dimensional Architecture established: 3D, 4D, 5D, 6D.
Pillar 2 activated.

## Next Version In Progress

No active next version. Decisions accumulating in DECISION_LOG.md.

---

## How to Update This File

When a new master spec version is published:
1. Update the "Current Version" section above
2. Move the old version details to the "Previous Versions" section below
3. Update "Next Version In Progress" status
4. Update OPENCLAW — sorry — update AGENTS.md project state section

## Previous Versions

| Version | Date | File | Status |
|---|---|---|---|
| V1.0.1 | April 2026 | harmony-master-spec-v1-0-1.md | Superseded |
| V1.0 | April 2026 | harmony-master-spec-v1-0-0.md | Superseded |
| V0.1 | March 2026 | harmony-master-spec-v0-1-0.md | Superseded |
```

---

## File 2: Updated CLAUDE.md

Update the existing `CLAUDE.md` at the repo root.
Keep all existing content. Add or replace the "Required Reading" section
with the following. If CLAUDE.md does not exist, create it with this content:

```markdown
# Harmony — Spatial Operating System
## Repository Context for Claude Tools

This is the Harmony project repository. Before beginning any task,
read the required documents below in order.

---

## Required Reading — Every Session

Read these three documents before writing any code or making any decision:

1. **`docs/specs/CURRENT_SPEC.md`**
   Tells you which master specification is current and links to it.
   Read the spec it points to.

2. **`docs/specs/DECISION_LOG.md`**
   Decisions made since the last spec update. These are active and binding
   even if not yet incorporated into a formal spec version.

3. **`agents/AGENTS.md`**
   Current project state, open ADRs, active pillar, and open questions.
   This is the team's shared memory.

Do not begin implementation until all three have been read.

---

## Naming Conventions

All file and folder naming follows `docs/specs/HARMONY_PROJECT_STRUCTURE.docx`.
When in doubt about where a file belongs or what to name it, consult that
document.

---

## Safety Rules

- Source code lives in `src/`. Documentation lives in `docs/`.
  These do not mix.
- Secrets never appear in prompts, logs, or filenames. `.env.example` only.
- Agents work on feature branches. Never commit directly to `main`.
- Migrations are produced, not executed. Execution requires Mikey's approval.
- ADR first, code second. No implementation without a covering ADR.
- HARMONY UPDATE line required at the end of every session.

---

## Infrastructure

This project runs on Claude Managed Agents for autonomous build execution.
Agent prompts live in `agents/prompts/`.
Security policy lives in `agents/security/SECURITY_POLICY.md`.
Managed Agents configuration lives in `agents/managed/`.

---

## Pillar Status

See `agents/AGENTS.md` for current pillar status.
See `docs/specs/CURRENT_SPEC.md` for the active specification.
See `docs/adr/ADR_INDEX.md` for all architectural decisions.
```

---

## File 3: docs/specs/DECISION_LOG.md

This file is created during Step 5 of the execution plan, populated from
the contents of `Master_Spec_Variations/`. The header for the file is:

```markdown
# Harmony — Decision Log
## Append-only. Never edit or delete existing entries.
## Add new entries at the bottom.

This log captures architectural decisions made between formal spec versions.
Every session that produces an architectural decision appends an entry here.
When a new spec version is compiled, entries are marked with the version
that incorporated them.

---

## Entry Format

### DEC-{NNN} | {YYYY-MM-DD} | {Pillar or Area}
**Decision:** What was decided.
**Impact:** What this changes in the architecture or build plan.
**ADR:** ADR-{NNN} if applicable, or "None — logged here only"
**Status:** Accepted | Pending Review
**Spec version:** V{N}.{N}.{N} if incorporated, or "Pending V1.2.0"

---

## Entries

(Populated from Master_Spec_Variations/ contents during reorganisation)
```
