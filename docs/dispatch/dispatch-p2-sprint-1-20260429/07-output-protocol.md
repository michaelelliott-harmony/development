# Output Protocol — What to Produce and Where to Put It

---

## Deliverables

| Deliverable | Location | Status Needed |
|---|---|---|
| Feature branch | `feature/p2-sprint-1-cherry-pick` (pushed to origin) | Done before PR |
| Pull request | Against `main` | Must reference all 5 modifications and their ADRs |
| Session report | `PM/sessions/2026-04-29-p2-sprint-1.md` | Done before session closes |

---

## Session Report Format

File at: `PM/sessions/2026-04-29-p2-sprint-1.md`

Required sections:
1. **Session Summary** — one paragraph, what was accomplished
2. **Branch** — name and commit hash
3. **Modifications Applied** — table of all 5 mods, file changed, ADR reference, status
4. **Test Results** — number of tests passing, any failures and how resolved
5. **Decisions Made** — any decisions you made during the session and your authority basis
6. **Known Gaps / Open Items** — anything that was not completed and why
7. **HARMONY UPDATE** — mandatory final line:

```
HARMONY UPDATE | 2026-04-29 | Pillar 2 Sprint 1 | feature/p2-sprint-1-cherry-pick | 
Tests: [N] passing | Modifications: 5/5 applied | PR: [URL or "pending"] | 
Status: [complete/partial]
```

---

## PR Description Template

```markdown
## Pillar 2 Sprint 1 — Foundation Pipeline (V2.0 Compliance)

### Summary
Cherry-pick of Branch B pipeline modules with five V2.0 compliance modifications.

### Branch source
Modules cherry-picked from `origin/claude/pillar-2-sprint-1-m1m2-ef4b6132`
CLI packaging from `origin/claude/p2-m1-source-adapters`

### Modifications
| # | File | Change | ADR |
|---|---|---|---|
| 1 | extract.py | source_lineage JSONB, valid_from mandatory, known_names enforcement | ADR-024 STD-V01, STD-V05 |
| 2 | runner.py | data_quality on asset bundle, field_descriptors on cell payload | ADR-024 STD-V02, ADR-022 |
| 3 | normalise.py | crs_authority + crs_code on geometry records | ADR-024 STD-V03 |
| 4 | manifest.py | source_tier range 1–4 enforced, Tier 0 blocked | ADR-022 D3, ADR-018 |
| 5 | all adapters | requests → httpx[http2] | DEC-021 |

### Tests
[N] tests passing. Zero failures.

### Acceptance criteria
All Sprint 1 AC from V2.0 brief §6.2 pass. See dispatch 04-acceptance-criteria.md.
```

---

## What Does NOT Go in This PR

- No migration files (migrations are produced in a separate deliverable and
  require Mikey's gate before execution)
- No changes to Pillar 1 source code
- No changes to ADR documents
- No changes to main branch docs outside `PM/sessions/`
