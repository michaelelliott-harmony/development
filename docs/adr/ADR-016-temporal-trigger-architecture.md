# ADR-016: Temporal Trigger Architecture — Permit Feed Integration

| Field | Value |
|---|---|
| **Status** | Accepted — approved by Mikey on April 22, 2026 |
| **Date** | April 19, 2026 (drafted) / April 22, 2026 (accepted) |
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

### 2.5 Fidelity Coverage Structure

When a cell is populated by ingestion, the `fidelity_coverage` field must carry the following structure:

```json
{
    "structural": {
        "status": "available",
        "source": "nsw_cadastral",
        "captured_at": "YYYY-MM-DD"
    },
    "photorealistic": {
        "status": "pending",
        "source": null,
        "captured_at": null
    }
}
```

When a cell transitions to `change_confirmed`, the photorealistic slot is reset:
- `photorealistic.status` → `pending`
- `photorealistic.source` → `null`
- `photorealistic.captured_at` → `null`

This signals to Pillar 3 that any existing photorealistic asset bundle for this cell is no longer accurate. The pipeline does not attempt to re-ingest photorealistic data — `pending` is a signal, not a trigger.

### 2.6 Address-to-Cell Resolution

Each permit record carries a lot address and (where available) a polygon boundary. The pipeline resolves permits to Harmony Cells using this hierarchy:

1. **Spatial intersection (preferred):** Use the permit polygon against the Harmony Cell grid at r10 resolution (parcel/building scale). If the polygon spans multiple cells, all intersecting cells are flagged.
2. **Address geocoding (fallback):** If spatial intersection fails (no polygon provided, or polygon is invalid), fall back to address geocoding via the cell's `known_names` index. Match the permit address string against indexed entity names.
3. **Unresolved (last resort):** If resolution fails entirely, log the permit as unresolved with the full permit record. Surface in the daily PM report. Do not discard — unresolved permits may be resolvable after additional data is ingested.

### 2.7 Error Handling for Permit Trigger Layer

The permit trigger layer must not block the primary ingestion pipeline. Failures in permit polling or resolution are logged and queued for retry. The following error states are handled:

- **API timeout or unavailability:** Retry with exponential backoff (30s, 120s, 480s), max 3 attempts, then log as deferred
- **Permit address unresolvable to cell:** Log as unresolved with full permit record, surface in daily PM report
- **Conflicting state transition** (e.g., `change_confirmed → change_expected`): Log as anomaly, do not apply transition, escalate to PM report
- **Duplicate permit event:** Idempotent handling — second application of the same event produces no state change or duplicate log entry

### 2.8 Multi-Source Architecture

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

### 2.9 Event Model: Event-Sourced, Not Snapshot-Updated

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

1. **ADR-016 must be accepted before any schema changes are written.** This is a hard gate.
2. **The temporal field migration requires Mikey's approval before execution.** Flag as `requires_approval: true` in session output.
3. **The permit adapter must not store API credentials.** The NSW Planning Portal API is public. If future endpoints require authentication, credentials must be managed through environment variables or a secrets vault — never in code, manifests, or prompts.
4. **The state transition service must be idempotent.** Applying the same permit event twice produces no duplicate state change, no duplicate event log entry, and no side effects.
5. **The adapter must implement a generic PermitSourceAdapter interface.** NSW-specific logic is isolated in the NSWPlanningPortalAdapter. The state transition service, event log, and resolver are jurisdiction-agnostic.
6. **Geographic scope is limited to Central Coast LGA for this milestone.** Do not attempt to connect feeds from other LGAs.

---

## 6. Known Gaps and Edge Cases

### 6.1 Gaps (To Be Resolved Post-Milestone 7)

