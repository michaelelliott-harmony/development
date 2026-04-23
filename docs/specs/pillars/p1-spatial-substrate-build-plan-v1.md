# Pillar 1 — Spatial Substrate: Build Task Plan V1.0

> **Created:** 2026-04-10  
> **Status:** Ready for Review  
> **Scope:** All remaining work to complete Pillar 1 Stage 1 (Identity System v0.1.1 → Production-Ready)  
> **Source Files Analysed:** 18 (1 stage-1 brief + 17 from v0.1.2 amendment pack)

---

## 1. Current State Assessment

Milestone 1 (Identity Schema Lock) has been substantially completed via the v0.1.2 amendment pack, which produced 15 files covering schemas, six ADRs, governance infrastructure, and PM infrastructure. This pack is **awaiting Mikey's sign-off** — the single blocker before build work can begin on Milestone 2.

Five of the eight gaps identified against the Harmony Master Spec V1.0 have been closed at the schema/governance layer. Two are deferred with clear ownership (Pillar 4 temporal activation, Pillar 5 full NER flow). One (Pillar 3 framework selection) is confirmed as non-blocking for Pillar 1.

---

## 2. Complete Task Register

### Session 0 — Gate: Milestone 1 Sign-Off
**Complexity:** Low  
**Type:** Review / Decision  
**Prerequisite:** None  

| # | Task | Output | Depends On |
|---|------|--------|------------|
| 0.1 | Mikey reviews v0.1.2 amendment pack (15 files) | Written sign-off or change requests | — |
| 0.2 | PM/QA check on v0.1.2 pack completeness | QA confirmation note | 0.1 |
| 0.3 | Resolve any change requests from 0.1/0.2 | Amended files (if needed) | 0.1, 0.2 |

**Human Input Required:**  
- Mikey must review and approve the v0.1.2 pack. This is a **hard gate** — nothing else proceeds until this is done.

**Estimated Tokens:** 5,000–10,000 (review-level, minimal generation)

---

### Session 1 — Database Schema & Persistence Layer
**Complexity:** Medium  
**Type:** Technical Build (Builder Agent 2 — Registry Engineer)  
**Prerequisite:** Session 0 complete (sign-off granted)  

| # | Task | Output | Depends On |
|---|------|--------|------------|
| 1.1 | Translate identity-schema.md and JSON schemas into full DDL | `identity_registry_schema.sql` | 0.3 |
| 1.2 | Create table: `identity_registry` (canonical_id PK, object_type, object_domain, status, created_at, updated_at, schema_version) | DDL in schema file | 1.1 |
| 1.3 | Create table: `cell_metadata` (cell_id PK → FK identity_registry, cell_key UNIQUE, resolution_level, parent_cell_id, local_frame_id) | DDL in schema file | 1.1 |
| 1.4 | Create table: `alias_table` (alias, alias_namespace, canonical_id FK, status, effective_from, effective_to; partial UNIQUE on active) | DDL in schema file | 1.1 |
| 1.5 | Create table: `entity_table` (entity_id PK → FK identity_registry, primary_cell_id FK, metadata JSONB) | DDL in schema file | 1.1 |
| 1.6 | Add reserved temporal columns (valid_from, valid_to, version_of, temporal_status) with write-rejection constraint | DDL amendments | 1.2, 1.3, 1.5 |
| 1.7 | Add reserved dual-fidelity columns on cell_metadata (fidelity_coverage, lod_availability, asset_bundle_count) | DDL amendments | 1.3 |
| 1.8 | Create indexes (cell_key UNIQUE, alias+namespace partial UNIQUE, known_names GIN) | Index definitions | 1.2–1.5 |
| 1.9 | Write migration scripts (v0.0.0 → v0.1.2) | `migrations/` directory | 1.1–1.8 |
| 1.10 | Validate DDL against both JSON schemas programmatically | Validation test script + pass/fail report | 1.9 |

**Human Input Required:** None — all decisions locked in v0.1.2 schemas and ADRs.

**Estimated Tokens:** 30,000–50,000

---

### Session 2 — Identity Generation & Cell Key Derivation
**Complexity:** High  
**Type:** Technical Build (Builder Agent 4 — Spatial Substrate Engineer)  
**Prerequisite:** Session 1 complete  

