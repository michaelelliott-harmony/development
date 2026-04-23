# Pillar 1 — Master Spec Variations

> **Purpose:** A running, comprehensive record of everything Pillar 1 has resolved, added, or clarified that should fold into a future revision of the Harmony Master Specification.
>
> **Format:** Reading B — comprehensive contribution file, not just deltas. When all five pillars have produced their variations files, the next master spec revision (V1.1 or V2.0) can be assembled by merging these five documents.
>
> **Pillar:** 1 — Spatial Substrate
> **Owner:** Builder Agent 1 (Architecture Lead)
> **Last Updated:** 2026-04-10 (v0.1.2 amendment)
> **Status:** Living document — appended to as Pillar 1 progresses through milestones

---

## How to Read This Document

Each section corresponds to a category of Pillar 1's contributions to the master spec. Each entry in each section is a *summary* of a decision, with a cross-reference to the ADR or schema file where the full detail lives. The variations file deliberately does not duplicate content — it is an index of contributions, not a re-statement of them.

When the master spec is next revised, the editor reads this file (and the equivalent files from other pillars) to identify what should be incorporated.

---

## Section 1 — Gap Register Items Resolved

These are items from the V1.0 Gap Register that Pillar 1 has closed (fully or at the schema layer).

### Gap 3 — Temporal Versioning (Closed at Schema Layer)

**V1.0 status:** *"Cell schemas and HCID structures must be confirmed as capable of supporting temporal versioning without breaking changes before ingestion begins at scale."*

**Pillar 1 resolution:** Bitemporal versioning model adopted at the schema layer in v0.1.2. Four reserved fields added to cell and entity schemas: `valid_from`, `valid_to`, `version_of`, `temporal_status`. Active implementation deferred to Pillar 4. Schema is forward-compatible — Pillar 4 can activate temporal versioning without breaking changes.

**Reference:** ADR-009 — Temporal Versioning Model

**What the master spec should say:** "Pillar 1 commits to bitemporal versioning at the schema layer. Pillar 4 owns active implementation. The schema distinguishes system time (`created_at`/`updated_at`) from valid time (`valid_from`/`valid_to`), and supports version chains via `version_of` and `temporal_status`."

---

### Gap 5 — Named-Entity Resolution (Closed at Substrate Layer)

**V1.0 status:** *"The Cell identity registry must support named-entity resolution from the outset."*

**Pillar 1 resolution:** The Identity Registry exposes named-entity resolution *primitives* — exact and fuzzy name lookup, multi-name attachment via `known_names`, ranked candidate returns with confidence scores, and context-filtered lookup. Full natural-language resolution (pronouns, descriptive paraphrases, conversational state) is composed by the Conversational Spatial Agent (Class III) in Pillar 5, drawing on Pillar 1's primitives, Pillar 4's semantic search, and Pillar 5's own conversational state.

**Reference:** ADR-010 — Named-Entity Resolution Boundary

**What the master spec should say:** "The Identity Registry is responsible for indexed name lookup primitives. The Conversational Spatial Agent (Class III) is responsible for full natural-language resolution by composing those primitives with semantic search and conversational context. The boundary is deliberate: each layer does what it is good at."

---

### Gap 4 — Federation (Preserved, Not Foreclosed)

**V1.0 status:** *"Sovereignty and trust architecture — the identity model must not foreclose the federated option."*

**Pillar 1 resolution:** The canonical ID format is deliberately federation-compatible. IDs carry no embedded operator, region, or jurisdiction. The phrase "single source of truth" in identity documentation refers to the *logical* registry, not a centralised deployment. Federation note added to ADR-001 in v0.1.2 to make this explicit.

**Reference:** ADR-001 §Federation Note

**What the master spec should say:** "The Identity Registry is the logical single source of truth. The current deployment model is centralised, but the canonical ID format and registry contract are compatible with a federated, multi-issuer model. Federation, when introduced, lives in the deployment topology, not in the identity format."

---

## Section 2 — Schema Additions and Reserved Fields

These are concrete schema-layer additions that should be reflected in any master spec section that summarises identity records.

### Cell Records (v0.1.2)

