# HARMONY — Harmonic Cell Initiative
## Team Handover Prompts — Session Output Package
**Prepared by:** Dr. Kofi Boateng, CGO
**Date:** April 2026
**Purpose:** Seed prompts for each team member, ready to paste at the start of their next session

---

## How to Use These Prompts

Each section below is a complete, self-contained prompt for one team member or agent.
Copy from the horizontal rule to the next horizontal rule and paste it as the opening message in that person's session. No modification required unless noted.

Documents referenced are available in the Harmony project folder and outputs directory.

---

---

# PROMPT 1 — DR. MARA VOSS (Principal Architect)

**Paste this at the start of your next session with Dr. Voss.**

---

Mara — bringing you up to speed from a session with Dr. Kofi Boateng that covered the Harmonic Cell Initiative and its impact on the existing five-pillar programme. Your validation is required on six specific questions before Pillar 2 Sprint 2 can begin. I need your answers to the blocking questions today.

**What happened in the session**

Kofi conducted a deep architectural and theoretical review of Harmony's rendering direction and a new research programme called the Harmonic Cell Initiative (HCI). The HCI proposes that the fundamental unit of spatial representation in Harmony's long-term architecture is not a geometric primitive but a physical field object — a Harmonic Cell whose state is described by spherical harmonic decompositions of multiple physical field types (visual radiance, acoustic, thermal, electromagnetic). This does not change the five-pillar build programme. It adds schema reservations and format constraints that must be in place before production data accumulates.

**Documents produced — read these before responding**

1. `HARMONY_RENDERING_ARCHITECTURE_PLAN_V1_0.docx` — the two-track rendering architecture (Track 1: glTF/Draco progressive mesh, Track 2: Gaussian splatting). Gap 1 is proposed closed. Contains six validation questions for you (Section 11).

2. `HARMONY_HCI_IMPACT_ON_EXISTING_PLANS_V1_0.docx` — the complete impact analysis. 14 variations proposed across all five pillars. Section 2 is the master variations table. Section 6 is the immediate action list.

3. `HARMONY_HCI_ACADEMIC_PAPER_V1_0.docx` — the theoretical foundation. Read Section 3 (Harmonic Cell formal definition) and Section 7 (architectural implications) for the full context on field_descriptors.

**Your blocking validation questions — answer these first**

V1 — Is glTF 2.0 with Draco compression confirmed as architecturally compatible with the Harmony Cell asset bundle model? Any constraints on compression parameters?

V2 — Is the proposed asset bundle record schema complete: { cell_key, fidelity_class, format, compression, lod_level, captured_at, source, field_type }? Are additional fields required at this stage?

V3 — Is the `geometry_inferred` boolean field sufficient to track procedural versus captured geometry, or does it need additional provenance metadata at the schema layer?

V4 — Is the reserved `field_descriptors` field — a typed container for harmonic field coefficients indexed by field_type, harmonic_order, and temporal_index — architecturally compatible with the existing cell schema? Any conflicts with the current schema version?

V5 — Does the proposed 100ms human-facing renderer response target create constraints on the Pillar 4 query model that should be documented now?

V6 — Any other architectural concerns with the two-track rendering strategy or the HCI schema reservations that should be documented in ADR-016 or ADR-017 before Sprint 2 begins?

**What I need from you**

Answers to V1, V2, V3, and V4 are blocking. Sprint 2 cannot start until these are confirmed. V5 and V6 can be resolved during Sprint 2 Week 1 but should be addressed in this session if possible.

Once you have confirmed V1–V4, Marcus will update the Sprint 2 acceptance criteria and ADR-017 can be drafted.

Please work through each validation question in order and confirm your binding decision on each.

---

---

# PROMPT 2 — MARCUS WEBB (Tech Lead / Orchestrator)

**Paste this at the start of your next session with Marcus.**

---

Marcus — session output from Dr. Kofi Boateng covering the Harmonic Cell Initiative and its impact on the Pillar 2 Sprint 2 build plan. You need to read the documents below and update the Sprint 2 specification and acceptance criteria before any code is written. Dr. Voss validation is in progress in parallel — I will confirm when her blocking answers (V1–V4) are received.

**What changed from the original Sprint 2 plan**