| Gap | Description | Resolution Path |
|---|---|---|
| Cell lifecycle completion | What transitions a cell from `change_confirmed` back to `stable` after re-ingestion of structural data? | Define a `re_ingested` event type or a `change_confirmed → stable` transition triggered by successful structural data refresh. Defer to Pillar 3/4 integration. |
| Multi-jurisdiction scaling | Adding QLD, VIC, or international jurisdictions requires new adapters with different field schemas, permit types, and API structures. | The PermitSourceAdapter interface is designed for this. Each jurisdiction is a new adapter implementation. No changes to the state transition service. |
| Push notification support | If the NSW Planning Portal adds webhook support, the adapter layer should be extended to receive push events alongside pull polling. | Design the adapter interface to support both. Pull is the baseline; push is an optimisation. |
| Conflicting permit events | How to handle a cell that receives `change_expected` while already in `change_in_progress` from a different permit? | Log as anomaly, do not apply the conflicting transition, escalate to PM report. This requires further analysis of real-world multi-permit scenarios. |

### 6.2 Edge Cases (Documented, Not Resolved in MVP)

The four-status state machine is a deliberate simplification of real-world building lifecycle complexity. The following edge cases are known and accepted for the MVP. The event-sourced model (Section 2.9) preserves the full history, so a more nuanced state model can be derived from the event log in future without re-ingesting any data.

| Edge Case | What Happens | Why This Is Acceptable |
|---|---|---|
| **Partial occupancy** — A mixed-use building receives an interim OC for ground floor retail while upper floors are still fitting out. Two separate OC applications exist against the same lot. | The first OC triggers `change_confirmed`. The second OC, when issued, would need to transition a cell already in `change_confirmed`. Under the current model, the second event is logged but produces no additional state change (idempotent — cell is already `change_confirmed`). | The event log captures both OC events with their dates. The cell reflects the earliest completion. A future refinement could introduce sub-cell or per-tenancy state tracking, but the structural geometry change (the building exists) is captured correctly by the first transition. |
| **Long DA-to-construction lag** — A DA is approved in 2024 but construction does not start until 2027. The cell sits in `change_expected` for three years. | The cell status is technically correct — a change is expected. Downstream consumers see `change_expected` and may assume it is imminent. | The event log records the DA lodgement date, so consumers can query how long ago the DA was lodged and distinguish a recent DA from a stale one. A future enhancement could add a `da_age_days` derived field or a `change_expected_stale` status for DAs older than a configurable threshold. |
| **Construction without permits** — An owner begins building without a CC. The council retroactively issues certificates. | The state machine shows `stable → change_expected → change_confirmed`, skipping `change_in_progress` entirely. The `change_in_progress` state is never recorded. | This reflects the permit record accurately — the council never issued a CC, so Harmony has no evidence of active construction. The event log is honest about what happened. If satellite change detection is added as a future temporal truth source (see Section 7), it would catch the physical construction independently of the permit record. |
| **Permit-reality timing mismatch** — The actual building completion may precede or follow the OC by weeks or months. Retailers may be fitting out before the OC is issued; the OC may be delayed by inspection backlogs. | `valid_from` reflects the certificate date, not the actual physical completion date. There may be a gap between when the building is physically finished and when Harmony records the change. | This is inherent to any permit-based system. The certificate date has legal authority — it is the government's official record that the building is complete. Physical observation could supplement this but introduces trust and verification complexity. For the MVP, legal authority is the correct standard. |

---

## 7. Global Scalability Note

The permit-based temporal trigger model described in this ADR is well-suited to jurisdictions with functioning digital planning systems — Australia, the UK, most of the EU, the US (at county level), Canada (at provincial/municipal level). However, Harmony's ambition is planetary scale, and many jurisdictions do not have digital permit systems, or have significant informal construction that bypasses permits entirely.

This section documents the architectural principle that ensures the temporal trigger layer scales globally without requiring permits as the only input.

### 7.1 Temporal Truth Hierarchy

The architecture supports a hierarchy of temporal truth sources, ranked by reliability. Higher-ranked sources take precedence where available, but lower-ranked sources become the primary input in jurisdictions where higher-ranked sources do not exist.