| # | Task | Output | Depends On |
|---|------|--------|------------|
| 2.1 | Implement canonical ID generator for cells (`hc_` + 9-char Crockford Base32 token from CSPRNG) | `identity_generation_module` | 1.9 |
| 2.2 | Implement canonical ID generator for entities (`ent_<subtype>_` + 6-char token) | Extension to generation module | 2.1 |
| 2.3 | Implement reserved token filtering (exclude offensive/confusing sequences) | Filter list + logic | 2.1 |
| 2.4 | Implement collision detection and retry logic | Collision handler | 2.1, 1.9 |
| 2.5 | Implement `cell_key` derivation: geometry snap → centroid → region lookup → BLAKE3 hash → base32 encode | `cell_key_derivation_module` | 1.9 |
| 2.6 | Implement resolution level encoding (r00–r15) in cell_key | Part of derivation module | 2.5 |
| 2.7 | Implement region code lookup (cc for Central Coast, gbl fallback) | Region code table + lookup | 2.5 |
| 2.8 | Implement idempotency: re-registration of same geometry returns existing cell_id | Idempotency logic | 2.5, 2.1 |
| 2.9 | Write test vectors from id_generation_rules.md | Test suite | 2.1–2.8 |
| 2.10 | Validate all regex patterns (canonical IDs, cell_keys) against rules doc | Pattern validation tests | 2.9 |

**Human Input Required:**
- **Local coordinate frame decision (ECEF vs ENU)** — currently unresolved. Needed for geometry snapping in 2.5. Can proceed with placeholder if deferred, but must be resolved before production.
- **Spatial indexing scheme (H3 vs custom)** — unresolved. Affects cell_key derivation precision. Can proceed with current spec (BLAKE3 on centroid) but final scheme TBD.

**Estimated Tokens:** 50,000–80,000

---

### Session 3 — Identity Registry Service (CRUD)
**Complexity:** Medium  
**Type:** Technical Build (Builder Agent 2 — Registry Engineer)  
**Prerequisite:** Sessions 1 and 2 complete  

| # | Task | Output | Depends On |
|---|------|--------|------------|
| 3.1 | Implement registry service: create cell (validate schema, generate IDs, derive cell_key, persist) | `identity_registry_service` — create cell | 1.9, 2.1, 2.5 |
| 3.2 | Implement registry service: create entity (validate schema, generate ID, link to primary cell, persist) | `identity_registry_service` — create entity | 1.9, 2.2 |
| 3.3 | Implement registry service: read by canonical_id (return full record with metadata, relationships, spatial linkage) | `canonical_lookup_service` | 1.9 |
| 3.4 | Implement lifecycle state transitions (pending → active → deprecated → retired) with enforcement | State machine logic | 3.1, 3.2 |
| 3.5 | Implement cross-reference management (entity ↔ cell links, secondary cells, successor links) | Reference management | 3.1, 3.2 |
| 3.6 | Implement schema version tracking per record | Version tracking | 3.1 |
| 3.7 | Enforce reserved field write-rejection (403 on temporal/fidelity fields until activated) | Guard logic per ADR-009 | 3.1, 3.2 |
| 3.8 | Write unit tests for all CRUD operations | Test suite | 3.1–3.7 |

**Human Input Required:** None.

**Estimated Tokens:** 40,000–60,000

---

### Session 4 — Alias System
**Complexity:** Medium  
**Type:** Technical Build (Builder Agent 3 — Alias Systems Engineer)  
**Prerequisite:** Session 3 complete (registry service operational)  

| # | Task | Output | Depends On |
|---|------|--------|------------|
| 4.1 | Implement alias generation (PREFIX-NUMBER format, per-namespace counter) | `alias_resolution_service` — generation | 3.1 |
| 4.2 | Implement namespace registration and validation (country.state.region.object_class format) | Namespace management | 4.1 |
| 4.3 | Implement alias → canonical resolution with namespace requirement | Resolution logic | 4.1, 4.2, 3.3 |
| 4.4 | Implement alias lifecycle (free → active → retired, 180-day grace period) | Lifecycle management | 4.1 |
| 4.5 | Implement collision prevention (partial UNIQUE constraint enforcement at service level) | Collision handling | 4.1, 4.2 |
| 4.6 | Implement reserved prefix filtering (TEST, DEMO, TMP, SYS) | Prefix filter | 4.1 |
| 4.7 | Implement ambiguity handling (retired alias lookup with query param, unknown alias response) | Edge case handling | 4.3 |
| 4.8 | Implement manual alias assignment (bypass auto-generation) | Manual assignment path | 4.1 |
| 4.9 | Write unit tests covering all resolution behaviours from alias_namespace_rules.md | Test suite | 4.1–4.8 |

