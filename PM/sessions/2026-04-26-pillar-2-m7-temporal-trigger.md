# Harmony Update │ Pillar 2 │ M7 — Temporal Trigger Layer │ Status: Done │ Tool: Code

**Session Date:** 2026-04-26
**Agent:** Dr. Yusuf Adeyemi — Lead Pipeline Architect, Pillar 2
**Branch:** `claude/feature/p2-m7-temporal-trigger-layer-20260426`
**Security Preamble Version:** v1.0

---

## Harmony Decision │ ADR-016 Temporal Trigger Architecture │ Status: Implemented

ADR-016 is Accepted (April 22, 2026). Reviewed in full at session start.
All implementation decisions in M7 are governed by ADR-016.

**Discrepancy noted:** The Pillar Brief (p2-data-ingestion-brief-v1-1.md) refers to the temporal trigger ADR as "ADR-015" in Tasks 10 and 11, and in Section 7 Open Decisions. The accepted ADR in the repository is ADR-016. This appears to be a reference holdover from the drafting process. Implementation is against ADR-016 (Accepted). No action required — for information only.

**Conflict resolved (dispatch takes precedence):**
ADR-016 §2.2 specifies a minimum 5-second interval between API requests.
The dispatch briefing (real API contract from Denniss Reddy, April 24, 2026) specifies 2 seconds.
Implemented: 2-second minimum interval, per dispatch. The brief notes: "the real API contract takes precedence over assumptions made before we had the documentation."

---

## Network Connectivity Status — BLOCKED

The NSW Planning Portal API (`api.apps1.nsw.gov.au`) returns:
```
HTTP 403 — Host not in allowlist
```

This is an outbound proxy restriction in the current environment. The domain is network-reachable but blocked by the proxy's allowlist policy. **The full implementation has been built against the confirmed API contract** (from Denniss Reddy's documentation, April 24, 2026).

**Action required:** Add `api.apps1.nsw.gov.au` to the environment's outbound proxy allowlist before running `pytest -m network`. All other acceptance criteria pass without network access.

---

## Deliverables

### D1 — PermitSourceAdapter Interface
- **File:** `harmony/pipelines/temporal/adapter.py`
- Abstract base class `PermitSourceAdapter` with three required methods:
  - `poll(since_datetime) → list[PermitRecord]`
  - `get_permit_polygon(permit_id) → dict | None`
  - `get_permit_address(permit_id) → str | None`

### D2 — NSWPlanningPortalAdapter
- **File:** `harmony/pipelines/temporal/adapter.py` (class `NSWPlanningPortalAdapter`)
- Polls all four NSW ePlanning endpoints: DA (`/OnlineDA`), CDC (`/OnlineCDC`), CC (`/OnlineCC`), OC (`/OC`)
- **Parameters sent as HTTP headers** (not query params) — per dispatch briefing critical note
- CouncilName filter: `{"CouncilName": ["Central Coast Council"]}`
- Pagination: increments PageNumber until response length < page_size
- Rate limiting: 2-second minimum interval per endpoint
- Retry: 30s → 120s → 480s on failure; logs as deferred after 3 attempts
- Normalises NSW field names → canonical `PermitRecord` dataclass
- `classify_event()` function maps permit records to `EventType` enum values

### D3 — Permit-to-Cell Resolver
- **File:** `harmony/pipelines/temporal/resolver.py` (class `PermitCellResolver`)
- Four-level resolution hierarchy (ADR-016 §2.6):
  1. **Spatial** — CC/OC X/Y coordinates → r10 Harmony cell via `derive_cell_key`
  2. **Lot/Plan** — Lot + PlanLabel composite key against known_names entity index
  3. **Address** — DA FullAddress against known_names via Pillar 1 `/resolve/known-name`
  4. **Unresolved** — logged to audit trail with full record; never discarded
- `resolve_batch()` returns `(resolved_events, unresolved_permits)` tuple
- Permits with no state machine event type (e.g. Determined DAs) silently skipped

### D4 — Cell State Transition Service
- **File:** `harmony/pipelines/temporal/transitions.py`
- Classes: `AuditLog` (SQLite append-only), `CellTransitionService`
- **State machine** (ADR-016 §2.3):
  - `stable` + DA lodged → `change_expected`
  - `change_expected` + DA withdrawn/refused → `stable`
  - `change_expected` + CC issued → `change_in_progress`
  - `change_in_progress` + OC issued → `change_confirmed`
