# Pillar 1 — Spatial Substrate: PM Brief V1.0

> **Created:** 2026-04-10  
> **Audience:** Mikey (Founder/PM)  
> **Purpose:** Structured overview of Pillar 1 scope, effort, schedule, dependencies, risks, and milestones for sprint planning and cross-pillar coordination.

---

## 1. Pillar Summary

Pillar 1 builds the Identity System — the foundational service that gives every object in Harmony (cells, buildings, parcels, roads, vegetation, infrastructure) a stable, unique identity. Without this, no other pillar can reliably refer to anything.

The system uses layered identity: a permanent canonical ID for machines, a human-friendly alias for people, a deterministic cell key for spatial operations, and semantic labels for AI. The key principle is that canonical IDs never change, even when aliases, names, or geometry evolve.

Stage 1 delivers the Identity Registry as a working local service with a REST API, database, alias resolution, cell key derivation, and sample Central Coast data — enough for Pillar 2 (Data Ingestion) to begin attaching data to cells.

---

## 2. Session Count & Complexity Estimate

| Session | Name | Complexity |
|---------|------|------------|
| 0 | Sign-Off Gate | Low |
| 1 | Database Schema & Persistence | Medium |
| 2 | ID Generation & Cell Key Derivation | **High** |
| 3 | Registry Service (CRUD) | Medium |
| 4 | Alias System | Medium |
| 5 | API Layer | Medium |
| 6 | Sample Data & Cell Integration | Low |
| 7 | End-to-End Integration Test | Medium |
| 8 | Governance & Documentation Close-Out | Low |

**Total: 9 sessions** (1 gate + 8 build/test sessions)

**Complexity Distribution:** 1 High, 4 Medium, 3 Low (plus 1 gate)

---

## 3. Token Estimates

| Session | Token Range |
|---------|-------------|
| 0 — Sign-Off Gate | 5,000 – 10,000 |
| 1 — Database Schema | 30,000 – 50,000 |
| 2 — ID Gen + Cell Key | 50,000 – 80,000 |
| 3 — Registry CRUD | 40,000 – 60,000 |
| 4 — Alias System | 30,000 – 50,000 |
| 5 — API Layer | 40,000 – 60,000 |
| 6 — Sample Data | 15,000 – 25,000 |
| 7 — E2E Test | 25,000 – 40,000 |
| 8 — Governance Close | 15,000 – 25,000 |
| **Overall** | **250,000 – 400,000** |

Session 2 (ID Generation + Cell Key) is the most token-intensive because it involves cryptographic generation, geometry hashing, and deterministic derivation logic with extensive test vectors.

---

## 4. Sprint Allocation (Two-Week Sprints)

Assumes sequential execution with CoWork sessions as the primary build mechanism, 2–3 sessions per sprint depending on complexity.

### Sprint 1 (Weeks 1–2)
- **Session 0** — Mikey sign-off on v0.1.2 (Day 1 target)
- **Session 1** — Database Schema & Persistence Layer
- **Session 2** — ID Generation & Cell Key Derivation

**Sprint 1 Goal:** Database operational, all ID generation logic implemented and tested.

### Sprint 2 (Weeks 3–4)
- **Session 3** — Registry Service (CRUD)
- **Session 4** — Alias System
- **Session 5** — API Layer (begin)

**Sprint 2 Goal:** Core registry service and alias system operational, API endpoints in progress.

### Sprint 3 (Weeks 5–6)
- **Session 5** — API Layer (complete if spilled)
- **Session 6** — Sample Data & Cell Integration
- **Session 7** — End-to-End Integration Test
- **Session 8** — Governance Close-Out

**Sprint 3 Goal:** Pillar 1 Stage 1 complete. All acceptance criteria passed. Pillar 2 unblocked.

**Total Duration:** 3 sprints (6 weeks), with buffer built into Sprint 3 for rework if E2E testing reveals issues.

---

## 5. Dependency Map

### What Pillar 1 Needs From Other Pillars

| Source | Dependency | Urgency | Status |
|--------|-----------|---------|--------|
| Master Spec V1.0 | Gap Register, North Stars, Agent Classes | Resolved | Closed in v0.1.2 |
| Pillar 3 | Framework selection (discrete vs continuous LOD) | Non-blocking | Separate chat; does not gate Pillar 1 |
| External | None | — | Pillar 1 is self-contained for Stage 1 |

**Pillar 1 has no hard external dependencies for Stage 1 execution.** The only gate is Mikey's sign-off.

### What Pillar 1 Delivers To Other Pillars

| Consumer | What They Get | When Available |
|----------|--------------|----------------|
| **Pillar 2 — Data Ingestion** | Canonical ID and cell_key for attaching ingested data to cells; `POST /cells` and `POST /entities` endpoints; reserved `valid_from` field for ingestion timestamps | End of Sprint 3 |
| **Pillar 3 — Rendering** | `GET /resolve/id` for spatial context resolution; reserved dual-fidelity fields (fidelity_coverage, lod_availability, asset_bundle_count); forward-compatibility note for discrete vs continuous LOD | End of Sprint 3 |
| **Pillar 4 — Knowledge Layer** | Reserved temporal versioning fields (valid_from, valid_to, version_of, temporal_status) for Pillar 4 to activate; known_names lookup primitives for semantic search integration | End of Sprint 3 |
| **Pillar 5 — Interaction Layer** | Named-entity resolution primitives (fuzzy lookup, context-filtered lookup, confidence scores); known_names array on all records; ADR-010 composition model defining the LLM ↔ registry boundary | End of Sprint 3 |
| **All Pillars** | Three-layer agent model terminology (ADR-011); identity-schema.md as canonical reference; alias_namespace_rules.md for any alias consumers | End of Sprint 1 (already available) |

