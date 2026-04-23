# HARMONY-SPEC-PROCESS.md
> CoWork Instruction File — Harmony Project Governance
> Last Updated: 2026-04-13 | Process Version: 1.1 | Current Live Spec: V1.0.1

---

## Purpose

This document defines the canonical process for managing the Harmony Master Specification. It governs how decisions are captured, how variations are applied, and how the master spec is versioned and archived. All Claude sessions and agents working on Harmony must follow this process.

---

## Folder Structure

```
Master_Spec_Variations/
  HARMONY-SPEC-PROCESS.md           ← This file (governance process)
  VAR-TEMPLATE.md                   ← Blank template for new variations
  /spec/
    master-spec-v[CURRENT].md       ← Live version (single source of truth)
    master-spec-v[NEXT]-draft.md    ← In-progress update (only one at a time)
    /archive/
      master-spec-v0.1.md
      ...
  /variations/
    /pending/
      VAR-[ID]-[slug].md            ← Approved, not yet in master
    /applied/
      VAR-[ID]-[slug].md            ← Applied to master (do not modify)
  /decisions/
    ADR-[ID]-[slug].md              ← Architecture Decision Records
```

---

## Versioning Schema

```
v[MAJOR].[MINOR].[PATCH]

MAJOR  — Fundamental architectural change (e.g. new pillar, schema redesign)
MINOR  — Significant feature addition or section restructure
PATCH  — Variation incorporation, clarifications, minor corrections
```

**Current live version** is always the highest version file in `/spec/` (not in `/archive/`).

---

## The Golden Rules

1. **Never edit the live master spec directly.** All changes flow through a variation file first.
2. **One draft at a time.** Only one `-draft.md` file may exist in `/spec/` at any time.
3. **Variation files are immutable once applied.** Move them to `/applied/` and do not modify them.
4. **Archive before publishing.** The old live version must be copied to `/archive/` before the draft is promoted.
5. **Project Knowledge must stay current.** After every version promotion, update the Harmony master spec in Claude Project Knowledge.

---

## End-to-End Change Flow

```
1. DECISION MADE
   └─ In any Claude chat or working session

2. CAPTURE AS VARIATION FILE
   └─ Create VAR-[ID]-[slug].md using the standard template
   └─ Save to /variations/pending/
   └─ Assign next sequential VAR ID

3. BATCH TRIGGER
   └─ Open a Spec Update Session when:
        - 3 or more variations are pending, OR
        - 2 weeks have passed since last update, OR
        - A high-priority variation is raised (flag in file)

4. SPEC UPDATE SESSION (dedicated Claude chat)
   └─ Attach: current master spec + all pending variation files
   └─ Use the standard handoff prompt (see below)
   └─ Output: master-spec-v[NEXT]-draft.md

5. REVIEW & APPROVE
   └─ Mikey reviews draft
   └─ Requests edits if needed
   └─ Gives explicit approval in chat

6. PROMOTE
   └─ Copy old live version to /archive/
   └─ Rename draft to master-spec-v[NEXT].md (remove -draft)
   └─ Move all applied VAR files to /variations/applied/
   └─ Update Claude Project Knowledge with new master spec
   └─ Update this file's "Last Updated" date and version ref
```

---

## Standard Spec Update Session — Handoff Prompt

Use this prompt verbatim when opening a Spec Update Session:

```
You are acting as the Harmony Spec Updater agent.

Your inputs:
- Current master spec: [attached — master-spec-v[X.X].md]
- Approved variation files: [attached — VAR-001, VAR-002, ...]

Your task:
1. Incorporate all variation files into the master spec
2. Output a complete master-spec-v[X.X.X]-draft.md
3. Do not change anything outside the scope of the variation files
4. Flag any conflicts, ambiguities, or sections that need Mikey's decision before
   you can apply a variation — list these at the TOP of your response before the draft
5. Note the VAR IDs applied in the draft's changelog section

Do not summarise. Output the full draft document.
```

---

## VAR ID Management

- IDs are sequential integers: VAR-001, VAR-002, VAR-003...
- Never reuse an ID, even if a variation is rejected
- Rejected variations stay in `/pending/` with status marked `Rejected` — do not delete
- Track the current highest ID at the top of this file:

**Current highest VAR ID: VAR-009** ← update this each time a new VAR is created

---

## Relationship to ADRs

- ADRs document *why* a decision was made (context, options considered, rationale)
- VARs document *what* changes to make to the master spec as a result
- A single ADR may produce one or more VARs
- Reference the ADR in the VAR file's header field

---

## What Goes in Project Knowledge vs CoWork

| Location | Content |
|---|---|
| **CoWork** | This process file, HARMONY-CONTEXT.md, agent handoff prompts |
| **Project Knowledge** | Current live master spec (updated after each version promotion) |
| **Local files** | All variation files, ADRs, archive versions |

---

## Session Orientation for Claude

If you are a Claude session reading this file, here is what you need to know:

- This is the Harmony project by Mikey — a Universal Spatial Address Protocol platform
- The master spec is the single source of truth for all architectural and product decisions
- You must not modify the master spec directly — capture any decisions as a VAR file
- If Mikey asks you to make an architectural decision, create a VAR file and ask him to approve it before treating it as canonical
- When in doubt, create the VAR file and flag it for review rather than assuming
