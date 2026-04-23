# Pillar 1 — Spatial Substrate
## Stage 1 Implementation Brief: Identity System (v0.1.1 — Approved)

> **Status:** Approved — Ready for Execution  
> **Stack:** Claude Chat (strategy) · Claude CoWork (execution) · Claude Code (technical build)  
> **Last Updated:** April 2026  
> **Pillar:** 1 of 5 — Spatial Substrate

---

## 1. Objective

Build the Harmony Identity System (v0.1.1) as a production-ready foundational service that enables:

- Stable canonical identity across spatial objects
- Human-friendly aliasing for usability
- Registry-based resolution across all pillars
- Deterministic spatial linkage via cell keys
- Future compatibility with contract anchoring

This system will serve as the identity backbone for:
- Spatial Substrate
- Data Ingestion Pipeline
- Rendering Interface
- Spatial Knowledge Layer
- Interaction Layer

---

## 2. Core Architecture (Locked)

### Identity Model

Harmony uses layered identity:

| Layer | Purpose | Example |
|---|---|---|
| Canonical ID | System truth | `hc_4fj9k2x7m` |
| Human Alias | Usability | `CC-421` |
| Friendly Name | UX context | `Coastline North Cell` |
| Semantic Labels | AI / context | `High-growth coastal zone` |

---

### Critical Addition (v0.1.1)

Cells MUST include:
- `cell_id` → canonical identity
- `cell_key` → deterministic substrate key

```json
{
  "cell_id": "hc_4fj9k2x7m",
  "cell_key": "hsam:r08:cc:a91f2"
}
```

This ensures:
- Reproducibility
- Debugging clarity
- Deterministic mapping
- Long-term system integrity

---

## 3. System Components to Build

### 3.1 Identity Registry Service
Core system of record.

**Responsibilities:**
- Store all identity records
- Resolve alias → canonical → metadata
- Manage lifecycle states
- Manage cross-references

---

### 3.2 Alias Resolution Service

**Responsibilities:**
- Resolve human alias → canonical ID
- Enforce namespace rules
- Handle ambiguity
- Support alias lifecycle

---

### 3.3 Canonical Resolution API

**Responsibilities:**
- Resolve canonical ID → full record
- Return metadata, relationships, and spatial linkage

---

### 3.4 Identity Generation Module

**Responsibilities:**
- Generate canonical IDs
- Enforce format rules
- Validate uniqueness

---

### 3.5 Cell Key Derivation Module

**Responsibilities:**
- Generate deterministic `cell_key`
- Map geometry → `cell_key`
- Maintain resolution hierarchy

---

### 3.6 Registry Persistence Layer

**Responsibilities:**
- Store identity records
- Support versioning
- Support historical lookup

---

## 4. Required Deliverables

### Schemas
- `identity-schema.md`
- `cell_identity_schema.json`
- `entity_identity_schema.json`

### Database
- `identity_registry_schema.sql`
- Migrations

### Rules & Policies
- `alias_namespace_rules.md`
- `id_generation_rules.md`

### Services
- `identity_registry_service`
- `alias_resolution_service`
- `canonical_lookup_service`

### Specs
- `resolution_service_spec.md`
- `cell_key_derivation_spec.md`

### Data
- `sample-central-coast-records.json`

### Architecture Decisions (ADRs)
- `ADR-001` — Layered identity
- `ADR-004` — `cell_id` vs `cell_key`
- `ADR-008` — Alias namespace model

---

## 5. API Contracts (v1)

### Resolve Alias

```
GET /resolve/alias?alias=CC-421&namespace=au.nsw.central_coast.cells
```

**Response:**
```json
{
  "canonical_id": "hc_4fj9k2x7m"
}
```

---

### Resolve Canonical

```
GET /resolve/id/hc_4fj9k2x7m
```

**Response:**
```json
{
  "canonical_id": "hc_4fj9k2x7m",
  "object_type": "cell",
  "cell_key": "hsam:r08:cc:a91f2",
  "human_alias": "CC-421",
  "friendly_name": "Coastline North Cell",
  "semantic_labels": [],
  "references": {}
}
```

---

### Register Entity

```
POST /entities
```

### Register Cell

