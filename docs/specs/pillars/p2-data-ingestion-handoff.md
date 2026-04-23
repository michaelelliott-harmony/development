# HARMONY — Pillar 2 Handoff Brief
## From: Pillar 1 Architecture Chat (Claude Chat)
## To: Pillar 2 — Data Ingestion Pipeline Chat

> **Date:** 2026-04-19
> **Author:** Architecture Lead (Pillar 1 Claude Chat)
> **Purpose:** Complete context transfer for the Pillar 2 chat. This document contains every decision, convention, constraint, and file reference that Pillar 2 needs to build correctly against the Pillar 1 substrate.
> **How to use:** Drop this file into the Pillar 2 Claude Project as a context document. The Pillar 2 chat should read it in full before producing any output.

---

## 1. What Has Been Built — Pillar 1 Is Complete

Pillar 1 (Spatial Substrate) is complete as of April 19, 2026. All six milestones are done, all eight acceptance criteria pass, and the identity substrate is operational with a live HTTP API.

**The headline numbers:**

- 8/8 acceptance criteria pass (formal scorecard in `PILLAR_1_STAGE_1_ACCEPTANCE.md`)
- 157 tests across four test suites (cell-key derivation, alias service, API integration, end-to-end HTTP acceptance)
- 14 ADRs in a single canonical sequence (`ADR_INDEX.md`)
- 12 HTTP endpoints with auto-generated OpenAPI documentation
- 5 sample Central Coast cells and 3 sample entities seeded and verified
- Schema version: v0.1.3

Pillar 2 is the first consumer of everything Pillar 1 built. It will exercise the HTTP contract at scale, validate the idempotency guarantee under real ingestion load, and begin building the data moat with Central Coast NSW datasets.

---

## 2. The Governing Architecture — Non-Negotiable Context

### 2.1 The Three North Stars

These are non-negotiable success criteria from the Harmony Master Specification V1.0. Every decision in every pillar must be evaluated against all three simultaneously. A decision that advances one while closing off another is not valid.

**North Star I — The Seamless World.** Continuous LOD streaming, not tile switching. The rendering experience must be a different category from Google Maps or Google Earth. Pillar 2's relevance: ingested data must support continuous LOD, not discrete tile-level loading.

**North Star II — The GPS-Free Spatial Substrate.** Harmony Cells are machine-readable spatial reference frames for autonomous navigation. Pillar 2's relevance: ingestion must carry dual fidelity — photorealistic for rendering AND sub-metre structural geometry for robotic navigation — within a single cell package.

**North Star III — The Spatial Knowledge Interface.** When a user asks an AI about a place, the world transforms around the answer. Pillar 2's relevance: ingested data must be semantically rich enough to support AI-generated spatial intelligence in Pillar 4.

### 2.2 The Five-Pillar Architecture

| Pillar | Name | Status |
|---|---|---|
| 1 | Spatial Substrate | **Complete** |
| 2 | Data Ingestion Pipeline | **Next — you are here** |
| 3 | Rendering Interface | Not started (independent research in separate chat) |
| 4 | Spatial Knowledge Layer | Not started |
| 5 | Interaction Layer | Not started |

### 2.3 The V1.0 Pillar 2 Obligation

From the master spec:

> "All external data is translated into Harmony semantics at ingestion. Raw coordinates, GIS layers, and external datasets never reach the rendering or intelligence layers in their original form."

> "The ingestion schema must carry a dual fidelity standard as a first-class requirement. Human-scale rendering requires photorealistic texture and geometry. Machine-scale navigation requires structural geometry at sub-metre fidelity — precise building footprints, traversable corridors, obstacle maps, vertical clearance for UAV paths. Both fidelity standards must be carried within a single Harmony Cell package."

### 2.4 Build Methodology

**Sequential pillar execution with independent prep work.** One pillar is "active" at any time — that's where integration work, decisions, and Mikey's attention live. Other pillars do only independent work (research, scaffolding, schema drafts) that doesn't require the active pillar's output.

**Agent-led development.** Claude Chat for strategy and architecture. Claude CoWork for execution and task orchestration. Claude Code for technical implementation and testing. Human (Mikey) makes final decisions at architecture gates.