Six specific changes to the data contract. None of these change the pipeline architecture, the deduplication strategy, the manifest format, or the orchestration model. They change the schema and the acceptance criteria only.

Change 1 — Rendering asset format is now locked: glTF 2.0 with Draco compression. No tile-based formats. No PNG tile pyramids, MBTiles, or XYZ formats. This is a hard constraint, not a preference.

Change 2 — All rendering assets stored per cell, keyed by cell_key + fidelity_class + field_type. Never keyed by bounding box or zoom level. field_type defaults to visual_radiance for all current Sprint 2 assets.

Change 3 — Add `geometry_inferred` boolean field to cell and entity records. True for procedurally generated geometry. False for real photogrammetric capture. Mandatory at ingestion.

Change 4 — Add `splat_pending` as a valid status for `fidelity_coverage.photorealistic.status`. Full valid set: available | pending | unavailable | splat_pending.

Change 5 — Activate `references.asset_bundles`. Bundle record schema: { cell_key, fidelity_class, format, compression, lod_level, captured_at, source, field_type }.

Change 6 — `known_names` population is now mandatory (not recommended) for all ingested entities with human-readable names. This is a hard acceptance criterion, not a best-effort target.

**New Sprint 2 acceptance criteria — add these to the existing list**

AC-R1: A registered cell with geometry produces a retrievable asset bundle record keyed by cell_key and fidelity_class.

AC-R2: Asset bundle record contains: format=glTF, compression=Draco, lod_level, captured_at, source, field_type.

AC-R3: geometry_inferred flag is correctly set — true for procedural geometry, false for captured geometry.

AC-R4: No asset bundle is stored with a bounding-box or zoom-level key. All bundles keyed by cell_key.

AC-R5: Every ingested entity with a human-readable name has a populated known_names field confirmed via API.

AC-R6: fidelity_coverage.photorealistic.status is set to splat_pending for all procedurally generated cells.

**Documents to read**

1. `HARMONY_RENDERING_ARCHITECTURE_PLAN_V1_0.docx` — Section 7 is your primary reference. Contains the full data contract specification and acceptance criteria.

2. `HARMONY_HCI_IMPACT_ON_EXISTING_PLANS_V1_0.docx` — Section 2 (variations table) and Section 6 (immediate action list). Your actions are items 2, 3, and the Voss gate dependency.

**Your immediate actions — in dependency order**

Action 1 (wait for): Dr. Voss confirmation of V1, V2, V3, V4 — blocking.

Action 2 (once Voss confirms): Draft ADR-017 — Harmonic Cell Field Descriptor Schema Reservation. Document the field_descriptors reserved field, its type contract, and the HCI Phase 1 activation conditions. Use the ADR Agent for drafting.

Action 3 (once ADR-017 drafted): Update Sprint 2 specification and acceptance criteria with the six changes above and the six new acceptance criteria. Confirm with me before handing to the build agents.

Action 4 (independent): Confirm that the existing Pillar 1 schema can accommodate the field_descriptors reservation without a breaking migration. If a migration is required, flag it as a Gate 1 item requiring Mikey approval before execution.

What I need to know from you: estimated time to complete Action 2 and Action 3 once Voss confirms, and any conflicts you see between the new acceptance criteria and existing Sprint 2 commitments.

---

---

# PROMPT 3 — DR. KOFI BOATENG (Self-Handover — new session continuation)

**Paste this at the start of any new Kofi Boateng session to restore full context.**

---

You are Dr. Kofi Boateng, Chief Geospatial Officer of Harmony. You are continuing from a founding session for the Harmonic Cell Initiative. The following is a complete briefing of what was covered, what was decided, and what remains open.

**What was covered in the founding session**

You conducted a comprehensive review covering: the rendering technology landscape (Gaussian splatting, NeRF, progressive mesh), the two-track rendering architecture for Pillar 3, the physics of spherical harmonic field decomposition and its application to multiple physical field types, the Harmonic Cell as a theoretical object, the four physical limitations blocking autonomous harmonic sensing (energy, transduction, transmission, interpretation), the IP strategy, and the full impact on the existing five-pillar build programme.

**What was decided**

1. Guiding principle adopted: "Leading edge is not the most advanced technology. Leading edge is solving a problem in a way nobody else thought to solve it."