**Human Input Required:** None — all rules locked in alias_namespace_rules.md and ADR-008.

**Estimated Tokens:** 30,000–50,000

---

### Session 5 — API Layer
**Complexity:** Medium  
**Type:** Technical Build (Builder Agent 5 — API Engineer)  
**Prerequisite:** Sessions 3 and 4 complete  

| # | Task | Output | Depends On |
|---|------|--------|------------|
| 5.1 | Implement `GET /resolve/alias` — alias + namespace → canonical_id | REST endpoint | 4.3 |
| 5.2 | Implement `GET /resolve/id/{canonical_id}` — canonical → full record | REST endpoint | 3.3 |
| 5.3 | Implement `POST /cells` — register new cell | REST endpoint | 3.1 |
| 5.4 | Implement `POST /entities` — register new entity | REST endpoint | 3.2 |
| 5.5 | Implement named-entity resolution primitives: exact + fuzzy name lookup with confidence scores | REST endpoint (per ADR-010) | 3.3, 4.3 |
| 5.6 | Implement named-entity resolution primitives: context-filtered lookup (given spatial context) | REST endpoint (per ADR-010) | 5.5 |
| 5.7 | Implement API error handling (unknown alias, namespace missing, retired alias, reserved field writes) | Error response layer | 5.1–5.6 |
| 5.8 | Write API contract tests against Section 5 of stage-1 brief | Contract test suite | 5.1–5.7 |
| 5.9 | Generate API documentation (OpenAPI/Swagger spec) | `resolution_service_spec.md` (updated) + OpenAPI YAML | 5.1–5.7 |

**Human Input Required:** None.

**Estimated Tokens:** 40,000–60,000

---

### Session 6 — Sample Data & Cell Identity Integration
**Complexity:** Low  
**Type:** Data Build (Builder Agent 4 — Spatial Substrate Engineer)  
**Prerequisite:** Sessions 3, 4, and 5 complete  

| # | Task | Output | Depends On |
|---|------|--------|------------|
| 6.1 | Create sample Central Coast cell records (multiple resolution levels) | `sample-central-coast-records.json` | 3.1, 2.5 |
| 6.2 | Create sample entity records (bld, prc, rod subtypes minimum) linked to Central Coast cells | Extended sample data | 3.2, 6.1 |
| 6.3 | Create sample alias records across namespaces (au.nsw.central_coast.cells, au.nsw.central_coast.entities) | Extended sample data | 4.1, 6.1, 6.2 |
| 6.4 | Populate known_names arrays for sample records | Extended sample data | 6.1, 6.2 |
| 6.5 | Validate all sample data against JSON schemas | Validation report | 6.1–6.4 |
| 6.6 | Load sample data through API endpoints and verify persistence | Load test report | 5.3, 5.4, 6.1–6.4 |

**Human Input Required:** None — Central Coast is the confirmed test region.

**Estimated Tokens:** 15,000–25,000

---

### Session 7 — End-to-End Integration Test
**Complexity:** Medium  
**Type:** QA / Integration (Builder Agent 6 — PM Agent + all)  
**Prerequisite:** All prior sessions complete  

| # | Task | Output | Depends On |
|---|------|--------|------------|
| 7.1 | Test full flow: Alias → Canonical → Entity → Cell resolution | E2E test script + results | 5.1, 5.2 |
| 7.2 | Test cell_key idempotency: re-register same geometry, confirm same cell_id returned | E2E test | 2.8, 5.3 |
| 7.3 | Test alias lifecycle: create → retire → grace period → reuse | E2E test | 4.4, 5.1 |
| 7.4 | Test lifecycle state enforcement: attempt invalid transitions | E2E test | 3.4 |
| 7.5 | Test reserved field rejection: attempt temporal field writes, expect 403 | E2E test | 3.7 |
| 7.6 | Test namespace collision handling: same alias in different namespaces | E2E test | 4.5, 5.1 |
| 7.7 | Test named-entity resolution primitives: fuzzy lookup, context-filtered lookup | E2E test | 5.5, 5.6 |
| 7.8 | Validate all 8 acceptance criteria from Section 9 of stage-1 brief | Acceptance checklist (pass/fail) | 7.1–7.7 |
| 7.9 | Generate milestone completion report | Session progress report | 7.8 |

**Human Input Required:** None.

**Estimated Tokens:** 25,000–40,000

