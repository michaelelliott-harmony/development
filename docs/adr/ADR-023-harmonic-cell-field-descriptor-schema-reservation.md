# ADR-023: Harmonic Cell Field Descriptor Schema Reservation

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | April 26, 2026 |
| **Author** | Jessica Grace Luis (ADR Agent) |
| **Supersedes** | None |
| **Related ADRs** | ADR-010 (Spatial Geometry Schema Extension), ADR-016 (Temporal Trigger Architecture — fidelity_coverage precedent) |
| **Pillar** | Cross-pillar — affects Pillar 1 schema, consumed by Pillars 2–5 |
| **Approval Required** | Yes — Dr. Mara Voss must accept before any schema changes |

---

## 1. Context

The Harmonic Cell Initiative (HCI) introduces field-based spatial descriptors — mathematical representations of continuous physical properties (light, sound, heat, electromagnetic fields) within Harmony Cells. These descriptors extend the cell model beyond geometric boundaries into the physics of the space itself.

Before HCI Phase 1 technology conditions are met and validated, the schema must reserve space for field descriptors without activating data writes. This follows the same pattern established by ADR-007 (bitemporal field reservation) and ADR-016 (fidelity_coverage activation) — reserve the schema space early, activate it when the technology and architecture are ready.

---

## 2. Decision

### 2.1 Reserved Field Definition

A new JSONB column `field_descriptors` shall be added to `cell_metadata` records only:

- **Type:** JSONB
- **Nullable:** Yes (DEFAULT NULL)
- **Initial state:** Empty (all records default to NULL)
- **Schema enforcement:** Application-layer validation only (see Section 2.2); database enforces valid JSON only

### 2.2 JSON Schema Contract

