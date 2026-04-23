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

**V1.2.0 (pending)** — incorporates Pillar 1 Stage 2:
- Volumetric Cell Extension built (2026-04-20, dispatch p1-stage2-20260420)
- Schema v0.1.3 → v0.2.0 (migration produced, not executed)
- Cell key format extended with `:v{alt_min}-{alt_max}` volumetric suffix
- ADR-015 populated from stub; ADR-017 added (implementation)
- Gap 7 (Dimensional Compatibility 3D→4D) closed at substrate layer
- Decision entries: DEC-010, DEC-011, DEC-012 in DECISION_LOG.md

---

## How to Update This File

When a new master spec version is published:
1. Update the "Current Version" section above
2. Move the old version details to the "Previous Versions" section below
3. Update "Next Version In Progress" status
4. Update AGENTS.md project state section

## Previous Versions

| Version | Date | File | Status |
|---|---|---|---|
| V1.0.1 | April 2026 | harmony-master-spec-v1-0-1.md | Superseded |
| V1.0 | April 2026 | harmony-master-spec-v1-0-0.md | Superseded |
| V0.1 | March 2026 | harmony-master-spec-v0-1-0.md | Superseded |
