# 03_CURRENT_STRUCTURE.md
## Current Folder Structure — As Observed in Screenshot

---

## Top-Level Folders (from screenshot)

```
harmony-project/           ← assumed parent
├── 01_project-context/
├── 02_architecture/
├── 03_agents/
├── 04_pillars/
├── 05_data/
├── 06_docs/
├── Master_Spec_Variations/
├── ASCA Pitch Day 2026/
└── validation/
```

---

## Mapping: Current → Target

Work through each folder. Read its contents before routing.

### `01_project-context/`
**Expected contents:** Early project notes, initial briefs, vision documents.
**Target:** Most content → `docs/specs/`. Business vision docs → `docs/specs/vision/`.
**Flag if found:** Any `.py`, `.sql` files — these are unexpected here.

### `02_architecture/`
**Expected contents:** Architecture notes, early ADR drafts, design documents.
**Target:** ADR drafts → `docs/adr/`. Architecture notes → `docs/specs/`.
**Flag if found:** Any files that look like accepted ADRs not yet in `docs/adr/`.

### `03_agents/`
**Expected contents:** Agent prompt files, OpenClaw documentation.
**Target:** Agent prompts → `agents/prompts/`. Config → `agents/managed/`.
**Action:** Apply full terminology migration per `02_TERMINOLOGY_MIGRATION.md`.

### `04_pillars/`
**Expected contents:** Pillar briefs, milestone specs, handoff documents.
**Target:** Pillar docs → `docs/specs/pillars/`. Dispatch packages → `docs/dispatch/`.
**Naming:** Apply pillar naming convention: `p{N}-{slug}-brief-v{N}.md`.

### `05_data/`
**Expected contents:** Pilot datasets, test fixtures, data samples.
**Target:** Pilot data → `data/pilot/`. Test fixtures → `data/fixtures/`.
**Flag if found:** Large binary files — note them but do not move without confirmation.

### `06_docs/`
**Expected contents:** General documentation, reports, meeting notes.
**Target:** Specs → `docs/specs/`. Reports → `docs/reports/`. ADRs → `docs/adr/`.

### `Master_Spec_Variations/`
**Expected contents:** Spec variation files (VAR001 through VAR020+), decision notes.
**Target:** Convert to `docs/specs/DECISION_LOG.md` entries (see `06_NEW_FILES.md`).
**Action:** Read every file. Extract the decision. Create a structured log entry. 
Do not simply move the raw files — transform them into the Decision Log format.

### `ASCA Pitch Day 2026/`
**Expected contents:** Military RFI response documents, pitch materials.
**Target:** Move to `../commercial/asca-pitch-2026/` — OUTSIDE the harmony repo.
**Critical:** Confirm the parent directory exists or create it before moving.
This folder must not remain inside the repo.

### `validation/`
**Expected contents:** Temporary test outputs from Pillar 2 API testing session.
**Action:**
1. List all files with sizes
2. Identify: test scripts worth keeping → `tests/ingestion/`
3. Identify: temporary outputs, logs, fixtures → flag for deletion confirmation
4. Include full file list in `REORG_PLAN.md` with recommended action for each

---

## Files Likely at Root Level

Also check for and route these files if found at root:

| File | Target |
|---|---|
| `CLAUDE.md` | Stay at root — will be updated in Phase 2 |
| `README.md` | Stay at root |
| `docker-compose.yml` | Stay at root — do not move |
| `.env.example` | Stay at root — do not move |
| `*.md` spec files at root | `docs/specs/` |
| Any `.py` at root | Flag — unexpected |