---

## 6. Binary Milestones with Success Criteria

Each milestone is pass/fail — no partial credit.

### M1 — Identity Schema Lock ✅ (Complete, pending sign-off)
- [x] identity-schema.md locked at v0.1.2
- [x] Both JSON schemas validate against spec
- [x] All 6 ADRs written and accepted
- [x] ID generation rules documented with test vectors
- [x] Alias namespace rules documented
- [ ] **Mikey sign-off received** ← remaining gate

### M2 — Registry Service (Local)
- [ ] Database DDL executes without error on target DB
- [ ] Migrations run forward cleanly
- [ ] Cell creation returns valid canonical_id and cell_key
- [ ] Entity creation returns valid canonical_id linked to primary cell
- [ ] Canonical ID lookup returns full record with all fields
- [ ] Lifecycle state transitions enforce valid paths only
- [ ] Reserved fields rejected with 403

### M3 — Alias System
- [ ] Alias resolves to canonical_id within correct namespace
- [ ] Namespace collision prevented (partial UNIQUE enforced)
- [ ] Alias lifecycle works: create → retire → grace → reuse
- [ ] Reserved prefixes rejected
- [ ] Ambiguity handling returns correct responses

### M4 — Cell Identity Integration
- [ ] Sample Central Coast cells registered with valid cell_keys
- [ ] Cell_key derivation is deterministic (same geometry → same key)
- [ ] Re-registration returns existing cell_id (idempotent)
- [ ] Sample entities linked to cells with correct references

### M5 — API Layer
- [ ] All four endpoints operational (resolve alias, resolve canonical, register cell, register entity)
- [ ] Named-entity resolution primitives return ranked candidates with confidence
- [ ] API contract tests pass against stage-1 brief Section 5
- [ ] OpenAPI spec generated

### M6 — End-to-End Acceptance
- [ ] Alias → canonical → entity → cell resolution flow completes
- [ ] Cell has BOTH canonical ID and deterministic cell_key
- [ ] Alias change does not break canonical identity
- [ ] Namespace collisions handled correctly
- [ ] Registry acts as single source of truth
- [ ] All 8 acceptance criteria from stage-1 brief Section 9 pass

---

## 7. Risk Flags

### Blockers (must resolve before build)

| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| R1 | **v0.1.2 sign-off delayed** | All build sessions blocked | Mikey to prioritise review; README has "How to Read" guide for efficient review |

### Active Risks (monitor during build)

| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| R2 | **ECEF vs ENU coordinate frame unresolved** | Cell key derivation (Session 2) uses placeholder geometry snapping | Proceed with centroid-only approach for Stage 1; resolve before Pillar 2 ingestion of real geometry |
| R3 | **Spatial indexing scheme (H3 vs custom) unresolved** | Cell key precision may need revision | Current BLAKE3-on-centroid spec is sufficient for Stage 1; flag for Pillar 2 planning |
| R4 | **Session 2 (High complexity) scope creep** | Cryptographic + geospatial logic is the densest session; risk of over-engineering | Enforce MVP scope per stage-1 brief risk table; defer exact metric edge lengths and BLAKE3 replacement to later milestone |
| R5 | **Region code assignment for boundary-spanning cells** | Edge case in cell_key derivation | Use `gbl` fallback for Stage 1; document as known limitation |
| R6 | **Three-layer terminology updates** | Old "Agent N" naming persists across documents | Low urgency; batch update in Session 8; does not block any build work |

### Upstream Risks (from other pillars)

| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| R7 | **Pillar 3 framework decision affects schema** | May require additive schema changes (not breaking) if discrete vs continuous LOD decision changes field requirements | Forward-compatibility note in identity-schema.md §6.2 already reserves dual-fidelity fields; monitor Pillar 3 chat |
| R8 | **Pillar 4 temporal activation may surface schema gaps** | Pillar 4 will activate reserved temporal fields; may discover implementation needs not covered by ADR-009 | ADR-009 explicitly states Pillar 4 should produce its own ADR; early coordination recommended |

---

## 8. Gantt Parameters

| Parameter | Value |
|-----------|-------|
| Start Sprint | Sprint 1 |
| End Sprint | Sprint 3 |
| Total Duration | 6 weeks |
| Critical Path | Yes — Pillar 1 is on the critical path for the entire Harmony project. All other pillars depend on the Identity System. |
| Parallel Tracks | Limited — Sessions 4 (Alias) and parts of Session 5 (API) could partially overlap. Session 8 (docs) can begin incrementally. |
| Hard Gate | Session 0 (sign-off) must complete before any build session starts |
| Buffer | Sprint 3 has built-in slack for rework after E2E testing |
| Float | None on critical path. Any slip in Sessions 1–3 delays everything downstream. |

### Sprint Timeline View

```
Sprint 1  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  [S0: Gate] [S1: DB] [S2: ID Gen]
Sprint 2  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  [S3: CRUD] [S4: Alias] [S5: API]
Sprint 3  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░  [S5/S6: Data] [S7: E2E] [S8: Close] + buffer
```

---

## 9. Next Action

**Mikey:** Review and sign off on the v0.1.2 amendment pack. This is the single action that unblocks everything. Start with the README.md "How to Read This Pack" section — it has a time-based reading guide. The three new ADRs (009, 010, 011) contain the strategic decisions worth the most attention.

---

*End of PM Brief V1.0*
