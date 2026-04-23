# HARMONY — Pillar Brief + PM Brief Template
## Instructions for generating both documents from a pillar depth-probe session

---

When generating documents from a completed depth-probe session, produce both documents below in full. Do not summarise or abbreviate any section. Every field marked REQUIRED must be completed. Fields marked OPTIONAL may be left as TBD if genuinely unknown at this stage.

Save Document 1 as: `HARMONY_[PILLAR NUMBER]_[PILLAR NAME]_BRIEF_V1.0.md`
Save Document 2 as: `HARMONY_[PILLAR NUMBER]_[PILLAR NAME]_PM_BRIEF_V1.0.md`

Both files should be saved into the relevant pillar folder in the Harmony project directory.

---

---

# DOCUMENT 1 — PILLAR BRIEF

---

# HARMONY — [Pillar Number]: [Pillar Name]
## Pillar Brief | Version 1.0
**Status:** Ready for Build / Pending Decisions (delete as appropriate)
**Date:** [Date]
**North Stars Served:** [I / II / III / combination]
**Depends On:** [List pillar numbers this pillar receives inputs from]
**Depended On By:** [List pillar numbers that consume outputs from this pillar]

---

## 1. Purpose

**One-sentence statement of this pillar's role in the Harmony platform:**
[Write here]

**What this pillar makes possible for the platform that would not exist without it:**
[Write here — be specific, not generic]

**The single most important thing this pillar must get right:**
[Write here]

---

## 2. North Star Obligations

For each North Star this pillar serves, state the specific contribution and the failure condition.

### North Star I — The Seamless World
**This pillar's contribution:**
[Write here, or state NOT APPLICABLE]

**Failure condition — what design choice would make this North Star undeliverable:**
[Write here, or state NOT APPLICABLE]

### North Star II — The GPS-Free Spatial Substrate
**This pillar's contribution:**
[Write here, or state NOT APPLICABLE]

**Failure condition:**
[Write here, or state NOT APPLICABLE]

### North Star III — The Spatial Knowledge Interface
**This pillar's contribution:**
[Write here, or state NOT APPLICABLE]

**Failure condition:**
[Write here, or state NOT APPLICABLE]

---

## 3. Resolved Decisions

List every decision resolved during the depth-probe session. Each entry is binding — CoWork should treat these as constraints, not suggestions.

| # | Decision | Resolution | Rationale |
|---|----------|-----------|-----------|
| 1 | [Decision statement] | [What was decided] | [Why] |
| 2 | | | |
| 3 | | | |

---

## 4. Tools and Technologies

List every tool, framework, technology, and external service this pillar requires.

| Tool / Technology | Role in This Pillar | Status | Notes |
|------------------|--------------------|----|-------|
| [Name] | [What it does here] | Confirmed / Under Evaluation / TBD | [Any notes] |

---

## 5. Inter-Pillar Interfaces

### Inputs This Pillar Receives
| From Pillar | What Is Received | Format / Protocol | When Needed |
|-------------|-----------------|------------------|-------------|
| [Pillar name] | [Description] | [Format] | [Build phase] |

### Outputs This Pillar Exposes
| To Pillar | What Is Delivered | Format / Protocol | When Available |
|-----------|------------------|------------------|---------------|
| [Pillar name] | [Description] | [Format] | [Build phase] |

---

## 6. Open Decisions (Deferred)

Decisions that do not need to be resolved before build begins, but must not be closed off by early build choices.

| # | Decision | Why Deferred | Constraint on Early Build | Target Resolution |
|---|----------|-------------|--------------------------|------------------|
| 1 | [Decision] | [Reason] | [What early build must not do] | [Phase or milestone] |

---

## 7. CoWork Build Instructions

This section is the direct instruction set for CoWork. Write it as if speaking to an agentic system that will execute without further clarification.

**Session objective:**
[One sentence stating what this CoWork session must produce]

**Input files to read before beginning:**
- `Project Context/HARMONY_MASTER_SPEC_V1.0.md`
- `[Pillar folder]/HARMONY_[PILLAR]_BRIEF_V1.0.md`
- [Any other files]

**Tasks to execute, in order:**

Task 1: [Task name]
- Description: [What CoWork must do]
- Output: [Specific file or artefact to produce]
- Save to: [Exact folder path]
- Success condition: [How to verify this task is complete]

Task 2: [Task name]
- Description:
- Output:
- Save to:
- Success condition:

[Continue for all tasks]

**On completion:**
Produce a session summary saved as `[Pillar folder]/SESSION_01_SUMMARY.md` confirming what was created, where each file was saved, and flagging any ambiguities or decisions that arose during execution that require human review before the next session.

---

## 8. Gaps and Risks

| # | Gap or Risk | Impact | Mitigation |
|---|-------------|--------|-----------|
| 1 | [Description] | [Which North Star or pillar is affected] | [How to manage] |

---

---

# DOCUMENT 2 — PROJECT MANAGEMENT BRIEF

---

# HARMONY — [Pillar Number]: [Pillar Name]
## Project Management Brief | Version 1.0
**Date:** [Date]
**Pillar Status:** Pre-Build / Active / Complete
**Priority:** Critical Path / High / Standard
**Estimated Total Sessions:** [Number]
**Estimated Total Tokens:** [Range — e.g. 200k–400k]
**Estimated Calendar Duration:** [e.g. 2 weeks / 4 weeks]
**Hard Dependencies:** [List any pillars or decisions that must complete before this pillar can begin]