**Two-week sprint cadence.** Each pillar progresses in two-week sprints with clear deliverables per sprint.

---

## 3. Decisions Made in Pillar 1 That Directly Affect Pillar 2

These are binding. They were decided in the Pillar 1 architecture chat and must not be re-opened without Mikey's explicit approval.

### 3.1 Entity Registration Is NOT Idempotent (ADR-011)

Cell registration is idempotent — registering the same geometry twice returns the same `cell_id`. Entity registration is deliberately NOT idempotent — registering the same building twice produces two different `entity_id` values.

**This means entity deduplication is Pillar 2's responsibility.** The identity layer does not attempt to detect duplicate entities because natural keys across ingestion sources are messy and heterogeneous. Pillar 2 must design its own deduplication strategy using source-system identifiers, spatial proximity, or content hashing.

This was explicitly confirmed by Mikey during Gate 3 closure.

### 3.2 Dual Fidelity Fields Are Reserved in the Schema (v0.1.2)

The following fields exist on cell records but are **reserved** — the registry rejects writes to them until Pillar 2 formally activates them:

- `fidelity_coverage` (object, nullable) — describes what fidelity types are available
- `lod_availability` (object, nullable) — maps LOD levels to availability status
- `asset_bundle_count` (integer, default 0) — denormalised count
- `references.asset_bundles` (array, default empty) — typed references to asset bundles

Pillar 2 owns the activation of these fields. When Pillar 2 is ready to populate them, it must:

1. Define the internal structure of `fidelity_coverage` and `lod_availability`
2. Define the asset bundle reference format
3. Produce an ADR (next available number is ADR-015) documenting the activation
4. Coordinate with Pillar 1's registry to lift the `403 Reserved` enforcement

### 3.3 Temporal Versioning Fields Are Reserved (ADR-007)

The cell and entity schemas carry four reserved temporal fields: `valid_from`, `valid_to`, `version_of`, `temporal_status`. These are owned by Pillar 4, not Pillar 2. However, Pillar 2 ingestion should populate `valid_from` for time-stamped data sources where the temporal validity is known at ingestion time.

### 3.4 The Cell Key Is Deterministic and Enables Distributed Ingestion

The `derive_cell_key()` function operates without database access. Ingestion pipelines can compute cell keys for incoming data independently, then register idempotently via the API. This means Pillar 2 can run distributed ingestion workers that each compute cell metadata locally and POST to the registry without coordination between workers.

### 3.5 The Alias Namespace Format Is Locked (ADR-006)

Namespaces are hierarchical, dotted, lowercase, country-first:

```
au.nsw.central_coast.cells
au.nsw.central_coast.entities
au.nsw.central_coast.parcels
```

NOT `cc.au.nsw.cc` or any other format. The regex is `^[a-z]{2,4}(\.[a-z0-9_]{2,32}){2,5}$`. Pillar 2 must register namespaces for its ingested data sources before binding aliases.

### 3.6 The Adjacency Model Is Precomputed (ADR-005)

When Pillar 2 registers cells, the registry service computes adjacency automatically. Pillar 2 does not need to compute or provide adjacency data — just provide the cell geometry and resolution level. The registry handles the rest.

### 3.7 12 Resolution Levels, 16-Child Subdivision

The Harmony Cell System has 12 levels (r00–r11). Each level subdivides into a 4×4 grid of 16 children. This is locked. Pillar 2 must map incoming data to the appropriate resolution level(s) within this hierarchy.

| Level | Approx. cell edge | Typical use |
|---|---|---|
| r00 | Continental | Cube face |
| r04 | ~250 km | Country/state |
| r06 | ~15 km | District |
| r08 | ~1 km | Suburb/block |
| r10 | ~60 m | Parcel/building |
| r11 | ~15 m | Room/sub-parcel |

### 3.8 The Gnomonic Cube Projection Has ~2.3× Distortion

Cells at cube face corners are up to ~2.3× larger than cells at face centres at the same resolution level. Every cell stores its actual computed geometry (`edge_length_m`, `area_m2`, `distortion_factor`). Pillar 2 should never infer cell size from resolution level alone — always use the stored values.

---

## 4. The Three-Layer Agent Model (ADR-009)

This is a terminology decision that applies project-wide. Three categories of "agent" exist in Harmony, and the terms are non-overlapping:

