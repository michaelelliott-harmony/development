# ADR-009 — Three-Layer Agent Model

> **Status:** Accepted
> **Date:** 2026-04-10
> **Pillar:** 1 — Spatial Substrate (project-wide implications)
> **Milestone:** 1 Amendment (v0.1.2)
> **Deciders:** Builder Agent 1 (Architecture Lead), confirmed by Mikey (Founder/PM)
> **Schema Version Affected:** 0.1.2 (terminology only)
> **Related:** Master Spec V1.0 (Agent Architecture section)

---

## Context

The word "agent" appears in the Harmony project in two completely different senses, and they are starting to collide in documentation:

**Sense A — Build-time agents.** The Claude Code and Claude CoWork instances doing the engineering work. The Stage 1 Implementation Brief lists six of them: Architecture Lead, Registry Engineer, Alias Systems Engineer, Spatial Substrate Engineer, API Engineer, PM/QA. The Agent Capability & ROI Analysis lists eight. These exist *only during the build phase*. They produce code, schemas, ADRs, and tests. They will not be present in the deployed Harmony system.

**Sense B — Runtime agents.** V1.0 introduces three Agent Classes that exist *inside* the deployed Harmony system: Spatial Agents (Class I), Navigation Agents (Class II), and Conversational Spatial Agents (Class III). These are infrastructure — they live in production, query the substrate, and serve other systems.

A third category emerged in conversation that didn't have a name yet:

**Sense C — Customer-facing agents.** The agents that real users actually talk to. The conversational interface in Reagent. Customer support agents. Sales assistants. Anything a non-technical end user interacts with. These are *also* runtime, but their job is to interact with people, not infrastructure.

Right now, all three of these are being called "agents" interchangeably in different documents, and the project is reaching the point where confusion is inevitable. A non-technical reader (the founder, an investor, a future hire) cannot distinguish "Agent 4 — Spatial Substrate Engineer" (a Claude Code instance writing schema files) from "Class I Spatial Agent" (a runtime infrastructure component) from "the Reagent assistant" (the thing the user types into).

---

## Decision

Harmony adopts a **three-layer agent model** with distinct terminology for each layer. The names are non-overlapping by design.

| Layer | Name | Existence | Job | Examples |
|---|---|---|---|---|
| **1** | **Builder Agents** | Build phase only | Engineer the Harmony system | Architecture Lead, Registry Engineer, Pipeline Engineer, Knowledge Graph Engineer, Project Manager Agent, QA Agent |
| **2** | **Runtime Agent Classes** (I, II, III) | Production infrastructure | Serve spatial intelligence to other systems | Spatial Agent (I), Navigation Agent (II), Conversational Spatial Agent (III) |
| **3** | **Digital Team Members** | Production, customer-facing | Interact with end users on behalf of the platform | Reagent assistant, customer support agent, conversational guide |

### Naming rules

**Builder Agents** are numbered and titled: `Builder Agent 1 — Architecture Lead`, `Builder Agent 2 — Registry Engineer`, etc. The numbering carries over from the Stage 1 Brief; only the noun changes from "Agent" to "Builder Agent." When context is clear ("the Builder Agent producing this file"), the role title alone may be used.

**Runtime Agent Classes** keep V1.0's existing naming: `Spatial Agent (Class I)`, `Navigation Agent (Class II)`, `Conversational Spatial Agent (Class III)`. The class number is part of the name.

**Digital Team Members** are named by their customer-facing role and the product they belong to: `Reagent Assistant`, `Reagent Support Agent`, etc. The phrase "Digital Team Member" is a category term used in documentation and architecture discussions, not a name a customer would ever see.

### The Class III boundary

Conversational Spatial Agents (Class III) sit at the boundary between Layer 2 and Layer 3. They are *infrastructure* (they resolve named entities to cells, they trigger rendering transitions) but they are *invoked by* Digital Team Members (which is what the user actually interacts with).

The architectural rule:

