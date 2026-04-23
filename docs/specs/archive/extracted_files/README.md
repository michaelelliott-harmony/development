# Milestone 1 — Identity Schema Lock — Amendment Pack v0.1.2

> **Pillar:** 1 — Spatial Substrate
> **Stage:** Milestone 1 of 6 — Amendment under Master Spec V1.0
> **Status:** Pack Generated — Awaiting Mikey Sign-Off
> **Schema Version:** 0.1.2 (supersedes 0.1.1)
> **Previous Pack:** `milestone-1-identity-schema-lock/` (v0.1.1)

This pack amends the original Milestone 1 deliverables to satisfy Harmony Master Specification V1.0 — closing five Gap Register items at the schema or governance layer, formalising the three-layer agent model, and introducing the project's PM infrastructure.

---

## Contents (15 files)

### Core schema documents (amended)

| File | Status | Purpose |
|---|---|---|
| `identity-schema.md` | Amended (0.1.1 → 0.1.2) | The locked layered identity model. Now includes temporal versioning, named-entity resolution, dual fidelity reserved fields, navigation profile note, federation note, and Pillar 3 forward-compatibility note. |
| `cell_identity_schema.json` | Amended (0.1.1 → 0.1.2) | JSON Schema for cell records with reserved fields. |
| `entity_identity_schema.json` | Amended (0.1.1 → 0.1.2) | JSON Schema for entity records with reserved fields. |
| `id_generation_rules.md` | Amended (0.1.1 → 0.1.2) | Version bump and cross-references. No format or algorithm changes. |

### Architecture Decision Records

| File | Status | Purpose |
|---|---|---|
| `ADR-001-layered-identity.md` | Amended | Federation note added. |
| `ADR-004-cell-id-vs-cell-key.md` | Unchanged (carries forward from v0.1.1) | Why every cell has both an opaque ID and a deterministic key. |
| `ADR-008-alias-namespace-model.md` | Unchanged (carries forward from v0.1.1) | Why aliases live in hierarchical namespaces. |
| `ADR-009-temporal-versioning.md` | **New** | Bitemporal versioning model. Closes Gap 3 at schema layer. |
| `ADR-010-named-entity-resolution-boundary.md` | **New** | Registry exposes primitives; resolution lives in Pillar 5. Closes Gap 5 at substrate layer. |
| `ADR-011-three-layer-agent-model.md` | **New** | Builder Agents / Runtime Agent Classes / Digital Team Members. |

### Governance and history

| File | Status | Purpose |
|---|---|---|
| `CHANGELOG.md` | **New** | Full version history starting at v0.1.1, then v0.1.2. Append-only. |
| `pillar-1-master-spec-variations.md` | **New** | Comprehensive Pillar 1 contribution file (Reading B). Becomes input to a future master spec revision. |
| `README.md` | This file | Pack index and acceptance criteria. |

### Project Management infrastructure

| File | Status | Purpose |
|---|---|---|
| `PM/README.md` | **New** | PM folder structure spec. |
| `PM/templates/session-progress-report-template.md` | **New** | Format every CoWork session follows. |
| `PM/agents/project-manager-agent-brief.md` | **New** | PM Agent role, inputs, outputs, opinion guidance. |
| `PM/sessions/2026-04-10-pillar-1-v0.1.2-amendment.md` | **New** | First live session report — covers this session. Seeds the PM Agent. |

### Carried forward from v0.1.1 (unchanged)

- `alias_namespace_rules.md` — Hierarchical alias namespace rules. No v0.1.2 changes.

---

## How to Read This Pack

**If you have 5 minutes:** Read this README, then `CHANGELOG.md` v0.1.2 section.