| Layer | Name | When | Who they serve |
|---|---|---|---|
| **Builder Agents** | Backend dev workers | Build phase | The project |
| **Runtime Agent Classes (I/II/III)** | Spatial infrastructure agents | Production | Other agents and systems |
| **Digital Team Members** | Customer-facing agents | Production | End users |

All CoWork and Code sessions use "Builder Agent" terminology. The agents inside the deployed Harmony system (Spatial Agent, Navigation Agent, Conversational Spatial Agent) are "Runtime Agent Classes." The agents that real users talk to are "Digital Team Members."

This was established in ADR-009 (originally ADR-011, renumbered in the v0.1.3 canonical merge).

---

## 5. The PM Infrastructure

Every meaningful CoWork or Code session must produce a session progress report. The PM infrastructure was established in the v0.1.2 amendment and is now operational.

### 5.1 Session Reports

At the end of every session, the active Builder Agent writes a report to `PM/sessions/` following the template at `PM/templates/session-progress-report-template.md`. The filename format is `YYYY-MM-DD-pillar-N-short-description.md`.

### 5.2 The PM Agent

A Project Manager Agent runs daily, reads session reports, and produces a briefing for Mikey. The PM Agent brief is at `PM/agents/project-manager-agent-brief.md`. The PM Agent has opinion scope on schedule, scope drift, blockers, and Claude ecosystem recommendations. It does NOT have opinion scope on technical architecture.

### 5.3 The Dashboard Update Protocol

There is a dashboard update protocol (`HARMONY_DASHBOARD_UPDATE_PROTOCOL_V1.0.docx` in the project context) that specifies how to report milestone progress back to the architecture chat. At the end of sessions where milestones advance, produce update lines in the specified format.

---

## 6. The ADR System

### 6.1 Canonical Numbering

All ADRs across all tracks (architecture and build) share a single numbering sequence. The current state is:

| # | Title | Status |
|---|---|---|
| ADR-001 | Layered Identity Model | Accepted (federation note v0.1.2) |
| ADR-002 | Cell Geometry — Gnomonic Cube Projection | To be extracted from spec |
| ADR-003 | Cell Key Derivation Architecture | Accepted |
| ADR-004 | cell_id vs cell_key Dual-Identifier Principle | Accepted |
| ADR-005 | Cell Adjacency Model | Accepted |
| ADR-006 | Alias Namespace Model | Accepted |
| ADR-007 | Temporal Versioning | Accepted (reserved at schema layer) |
| ADR-008 | Named-Entity Resolution Boundary | Accepted |
| ADR-009 | Three-Layer Agent Model | Accepted |
| ADR-010 | Spatial Geometry Schema Extension (v0.1.3) | Accepted |
| ADR-011 | Gate 3 Closure — Identity Generation Order | Accepted |
| ADR-012 | Alias Generation Architecture | Accepted |
| ADR-013 | API Layer Architecture | Accepted |
| ADR-014 | Pillar 1 Stage 1 Completion | Accepted |

**The next available ADR number is ADR-015.** Pillar 2 should use this for its first architectural decision.

### 6.2 ADR Governance

New ADRs must:
1. Use the next available number from `ADR_INDEX.md`
2. Follow the format established by the existing ADRs (Context, Decision, Consequences, Alternatives Considered)
3. Be added to `ADR_INDEX.md` when created
4. Reference the canonical numbers, never the old parallel-track numbers

The old parallel numbering (where the architecture track and build track each had their own ADR-004) was resolved in v0.1.3. It must not recur. One sequence, project-wide.

---

## 7. The Pillar 1 HTTP API — Pillar 2's Primary Interface

Pillar 2 consumes Pillar 1 through the REST API. The full OpenAPI spec is auto-generated at `/docs` and `/openapi.json` when the server is running. Here are the endpoints Pillar 2 will use most:

### Cell Registration (Primary Pillar 2 operation)

```
POST /cells
```
Accepts a JSON body with cell geometry and metadata. Returns the full cell record including computed `canonical_id`, `cell_key`, adjacency, and geometry. Idempotent on `cell_key` — re-posting the same geometry returns the existing record with `200 OK`.

### Entity Registration

