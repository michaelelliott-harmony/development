# Harmony Spatial Operating System — Pillar I — Spatial Substrate
# Session 04 Summary: Alias System

> **Date:** 2026-04-18  
> **Session Type:** Technical Build  
> **Active Pillar:** Pillar 1 — Spatial Substrate  
> **Active Milestone:** Milestone 2 — Identity Services  
> **Builder Agent:** Spatial Substrate Engineer (Builder Agent 4)  
> **Schema Version Affected:** v0.1.3

---

## Summary

Designed and implemented the complete Alias System for Harmony's Spatial Substrate, delivering counter-based alias generation, namespace handling, lifecycle management, and registry integration. Built against the locked `alias_namespace_rules.md` specification and ADR-006 (Alias Namespace Model). Produced 10 deliverables: the alias service module, namespace counter DDL, database migration, registry integration, sample entity records, a 62-test suite (all green), ADR-012, this session summary, and a PM report. The alias system enforces the `(alias, namespace)` tuple as the unit of identity, 180-day grace periods on retired alias reuse, reserved prefix filtering, case-insensitive lookup with uppercase storage, and mandatory namespace on every resolution call.

---

## Files Produced

| # | Deliverable | Path |
|---|-------------|------|
| 1 | Alias Service Module | `harmony/packages/alias/src/alias_service.py` |
| 2 | Database Migration — Namespace Registry | `harmony/db/migrations/002_alias_namespace_registry.sql` |
| 3 | Database Schema (updated) | `harmony/db/identity_registry_schema.sql` |
| 4 | Registry Service (updated) | `harmony/packages/registry/src/registry.py` |
| 5 | Sample Entity Records (3 entities added) | `harmony/data/sample-central-coast-records.json` |
| 6 | Test Suite | `harmony/packages/alias/tests/test_alias_service.py` |
| 7 | ADR-012 — Alias Generation Architecture | `harmony/docs/adr/ADR-012-alias-generation-architecture.md` |
| 8 | Session Summary (this file) | `harmony/docs/sessions/SESSION_04_SUMMARY.md` |
| 9 | PM Session Report | `PM/sessions/2026-04-18-pillar-1-session-4-alias-system.md` |

All paths are relative to `pillar-1-spatial-substrate/`.

---

## Sample Entity Records

| # | Entity ID | Subtype | Description | Alias | Namespace |
|---|-----------|---------|-------------|-------|-----------|
| 1 | ent_bld_k3f9m2 | bld | Building — Gosford waterfront | ENT-1 | au.nsw.central_coast.entities |
| 2 | ent_prc_h7w4n1 | prc | Parcel — Gosford CBD | ENT-2 | au.nsw.central_coast.entities |
| 3 | ent_rod_b2c8v5 | rod | Road segment — Terrigal | ENT-3 | au.nsw.central_coast.entities |

---

## Key Decisions

1. **Counter-based alias generation (ADR-012).** Aliases are generated via per-namespace atomic counters (`UPDATE ... RETURNING`), not derived from object properties. The counter is monotonically increasing and never decremented. This guarantees zero collision risk on auto-generation.

2. **Partial unique constraint replaces full UNIQUE.** Migration 002 drops the Session 3 full UNIQUE constraint on `alias_table` and replaces it with a partial unique index (`WHERE status = 'active'`). This enables the full alias lifecycle: multiple retired entries can coexist for the same `(alias, namespace)` tuple.

3. **180-day grace period enforced in application code.** The grace period is not a database constraint but an application-level check in `bind_alias()`. This matches ADR-006's implementation notes and keeps the database layer simple.

4. **Namespace format: regex is the spec.** The locked regex `^[a-z]{2,4}(\.[a-z0-9_]{2,32}){2,5}$` permits 3–7 segment namespaces. Convention recommends 4 segments minimum (country.state.region.class), but the regex is authoritative. Tests were corrected to match the regex, not the convention.

---

## Verification Results

### Test Suite: Alias Service (62 tests)

