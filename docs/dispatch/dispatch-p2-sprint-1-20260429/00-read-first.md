# Dispatch: Pillar 2 Sprint 1 — Foundation Pipeline (V2.0 Compliance)
## READ THIS FIRST — Mandatory pre-work before touching any code

**Dispatch ID:** dispatch-p2-sprint-1-20260429  
**Date:** 2026-04-29  
**Issued by:** Marcus Webb (Tech Lead / Orchestrator)  
**Assigned to:** Dr. Yusuf Adeyemi (Pipeline Architect)  
**Model:** claude-sonnet-4-6

---

## Before You Write a Single Line of Code

Read these documents in order. Do not skip any.

1. `agents/AGENTS.md` — current project state and team roster
2. `docs/specs/CURRENT_SPEC.md` — active specification pointer
3. `docs/specs/DECISION_LOG.md` — active decisions binding on this sprint
4. `agents/AUTHORITY_MATRIX.md` — escalation routing
5. `agents/security/SECURITY_POLICY.md` — non-negotiable security rules
6. `docs/adr/ADR-022-rendering-asset-format-and-data-contract.md` — fidelity schema contract
7. `docs/adr/ADR-024-geospatial-standards-compliance.md` — five V2.0 compliance gaps
8. The remaining files in this dispatch directory, in numbered order

Do not begin Step 1 (branch creation) until all documents above have been read.

---

## What This Sprint Is

Sprint 1 delivers the Pillar 2 Foundation Pipeline (M1, M2, M3) on a fresh
cherry-pick of proven Branch B code with five V2.0 compliance modifications
applied on top.

This is **Option B: selective cherry-pick from Branch B**. It is not a fresh
build. It is not a straight merge of Branch B. You are transplanting the sound
modules from Branch B and then applying five compliance modifications in place.

---

## Output Protocol

Every session produces:
- A committed feature branch: `feature/p2-sprint-1-cherry-pick`
- A pull request against main
- A session report filed to: `PM/sessions/2026-04-29-p2-sprint-1.md`
- A HARMONY UPDATE line at the end of the session report

The session report is your accountability document. It records every decision
you made, every test result, every ambiguity you resolved and how.

---

## Ambiguity Protocol

If you encounter a question not answered by this dispatch:

1. Check `agents/AUTHORITY_MATRIX.md` for the correct authority
2. Check `docs/specs/DECISION_LOG.md` for a relevant decision entry
3. Check the ADRs referenced in this dispatch
4. If still unresolved, route to Marcus Webb — do NOT stop work
5. Never route to Mikey for questions covered by this dispatch

---

## Absolute Rules — Read, Understand, Follow

- Never commit directly to main
- Never execute migrations — produce them only
- Secrets never in code, logs, or filenames — `.env.example` only
- ADR first, code second — all modifications here are covered by existing ADRs
- Tests must pass before the PR is opened
