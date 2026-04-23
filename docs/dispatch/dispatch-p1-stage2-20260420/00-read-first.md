# 00 — Read First
## Dispatch: Pillar 1 Stage 2 — Volumetric Cell Extension
## Task ID: p1-stage2-20260420
## Tool: Claude Code

---

## Reading Order

Read every file before touching anything:

1. This file — orientation and safety rules
2. 01-agent-identity.md — who you are for this session
3. 02-harmony-context.md — what Harmony is
4. 03-pillar-state.md — current build state
5. 04-adr-summary.md — governing decisions (ADR-015 is primary)
6. 05-session-brief.md — the specific task
7. 06-security-policy.md — non-negotiables
8. 07-output-protocol.md — how to report back

Also read before starting:
- docs/specs/CURRENT_SPEC.md
- docs/specs/DECISION_LOG.md
- agents/AGENTS.md

---

## What This Dispatch Is

Pillar 1 Stage 1 is complete and validated: 8/8 acceptance criteria,
157 tests, 14 ADRs, 12 HTTP endpoints. You are building Stage 2 —
the extension of the Harmony Cell System from 2D surface tessellation
to a full 3D volumetric addressing system, from seabed to sky.

ADR-015 (Adaptive Volumetric Cell Extension) is accepted. You implement
what it specifies. You do not redesign it.

---

## The Two Non-Negotiables

1. Stage 2 is fully backward compatible. Surface cells from Stage 1
   must continue to work exactly as they do today. No Stage 1 test
   may fail after your changes.

2. Stage 2 must not foreclose the 4D temporal model. Before marking
   this session complete, confirm the v0.2.0 schema and volumetric
   cell key format are forward-compatible with a temporal suffix.
   If you find a structural reason they are not, file a BLOCKED report
   immediately.

---

## Scope

In scope: altitude fields, vertical subdivision, volumetric cell key
format, vertical adjacency, schema migration v0.1.3 to v0.2.0,
test suite for volumetric cells, ADR-016.

Out of scope: temporal fields (Pillar 4), confidence scoring (Pillar 4),
spatial type rules (Pillar 5), Pillar 2 ingestion pipeline, any API
changes not required by Stage 2.

The source tree lives at:
04_pillars/pillar-1-spatial-substrate/harmony/

All implementation work goes inside that tree. Do not create source
files anywhere else.
