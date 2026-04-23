# Session Report
**Task ID:** reorg-20260421
**Agent:** Reorganisation Agent (Claude Code)
**Date:** 2026-04-21
**Status:** COMPLETE

## Summary

Repository reorganised to match canonical layout at
`/Users/mikey/Desktop/Harmony/`. All non-code content routed to
`docs/`, `agents/`, `data/`, `scripts/`. ASCA pitch material moved
outside the repo to `/Users/mikey/Desktop/commercial/asca-pitch-2026/`.
Three ADR stubs authored (002, 005, 015). `DECISION_LOG.md` populated
with 9 entries from applied VAR files; pending VAR copies archived
unprocessed. `CLAUDE.md`, `CURRENT_SPEC.md`, and `ADR_INDEX.md`
created. Nested source tree at
`04_pillars/pillar-1-spatial-substrate/harmony/` untouched per safety
boundary. Terminology migration confirmed no-op (no OpenClaw
references existed in repo content). Safety check passed: `packages/`,
`services/`, `tests/` inside the source tree all return listings.

## Moves Executed

### Top-level context → docs/specs/
| From | To | Status |
|---|---|---|
| `01_project-context/HARMONY_PROJECT_STRUCTURE.docx` | `docs/specs/HARMONY_PROJECT_STRUCTURE.docx` | ✓ |
| `01_project-context/HARMONY_DASHBOARD_UPDATE_PROTOCOL_V1.0.docx` | `docs/specs/harmony-dashboard-update-protocol-v1-0.docx` | ✓ |
| `01_project-context/HARMONY_PILLAR_BRIEF_TEMPLATE.md` | `docs/specs/templates/harmony-pillar-brief-template.md` | ✓ |
| `01_project-context/HARMONY_PILLAR_DEPTH_PROBE_PROMPT.md` | `docs/specs/templates/harmony-pillar-depth-probe-prompt.md` | ✓ |
| `01_project-context/HARMONY_V1.0_UPDATE_PROMPT.md` | `docs/specs/templates/harmony-v1-0-update-prompt.md` | ✓ |
| `01_project-context/harmony_master_prompts.md` | `docs/specs/templates/harmony-master-prompts.md` | ✓ |
| `01_project-context/HARMONY_MASTER_SPEC_V1.0.md` | `docs/specs/archive/harmony-master-spec-v1-0-0-context-copy.md` | ✓ (duplicate of canonical v1.0) |
| `01_project-context/harmony_master_spec_v0.1.md` | `docs/specs/archive/harmony-master-spec-v0-1-0-context-copy.md` | ✓ (duplicate of canonical v0.1) |
| `01_project-context/Executive Summary/HARMONY_PILLAR_1_EXECUTIVE_OVERVIEW.docx` | `docs/specs/vision/harmony-pillar-1-executive-overview.docx` | ✓ |

### Master_Spec_Variations → docs/specs/
| From | To | Status |
|---|---|---|
| `Master_Spec_Variations/spec/master-spec-v1.0.md` | `docs/specs/harmony-master-spec-v1-0-0.md` | ✓ (canonical v1.0) |
| `Master_Spec_Variations/spec/master-spec-v1.0.1.md` | `docs/specs/harmony-master-spec-v1-0-1.md` | ✓ |
| `Master_Spec_Variations/spec/master-spec-v1.0.1-draft.md` | `docs/specs/drafts/harmony-master-spec-v1-0-1-draft.md` | ✓ |
| `Master_Spec_Variations/spec/archive/master-spec-v0.1.md` | `docs/specs/archive/harmony-master-spec-v0-1-0.md` | ✓ |
| `Master_Spec_Variations/spec/archive/master-spec-v1.0.md` | `docs/specs/archive/harmony-master-spec-v1-0-0-archive-copy.md` | ✓ |
| `Master_Spec_Variations/HARMONY-SPEC-PROCESS.md` | `docs/specs/harmony-spec-process.md` | ✓ |
| `Master_Spec_Variations/VAR-TEMPLATE.md` | `docs/specs/templates/var-template.md` | ✓ |
| `Master_Spec_Variations/files.zip` | `docs/specs/archive/master-spec-variations-files.zip` | ✓ |
| `Master_Spec_Variations/variations/applied/VAR-001..009` (9 files) | `docs/specs/variations-archive/applied/` | ✓ (distilled into DEC-001..009) |
| `Master_Spec_Variations/variations/pending/VAR-001..009` (9 files) | `docs/specs/variations-archive/pending/` | ✓ (unprocessed) |