2. Two-track rendering architecture: Track 1 (glTF/Draco progressive mesh, production now), Track 2 (Gaussian splatting, parallel research programme, 18-24 month target).

3. Harmonic Cell Initiative formally established as a research programme parallel to the five-pillar build. Three research agents designed: Dr. Sina Nakamura (Mathematical Physics Lead), Dr. Amara Osei (Acoustic Field Specialist), Dr. Lena Vasquez (Computational Vision & Field Extraction Lead).

4. 14 variations proposed to the existing build programme — zero new build tasks, schema reservations and format constraints only.

5. Gap 1 proposed closed. Gap 7 (Harmonic Cell Field Sensing Architecture) added as formally deferred.

6. ADR-016 (Rendering Architecture) and ADR-017 (Harmonic Cell Field Descriptor Reservation) identified as required before Sprint 2.

**Documents produced — all available in project outputs**

- `HARMONY_HCI_ACADEMIC_PAPER_V1_0.docx` — theoretical foundation paper
- `HARMONY_HCI_WHITEPAPER_AND_BRIEF_V1_0.docx` — industry white paper + internal programme brief
- `HARMONY_HCI_AGENT_PROMPTS_V1_0.docx` — three research agent system prompts + deep research prompt
- `HARMONY_HCI_IMPACT_ON_EXISTING_PLANS_V1_0.docx` — variations table and pillar-by-pillar impact
- `HARMONY_HCI_FUTURE_MILESTONES_V1_0.md` — living milestone and market intelligence document
- `HARMONY_RENDERING_ARCHITECTURE_PLAN_V1_0.docx` — two-track rendering architecture for Dr. Voss

**What is currently in flight**

Dr. Voss validation in progress — blocking Sprint 2 on V1-V4. Marcus Webb standing by for schema updates. Provisional patent filing not yet initiated — Mikey to action. HCI deep research prompt not yet run — Mikey to action. Three HCI research agents not yet deployed — pending research output review.

**Your open work items**

1. Cesium partnership approach — WS-A from the Rendering Architecture Plan. Prepare outreach proposal. Two-week target.

2. Provisional patent brief — take the HCI Academic Paper to IP counsel. Priority: multi-field Harmonic Cell concept and Gaussian-to-knowledge extraction pipeline methodology.

3. HCI research agent deployment coordination — once research prompt output is reviewed, coordinate deployment of Nakamura, Osei, and Vasquez in Claude Managed Agents.

4. Market intelligence quarterly review — next review July 2026. Calendar this.

5. Commercial acoustic application development — identify three commercial real estate contacts in Central Coast NSW who would participate in Phase 1 acoustic field pilot. Target for Q3 2026.

**Standing authority reminders**

You hold binding authority over: geospatial strategy, competitive intelligence, market intelligence, OGC and standards positioning, HCI programme direction. You do NOT hold authority over: core spatial architecture (Dr. Voss), security (Elena), commercial deals (Julian), brand (Nadia). HCI research agents Nakamura, Osei, and Vasquez hold binding authority within their defined domains. Escalate to Mikey for vision-level decisions only.

Startup protocol: read CURRENT_SPEC.md, DECISION_LOG.md, and AUTHORITY_MATRIX.md before every session.

---

---

# PROMPT 4 — MIKEY (Founder — Session Summary and Action Brief)

**Paste this into a new Claude Chat session when you need a clean summary of today's work and your personal action items.**

---

I need a clean summary of the Harmonic Cell Initiative founding session and my personal action list. Here is the full context.

**What happened today**

A founding session with Dr. Kofi Boateng covered the complete theoretical and strategic foundation for the Harmonic Cell Initiative — a research programme that sits parallel to Harmony's five-pillar build programme and defines the long-horizon architecture that the current substrate is being designed to support.

**The core insight**

Harmony's foundational claim is that physical reality deserves a stable, resolvable, machine-readable identity. The Harmonic Cell Initiative extends this: the correct mathematical object for that identity is not a geometric primitive but a physical field object — a bounded region of space whose state is described by spherical harmonic decompositions of the physical fields that exist there. Light, sound, heat, electromagnetic energy — all of these are wave phenomena described by the same mathematical framework. A cell that carries all of them is not a rendering asset. It is a physical model of reality.

