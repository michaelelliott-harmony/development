# Harmony Identity Schema

> **Version:** 0.1.2
> **Status:** Locked — Milestone 1 Amendment under Master Spec V1.0
> **Pillar:** 1 — Spatial Substrate
> **Owner:** Agent 1 — Spatial Architecture Lead (Builder)
> **Supersedes:** identity-schema.md v0.1.1
> **Change Log:** See `CHANGELOG.md`

---

## 1. Purpose

This document is the locked specification for how every addressable object in the Harmony Spatial Operating System is identified, resolved, and referenced. It is the single source of truth for identity across all five pillars.

It defines:

- The layered identity model
- The canonical record structure
- The relationship between `cell_id` and `cell_key`
- Object types currently in scope
- Lifecycle states
- Reference and linkage rules
- Reserved fields for temporal versioning, named-entity resolution, and dual fidelity

All downstream systems — ingestion, rendering, knowledge, interaction — must conform to this schema. Any deviation requires an ADR.

---

## 2. Core Principle

> **Canonical IDs are for truth. Aliases are for people. Semantic labels are for intelligence.**

Every layer in the identity model exists to serve a different consumer:

| Layer | Consumer | Property |
|---|---|---|
| Canonical ID | The system | Immutable, opaque, globally unique |
| Cell Key | The substrate | Deterministic, derivable, reproducible |
| Human Alias | People | Mutable, namespaced, friendly |
| Friendly Name | UX surfaces | Mutable, descriptive, non-unique |
| Known Names | Named-entity resolution | Mutable, multi-valued, non-authoritative |
| Semantic Labels | AI / context | Mutable, multi-valued, generated |

The separation is non-negotiable. Conflating any two of these layers breaks the system in ways that cannot be cleanly unwound later. See ADR-001.

---

## 3. The Layered Identity Model

### 3.1 Layers in Order of Authority

```
┌────────────────────────────────────────────────────┐
│ Layer 1 — Canonical ID         (system truth)      │  ← never changes
│ Layer 2 — Cell Key             (substrate truth)   │  ← derivable
│ Layer 3 — Human Alias          (usability)         │  ← mutable, namespaced
│ Layer 4 — Friendly Name        (UX)                │  ← mutable
│ Layer 5 — Known Names          (NER primitives)    │  ← mutable, multi
│ Layer 6 — Semantic Labels      (intelligence)      │  ← mutable, multi
└────────────────────────────────────────────────────┘
```

When two layers disagree, the higher layer wins. Aliases never override canonical IDs. Friendly names never override aliases. Known names and semantic labels never override anything — they are descriptive only.

### 3.2 Layer Definitions

**Canonical ID** — The immutable identity of an object. Generated once. Never reused. Never changed. Opaque (carries no embedded meaning). The only identifier guaranteed to be stable across the lifetime of the system. See `id_generation_rules.md` §2.

**Cell Key** — A deterministic key derived from the spatial geometry and resolution level of a cell. Two systems given the same geometry and resolution must produce the same `cell_key`. This makes spatial linkage reproducible without consulting the registry. Cells only. See ADR-004 and `id_generation_rules.md` §4.

**Human Alias** — A short, human-readable identifier scoped within a namespace (e.g. `CC-421` in `au.nsw.central_coast.cells`). Aliases may change. Aliases may be retired. Aliases may collide across namespaces but never within one. See `alias_namespace_rules.md`.

**Friendly Name** — A free-text label intended for display in UI surfaces. Not unique. Not resolvable through the alias path.

**Known Names** *(new in v0.1.2)* — A multi-valued list of natural-language names by which an object may be referred to. The Sydney Opera House might have known names `["Sydney Opera House", "the Opera House", "Opera House Sydney"]`. These are indexed by the registry to support fast name-to-candidate lookup primitives that the Conversational Spatial Agent (Class III) composes with semantic search and conversational context. Known names are *not* resolvable to a single canonical ID — they return ranked candidates with confidence scores. See ADR-010.

**Semantic Labels** — A multi-valued list of descriptive tags applied by humans or AI systems. Used by the Spatial Knowledge Layer (Pillar 4) for context, search, and reasoning. Not authoritative. Not resolvable.

---

## 4. Object Types

The registry recognises the following object types in v0.1.2:

