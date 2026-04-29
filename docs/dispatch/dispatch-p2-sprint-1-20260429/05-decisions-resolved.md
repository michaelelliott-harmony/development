# Decisions Resolved by Marcus Webb — Pre-Dispatch

The following ambiguities were identified during dispatch preparation and
resolved before sending this brief to Dr. Adeyemi. Dr. Adeyemi does not need
to re-raise these; they are settled.

---

## R1 — extract.py Added to Cherry-Pick List

**Issue:** The cherry-pick file list in the original dispatch instruction does
not include `extract.py`. However:
- `runner.py` (which IS in the list) imports and calls `extract.extract()`
- Modification 1 explicitly targets `extract.py`
- `extract.py` is confirmed present on Branch B at
  `04_pillars/pillar-2-data-ingestion/harmony/pipelines/extract.py`

**Resolution:** `extract.py` is added to the cherry-pick list.  
**Authority:** File routing → Marcus Webb (AUTHORITY_MATRIX).  
**Action required:** None. The corrected cherry-pick command in `03-session-brief.md`
already includes this file.

---

## R2 — Manifests Path Corrected

**Issue:** The original dispatch instruction lists `manifests/` as the
cherry-pick path for the YAML manifest files. On Branch B, the manifests
live at `04_pillars/pillar-2-data-ingestion/harmony/pipelines/manifests/`,
not at `04_pillars/pillar-2-data-ingestion/manifests/`.

**Resolution:** The corrected cherry-pick path is
`04_pillars/pillar-2-data-ingestion/harmony/pipelines/manifests/`.  
**Authority:** File routing → Marcus Webb (AUTHORITY_MATRIX).  
**Action required:** None. The corrected cherry-pick command in `03-session-brief.md`
already uses this path.

---

## R3 — V2.0 Brief MD Location

**Issue:** The V2.0 brief `.md` is not on `main` — it lives on branch
`origin/docs/p2-brief-v2-md-20260429`. The `.docx` version is on main at
`04_pillars/pillar-2-data-ingestion/docs/HARMONY_P2_DATA_INGESTION_PIPELINE_BRIEF_V2_0.docx`.

**Resolution:** All acceptance criteria from §6.2 of the V2.0 brief are
reproduced in `04-acceptance-criteria.md` in this dispatch. Dr. Adeyemi
does not need to fetch the brief separately.  
**Authority:** Marcus Webb.  
**Action required:** None.

---

## R4 — Branch B audit session report missing

**Issue:** The reference document `PM/sessions/2026-04-29-branch-b-audit.md`
is referenced in the dispatch brief but does not exist on main.

**Resolution:** Mikey has confirmed all three Sprint 1 blockers are resolved
as the precondition for this dispatch. The audit findings that matter are
embedded in the five compliance modifications. The missing file does not
block execution.  
**Authority:** Marcus Webb (confirmed blocker resolution from Mikey's instruction).  
**Action required:** None for Dr. Adeyemi. The PM Agent should file a retrospective
note at session close.

---

## R5 — setup.py requests dependency must also be updated

**Issue:** Branch A's `setup.py` lists `requests>=2.31.0,<3` in
`install_requires`. Modification 5 replaces `requests` with `httpx` in
all adapters. The dependency in `setup.py` must be updated to match.

**Resolution:** `setup.py` must replace `"requests>=2.31.0,<3"` with
`"httpx[http2]>=0.27.0,<1"` as part of Modification 5. This is included
in the Modification 5 instructions in `03-session-brief.md`.  
**Authority:** Marcus Webb (file routing / dependency hygiene).  
**Action required:** Included in session brief — no separate action needed.

---

## R6 — fidelity PATCH hook in runner.py

**Issue:** `runner.py` in Branch B contains a commented-out `patch_cell_fidelity`
call with the comment "Until then, fidelity_coverage is carried in entity
metadata (interim accepted by Mikey)". DEC-017 confirms the PATCH endpoint
is now live.

**Resolution:** The fidelity PATCH hook should be wired in. Confirm
`p1_client.py` exposes `patch_cell_fidelity`; if not, implement the method.
This is within Dr. Adeyemi's pipeline implementation authority.  
**Authority:** Marcus Webb routing to DEC-017 (no escalation needed).  
**Action required:** Included in ADR summary (02-adr-summary.md) — Dr. Adeyemi
to implement.
