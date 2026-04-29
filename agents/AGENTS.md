# Harmony Development Team
## Agent Roster | Managed Agents | April 2026

Every agent reads this file at session start.
This is the team's shared memory and current project state.

---

## The Team

| Role | Name | Model | Agent ID |
|---|---|---|---|
| Tech Lead / Orchestrator | Marcus Webb | Sonnet 4.6 | agent_011CaLKNaNDaiav7QTFMrLEQ |
| Principal Architect | Dr. Mara Voss | Opus 4.6 | agent_011CaLKZ67QqjECE8qXXq28P |
| CISO | Elena Márquez-Reid | Sonnet 4.6 | agent_011CaLKefhtwo7VhG18r5Vc1 |
| Pipeline Architect | Dr. Yusuf Adeyemi | Sonnet 4.6 | agent_011CaLKjMBoPHLCt1USvMmx7 |
| Project Manager | Jack Starling | Sonnet 4.6 | agent_011CaLKrCEVcdJrKLWWuaWKK |
| QA Engineer | Luca Ferretti | Haiku 4.5 | agent_011CaLLDTBjx7jbnirfkZCHy |
| ADR Agent | Jessica Grace Luis | Haiku 4.5 | agent_011CaLLMuxmwjh1UvbWVyNhe |
| Reviewer | Shane Rutherford | Haiku 4.5 | agent_011CaLLkoto8Q8BoZctvVRag |
| File Systems Architect | Priya Kapoor | Sonnet 4.6 | agent_011CaMszdCcbx12ZACwxeDX2 |
| Chief Geospatial Officer | Dr. Kofi Boateng | Opus 4.6 | agent_011CaMt4qhZCcUUWdJC9euGZ |
| Chief Rendering Architect | Dr. Lin Park | Opus 4.6 | agent_011CaUFF1NxkSV9sDSkKnaVj |

---

## Current Project State

Active Pillar: 2 — Data Ingestion Pipeline
Sprint 1 IN PROGRESS — dispatched to Dr. Adeyemi 2026-04-29
Schema Version: v0.2.0
Tests Passing: ~297 (pre-Sprint 1 baseline)
Sprint 1 branch: feature/p2-sprint-1-cherry-pick (not yet pushed by Adeyemi)
M7 exists as standalone module on main. M1-M6 cherry-picked from Branch B into Sprint 1 branch with 5 V2.0 compliance mods.
Dispatch package: docs/dispatch/dispatch-p2-sprint-1-20260429/
ADRs Locked: 18 (next available ADR-025)
Last Update: 29 Apr 2026

## Pillar Status

| Pillar | Name | Status |
|---|---|---|
| 1 | Spatial Substrate | COMPLETE — Stage 1, Stage 2, and fidelity API extension done |
| 2 | Data Ingestion Pipeline | ACTIVE — Sprint 1 in progress |
| 3 | Rendering Interface | PREP — framework research in progress |
| 4 | Spatial Knowledge Layer | PENDING |
| 5 | Interaction Layer | PENDING |

## Open Gates

G1 — Approve source allowlist — Sprint 1 — 15 min — THIS WEEK

## Key Documents

- docs/specs/CURRENT_SPEC.md — active specification pointer
- docs/specs/DECISION_LOG.md — decisions since last spec update
- docs/adr/ADR_INDEX.md — all architectural decisions
- agents/AUTHORITY_MATRIX.md — decision routing table
- agents/security/SECURITY_POLICY.md — security non-negotiables
- 04_pillars/pillar-2-data-ingestion/docs/HARMONY_P2_DATA_INGESTION_PIPELINE_BRIEF_V2_0.docx