| `object_type` | Prefix | Description |
|---|---|---|
| `cell` | `hc_` | A Harmony Cell — an addressable unit of the spatial substrate |
| `entity` | `ent_<type>_` | A real-world feature (building, parcel, road, etc.) bound to one or more cells |
| `dataset` | `ds_` | A registered source dataset (reserved — used by Pillar 2) |
| `state` | `st_` | A temporal state record (reserved — used by Pillar 4) |
| `contract_anchor` | `ca_<type>_` | Reserved for future blockchain anchoring (see ADR-001 §Future) |

Only `cell` and `entity` are active in Milestone 1. The remaining types are reserved to prevent prefix collisions in later pillars.

### 4.1 Entity Subtypes (v0.1.2)

Entities carry a three-letter subtype embedded in their canonical ID:

| Subtype | Meaning |
|---|---|
| `bld` | Building |
| `prc` | Parcel |
| `rod` | Road segment |
| `wtr` | Water feature |
| `veg` | Vegetation feature |
| `inf` | Infrastructure (utility, pole, etc.) |

Subtypes are part of the canonical ID and therefore immutable. Adding a new subtype requires a schema migration and an ADR.

---

## 5. Lifecycle States

Every record in the registry carries a `status` field. The state machine is:

```
   ┌─────────┐    activate    ┌────────┐
   │ pending │ ─────────────► │ active │
   └─────────┘                └───┬────┘
        │                         │
        │                         │ deprecate
        │                         ▼
        │                    ┌────────────┐
        │                    │ deprecated │
        │                    └─────┬──────┘
        │                          │
        │                          │ retire
        │                          ▼
        │                    ┌──────────┐
        └───────────────────►│ retired  │
              cancel         └──────────┘
```

| State | Meaning |
|---|---|
| `pending` | Reserved but not yet in use. Not resolvable by default. |
| `active` | In use. Fully resolvable. Default state. |
| `deprecated` | Still resolvable, but consumers should migrate to a successor. |
| `retired` | No longer resolvable except via historical lookup. |

**Rules:**
- Canonical IDs are never deleted, only retired.
- A retired canonical ID is never reused.
- Deprecation requires a `successor_id` if a replacement exists.

The `status` field is the **lifecycle** state of a record. It is distinct from `temporal_status` (see §6.2), which describes whether the record is the *current* version of a temporally-versioned object.

---

## 6. Canonical Record Structure

### 6.1 Cell Record (v0.1.2)

```json
{
  "canonical_id": "hc_4fj9k2x7m",
  "object_type": "cell",
  "object_domain": "spatial.substrate.cell",
  "cell_key": "hsam:r08:cc:a91f2",
  "resolution_level": 8,
  "human_alias": "CC-421",
  "alias_namespace": "au.nsw.central_coast.cells",
  "friendly_name": "Coastline North Cell",
  "known_names": [],
  "semantic_labels": [
    "High-growth coastal residential zone"
  ],
  "status": "active",
  "schema_version": "0.1.2",
  "created_at": "2026-04-07T09:00:00Z",
  "updated_at": "2026-04-10T10:00:00Z",

  "valid_from": null,
  "valid_to": null,
  "version_of": null,
  "temporal_status": null,

  "fidelity_coverage": null,
  "lod_availability": null,
  "asset_bundle_count": 0,

  "references": {
    "parent_cell_id": null,
    "child_cell_ids": [],
    "entity_ids": ["ent_bld_91af82"],
    "dataset_ids": [],
    "state_ids": [],
    "asset_bundles": [],
    "successor_id": null
  }
}
```

### 6.2 Reserved Fields (v0.1.2)

The following fields are part of the v0.1.2 schema but are **reserved**. They exist to ensure forward-compatibility with later pillars without requiring a breaking schema change. Writes to reserved fields are rejected by the registry until the owning pillar formally activates them.

#### Temporal Versioning Fields (owned by Pillar 4)

| Field | Type | Purpose |
|---|---|---|
| `valid_from` | timestamp / null | The time at which this version of the object became valid in the real world |
| `valid_to` | timestamp / null | The time at which this version ceased to be valid (e.g. building demolished) |
| `version_of` | canonical_id / null | If this record is a new version of an existing object, the canonical ID of the original |
| `temporal_status` | enum / null | One of `current`, `historical`, `superseded`, `projected` |

