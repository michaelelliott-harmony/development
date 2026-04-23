# ADR-015: Temporal Trigger Architecture — Permit Feed Integration

| Field | Value |
|---|---|
| **Status** | Draft — requires Mikey's approval before acceptance |
| **Date** | April 19, 2026 |
| **Author** | Architecture Chat (for Dr. Mara Voss, Principal Architect) |
| **Supersedes** | None |
| **Related ADRs** | ADR-007 (Bitemporal Schema Reservation), ADR-011 (Entity Lifecycle) |
| **Pillar** | Pillar 2 — Data Ingestion Pipeline, Milestone 7 |
| **Approval Required** | Yes — Mikey must review and accept before any schema changes or migration execution |

---

## 1. Context

The Harmony Cell registry, as shipped in Pillar 1, reserves four bitemporal fields on every cell record: `valid_from`, `valid_to`, `version_of`, and `temporal_status` (ADR-007). These fields exist in the schema but are not populated — they carry default values and are enforced as `403 Reserved` to prevent premature writes.

The question this ADR resolves is: what populates these fields, when, and from what source of truth?

Without a temporal trigger mechanism, every cell's `valid_from` would reflect the moment Harmony ingested the data — not the moment the real world changed. A building completed in January 2026 but ingested in April 2026 would carry `valid_from: 2026-04-19`. This is ingestion time, not reality time. The distinction matters for every downstream consumer: historical queries ("what was here in 2024?"), investment analysis ("when did this neighbourhood change?"), and autonomous navigation ("is this obstacle data current?").

The Gosford Observation — a completed residential building on Mann Street still showing as a construction site on Google Maps — demonstrates the structural consequence of platforms that refresh on a capture schedule rather than a real-world event schedule. Harmony closes this gap by connecting to official permit feeds that report real-world building events as they are recorded by planning authorities.

---

## 2. Decision

### 2.1 Canonical Source of Temporal Truth

The canonical source of temporal truth for a Harmony Cell is the official permit record from the relevant planning authority — not the ingestion timestamp, not satellite imagery vintage, and not manual observation.

For the Central Coast NSW pilot, this means the NSW Planning Portal's DA (Development Application), CDC (Complying Development Certificate), and PCC (Post Consent Certificate, including Occupation Certificates) data feeds.

The governing rule: **`valid_from` on a cell record is set to the completion certificate date from the Planning Portal, not `datetime.now()` at ingestion.**

### 2.2 Acquisition Model: Pull-Based Polling

The temporal trigger layer acquires permit data via scheduled polling (pull model) of the NSW Planning Portal APIs.

**Why pull, not push:**
- The NSW Planning Portal does not currently advertise webhook or event subscription endpoints for the DA, CDC, or PCC feeds.
- Pull is universally reliable — it works regardless of whether the source supports push semantics.
- Pull allows Harmony to control polling frequency, retry logic, and backfill without depending on the source's delivery guarantees.
- If push (webhooks) becomes available from NSW or other jurisdictions in the future, it can be added as a non-breaking enhancement alongside pull. The state transition service is agnostic to how events arrive — it processes normalised permit events regardless of acquisition method.

**Polling schedule:**
- Default: daily at 06:00 AEST (before business hours, after overnight batch updates to the Portal)
- High-activity areas (configurable per LGA): hourly during business hours (08:00–18:00 AEST)
- Minimum interval between requests to the same endpoint: 5 seconds (respectful polling)
- Maximum retry attempts on failure: 3, with exponential backoff (30s, 120s, 480s)
- After 3 failures: log as deferred, include in daily PM report, retry on next scheduled poll

### 2.3 Cell State Machine

A new field `cell_status` is added to the cell record with four possible values:

```
stable ──[DA lodged]──→ change_expected
                             │
                      [CC issued]
                             │
                             ▼
                      change_in_progress
                             │
                      [OC issued]
                             │
                             ▼
                      change_confirmed
```

Reverse transition: `change_expected → stable` on DA withdrawn or refused.