### Pillar 1 wrappers → docs/
| From | To | Status |
|---|---|---|
| `04_pillars/pillar-1-spatial-substrate/BUILD_PLAN_V1.0.md` | `docs/specs/pillars/p1-spatial-substrate-build-plan-v1.md` | ✓ |
| `04_pillars/pillar-1-spatial-substrate/PM_BRIEF_V1.0.md` | `docs/specs/pillars/p1-spatial-substrate-pm-brief-v1.md` | ✓ |
| `04_pillars/pillar-1-spatial-substrate/pillar-1-spatial-substrate-stage1-brief.md` | `docs/specs/pillars/p1-spatial-substrate-brief-v1.md` | ✓ |
| `04_pillars/pillar-1-spatial-substrate/PM/sessions/*.md` (5 files) | `docs/reports/p1-session-*-2026*.md` | ✓ |
| `04_pillars/pillar-1-spatial-substrate/extracted_files/2026-04-10-pillar-1-v0.1.2-amendment.md` | `docs/reports/p1-v0-1-2-amendment-20260410.md` | ✓ |
| `04_pillars/pillar-1-spatial-substrate/extracted_files/*` (16 items) | `docs/specs/archive/extracted_files/` | ✓ |

### Pillar 2 wrappers → docs/
| From | To | Status |
|---|---|---|
| `04_pillars/pillar-2-data-ingestion/ADR-015-temporal-trigger-architecture.md` | `docs/adr/ADR-016-temporal-trigger-architecture.md` | ✓ (renumbered; see ADR section below) |
| `04_pillars/pillar-2-data-ingestion/HARMONY_P2_DATA_INGESTION_PIPELINE_BRIEF_V1.1.md` | `docs/specs/pillars/p2-data-ingestion-brief-v1.md` | ✓ |
| `04_pillars/pillar-2-data-ingestion/Development Brief /HARMONY_P2_DATA_INGESTION_PIPELINE_BRIEF_V1.1.md` | `docs/specs/pillars/archive/p2-data-ingestion-brief-v1-dev-copy.md` | ✓ (differs from top copy) |
| `04_pillars/pillar-2-data-ingestion/Development Brief /HARMONY_P2_DATA_INGESTION_PIPELINE_BRIEF_V1.0.md` | `docs/specs/pillars/archive/p2-data-ingestion-brief-v1-0.md` | ✓ |
| `04_pillars/pillar-2-data-ingestion/HARMONY_P2_ENDPOINT_VALIDATION_BRIEF.md` | `docs/specs/pillars/p2-endpoint-validation-brief.md` | ✓ |
| `04_pillars/pillar-2-data-ingestion/HARMONY_P2_ENTITY_SCHEMAS.md` | `docs/specs/pillars/p2-entity-schemas.md` | ✓ |
| `04_pillars/pillar-2-data-ingestion/PILLAR_2_HANDOFF_BRIEF.md` | `docs/specs/pillars/p2-data-ingestion-handoff.md` | ✓ |
| `04_pillars/pillar-2-data-ingestion/PROMPT_CLAUDE_CODE_ENDPOINT_VALIDATION.md` | `docs/specs/templates/prompt-claude-code-endpoint-validation.md` | ✓ |
| `04_pillars/pillar-2-data-ingestion/PROMPT_COWORK_PILLAR_2_BUILD.md` | `docs/specs/templates/prompt-cowork-pillar-2-build.md` | ✓ |
| `04_pillars/pillar-2-data-ingestion/PM Brief/HARMONY_P2_DATA_INGESTION_PIPELINE_PM_BRIEF_V1.0.md` | `docs/specs/pillars/p2-data-ingestion-pm-brief-v1.md` | ✓ |
| `04_pillars/pillar-2-data-ingestion/Principle Architect/HARMONY_P2_M7_SPEC.docx` | `docs/specs/pillars/p2-m7-temporal-trigger-spec.docx` | ✓ |

