# HARMONY — Spatial Operating System
## Master Specification | Version 1.0.1
**Status:** Active  
**Supersedes:** V1.0 — Master Specification  
**Date:** April 2026  
**Owner:** Mikey (Founder)

---

## Version History

| Version | Date | Summary of Change |
|---------|------|-------------------|
| V0.1 | March 2026 | Spatial Substrate established. Harmony Cell System defined: hierarchical cell structure, HCID identity model, local ENU coordinate frames, entity occupancy principles, Central Coast NSW as pilot region. |
| V1.0 | April 2026 | Three North Stars formalised as governing design criteria. Five-pillar obligations updated. Agent Architecture made explicit with three agent classes. Gap Register introduced. Build sequencing model defined. |
| V1.0.1 | April 2026 | Pillar 1 Milestone 1 decisions incorporated. Harmony Cell System confirmed as committed custom spatial indexing layer (VAR-009). Six-layer identity model formalised (VAR-001). Dual-identifier substrate documented (VAR-002). Bitemporal versioning committed at schema layer (VAR-003). Named-entity resolution boundary established (VAR-004). Federation-compatible identity format confirmed (VAR-005). Three-layer agent model added (VAR-006). Schema field additions v0.1.2 referenced (VAR-007). Gap Register updated — Gaps 3, 4, 5 status changed (VAR-008). |

---

## What Harmony Is

Harmony is a Spatial Operating System — the layer between physical reality and intelligence that the internet forgot to build. Its foundational claim is that every object in the physical world — every parcel, building, zone, street segment, corridor, and geographic feature — deserves a stable, resolvable, machine-readable identity that any system on Earth can query and trust.

The one-line definition: **Harmony is the Universal Spatial Address Protocol for the physical world.**

It is not a GIS viewer. It is not a mapping platform. It is the canonical spatial substrate upon which all applications that need to reason about physical space — human or machine — can be built.

The first commercial application layer is **Reagent** (RE + AGENT), an AI-powered platform targeting independent real estate agencies. Reagent is the proof that the protocol has commercial gravity. The real estate agent sees leads and listings. Underneath, they are interacting with a spatial operating system.

---

## The Three North Stars

These are non-negotiable success criteria. Every architectural decision, every schema choice, and every deferred feature must be evaluated against all three simultaneously. A decision that advances one north star while closing off another is not a valid decision.

---

### North Star I — The Seamless World

Every existing mapping and GIS platform inherits the tile-and-polygon model of paper cartography. The world is divided into discrete chunks loaded at discrete resolutions. The seams, polygon pop-in, loading delays, and geometric distortion that every Google Maps or Google Earth user has experienced are not implementation failures — they are structural consequences of that underlying model.

**The first north star is the elimination of this experience entirely.** Any user who has spent time with existing mapping platforms must, on first encounter with Harmony's rendering layer, have an unambiguous recognition that this is a different category of experience. A seamless descent from orbital view to street level, with geometry that resolves continuously and without visible boundaries, rendered in real time at whatever resolution the viewer demands.

The Harmony Cell System's hierarchical structure and local coordinate frames are the correct architectural foundation for this. The rendering layer must honour it.

---

### North Star II — The GPS-Free Spatial Substrate

GPS is a fragile and increasingly insufficient positioning system. It is unreliable indoors, trivially jammed or spoofed, and unsuitable as the sole positioning reference for the coming generation of autonomous systems — drones, autonomous vehicles, UAVs, and humanoid robots navigating complex environments in real time.

The solution converging across all major robotics programmes is simultaneous localisation and mapping (SLAM). The structural problem is that every robot builds its own private map. There is no shared spatial substrate, no canonical record against which any machine can localise with confidence.

**The second north star is that Harmony becomes that canonical substrate.** A Harmony Cell is not merely a rendering unit. It is a machine-readable spatial reference frame — a stable, authoritative, continuously updated description of what exists at a given location at sub-metre fidelity, queryable at the speed that autonomous navigation decisions require. A drone navigating via Harmony does not need GPS. It needs a Harmony Cell query and a confidence score.

---

### North Star III — The Spatial Knowledge Interface

The conversational interface is the dominant paradigm for AI interaction today, and it is structurally impoverished: it presents knowledge as a sequence of words on a flat screen, stripped of the spatial and experiential context in which that knowledge lives.

