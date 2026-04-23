# 04_TARGET_STRUCTURE.md
## Target Folder Structure — Canonical Layout

---

## The Harmony Repo

```
harmony/
│
├── CLAUDE.md                          ← Updated — see 06_NEW_FILES.md
├── README.md                          ← Unchanged
├── docker-compose.yml                 ← Unchanged
├── .env.example                       ← Unchanged
│
├── docs/
│   ├── adr/
│   │   ├── ADR_INDEX.md               ← Canonical ADR sequence
│   │   ├── ADR-001-layered-identity-model.md
│   │   ├── ADR-002-gnomonic-cube-projection.md
│   │   ├── ADR-003-cell-key-derivation.md
│   │   ├── ADR-004-dual-identifier-principle.md
│   │   ├── ADR-005-cell-adjacency-model.md
│   │   ├── ADR-006-alias-namespace-model.md
│   │   ├── ADR-007-temporal-versioning.md
│   │   ├── ADR-008-named-entity-resolution-boundary.md
│   │   ├── ADR-009-three-layer-agent-model.md
│   │   ├── ADR-010-spatial-geometry-schema.md
│   │   ├── ADR-011-identity-generation-order.md
│   │   ├── ADR-012-alias-generation-architecture.md
│   │   ├── ADR-013-api-layer-architecture.md
│   │   ├── ADR-014-pillar-1-stage-1-completion.md
│   │   └── ADR-015-adaptive-volumetric-cell-extension.md
│   │
│   ├── specs/
│   │   ├── CURRENT_SPEC.md            ← NEW — stable pointer (see 06_NEW_FILES.md)
│   │   ├── DECISION_LOG.md            ← NEW — replaces Master_Spec_Variations
│   │   ├── HARMONY_PROJECT_STRUCTURE.docx  ← The document just produced
│   │   ├── harmony-master-spec-v1-1-0.md   ← Current master spec
│   │   ├── pillars/
│   │   │   ├── p1-spatial-substrate-brief-v1.md
│   │   │   ├── p1-stage1-completion-report.md
│   │   │   ├── p2-data-ingestion-brief-v1.md
│   │   │   ├── p2-m7-temporal-trigger-spec.md
│   │   │   └── p2-data-ingestion-handoff.md
│   │   └── vision/
│   │       └── (early vision and context documents)
│   │
│   ├── dispatch/
│   │   └── dispatch-p1-stage2-20260420/
│   │       ├── 00-read-first.md
│   │       ├── 01-agent-identity.md
│   │       ├── 02-harmony-context.md
│   │       ├── 03-pillar-state.md
│   │       ├── 04-adr-summary.md
│   │       ├── 05-session-brief.md
│   │       ├── 06-security-policy.md
│   │       └── 07-output-protocol.md
│   │
│   └── reports/
│       └── (session output reports filed here)
│
├── src/
│   ├── core/                          ← UNTOUCHED
│   ├── api/                           ← UNTOUCHED
│   ├── db/
│   │   ├── migrations/                ← UNTOUCHED
│   │   └── schemas/                   ← UNTOUCHED
│   └── ingestion/                     ← UNTOUCHED
│
├── tests/
│   ├── core/                          ← UNTOUCHED
│   ├── api/                           ← UNTOUCHED
│   ├── db/                            ← UNTOUCHED
│   └── ingestion/                     ← UNTOUCHED (validation/ contents reviewed here)
│
├── agents/
│   ├── AGENTS.md                      ← Renamed from OPENCLAW.md, terminology updated
│   ├── prompts/
│   │   ├── DR_MARA_VOSS.md
│   │   ├── TECH_LEAD.md
│   │   ├── SPATIAL_ENGINEER.md
│   │   ├── BACKEND_ENGINEER.md
│   │   ├── QA_AGENT.md
│   │   ├── ADR_AGENT.md
│   │   └── REVIEWER.md
│   ├── security/
│   │   └── SECURITY_POLICY.md
│   └── managed/
│       ├── MANAGED_AGENTS_SETUP.md    ← Renamed from ORCHESTRATOR.md
│       └── task-queue-schema.sql
│
└── data/
    ├── pilot/
    │   └── (Central Coast NSW datasets)
    └── fixtures/
        └── (test fixtures)
```

---

## Outside the Repo

```
~/harmony-project/              ← or wherever parent lives
├── harmony/                    ← the repo above
└── commercial/
    └── asca-pitch-2026/        ← ASCA military RFI (moved from inside repo)
```

---

## Naming Rules Applied

Every file in `docs/` follows the conventions from `HARMONY_PROJECT_STRUCTURE.docx`:

- Lowercase with hyphens for all filenames
- ADRs: `ADR-{NNN}-{slug}.md`
- Specs: `harmony-master-spec-v{N}-{N}-{N}.md`
- Pillar docs: `p{N}-{slug}-brief-v{N}.md`
- Reports: `p{N}-m{N}-report-{YYYYMMDD}.md`
- Dispatch folders: `dispatch-p{N}-{slug}-{YYYYMMDD}/`
- Numbers inside dispatch folders: `{NN}-{slug}.md` (two-digit prefix)
