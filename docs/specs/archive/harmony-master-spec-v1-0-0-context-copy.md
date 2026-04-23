# HARMONY — Spatial Operating System
## Master Specification | Version 1.0
**Status:** Active  
**Supersedes:** V0.1 — Spatial Substrate Architecture Blueprint  
**Date:** April 2026  
**Owner:** Mikey (Founder)

---

## Version History

| Version | Date | Summary of Change |
|---------|------|-------------------|
| V0.1 | March 2026 | Spatial Substrate established. Harmony Cell System defined: hierarchical cell structure, HCID identity model, local ENU coordinate frames, entity occupancy principles, Central Coast NSW as pilot region. |
| V1.0 | April 2026 | Three North Stars formalised as governing design criteria. Five-pillar obligations updated. Agent Architecture made explicit with three agent classes. Gap Register introduced. Build sequencing model defined. |

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

**Unchanged from V0.1.** The Harmony Cell System remains the correct foundation. The HCID identity model, hierarchical cell structure, local ENU coordinate frames, and entity occupancy model are all carried forward without modification.

**V1.0 addition:** Every schema and lifecycle decision must be validated against the machine query use case as well as the human rendering case. The temporal memory architecture, deferred in V0.1, must be formally scoped as a design intent in V1.0. Cell schemas and HCID structures must be confirmed capable of supporting temporal versioning without breaking changes before ingestion begins at scale.

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

---

### Pillar V — Interaction Layer (Spatial Knowledge Interface)

The Interaction Layer is the Spatial Knowledge Interface. It operates through three components in concert.

The **semantic extraction pipeline** parses LLM output in real time, identifies spatially meaningful entities (places, buildings, routes, geographic features), and resolves them against the Harmony Cell identity registry.

The **triggering protocol** defines the conditions and thresholds that determine when a conversational response should initiate a spatial transition and what form that transition takes.

The **continuity model** is the design principle that the conversational context is not interrupted or replaced by the spatial experience. Both modes of knowing operate simultaneously — the spatial experience serves as the physical context in which the conversational knowledge unfolds.

---

## Agent Architecture

Three agent classes operate within Harmony. They share the same spatial substrate, draw from the same Harmony Cell identity registry, and are governed by the same entity occupancy model. No agent class owns the substrate — each queries it and writes to its state layer within defined permissions.

---

### Class I — Spatial Agents

Associated with Harmony Cells and their occupying entities. A spatial agent holds read access to a cell's geometry, entity index, state, and relationship references, and can respond to queries that require reasoning rather than simple data retrieval. Spatial agents carry temporal context, respond to state changes, and synthesise information across neighbouring cells.

Spatial agents serve all three north stars: they carry LOD context for seamless rendering, provide navigation context for autonomous machines, and provide factual and historical grounding for the Spatial Knowledge Interface.

---

### Class II — Navigation Agents

Machine-facing intelligence units designed to serve autonomous systems localising and routing in real time. A navigation agent operates on a sliding window of Harmony Cells centred on a moving entity and maintains a continuously updated model of traversable space, known obstacles, confidence-weighted geometry, and neighbouring cell states.

The distinguishing design principle is **latency**. Navigation agents must operate at machine timescales — serving updated spatial context within the response window that an autonomous navigation decision requires. This implies a different caching model, query interface, and state update frequency than Spatial Agents, even though both draw from the same substrate.

---

### Class III — Conversational Spatial Agents

Sit at the boundary between the Interaction Layer and the Spatial Knowledge Layer. Their function is threefold: parse LLM semantic output to identify spatial entities, query the Harmony Cell registry to resolve those entities to stable spatial addresses, and signal the rendering engine to initiate a spatial transition.

The conversational spatial agent does not replace the LLM. It augments its output with spatial grounding. **The LLM provides the knowledge. The conversational spatial agent provides the address. The rendering engine provides the experience.**

---

## Build Sequencing

The three north stars are not competing priorities. They occupy different pillars and draw from the same foundation. Pursuing them in parallel is architecturally correct.

**The single rule:** Build one foundation. Design it to carry all three futures from day one. Do not begin building the rendering surface, the navigation query model, or the conversational spatial pipeline until the Cell System has proven itself with real data in the Central Coast NSW pilot region. Once it has, all three tracks open simultaneously.

The risk to manage is attentional, not architectural. Hold all three north stars visible in every substrate decision, but assign a single primary track to each development phase.

---

## Gap Register — V1.0

### Resolve Before Build Proceeds

**Gap 1 — Rendering Philosophy Commitment**  
The rendering layer must formally commit to continuous LOD streaming rather than tile switching. The specific technology is not locked, but the philosophy must be. A tile-based rendering layer cannot be evolved into the seamless world experience without a full rebuild.

**Gap 2 — Machine Query Latency Specification**  
A provisional latency target for machine-speed spatial queries must be established before the Spatial Knowledge Layer schema is finalised. Without a target, the data model and caching architecture cannot be correctly designed.

**Gap 3 — Temporal Memory Design Intent**  
The Spatial Knowledge Interface depends on historically grounded spatial identity. Cell schemas and HCID structures must be confirmed as capable of supporting temporal versioning without breaking changes before ingestion begins at scale.

### Defer With Documentation

**Gap 4 — Sovereignty and Trust Architecture**  
Whether Harmony pursues a decentralised or federated truth protocol versus a centralised custodian model is strategically significant but does not block the Central Coast pilot. Formally deferred. Note: the identity model must not be designed in a way that forecloses the federated option.

**Gap 5 — LLM Integration Protocol**  
The conversational spatial agent's integration protocol with a connected LLM can be deferred until Pillar V development begins. The Cell identity registry must support named-entity resolution from the outset.

**Gap 6 — Commercial Model for the Machine Substrate**  
The business model for the GPS-free navigation layer (licensing, API access, robotics partnerships) is not yet specified. Deferred, but must be scoped before any external capital conversations that extend beyond the real estate vertical.

---

## Pilot Region

**Central Coast NSW, Australia**

The Central Coast is the initial seeding region for the Harmony Cell System. All V0.1 and V1.0 development targets this region first. The pilot validates the substrate before expansion.

Key contact: **Tom O'Gorman, Change Property** — primary pilot partner for the Reagent application layer.

---

*Harmony Master Specification V1.0 — Confidential — April 2026*