- **Idempotent:** unique index on `(cell_key, permit_id, event_type)` in SQLite
- **Audit log** (ADR-016 §2.9): append-only `cell_transition_events` table
- **valid_from:** set to `OC DeterminationDate` on OC events. Never `datetime.now()`
- **Anomaly handling:** conflicting transitions logged to `result.anomalies`, not applied
- **Fidelity reset:** calls `PATCH /cells/{cell_key}/fidelity` on `change_confirmed`
- All writes via Pillar 1 HTTP API

### D5 — Temporal Field Activation Migration
- **File:** `harmony/pipelines/migrations/m7_temporal_field_activation.py`
- **Status:** `REQUIRES_APPROVAL = True` — **do not execute without Mikey's Telegram approval**
- Schema version: `0.2.0 → 0.3.0`
- `up()`: adds `cell_status` column, activates `valid_from`/`valid_to`/`version_of`/`temporal_status`, drops ADR-007 reservation trigger, adds indexes
- `down()`: removes `cell_status`, re-installs reservation trigger (does not drop data columns)
- `execute_with_approval(conn, approved_by, approved_at)` enforces Mikey-only approval

### D6 — Fidelity Reset Logic
- **File:** `harmony/pipelines/temporal/fidelity.py`
- `reset_photorealistic_fidelity(cell_key, p1_url)` — reads current structural slot, POSTs full-replacement via `PATCH /cells/{cell_key}/fidelity` with `photorealistic.status = "pending"`
- `build_pending_photorealistic_slot()` — returns the canonical reset structure (ADR-016 §2.5)
- `reset_photorealistic_fidelity_batch()` — batch reset for runner integration
- The `PATCH /cells/{cell_key}/fidelity` endpoint is already live in Pillar 1

### D7 — Test Suite
- **96 tests collected, 95 passing, 1 skipped (AC1 live network), 0 failing**
- Test files:
  - `tests/temporal/conftest.py` — fixtures, Gosford DA fixture loader
  - `tests/temporal/test_adapter.py` — 32 tests (adapter, normalisation, classification, headers, retry)
  - `tests/temporal/test_resolver.py` — 14 tests (all 4 resolution paths, batch)
  - `tests/temporal/test_transitions.py` — 24 tests (state machine, idempotency, anomalies, audit log)
  - `tests/temporal/test_acceptance.py` — 26 tests (AC1–AC8)
- **Gosford DA fixture:** `fixtures/gosford_da_fixture.json`
  - Structured from documented NSW API field schema (April 24, 2026)
  - Primary record: `DA/2026/0142` — 88 Mann Street, Gosford NSW 2250 (the Gosford Observation reference site)
  - Includes DA, CC, OC, and CDC records
  - **Note:** Live API call for fixture was not possible due to network block. Fixture uses confirmed field names from Denniss Reddy's API documentation.

### D8 — Session Report
- This document

---

## Acceptance Criteria Status

| # | Criterion | Status | Notes |
|---|---|---|---|
| AC1 | Adapter connects to DA API, retrieves ≥1 Central Coast record | ⚠️ PARTIAL | Structure/normalisation: PASS. Live call: SKIPPED (proxy blocks api.apps1.nsw.gov.au). Unblock needed. |
| AC2 | Permit address/coordinates resolve to Harmony Cell(s) | ✅ PASS | Spatial (X/Y→r10) and address (known_names) both tested |
| AC3 | All four state transitions produce correct cell_status values | ✅ PASS | Including reverse: change_expected → stable |
| AC4 | valid_from = OC DeterminationDate, not datetime.now() | ✅ PASS | Historical test date (2025-07-04) proves it's never now() |
| AC5 | photorealistic.status = pending after change_confirmed | ✅ PASS | Transition service + fidelity module tested |
| AC6 | Same event applied twice produces no duplicate transition | ✅ PASS | Idempotency tested 3× including N-repetition test |
| AC7 | Migration has working up and down functions | ✅ PASS | Approval enforcement tested; REQUIRES_APPROVAL=True |
| AC8 | ADR-016 Accepted before migration is produced | ✅ PASS | ADR-016 Accepted April 22, 2026; verified in test |

---

## Permit Events Summary (from Gosford fixture)