| Field | Status | Owner | Purpose |
|---|---|---|---|
| `canonical_id` | Active | Pillar 1 | Immutable opaque identifier |
| `cell_key` | Active | Pillar 1 | Deterministic substrate key |
| `human_alias` | Active | Pillar 1 | Namespaced human-friendly alias |
| `alias_namespace` | Active | Pillar 1 | Hierarchical dotted namespace |
| `friendly_name` | Active | Pillar 1 | Free-text display name |
| `known_names` | Reserved (indexed) | Pillar 5 reads, Pillar 1 indexes | Named-entity resolution primitives |
| `semantic_labels` | Active | Pillar 4 | AI-generated descriptive tags |
| `valid_from` / `valid_to` | Reserved | Pillar 4 | Temporal valid time |
| `version_of` | Reserved | Pillar 4 | Temporal version chain |
| `temporal_status` | Reserved | Pillar 4 | Temporal lifecycle |
| `fidelity_coverage` | Reserved | Pillar 2 | Dual fidelity coverage map |
| `lod_availability` | Reserved | Pillar 2 | LOD availability map |
| `asset_bundle_count` | Reserved | Pillar 2 | Denormalised count |
| `references.asset_bundles` | Reserved | Pillar 2 | Typed asset bundle references |

### Entity Records (v0.1.2)

| Field | Status | Owner | Purpose |
|---|---|---|---|
| `canonical_id` | Active | Pillar 1 | Immutable opaque identifier with embedded subtype |
| `entity_subtype` | Active | Pillar 1 | One of: bld, prc, rod, wtr, veg, inf |
| `human_alias` / `alias_namespace` | Active | Pillar 1 | Same as cells |
| `friendly_name` | Active | Pillar 1 | Same as cells |
| `known_names` | Reserved (indexed) | Pillar 5 reads, Pillar 1 indexes | Named-entity resolution |
| `semantic_labels` | Active | Pillar 4 | AI-generated descriptive tags |
| `valid_from` / `valid_to` | Reserved | Pillar 4 | Temporal |
| `version_of` / `temporal_status` | Reserved | Pillar 4 | Temporal |
| `references.primary_cell_id` | Active | Pillar 1 | Required primary cell binding |
| `references.secondary_cell_ids` | Active | Pillar 1 | Multi-cell occupancy |

**What the master spec should say:** The master spec's identity table should be updated to reflect these layers and reserved fields. The current V1.0 spec describes identity at a conceptual level and does not enumerate fields — that's appropriate. The next revision should add a "see Pillar 1 schema for current field list" cross-reference.

---

## Section 3 — New Concepts Introduced

These are concepts that did not exist in the V1.0 master spec and should be considered for inclusion in a future revision.

### 3.1 The Layered Identity Model (six layers in v0.1.2)

The principle that identity is split into distinct layers, each with its own consumer and mutability rules. Documented in ADR-001 and `identity-schema.md`. The pinned principle: *"Canonical IDs are for truth. Aliases are for people. Semantic labels are for intelligence."*

**What the master spec should say:** Adopt the layered model as a foundational principle in the Pillar I (Spatial Substrate) section. The current V1.0 spec mentions "stable identity" but does not articulate the layered model.

### 3.2 cell_id vs cell_key (Two-Identifier Substrate)

Every cell carries both an opaque immutable canonical ID *and* a deterministic derivable substrate key. Documented in ADR-004. This is the resolution to the "stability vs reproducibility" tension that any spatial substrate faces.

**What the master spec should say:** This should be added as a foundational design decision in the Pillar I section. It is one of the most consequential architectural calls in the project.

### 3.3 The Three-Layer Agent Model