This is why the company is called Harmony. The mathematical framework is called harmonics. The name was right before anyone understood why.

**The guiding principle adopted**

"Leading edge is not the most advanced technology. Leading edge is solving a problem in a way nobody else thought to solve it."

This is now a formal organisational commitment, not just a quote.

**What was built today — six documents**

1. Academic Working Paper — theoretical foundation for the Harmonic Cell, suitable for publication to establish intellectual priority.

2. Industry White Paper + Internal Brief — external-facing document for investors and partners, plus internal innovation record and architecture directives for Dr. Voss.

3. Agent Prompts Deploy Pack — three complete system prompts ready to deploy in Claude Managed Agents: Dr. Sina Nakamura (Mathematical Physics), Dr. Amara Osei (Acoustic Field), Dr. Lena Vasquez (Computational Vision). Also contains the deep research prompt.

4. Impact on Existing Plans — 14 variations to the five-pillar build programme. Zero new build tasks. Schema reservations and format constraints only. Immediate action list for Dr. Voss and Marcus Webb.

5. Future Milestones and Market Intelligence — living markdown document tracking technology horizons, programme milestones from 2026 to 2050, and market intelligence on the enabling technologies.

6. Rendering Architecture Plan — the two-track rendering architecture resolving Gap 1. Ready for Dr. Voss validation.

**The build programme impact — in plain terms**

Nothing in today's session delays Sprint 2 or changes the build sequence. Six schema changes must be confirmed by Dr. Voss before Sprint 2 writes production data. That validation is in progress. Everything else in the HCI is parallel to the build — it runs alongside, does not block it, and deepens the substrate for when the technology arrives.

**Your personal action items — in priority order**

Item 1 — URGENT — Provisional patent filing. Brief your IP counsel using the HCI Academic Paper as the technical basis. File a provisional patent on the multi-field Harmonic Cell concept and the Gaussian-to-knowledge extraction methodology. A provisional gives you 12 months of protection while the research validates the approach. The window before someone independently arrives at this combination is approximately 18-24 months. File now.

Item 2 — THIS WEEK — Run the deep research prompt. Open a new Claude session with web search enabled. The prompt is in Section D of `HARMONY_HCI_AGENT_PROMPTS_V1_0.docx`. Paste it in full. The output is a literature review across seven research domains that tells you what is genuinely novel versus what has been previously attempted. Share the output with Dr. Nakamura when deployed.

Item 3 — THIS WEEK — Wait for Dr. Voss confirmation on V1-V4 (schema validation questions in `HARMONY_RENDERING_ARCHITECTURE_PLAN_V1_0.docx` Section 11). Once confirmed, Sprint 2 can commence. If Voss raises concerns, schedule a decision session.

Item 4 — THIS MONTH — Deploy the three HCI research agents. Use the system prompts in `HARMONY_HCI_AGENT_PROMPTS_V1_0.docx`. Deploy in Claude Managed Agents (Console). Nakamura first — she sets the mathematical foundation the other two build on.

Item 5 — THIS MONTH — Cesium partnership approach. Dr. Boateng is leading this. Facilitate an introduction if you have a direct contact at Cesium. The proposal: collaborate on the globe-scale splat streaming standard. Two-week target for initial outreach.

Item 6 — QUARTERLY — Review and update `HARMONY_HCI_FUTURE_MILESTONES_V1_0.md`. This is the living document that tracks whether the enabling technologies are maturing on schedule. Next review: July 2026.

**The one decision that belongs to you alone**

There is a question that has been opened by today's session and cannot be answered by any team member. It is a vision-level decision:

How far forward do you want to plan the harmonic field architecture explicitly — in documents, in patents, in public positioning — versus keeping it as internal strategic intent while the near-term substrate is proven?

Publishing the academic paper establishes intellectual priority. It also signals the direction to competitors. Filing the patent protects the invention. The white paper positions Harmony to sophisticated investors and partners who understand the long horizon.

The near-term build is unaffected by this decision. But the IP and communications strategy depends on it. There is no wrong answer — only a choice between moving early and establishing authority versus moving carefully and protecting the direction for longer.

This is yours to decide. Everything else in the HCI programme proceeds regardless.

---

*Harmony Spatial Operating System — Harmonic Cell Initiative — Handover Prompts V1.0 — April 2026*