```
POST /entities
```
Registers a real-world feature (building, parcel, road, etc.) anchored to one or more cells. Returns `201 Created`. NOT idempotent — Pillar 2 must handle deduplication before calling this.

### Alias Management

```
POST /namespaces — register a namespace for ingested data
POST /aliases — bind an alias to a canonical_id
GET /resolve/alias?alias=...&namespace=... — resolve (namespace required, always)
```

### Resolution

```
GET /resolve/cell/{canonical_id}
GET /resolve/cell-key/{cell_key}
GET /resolve/entity/{canonical_id}
```

### Adjacency (relevant for spatial joins)

```
GET /cells/{cell_key}/adjacency?depth=1|2|3
```

### Environment

```
HARMONY_DB_URL="postgresql://localhost:5432/harmony_dev"
```

Server starts with: `uvicorn harmony.services.api.main:app --host 127.0.0.1 --port 8000`

---

## 8. Files Pillar 2 Should Have in Its Project Context

The following files should be uploaded to the Pillar 2 Claude Project. They are the minimum set needed for Pillar 2 to build correctly.

### From the Pillar 1 architecture track (this chat's outputs)

| File | Purpose |
|---|---|
| `identity-schema.md` (v0.1.3) | The locked identity schema — what cell and entity records look like |
| `id_generation_rules.md` (v0.1.3) | How IDs and cell keys are generated |
| `alias_namespace_rules.md` | The locked alias and namespace spec |
| `ADR_INDEX.md` | Canonical ADR sequence — use this for numbering |
| `CHANGELOG.md` | Version history — understand what changed and when |
| `pillar-1-master-spec-variations.md` | What Pillar 1 decided that should fold into the master spec |
| `PM/templates/session-progress-report-template.md` | Format for session reports |
| `PM/agents/project-manager-agent-brief.md` | PM Agent role definition |

### From the master spec and business plan

| File | Purpose |
|---|---|
| `master-spec-v1.0.1.md` | The governing master specification |
| `harmony-agent-analysis.md` | Agent capability scores and build timeline |
| `harmony_gis_business_plan.docx` | Business plan with Pillar 2 cost estimates |
| `HARMONY_PILLAR_DEPTH_PROBE_PROMPT.md` | Prompt for running the depth-probe on Pillar 2 |
| `HARMONY_PILLAR_BRIEF_TEMPLATE.md` | Template for producing the Pillar 2 brief and PM brief |
| `HARMONY_DASHBOARD_UPDATE_PROTOCOL_V1.0.docx` | How to report progress back |

### From the Pillar 1 build (CoWork/Code outputs)

| File | Purpose |
|---|---|
| `PILLAR_1_STAGE_1_ACCEPTANCE.md` | Proof that Pillar 1 is done |
| `SESSION_06_SUMMARY.md` | Final session summary — what Pillar 2 inherits |
| `harmony/services/api/main.py` | The API application Pillar 2 will POST to |
| `harmony/data/sample-central-coast-records.json` | Sample data — the acceptance test dataset |

### This handoff brief

| File | Purpose |
|---|---|
| This file | Complete context transfer — read first |

---

## 9. What Pillar 2 Must Deliver (from the original analysis)

The Agent Capability & ROI Analysis scores Pillar 2 at **830/1000 (83% agent-completable)**. Estimated timeline: **4–5 weeks agent-led** (vs 3–4 months human-led).

### Core deliverables (from the analysis and master spec)

1. **CRS normalisation pipeline** — all input formats → WGS84
2. **Geometry validation suite** — topology checks, self-intersection detection
3. **Geometry → cell mapping engine** — map incoming geometry to Harmony Cells at the appropriate resolution level(s)
4. **Entity extraction scripts** — buildings, parcels, roads from raw GIS layers
5. **Dataset registration service** — catalogue incoming datasets with provenance
6. **Pipeline orchestration** — job queuing, error handling, retry logic
7. **Central Coast pilot pipeline** — real zoning/cadastral data through the full stack

### Key tools and libraries identified

- GDAL / OGR — industry standard geospatial transformation
- Shapely — geometry operations
- Fiona — file I/O for spatial formats
- PyProj — CRS transformation
- GeoPandas — spatial dataframes
- DuckDB — analytical queries during pipeline processing
- PostGIS — spatial query support in the database
- Apache Airflow or Prefect — pipeline orchestration (agent-selectable)