Builder Agents (build phase, engineering work), Runtime Agent Classes I/II/III (V1.0's existing classes — production infrastructure), and Digital Team Members (production, customer-facing). Documented in ADR-011.

**What the master spec should say:** Add a brief addendum to the V1.0 Agent Architecture section formalising the three-layer model. The Runtime Agent Classes are already defined in V1.0 — this addendum adds Builder Agents and Digital Team Members as the surrounding categories.

### 3.4 Bitemporal Versioning at the Substrate Layer

The schema distinguishes system time from valid time and supports version chains. Documented in ADR-009.

**What the master spec should say:** Add to the Pillar IV (Spatial Knowledge Layer) section as the substrate's commitment to support what Pillar IV will activate.

### 3.5 The Resolution Primitives Boundary

The Identity Registry exposes name-lookup primitives but does not own natural-language resolution. Resolution is composed across Pillar 1, Pillar 4, and Pillar 5. Documented in ADR-010.

**What the master spec should say:** Add to the Pillar V (Interaction Layer) section as the architectural division of responsibility for the Spatial Knowledge Interface (V1.0 North Star III).

### 3.6 Federation-Compatible Identity Format

The canonical ID format is deliberately federation-compatible. Documented in the ADR-001 federation note.

**What the master spec should say:** When the V1.0 Gap 4 is eventually addressed, the master spec should reference the federation note as evidence that the identity layer is ready.

---

## Section 4 — Open Items Pillar 1 Surfaced But Doesn't Own

These are decisions Pillar 1 identified as necessary but that belong to other pillars or other working sessions.

### 4.1 Pillar 3 Framework Decision (V1.0 Gap 1)

**Status:** Being handled in a separate dedicated chat with full Pillar 3 context. Pillar 1 has confirmed it has no hard dependency on this decision. A forward-compatibility note has been added to `identity-schema.md` §12 noting that the schema does not commit to a discrete-level vs continuous-LOD substrate model.

**Pillar 1 deliverable:** None directly. Schema is forward-compatible.

### 4.2 Machine Query Latency Target (V1.0 Gap 2)

**Status:** A `profile=navigation` resolution endpoint has been reserved in the schema (see `identity-schema.md` §7.1). The actual latency target must be set before Pillar 4's Spatial Knowledge Layer schema is finalised.

**Pillar 1 deliverable:** Reserved endpoint specification. Target value is a Pillar 4 (or pre-Pillar-4) decision.

### 4.3 Active Temporal Implementation

**Status:** Schema reserved. Pillar 4 owns activation. The four reserved temporal fields are forward-compatible.

**Pillar 1 deliverable:** None until Pillar 4 begins.

### 4.4 Active Dual Fidelity Implementation

**Status:** Schema reserved. Pillar 2 owns activation. Four reserved fields and one reserved reference array.

**Pillar 1 deliverable:** None until Pillar 2 begins.

### 4.5 Conversational Spatial Agent (Class III) Resolution Flow

**Status:** Pillar 1 has provided primitives. The full flow lives in Pillar 5. ADR-010 documents the boundary.

**Pillar 1 deliverable:** None directly. Primitives delivered.

### 4.6 Local Coordinate Frames (ECEF vs ENU)

**Status:** Open from the original Stage 1 Brief and the master spec. Not addressed in v0.1.1 or v0.1.2 because Milestone 1 covers identity only, not geometry. To be addressed in a later Pillar 1 milestone.

**Pillar 1 deliverable:** Pending. Not blocking Milestone 1 sign-off.

### 4.7 Spatial Indexing Scheme (H3 vs Custom)

**Status:** Open. Affects the metric edge length for each resolution level (`id_generation_rules.md` §4.4). Not affecting Milestone 1 because the schema uses level numbers, not metric values.

**Pillar 1 deliverable:** Pending. To be addressed in a later Pillar 1 milestone.

---

## Section 5 — Recommended Changes to the Next Master Spec Revision

Concrete edit recommendations for the next master spec editor (whether human or Builder Agent) when V1.1 or V2.0 is assembled.

### Pillar I (Spatial Substrate) section

- Add the layered identity model as a foundational principle (Section 3.1 above)
- Add `cell_id` vs `cell_key` as a key architectural decision (Section 3.2 above)
- Add the bitemporal commitment with cross-reference to Pillar IV (Section 3.4 above)
- Add a paragraph on federation compatibility (Section 3.6 above)
- Update the identity field summary to reference the v0.1.2 schema

### Pillar IV (Spatial Knowledge Layer) section

- Add a note that temporal versioning is reserved at the substrate layer and active implementation is owned here
- Reference ADR-009 as the substrate-layer commitment

### Pillar V (Interaction Layer) section

- Add the resolution primitives boundary (Section 3.5 above)
- Reference ADR-010 as the architectural division
- Note that Class III agents are the consumers of the registry's name lookup primitives

### Agent Architecture section

- Add the three-layer agent model addendum (Section 3.3 above)
- Reference ADR-011

### Gap Register section

- Mark Gap 3 as "closed at substrate layer, awaiting Pillar 4 activation"
- Mark Gap 5 as "closed at substrate layer, awaiting Pillar 5 activation"
- Mark Gap 4 as "preserved, federation note added to ADR-001"
- Leave Gaps 1, 2, 6 open

---

## Appendix — Cross-Reference Index

| Master Spec Concept | Pillar 1 Source |
|---|---|
| Layered identity | ADR-001, identity-schema.md §3 |
| Cell key | ADR-004, id_generation_rules.md §4 |
| Alias namespaces | ADR-008, alias_namespace_rules.md |
| Temporal versioning | ADR-009, identity-schema.md §6.2 |
| Named-entity resolution | ADR-010, identity-schema.md §3.2 |
| Three-layer agent model | ADR-011 |
| Federation compatibility | ADR-001 federation note |
| Identity registry contract | identity-schema.md §13 |
| Cell record schema | cell_identity_schema.json |
| Entity record schema | entity_identity_schema.json |

---

*Pillar 1 — Master Spec Variations — Living Document*
*Next update: when Pillar 1 progresses to Milestone 2 or beyond*
