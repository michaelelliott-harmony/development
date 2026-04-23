# id_generation_rules.md — v0.1.3 Patch Notes

> **Purpose:** This file lists the specific edits to apply to the v0.1.2 `id_generation_rules.md` to bring it to v0.1.3. A full replacement file is not issued because the changes are targeted.
>
> **Apply these edits to:** `id_generation_rules.md` in your project.
> **Resulting version:** 0.1.3

---

## Edit 1 — Header Version Bump

Change:
```
> **Version:** 0.1.2
```
To:
```
> **Version:** 0.1.3
> **Change from v0.1.2:** Cell key regex updated to production 16-char hash form (per Session 2 D3). Resolution table updated from 16 levels to 12 levels (per Session 2 D2). Gate 3 closure referenced in §11.
```

---

## Edit 2 — §4.1 Cell Key Regex

Replace the entire §4.1 regex line:
```
Regex:   ^hsam:r[0-9]{2}:[a-z0-9]{2,8}:[a-z0-9]{5}$
```

With:
```
Regex:   ^hsam:r[0-9]{2}:[a-z0-9]{2,8}:[0-9a-hjkmnp-tv-z]{16}$
```

Update the example to match production form:
```
Example: hsam:r08:cc:g2f39nh7keq4h9f0
```

Note: the hash alphabet is Crockford Base32 minus `i`, `l`, `o`, `u` (per §3).

---

## Edit 3 — §4.2 Derivation Algorithm

In step 5, change:
```
5. Hash the byte sequence with BLAKE3, take the first 25 bits
6. Encode those 25 bits as 5 characters using the alphabet from §3
```

To:
```
5. Hash the byte sequence with BLAKE3, take the first 80 bits (10 bytes)
6. Encode those 80 bits as 16 characters using the alphabet from §3
```

Rationale: at Level 12 for Central Coast alone (~2.9 billion cells), 25-bit keys would collide with near-certainty. 80 bits brings birthday-bound collision to ~3.5 × 10⁻⁶. See Session 2 D3.

---

## Edit 4 — §4.4 Resolution Levels Table

Replace the resolution table with:

| Level | Approx. cell edge | Purpose |
|---|---|---|
| `r00` | Continental (cube face) | Top-level partitions |
| `r02` | ~1000 km | Continent / large region |
| `r04` | ~250 km | Country / state scale |
| `r06` | ~15 km | District / neighbourhood |
| `r08` | ~1 km | Block / suburb |
| `r10` | ~60 m | Parcel / building |
| `r11` | ~15 m | Room / sub-parcel |

Append the note: *"The Harmony Cell System has 12 resolution levels (r00–r11). Each level divides the previous level's edge by 4 (16-cell subdivision). Actual cell edge length varies by up to ~2.3× across a face due to gnomonic distortion; the values above are mid-face typical. Every cell registration stores its actual `edge_length_m`."*

---

## Edit 5 — §9 Validation Patterns

Update the `cell_key` pattern:

```python
"cell_key":        r"^hsam:r[0-9]{2}:[a-z0-9]{2,8}:[0-9a-hjkmnp-tv-z]{16}$",
```

Also update resolution level maximum in the cell regex comment: levels are 0–11, not 0–15.

---

## Edit 6 — §11 Open Items

Update the first bullet to reference ADR-002 and the gnomonic commitment:

- Remove: *"The exact spatial indexing scheme that defines the canonical grid (Pillar 1, later milestone — affected by Pillar 3 framework decision...)"*
- Replace with: *"The spatial indexing scheme is locked in ADR-002 (gnomonic cube projection, 4×4 subdivision, 12 levels). Metric edge lengths per level are approximate; actual per-cell values are stored in the cell record."*

Add new closing bullet:
- *"Gate 3 (identity generation order) is closed by ADR-011. The cell / entity / alias registration sequences are formally locked."*

---

## Edit 7 — ADR Cross-References

Throughout the document, update any ADR references to use the canonical sequence:

- Any reference to "ADR-009" (temporal) → "ADR-007"
- Any reference to "ADR-010" (named-entity) → "ADR-008"

See `ADR_INDEX.md` for the full rename map.

---

*End of patch notes — apply these edits to produce id_generation_rules.md v0.1.3*