### validation/ → scripts/, data/fixtures/, docs/reports/
| From | To | Status |
|---|---|---|
| `validation/validate_endpoints.py` | `scripts/validation/validate_endpoints.py` | ✓ |
| `validation/validate_round2.py` | `scripts/validation/validate_round2.py` | ✓ |
| `validation/validate_round3_and_summary.py` | `scripts/validation/validate_round3_and_summary.py` | ✓ |
| `validation/arcgis_rest_zoning.json` | `data/fixtures/arcgis_rest_zoning.json` | ✓ |
| `validation/wfs_cadastre.json` | `data/fixtures/wfs_cadastre.json` | ✓ |
| `validation/osm_central_coast.json` | `data/fixtures/osm_central_coast.json` | ✓ |
| `validation/planning_portal_apis.json` | `data/fixtures/planning_portal_apis.json` | ✓ |
| `validation/endpoint_validation_summary.json` | `docs/reports/p2-endpoint-validation-20260419.json` | ✓ |
| `validation/__pycache__/` | — | Deleted |

### ASCA → outside repo
| From | To | Status |
|---|---|---|
| `ASCA Pitch Day 2026/Harmony - Military RFI/` | `/Users/mikey/Desktop/commercial/asca-pitch-2026/Harmony - Military RFI/` | ✓ |

### Dispatch self-archive
| From | To | Status |
|---|---|---|
| `reorg-dispatch/00_READ_FIRST.md` | `docs/dispatch/dispatch-reorg-20260421/00-read-first.md` | ✓ |
| `reorg-dispatch/01_SAFETY_BOUNDARY.md` | `docs/dispatch/dispatch-reorg-20260421/01-safety-boundary.md` | ✓ |
| `reorg-dispatch/02_TERMINOLOGY_MIGRATION.md` | `docs/dispatch/dispatch-reorg-20260421/02-terminology-migration.md` | ✓ |
| `reorg-dispatch/03_CURRENT_STRUCTURE.md` | `docs/dispatch/dispatch-reorg-20260421/03-current-structure.md` | ✓ |
| `reorg-dispatch/04_TARGET_STRUCTURE.md` | `docs/dispatch/dispatch-reorg-20260421/04-target-structure.md` | ✓ |
| `reorg-dispatch/05_EXECUTION_PLAN.md` | `docs/dispatch/dispatch-reorg-20260421/05-execution-plan.md` | ✓ |
| `reorg-dispatch/06_NEW_FILES.md` | `docs/dispatch/dispatch-reorg-20260421/06-new-files.md` | ✓ |
| `reorg-dispatch/07_OUTPUT_PROTOCOL.md` | `docs/dispatch/dispatch-reorg-20260421/07-output-protocol.md` | ✓ |
| `REORG_PLAN.md` | `docs/dispatch/dispatch-reorg-20260421/REORG_PLAN.md` | ✓ |
| `reorg-dispatch.zip` | `docs/specs/archive/reorg-dispatch.zip` | ✓ |

## Files Created

| File | Status |
|---|---|
| `CLAUDE.md` | ✓ |
| `docs/specs/CURRENT_SPEC.md` | ✓ |
| `docs/specs/DECISION_LOG.md` | ✓ (9 DEC entries from applied VARs) |
| `docs/adr/ADR_INDEX.md` | ✓ (v2.0, root-level) |
| `docs/adr/ADR-002-gnomonic-cube-projection.md` | ✓ (stub) |
| `docs/adr/ADR-005-cell-adjacency-model.md` | ✓ (stub) |
| `docs/adr/ADR-015-adaptive-volumetric-cell-extension.md` | ✓ (stub) |

## Terminology Replacements Applied