| Status | Trigger | Meaning | Downstream Impact |
|---|---|---|---|
| `stable` | Default at registration | No known change expected. Current data reflects reality. | All consumers trust cell data at face value. |
| `change_expected` | DA lodged | A permit has been lodged. Current data will become stale. | Reagent can surface "development activity detected." Knowledge layer can note pending change. |
| `change_in_progress` | Construction Certificate issued | Active construction confirmed. Structural data is transitional. | Navigation Agents reduce confidence in structural geometry. Renderer may flag area for visual refresh. |
| `change_confirmed` | Occupation Certificate issued | Development complete. Cell requires re-ingestion. | `valid_from` updated to certificate date. Photorealistic fidelity reset to `pending`. Cell queued for structural data refresh. |

### 2.4 Temporal Field Population Rules

| Field | Populated When | Populated With | Rule |
|---|---|---|---|
| `valid_from` | On `change_confirmed` transition | Occupation certificate date from the Planning Portal | Never `datetime.now()`. Always the certificate date. |
| `valid_to` | When a superseding change is confirmed for the same cell | The `valid_from` of the superseding version | Remains `null` for the current version of a cell. |
| `version_of` | On `change_confirmed` when a prior version exists | The `canonical_id` of the prior cell version | Creates the version chain. |
| `temporal_status` | On `change_confirmed` for the prior version | Changes from `current` to `superseded` | The new version becomes `current`. |

### 2.5 Multi-Source Architecture

The temporal trigger layer is designed as a pluggable adapter pattern:

```
PermitSourceAdapter (interface)
    ├── NSWPlanningPortalAdapter (Central Coast pilot)
    ├── [future] QLDPlanningAdapter
    ├── [future] VICPlanningAdapter
    └── [future] GenericPermitCSVAdapter
```

Each adapter implements:
- `poll(since_datetime) → list[PermitEvent]`
- `get_permit_polygon(permit_id) → Geometry | None`
- `get_permit_address(permit_id) → str | None`

The state transition service consumes `PermitEvent` objects and is completely agnostic to which adapter produced them. Adding a new jurisdiction means implementing a new adapter — not modifying the transition logic.

### 2.6 Event Model: Event-Sourced, Not Snapshot-Updated

Cell state transitions are recorded as an append-only event log, not as in-place updates to a status field. The current `cell_status` is derived from the most recent event.

```
Event log entry:
{
    "cell_key": "...",
    "event_type": "da_lodged | cc_issued | oc_issued | da_withdrawn",
    "permit_id": "DA/2026/0142",
    "permit_source": "nsw_planning_portal",
    "event_date": "2026-03-15",
    "ingested_at": "2026-04-19T06:00:00Z",
    "previous_status": "stable",
    "new_status": "change_expected"
}
```

**Why event-sourced:**
- Full audit trail — every state transition is traceable to a specific permit event
- Debugging — if a cell is in an unexpected state, the event log shows exactly how it got there
- Replay capability — if the state machine logic is corrected, events can be replayed to derive correct current state
- Analytics — downstream consumers can query the event log for temporal patterns ("how many cells transitioned in Q1?")

The `cell_status` field on the cell record is a denormalised derived value, updated on each event for query performance. The event log is the source of truth.

---

## 3. Consequences

### What This Enables

- **Pillar 3 (Rendering):** Can query `fidelity_coverage.photorealistic.status = pending` to prioritise visual refresh for recently changed areas. The city stays visually current.
- **Pillar 4 (Knowledge Layer):** Bitemporal queries activate — "what existed here in 2024?" becomes answerable. Temporal versioning is live.
- **Pillar 5 (Interaction Layer):** A user asking "is this still under construction?" gets an authoritative answer derived from official permit records, not stale imagery.
- **Reagent:** Development activity alerts, neighbourhood change tracking, temporal context for property valuation.
- **Investor Demonstration:** The Gosford site — completed apartments showing as construction on Google Maps — becomes a live proof point that Harmony is more current than Google.
- **Navigation Agents (Class II):** Can reduce confidence in structural geometry for cells in `change_in_progress` status, improving autonomous decision safety.

### What This Costs

