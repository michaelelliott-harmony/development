# Reorganisation Plan
## Task ID: reorg-20260421
## Status: AWAITING APPROVAL — do not execute until approved

---

## Critical Findings Before You Read the Tables

Four issues arose while surveying the filesystem that the dispatch
assumptions do not match. Please resolve these before Phase 2.

1. **The repo does not have the assumed root layout.**
   The dispatch assumes the Harmony repo root has `src/`, `tests/`,
   `docker-compose.yml`, `.env`, `.env.example`. None of these exist at
   `/Users/mikey/Desktop/Harmony/`. The actual Harmony code lives nested
   at `04_pillars/pillar-1-spatial-substrate/harmony/` and uses
   `packages/ + services/` instead of `src/`. Safety boundaries in
   `01_SAFETY_BOUNDARY.md` must be understood as applying to that
   nested code tree, not to a top-level `src/`. This changes what Step
   1 means (creating a `docs/` tree at `/Users/mikey/Desktop/Harmony/`
   vs. at the nested harmony path). **Decision needed: which path is
   the canonical repo root for this reorganisation?**

2. **No OpenClaw material exists in the repo.**
   The terminology migration file lists `openclaw/` folders,
   `OPENCLAW.md`, `ORCHESTRATOR.md`, `schema.sql`, and agent prompt
   files (`TECH_LEAD.md`, etc.) to rename and migrate. None of these
   files exist. `03_agents/` contains only empty `outputs/` and
   `prompts/` subdirectories. A repo-wide search for
   `OpenClaw|openclaw|OPENCLAW` returns hits only inside
   `reorg-dispatch/` itself. The terminology migration therefore has
   no documentation targets in this repo — Steps 6 and the
   "Terminology Replacements" table will be empty. **Decision needed:
   confirm no OpenClaw files exist and Steps 6/terminology migration
   are no-ops, or point me at the missing source.**

3. **ADRs on disk do not fully match the target ADR list.**
   - ADR-002 `gnomonic-cube-projection` does not exist as a standalone
     file (embedded inside `cell_geometry_spec.md` per `ADR_INDEX.md`).
   - ADR-005 `cell-adjacency-model` does not exist on disk (absent
     from `harmony/docs/adr/`; `ADR_INDEX.md` lists it as Accepted).
   - ADR-015 on disk is `ADR-015-temporal-trigger-architecture.md` in
     pillar-2. The target lists ADR-015 as
     `adaptive-volumetric-cell-extension`. These are different
     subjects — not a rename.
   These are either content gaps or a target-list mismatch.
   **Decision needed: skip the missing ADRs, or flag for later
   authorship?**

4. **`Master_Spec_Variations/spec/` holds live master specs, not
   variations.** It contains `master-spec-v1.0.md` (read-only),
   `master-spec-v1.0.1.md`, `master-spec-v1.0.1-draft.md`, and an
   `archive/` subfolder with v0.1 and v1.0. The dispatch says to
   "convert to DECISION_LOG.md entries" for everything in
   `Master_Spec_Variations/`. These are authoritative spec files, not
   decision records. I plan to route them to `docs/specs/` with proper
   naming (`harmony-master-spec-vN-N-N.md`) and convert only the VAR
   files to DECISION_LOG. **Decision needed: confirm that split.**

---

## Files to Move

Paths are relative to `/Users/mikey/Desktop/Harmony/`. "New root"
refers to the chosen canonical repo root — I have drafted the plan
assuming the root stays at `/Users/mikey/Desktop/Harmony/` (i.e. the
nested `harmony/` inside pillar-1 is left alone as untouchable source
code). Revise if you want the root to move.

### Top-level context → docs/specs/

