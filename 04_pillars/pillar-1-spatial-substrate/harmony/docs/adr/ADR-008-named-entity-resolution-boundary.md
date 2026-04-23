# ADR-008 — Named-Entity Resolution Boundary

> **Status:** Accepted
> **Date:** 2026-04-10
> **Pillar:** 1 — Spatial Substrate (with implications for Pillars 4 and 5)
> **Milestone:** 1 Amendment (v0.1.2)
> **Deciders:** Builder Agent 1 (Architecture Lead)
> **Schema Version Affected:** 0.1.2
> **Closes:** Master Spec V1.0 Gap 5
> **Related:** ADR-001 (Layered Identity), V1.0 Agent Class III (Conversational Spatial Agent)

---

## Context

V1.0 introduces the Conversational Spatial Agent (Class III) — the runtime agent that sits between the LLM and the rendering engine. Its job, when an LLM produces a response like *"The Sydney Opera House sits on Bennelong Point, just east of the Royal Botanic Garden,"* is to:

1. Identify that "Sydney Opera House," "Bennelong Point," and "Royal Botanic Garden" are spatial entities
2. Resolve each to a Harmony Cell or entity canonical_id
3. Rank them so the rendering engine knows which one is the primary subject
4. Trigger the spatial transition

V1.0 Gap 5 makes this an explicit substrate requirement: **the Cell identity registry must support named-entity resolution from the outset.**

The temptation is to interpret this as "the registry should resolve names." But on closer examination, that interpretation creates more problems than it solves.

### The messiness of how LLMs refer to places

A single LLM response can refer to the same place in many ways:

- "The Sydney Opera House" — exact name
- "the Opera House" — partial name
- "Utzon's masterpiece" — descriptive reference
- "the venue" — contextual reference
- "it" — pronoun, depends on prior sentences
- "Sydney's iconic harbourside building" — descriptive paraphrase
- "the place we just discussed" — conversational state

A literal name index handles the first one or two. A fuzzy search handles slightly more. None of them handle pronouns, descriptions, or contextual references. The thing that handles all of these is the LLM itself — given the right tools.

### What the registry is good at vs what the LLM is good at

The registry is good at: fast indexed lookups, exact matches, fuzzy string matches, returning ranked candidates, providing metadata.

The LLM is good at: named-entity recognition, disambiguation, contextual reasoning, pronoun resolution, deciding which of several candidates is most likely the intended one given conversational context.

If the registry tries to do the LLM's job, it does it badly. If the LLM tries to do the registry's job, it does it slowly and unreliably. The right design uses each for what it's good at.

---

## Decision

The Identity Registry exposes **named-entity resolution primitives**. It does not perform natural-language resolution itself. Natural-language resolution is a Pillar 5 responsibility, performed by the Conversational Spatial Agent (Class III), which composes registry primitives with semantic search (Pillar 4) and conversational state (Pillar 5).

### The four primitives the registry exposes

**Primitive 1 — Exact and fuzzy name lookup.** Given a string, return cells/entities whose `friendly_name`, `human_alias`, or `known_names` match exactly or fuzzily, with confidence scores. Indexed lookup, fast, lives in the registry.

**Primitive 2 — Multi-name attachment.** Each cell and entity record may carry a `known_names` array — a multi-valued list of natural-language names by which that object may be referred to. The Sydney Opera House would carry `known_names: ["Sydney Opera House", "the Opera House", "Opera House Sydney"]`. The registry indexes these for Primitive 1.

**Primitive 3 — Ranked candidates with confidence.** Name lookup never returns a single answer to a fuzzy query. It returns a list of candidates with confidence scores, sorted by confidence. The caller decides what to do with the ranking.

**Primitive 4 — Context-filtered lookup.** Given a name and a spatial context (a bounding region, an anchor cell, or a previously-resolved entity), return only candidates within that context. This handles "Central Park" disambiguation when surrounding sentences mention Manhattan.

### What the registry deliberately does NOT do

- Resolve pronouns (Pillar 5 conversational state)
- Resolve descriptive paraphrases like "Utzon's masterpiece" (Pillar 4 semantic search)
- Maintain conversational recency stacks (Pillar 5)
- Decide which of several candidates is the "right" one in a given conversation (the LLM, via the Conversational Spatial Agent)
- Promise that name lookups return single answers

### Composition model

The Conversational Spatial Agent's resolution flow:

```
1. LLM generates text
2. Conversational Spatial Agent extracts candidate name strings
3. For each candidate:
   a. If pronoun → resolve against conversational recency stack (Pillar 5 internal)
   b. Otherwise → call registry Primitive 1 (exact/fuzzy name lookup)
   c. If descriptive paraphrase → call Pillar 4 semantic search
   d. If multiple candidates → call registry Primitive 4 with surrounding context
   e. If still ambiguous → ask LLM to disambiguate using full conversation context
4. Return ranked, confidence-scored resolution to rendering engine
```

The registry is involved in steps 3b and 3d only. Everything else lives outside Pillar 1.

### Schema implications

The `known_names` field is added to both `cell_identity_schema.json` and `entity_identity_schema.json` in v0.1.2. It is reserved at the *write* layer but the registry indexes it from the start. This means:

- Pillar 1 builds and ships the indexed lookup primitive immediately
- Other pillars can populate `known_names` when they begin (Pillar 2 from data sources, Pillar 4 from semantic enrichment)
- By the time Pillar 5 builds the Conversational Spatial Agent, the primitives are ready

---

## Consequences

### Positive

- **Plays to the LLM's strengths.** Claude is excellent at NER, disambiguation, and contextual reasoning. The architecture uses the LLM for what only the LLM can do.
- **Plays to the registry's strengths.** Fast indexed lookups with confidence scores are exactly what databases are good at.
- **Avoids confident-but-wrong resolution.** Returning ranked candidates rather than single answers means the LLM has signal when it's uncertain, and can ask follow-up questions or check context before triggering a spatial transition.
- **Honours Gap 5.** The registry *does* support named-entity resolution from the outset — it provides the primitives. The full resolution pipeline composes those primitives elsewhere.
- **Keeps the identity layer narrow.** ADR-001's principle of small, focused identity layers is preserved. Adding name resolution as a *primitive* doesn't bloat the registry; trying to make it a *full resolver* would.
- **Forward-compatible with multilingual and cross-cultural names.** Adding language tags to `known_names` is a future patch, not a structural change.

### Negative

- **More moving parts.** The full resolution flow involves Pillar 1, Pillar 4, and Pillar 5. Coordination cost is real.
- **Requires Pillar 4 semantic search.** Descriptive paraphrase resolution depends on Pillar 4 being live, which means the Conversational Spatial Agent isn't fully functional until Pillar 4 lands. Mitigated by the fact that the simple cases (exact name match) work as soon as Pillar 1 ships.
- **Population burden.** `known_names` need to be populated for the system to be useful. Some will come from data sources (Pillar 2), some from semantic enrichment (Pillar 4), and some may need manual curation for high-value entities like landmarks. This is real ongoing work.
- **Confidence-score interpretation.** Callers need to understand that name lookup returns probabilities, not facts. Documentation burden.

### Neutral

- The registry's resolution endpoints become more complex (multiple modes: by canonical_id, by alias, by name) but each mode is independently testable.

---

## Alternatives Considered

### A. Registry Owns Full Name Resolution

The registry takes natural language as input and returns single canonical IDs.

**Rejected because:** the registry has no conversational context, no semantic embedding model, and no way to handle descriptive paraphrases. It would either return wrong answers confidently or refuse to answer at all.

### B. Registry Provides Only Canonical Lookup; Naming Lives Elsewhere

Don't add `known_names` at all. Let Pillar 4 maintain a separate name index outside the registry.

**Rejected because:** it creates two sources of truth for "what is this object called," and Pillar 4 would need to keep its name index in sync with cell/entity creation. The single-source-of-truth principle from ADR-001 wins here.

### C. Vector Embeddings in the Registry

Store name embeddings on every record and let the registry do semantic similarity search itself.

**Rejected because:** semantic embedding is Pillar 4's job. Embedding storage and ANN indexes have very different operational characteristics from the rest of the registry. Mixing them couples Pillar 1 to embedding model choice and version, which we want to avoid.

### D. Defer the Entire Decision to Pillar 5

Don't add `known_names` in v0.1.2. Decide the resolution boundary when Pillar 5 starts.

**Rejected because:** by then, every cell and entity record has been written without `known_names`, and adding the field requires a schema migration. Reserving it now is the cheap option.

---

## Implementation Notes

- `known_names` is added to both cell and entity schemas in v0.1.2 as an array of strings, default empty.
- The registry's name index is a Milestone 2/5 concern (lookup endpoint design).
- Confidence scoring for fuzzy name lookups is a Milestone 5 concern (resolution_service_spec.md).
- Pillar 5 will produce its own ADR documenting the Conversational Spatial Agent's full resolution flow when it begins.

---

*ADR-008 — Locked*
