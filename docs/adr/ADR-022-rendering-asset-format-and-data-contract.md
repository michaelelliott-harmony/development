# ADR-022: Rendering Asset Format and Data Contract

**Status:** Accepted

**Date:** 2026-04-24

**Acceptance Date:** 2026-04-24 (amended with Dr. Voss review corrections)

**Deciders:** Marcus Webb, Dr. Mara Voss, Dr. Kofi Boateng

---

## Context

Pillar 3 (Rendering Interface) requires formal specification of:

1. The canonical asset encoding format for 3D geometry delivery to rendering pipelines
2. The schema contract for asset bundles (metadata + geometry references)
3. The fidelity coverage states and their semantics
4. The relationship between geometry inference and fidelity status (atomic enforcement)
5. Resolution of Gap 1 (Asset Encoding) and partial closure of Gap 2 (Rendering Performance)

The rendering subsystem must consume geometry from the Harmony Cell registry and deliver it to downstream visualisation engines (web, mobile, spatial AR). The asset format decision directly impacts:

- Ingestion adapter workload (geometry transcoding)
- Cache efficiency (compression ratio and decode time)
- Client payload size (bandwidth and latency)
- Browser/engine compatibility (codec support)
- Streaming and LOD delivery strategy

Gap 1 asks: "Which 3D asset encoding standard shall Harmony canonicalise on?"
Gap 2 asks: "Can we deliver cell geometry to a human-facing interface in <100ms?"

---

## Decision

### D1: Canonical Asset Format — glTF 2.0 + Draco Compression

Harmony adopts **glTF 2.0** (GL Transmission Format 2.0, ISO/IEC 40588) as the canonical encoding for all 3D geometry delivered via the rendering pipeline.

All glTF payloads **must** use **Draco compression** (Google Draco v1.5+) with:
- **Compression level:** 7 (maximum compression, balancing ratio and decode latency)
- **Quantization:** 14-bit for vertex positions, 10-bit for normals
- **Preserved attributes:** geometry, topology, normals, UV coordinates (if present)

**Rationale:**
- glTF 2.0 is an ISO standard with broad engine support (three.js, Babylon.js, Cesium.js, Unreal, Unity, native engines)
- Draco compression at level 7 achieves 10–20× compression over uncompressed geometry while maintaining <5ms decode latency on modern hardware
- Draco is codec-stable (v1.5 has 5+ years of production use) and open-source (Apache 2.0)
- Quantization settings balance visual fidelity (±0.006m positional error at cell scale) with payload size

### D2: Asset Bundle Schema

Every asset bundle carries the following schema:

```json
{
  "bundle_id": "string (UUID)",
  "cell_id": "string (canonical cell ID)",
  "created_at": "ISO 8601 timestamp",
  "encoding_format": "string (enum: 'gltf2_draco_l7')",
  "encoding_version": "string (semantic version of encoding standard)",
  "geometry_source_url": "string or null (nullable)",
  "geometry_source_hash": "string (SHA-256 of original geometry before encoding)",
  "geometry_inferred": "boolean",
  "fidelity_coverage": {
    "photorealistic": {
      "status": "enum (available | pending | splat_pending)",
      "source_tier": "integer or null (1–4 if status='available' or 'splat_pending'; nullable if status='pending')",
      "confidence": "number (0.0–1.0)",
      "timestamp": "ISO 8601 (moment of assessment)"
    },
    "structural": {
      "status": "enum (available | pending | splat_pending)",
      "source_tier": "integer or null (1–4 if status='available' or 'splat_pending'; nullable if status='pending')",
      "confidence": "number (0.0–1.0)",
      "timestamp": "ISO 8601"
    }
  },
  "payload_bytes": "integer (size in bytes of encoded glTF blob)",
  "vertex_count": "integer (triangle count × 3)",
  "bounds": {
    "min": {"x": "number", "y": "number", "z": "number"},
    "max": {"x": "number", "y": "number", "z": "number"}
  },
  "lod_chain": [
    {
      "lod_level": "integer (0 = highest detail)",
      "vertex_count": "integer",
      "url": "string (reference to glTF asset in storage)"
    }
  ]
}
```

All fields are required except `geometry_source_url` (nullable to accommodate inferred or synthetic geometry).

**Cardinality Constraint:** The `lod_chain` array **must contain at least one entry**. An empty array is semantically invalid; absence of the entire bundle is the correct signal for "no geometry". This ensures that every asset bundle present in the system has at least a LOD-0 (highest-detail) representation available.

**Schema-Level Constraints:**