- Digital Team Members talk to **users**
- Conversational Spatial Agents talk to **Digital Team Members** (via API) and to the **rendering engine** (via spatial-transition signals)
- Spatial Agents and Navigation Agents talk to **other agents** (Conversational Spatial Agents, autonomous systems, Digital Team Members)
- All Runtime Agents read from the **same substrate** (the Identity Registry, the spatial substrate, eventually the Knowledge Layer)

This separation means a user talking to the Reagent Assistant never directly invokes a Class III agent. The Reagent Assistant (a Digital Team Member) decides when to invoke spatial intelligence and calls the Class III agent on the user's behalf.

### Mapping to existing documents

The following documents need terminology updates as a follow-up to this ADR:

- `pillar-1-spatial-substrate-stage1-brief.md` §7 — "Agent 1" through "Agent 6" become "Builder Agent 1" through "Builder Agent 6"
- `harmony-agent-analysis.md` — the eight build-time agents become Builder Agents
- `harmony_master_spec_v0.1.md` §6 — same renaming
- `harmony_gis_business_plan.docx` §6 — "Agent team structure" table becomes "Builder Agent team structure"
- All future PM session reports use "Builder Agent" exclusively for build-time work

These updates are documentation-only and do not affect any schema, code, or interface.

---

## Consequences

### Positive

- **Eliminates a real source of confusion.** A non-technical reader can immediately distinguish "the agent that built this" from "the agent inside Harmony" from "the agent the user talks to."
- **Honours V1.0.** V1.0's three Runtime Agent Classes are preserved unchanged. The new vocabulary slots in around them.
- **Future-proof.** When Harmony eventually has many Digital Team Members (Reagent assistant, sales agent, support agent, investor relations agent), they all share a category name without colliding with infrastructure or build-time terminology.
- **Investor-friendly.** "We have three layers of AI agents — Builders that built the system, Runtime Agents that run inside it, and Digital Team Members that talk to customers" is a sentence that lands cleanly with non-technical audiences.
- **Documentation discipline.** Forces every future document to be explicit about which layer it's discussing.

### Negative

- **Renaming work.** Every existing document that uses "Agent" needs to be updated. Real but small.
- **Slightly longer names.** "Builder Agent 1" is longer than "Agent 1." Tolerable.
- **Discipline required.** Future contributors will revert to "agent" as a generic term unless documentation enforces the distinction. Mitigated by adding the three-layer model to onboarding documentation.

### Neutral

- The model doesn't change any code, schema, or interface. It is a vocabulary lock.

---

## Alternatives Considered

### A. Keep "Agent" as a Generic Term

Rely on context to distinguish the three senses.

**Rejected because:** the project is already past the point where context disambiguates. The founder explicitly raised this as causing confusion. Context-based disambiguation works for two senses, not three.

### B. Two Layers Only (Build vs Runtime)

Collapse Digital Team Members into Runtime Agent Classes.

**Rejected because:** customer-facing agents have very different design constraints, deployment patterns, and lifecycle from infrastructure agents. Merging them would obscure those differences and complicate later architecture.

### C. Different Names

Alternatives floated and rejected: "Build Roles" (too HR-ish), "Engineer Agents" (collides with the role title "Engineer"), "Worker Agents" (too generic).

"Builder Agents" was chosen because *Builder* clearly implies the build phase and is unambiguous about the role.

### D. Defer the Decision

Wait until naming actually breaks something.

**Rejected because:** the founder raised this proactively, the cost of fixing it later (renaming many more documents) is higher than fixing it now, and the new ADR-009 is itself the right place to lock this in.

---

## Implementation Notes

- This ADR is a **terminology lock**, not a schema or code change.
- A separate documentation update task (low priority, can run in background) renames "Agent N" to "Builder Agent N" across existing documents.
- The PM Agent (defined in `PM/agents/project-manager-agent-brief.md`) is, under this ADR, a Builder Agent. It should be referred to as "Project Manager Agent" or "Builder PM Agent" in formal documentation.
- The three-layer model should be added as a small addendum to the master spec V1.0 in the next master spec revision.

---

*ADR-009 — Locked*