**The third north star changes this permanently.** When a user asks an AI system about a place, the correct response is not a paragraph. The world should transform around the answer. The conversational interface gives way to a spatial one: the globe appears, the camera moves toward the subject of the question, and the knowledge unfolds as the user travels through Harmony toward the place being described. The text does not stop. The spatial experience does not replace the knowledge — it becomes the physical context in which the knowledge lands and is remembered.

This is the moment that changes what people believe AI can do. It requires three capabilities operating simultaneously: a spatial substrate with continuous global coverage, a real-time semantic pipeline that extracts spatially meaningful entities from AI-generated responses, and a rendering engine capable of transitioning from conversational to spatial experience without breaking the continuity of the interaction. Harmony is the only platform positioned to deliver all three from a single architecture.

---

## The Five-Pillar Architecture

The five-pillar structure is unchanged from V0.1. Each pillar now carries a defined obligation relative to the three north stars.

| Pillar | Name | North Stars Served | Primary Obligation |
|--------|------|-------------------|-------------------|
| I | Spatial Substrate | I, II | Hierarchical spatial identity, local frames, and entity model enabling seamless rendering and machine-speed queries |
| II | Data Ingestion Pipeline | I, II, III | Ingest at dual fidelity: photorealistic for rendering, sub-metre structural for robotic navigation |
| III | Rendering Interface | I, III | Continuous LOD streaming, no tile switching, cinematic spatial transitions for the Knowledge Interface |
| IV | Spatial Knowledge Layer | II, III | Serve spatial intelligence to humans and machines; expose query model fast enough for real-time navigation |
| V | Interaction Layer | III | The Spatial Knowledge Interface — the surface where conversational AI and spatial reality become a single experience |

---

### Pillar I — Spatial Substrate (Harmony Cell System)

The Harmony Cell System is the committed custom spatial indexing layer for the project. Existing open-source solutions (Uber H3, Google S2) were evaluated and set aside — they are general-purpose hexagonal or quadrilateral tiling systems designed for analytics and proximity queries, not for the requirements Harmony places on its substrate: seamless continuous-LOD rendering (North Star I), machine-speed spatial reference frames for autonomous navigation (North Star II), and stable entity-bearing identity that supports temporal versioning and named-entity resolution. The Harmony Cell System is not a wrapper around an existing library — it is a purpose-built spatial substrate. *[VAR-009]*

The HCID identity model, hierarchical cell structure, cell_key derivation, local ENU coordinate frames, and entity occupancy model are all implementations of this commitment.

#### The Six-Layer Identity Model

The identity system is formally structured as a six-layer model *[VAR-001]*:

| Layer | Name | Purpose | Mutability |
|-------|------|---------|------------|
| 1 | Canonical ID | Immutable opaque identifier — the source of truth | Immutable |
| 2 | Cell Key | Deterministic, derivable substrate key for spatial reproducibility | Immutable (derived) |
| 3 | Human Alias | Namespaced human-friendly address (e.g. CC-421) | Mutable (governed) |
| 4 | Friendly Name | Free-text display name | Mutable |
| 5 | Known Names | Indexed name variants for entity resolution primitives | Mutable (indexed) |
| 6 | Semantic Labels | AI-generated descriptive tags | Mutable (AI-managed) |

The governing principle: **Canonical IDs are for truth. Aliases are for people. Semantic labels are for intelligence.**

#### Dual-Identifier Design

Every Harmony Cell carries two identifiers *[VAR-002]*. The canonical ID (`cell_id`) is an opaque, immutable identifier assigned at creation — it is the permanent address used by all systems. The cell key (`cell_key`) is a deterministic key derivable from the cell's spatial parameters (level, position) — it enables substrate-level operations such as neighbour lookup, parent/child traversal, and spatial joins without requiring a registry round-trip. This dual-identifier design resolves the stability-vs-reproducibility tension inherent in any spatial indexing system.

#### Bitemporal Versioning Commitment

Pillar 1 commits to bitemporal versioning at the schema layer *[VAR-003]*. The schema distinguishes system time (`created_at`/`updated_at`) from valid time (`valid_from`/`valid_to`), and supports version chains via `version_of` and `temporal_status`. Four reserved fields are present in cell and entity schemas. Pillar 4 owns active implementation. See ADR-009.

#### Federation-Compatible Identity

