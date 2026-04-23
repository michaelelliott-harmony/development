# ADR-018: Data Tier Model and Provenance Hierarchy

**Status:** Proposed
**Date:** 2026-04-23
**Deciders:** Mikey (founder), Dr. Mara Voss (Principal Architect)
**Pillar:** 2 (Data Ingestion Pipeline)
**Related:** ADR-007 (Temporal Versioning), ADR-010 (Spatial Geometry Schema Extension), ADR-015 (Central Coast Data Sourcing)

---

## Context

Harmony's Central Coast MVP ingests data exclusively from NSW authoritative sources (ADR-015). However, the platform's long-term value proposition — planetary-scale spatial intelligence — requires a strategy for populating cells outside jurisdictions where authoritative government data is available or accessible.

Three facts drive this decision:

First, authoritative government data does not exist uniformly worldwide. For many regions, the best available data is community-maintained (OpenStreetMap) or ML-derived (Microsoft Building Footprints, Google Open Buildings, Overture Maps Foundation). These sources have materially different quality, licensing, and trust characteristics than NSW Spatial Services.

Second, different data classes arrive at different trust levels. A building footprint from NSW Spatial is authoritative; the same building in OSM may be community-contributed with no verification. The cell package format must allow these to coexist without losing track of which is which.

Third, autonomous systems consuming Harmony (North Star II) cannot tolerate mixed provenance without knowing it. A Class II Navigation Agent making landing decisions must know whether the structural geometry it is consuming came from a government survey or an ML-derived dataset with a 0.7 confidence score.

The current cell package format does not encode source tier, confidence, or provenance in a structured way. This ADR closes that gap.

---

## Decision

Adopt a four-tier data model that classifies every ingested data element by source authority, and carry tier, confidence, and provenance metadata through the cell package format.

**The four tiers:**

- **Tier 1 — Authoritative.** Government or legally authoritative sources. NSW Spatial Services, NSW Planning Portal, Valuer General. Assumed accurate; conflicts resolved in favour of Tier 1.
- **Tier 2 — Open Authoritative.** Globally uniform open-source projects with formal governance. Overture Maps Foundation is the preferred Tier 2 source. OpenStreetMap is acceptable where Overture coverage is absent.
- **Tier 3 — ML-Derived / Commercial.** Machine-generated datasets (Microsoft Building Footprints, Google Open Buildings) and commercial feeds. Confidence-scored; treated as supplementary to Tiers 1 and 2.
- **Tier 4 — Generated Knowledge.** LLM-generated or inferred content. **Never populates structural or photorealistic fidelity slots.** Lives only in the Pillar 4 knowledge layer, clearly attributed, never consumed by autonomous systems.

**Cell package implication:**

Every geometry and attribute in the cell package carries three provenance fields:

- `source_tier` — integer 1–4
- `source_id` — the specific source (e.g. `nsw_spatial`, `overture_2026_q1`, `claude_generated`)
- `confidence` — float 0.0–1.0, where 1.0 indicates Tier 1 authoritative data

**Conflict resolution:**

When multiple sources contribute to the same cell element, the higher tier wins. Within a tier, the more recent source wins. Conflicting Tier 1 sources (rare — e.g. cadastral discrepancies) escalate for human review rather than auto-resolving.

**Safety firewall for autonomous consumers:**

The Pillar 4 machine query interface (read path for autonomous agents) filters to `source_tier <= 3` by default. Tier 4 generated knowledge is never returned to autonomous consumers unless explicitly requested with a safety-acknowledged flag — and even then, never for the structural or photorealistic fidelity slots.

---

## Consequences

**Positive:**

- Enables global cell population without compromising the authority of the Central Coast MVP
- Establishes a clean pattern for future source additions — new sources slot into existing tiers rather than requiring schema changes
- Creates the instrumentation needed for the knowledge-density score concept flagged for Pillar 4
- Firewalls LLM-generated content from safety-critical autonomous decisions
- Makes Harmony's data moat legible — the ratio of Tier 1 coverage to Tier 2/3 coverage is a measurable platform asset

**Negative:**

- Every Pillar 2 ingestion adapter must populate provenance fields correctly — adds schema surface area
- Conflict resolution logic is non-trivial for attribute-level conflicts (geometry conflicts are easier)
- Tier 3 ML-derived sources require confidence thresholds that need tuning per source

**Neutral:**

- This ADR describes the architecture but does not commit Pillar 2 MVP to ingesting Tier 2 or Tier 3 sources. The MVP remains Tier 1 only. Tier 2/3 ingestion is a post-MVP expansion, governed by this architecture when it happens.

---

## Alternatives Considered

**Alternative 1: Treat all sources as equivalent, resolve conflicts by timestamp.** Rejected. Collapses the distinction between authoritative and community-maintained data, creating unacceptable risk for autonomous consumers.

**Alternative 2: Single `is_authoritative` boolean.** Rejected. Binary classification cannot distinguish government data from Overture from ML-derived, all of which have materially different trust characteristics.

**Alternative 3: Defer provenance architecture until post-MVP.** Rejected. Retrofitting provenance into an already-populated registry is vastly more expensive than carrying it from day one. Even if MVP ingests only Tier 1, the schema must anticipate Tiers 2–4.

---

## Open Questions

- Which confidence-scoring methodology applies to Tier 3 ML-derived sources? Each source publishes its own; should Harmony normalise these onto a common scale?
- Does Tier 4 knowledge enter the cell package directly, or is it held in a separate Pillar 4 knowledge store and joined at query time? (Pillar 4 to resolve.)
- What is the explicit process for escalating Tier 1 conflicts? (Flag for dataset registry; full resolution deferred to post-MVP.)