These fields support scenarios such as: a building is demolished and rebuilt on the same parcel. Under temporal versioning, the original building is marked `temporal_status: historical` with a `valid_to` timestamp. The new building is a separate canonical_id with `version_of` pointing to the original (or null if treated as a fresh entity) and `temporal_status: current`. See ADR-009.

#### Named-Entity Resolution Fields (owned by Pillar 5, indexed by Pillar 1)

| Field | Type | Purpose |
|---|---|---|
| `known_names` | array of strings | Natural-language names this object may be referred to by |

The registry indexes `known_names` for fast lookup but does not treat them as authoritative identifiers. The Conversational Spatial Agent (Class III) composes registry name lookups with semantic search and conversational state to perform full natural-language resolution. See ADR-010.

#### Dual Fidelity Fields (owned by Pillar 2)

| Field | Type | Purpose |
|---|---|---|
| `fidelity_coverage` | object / null | Describes which fidelity types are available for this cell, e.g. `{"photoreal": "lod_8", "structural": "lod_12"}` |
| `lod_availability` | object / null | Maps LOD levels to availability status |
| `asset_bundle_count` | integer | Denormalised count of asset bundles attached to this cell, for fast filtering |
| `references.asset_bundles` | array | Typed references to asset bundles holding photorealistic and structural geometry under the dual fidelity rule |

These fields support V1.0's Pillar II obligation that photorealistic and sub-metre structural geometry must coexist within a single Harmony Cell package. See ADR-009 for forward-compatibility commitments.

### 6.3 Field Authority

| Field | Mutable | Source of Truth |
|---|---|---|
| `canonical_id` | No | Identity Generation Module |
| `object_type` | No | Set at creation |
| `object_domain` | No | Set at creation |
| `cell_key` | No | Cell Key Derivation Module |
| `human_alias` | Yes | Alias Resolution Service |
| `alias_namespace` | Yes (with alias) | Alias Resolution Service |
| `friendly_name` | Yes | Identity Registry Service |
| `known_names` | Yes | Identity Registry Service (writes), Pillar 5 (consumption) |
| `semantic_labels` | Yes | Pillar 4 (Knowledge Layer) |
| `status` | Yes | Identity Registry Service |
| `valid_from` / `valid_to` | Reserved | Pillar 4 (when activated) |
| `version_of` | Reserved (immutable when set) | Pillar 4 |
| `temporal_status` | Reserved | Pillar 4 |
| `fidelity_coverage` / `lod_availability` | Reserved | Pillar 2 |
| `references.*` | Yes | Identity Registry Service |

Immutable fields cannot be changed after creation. Attempting to write them returns `409 Conflict`. Attempting to write reserved fields returns `403 Reserved`.

---

## 7. Cell-Specific Rules

A cell record MUST satisfy:

1. `object_type == "cell"`
2. `canonical_id` matches `^hc_[a-z0-9]{9}$`
3. `cell_key` is present and matches the format defined in `id_generation_rules.md` §4
4. `cell_key` is reproducible from the cell's geometry + resolution level
5. Either `parent_cell_id` is null (root) or it resolves to an existing active cell
6. `resolution_level` is consistent with the parent (child level = parent level + 1)

### 7.1 Resolution Profile (Navigation) — Reserved

The resolution endpoint will support a `profile=navigation` query parameter that returns a stripped-down cell record optimised for machine-speed queries. Navigation Agents (Class II) operating sliding-window queries on autonomous systems require sub-millisecond responses with minimal payload.

The navigation profile will return only:
- `canonical_id`
- `cell_key`
- `resolution_level`
- minimal geometric reference
- `temporal_status` (when activated)

The full latency target for the navigation profile is reserved for resolution before Pillar 4's schema is finalised. See Gap 2 in the V1.0 master spec.

This profile is documented as a reserved API surface. The full specification will land in `resolution_service_spec.md` (Milestone 5).

---

## 8. Entity-Specific Rules

An entity record MUST satisfy:

1. `object_type == "entity"`
2. `canonical_id` matches `^ent_[a-z]{3}_[a-z0-9]{6}$`
3. The three-letter subtype is one of the registered entity subtypes (§4.1)
4. `references.primary_cell_id` is present and resolves to an active cell
5. `references.secondary_cell_ids` (optional) all resolve to active cells

Entities may live in multiple cells (e.g. a road segment crossing a boundary). Exactly one cell is designated `primary` for indexing purposes.

