# 00_READ_FIRST.md
## Dispatch: Project Reorganisation + Terminology Migration
## Task ID: reorg-20260421
## Tool: Claude Code

---

## Reading Order

Read every file before touching anything:

1. This file — orientation and safety rules
2. `01_SAFETY_BOUNDARY.md` — what you must never touch
3. `02_TERMINOLOGY_MIGRATION.md` — OpenClaw → Managed Agents changes
4. `03_CURRENT_STRUCTURE.md` — what exists now
5. `04_TARGET_STRUCTURE.md` — what it must look like when done
6. `05_EXECUTION_PLAN.md` — the exact steps in order
7. `06_NEW_FILES.md` — files to create from scratch
8. `07_OUTPUT_PROTOCOL.md` — how to report back

---

## The Two-Phase Rule

**This dispatch executes in two phases. Phase 1 produces a plan. Phase 2 executes it.**

**Phase 1 — PLAN (do this first):**
Read the current file system. Map every existing file to its target location using the rules in this dispatch. Produce `REORG_PLAN.md` listing every move, rename, and creation. Stop. Do not move anything yet.

**Phase 2 — EXECUTE (only after plan is reviewed):**
Mikey reviews `REORG_PLAN.md` and replies "approved" or with amendments. Only then execute the moves in the order specified in `05_EXECUTION_PLAN.md`.

---

## What This Dispatch Is

The Harmony project has accumulated a folder structure that no longer matches its canonical layout. This dispatch does three things:

1. **Reorganises** the file and folder structure to match the canonical layout in `HARMONY_PROJECT_STRUCTURE.docx`
2. **Migrates terminology** — every reference to "OpenClaw" in documentation files is replaced with the correct Managed Agents terminology
3. **Creates new infrastructure files** — `CURRENT_SPEC.md`, `DECISION_LOG.md`, and an updated `CLAUDE.md`

**This dispatch does not touch source code.** The safety boundary is absolute and defined in `01_SAFETY_BOUNDARY.md`.
