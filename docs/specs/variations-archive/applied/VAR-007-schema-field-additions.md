# VAR-007 — Schema Field Additions v0.1.2
> Harmony Variation File | Status: APPLIED
> Raised: 2026-04-13 | Applied: 2026-04-13

---

## Header

| Field | Value |
|---|---|
| **VAR ID** | VAR-007 |
| **Status** | `APPLIED` |
| **Priority** | `STANDARD` |
| **Raised by** | Mikey |
| **Date raised** | 2026-04-13 |
| **Date applied** | 2026-04-13 |
| **Applied in version** | V1.0.1 |
| **Related ADR** | Multiple ADRs (cross-reference) |
| **Raised in chat** | Pillar 1 Spatial Substrate build sessions, April 2026 |

---

## Decision Summary

The cell and entity record schemas have been expanded significantly in v0.1.2. Cell records now include: canonical_id, cell_key, human_alias, alias_namespace, friendly_name, known_names (reserved, indexed), semantic_labels, valid_from/valid_to (reserved), version_of (reserved), temporal_status (reserved), fidelity_coverage (reserved for Pillar 2), lod_availability (reserved for Pillar 2), asset_bundle_count (reserved for Pillar 2), references.asset_bundles (reserved for Pillar 2). Entity records include: canonical_id with embedded subtype, entity_subtype, human_alias/alias_namespace, friendly_name, known_names (reserved), semantic_labels, temporal fields (reserved), references.primary_cell_id, references.secondary_cell_ids.

---

## Sections Affected in Master Spec

- Pillar I — Spatial Substrate (Technical Specifications / Identity System)

---

## Change Detail

### Pillar I — Spatial Substrate (Technical Specifications / Identity System)

**Current text:**
```
V1.0 describes identity at a conceptual level with a basic table.
```

**Add/Replace:**
```
For the current field-level schema, see the Pillar 1 cell and entity identity schemas (v0.1.2). Fields are categorised as Active (in use), Reserved (schema-present, awaiting activation by the owning pillar), or Indexed (maintained by one pillar, consumed by another).

Cell record schema (v0.1.2):
- Active: canonical_id, cell_key, human_alias, alias_namespace, friendly_name, references.asset_bundles
- Reserved/Indexed: known_names, semantic_labels, valid_from, valid_to, version_of, temporal_status, fidelity_coverage, lod_availability, asset_bundle_count

Entity record schema (v0.1.2):
- Active: canonical_id, entity_subtype, human_alias, alias_namespace, friendly_name, references.primary_cell_id, references.secondary_cell_ids
- Reserved/Indexed: known_names, semantic_labels, temporal fields (valid_from, valid_to, version_of, temporal_status)
```

**Reason for change:**
V1.0's identity table is now significantly out of date relative to the implemented schema.

---

## Conflicts or Dependencies

- [ ] Reserved fields for Pillar 2 and Pillar 4 are schema-present but inert — those pillars must activate them.

---

## Open Questions (if any)

- [ ] None

---

## Changelog

| Date | Action | Notes |
|---|---|---|
| 2026-04-13 | Created | Extracted from Pillar 1 variations document |
