# 05_EXECUTION_PLAN.md
## Execution Plan — Phase 2 Only (After Plan Approval)

---

## Pre-Execution Checklist

Before executing a single move, confirm:
- [ ] `REORG_PLAN.md` has been produced and approved by Mikey
- [ ] Safety check: `python -m pytest tests/ -q` passes with current structure
- [ ] Parent directory `../commercial/` exists or has been created
- [ ] No migration, test, or source code files are in the move list

---

## Execution Order

Execute in this exact order. Each step is a logical group.
Complete each group fully before starting the next.

---

### Step 1 — Create Target Folder Structure

Create all target directories before moving anything.
Existing directories are left alone — only create missing ones.

```bash
mkdir -p docs/adr
mkdir -p docs/specs/pillars
mkdir -p docs/specs/vision
mkdir -p docs/dispatch
mkdir -p docs/reports
mkdir -p agents/prompts
mkdir -p agents/security
mkdir -p agents/managed
mkdir -p data/pilot
mkdir -p data/fixtures
mkdir -p ../commercial/asca-pitch-2026
```

---

### Step 2 — Move ASCA Folder Outside Repo

This is the highest-priority move — sensitive business material should
not be inside the technical repo.

```bash
mv "ASCA Pitch Day 2026/"* ../commercial/asca-pitch-2026/
rmdir "ASCA Pitch Day 2026"
```

Confirm: `ls ../commercial/asca-pitch-2026/` shows the moved files.

---

### Step 3 — Route ADRs to docs/adr/

Find all ADR files across the current structure and move them to `docs/adr/`.
Apply the naming convention: `ADR-{NNN}-{slug}.md`

For each ADR found:
1. Check if a correctly-named version already exists in `docs/adr/`
2. If yes — compare content, keep the more complete version, flag the duplicate
3. If no — rename to convention and move

Create or update `docs/adr/ADR_INDEX.md` listing all ADRs with status.

---

### Step 4 — Route Spec Files to docs/specs/

Move all master spec versions to `docs/specs/`:
- Apply naming: `harmony-master-spec-v{N}-{N}-{N}.md`
- If PDF versions exist, move alongside with same base name

Move pillar-specific documents to `docs/specs/pillars/`:
- Apply naming: `p{N}-{slug}-brief-v{N}.md`
- Handoff docs: `p{N}-{slug}-handoff.md`
- Milestone specs: `p{N}-m{N}-{slug}-spec.md`

Move early vision/context documents to `docs/specs/vision/`.

---

### Step 5 — Convert Master_Spec_Variations to Decision Log

Read every file in `Master_Spec_Variations/`. For each one, create
a structured entry in `docs/specs/DECISION_LOG.md` using this format:

```markdown
### DEC-{NNN} | {date from file or today} | {pillar or area}
**Decision:** {what was decided}
**Impact:** {what it changes}
**Status:** Accepted
**Spec version:** {which spec version captured this, or "pending V1.2.0"}
```

After all entries are created in the log, move the original
`Master_Spec_Variations/` folder to `docs/specs/variations-archive/`
as a read-only archive. Do not delete it.

---

### Step 6 — Migrate agents/ (formerly openclaw/)

```bash
# If openclaw/ exists at root:
mv openclaw/OPENCLAW.md agents/AGENTS.md
mv openclaw/agents/* agents/prompts/
mv openclaw/security/SECURITY_POLICY.md agents/security/
mv openclaw/orchestrator/schema.sql agents/managed/task-queue-schema.sql
mv openclaw/orchestrator/ORCHESTRATOR.md agents/managed/MANAGED_AGENTS_SETUP.md
rmdir openclaw/agents openclaw/security openclaw/orchestrator openclaw

# If 03_agents/ contains agent files:
# Route prompt files to agents/prompts/
# Route config files to agents/managed/
```

Apply terminology replacements per `02_TERMINOLOGY_MIGRATION.md`
to all `.md` files in `agents/`.

---

### Step 7 — Route Dispatch Packages to docs/dispatch/

Find all dispatch packages (folders with numbered 00–07 files).
Move each to `docs/dispatch/dispatch-p{N}-{slug}-{YYYYMMDD}/`.
Apply the two-digit prefix naming to files inside: `{NN}-{slug}.md`.

---

### Step 8 — Route Data Files to data/

Move pilot datasets to `data/pilot/`.
Apply naming: `cc_{source}_{YYYYMMDD}.{ext}` for Central Coast files.
Move test fixtures to `data/fixtures/`.

---

### Step 9 — Process validation/ Folder

Based on the file-by-file assessment in `REORG_PLAN.md`:
- Route approved test files to `tests/ingestion/`
- Flag anything else for Mikey's delete confirmation
- Do not delete automatically

---

### Step 10 — Create New Infrastructure Files

Create the three new files defined in `06_NEW_FILES.md`:
1. `docs/specs/CURRENT_SPEC.md`
2. Updated `CLAUDE.md`

`DECISION_LOG.md` was created in Step 5.

---

### Step 11 — Clean Up Empty Folders

After all moves are complete, identify empty folders from the old structure.
List them. Do not delete automatically — include in output report for Mikey
to confirm.

Likely candidates:
```
01_project-context/    (after contents moved)
02_architecture/       (after contents moved)
03_agents/             (after contents moved)
04_pillars/            (after contents moved)
05_data/               (after contents moved)
06_docs/               (after contents moved)
```

---

### Step 12 — Post-Execution Safety Check

Run the full safety check from `01_SAFETY_BOUNDARY.md`:

```bash
python -m pytest tests/ -q
python -c "from src.api import app; print('API OK')"
python -c "from src.core import cell_key; print('Core OK')"
```

All three must pass. If any fail — stop, report immediately, do not
proceed with cleanup.

---

### Step 13 — File Output Report

File `p0-reorg-report-20260421.md` to `docs/reports/` using the
output protocol in `07_OUTPUT_PROTOCOL.md`. Include the HARMONY UPDATE line.