- **External API dependency:** Pillar 2 now depends on the NSW Planning Portal being available. Mitigation: retry logic, deferred processing, and the fact that permit data is not time-critical at the second level — daily polling is sufficient.
- **Address resolution complexity:** Not all permits carry polygon boundaries. Some carry only street addresses, which must be geocoded against the cell's `known_names` index. Fallback resolution adds a failure path that must be handled gracefully.
- **Schema migration:** The temporal field activation migration is an irreversible schema change once executed in production. Mitigation: up and down migration functions, tested against dev database, gated on Mikey's approval.

### What This Does Not Do

- Does not implement a public-facing contribution API — that is a future milestone
- Does not trigger automatic re-ingestion of structural or photorealistic data — `change_confirmed` sets `photorealistic.status = pending` as a signal, not a trigger
- Does not modify `canonical_id` or `cell_key` of any existing cell — state transitions update status fields only
- Does not cover jurisdictions beyond the Central Coast LGA in this milestone

---

## 4. Alternatives Considered

### Alternative A: Satellite Imagery Change Detection

Detect changes by comparing consecutive satellite or aerial captures. Reject: this is the model Harmony is designed to beat. It refreshes on a capture schedule, not a real-world event schedule. It also cannot distinguish between a completed building and an in-progress construction site — the permit record can.

### Alternative B: Crowdsourced Change Reports

Allow users or field agents to report changes. Reject for MVP: introduces trust and moderation complexity. May be valuable as a supplementary signal in the future, but cannot be the canonical source of temporal truth — official permit records have legal authority that crowdsourced reports do not.

### Alternative C: Snapshot-Updated Cell Status

Update `cell_status` as an in-place field update with no event log. Reject: loses audit trail, makes debugging impossible, and prevents temporal analytics. The append-only event log is marginally more storage but dramatically more useful.

### Alternative D: Push-Based Event Ingestion

Subscribe to webhook notifications from the Planning Portal instead of polling. Defer, not reject: the NSW Planning Portal does not currently advertise webhook support. If it becomes available, the adapter interface supports adding a push listener alongside the pull poller without modifying the state transition service.

---

## 5. Implementation Constraints

1. **ADR-015 must be accepted before any schema changes are written.** This is a hard gate.
2. **The temporal field migration requires Mikey's approval before execution.** Flag as `requires_approval: true` in session output.
3. **The permit adapter must not store API credentials.** The NSW Planning Portal API is public. If future endpoints require authentication, credentials must be managed through environment variables or a secrets vault — never in code, manifests, or prompts.
4. **The state transition service must be idempotent.** Applying the same permit event twice produces no duplicate state change, no duplicate event log entry, and no side effects.
5. **The adapter must implement a generic PermitSourceAdapter interface.** NSW-specific logic is isolated in the NSWPlanningPortalAdapter. The state transition service, event log, and resolver are jurisdiction-agnostic.
6. **Geographic scope is limited to Central Coast LGA for this milestone.** Do not attempt to connect feeds from other LGAs.

---

## 6. Known Gaps (To Be Resolved Post-Milestone 7)

| Gap | Description | Resolution Path |
|---|---|---|
| Cell lifecycle completion | What transitions a cell from `change_confirmed` back to `stable` after re-ingestion of structural data? | Define a `re_ingested` event type or a `change_confirmed → stable` transition triggered by successful structural data refresh. Defer to Pillar 3/4 integration. |
| Multi-jurisdiction scaling | Adding QLD, VIC, or international jurisdictions requires new adapters with different field schemas, permit types, and API structures. | The PermitSourceAdapter interface is designed for this. Each jurisdiction is a new adapter implementation. No changes to the state transition service. |
| Push notification support | If the NSW Planning Portal adds webhook support, the adapter layer should be extended to receive push events alongside pull polling. | Design the adapter interface to support both. Pull is the baseline; push is an optimisation. |
| Conflicting permit events | How to handle a cell that receives `change_expected` while already in `change_in_progress` from a different permit? | Log as anomaly, do not apply the conflicting transition, escalate to PM report. This requires further analysis of real-world multi-permit scenarios. |

---

*ADR-015 — Temporal Trigger Architecture — Draft — April 2026*
*Status: Requires Mikey's approval before acceptance*
