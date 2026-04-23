# Harmony ID Generation Rules

> **Version:** 0.1.3
> **Status:** Locked — Milestone 1 Amendment under Master Spec V1.0
> **Pillar:** 1 — Spatial Substrate
> **Owner:** Builder Agent 1 (rules) · Builder Agent 2 (cell_key) · Builder Agent 4 (entities)
> **Change from v0.1.2:** Cell key regex updated to production 16-char hash form (per Session 2 D3). Resolution table updated from 16 levels to 12 levels (per Session 2 D2). Gate 3 closure referenced in §11.

---

## 1. Purpose

This document defines the deterministic rules for generating every type of identifier in the Harmony system. Any implementation — Python, TypeScript, Rust — that follows these rules must produce identifiers that are interoperable with every other implementation.

If two implementations disagree on how to generate an ID, this document is the tiebreaker.

---

## 2. Canonical ID Format

### 2.1 Universal Properties

All canonical IDs share the following properties:

- **Opaque** — they carry no embedded meaning that consumers may rely on
- **Lowercase** — `[a-z0-9_]` only
- **Stable prefix** — the prefix declares the object type and is part of the ID
- **Collision-resistant** — generated such that the probability of collision within the system lifetime is negligible
- **URL-safe** — usable in path segments without escaping
- **Sortable** — lexicographic sort is acceptable; chronological ordering is not required
- **Federation-compatible** — no embedded operator, region, or jurisdiction information (see ADR-001 federation note)

Canonical IDs are NOT:
- Hashes of the object's content (the object can change; the ID cannot)
- Sequential integers (no shared counter; no leakage of creation order)
- UUIDs (too long for the use case; not human-skimmable)

### 2.2 Cell Canonical ID

```
Format:  hc_<token>
Regex:   ^hc_[a-z0-9]{9}$
Example: hc_4fj9k2x7m
```

- Prefix: `hc_` (Harmony Cell)
- Token: 9 characters from the alphabet `[a-z0-9]` (Crockford-style, see §3)
- Total length: 12 characters

The 9-character token at base-32 yields ~3.5 × 10¹³ possible IDs, sufficient for trillions of cells with negligible collision risk.

### 2.3 Entity Canonical ID

```
Format:  ent_<subtype>_<token>
Regex:   ^ent_[a-z]{3}_[a-z0-9]{6}$
Example: ent_bld_91af82
```

- Prefix: `ent_`
- Subtype: exactly 3 lowercase letters from the registered entity subtypes (see `identity-schema.md` §4.1)
- Token: 6 characters from `[a-z0-9]`
- Total length: 14 characters

### 2.4 Dataset Canonical ID *(reserved)*

```
Format:  ds_<token>
Regex:   ^ds_[a-z0-9]{8}$
```

### 2.5 State Canonical ID *(reserved)*

```
Format:  st_<token>
Regex:   ^st_[a-z0-9]{10}$
```

### 2.6 Contract Anchor ID *(reserved)*

```
Format:  ca_<type>_<token>
Regex:   ^ca_[a-z]{3}_[a-z0-9]{8}$
```

---

## 3. Token Alphabet

The token alphabet is **Crockford Base32** with the following modifications:

- Lowercase only
- Excludes: `i`, `l`, `o`, `u` (visual ambiguity and accidental words)
- Final alphabet: `0123456789abcdefghjkmnpqrstvwxyz` (32 characters)

This guarantees:
- No visual confusion between `1`/`l`, `0`/`o`
- No accidental profanity in generated tokens
- Direct interoperability with Crockford Base32 decoders

---

## 4. Cell Key Format

`cell_key` is fundamentally different from `canonical_id`. It is **deterministic**, **derivable**, and **reproducible**. See ADR-004 for the full rationale.

### 4.1 Format

```
Format:  hsam:r<level>:<region>:<hash>
Regex:   ^hsam:r[0-9]{2}:[a-z0-9]{2,8}:[0-9a-hjkmnp-tv-z]{16}$
Example: hsam:r08:cc:g2f39nh7keq4h9f0
```

| Component | Meaning |
|---|---|
| `hsam` | Harmony Spatial Addressing Model — fixed prefix |
| `r<level>` | Resolution level, two digits, zero-padded (`r00`–`r11`) |
| `<region>` | Short region code (registered, see §4.3) |
| `<hash>` | 16-character deterministic hash of the cell geometry at this resolution |

### 4.2 Derivation Algorithm

Given a cell geometry `G` and resolution level `L`:

1. Snap `G` to the canonical grid for resolution `L` (avoids floating-point drift)
2. Compute the centroid of the snapped geometry in WGS84
3. Look up the `region` code for that centroid (see §4.3)
4. Serialise the snapped geometry as a canonical byte sequence (well-known binary, big-endian)
5. Hash the byte sequence with BLAKE3, take the first 80 bits (10 bytes)
6. Encode those 80 bits as 16 characters using the alphabet from §3
7. Assemble: `hsam:r{L:02d}:{region}:{hash}`

The same `(G, L)` pair MUST always produce the same `cell_key` regardless of which implementation generates it. This is a hard requirement — drift here breaks substrate linkage across the system.

### 4.3 Region Codes

Region codes are short, registered identifiers for major geographic regions. The initial registry is intentionally small:

| Code | Region |
|---|---|
| `cc` | Central Coast (NSW, Australia) — Pillar 1 reference dataset |
| `gbl` | Global / unassigned (fallback only) |

New region codes are added by ADR. The fallback `gbl` exists so the system never fails to produce a `cell_key`, but its use is logged as a warning.