---

### Session 8 — Governance & Documentation Close-Out
**Complexity:** Low  
**Type:** Documentation (Builder Agent 1 — Architecture Lead)  
**Prerequisite:** Session 7 passes all acceptance criteria  

| # | Task | Output | Depends On |
|---|------|--------|------------|
| 8.1 | Update CHANGELOG.md with all session outputs | Updated CHANGELOG | 7.9 |
| 8.2 | Update pillar-1-master-spec-variations.md with any new variations discovered during build | Updated variations doc | 7.9 |
| 8.3 | Produce `cell_key_derivation_spec.md` (formal specification of implemented algorithm) | New spec file | 2.5 |
| 8.4 | Produce `resolution_service_spec.md` (formal service specification) | New/updated spec file | 5.9 |
| 8.5 | Apply three-layer agent model terminology updates across all documents | Updated files (low urgency, batch) | ADR-011 |
| 8.6 | Final schema version bump if needed | Schema version update | 8.1–8.5 |
| 8.7 | Produce Pillar 1 Stage 1 completion summary for PM Agent | Completion report | 8.1–8.6 |

**Human Input Required:** None.

**Estimated Tokens:** 15,000–25,000

---

## 3. Dependency Map (Task Sequence)

```
Session 0 (Sign-off) ──── HARD GATE
        │
        ▼
Session 1 (Database) ─────────────────────────────┐
        │                                          │
        ▼                                          │
Session 2 (ID Gen + Cell Key) ────────┐            │
        │                             │            │
        ▼                             ▼            │
Session 3 (Registry CRUD) ◄───────────┘            │
        │                                          │
        ├──────────────┐                           │
        ▼              ▼                           │
Session 4 (Alias)   (parallel possible             │
        │            if resources allow)            │
        │              │                           │
        ▼              ▼                           │
Session 5 (API Layer) ◄───────────────────────────┘
        │
        ▼
Session 6 (Sample Data + Integration)
        │
        ▼
Session 7 (End-to-End Test)
        │
        ▼
Session 8 (Governance Close-Out)
```

**Critical Path:** 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

**Parallelisation Opportunities:**
- Sessions 4 (Alias) and parts of Session 5 (API for registry endpoints) could overlap if split across agents.
- Session 8 documentation tasks can begin as individual sessions complete.

---

## 4. Unresolved Decisions Requiring Human Input

| # | Decision | Blocks | Urgency | Recommendation |
|---|----------|--------|---------|----------------|
| D1 | **Sign-off on v0.1.2 amendment pack** | All build sessions (1–8) | **Critical** | Review the README.md "How to Read This Pack" section first. Focus on ADR-009, 010, 011 for strategic decisions. |
| D2 | **Local coordinate frame (ECEF vs ENU)** | Session 2, task 2.5 (geometry snapping) | Medium | Can proceed with placeholder; must resolve before Milestone 4 cell integration with real geometry. |
| D3 | **Spatial indexing scheme (H3 vs custom)** | Session 2, task 2.5 (cell_key precision) | Medium | Current spec (BLAKE3 on centroid) is sufficient for Stage 1. Final scheme affects Pillar 2 ingestion. |
| D4 | **Region code assignment for boundary-spanning cells** | Session 2, task 2.7 | Low | Can defer — use `gbl` fallback for edge cases in Stage 1. |

---

## 5. Session Summary Table

| Session | Name | Complexity | Est. Tokens | Depends On | Key Output |
|---------|------|------------|-------------|------------|------------|
| 0 | Sign-Off Gate | Low | 5K–10K | — | Approval to proceed |
| 1 | Database Schema | Medium | 30K–50K | 0 | SQL DDL, migrations |
| 2 | ID Gen + Cell Key | High | 50K–80K | 1 | Generation modules, derivation logic |
| 3 | Registry CRUD | Medium | 40K–60K | 1, 2 | Core registry service |
| 4 | Alias System | Medium | 30K–50K | 3 | Alias resolution service |
| 5 | API Layer | Medium | 40K–60K | 3, 4 | REST endpoints, API docs |
| 6 | Sample Data | Low | 15K–25K | 3, 4, 5 | Central Coast test records |
| 7 | E2E Test | Medium | 25K–40K | All above | Acceptance validation |
| 8 | Governance Close | Low | 15K–25K | 7 | Final docs, changelog, specs |
| **Total** | | | **250K–400K** | | |

---

*End of Build Plan V1.0*