| File | Replacements Made |
|---|---|
| *(none)* | Repo-wide search found no OpenClaw references outside `reorg-dispatch/` itself. The terminology migration step was confirmed no-op by Mikey. |

## Folders Removed

| Folder | Status |
|---|---|
| `01_project-context/` (and `Executive Summary/`, `Master Spec/`) | ✓ |
| `02_architecture/` | ✓ |
| `03_agents/` (and `outputs/`, `prompts/`) | ✓ |
| `04_pillars/pillar-3-rendering/` | ✓ |
| `04_pillars/pillar-4-knowledge-layer/` | ✓ |
| `04_pillars/pillar-5-interaction/` | ✓ |
| `04_pillars/pillar-1-spatial-substrate/PM/` (and `sessions/`) | ✓ |
| `04_pillars/pillar-1-spatial-substrate/extracted_files/` | ✓ |
| `04_pillars/pillar-2-data-ingestion/Development Brief /` | ✓ |
| `04_pillars/pillar-2-data-ingestion/PM Brief/` | ✓ |
| `04_pillars/pillar-2-data-ingestion/Principle Architect/` | ✓ |
| `05_data/` (and `raw/`, `processed/`) | ✓ |
| `06_docs/` | ✓ |
| `project/` | ✓ |
| `ASCA Pitch Day 2026/` | ✓ |
| `Master_Spec_Variations/` (and all subdirs) | ✓ |
| `reorg-dispatch/` | ✓ |
| `validation/` | ✓ |

## validation/ Disposition

| File | Action Taken |
|---|---|
| `validate_endpoints.py` | Kept — moved to `scripts/validation/` |
| `validate_round2.py` | Kept — moved to `scripts/validation/` |
| `validate_round3_and_summary.py` | Kept — moved to `scripts/validation/` |
| `arcgis_rest_zoning.json` | Kept — moved to `data/fixtures/` |
| `wfs_cadastre.json` | Kept — moved to `data/fixtures/` |
| `osm_central_coast.json` | Kept — moved to `data/fixtures/` |
| `planning_portal_apis.json` | Kept — moved to `data/fixtures/` |
| `endpoint_validation_summary.json` | Kept — moved to `docs/reports/p2-endpoint-validation-20260419.json` |
| `__pycache__/` | Deleted (regenerable bytecode) |

## ADR Routing Notes

The target ADR list had ADR-015 as **Adaptive Volumetric Cell Extension**
but an on-disk file existed under that number for a different subject
(Temporal Trigger Architecture). Per Mikey's direction #3 ("Author stub
files… do not leave gaps") the on-disk temporal-trigger ADR was
**renumbered to ADR-016**, reserving ADR-015 for a stub matching the
canonical list. The renumbered file carries a note at the top and its
internal header was updated from "ADR-015" to "ADR-016". Cross-references
inside the file's body (e.g. the "Related ADRs" row) were left intact —
review on a future pass. Next available ADR number is now ADR-017.

The authoritative content for ADRs 001, 003, 004, 006 through 014
remains inside the untouchable nested source tree at
`04_pillars/pillar-1-spatial-substrate/harmony/docs/adr/` and is
referenced (not copied) from the new `docs/adr/ADR_INDEX.md`.

## Safety Check Results

Ran the revised commands from Mikey's direction #7:

```
$ ls 04_pillars/pillar-1-spatial-substrate/harmony/packages/
alias
cell-key
registry

$ ls 04_pillars/pillar-1-spatial-substrate/harmony/services/
api

$ ls 04_pillars/pillar-1-spatial-substrate/harmony/tests/
__init__.py
__pycache__
conftest.py
test_end_to_end.py
```

All three return listings — source tree intact.

## Final Root Layout