```
harmony/packages/alias/tests/test_alias_service.py — 62 passed, 0 failed

Test Classes:
  TestAliasFormatValidation     — 16 tests (format, case normalisation, reserved prefixes)
  TestNamespaceFormatValidation —  9 tests (format, case normalisation, boundaries)
  TestAliasExtraction           —  5 tests (prefix and number extraction)
  TestAliasIdGeneration         —  3 tests (format, uniqueness, Crockford charset)
  TestReservedPrefixes          —  2 tests (reject all reserved, accept non-reserved)
  TestNamespaceResolution       —  3 tests (error class reporting)
  TestAliasConflictError        —  3 tests (conflict, reason, grace period)
  TestCrossNamespaceIndependence—  1 test  (same alias valid in different namespaces)
  TestGracePeriod               —  4 tests (180 days, arithmetic, within, after)
  TestRegexPatterns             —  5 tests (regex matches spec, boundary cases)
  TestRegistrationFlowMock      —  4 tests (resolve/bind with mocked DB)
```

### Cumulative Test State

| Suite | Tests | Status |
|-------|-------|--------|
| Session 2 — Identity Schema | 60 | All pass |
| Session 4 — Alias Service | 62 | All pass |
| **Total** | **122** | **All pass** |

---

## Spec Compliance Checklist

| Requirement | Source | Status |
|-------------|--------|--------|
| Alias format `^[A-Z]{2,4}-[0-9]{1,6}$` | §2 | Implemented + tested |
| Case-insensitive lookup, uppercase storage | §2 | Implemented + tested |
| Namespace format `^[a-z]{2,4}(\.[a-z0-9_]{2,32}){2,5}$` | §3 | Implemented + tested |
| `(alias, namespace)` tuple is unit of identity | §4 | Implemented + tested |
| Partial unique constraint `WHERE status = 'active'` | §5.1 | Implemented in migration 002 |
| Cross-namespace independence | §5.2 | Tested |
| `409 Conflict` on active collision | §5.3 | Implemented |
| Lifecycle: free → active → retired | §6 | Implemented |
| 180-day grace period | §6 | Implemented + tested |
| `400 Bad Request` if namespace missing | §7.4 | Implemented + tested |
| Reserved prefixes: TEST, DEMO, TMP, SYS | §8 | Implemented + tested |
| Counter-based auto-generation | §9 | Implemented (ADR-012) |
| Counter never decremented | §9 | Implemented |

---

## Corrections Applied

1. **Namespace format** — Session 3 used `cc.au.nsw.cc` as sample namespaces. Corrected to country-first format `au.nsw.central_coast.cells` per the locked spec.

2. **Partial unique constraint** — Session 3's `alias_table` had a full UNIQUE constraint. Migration 002 replaces this with a partial unique index to support the retired-alias reuse lifecycle.

3. **Three-segment namespace validity** — Two tests initially asserted that 3-segment namespaces (e.g., `au.nsw.cells`) were invalid. The locked regex `{2,5}` permits them. Tests corrected to match the spec.

---

## Cross-Pillar Implications

- **Pillar 2 (Visual Fidelity):** Entities now have aliases and can be referenced by human-friendly names in visual layer metadata.
- **Pillar 4 (Temporal Versioning):** The alias lifecycle (active → retired with grace period) will need to integrate with temporal versioning once ADR-007 is implemented. The `effective_from`/`effective_to` columns on `alias_table` are ready for this.
- **Pillar 5 (Agent Layer):** Agents resolving aliases must always specify a namespace. The three-layer agent model (ADR-009) should include namespace context in agent session configuration.

---

## Open Items Carried Forward

1. **Database integration tests** — The current test suite mocks the database. Full PostgreSQL integration tests are deferred to CI/CD pipeline setup.
2. **Alias permissions** — Who can mint and retire aliases (per `alias_namespace_rules.md` §11). Needs the access control layer.
3. **Bulk alias migration tooling** — Deferred to Milestone 3+.
4. **ADR-011 gate-3-closure reference** — The brief referenced `ADR-011-gate-3-closure-identity-generation-order.md` which does not exist in the archive. The alias registration order was taken from the inline brief constraints. This should be reconciled.

---

*End of Session 04 Summary*
