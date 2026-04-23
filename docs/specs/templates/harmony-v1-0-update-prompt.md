# HARMONY — Context Update Prompt
## For use in existing Harmony chat threads to upgrade them to V1.0

---

Paste the following prompt at the start of any existing Harmony conversation thread.

---

**--- PASTE BELOW THIS LINE ---**

This project has been formally updated to Harmony Master Specification V1.0. Please read the following update carefully and treat it as the authoritative governing context for all future responses in this conversation. It supersedes any earlier architectural framing, priorities, or assumptions established in this thread.

**What has changed**

The core architecture established in previous conversations — the Harmony Cell System, the five-pillar structure, the HCID identity model, local ENU coordinate frames, and the entity occupancy principle — is unchanged and remains valid. What V1.0 adds is governing intent in the form of three North Stars, an explicit Agent Architecture, and a Gap Register of decisions that must be resolved before build progresses.

**The Three North Stars**

These are non-negotiable success criteria. Every architectural decision, every schema choice, and every deferred feature must be evaluated against all three simultaneously.

North Star I — The Seamless World. Any user familiar with Google Maps or Google Earth must, on first encounter with Harmony's rendering layer, have an unambiguous recognition that this is a different category of experience. The rendering layer commits to continuous level-of-detail streaming. Tile switching is not the model and cannot become it.

North Star II — The GPS-Free Spatial Substrate. Harmony Cells are not merely rendering units. They are machine-readable spatial reference frames — stable, authoritative, continuously updated descriptions of physical space at sub-metre fidelity, queryable at the speed autonomous navigation decisions require. A drone navigating via Harmony does not need GPS.

North Star III — The Spatial Knowledge Interface. When a user asks an AI system about a place, the world should transform around the answer. The conversational interface gives way to a spatial one — the globe appears, the camera moves toward the subject of the question, and the knowledge unfolds as the user travels through Harmony toward the place being described. Text does not stop. The spatial experience becomes the physical context in which knowledge lands and is remembered.

**Updated Pillar Obligations**

Pillar I — Spatial Substrate: every schema decision must now be validated against the machine query use case as well as human rendering. Temporal memory must be scoped as a design intent even where implementation is staged.

Pillar II — Data Ingestion Pipeline: a dual fidelity standard is now a first-class requirement. Photorealistic assets for rendering and sub-metre structural geometry for robotic navigation must be carried within a single Harmony Cell package.

Pillar III — Rendering Interface: continuous LOD streaming is the committed philosophy. The rendering engine must additionally support triggered cinematic transitions — receiving a place identity from the Interaction Layer and beginning camera movement toward that location at conversational response speed.

Pillar IV — Spatial Knowledge Layer: the query model must serve both human and machine consumers as first-class cases. A machine query latency target must be established before the knowledge layer schema is finalised.

Pillar V — Interaction Layer: this pillar now has its defining capability — the Spatial Knowledge Interface. It operates through three components: a semantic extraction pipeline that parses LLM output and identifies spatial entities in real time, a triggering protocol that determines when a response should initiate a spatial transition, and a continuity model that ensures the conversational and spatial modes operate simultaneously rather than one replacing the other.

**The Three Agent Classes**

Class I — Spatial Agents: associated with Harmony Cells, carry geometry, state, temporal context, and relationship references, and can reason rather than merely retrieve.

Class II — Navigation Agents: machine-facing, operate on a sliding window of cells centred on a moving autonomous entity, must serve updated spatial context at machine timescales.

Class III — Conversational Spatial Agents: sit at the boundary between the Interaction Layer and the Spatial Knowledge Layer. Parse LLM output for spatial entities, resolve them against the Harmony Cell registry, and signal the rendering engine. The LLM provides the knowledge. The conversational spatial agent provides the address. The rendering engine provides the experience.

**The Gap Register — items that must not be closed off**

Gap 1: The rendering layer must commit to continuous LOD streaming before further rendering architecture decisions are made.

Gap 2: A machine query latency target must be established before the Spatial Knowledge Layer schema is finalised.

Gap 3: Cell schemas and HCID structures must be confirmed as capable of supporting temporal versioning without breaking changes before ingestion begins at scale.

Gap 4 (deferred): Sovereignty and trust architecture — the identity model must not foreclose the federated option.

Gap 5 (deferred): LLM integration protocol for the conversational spatial agent — the Cell identity registry must support named-entity resolution from the outset.

Gap 6 (deferred): Commercial model for the GPS-free machine substrate must be scoped before any external capital conversations beyond the real estate vertical.

**Build sequencing**

The three north stars are not competing priorities. They occupy different pillars and draw from the same foundation. The single governing rule is: build one foundation, design it to carry all three futures from day one, and do not begin building the rendering surface, navigation query model, or conversational spatial pipeline until the Cell System has proven itself with real data in the Central Coast NSW pilot region.

**Instruction**

Please confirm you have read and integrated this update, then identify any decisions, recommendations, or plans made in this conversation thread that should now be revisited in light of the V1.0 governing criteria. Flag anything that may conflict with the three north stars, the updated pillar obligations, or the Gap Register constraints, and propose how each should be resolved or updated.

**--- PASTE ABOVE THIS LINE ---**