**If you have 15 minutes:** Add `PM/sessions/2026-04-10-pillar-1-v0.1.2-amendment.md` (the session report — it summarises everything that was decided and why) and `pillar-1-master-spec-variations.md` (which captures Pillar 1's full contribution to the master spec for future reference).

**If you're reviewing the architectural decisions:** Read the three new ADRs (009, 010, 011) plus the federation note appended to ADR-001.

**If you're implementing against the schema:** Start with `identity-schema.md` v0.1.2, then validate against the JSON schemas. The reserved fields are clearly marked — do not write to them until the owning pillar formally activates them.

---

## What This Pack Closes

| Gap | V1.0 Status | After v0.1.2 |
|---|---|---|
| **Gap 1** — Continuous LOD commitment | Open | Still open (handled in dedicated Pillar 3 chat). Pillar 1 confirmed no hard dependency. Forward-compatibility note added. |
| **Gap 2** — Machine query latency target | Open | Reserved at schema layer (`profile=navigation` endpoint). Target value still pending — to be set before Pillar 4 schema finalisation. |
| **Gap 3** — Temporal versioning | Open | **Closed at schema layer.** ADR-009. Pillar 4 owns activation. |
| **Gap 4** — Federation (deferred) | Deferred | **Preserved.** Federation note in ADR-001 confirms canonical ID format is federation-compatible. |
| **Gap 5** — LLM integration (deferred) | Deferred | **Closed at substrate layer.** ADR-010. `known_names` reserved on all records. Pillar 5 owns full resolution flow. |
| **Gap 6** — Commercial model (deferred) | Deferred | Unchanged — not a Pillar 1 concern. |

---

## Acceptance Criteria for v0.1.2

From the original brief, plus the V1.0 amendment requirements:

**Original Milestone 1 criteria (carried forward):**
- [x] `identity-schema.md` — locked at v0.1.2
- [x] `cell_identity_schema.json` — locked at v0.1.2
- [x] `entity_identity_schema.json` — locked at v0.1.2
- [x] `id_generation_rules.md` — locked at v0.1.2
- [x] `alias_namespace_rules.md` — unchanged from v0.1.1
- [x] ADR-001 — Layered identity (with federation amendment)
- [x] ADR-004 — `cell_id` vs `cell_key`
- [x] ADR-008 — Alias namespace model

**New criteria for v0.1.2 (V1.0 alignment):**
- [x] ADR-009 — Temporal versioning (Gap 3 closed at schema layer)
- [x] ADR-010 — Named-entity resolution boundary (Gap 5 closed at substrate layer)
- [x] ADR-011 — Three-layer agent model
- [x] Reserved fields for temporal versioning in both schemas
- [x] Reserved fields for named-entity resolution (`known_names`)
- [x] Reserved fields for dual fidelity (Pillar 2 forward compatibility)
- [x] Federation note in ADR-001 (Gap 4 preserved)
- [x] Navigation profile note in identity-schema.md (Gap 2 substrate-side hook)
- [x] Pillar 3 forward-compatibility note in identity-schema.md
- [x] `CHANGELOG.md` established
- [x] `pillar-1-master-spec-variations.md` established
- [x] PM infrastructure established (`PM/` folder, template, agent brief, first session report)

**Not yet complete (gates v0.1.2 sign-off):**
- [ ] Mikey's review and approval
- [ ] First PM Agent daily briefing produced from this session report
- [ ] Future PM/QA Builder Agent traceability check

---

## What This Pack Deliberately Does Not Include

These belong to later milestones, other pillars, or other working sessions:

- **Database DDL** (`identity_registry_schema.sql`) — Milestone 2
- **Service implementations** — Milestones 2, 3
- **API endpoint code** — Milestone 5
- **Sample Central Coast records** — Milestone 4
- **Active temporal versioning implementation** — Pillar 4
- **Active dual fidelity implementation** — Pillar 2
- **Full named-entity resolution flow** — Pillar 5
- **Pillar 3 framework selection** — separate dedicated chat
- **The H3-vs-custom indexing decision** — separate ADR, gates the metric mapping but not the schema
- **Local coordinate frame specification** — separate Pillar 1 milestone
- **Terminology updates to existing project documents** (rename "Agent N" to "Builder Agent N") — low-priority follow-up task

---

## Cross-References

This pack should be read alongside:

- `harmony_master_spec_v0.1.md` — original system spec (will be superseded)
- `HARMONY_MASTER_SPEC_V1_0.md` — current governing master specification
- `pillar-1-spatial-substrate-stage1-brief.md` — original Stage 1 brief for Milestone 1
- `harmony_master_prompts.md` — prompt library
- `harmony-agent-analysis.md` — Builder Agent capability analysis
- `harmony_gis_business_plan.docx` — business plan

---

## Next Steps After Sign-Off

Once Mikey signs off the v0.1.2 pack:

1. **Milestone 2 (Registry Service Local) can begin.** All Milestone 1 inputs are now locked.
2. **PM Agent first run.** With the seed session report in `PM/sessions/`, the PM Agent can produce its first daily briefing tomorrow.
3. **Terminology follow-up.** Schedule a low-priority session to update existing documents with the Builder Agent rename.
4. **Independent prep work** for Pillars 2, 3, 4, 5 can be queued (per the sequential-with-prep model) once Milestone 2 has its own footing.

---

*Milestone 1 v0.1.2 amendment pack — generated under Harmony Master Spec V1.0*