Entities may carry `known_names` for named-entity resolution. The Sydney Opera House, registered as a `bld` entity, would carry known names like `["Sydney Opera House", "the Opera House", "Opera House Sydney", "Utzon's masterpiece"]`. Known names are indexed but not unique — multiple entities may share known names, and the registry returns ranked candidates.

---

## 9. Reference Model

References are typed and directional:

```
cell ──parent──► cell
cell ──child───► cell
cell ──contains──► entity
cell ──asset_bundle──► asset_bundle    [reserved, Pillar 2]
entity ──primary──► cell
entity ──secondary──► cell
record ──successor──► record           (deprecation chain)
record ──version_of──► record          (temporal chain) [reserved, Pillar 4]
```

All references are stored as canonical IDs only. Aliases, friendly names, and known names are never persisted in `references` blocks. This ensures that human-facing changes never cascade through the graph.

---

## 10. Schema Versioning

Every record carries `schema_version`. The current version is `0.1.2`.

- **Patch bumps** (`0.1.1 → 0.1.2`) — backwards-compatible field additions, including reserved fields
- **Minor bumps** (`0.1.x → 0.2.0`) — backwards-compatible structural changes
- **Major bumps** (`0.x → 1.0`) — breaking changes; require migration

A reader at version N must be able to read records at version ≤ N. The registry never silently rewrites records to a newer version.

`schema_version` is distinct from `temporal_status`. The former describes the *format* of the record. The latter describes whether the record is the *current temporal version* of the object it represents.

---

## 11. JSON Schema Files

Machine-readable schemas accompany this document:

- `cell_identity_schema.json` — JSON Schema for cell records (v0.1.2)
- `entity_identity_schema.json` — JSON Schema for entity records (v0.1.2)

Any service writing to the registry MUST validate against these schemas before commit.

---

## 12. What This Schema Does Not Cover

Out of scope for v0.1.2 (deferred to later milestones or pillars):

- Geometry storage and indexing (Pillar 1, later milestone — `cell_key` derivation only at this stage)
- Local coordinate frames (Pillar 1, later milestone)
- Dataset and state record structures (Pillar 2, Pillar 4)
- Contract anchor mechanics (future)
- Semantic label generation pipelines (Pillar 4)
- Permissions and access control (cross-cutting, later)
- The active implementation of temporal versioning (reserved, Pillar 4)
- The active implementation of dual fidelity asset bundles (reserved, Pillar 2)
- The full named-entity resolution pipeline (Pillar 5; Pillar 1 supplies the primitives only)

### 12.1 Forward-Compatibility Note — Pillar 3 Rendering

The schema does not commit to a discrete-level vs continuous-LOD substrate model. The current `resolution_level` field is a discrete integer (`r00`–`r15`). If the Pillar 3 framework decision (Gap 1, V1.0) requires continuous LOD blending across levels, the schema may need additive changes — such as multi-level cell representations or fractional resolution support.

This interaction point is documented here so that future readers understand the schema is *forward-compatible* with continuous LOD but does not yet *commit* to a specific implementation. Any change driven by Pillar 3 will require its own ADR and a schema version bump.

---

## 13. Governance

Changes to this schema require:

1. An ADR documenting the change
2. Approval from Builder Agent 1 (Architecture Lead)
3. A schema version bump
4. A migration plan if the change is not backwards-compatible
5. An entry in `CHANGELOG.md`
6. An entry in `pillar-1-master-spec-variations.md` if the change should fold into a future master spec revision

The registry is the single source of truth (logical sense — see §14). No service may maintain its own private identity table.

---

## 14. Federation Note

The phrase "single source of truth" used throughout this document refers to the **logical** registry — the canonical, authoritative source of identity for the Harmony system. It does not commit Harmony to a centralised, single-operator implementation.

The canonical ID format (opaque, prefix-stable, URL-safe, generated via CSPRNG with no embedded location or operator information) is deliberately compatible with a federated, multi-issuer identity model. Should Harmony's sovereignty and trust architecture (V1.0 Gap 4) ultimately favour a federated approach, the identity layer can support it without breaking changes.

This note exists to ensure the federation option remains open, consistent with Gap 4's "deferred but must not be foreclosed" status.

---

*End of identity-schema.md v0.1.2 — locked*
