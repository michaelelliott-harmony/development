# 02_TERMINOLOGY_MIGRATION.md
## OpenClaw → Managed Agents Terminology Migration

---

## Why This Change Is Being Made

OpenClaw was the project name for Harmony's autonomous development team
infrastructure. The team has decided to use Claude Managed Agents as the
infrastructure layer instead of a custom-built orchestrator. The terminology
throughout all documentation must reflect this.

---

## Folder Renames

| Old Folder | New Folder | Notes |
|---|---|---|
| `openclaw/` | `agents/` | Top-level rename |
| `openclaw/agents/` | `agents/prompts/` | Agent prompt files |
| `openclaw/security/` | `agents/security/` | Security policy |
| `openclaw/orchestrator/` | `agents/managed/` | Managed Agents config |

---

## File Renames

| Old Filename | New Filename | Location |
|---|---|---|
| `OPENCLAW.md` | `AGENTS.md` | `agents/` |
| `SECURITY_POLICY.md` | `SECURITY_POLICY.md` | `agents/security/` (unchanged name) |
| `schema.sql` | `task-queue-schema.sql` | `agents/managed/` |
| `ORCHESTRATOR.md` | `MANAGED_AGENTS_SETUP.md` | `agents/managed/` |

---

## Text Replacements in Documentation Files

For every `.md` file outside of `src/` and `tests/`, apply these
replacements. Do them carefully — search for exact strings and replace.
Do not do bulk find-replace across the entire repo blindly.

| Find | Replace With | Context |
|---|---|---|
| `OpenClaw` | `Harmony Agent Team` | General references |
| `openclaw/` | `agents/` | File path references |
| `OPENCLAW.md` | `AGENTS.md` | File references |
| `OpenClaw task queue` | `Managed Agents task queue` | Specific feature references |
| `OpenClaw orchestrator` | `Managed Agents orchestrator` | Specific feature references |
| `Claude Managed Agents` | `Claude Managed Agents` | Already correct — do not change |
| `custom orchestrator` | `Managed Agents` | Where applicable |

---

## Agent Prompt Files — Folder Migration Only

The agent prompt files (`TECH_LEAD.md`, `SPATIAL_ENGINEER.md`,
`BACKEND_ENGINEER.md`, `QA_AGENT.md`, `ADR_AGENT.md`, `REVIEWER.md`,
`DR_MARA_VOSS.md`) move to `agents/prompts/` with no content changes.

The content of these prompts is architecturally correct. Only their
location changes.

---

## Files to Check for OpenClaw References

Search these files for OpenClaw references and apply replacements:

- `CLAUDE.md`
- `agents/AGENTS.md` (formerly OPENCLAW.md)
- `agents/managed/MANAGED_AGENTS_SETUP.md`
- `docs/dispatch/**/*.md`
- `docs/specs/**/*.md`
- Any `*_report.md` files in `docs/reports/`

---

## What Does NOT Change

- The names of the AI personas (Dr. Mara Voss, etc.) — these are
  product personas, not infrastructure names
- ADR content — ADRs are immutable once accepted
- Any reference to "Managed Agents" that is already correct
- The security policy content — only its location changes
