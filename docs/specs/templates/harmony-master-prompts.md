# Harmony — Master Prompts Library

> **Status:** Active  
> **Stack:** Claude Chat (strategy) · Claude CoWork (execution) · Claude Code (technical build)  
> **Last Updated:** April 2026  
> **Usage:** These prompts are designed to be used within Claude Projects. Replace `[INSERT PILLAR NAME]` with the relevant pillar before use.

---

## Prompt 1 — Master Pillar Exploration

```
You are acting as the Chief Systems Architect for the Harmony Spatial Operating System.

Harmony aims to build a unified spatial operating system that models the state of the physical world through a combination of geospatial infrastructure, intelligent data pipelines, advanced rendering systems, and AI-driven spatial intelligence.

We are exploring one foundational pillar of the system.

The pillar being analyzed is: [INSERT PILLAR NAME]

Your task is to produce a clear and rigorous development blueprint that serves two audiences:
1) The product manager (non-technical but systems-oriented) who must understand the architecture and guide the process.
2) An agentic development team operating through Claude Code and Claude CoWork.

The output must translate the conceptual vision into a structured development plan that can be executed step by step.

Your response must include the following sections.

---

SYSTEM PURPOSE
Explain the role this pillar plays in the overall Harmony spatial operating system.
Describe how it connects to the other four pillars and why it must exist before the system can scale.

---

CORE PROBLEMS THIS PILLAR SOLVES
Identify the fundamental limitations in existing spatial platforms that this pillar addresses.
Explain why these problems matter for a global spatial operating system.

---

ARCHITECTURAL PRINCIPLES
Define the guiding design rules for this pillar.
These should be durable decisions that will influence the system for years.
Examples include:
hierarchical spatial indexing
streaming-first architecture
renderer abstraction layers
predictive data pipelines
entity-based spatial modeling

---

SYSTEM COMPONENTS
Break the pillar into its major subsystems.
For each subsystem explain:
its responsibility
the data it handles
the interfaces it exposes

---

TECHNICAL STACK OPTIONS
Identify the tools, frameworks, or technologies that could implement each subsystem.
Explain the tradeoffs between different options.

---

CLAUDE AGENT ROLES
Define the agents required to build this pillar.
For each agent specify:
their role
their required skills
their tools
their expected outputs

---

DEVELOPMENT MILESTONES
Break the pillar into incremental milestones that can be completed sequentially.
Each milestone should produce a working output that moves the system closer to production.
Avoid abstract tasks.
Each milestone must create something observable.

---

MINIMUM VIABLE IMPLEMENTATION
Define what the smallest functional version of this pillar looks like.
This version should be capable of integrating with the other pillars.

---

FUTURE EXPANSION PATH
Describe how the pillar can evolve once the minimum version is operational.
Focus on capabilities that support the long-term vision of a unified spatial operating system.

---

RISKS AND UNKNOWN AREAS
Identify areas where experimentation or research will be required.
Suggest strategies for testing these uncertainties early.

---

OUTPUT FORMAT
Present the final blueprint as a structured document that can be used both by the product manager and by Claude Code agents implementing the system.
```

---

## Prompt 2 — System Diagram Request

```
Using the architecture described above, produce a system diagram for this pillar within the Harmony Spatial Operating System.

The diagram must clearly illustrate:
• the major components within this pillar
• how these components interact internally
• how this pillar connects to the other four Harmony pillars

The five pillars of the Harmony system are:
1 Spatial Substrate
2 Data Ingestion Pipeline
3 Rendering Interface
4 Spatial Knowledge Layer
5 Interaction Layer

Your diagram must show:
• upstream dependencies
• downstream consumers
• data flow between systems
• APIs or contracts exposed by this pillar

Provide the diagram in a format that can easily be recreated by developers, such as:
• Mermaid diagram syntax
• architecture graph specification
• or a clearly structured textual diagram

Also include a short explanation describing how the components collaborate during a typical system operation.
```

---

## Prompt 3 — Repository Structure Request

```
Design the repository structure required to implement this pillar within the Harmony platform.

The repository should follow a modular architecture that supports the five Harmony pillars while allowing independent development of each subsystem.

Your response must include:
A top-level repository layout.

Example structure:
harmony/
  apps/
  packages/
  services/
  pipelines/
  data/
  agents/
  docs/

Then define where the code for this pillar should live inside that structure.

For each directory explain:
• its purpose
• the type of code stored there
• how it interacts with other modules

Also specify:
• programming languages likely used
• major dependencies or frameworks
• configuration files required

Finally describe how Claude Code agents will interact with this repository.
For example:
• Which directories they generate code in
• Which directories they read for context
• Which directories store outputs

The repository design should prioritize:
• modularity
• maintainability
• long-term scalability
```

---

## Prompt 4 — Execution Plan Request

```
Translate the architecture for this pillar into a structured execution plan.

The plan should be designed for a team of Claude agents working under a product manager.

Break development into phases.
For each phase include:
• the objective
• the specific deliverables
• the agents responsible
• the tools required
• the expected outputs

Each phase must produce a working artifact that can be tested.
Examples of artifacts:
• running services
• working pipelines
• functional UI components
• validated datasets
• integration tests

Also include acceptance criteria for each phase.
Acceptance criteria should clearly define when the phase is considered complete.

The plan should include approximately:
• 5–8 development phases
• incremental system capability growth
• integration checkpoints with other Harmony pillars

End the execution plan with a first-week sprint plan that could begin immediately.
```

---

## Prompt 5 — Master Timeline Alignment Request

```
Harmony is being developed through five architectural pillars.

Each pillar is explored in separate design discussions, but the development must align to a shared master timeline.

Using the architecture and execution plan defined above, identify:
1 The dependencies this pillar has on the other pillars
2 The deliverables this pillar must provide before other pillars can progress
3 The integration milestones where this pillar interacts with the rest of the system

Then map this pillar's execution plan onto the following master development stages.

Stage 1 — Spatial Foundation
The planet indexing system and spatial cell architecture are operational.

Stage 2 — Data Pipeline
Real-world datasets can be ingested and transformed into Harmony-compatible layers.

Stage 3 — Visualization
The globe client can render terrain, layers, and navigation.

Stage 4 — Spatial Intelligence
Entities such as buildings and parcels accumulate attributes and historical state.

Stage 5 — Interaction
Users can navigate the system through queries, layers, and conversational commands.

For each stage specify:
• what this pillar contributes
• what it requires from other pillars
• risks that could delay the stage

The goal is to ensure all pillar architectures converge toward a unified development timeline.
```

---

## Usage Notes

- Always load `harmony_master_spec_v0.1.md` as context before running any of these prompts
- Replace `[INSERT PILLAR NAME]` in Prompt 1 with the specific pillar being explored
- Prompts 2–5 are designed to run sequentially after Prompt 1 within the same conversation
- Outputs from each prompt should be saved to the relevant subfolder under `04_pillars/`
- Prompt 3 repository outputs should be cross-referenced against the file system defined in the master spec