The `field_descriptors` column holds a JSON array of field descriptor objects. This ADR defines a typed contract (enforced at the application layer, not the database) that governs the structure:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["field_type", "harmonic_order", "temporal_index"],
    "properties": {
      "field_type": {
        "type": "string",
        "description": "Physical field category. Initial set: visual_radiance, acoustic, thermal, electromagnetic. Additional values permitted without schema migration.",
        "enum_documentation": [
          "visual_radiance — spherical harmonic decomposition of light field intensity and chrominance",
          "acoustic — spherical harmonic decomposition of sound pressure levels and frequency distribution",
          "thermal — scalar or low-order harmonic decomposition of temperature distribution",
          "electromagnetic — spherical harmonic decomposition of RF field strength and polarisation"
        ]
      },
      "harmonic_order": {
        "type": "integer",
        "minimum": 0,
        "description": "Order of the spherical harmonic expansion. 0 = omnidirectional (scalar), 1 = first-order (dipole), 2+ = higher-order directional resolution. Maximum useful order is sensor-dependent and defined in the activation ADR."
      },
      "temporal_index": {
        "oneOf": [
          {"type": "string", "format": "date-time"},
          {"type": "integer", "minimum": 0}
        ],
        "description": "Time reference for this measurement. ISO 8601 timestamp for absolute time, or integer sequence index for relative ordering within a measurement series."
      },
      "coefficients": {
        "type": "array",
        "items": {"type": "number"},
        "description": "Spherical harmonic coefficients for this field_type at this order. Array length = (2 * harmonic_order + 1). Coefficient ordering convention defined in the activation ADR."
      },
      "source": {
        "type": "string",
        "description": "Identifier of the sensor, model, or process that produced this measurement."
      },
      "confidence": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "description": "Confidence score for this measurement. 1.0 = direct sensor measurement, lower values for modelled or inferred data."
      }
    },
    "additionalProperties": true
  }
}
```

**Composite key:** Within a cell's `field_descriptors`, the tuple `(field_type, harmonic_order, temporal_index)` uniquely identifies a measurement. Together they specify:
- **field_type:** WHAT physical property is described
- **harmonic_order:** At what RESOLUTION the decomposition is made
- **temporal_index:** WHEN the measurement was taken

### 2.3 Example Structure

This example is for documentation only and instantiates the JSON Schema:

```json
{
  "field_descriptors": [
    {
      "field_type": "visual_radiance",
      "harmonic_order": 2,
      "temporal_index": "2026-04-26T12:00:00Z",
      "coefficients": [0.42, 0.18, -0.07, 0.31, 0.09],
      "source": "hci_sensor_array",
      "confidence": 0.92
    },
    {
      "field_type": "acoustic",
      "harmonic_order": 1,
      "temporal_index": "2026-04-26T12:00:00Z",
      "coefficients": [0.15, 0.08, 0.22],
      "source": "environmental_monitoring",
      "confidence": 0.87
    }
  ]
}
```

### 2.4 Scope: Cell Metadata Only

The `field_descriptors` reservation is scoped to `cell_metadata` records exclusively. Field descriptors describe the physical state of a bounded spatial region (a cell), not the properties of named objects (entities).

Justification: The spherical harmonic decomposition represents the ambient physical field within a cell's spatial bounds. This is an intrinsic property of the cell itself, not an attribute of entities that may occupy the cell.

### 2.5 Activation Conditions (Documented, Not Enforced)

This ADR reserves the schema space only. The column exists, defaults to NULL, and contains no data. Activation is deferred to a future ADR (ADR-024 or later) that will define:

- **Data sources:** Which systems populate field descriptors and under what conditions
- **Validation rules:** Application-layer enforcement of the JSON Schema contract (Section 2.2)
- **Write permissions:** Which agents or services have authorization to write to `field_descriptors`
- **Consumer contracts:** Who reads field descriptors, how frequently, and what guarantees they require
- **Temporal semantics:** How time-varying measurements are recorded and queried

Until the activation ADR is accepted, no data shall be written to `field_descriptors`.

**Gap 8 Anchor:** Activation is contingent on closure of Gap 8 (Harmonic Cell Field Sensing Architecture) in the Harmony Gap Register. Gap 8 was proposed by Dr. Kofi Boateng in the HCI programme (formally deferred) and should be added to the gap register in the next master specification revision (V1.1 or V2.0). The activation ADR must reference Gap 8 closure as a prerequisite, providing a formal architectural anchor rather than a dependency on external technology milestones the project does not control.

### 2.6 Forward-Compatibility Requirement

The schema must support additional `field_type` values beyond the four initial types without requiring a schema migration:

- **Type constraint:** Use a string type for `field_type`, NOT a database enum. String types are schema-flexible; enums require a migration to add new values.
- **No CHECK constraints on `field_type`:** The JSON Schema (Section 2.2) documents the initial set but does not enforce it via database constraints. Validation of allowed types is an application-layer concern, defined in the activation ADR. The database enforces only that the column contains valid JSON.
- **JSONB schema flexibility:** New keys within descriptor objects (e.g., `basis_function`, `spatial_resolution`, application-specific fields) do not require schema changes. JSONB columns are schema-agnostic by design. The JSON Schema is defined now; application code enforces it.

**Example:** Adding support for `chemical` field type requires no schema migration — the application activation ADR will update validation rules, and the application simply begins writing objects with `"field_type": "chemical"` in the same `field_descriptors` array.

### 2.7 Database-Layer Constraints (Minimal)

This is a reservation, not an enforcement. The database-level constraint is that `field_descriptors` is either NULL (no data) or valid JSON. No CHECK constraints on field content, no type validation for keys, no range checks on `harmonic_order`. All structured validation rules are defined in the JSON Schema (Section 2.2) and enforced at the application layer, which provides flexibility as HCI Phase 1 technology evolves.

---

## 3. Consequences

### What This Enables

- **HCI Phase 1 activation without schema migration:** When HCI Phase 1 technology is validated and ready, the activation ADR will define data sources and write rules. The column already exists — activation requires an ADR and application code, not a database migration.
- **Documented design intent:** The four initial field types (`visual_radiance`, `acoustic`, `thermal`, `electromagnetic`) are documented as the design intent without being locked into the schema.
- **Future field types without migration:** When new field types are needed (e.g., `chemical`, `gravitational`, `magnetic`), they are added at the application layer. No schema change required.
- **Follows proven pattern:** ADR-007 reserved bitemporal fields, ADR-016 activated them. ADR-023 reserves field descriptors; a future ADR activates them. This pattern de-risks architectural changes by separating reservation from activation.

### What This Does Not Do

- Does not define data sources for field descriptors (deferred to activation ADR)
- Does not define validation rules for field content (deferred to activation ADR)
- Does not define consumer contracts — who reads field descriptors and what guarantees they require (deferred to activation ADR)
- Does not activate any data writes (column remains NULL until activation ADR is accepted)
- Does not create CHECK constraints (validation is application-layer responsibility)
- Does not define spherical harmonic basis functions or coefficient encoding — that is HCI Phase 1 technical work

### Cost Trade-Offs

- **Small cost:** Adding a JSONB column to cell_metadata. On small or empty tables, this is negligible. On production tables with millions of rows, this is an offline ALTER TABLE operation (~few seconds per million rows, depending on storage backend). This cost is paid once at deployment; the benefit is avoiding a more expensive migration later.
- **Application-layer validation:** Data validation for field descriptors must be implemented at the application layer, enforcing the JSON Schema (Section 2.2). This is acceptable because validation rules will change as HCI Phase 1 technology evolves. Application-layer validation provides flexibility that database constraints do not.

---

## 3.1 Architectural Compatibility Validation (V4)

**Validated by:** Dr. Mara Voss, Principal Architect  
**Date:** April 27, 2026

**V4: Is the reserved field_descriptors field architecturally compatible with the existing cell schema?**

**Answer:** Yes, in principle. A nullable JSONB column with DEFAULT NULL on cell_metadata does not conflict with schema v0.2.0. It does not interfere with the Pillar 1 identity model, the volumetric cell extension, the bitemporal reservation, or any Pillar 2 ingestion path.

The reservation is architecturally compatible — provided:

1. The container carries a defined JSON Schema contract (addressed in Section 2.2)
2. The scope is limited to cell_metadata only unless entity-level justification is provided and documented (addressed in Section 2.4)

This validation is conditional on the ADR being properly drafted with these two provisions met. Both are now addressed in this revision.

**Note:** Dr. Voss's V4 answer should be logged as a DEC entry in the Decision Log by Marcus Webb once the ADR is accepted. It is conditional on acceptance — do not log before then.

---

## 4. Alternatives Considered

### Alternative A: Wait Until HCI Phase 1 Is Ready

Defer schema reservation until the activation ADR is drafted and ready to be accepted.

**Rejected:** Adding a JSONB column to a table with millions of rows is an expensive migration. If the table is empty or small when the column is added, the cost is negligible. Harmony's production cells table is currently small; the cost-benefit is favorable now. Waiting until Phase 1 is complete moves the cost to a time when the table is larger and the system is under operational load.

### Alternative B: Use a Separate Table for Field Descriptors

Instead of a JSONB column on the cell record, create a separate `cell_field_descriptors` table with a foreign key to cells.

**Deferred, not rejected:** A separate table may be the right architectural choice once query patterns are known (e.g., if field descriptors are frequently joined with cells, or frequently queried independently). The JSONB column is a reservation strategy that preserves the option to migrate to a separate table later. The activation ADR can evaluate both approaches based on operational data and choose accordingly. The reservation doesn't foreclose the separate-table option.

### Alternative C: Use a Database Enum for `field_type`

Define `field_type` as a PostgreSQL ENUM type instead of a string.

**Rejected:** Adding new enum values requires an ALTER TYPE statement, which is a schema migration (albeit faster than a full table migration). A string field with application-layer validation is more flexible and aligns with the forward-compatibility requirement. Enums are optimized for fixed, rarely-changing categories; field types may evolve as HCI matures.

### Alternative D: Entity-Level Field Descriptors

Reserve `field_descriptors` on entity records in addition to cell_metadata.

**Rejected (unless new justification provided):** Field descriptors as defined in this ADR describe the ambient physical state of a bounded spatial region (a cell). They are not attributes of named objects (entities). If entity-level acoustic or thermal signatures are required — e.g., per-building noise profiles distinct from ambient cell acoustics, or per-vehicle thermal emissions — a separate ADR should be drafted with architectural justification from Dr. Kofi Boateng (Knowledge Layer). This reservation does not foreclose that option; a future ADR can define entity-level field descriptors independently.

---

## 5. Implementation Constraints

1. **ADR-023 must be accepted before any schema changes are written.** This is a hard gate.
2. **The schema migration requires Dr. Voss's approval before execution.** Flag as `requires_approval: true` in session output.
3. **The column is added to `cell_metadata` as NULL DEFAULT.** No data is written until the activation ADR is accepted.
4. **JSON Schema enforcement is application-layer responsibility.** The JSON Schema (Section 2.2) is the contract; application code enforces it. The database ensures only that the column contains valid JSON.
5. **JSONB columns require the `jsonb` type in PostgreSQL.** If using a different database backend, the equivalent schemaless type is acceptable (e.g., JSON in MySQL 5.7+, or a document type in document databases).
6. **Application code must not attempt to write to `field_descriptors` before the activation ADR is accepted.** Enforce this via code review and, ideally, a database trigger that rejects writes outside of the activation window.

---

## 6. Related Decisions

- **ADR-007 (Temporal Versioning Model):** Established the pattern of reserving schema space for features that are not yet activated. The bitemporal fields (`valid_from`, `valid_to`, `version_of`, `temporal_status`) exist in the schema but were not populated until ADR-016 defined activation.
- **ADR-016 (Temporal Trigger Architecture):** Activated bitemporal fields via fidelity_coverage precedent. `field_descriptors` follows the same pattern: reserve early, activate later.
- **ADR-010 (Spatial Geometry Schema Extension):** Extended the cell schema to include geometric properties. Field descriptors extend the model further into physics properties.

---

## 7. Review Date

This ADR should be reviewed when:

- HCI Phase 1 technology validation is complete and the activation ADR is drafted
- Query patterns for field descriptors are known
- A decision is made to migrate from JSONB column to a separate table (if performance data indicates it)

---

*ADR-023 — Harmonic Cell Field Descriptor Schema Reservation — Accepted April 29, 2026*