---

## 1. Pillar Summary for PM Agent

Provide a plain-language summary of what this pillar does, why it matters to the overall project, and what it must deliver. Write this as if briefing a project manager who has not read the full specification.

[Write 3–5 sentences here]

---

## 2. Build Phases

Break the pillar's work into phases. A phase is a coherent block of work with a clear start condition, a clear end condition, and a set of deliverables. Phases may run in parallel where dependencies allow.

### Phase 1: [Phase Name]
**Objective:** [What this phase achieves]
**Start Condition:** [What must be true or complete before this phase begins]
**End Condition / Milestone:** [What defines this phase as complete]
**Deliverables:**
- [List specific files, schemas, documents, or working components]

**Sessions in this phase:**

| Session | Objective | Estimated Tokens | Estimated Duration | Inputs Required | Output |
|---------|-----------|-----------------|-------------------|----------------|--------|
| Session 01 | [What this session does] | [e.g. 50k–80k] | [e.g. 2–3 hours] | [Files or decisions needed] | [File or artefact produced] |
| Session 02 | | | | | |

---

### Phase 2: [Phase Name]
**Objective:**
**Start Condition:**
**End Condition / Milestone:**
**Deliverables:**

**Sessions in this phase:**

| Session | Objective | Estimated Tokens | Estimated Duration | Inputs Required | Output |
|---------|-----------|-----------------|-------------------|----------------|--------|
| Session 01 | | | | | |

---

[Add Phase 3, 4 etc. as required]

---

## 3. Sprint Allocation

Map phases to sprints within the overall Harmony build timeline. A sprint is two weeks unless otherwise specified.

| Sprint | Phase(s) | Key Activities | Milestone | Dependencies |
|--------|---------|---------------|-----------|-------------|
| Sprint 1 | [Phase] | [What happens] | [Milestone name] | [What must be done first] |
| Sprint 2 | | | | |
| Sprint 3 | | | | |

---

## 4. Dependency Map

### Blocking Dependencies (this pillar cannot start without these)
| Dependency | Type | Owner | Status |
|-----------|------|-------|--------|
| [Pillar or decision name] | Pillar / Decision / External | [Who resolves it] | Resolved / Pending |

### Soft Dependencies (this pillar is constrained but not blocked without these)
| Dependency | Impact if Missing | Workaround |
|-----------|-----------------|-----------|
| [Description] | [What is degraded] | [How to proceed anyway] |

### Downstream Impact (what this pillar blocks)
| Dependent Pillar | What It Needs From This Pillar | When It Needs It |
|-----------------|-------------------------------|-----------------|
| [Pillar name] | [Specific output] | [Sprint or phase] |

---

## 5. Token Budget

Provide a token estimate for each session type this pillar requires. These estimates allow the PM Agent to schedule sessions within Claude usage limits and plan for capacity across the full project.

| Session Type | Typical Token Range | Frequency | Notes |
|-------------|-------------------|-----------|-------|
| Depth-probe / decision session | 30k–60k | Once per pillar | High reasoning load |
| Schema design session | 40k–80k | [Number] sessions | Depends on complexity |
| CoWork build session | 60k–150k | [Number] sessions | File I/O intensive |
| Review and iteration session | 20k–40k | Per deliverable | Lower load |
| **Total estimated for this pillar** | **[Range]** | | |

---

## 6. Milestones

List the specific, verifiable milestones for this pillar. Each milestone should be a binary state — either achieved or not achieved. No partial credit.

| Milestone | Description | Target Sprint | Success Criteria | Dependent On |
|-----------|-------------|--------------|-----------------|-------------|
| M1 | [Name] | Sprint [N] | [What must be true] | [Any prior milestone] |
| M2 | | | | |
| M3 | Pillar Complete | Sprint [N] | All deliverables produced, reviewed, and saved. All open decisions resolved or formally deferred. PM Brief updated. | M1, M2 |

---

## 7. Risks and Blockers

| # | Risk or Blocker | Probability | Impact | Mitigation | Owner |
|---|----------------|-------------|--------|-----------|-------|
| 1 | [Description] | High / Med / Low | High / Med / Low | [How to manage] | TBD |

---

## 8. PM Agent Instructions

This section is the direct instruction for the PM Agent building the master plan and Gantt chart. Write it as a clear, unambiguous brief.

**Add this pillar to the master Gantt chart with the following parameters:**

- Pillar name: [Name]
- Start sprint: [Sprint number — based on dependencies]
- End sprint: [Sprint number]
- Total duration: [Weeks]
- Colour code: [Assign a consistent colour per pillar — suggest navy for Pillar I, teal for Pillar II, gold for Pillar III, slate for Pillar IV, green for Pillar V]
- Critical path: [Yes / No]

**Flag the following dependencies as blockers in the Gantt chart:**
[List each blocking dependency with the pillar or milestone it depends on]

**Schedule the following milestones as Gantt markers:**
[List each milestone with its target sprint]

**Token budget note for scheduling:**
This pillar requires approximately [total token estimate] tokens across [total session count] sessions. Sessions should not be scheduled on the same day as other high-token pillar sessions to stay within daily usage limits.

---

*HARMONY Pillar Brief + PM Brief Template — For use with HARMONY_PILLAR_DEPTH_PROBE_PROMPT.md*