The following CHECK constraints are mandatory on the `asset_bundles` table:

```sql
-- Tier 4 (synthetic/AI-generated) cannot be marked 'available' in photorealistic fidelity
CHECK (
    (fidelity_coverage->'photorealistic'->>'source_tier')::int != 4
    OR (fidelity_coverage->'photorealistic'->>'status') != 'available'
)

-- Tier 4 (synthetic/AI-generated) cannot be marked 'available' in structural fidelity
CHECK (
    (fidelity_coverage->'structural'->>'source_tier')::int != 4
    OR (fidelity_coverage->'structural'->>'status') != 'available'
)

-- LOD chain must have at least one entry
CHECK (
    array_length(lod_chain, 1) >= 1
)
```

**Rationale:** Tier 4 data is synthetic or AI-generated and must never be classified as "available" for rendering (Tier 4 can only be `pending` or `splat_pending`). This constraint preserves the hard boundary between measured/processed data (Tiers 1–3) and generated data (Tier 4), preventing accidental misrepresentation of synthetic geometry as measured geometry to end users.

### D3: Fidelity Coverage States and Semantics

Three valid fidelity states are defined in the `fidelity_coverage.*.status` field:

| State | Meaning | Interpretation |
|---|---|---|
| `available` | Geometry exists and is suitable for rendering at this fidelity level | The cell has either measured geometry (inferred=false) or a complete inferred representation (inferred=true, splat_pending=false). **Tier 4 cannot have this status.** |
| `pending` | Geometry is queued for acquisition or processing | A request for geometry has been filed but the result is not yet computed or stored. `source_tier` is nullable in this state. |
| `splat_pending` | Geometry is available in a degraded form pending upgrade via photogrammetry or measurement | The cell currently holds a splat (point cloud or mesh inferred from adjacent cells or satellite imagery) and is awaiting higher-fidelity measurement. **Tier 4 cannot have this status.** |

**Tier Range:** Source tiers are 1–4 per ADR-018 (Tier 0 does not exist). Tier 4 (synthetic/AI-generated) is excluded from `available` and `splat_pending` states and may only occupy `pending` state.

### D4: Atomic Enforcement — geometry_inferred → splat_pending

When `geometry_inferred` is **true**, the system **atomically forces**:

```
fidelity_coverage.photorealistic.status = "splat_pending"
```

This enforcement is **schema-level**, enforced via a database CHECK constraint:

```sql
CHECK (
  (geometry_inferred = false) OR 
  (geometry_inferred = true AND fidelity_coverage.photorealistic.status = 'splat_pending')
)
```

**Rationale:** An inferred geometry (reconstructed from adjacent cells, satellite imagery, or AI upsampling) is not a direct measurement. It is a best-effort stand-in and must be marked as pending final photogrammetry or field survey. This constraint prevents misclassification of inferred geometry as "available" measured geometry, which would violate Tier semantics (Tier 4 = synthetic/AI-generated; Tier 1–3 = measured/processed).

### D4b: Dual Source_Tier Semantics

Every asset bundle carries **two independent `source_tier` fields** with distinct semantics:

1. **Provenance `source_tier`** (record-level, per ADR-018): Tier of the original data source (Tier 1 = field survey, Tier 2 = published reference, Tier 3 = derived/computed, Tier 4 = synthetic/AI)
2. **Fidelity `source_tier`** (per-fidelity-level, in `fidelity_coverage`): Tier of the data used to assess this specific fidelity level

**Key invariant:** The fidelity-level `source_tier` **cannot be lower (more trustworthy) than the provenance `source_tier`**.

Example:
- A building has provenance Tier 1 (measured via LIDAR survey)
- Its photorealistic fidelity is Tier 1 (from the LIDAR data)
- Its structural fidelity is Tier 3 (derived from the LIDAR via automated simplification)
- This is valid: fidelity Tier 3 ≥ provenance Tier 1

Counterexample (invalid):
- A building has provenance Tier 2 (from published CAD)
- Its photorealistic fidelity is Tier 1 (impossible — where did Tier 1 come from?)
- This is invalid: fidelity Tier 1 < provenance Tier 2

**Tier 4 Exclusion on Both Fields:**

The Tier 4 exclusion (cannot be `available` in either fidelity state) applies to **both fields independently**:
- If provenance `source_tier` = 4, no fidelity slot can be `available` (even if fidelity `source_tier` is lower, e.g., Tier 4 geometry + Tier 3 structural fidelity is forbidden)
- If a fidelity's `source_tier` = 4, that fidelity cannot be `available` (regardless of provenance tier)