| Current Path | Target Path | Action | Notes |
|---|---|---|---|
| `01_project-context/HARMONY_MASTER_SPEC_V1.0.md` | `docs/specs/harmony-master-spec-v1-0-0.md` | Rename + Move | Same content as `Master_Spec_Variations/spec/archive/master-spec-v1.0.md` — flag duplicate |
| `01_project-context/HARMONY_DASHBOARD_UPDATE_PROTOCOL_V1.0.docx` | `docs/specs/harmony-dashboard-update-protocol-v1-0.docx` | Rename + Move | |
| `01_project-context/HARMONY_PILLAR_BRIEF_TEMPLATE.md` | `docs/specs/templates/harmony-pillar-brief-template.md` | Rename + Move | `templates/` subfolder not in target tree — flag |
| `01_project-context/HARMONY_PILLAR_DEPTH_PROBE_PROMPT.md` | `docs/specs/templates/harmony-pillar-depth-probe-prompt.md` | Rename + Move | same |
| `01_project-context/HARMONY_PROJECT_STRUCTURE.docx` | `docs/specs/HARMONY_PROJECT_STRUCTURE.docx` | Move | Target keeps exact filename |
| `01_project-context/HARMONY_V1.0_UPDATE_PROMPT.md` | `docs/specs/templates/harmony-v1-0-update-prompt.md` | Rename + Move | |
| `01_project-context/harmony_master_prompts.md` | `docs/specs/templates/harmony-master-prompts.md` | Rename + Move | |
| `01_project-context/harmony_master_spec_v0.1.md` | `docs/specs/harmony-master-spec-v0-1-0.md` | Rename + Move | Same content as `Master_Spec_Variations/spec/archive/master-spec-v0.1.md` — flag duplicate |
| `01_project-context/Executive Summary/HARMONY_PILLAR_1_EXECUTIVE_OVERVIEW.docx` | `docs/specs/vision/harmony-pillar-1-executive-overview.docx` | Rename + Move | |
| `01_project-context/Master Spec/` | — | Remove after move | Empty directory |
| `01_project-context/.DS_Store` | — | Leave | macOS artefact; delete in cleanup step |

### Master_Spec_Variations → docs/specs/ + DECISION_LOG.md

| Current Path | Target Path | Action | Notes |
|---|---|---|---|
| `Master_Spec_Variations/spec/master-spec-v1.0.md` | `docs/specs/harmony-master-spec-v1-0-0.md` | Rename + Move | Read-only perms on source; prefer this copy over `01_project-context/HARMONY_MASTER_SPEC_V1.0.md` (larger or equal); confirm duplicate dispatch |
| `Master_Spec_Variations/spec/master-spec-v1.0.1.md` | `docs/specs/harmony-master-spec-v1-0-1.md` | Rename + Move | |
| `Master_Spec_Variations/spec/master-spec-v1.0.1-draft.md` | `docs/specs/drafts/harmony-master-spec-v1-0-1-draft.md` | Rename + Move | `drafts/` subfolder not in target — flag |
| `Master_Spec_Variations/spec/archive/master-spec-v0.1.md` | `docs/specs/archive/harmony-master-spec-v0-1-0.md` | Rename + Move | Read-only perms |
| `Master_Spec_Variations/spec/archive/master-spec-v1.0.md` | `docs/specs/archive/harmony-master-spec-v1-0-0.md` | Rename + Move | Will collide with primary v1.0 above — keep as archive only |
| `Master_Spec_Variations/HARMONY-SPEC-PROCESS.md` | `docs/specs/harmony-spec-process.md` | Rename + Move | Governance doc; not a VAR |
| `Master_Spec_Variations/VAR-TEMPLATE.md` | `docs/specs/templates/var-template.md` | Rename + Move | |
| `Master_Spec_Variations/variations/applied/VAR-001-layered-identity-model.md` | — | Convert → `docs/specs/DECISION_LOG.md` entry DEC-001 | Then move original to `docs/specs/variations-archive/applied/` |
| `Master_Spec_Variations/variations/applied/VAR-002-two-identifier-substrate.md` | — | Convert → DEC-002 | archive original |
| `Master_Spec_Variations/variations/applied/VAR-003-bitemporal-versioning.md` | — | Convert → DEC-003 | archive original |
| `Master_Spec_Variations/variations/applied/VAR-004-named-entity-resolution.md` | — | Convert → DEC-004 | archive original |
| `Master_Spec_Variations/variations/applied/VAR-005-federation-compatible-identity.md` | — | Convert → DEC-005 | archive original |
| `Master_Spec_Variations/variations/applied/VAR-006-three-layer-agent-model.md` | — | Convert → DEC-006 | archive original |
| `Master_Spec_Variations/variations/applied/VAR-007-schema-field-additions.md` | — | Convert → DEC-007 | archive original |
| `Master_Spec_Variations/variations/applied/VAR-008-gap-register-updates.md` | — | Convert → DEC-008 | archive original |
| `Master_Spec_Variations/variations/applied/VAR-009-harmony-cell-system-commitment.md` | — | Convert → DEC-009 | archive original |
| `Master_Spec_Variations/variations/pending/VAR-001..009-*.md` (9 files) | `docs/specs/variations-archive/pending/` | Move | Older/identical-titled PENDING copies — confirm they can be archived without a DEC entry (likely superseded by applied versions) |
| `Master_Spec_Variations/decisions/` | — | Remove after move | Empty directory |
| `Master_Spec_Variations/untitled folder/` | — | Flag | Empty directory of unknown purpose — remove in cleanup |
| `Master_Spec_Variations/files.zip` | `docs/specs/archive/master-spec-variations-files.zip` | Move | Zip blob — keep or delete? Flagged |
| `Master_Spec_Variations/.DS_Store` | — | Leave / cleanup | |

