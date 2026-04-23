# 01_SAFETY_BOUNDARY.md
## Absolute Safety Rules — Read Before Touching Anything

---

## The Inviolable Rule

**This reorganisation touches documentation and folder structure only.**
**Source code, tests, migrations, and running infrastructure are never touched.**

If you find yourself about to modify a `.py`, `.sql`, `.yml`, or `.json` file inside `src/` or `tests/` — stop. That action is outside the scope of this dispatch. Flag it in your output report and do not proceed.

---

## Do Not Touch — Ever

| Path | Why |
|---|---|
| `src/core/` | Pillar 1 cell system — live, tested, production-grade |
| `src/api/` | Pillar 1 HTTP API — 12 endpoints, 157 tests passing |
| `src/db/migrations/` | Migration files — each one required for schema history |
| `src/db/schemas/` | Schema definitions — referenced by live code |
| `src/ingestion/` | Pillar 2 pipeline — active build |
| `tests/` | All test suites — 157 passing tests must continue to pass |
| `docker-compose.yml` | Infrastructure definition |
| `.env` | Live secrets — do not read, do not move, do not touch |
| `.env.example` | Template — leave in place |
| Any `.git/` directory | Version control internals |

---

## Do Not Delete — Anything

This dispatch contains **zero deletions**. Every file is either:
- Moved to its correct location
- Renamed to the correct convention
- Left in place if its destination is ambiguous (flagged for review)

If a file appears to be a duplicate, flag it. Do not delete it.

---

## The Validation Folder Exception

The `validation/` folder was created by a previous Claude Code session during Pillar 2 API testing. Before moving anything from it:

1. List all files inside it
2. For each file, determine: is this a test file worth keeping, or a temporary build artefact?
3. Include this assessment in the `REORG_PLAN.md`
4. Do not route any file from `validation/` until Mikey has confirmed the plan

---

## Confirming Safety After Execution

After Phase 2 is complete, run the following to confirm nothing broke:

```bash
# Confirm test suite still passes
cd harmony && python -m pytest tests/ -q

# Confirm API is still importable
cd harmony && python -c "from src.api import app; print('API OK')"

# Confirm core module is still importable  
cd harmony && python -c "from src.core import cell_key; print('Core OK')"
```

If any of these fail, stop immediately and report. Do not attempt to fix — report the failure with full output.