This ensures the hard boundary: no geometry carrying Tier 4 at any level can be presented to users as "finished" or "ready for rendering".

### D5: Gap Closure Status

**Gap 1 (Asset Encoding):** CLOSED

The question "Which 3D asset encoding standard shall Harmony canonicalise on?" is answered: glTF 2.0 with Draco compression level 7 is the canonical format, with no alternative encodings permitted in the rendering pipeline.

**Gap 2 (Rendering Performance):** PARTIALLY CLOSED

The question "Can we deliver cell geometry to a human-facing interface in <100ms?" is addressed:

- **Accepted (provisional):** 100ms is the target for end-to-end geometry delivery from cell registry → glTF encoding → network transmission → client decode → render.
- **Status:** Provisional — contingent on:
  - Network latency <20ms (cell-to-client)
  - Draco decode latency ≤5ms (hardware-dependent; verified on reference devices)
  - Client LOD selection algorithm ≤5ms (implementation-dependent)
  - Storage fetch ≤30ms (cache hit assumed)
  
- **Gap remains open for:** Implementation verification (Pillar 3 M2) and fallback strategy if any component exceeds its budget

The 100ms target is a design goal, not a guarantee. Pillar 3 Sprint 2 will measure end-to-end latency and define fallback strategies (e.g., progressive mesh loading, pre-cached LOD0 for common cells).

---

## Rationale

### Format Choice

glTF 2.0 was selected over alternatives (USD, FBX, Cesium3DTiles) because:

1. **Standardisation:** ISO/IEC 40588 removes vendor lock-in and ensures long-term stability
2. **Browser support:** Native or near-native support in all major web engines (three.js, Babylon.js, Cesium.js)
3. **Compression:** Draco compression is built into the glTF 2.0 spec and widely supported; no proprietary codec required
4. **Ecosystem:** Largest open-source tooling ecosystem (Blender, Three.js, GLTF validators, transcoding tools)
5. **File size:** Draco L7 achieves smaller payloads than alternatives (USD is uncompressed; FBX is binary-only; Cesium3DTiles is geometry + metadata, not raw geometry)

Alternatives rejected:
- **USD:** Primarily for offline rendering; no real-time decoder standardisation; large uncompressed file size
- **FBX:** Proprietary (Autodesk); codec complexity; browser support limited to polyfill
- **Cesium3DTiles:** Container format for geometry + metadata; adds overhead; Harmony already has metadata in the cell registry
- **OBJ/MTL:** Legacy; no compression support; poor support for complex topology

### Fidelity State Model

The three-state model (`available`, `pending`, `splat_pending`) reflects Harmony's actual geometry lifecycle:

- **available:** Trustworthy for rendering; either measured or fully processed synthetic
- **pending:** Not yet acquired; placeholder geometry may exist (e.g., from adjacent cells)
- **splat_pending:** Placeholder geometry exists (inferred) but final measurement is queued

This avoids the false binary distinction between "has geometry" vs. "doesn't have geometry". Rendering clients can query status and decide whether to use splat geometry, request measurement, or defer rendering.

### Schema-Level Enforcement of geometry_inferred → splat_pending

Pushing the constraint to the schema level (CHECK constraint, not application logic) ensures:

1. **Invariant preservation:** No code path can violate the constraint; database enforces it atomically
2. **Auditability:** Violations appear in the database error log, not hidden in application logic
3. **Performance:** CHECK constraint is evaluated during INSERT/UPDATE; no post-hoc validation scan needed
4. **Correctness:** The constraint becomes part of the schema contract, visible to all consumers (documentation, schema introspection tools, migrations)

### Gap 1 Closure

Gap 1 is formally closed: Harmony will not re-evaluate alternative formats. If future requirements demand USD support (for offline VFX pipelines) or Cesium3DTiles (for multi-asset containers), those will be downstream transcoding steps, not canonical format changes.

### Gap 2 Partial Closure

Gap 2 remains partially open because:
- The 100ms target is architectural; implementation will measure actual latency
- Network and hardware are out of Harmony's control; fallback strategies may be needed
- Pillar 3 M2 will benchmark decode latency on reference devices and define SLA tiers
- If 100ms cannot be met, the gap will evolve to ask: "Can we meet <500ms (progressive load)?" or "Can we cache N% of cells for <100ms?"

---

## Alternatives Considered

### A1: Use USD (Universal Scene Description)

**Advantages:**
- Widely adopted in VFX/animation pipelines
- Hierarchical, extensible structure

