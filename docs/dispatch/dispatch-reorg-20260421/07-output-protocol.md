# 07_OUTPUT_PROTOCOL.md
## How to Report Back

---

## Phase 1 Output (Required Before Any Moves)

Produce `REORG_PLAN.md` in the current working directory.
This file must contain:

```markdown
# Reorganisation Plan
## Task ID: reorg-20260421
## Status: AWAITING APPROVAL — do not execute until approved

### Files to Move
| Current Path | Target Path | Action | Notes |
|---|---|---|---|
| ... | ... | Move | |
| ... | ... | Rename + Move | |

### Files to Create
| Target Path | Source |
|---|---|
| docs/specs/CURRENT_SPEC.md | New file per 06_NEW_FILES.md |
| CLAUDE.md | Updated per 06_NEW_FILES.md |

### validation/ Contents
| File | Size | Recommendation | Reason |
|---|---|---|---|
| ... | ... | Keep → tests/ingestion/ | |
| ... | ... | Flag for deletion | Temporary build artefact |

### Terminology Replacements
| File | Occurrences of "OpenClaw" | Action |
|---|---|---|

### Empty Folders After Moves
| Folder | Safe to Remove? |
|---|---|

### Ambiguous Files
(Files whose correct destination is unclear — flagged for Mikey's decision)
| File | Current Location | Ambiguity | Options |
|---|---|---|---|

### ASCA Confirmation
- [ ] Confirmed ASCA folder will move to: ../commercial/asca-pitch-2026/
- [ ] Confirmed parent directory ../commercial/ exists or will be created

### Safety Confirmation
- [ ] No .py, .sql, .yml, or .json files in src/ or tests/ are in the move list
- [ ] docker-compose.yml is not in the move list
- [ ] .env and .env.example are not in the move list
```

Stop after producing this file. Send it to Mikey for review.
Do not proceed to Phase 2 until you receive explicit approval.

---

## Phase 2 Output (After Execution)

File `p0-reorg-report-20260421.md` to `docs/reports/` containing:

```markdown
# Session Report
**Task ID:** reorg-20260421
**Agent:** Reorganisation Agent
**Date:** 2026-04-21
**Status:** COMPLETE | PARTIAL | BLOCKED

## Summary
What was done, what was not done, what requires follow-up.

## Moves Executed
| From | To | Status |
|---|---|---|

## Files Created
| File | Status |
|---|---|

## Terminology Replacements Applied
| File | Replacements Made |
|---|---|

## Folders Removed
| Folder | Status |
|---|---|

## Validation/ Disposition
| File | Action Taken |
|---|---|

## Safety Check Results
- pytest: PASS / FAIL (include output if FAIL)
- API import: PASS / FAIL
- Core import: PASS / FAIL

## Ambiguous Items Remaining
(Anything that still needs Mikey's decision)

## Requires Approval
(Any empty folders not yet deleted, validation/ files not yet deleted)

## HARMONY UPDATE LINE
HARMONY UPDATE | 21 Apr 2026 | Project Structure | Reorganisation complete.
Managed Agents terminology applied. CURRENT_SPEC.md and DECISION_LOG.md
created. ASCA moved outside repo. | Pillars: 1 ✓ 2 active
```
