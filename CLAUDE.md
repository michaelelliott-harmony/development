# Harmony — Spatial Operating System
## Repository Context for Claude Tools

This is the Harmony project repository. Before beginning any task,
read the required documents below in order.

---

## Required Reading — Every Session

Read these three documents before writing any code or making any decision:

1. **`docs/specs/CURRENT_SPEC.md`**
   Tells you which master specification is current and links to it.
   Read the spec it points to.

2. **`docs/specs/DECISION_LOG.md`**
   Decisions made since the last spec update. These are active and binding
   even if not yet incorporated into a formal spec version.

3. **`agents/AGENTS.md`**
   Current project state, open ADRs, active pillar, and open questions.
   This is the team's shared memory.

Do not begin implementation until all three have been read.

---

## Naming Conventions

All file and folder naming follows `docs/specs/HARMONY_PROJECT_STRUCTURE.docx`.
When in doubt about where a file belongs or what to name it, consult that
document.

---

## Safety Rules

- Source code lives in `src/`. Documentation lives in `docs/`.
  These do not mix.
- Secrets never appear in prompts, logs, or filenames. `.env.example` only.
- Agents work on feature branches. Never commit directly to `main`.
- Migrations are produced, not executed. Execution requires Mikey's approval.
- ADR first, code second. No implementation without a covering ADR.
- HARMONY UPDATE line required at the end of every session.

---

## Infrastructure

This project runs on Claude Managed Agents for autonomous build execution.
Agent prompts live in `agents/prompts/`.
Security policy lives in `agents/security/SECURITY_POLICY.md`.
Managed Agents configuration lives in `agents/managed/`.

---

## Pillar Status

See `agents/AGENTS.md` for current pillar status.
See `docs/specs/CURRENT_SPEC.md` for the active specification.
See `docs/adr/ADR_INDEX.md` for all architectural decisions.