**Disadvantages:**
- No built-in compression; uncompressed files 3–5× larger than glTF+Draco
- No ISO standard; Pixar-governed
- Browser support requires polyfill (slower)
- Overkill for Harmony's use case (we already model hierarchy and metadata in the cell registry)

**Rejected:** Payload size and browser support are disqualifying for a human-facing interface.

### A2: Use Cesium 3D Tiles

**Advantages:**
- Built for geographic data; hierarchical LOD structure aligns with cell levels
- Mature ecosystem (Cesium.js, CesiumJS)

**Disadvantages:**
- Container format (tileset.json + geometry); adds metadata overhead (Harmony already has metadata in cell registry)
- Proprietary glTF extensions; binds tightly to Cesium ecosystem
- Not an ISO standard

**Rejected:** Adds unnecessary complexity; glTF 2.0 alone is sufficient for geometry delivery.

### A3: Use FBX or Proprietary Binary Format

**Advantages:**
- Smaller file size than OBJ
- Widely supported in game engines

**Disadvantages:**
- FBX: Proprietary (Autodesk); patent/licensing complexity
- Browser support: Requires WASM polyfill; slower decode
- Long-term stability: Proprietary formats risk obsolescence

**Rejected:** Open, standardised format required for long-term interoperability.

### A4: Draco Compression Level 5 (vs. Level 7)

**Advantages:**
- Faster decode (~2–3ms vs. 5ms)
- Adequate compression for most use cases

**Disadvantages:**
- 15–20% larger files than L7
- At target 100ms budget, 3ms savings is marginal vs. 15% payload bloat
- Modern hardware (2020+) decodes L7 in <5ms; older devices are out of support scope

**Rejected:** L7 is appropriate for Harmony's target audience (modern web browsers, mobile, AR platforms).

### A5: Make Fidelity a Two-State System (available | pending)

**Advantages:**
- Simpler state machine
- Fewer database states

**Disadvantages:**
- Cannot distinguish between "has placeholder geometry" and "has no geometry"
- Rendering clients cannot make informed decisions (Do I show the splat or ask the user to wait?)
- Violates Tier semantics (synthetic geometry is Tier 3, not Tier 1 or 2)

**Rejected:** The three-state model is necessary for correct rendering behaviour and Tier hygiene.

---

## Consequences

### Positive

1. **Standardisation:** All rendering clients speak a common format; no format-specific code per engine
2. **Compression:** 10–20× smaller payloads reduce bandwidth costs and improve end-user latency
3. **Ecosystem:** Draco decoders are widely available (WASM, native, GPU-accelerated); no proprietary dependency
4. **Schema clarity:** The bundle schema is a formal contract; clients can validate structure before decode
5. **Gap 1 closed:** No future format churn; architectural decision is stable

### Negative

1. **Encoding workload:** Every geometry ingested must be transcoded to glTF+Draco; ingestion adapters must include transcoding logic
2. **Decode latency:** Draco decoding adds 5ms per geometry blob; must be budgeted into the 100ms target
3. **Storage overhead:** Schema requires per-bundle metadata (bounds, LOD chain, source hash); adds ~500 bytes per bundle
4. **Browser fragmentation:** Draco WASM decoder is fast but requires a polyfill; fallback to uncompressed glTF for older clients (larger payload, slower)

### Implementation Obligations

1. **Pillar 2:** All ingestion adapters must emit glTF 2.0 + Draco L7; schema migration must add `geometry_inferred` boolean and `fidelity_coverage` structure
2. **Pillar 3:** Rendering clients must include Draco decoder (WASM module); must respect `fidelity_coverage.*.status` when deciding whether to render geometry
3. **Schema:** CHECK constraint on `asset_bundles` table enforces `geometry_inferred → splat_pending` atomically
4. **Testing:** Benchmark suite must measure end-to-end latency (registry → glTF → network → decode → render) on reference hardware
5. **Documentation:** Asset bundle API must document fidelity states and client responsibilities (when to show/hide splat geometry)

---

## Review Date

2026-06-15

(Pillar 3 M2 delivery checkpoint; end-to-end latency benchmarks and fallback strategy due)

---

## Appendix: Draco Compression Parameters

Harmony asset bundles use fixed Draco parameters to ensure interoperability:

```
draco_encoder [input.glb] [output.glb]
  --quantization_position 14
  --quantization_normal 10
  --quantization_color 8
  --quantization_generic 8
  --compression_level 7
  --expert_encode
```

All Harmony ingestion adapters must use these parameters. Clients may request lower compression levels for real-time encoding (e.g., client-side measurement upload) via a separate fast-path encoder with level 3–4.