### Human decision gates for Pillar 2

- **Dataset sourcing** — which actual Central Coast NSW datasets to ingest first
- **Entity extraction thresholds** — what counts as a building vs a structure
- **Domain knowledge** for Australian cadastral/zoning data structure
- **CRS edge cases** — datum shifts, historical coordinate systems

---

## 10. The V1.0 Gap Register — What Pillar 2 Touches

| Gap | Status | Pillar 2 Relevance |
|---|---|---|
| Gap 1 — Rendering (continuous LOD) | Open, separate chat | Pillar 2 must prepare data in a format compatible with continuous LOD, not tile-based loading |
| Gap 2 — Machine query latency | Reserved, pre-Pillar-4 | Not directly Pillar 2's concern |
| Gap 3 — Temporal versioning | Closed at schema layer | Pillar 2 should populate `valid_from` where source data includes timestamps |
| Gap 4 — Federation | Preserved | Not Pillar 2's concern |
| Gap 5 — Named-entity resolution | Closed at substrate layer | Pillar 2 should populate `known_names` where source data includes place names |
| Gap 6 — Commercial model | Deferred | Not Pillar 2's concern |

---

## 11. The Pillar 1 Master Spec Variations — What Pillar 2 Should Know

Pillar 1 produced a comprehensive variations file (`pillar-1-master-spec-variations.md`) documenting everything it decided that should fold into the next master spec revision. Pillar 2 should produce its own equivalent file: `pillar-2-master-spec-variations.md`, following the same structure (Reading B — comprehensive, not just deltas).

When all five pillars have produced their variations files, the next master spec revision can be assembled by merging them.

---

## 12. Recommended First Steps for Pillar 2

1. **Run the Pillar 2 depth-probe** using `HARMONY_PILLAR_DEPTH_PROBE_PROMPT.md` with Pillar 2 context filled in. This produces the detailed Pillar Brief and PM Brief.

2. **Source the Central Coast datasets.** The pilot region is Central Coast NSW, Australia (approximate centre: -33.4, 151.3). The primary datasets to target are cadastral boundaries, zoning layers, building footprints, and road network data from NSW government open data sources.

3. **Design the geometry → cell mapping algorithm.** This is the core novel component of Pillar 2 — mapping arbitrary input geometry (polygons, lines, points) to the correct Harmony Cell(s) at the appropriate resolution level. The cell key derivation module (`derive.py`) provides the foundation, but Pillar 2 needs to handle geometry that spans multiple cells, geometry at different scales, and geometry that doesn't align cleanly with the cell grid.

4. **Design the entity deduplication strategy.** This is the Pillar 2 responsibility that Pillar 1 explicitly pushed downstream. Decide early how duplicate entities will be detected and resolved — before ingestion runs at scale and creates a dedup backlog.

5. **Activate the dual fidelity fields.** Produce ADR-015 defining the internal structure of `fidelity_coverage`, `lod_availability`, and the asset bundle reference format. This unlocks the reserved schema fields and allows Pillar 2 to start populating them.

---

## 13. Pilot Region and Contacts

**Central Coast NSW, Australia** is the initial seeding region for the Harmony Cell System. All development targets this region first.

**Key contact:** Tom O'Gorman, Change Property — primary pilot partner for the Reagent application layer.

---

## 14. One Final Note

Pillar 1 was built in approximately two weeks across eight sessions with 157 passing tests and 14 ADRs. The methodology that made this work was: precise briefs with locked source-of-truth references, session summaries fed back to the architecture chat for cross-track review, structured PM reporting, and a discipline of resolving ambiguities in writing (via ADRs) rather than letting them accumulate as implicit decisions in code.

Pillar 2 should follow the same methodology. Every session should reference its source documents explicitly. Every decision that isn't in the brief should be flagged in the session summary. Every new ADR should use the next number from the canonical sequence. And every session should produce a PM report so Mikey stays in control of the project without drowning in it.

The spatial substrate is built. Now build the pipeline that fills it with the real world.

---

*Pillar 2 Handoff Brief — from the Pillar 1 Architecture Chat — April 2026*