### 4.4 Resolution Levels

| Level | Approx. cell edge | Purpose |
|---|---|---|
| `r00` | Continental (cube face) | Top-level partitions |
| `r02` | ~1000 km | Continent / large region |
| `r04` | ~250 km | Country / state scale |
| `r06` | ~15 km | District / neighbourhood |
| `r08` | ~1 km | Block / suburb |
| `r10` | ~60 m | Parcel / building |
| `r11` | ~15 m | Room / sub-parcel |

The Harmony Cell System has 12 resolution levels (r00–r11). Each level divides the previous level's edge by 4 (16-cell subdivision). Actual cell edge length varies by up to ~2.3× across a face due to gnomonic distortion; the values above are mid-face typical. Every cell registration stores its actual `edge_length_m`.

### 4.5 Cell Key vs Cell ID — When to Use Which

| Situation | Use |
|---|---|
| Storing a reference in another record | `cell_id` |
| Computing a spatial join from raw geometry | `cell_key` |
| Logging or debugging spatial pipelines | `cell_key` |
| API responses to clients | both |
| Sorting or grouping cells in queries | `cell_id` (indexed) |

**Both fields exist on every cell record. Neither is optional.** See ADR-004.

---

## 5. Generation Procedure

### 5.1 Cell ID

```
1. Caller provides geometry G and resolution L
2. Compute cell_key from (G, L)             [deterministic]
3. Check registry for existing cell_key
   3a. If found → return existing canonical_id (idempotent)
   3b. If not found → continue
4. Generate candidate canonical_id (random 9-char token)
5. Check uniqueness against registry
   5a. If collision → regenerate (max 3 attempts)
   5b. If 3 collisions → escalate as system error
6. Insert (canonical_id, cell_key, ...) into registry
7. Return canonical_id
```

Step 3 makes cell registration idempotent: re-registering the same geometry+resolution returns the same canonical ID. This is essential for ingestion pipelines that may re-run.

### 5.2 Entity ID

```
1. Caller provides object_type "entity" and subtype S
2. Validate S is in the registered subtype list
3. Generate candidate token (random 6-char)
4. Assemble: ent_{S}_{token}
5. Check uniqueness against registry
6. On collision: regenerate (max 3 attempts)
7. Insert and return
```

Entity IDs are NOT idempotent against geometry. The same building registered twice produces two entity IDs. Deduplication is the responsibility of the ingestion pipeline (Pillar 2), not the identity layer.

---

## 6. Randomness Source

Token generation MUST use a cryptographically secure random source:

- Python: `secrets.token_bytes`
- TypeScript / Node: `crypto.randomBytes`
- Rust: `rand::rngs::OsRng`

`Math.random()`, `random.random()`, and similar non-CSPRNG sources are forbidden. This is enforced in code review.

---

## 7. Uniqueness and Collision Handling

- Uniqueness is enforced at the database level via a `UNIQUE` constraint on `canonical_id`
- The application layer also checks before insert to surface friendlier errors
- On collision: regenerate up to 3 times, then fail loudly
- Three collisions in a row indicates either an exhausted ID space or a broken RNG — both are P0 incidents

---

## 8. Reserved Tokens

The following tokens are reserved and MUST NOT be generated:

- Any token consisting entirely of the same character (e.g. `000000000`)
- Any token matching `^test`, `^demo`, `^null`, `^none`
- Any token matching the patterns used in this document's examples

Reserved tokens are filtered after generation; if generated, regenerate.

---

## 9. Validation

Every identifier MUST pass regex validation before being accepted by the registry:

```python
PATTERNS = {
    "cell":            r"^hc_[a-z0-9]{9}$",
    "entity":          r"^ent_[a-z]{3}_[a-z0-9]{6}$",
    "dataset":         r"^ds_[a-z0-9]{8}$",
    "state":           r"^st_[a-z0-9]{10}$",
    "contract_anchor": r"^ca_[a-z]{3}_[a-z0-9]{8}$",
    "cell_key":        r"^hsam:r[0-9]{2}:[a-z0-9]{2,8}:[0-9a-hjkmnp-tv-z]{16}$",
}
```

These regexes are the canonical validation source. Any implementation must use them verbatim.

---

## 10. Test Vectors

Implementations of these rules MUST pass the following test vectors. These will be expanded in Milestone 2.

### 10.1 Token Alphabet

```
input: 0
output: '0'
input: 31
output: 'z'
input: 32
output: '10'
```

### 10.2 Cell Key Determinism

```
geometry: <reference polygon CC-A>  (provided in sample-central-coast-records.json)
level:    8
expected: hsam:r08:cc:a91f2
```

A run on any platform must produce the expected `cell_key` byte-for-byte.

---

## 11. Open Items (deferred to later milestones)

These are explicitly NOT decided in v0.1.3:

- The spatial indexing scheme is locked in ADR-002 (gnomonic cube projection, 4×4 subdivision, 12 levels). Metric edge lengths per level are approximate; actual per-cell values are stored in the cell record.
- How region codes are assigned for cells spanning region boundaries
- The migration story if BLAKE3 is ever replaced
- The activation mechanism for the temporal versioning fields reserved in v0.1.2 (see ADR-007)
- The full named-entity resolution flow (see ADR-008 — Pillar 1 supplies primitives only)
- Gate 3 (identity generation order) is closed by ADR-011. The cell / entity / alias registration sequences are formally locked.

Each will require its own ADR.

---

*End of id_generation_rules.md v0.1.3 — locked*