The Identity Registry is the logical single source of truth *[VAR-005]*. The canonical ID format carries no embedded operator, region, or jurisdiction — it is deliberately federation-compatible. The current deployment model is centralised, but the identity format and registry contract support a future federated, multi-issuer model. Federation, when introduced, lives in the deployment topology, not in the identity format. See ADR-001 federation note.

#### Schema Field Reference (v0.1.2)

For the current field-level schema, see the Pillar 1 cell and entity identity schemas (v0.1.2) *[VAR-007]*. Fields are categorised as Active (in use), Reserved (schema-present, awaiting activation by the owning pillar), or Indexed (maintained by one pillar, consumed by another).

**Cell record schema (v0.1.2):**
Active: `canonical_id`, `cell_key`, `human_alias`, `alias_namespace`, `friendly_name`
Reserved/Indexed: `known_names`, `semantic_labels`, `valid_from`, `valid_to`, `version_of`, `temporal_status`, `fidelity_coverage`, `lod_availability`, `asset_bundle_count`, `references.asset_bundles`

**Entity record schema (v0.1.2):**
Active: `canonical_id`, `entity_subtype`, `human_alias`, `alias_namespace`, `friendly_name`, `references.primary_cell_id`, `references.secondary_cell_ids`
Reserved/Indexed: `known_names`, `semantic_labels`, `valid_from`, `valid_to`, `version_of`, `temporal_status`

**V1.0 addition (carried forward):** Every schema and lifecycle decision must be validated against the machine query use case as well as the human rendering case.

**Core principle (from V0.1, restated):** A building is not a coordinate. A building occupies one or more Harmony Cells. Those cells hold the building's geometry, state, and intelligence. This is what makes Harmony a spatial operating system rather than a GIS viewer.

---

### Pillar II — Data Ingestion Pipeline

All external data is translated into Harmony semantics at ingestion. Raw coordinates, GIS layers, and external datasets never reach the rendering or intelligence layers in their original form.

**V1.0 addition:** The ingestion schema must carry a dual fidelity standard as a first-class requirement. Human-scale rendering requires photorealistic texture and geometry. Machine-scale navigation requires structural geometry at sub-metre fidelity — precise building footprints, traversable corridors, obstacle maps, vertical clearance for UAV paths. Both fidelity standards must be carried within a single Harmony Cell package.

---

### Pillar III — Rendering Interface

**V1.0 commitment:** The rendering philosophy is continuous level-of-detail streaming. Tile switching is not the model. The specific technology (Gaussian splatting, photogrammetric mesh streaming, neural radiance field integration) is not locked, but the philosophy is. A rendering layer built on tile switching cannot be evolved into the seamless world experience without a full rebuild.

**V1.0 addition (from North Star III):** The rendering engine must support triggered spatial transitions — the ability to receive a place identity from the Interaction Layer, locate the corresponding Harmony Cells, and begin a cinematic camera movement toward that location within a response time that feels immediate to a user who has just asked a conversational question.

---

### Pillar IV — Spatial Knowledge Layer

The intelligence layer that transforms raw geometry and entity data into queryable, interpretable, machine-actionable spatial understanding.

**V1.0 addition:** The query model must serve both human queries and machine queries as first-class consumers. A provisional machine query latency target must be established before the knowledge layer schema is finalised (see Gap Register, Gap 2). The data model and query interface must accommodate both without architectural compromise.

**V1.0.1 addition:** Temporal versioning is reserved at the substrate layer (Pillar I) and active implementation is owned by Pillar IV *[VAR-003]*. The substrate's bitemporal model (ADR-009) provides the schema foundation; Pillar IV activates the version chain logic, query semantics, and historical state retrieval.

---

### Pillar V — Interaction Layer (Spatial Knowledge Interface)

The Interaction Layer is the Spatial Knowledge Interface. It operates through three components in concert.

The **semantic extraction pipeline** parses LLM output in real time, identifies spatially meaningful entities (places, buildings, routes, geographic features), and resolves them against the Harmony Cell identity registry.

The **triggering protocol** defines the conditions and thresholds that determine when a conversational response should initiate a spatial transition and what form that transition takes.

The **continuity model** is the design principle that the conversational context is not interrupted or replaced by the spatial experience. Both modes of knowing operate simultaneously — the spatial experience serves as the physical context in which the conversational knowledge unfolds.