| Rank | Source Type | Trust Level | Availability | Example |
|---|---|---|---|---|
| 1 | Official permit records | Highest — legal authority | Jurisdictions with digital planning systems (AU, UK, EU, US, CA) | NSW Planning Portal DA/CDC/PCC feeds |
| 2 | Satellite/aerial change detection | Medium — detects physical change, cannot determine intent or status | Global — any location with satellite coverage | Sentinel-2 time series analysis detecting ground disturbance or new rooflines |
| 3 | Crowdsourced reports | Lower — community-contributed, requires trust model | Regions with active mapping communities | OpenStreetMap community edits, field surveys, local contributor reports |
| 4 | AI-inferred change | Variable — depends on model confidence | Future capability | Harmony Knowledge Layer detecting anomalies between structural geometry and recent imagery |

### 7.2 How This Works With the Current Architecture

The cell state machine (Section 2.3) does not change. The four statuses — `stable`, `change_expected`, `change_in_progress`, `change_confirmed` — remain the same. What changes across jurisdictions is *what triggers the transitions*.

In Australia, a DA lodgement triggers `change_expected`. In a jurisdiction without digital permits, a satellite-detected ground disturbance within a cell might trigger the same transition. The state transition service is already agnostic to the source — it processes generic events. The event log already records the source: `"permit_source": "nsw_planning_portal"` in Australia would become `"permit_source": "satellite_change_detection"` in a jurisdiction relying on satellite data.

The `PermitSourceAdapter` interface already supports this. A `SatelliteChangeDetectionAdapter` or a `CrowdsourcedReportAdapter` would implement the same interface and produce the same event format. No changes to the state transition service, event log, resolver, or cell state machine are required.

### 7.3 Design Constraint for Future Adapters

When building adapters for non-permit sources, the following constraints apply:

- **Every event must carry a confidence score.** Permit records have implicit high confidence (they are legal documents). Satellite detections and crowdsourced reports have variable confidence. The event log should record this, and downstream consumers should be able to filter by confidence threshold.
- **Source ranking must be respected.** If a cell has both a permit-based event and a satellite-based event, the permit-based event takes precedence. A satellite detection should not override an official permit record.
- **The temporal truth hierarchy is configurable per jurisdiction.** A jurisdiction profile defines which source types are available and at what rank. Australia's profile uses permits as rank 1. A jurisdiction in Sub-Saharan Africa might use satellite detection as rank 1 and crowdsourced reports as rank 2, with no permit source at all.

### 7.4 Cost Implications at Scale

Polling cost scales linearly with the number of jurisdictions, but remains low in absolute terms:

| Scale | Jurisdictions | Daily API Calls | Estimated Monthly Compute Cost |
|---|---|---|---|
| Central Coast pilot | 1 LGA | ~50 | <$1 |
| National Australia | 6–8 state APIs | ~5,000 | <$50 |
| Developed international (AU + UK + US + CA + EU) | ~50 national/state APIs | ~50,000 | <$500 |
| Global (including satellite detection) | ~200 country-level adapters + satellite pipeline | Variable — satellite processing dominates | $2,000–10,000 (primarily satellite compute, not API polling) |

The financial inflection point is not API polling — it is satellite imagery processing and AI inference at global scale. API polling remains negligible at any scale. The expensive transition is moving from Rank 1 (permits) to Rank 2 (satellite detection) as the primary source for regions without digital planning systems. That cost is dominated by imagery acquisition and change detection compute, not by the temporal trigger layer itself.

The second cost dimension is adapter engineering. Building an adapter for a well-documented API takes 1–3 days of agent time. At 200+ jurisdictions, this becomes a scaling challenge. The long-term solution is an AI-assisted adapter generator — a Pillar 4 capability where the Knowledge Layer reads a new jurisdiction's API documentation and produces an adapter implementation. This is a Phase 2 capability, not an MVP concern.

---

*ADR-016 — Temporal Trigger Architecture — Accepted April 22, 2026*