```
POST /cells
```

---

## 6. Database Model

### identity_registry

```sql
canonical_id    TEXT PRIMARY KEY,
object_type     TEXT,
object_domain   TEXT,
status          TEXT,
created_at      TIMESTAMP,
updated_at      TIMESTAMP,
schema_version  TEXT
```

### cell_metadata

```sql
cell_id           TEXT PRIMARY KEY,
cell_key          TEXT,
resolution_level  INT,
parent_cell_id    TEXT,
local_frame_id    TEXT
```

### alias_table

```sql
alias             TEXT,
alias_namespace   TEXT,
canonical_id      TEXT,
status            TEXT,
effective_from    TIMESTAMP,
effective_to      TIMESTAMP
```

### entity_table

```sql
entity_id       TEXT PRIMARY KEY,
primary_cell_id TEXT,
metadata        JSONB
```

---

## 7. Claude Agent Execution Plan

### Agent 1 — Architecture Lead
**Output:**
- `identity-schema.md`
- ADRs
- Service contracts

### Agent 2 — Registry Engineer
**Build:**
- DB schema
- Migrations
- Registry service

### Agent 3 — Alias Systems Engineer
**Build:**
- Alias generation rules
- Namespace handling
- Resolution logic

### Agent 4 — Spatial Substrate Engineer
**Build:**
- `cell_key` derivation
- Cell registration logic

### Agent 5 — API Engineer
**Build:**
- REST endpoints
- Service layer
- Integration with registry

### Agent 6 — PM Agent
**Produce:**
- Milestone tracking
- Acceptance validation
- Test scenarios

---

## 8. Stage 1 Milestones

| Milestone | Deliverables |
|---|---|
| 1 — Identity Schema Lock | Schemas, ADRs, ID rules |
| 2 — Registry Service (Local) | Database, CRUD operations, canonical lookup |
| 3 — Alias System | Alias generation, namespace resolution, ambiguity handling |
| 4 — Cell Identity Integration | `cell_id` + `cell_key` linkage, sample Central Coast cells |
| 5 — API Layer | Resolve endpoints, register endpoints |
| 6 — End-to-End Test | Alias → canonical → entity → cell resolution flow |

---

## 9. Acceptance Criteria (Non-Negotiable)

The system is complete when:

- [ ] Alias resolves to canonical ID
- [ ] Canonical ID resolves to full metadata
- [ ] Cell has BOTH canonical ID and deterministic `cell_key`
- [ ] Entity links to primary and secondary cells
- [ ] Alias can change without breaking canonical identity
- [ ] Lifecycle states are enforced
- [ ] Namespace collisions are handled
- [ ] Registry acts as single source of truth

---

## 10. Example End-to-End Record

```json
{
  "canonical_id": "hc_4fj9k2x7m",
  "object_type": "cell",
  "cell_key": "hsam:r08:cc:a91f2",
  "human_alias": "CC-421",
  "friendly_name": "Coastline North Cell",
  "semantic_labels": [
    "High-growth coastal residential zone"
  ],
  "status": "active",
  "references": {
    "entity_ids": ["ent_bld_91af82"]
  }
}
```

---

## 11. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Over-engineering identity | Enforce MVP scope |
| Alias collisions | Namespace model |
| ID instability | Strict immutability rules |
| Missing substrate linkage | Enforce `cell_key` requirement |
| Registry inconsistency | Single source of truth rule |

---

## 12. What This Enables Next

Once Stage 1 is complete, Harmony unlocks:

- **Data ingestion** can attach to cells
- **Rendering** can resolve spatial context
- **Knowledge layer** can attach meaning
- **Interaction layer** can resolve user intent

Without this system, nothing else scales cleanly.

---

## 13. Pinned Principle

> **Canonical IDs are for truth. Aliases are for people. Semantic labels are for intelligence.**

---

## 14. Immediate Next Step

Open the `Pillar 1 — Spatial Substrate` conversation in the Harmony Claude Project and request:

> *"Generate the full implementation pack for the identity registry service, database schema, API endpoints, Claude agent task breakdown, and first working prototype for local environment."*

---

*Next stage: Spatial Substrate → Execution Plan + First Sprint*