**V1.0.1 addition — Named-Entity Resolution Boundary:** The Conversational Spatial Agent (Class III) composes full natural-language entity resolution from three sources: Pillar 1's Identity Registry name-lookup primitives (exact match, fuzzy match, known_names index), Pillar 4's semantic search, and Pillar 5's own conversational state and context *[VAR-004]*. The Identity Registry is not responsible for natural-language resolution — it provides the indexed primitives. The boundary is deliberate and documented in ADR-010.

---

## Agent Architecture

### The Three-Layer Agent Model

The Harmony agent model operates across three layers *[VAR-006]*:

**Builder Agents** operate during the build phase — they are the engineering agents (one per pillar) responsible for architecture, schema, and implementation. Builder Agents are temporary; they exist to construct the system.

**Runtime Agent Classes (I, II, III)** are the production infrastructure agents defined below — they operate the spatial substrate, serve navigation queries, and bridge conversational AI with spatial experience.

**Digital Team Members** are the customer-facing agents that interact with end users through the application layer (e.g., Reagent).

This three-layer model is documented in ADR-011.

---

### Runtime Agent Classes

Three runtime agent classes operate within Harmony. They share the same spatial substrate, draw from the same Harmony Cell identity registry, and are governed by the same entity occupancy model. No agent class owns the substrate — each queries it and writes to its state layer within defined permissions.

---

#### Class I — Spatial Agents

Associated with Harmony Cells and their occupying entities. A spatial agent holds read access to a cell's geometry, entity index, state, and relationship references, and can respond to queries that require reasoning rather than simple data retrieval. Spatial agents carry temporal context, respond to state changes, and synthesise information across neighbouring cells.

Spatial agents serve all three north stars: they carry LOD context for seamless rendering, provide navigation context for autonomous machines, and provide factual and historical grounding for the Spatial Knowledge Interface.

---

#### Class II — Navigation Agents

Machine-facing intelligence units designed to serve autonomous systems localising and routing in real time. A navigation agent operates on a sliding window of Harmony Cells centred on a moving entity and maintains a continuously updated model of traversable space, known obstacles, confidence-weighted geometry, and neighbouring cell states.

The distinguishing design principle is **latency**. Navigation agents must operate at machine timescales — serving updated spatial context within the response window that an autonomous navigation decision requires. This implies a different caching model, query interface, and state update frequency than Spatial Agents, even though both draw from the same substrate.

---

#### Class III — Conversational Spatial Agents

Sit at the boundary between the Interaction Layer and the Spatial Knowledge Layer. Their function is threefold: parse LLM semantic output to identify spatial entities, query the Harmony Cell registry to resolve those entities to stable spatial addresses, and signal the rendering engine to initiate a spatial transition.

The conversational spatial agent does not replace the LLM. It augments its output with spatial grounding. **The LLM provides the knowledge. The conversational spatial agent provides the address. The rendering engine provides the experience.**

Class III agents are the primary consumers of the Identity Registry's name-lookup primitives (see ADR-010) *[VAR-004]*.

---

## Build Sequencing

The three north stars are not competing priorities. They occupy different pillars and draw from the same foundation. Pursuing them in parallel is architecturally correct.

**The single rule:** Build one foundation. Design it to carry all three futures from day one. Do not begin building the rendering surface, the navigation query model, or the conversational spatial pipeline until the Cell System has proven itself with real data in the Central Coast NSW pilot region. Once it has, all three tracks open simultaneously.

The risk to manage is attentional, not architectural. Hold all three north stars visible in every substrate decision, but assign a single primary track to each development phase.

---

## Gap Register — V1.0.1

### Resolve Before Build Proceeds

**Gap 1 — Rendering Philosophy Commitment**  
The rendering layer must formally commit to continuous LOD streaming rather than tile switching. The specific technology is not locked, but the philosophy must be. A tile-based rendering layer cannot be evolved into the seamless world experience without a full rebuild.  
*Status: Open — unchanged from V1.0.*

**Gap 2 — Machine Query Latency Specification**  
A provisional latency target for machine-speed spatial queries must be established before the Spatial Knowledge Layer schema is finalised. Without a target, the data model and caching architecture cannot be correctly designed.  
*Status: Open — unchanged from V1.0.*