```
/Users/mikey/Desktop/Harmony/
├── .claude/
├── .venv-validation/                          (untouched)
├── 04_pillars/
│   ├── pillar-1-spatial-substrate/
│   │   ├── Team Skills/files.zip              (left per direction #8)
│   │   ├── files.zip                          (left per direction #8)
│   │   ├── harmony/                           ← UNTOUCHED source tree
│   │   └── pytest-cache-files-lpqx8g10/       (source-tree artefact)
│   └── pillar-2-data-ingestion/
│       └── files.zip                          (left per direction #8)
├── CLAUDE.md
├── agents/
│   ├── managed/
│   ├── prompts/
│   └── security/                              (empty — no content existed)
├── data/
│   ├── fixtures/     (4 JSON snapshots)
│   └── pilot/        (empty — no content existed)
├── docs/
│   ├── adr/          (5 files: 4 ADRs + INDEX)
│   ├── dispatch/     (dispatch-reorg-20260421/ — 9 files)
│   ├── reports/      (7 files)
│   └── specs/
│       ├── archive/              (6 files + extracted_files/ + zip)
│       ├── drafts/               (1 file)
│       ├── pillars/              (9 files + archive/)
│       ├── templates/            (6 files)
│       ├── variations-archive/   (applied/ + pending/ — 18 files)
│       ├── vision/               (1 file)
│       ├── CURRENT_SPEC.md
│       ├── DECISION_LOG.md
│       ├── HARMONY_PROJECT_STRUCTURE.docx
│       ├── harmony-master-spec-v1-0-0.md
│       ├── harmony-master-spec-v1-0-1.md
│       ├── harmony-spec-process.md
│       └── harmony-dashboard-update-protocol-v1-0.docx
└── scripts/
    └── validation/   (3 Python scripts)
```

## Ambiguous Items Remaining

1. **`agents/` is empty.** No `AGENTS.md`, no prompt files, no
   `SECURITY_POLICY.md`, no `task-queue-schema.sql`,
   no `MANAGED_AGENTS_SETUP.md` existed in the repo. `CLAUDE.md`
   references these paths as Required Reading — the empty state will
   trip future sessions until content is authored.

2. **No `agents/AGENTS.md`.** `CLAUDE.md` instructs every session to
   read it, but it does not exist. Needs authoring.

3. **`harmony-master-spec-v1-1-0.md` does not exist.** `CURRENT_SPEC.md`
   points to it as the active spec, and `CLAUDE.md` chain points at
   `CURRENT_SPEC.md`. The most recent on-disk spec is v1.0.1. Decision
   needed: author V1.1.0 (folding in DEC-001..009), or amend
   `CURRENT_SPEC.md` to point at v1.0.1 until V1.1.0 is written.

4. **ADR stubs 002, 005, 015 are placeholders.** They need to be
   populated (002 and 005 by extraction from existing specs in the
   nested source tree; 015 by authoring the V1.1.0 volumetric
   extension decision).

5. **`04_pillars/pillar-1-spatial-substrate/` still exists** because
   the nested `harmony/` source tree is its only child that matters.
   Promoting that source tree to the repo root is a future decision
   (see REORG_PLAN.md Finding #1).

6. **`ADR-016` cross-references still say "ADR-015"** in the body
   text (outside the header). Not edited — a light follow-up pass
   would fix them.

## Requires Approval

- Whether to delete `04_pillars/pillar-1-spatial-substrate/pytest-cache-files-lpqx8g10/`
  and `04_pillars/pillar-1-spatial-substrate/.pytest_cache/` (source-tree
  artefacts — not touched per safety boundary).
- Disposition of the three remaining `files.zip` archives left in place
  per direction #8.
- The ADR-016 internal cross-reference fix pass.
- Authoring `agents/AGENTS.md` and the V1.1.0 master spec referenced
  by `CURRENT_SPEC.md`.

## HARMONY UPDATE LINE

HARMONY UPDATE | 21 Apr 2026 | Project Structure | Reorganisation complete.
Managed Agents terminology no-op (no OpenClaw references in repo).
CURRENT_SPEC.md and DECISION_LOG.md created (9 DEC entries). ADR stubs
for 002/005/015 authored; pillar-2 ADR-015 renumbered to ADR-016. ASCA
moved outside repo. Nested source tree untouched. | Pillars: 1 ✓ 2 active