### Pillar 1 folder → docs/specs/pillars/ + docs/adr/ + docs/reports/

| Current Path | Target Path | Action | Notes |
|---|---|---|---|
| `04_pillars/pillar-1-spatial-substrate/BUILD_PLAN_V1.0.md` | `docs/specs/pillars/p1-spatial-substrate-build-plan-v1.md` | Rename + Move | |
| `04_pillars/pillar-1-spatial-substrate/PM_BRIEF_V1.0.md` | `docs/specs/pillars/p1-spatial-substrate-pm-brief-v1.md` | Rename + Move | |
| `04_pillars/pillar-1-spatial-substrate/pillar-1-spatial-substrate-stage1-brief.md` | `docs/specs/pillars/p1-spatial-substrate-brief-v1.md` | Rename + Move | Matches target name |
| `04_pillars/pillar-1-spatial-substrate/PM/sessions/2026-04-18-pillar-1-adr-renumbering.md` | `docs/reports/p1-session-adr-renumber-20260418.md` | Rename + Move | |
| `04_pillars/pillar-1-spatial-substrate/PM/sessions/2026-04-18-pillar-1-session-4-alias-system.md` | `docs/reports/p1-session-4-alias-system-20260418.md` | Rename + Move | |
| `04_pillars/pillar-1-spatial-substrate/PM/sessions/2026-04-19-pillar-1-session-5-api-layer.md` | `docs/reports/p1-session-5-api-layer-20260419.md` | Rename + Move | |
| `04_pillars/pillar-1-spatial-substrate/PM/sessions/2026-04-19-pillar-1-session-5b-fixup.md` | `docs/reports/p1-session-5b-fixup-20260419.md` | Rename + Move | |
| `04_pillars/pillar-1-spatial-substrate/PM/sessions/2026-04-19-pillar-1-session-6-e2e-acceptance.md` | `docs/reports/p1-session-6-e2e-acceptance-20260419.md` | Rename + Move | |
| `04_pillars/pillar-1-spatial-substrate/PM/.DS_Store` | — | Cleanup | |
| `04_pillars/pillar-1-spatial-substrate/.DS_Store` | — | Cleanup | |
| `04_pillars/pillar-1-spatial-substrate/Team Skills/files.zip` | Flag | Do not move | Binary blob; intent unknown |
| `04_pillars/pillar-1-spatial-substrate/files.zip` | Flag | Do not move | Binary blob; intent unknown |
| `04_pillars/pillar-1-spatial-substrate/extracted_files/*.md` (12 files) | — | Flag for deletion/archive | These are older copies of files already present in `harmony/docs/` — duplicates. See Ambiguous Files section. |
| `04_pillars/pillar-1-spatial-substrate/extracted_files/*.json` (2 files) | Flag | Likely outdated fixtures | |
| `04_pillars/pillar-1-spatial-substrate/extracted_files/mnt/user-data/outputs/milestone-1-v0.1.2-amendment/PM/README.md` | Flag for deletion | Stale extraction artefact | |
| `04_pillars/pillar-1-spatial-substrate/.pytest_cache/` | — | Untouchable / cleanup candidate | Source-tree artefact — defer to Mikey |
| `04_pillars/pillar-1-spatial-substrate/.venv/` | — | **DO NOT MOVE** | Python venv — source-related, keep in place |
| `04_pillars/pillar-1-spatial-substrate/harmony/` | **DO NOT MOVE** | — | Nested code repo; treat as source (see Finding #1) |
| `04_pillars/pillar-1-spatial-substrate/pytest-cache-files-lpqx8g10/` | — | Flag | Source-tree artefact |

### Pillar 2 folder → docs/specs/pillars/ + docs/adr/

| Current Path | Target Path | Action | Notes |
|---|---|---|---|
| `04_pillars/pillar-2-data-ingestion/ADR-015-temporal-trigger-architecture.md` | `docs/adr/ADR-015-temporal-trigger-architecture.md` | Move | Title mismatch with target list's ADR-015 — flagged in Finding #3 |
| `04_pillars/pillar-2-data-ingestion/HARMONY_P2_DATA_INGESTION_PIPELINE_BRIEF_V1.1.md` | `docs/specs/pillars/p2-data-ingestion-brief-v1.md` | Rename + Move | Matches target |
| `04_pillars/pillar-2-data-ingestion/HARMONY_P2_ENDPOINT_VALIDATION_BRIEF.md` | `docs/specs/pillars/p2-endpoint-validation-brief.md` | Rename + Move | |
| `04_pillars/pillar-2-data-ingestion/HARMONY_P2_ENTITY_SCHEMAS.md` | `docs/specs/pillars/p2-entity-schemas.md` | Rename + Move | |
| `04_pillars/pillar-2-data-ingestion/PILLAR_2_HANDOFF_BRIEF.md` | `docs/specs/pillars/p2-data-ingestion-handoff.md` | Rename + Move | Matches target |
| `04_pillars/pillar-2-data-ingestion/PROMPT_CLAUDE_CODE_ENDPOINT_VALIDATION.md` | `docs/specs/templates/prompt-claude-code-endpoint-validation.md` | Rename + Move | |
| `04_pillars/pillar-2-data-ingestion/PROMPT_COWORK_PILLAR_2_BUILD.md` | `docs/specs/templates/prompt-cowork-pillar-2-build.md` | Rename + Move | |
| `04_pillars/pillar-2-data-ingestion/Development Brief /HARMONY_P2_DATA_INGESTION_PIPELINE_BRIEF_V1.0.md` | `docs/specs/pillars/archive/p2-data-ingestion-brief-v1-0.md` | Rename + Move | Older v1.0 of same brief; archive |
| `04_pillars/pillar-2-data-ingestion/Development Brief /HARMONY_P2_DATA_INGESTION_PIPELINE_BRIEF_V1.1.md` | Flag duplicate | — | Identical to top-level v1.1 copy — pick one canonical, archive other |
| `04_pillars/pillar-2-data-ingestion/PM Brief/HARMONY_P2_DATA_INGESTION_PIPELINE_PM_BRIEF_V1.0.md` | `docs/specs/pillars/p2-data-ingestion-pm-brief-v1.md` | Rename + Move | |
| `04_pillars/pillar-2-data-ingestion/Principle Architect/HARMONY_P2_M7_SPEC.docx` | `docs/specs/pillars/p2-m7-temporal-trigger-spec.docx` | Rename + Move | Target expects `.md` — flag format mismatch |
| `04_pillars/pillar-2-data-ingestion/files.zip` | Flag | Do not move | Binary blob |
| `04_pillars/pillar-2-data-ingestion/.DS_Store` | — | Cleanup | |

### Empty pillar folders

| Path | Action |
|---|---|
| `04_pillars/pillar-3-rendering/` | Remove in cleanup |
| `04_pillars/pillar-4-knowledge-layer/` | Remove in cleanup |
| `04_pillars/pillar-5-interaction/` | Remove in cleanup |

### ASCA → outside repo

| Current Path | Target Path | Action | Notes |
|---|---|---|---|
| `ASCA Pitch Day 2026/Harmony - Military RFI/files.zip` | `../commercial/asca-pitch-2026/Harmony - Military RFI/files.zip` | Move | Must create parent `../commercial/` |
| `ASCA Pitch Day 2026/` | — | Remove after move | |

### Data folders

Both `05_data/raw/` and `05_data/processed/` are empty. No pilot data
files are present in this repo root. The only sample data file found
is `04_pillars/pillar-1-spatial-substrate/harmony/data/sample-central-coast-records.json`
which sits inside the untouchable nested code repo — do not move.

| Current Path | Target Path | Action | Notes |
|---|---|---|---|
| `05_data/raw/` | `data/pilot/` | Remove source, create target empty | No files to move |
| `05_data/processed/` | `data/fixtures/` | Remove source, create target empty | No files to move |

### Agents

No OpenClaw/agent prompt files exist anywhere in the repo. `03_agents/`
contains only empty subdirectories.

| Current Path | Target Path | Action | Notes |
|---|---|---|---|
| `03_agents/outputs/` | — | Remove in cleanup | Empty |
| `03_agents/prompts/` | `agents/prompts/` | Move (empty) or just create new | Either way ends up empty |
| `03_agents/.DS_Store` | — | Cleanup | |

### Root-level misc

| Current Path | Target Path | Action | Notes |
|---|---|---|---|
| `reorg-dispatch/` | Leave in place through Phase 2, then `docs/dispatch/dispatch-reorg-20260421/` | Move after execution | Self-archive after success |
| `reorg-dispatch.zip` | Flag | Do not move | Source of the dispatch package |
| `project/` | — | Remove in cleanup | Empty directory |
| `.venv-validation/` | Leave | — | Source-related |
| `.claude/settings.local.json` | Leave | — | Claude Code local settings |
| `.DS_Store` at root | — | Cleanup | |

---

## Files to Create

| Target Path | Source |
|---|---|
| `docs/specs/CURRENT_SPEC.md` | New file per `06_NEW_FILES.md` File 1 |
| `docs/specs/DECISION_LOG.md` | Header per `06_NEW_FILES.md` File 3 + 9 entries populated from `Master_Spec_Variations/variations/applied/` |
| `CLAUDE.md` | New file at repo root per `06_NEW_FILES.md` File 2 (no existing `CLAUDE.md` at root to update) |
| `docs/adr/ADR_INDEX.md` | Move-and-update from `04_pillars/pillar-1-spatial-substrate/harmony/docs/ADR_INDEX.md`? — **flag**, see Ambiguous Files |

---

## validation/ Contents

| File | Size | Recommendation | Reason |
|---|---|---|---|
| `validate_endpoints.py` | 31 KB | **Keep → `tests/ingestion/` or `scripts/validation/`** | Real test/validation script for Pillar 2 endpoints; would be lost if deleted. Target location ambiguous because no `tests/ingestion/` exists at the chosen root — **flag** |
| `validate_round2.py` | 21 KB | **Keep → same target** | Continuation of above |
| `validate_round3_and_summary.py` | 15 KB | **Keep → same target** | Final round + summary generator |
| `arcgis_rest_zoning.json` | 17 KB | **Keep → `data/fixtures/`** | Endpoint response snapshot (Central Coast zoning) |
| `wfs_cadastre.json` | 19 KB | **Keep → `data/fixtures/`** | Endpoint response snapshot (cadastre) |
| `osm_central_coast.json` | 5 KB | **Keep → `data/fixtures/`** | OSM snapshot |
| `planning_portal_apis.json` | 3 KB | **Keep → `data/fixtures/`** | Planning portal catalogue |
| `endpoint_validation_summary.json` | 7 KB | **Keep → `docs/reports/p2-endpoint-validation-20260419.json`** | Summary report artefact — reference material |
| `__pycache__/validate_round2.cpython-314.pyc` | 25 KB | **Delete (flag)** | Python bytecode, regenerable |
| `__pycache__/` | folder | **Delete (flag)** | Container above |

All validation/ files were produced on 2026-04-19/20 during Pillar 2
endpoint validation. None appear to be ephemeral build artefacts
other than the pycache.

---

## Terminology Replacements

| File | Occurrences of "OpenClaw" | Action |
|---|---|---|
| *(repo-wide search)* | 0 outside `reorg-dispatch/` itself | **No replacements needed in repo content** |
| `reorg-dispatch/*.md` (7 files, 24 matches) | — | Leave untouched — dispatch is self-archiving |

The terminology migration described in `02_TERMINOLOGY_MIGRATION.md`
has zero files to update in the actual repo. See Finding #2.

---

## Empty Folders After Moves

| Folder | Safe to Remove? |
|---|---|
| `01_project-context/Master Spec/` | Yes |
| `01_project-context/Executive Summary/` | Yes (after overview moved) |
| `01_project-context/` | Yes (after all files moved) |
| `02_architecture/` | Yes (already empty) |
| `03_agents/outputs/` | Yes (already empty) |
| `03_agents/prompts/` | Yes (already empty) |
| `03_agents/` | Yes |
| `04_pillars/pillar-3-rendering/` | Yes (already empty) |
| `04_pillars/pillar-4-knowledge-layer/` | Yes (already empty) |
| `04_pillars/pillar-5-interaction/` | Yes (already empty) |
| `04_pillars/pillar-1-spatial-substrate/PM/sessions/` | Yes (after moves) |
| `04_pillars/pillar-1-spatial-substrate/PM/` | Yes |
| `04_pillars/pillar-2-data-ingestion/Development Brief /` | Yes (after moves) |
| `04_pillars/pillar-2-data-ingestion/PM Brief/` | Yes |
| `04_pillars/pillar-2-data-ingestion/Principle Architect/` | Yes |
| `04_pillars/pillar-1-spatial-substrate/` | **NO** — contains `harmony/` source tree and venv; remains in place until the root question (Finding #1) is settled |
| `04_pillars/pillar-2-data-ingestion/` | Yes once all non-source moved |
| `04_pillars/` | Only if pillar-1 is also removed (depends on Finding #1) |
| `05_data/raw/` | Yes |
| `05_data/processed/` | Yes |
| `05_data/` | Yes |
| `06_docs/` | Yes (already empty) |
| `Master_Spec_Variations/decisions/` | Yes |
| `Master_Spec_Variations/untitled folder/` | Yes (flag — unknown purpose) |
| `Master_Spec_Variations/spec/archive/` | Yes after moves |
| `Master_Spec_Variations/spec/` | Yes after moves |
| `Master_Spec_Variations/variations/applied/` | Yes (originals archived) |
| `Master_Spec_Variations/variations/pending/` | Yes (archived) |
| `Master_Spec_Variations/variations/` | Yes |
| `Master_Spec_Variations/` | Yes |
| `ASCA Pitch Day 2026/Harmony - Military RFI/` | Yes after move |
| `ASCA Pitch Day 2026/` | Yes |
| `project/` | Yes (empty, unknown) |

---

## Ambiguous Files

| File | Current Location | Ambiguity | Options |
|---|---|---|---|
| `HARMONY_MASTER_SPEC_V1.0.md` | `01_project-context/` and `Master_Spec_Variations/spec/master-spec-v1.0.md` and `Master_Spec_Variations/spec/archive/master-spec-v1.0.md` | Three copies of v1.0 master spec | Pick canonical (suggest `Master_Spec_Variations/spec/master-spec-v1.0.md`, read-only); archive others; byte-compare first |
| `harmony_master_spec_v0.1.md` | `01_project-context/` and `Master_Spec_Variations/spec/archive/master-spec-v0.1.md` | Two copies | Byte-compare, keep one at `docs/specs/archive/` |
| `master-spec-v1.0.1-draft.md` vs `master-spec-v1.0.1.md` | `Master_Spec_Variations/spec/` | Draft and final | Keep final in `docs/specs/`, draft in `docs/specs/drafts/` or delete |
| `VAR-001…009` in `applied/` vs `pending/` | Both subfolders hold same titles | Pending copies appear older/superseded | Recommend archiving pending without new DEC entries — confirm |
| `extracted_files/ADR-*.md` (7 files) | pillar-1 | Older copies of ADRs already in `harmony/docs/adr/` under renumbered names | Recommend delete as superseded per `ADR_INDEX.md` rename map; require Mikey confirmation |
| `extracted_files/pillar-1-master-spec-variations.md` | pillar-1 | Also exists at `harmony/docs/pillar-1-master-spec-variations.md` | Inner nested copy is authoritative; outer is duplicate — flag |
| `extracted_files/id_generation_rules.md`, `identity-schema.md`, `alias_namespace_rules.md`, `CHANGELOG.md`, `README.md`, `project-manager-agent-brief.md`, `session-progress-report-template.md`, `*.json` | pillar-1 | All present in newer form inside `harmony/docs/` | Recommend delete as stale extractions |
| `extracted_files/2026-04-10-pillar-1-v0.1.2-amendment.md` | pillar-1 | Dated amendment note | Move to `docs/reports/p1-v0-1-2-amendment-20260410.md` rather than delete |
| `ADR_INDEX.md` | `harmony/docs/ADR_INDEX.md` (inside untouchable nested repo) | Target wants `docs/adr/ADR_INDEX.md` at chosen root | **Copy** it (rather than move), or leave untouched and author a new root-level index — Mikey's call |
| `04_pillars/pillar-1-spatial-substrate/harmony/docs/adr/ADR-*.md` (12 files) | inside nested repo | Safety boundary says don't touch nested repo; target structure says ADRs live at `docs/adr/` | Option A: leave in place, create root `docs/adr/` as symlink; Option B: copy (not move); Option C: treat nested repo as the repo and run reorg inside it |
| `04_pillars/pillar-2-data-ingestion/ADR-015-temporal-trigger-architecture.md` | | Subject doesn't match target's ADR-015 name | Move as-is; add to new ADR_INDEX |
| `files.zip` in Pillar 1 (3 files), Pillar 2 (1), Master_Spec_Variations (1), ASCA (1), `reorg-dispatch.zip` at root | various | Source archives of extracted content | Default: leave in place or move alongside unzipped counterparts; flag each for Mikey |
| `01_project-context/HARMONY_PILLAR_BRIEF_TEMPLATE.md` + other `TEMPLATE`/`PROMPT` files | `01_project-context/` | Templates not explicitly in target tree | Proposing `docs/specs/templates/`; confirm |
| Drafts (`master-spec-v1.0.1-draft.md`) | `Master_Spec_Variations/spec/` | Not in target tree | Proposing `docs/specs/drafts/`; confirm |
| `.venv-validation/` at root | `/Users/mikey/Desktop/Harmony/` | Virtualenv | Leave untouched |
| `reorg-dispatch/` and `reorg-dispatch.zip` | root | This dispatch | Archive after success |

---

## ASCA Confirmation

- [ ] Confirmed ASCA folder will move to: `../commercial/asca-pitch-2026/`
  (i.e. `/Users/mikey/Desktop/commercial/asca-pitch-2026/`)
- [ ] Confirmed parent directory `/Users/mikey/Desktop/commercial/` will be created
- Note: `/Users/mikey/Desktop/commercial/` does not currently exist. `mkdir -p` will create it in Step 1.

---

## Safety Confirmation

- [x] No `.py`, `.sql`, `.yml`, or `.json` files inside the nested `harmony/` source tree (`04_pillars/pillar-1-spatial-substrate/harmony/`) are in the move list.
- [x] No `docker-compose.yml` exists in the repo — nothing to protect, but Step 1 creation commands do not touch any source files.
- [x] No `.env` or `.env.example` exists in the repo. Nothing to protect or move.
- [x] No `src/`, `tests/` at root — the dispatch's `src/core/`, `src/api/`, `src/db/`, `src/ingestion/`, `tests/` do not exist at the chosen root. The analogous untouchable tree is `04_pillars/pillar-1-spatial-substrate/harmony/{packages,services,db,tests,scripts,data}/` — **confirm I should treat this tree as the "untouchable source"**.
- [x] `reorg-dispatch/` itself will not be edited during Phase 2; only archived at the end.
- [ ] Post-execution safety check (`pytest`, `from src.api import app`, `from src.core import cell_key`) will fail as written because import paths don't match (`packages/cell-key/` not `src/core/`). Substitute commands are required — **needs Mikey's confirmation of revised check.**

---

## Requires Mikey's Decision Before Phase 2

1. Is the canonical root `/Users/mikey/Desktop/Harmony/`, with the nested `harmony/` treated as the source tree to leave untouched? Or should the entire `04_pillars/pillar-1-spatial-substrate/harmony/` tree be promoted up and the wrappers removed?
2. Confirm the terminology migration is a no-op in this repo.
3. For ADRs 002, 005, 015: skip, author stubs, or leave current state?
4. Can `Master_Spec_Variations/variations/pending/` be archived without DEC entries?
5. For the `extracted_files/` older ADR copies: confirm they can be deleted as superseded (or archived — no deletion is default).
6. Approve proposed subfolders not in the target tree: `docs/specs/templates/`, `docs/specs/drafts/`, `docs/specs/archive/`, `docs/specs/variations-archive/`, `docs/specs/pillars/archive/`.
7. Replace the post-execution safety-check commands with ones matching the actual `packages/ + services/` layout.
8. Disposition of `files.zip` archives (5 total across the repo) and `reorg-dispatch.zip` at root.

---

**STATUS: AWAITING APPROVAL. No files will be moved, renamed, created, or deleted until Mikey replies with "approved" or amendments.**