**Gap 3 — Temporal Memory Design Intent**  
~~The Spatial Knowledge Interface depends on historically grounded spatial identity. Cell schemas and HCID structures must be confirmed as capable of supporting temporal versioning without breaking changes before ingestion begins at scale.~~  
*Status: Closed at substrate layer — bitemporal schema confirmed. Four reserved fields (valid_from, valid_to, version_of, temporal_status) present in cell and entity schemas. Awaiting Pillar 4 activation. See ADR-009.* *[VAR-003, VAR-008]*

### Defer With Documentation

**Gap 4 — Sovereignty and Trust Architecture**  
~~Whether Harmony pursues a decentralised or federated truth protocol versus a centralised custodian model is strategically significant but does not block the Central Coast pilot. Formally deferred. Note: the identity model must not be designed in a way that forecloses the federated option.~~  
*Status: Preserved — federation not foreclosed. The canonical ID format is confirmed federation-compatible. Identity carries no embedded operator or jurisdiction. Formal federation architecture deferred. See ADR-001 federation note.* *[VAR-005, VAR-008]*

**Gap 5 — LLM Integration Protocol**  
~~The conversational spatial agent's integration protocol with a connected LLM can be deferred until Pillar V development begins. The Cell identity registry must support named-entity resolution from the outset.~~  
*Status: Closed at substrate layer — Identity Registry name-lookup primitives delivered (exact match, fuzzy match, known_names index, confidence-scored candidates, context-filtered lookup). Full natural-language resolution awaits Pillar 5 activation. See ADR-010.* *[VAR-004, VAR-008]*

**Gap 6 — Commercial Model for the Machine Substrate**  
The business model for the GPS-free navigation layer (licensing, API access, robotics partnerships) is not yet specified. Deferred, but must be scoped before any external capital conversations that extend beyond the real estate vertical.  
*Status: Open — unchanged from V1.0.*

---

## Open Specifications / Unresolved Areas

The following areas are still evolving and require decisions before or during their relevant build stage:

| Area | Status |
|---|---|
| Spatial Index Choice | **RESOLVED** — The Harmony Cell System is the committed custom spatial indexing layer. H3, S2, and other existing open-source solutions were evaluated and set aside. The Harmony Cell System provides purpose-built hierarchical indexing, deterministic cell key derivation, local coordinate frame attachment, and entity occupancy semantics that no general-purpose library offers. *[VAR-009]* |
| Cell Granularity | Open — Optimal sizing across levels. Metric edge lengths per resolution level to be determined in a later Pillar 1 milestone. |
| Identity Encoding | **RESOLVED** — Six-layer identity model adopted. See Pillar I section. *[VAR-001]* |
| Local Frame Precision | Open — Handling ECEF vs ENU transitions. To be addressed in a later Pillar 1 milestone. |
| Rendering Evolution | Open — WebGL vs WebGPU future path. |
| Gaussian Splat Integration | Open — When/how to integrate. |
| Blockchain Layer | Open — Contract anchoring architecture. |
| Semantic Layer | Partially resolved — `semantic_labels` field present in schema (v0.1.2), AI-generated. Generation and storage rules to be defined by Pillar 4. |

---

## Pilot Region

**Central Coast NSW, Australia**

The Central Coast is the initial seeding region for the Harmony Cell System. All V0.1 and V1.0 development targets this region first. The pilot validates the substrate before expansion.

Key contact: **Tom O'Gorman, Change Property** — primary pilot partner for the Reagent application layer.

---

## V1.0.1 Changelog — Variations Applied

| VAR ID | Title | Sections Modified |
|--------|-------|-------------------|
| VAR-001 | Layered Identity Model | Pillar I |
| VAR-002 | Two-Identifier Substrate | Pillar I |
| VAR-003 | Bitemporal Versioning Schema Commitment | Pillar I, Pillar IV, Gap Register |
| VAR-004 | Named-Entity Resolution Boundary | Pillar V, Agent Architecture (Class III), Gap Register |
| VAR-005 | Federation-Compatible Identity Format | Pillar I, Gap Register |
| VAR-006 | Three-Layer Agent Model | Agent Architecture |
| VAR-007 | Schema Field Additions v0.1.2 | Pillar I |
| VAR-008 | Gap Register Status Updates | Gap Register |
| VAR-009 | Harmony Cell System Commitment | Pillar I, Open Specifications |

---

*Harmony Master Specification V1.0.1 — Confidential — April 2026*