| Permit ID | Type | Status | Event | Target Transition |
|---|---|---|---|---|
| DA/2026/0142 | DA | Under Assessment | da_lodged | stable → change_expected |
| DA/2026/0211 | DA | Withdrawn | da_withdrawn | change_expected → stable |
| CC/2026/0055 | CC | Issued | cc_issued | change_expected → change_in_progress |
| OC/2025/0312 | OC | Issued | oc_issued | change_in_progress → change_confirmed |
| CDC/2026/0033 | CDC | Issued | cc_issued | change_expected → change_in_progress |

- **State transitions in test suite:** 3 forward + 1 reverse = 4 unique transitions validated
- **Unresolved permits:** 1 (DA/2026/NORESOLUTION — deliberately unresolvable test case)
- **Fidelity resets triggered:** On every change_confirmed event

---

## Migration File — Requires Approval

**File:** `04_pillars/pillar-2-data-ingestion/harmony/pipelines/migrations/m7_temporal_field_activation.py`
**Flag:** `requires_approval: true`
**Gate:** Mikey's logged Telegram approval required before execution
**Authority:** AUTHORITY_MATRIX.md — "Migration execution: Mikey only"
**Schema change:** `0.2.0 → 0.3.0`

Do not execute `up()` without approval. The migration is safe to inspect and review. The `execute_with_approval()` guard will raise `PermissionError` for any non-Mikey approver.

---

## File Manifest

```
04_pillars/pillar-2-data-ingestion/
├── fixtures/
│   └── gosford_da_fixture.json            ← Gosford DA test fixture (NSW API schema)
├── harmony/
│   └── pipelines/
│       ├── temporal/
│       │   ├── __init__.py
│       │   ├── adapter.py                 ← D2: PermitSourceAdapter + NSWPlanningPortalAdapter
│       │   ├── fidelity.py                ← D6: Fidelity reset logic
│       │   ├── models.py                  ← Shared data models (PermitRecord, PermitEvent, etc.)
│       │   ├── resolver.py                ← D3: Permit-to-Cell resolver
│       │   └── transitions.py             ← D4: Cell State Transition Service + AuditLog
│       └── migrations/
│           ├── __init__.py
│           └── m7_temporal_field_activation.py  ← D5: Migration (REQUIRES APPROVAL)
├── pytest.ini                             ← Test config with 'network' marker
└── tests/
    └── temporal/
        ├── __init__.py
        ├── conftest.py                    ← Fixtures, Gosford fixture loader
        ├── test_acceptance.py             ← AC1–AC8 acceptance tests
        ├── test_adapter.py                ← D2 adapter tests
        ├── test_resolver.py               ← D3 resolver tests
        └── test_transitions.py            ← D4 transition service tests
```

---

## Open Actions

1. **Network unblock (blocking AC1 live validation):** Add `api.apps1.nsw.gov.au` to the environment's outbound proxy allowlist. Run `pytest -m network` to validate AC1 against the live API once unblocked.

2. **Migration approval gate:** Raise with Mikey for review. File is at `harmony/pipelines/migrations/m7_temporal_field_activation.py`. Do not execute without logged Telegram approval.

3. **PATCH /cells/{cell_key}/status endpoint:** The transition service calls this endpoint to update `cell_status` on the cell record. This endpoint is not yet in the Pillar 1 API (only `/fidelity` is live). Two options:
   - Ask Marcus to add `PATCH /cells/{cell_key}/status` alongside the D5 migration
   - Encode `cell_status` as a metadata field via entity metadata interim (same pattern as Sprint 2 fidelity interim)
   Current implementation logs the call and handles failure gracefully (cell_status is still tracked in the audit log as source of truth).

4. **Gosford DA fixture — live validation:** Once the network is unblocked, replace the structured fixture data with a live API response from DA API query. The fixture field structure matches the documented contract exactly.

---

## HARMONY UPDATE

```
HARMONY UPDATE │ Pillar 2 │ M7 — Temporal trigger layer │ Status: Done │ Tool: Code
HARMONY DECISION │ ADR-016 Temporal trigger architecture │ Status: Implemented
```

---

## Security Footer

- **Preamble version:** v1.0
- **Destructive actions requested:** 1 (migration execution — NOT executed, flagged for Mikey approval)
- **Destructive actions approved via Telegram:** 0
- **Escalations raised:** 0
- **Secrets discovered in-context:** 0 (NSW ePlanning API is public, no credentials required)
- **Dependency changes:** 0 (all dependencies — requests, pydantic, sqlite3 — already present in environment)

---

*Harmony Pillar 2 — M7 Session Report — April 26, 2026*
*Dr. Yusuf Adeyemi — Lead Pipeline Architect*
