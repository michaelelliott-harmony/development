# 04 — ADR Summary
## Governing Decisions — Stage 2 Relevant

---

## How to Use This File

Every decision listed here is binding. Check before making any
architectural choice. If a task requires deviation, produce a new
ADR — do not deviate silently.

---

## ADRs Most Relevant to Stage 2

**ADR-003 — Cell Key Derivation Architecture**
BLAKE3 hash → 80 bits → 16 Crockford Base32 characters. Deterministic.
Same geometry always produces same key.

Surface cell key format (UNCHANGED by Stage 2):
hsam:r{resolution}:{region}:{16-char-hash}

Volumetric cell key format (Stage 2 addition):
hsam:r{resolution}:{region}:{16-char-hash}:v{alt_min}-{alt_max}

Where alt values are in metres, one decimal place.
Reserve @ separator for future temporal suffix:
hsam:r{resolution}:{region}:{16-char-hash}:v{alt_min}-{alt_max}@{date}
Do not implement temporal suffix — reserve the separator only.

**ADR-004 — Dual-Identifier Principle**
Every cell carries cell_id (canonical, immutable) AND cell_key
(deterministic, derivable). Both apply to volumetric cells.

**ADR-005 — Cell Adjacency Model**
Precomputed at registration. Never runtime-computed. Stage 2 extends
this to include vertical adjacency (up/down) for volumetric cells.
Lateral adjacency for volumetric cells uses the same 24-entry boundary
transition table as surface cells.

**ADR-007 — Temporal Versioning**
Four reserved fields: valid_from, valid_to, version_of, temporal_status.
DO NOT populate these. DO NOT add them to the Stage 2 migration.
They are already reserved in the schema. Pillar 4 activates them.

**ADR-013 — API Layer Architecture**
12 HTTP endpoints. FastAPI. All inter-pillar interaction through API
only. No direct module imports from downstream pillars.

**ADR-015 — Adaptive Volumetric Cell Extension (PRIMARY ADR)**
- Surface cells extend full vertical column (null altitude) — default
- Volumetric cells represent specific altitude bands
- Vertical subdivision is adaptive — only where structure exists
- Altitude range: -11,000m (seabed) to 1,000m+ (aviation)
- Cell key altitude suffix: :v{alt_min}-{alt_max}
- Vertical adjacency: up/down neighbours added
- Schema path: v0.1.3 → v0.2.0
- Backward compatible: surface cell keys unchanged

---

## Your First Deliverable: ADR-016

Before writing any code, produce ADR-016 at:
docs/adr/ADR-016-pillar-1-stage-2-implementation.md

ADR-016 documents:
- Vertical adjacency storage format decision
- Altitude validation rules
- Forward-compatibility confirmation (@ separator reservation)
- Any implementation choices not covered by ADR-015

Status: Accepted (you write and accept it — it is an implementation ADR,
not a design ADR; design is covered by ADR-015).
