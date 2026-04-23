# Harmony — Master System Specification v0.1

> **Status:** Active  
> **Stack:** Claude Chat (strategy) · Claude CoWork (execution) · Claude Code (technical build)  
> **Last Updated:** April 2026

---

## 1. Project Overview

Harmony is a geographic information system (GIS) platform built on a custom spatial substrate — the **Harmony Cell System** — that converts the planet from raw coordinates into addressable, AI-compatible computational space.

The system is structured into five foundational pillars, each with its own agent, build phase, and milestone set.

---

## 2. Project Pillars

### Pillar 1 — Spatial Substrate

Defines how the planet is computationally addressed.

**Components:**
- Harmony Cell System
- Hierarchical spatial indexing
- Local coordinate frames
- Cell identity system
- Entity-to-cell relationship model

**Purpose:** Convert the world from coordinates into addressable computational space.

---

### Pillar 2 — Data Ingestion Pipeline

Transforms real-world data into Harmony-compatible structures.

**Components:**
- CRS normalisation
- Geometry validation
- Mapping data → cells
- Entity extraction
- Dataset registration

**Purpose:** Make messy real-world data usable inside Harmony.

---

### Pillar 3 — Rendering Interface

Handles visualisation of spatial data.

**Components:**
- Globe client
- Streaming logic
- Layer rendering
- Camera navigation
- Interaction hooks

**Purpose:** Convert spatial data into human-visible experience.

---

### Pillar 4 — Spatial Knowledge Layer

Transforms space into intelligence.

**Components:**
- Entity graph
- Relationships
- State over time
- Analytics
- AI context

**Purpose:** Make space meaningful and queryable.

---

### Pillar 5 — Interaction Layer

Defines how humans and systems interact with space.

**Components:**
- Conversational navigation
- Semantic queries
- UI/UX
- Workflow orchestration

**Purpose:** Move from maps → intent-driven interaction.

---

## 3. Agent Definitions

### Agent 1 — Spatial Architecture Lead

**Owns:**
- Harmony Cell specification
- Identity model
- Hierarchy rules
- System architecture

**Outputs:**
- Architecture docs
- Schema definitions
- ADRs

---

### Agent 2 — Spatial Index Engineer

**Owns:**
- Cell generation engine
- Hierarchical indexing
- Neighbour logic
- Parent/child relationships

**Outputs:**
- Spatial index package
- Registry generator

---

### Agent 3 — Geospatial Pipeline Engineer

**Owns:**
- Data ingestion
- CRS normalisation
- Geometry → cell mapping
- Dataset transformation

**Outputs:**
- Pipelines
- Processed datasets

---

### Agent 4 — Entity Schema Engineer

**Owns:**
- Entity model
- Metadata schema
- Relationships
- State model

**Outputs:**
- Schema definitions
- JSON structures

---

### Agent 5 — Renderer Integration Engineer

**Owns:**
- Cell-based rendering
- Viewport → cell logic
- Layer loading

**Outputs:**
- Globe integration
- Rendering hooks

---

### Agent 6 — PM / QA Agent

**Owns:**
- Milestones
- Progress tracking
- Acceptance criteria
- Risk management

**Outputs:**
- Reports
- Milestone tracking

---

## 4. Technical Specifications

### Harmony Cell System v0.1

#### Cell Definition

```json
{
  "cell_id": "hc_4fj9k2x7m",
  "level": 4,
  "parent_id": "hc_parent",
  "children_ids": [],
  "bbox_wgs84": {},
  "centroid_wgs84": {},
  "local_frame": {
    "origin": [],
    "basis": "ENU"
  },
  "entity_refs": [],
  "dataset_refs": [],
  "state_refs": []
}
```

---

#### Identity System (Layered)

| Layer | Format | Example |
|---|---|---|
| Canonical ID | `hc_[hash]` | `hc_4fj9k2x7m` |
| Human Alias | `CC-[number]` | `CC-421` |
| Friendly Name | Plain text | `Coastline North Cell` |
| Semantic Label | Descriptive | `High-growth residential zone` |
| Entity ID | `ent_[type]_[hash]` | `ent_bld_91af82` |
| Combined Reference | `cell_id::entity_id` | `hc_4fj9k2x7m::ent_bld_91af82` |
| Contract Anchor (Future) | `ca_[type]_[hash]` | `ca_bld_f82m91q1` |

---

## 5. File System Structure

```
harmony/
  apps/
    harmony-globe/
  packages/
    spatial-index/
    entity-model/
    cell-runtime/
  pipelines/
    cell-assignment/
    zoning-central-coast/
  data/
    raw/
    processed/
    cell-packages/
  docs/
    architecture/
    product/
    research/
  agents/
    prompts/
    outputs/
```

---

## 6. Skills & Capabilities

The system must support:

- Hierarchical spatial indexing
- Streaming-first architecture
- Entity-based modelling
- Local coordinate frames
- AI-compatible data structures
- Predictive loading
- Temporal state tracking
- Multi-layer identity system

---

## 7. Build Sequence & Dependencies

### Correct Build Order

| Stage | Pillar | Focus |
|---|---|---|
| 1 | Spatial Substrate | Cells + indexing |
| 2 | Data Ingestion Pipeline | Data → cells |
| 3 | Rendering Interface | Render cells |
| 4 | Spatial Knowledge Layer | Entities + state |
| 5 | Interaction Layer | User + AI navigation |

Each stage is dependent on the completion of the prior stage. Do not begin Stage N+1 until Stage N acceptance criteria are met.

---

## 8. Open Specifications / Unresolved Areas

The following areas are still evolving and require decisions before or during their relevant build stage:

| Area | Open Question |
|---|---|
| Spatial Index Choice | H3 vs custom system |
| Cell Granularity | Optimal sizing across levels |
| Identity Encoding | Token generation method |
| Local Frame Precision | Handling ECEF vs ENU transitions |
| Rendering Evolution | WebGL vs WebGPU future path |
| Gaussian Splat Integration | When/how to integrate |
| Blockchain Layer | Contract anchoring architecture |
| Semantic Layer | How AI labels are generated and stored |

---

## 9. Tool Stack

| Tool | Role |
|---|---|
| Claude Chat | Strategy, architecture decisions, planning |
| Claude CoWork | Execution, task automation, agent orchestration |
| Claude Code | Technical build, code generation, repo management |

---

*This document is the baseline system specification for the Harmony GIS platform. All pillar threads and agent prompts should reference this document as the source of truth.*
