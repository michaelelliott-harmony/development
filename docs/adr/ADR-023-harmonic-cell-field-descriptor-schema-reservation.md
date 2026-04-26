# ADR-023: Harmonic Cell Field Descriptor Schema Reservation

| Field | Value |
|---|---|
| **Status** | Proposed — requires Dr. Voss acceptance |
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

A new JSONB column `field_descriptors` shall be added to both cell and entity records:

- **Type:** JSONB
- **Nullable:** Yes (DEFAULT NULL)
- **Initial state:** Empty (all records default to NULL)
- **No CHECK constraints:** Validation rules are deferred to the activation ADR

### 2.2 Typed Container Structure

The `field_descriptors` column holds a JSON array of field descriptor objects. Each object is indexed by:

- **`field_type`** — string, identifying the category of physical field. Initial set: `visual_radiance`, `acoustic`, `thermal`, `electromagnetic`. Additional values must be supported without schema migration (forward-compatibility requirement — see Section 2.5).
- **`harmonic_order`** — integer, representing the order of the spherical harmonic or field expansion term.
- **`temporal_index`** — timestamp or integer sequence, enabling time-varying field measurements.

Additional keys within each descriptor object (e.g., `coefficients`, `source`, `confidence`, `basis_function`, `spatial_resolution`) are schema-flexible by nature of JSONB and do not require schema changes.

### 2.3 Example Structure

This example is for documentation only and is not enforced by the schema:

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

### 2.4 Activation Conditions (Documented, Not Enforced)

This ADR reserves the schema space only. The column exists, defaults to NULL, and contains no data. Activation is deferred to a future ADR (ADR-024 or later) that will define:

- **Data sources:** Which systems populate field descriptors and under what conditions
- **Validation rules:** What values are permitted in `coefficients`, `basis_function`, and other keys
- **Write permissions:** Which agents or services have authorization to write to `field_descriptors`
- **Consumer contracts:** Who reads field descriptors, how frequently, and what guarantees they require
- **Temporal semantics:** How time-varying measurements are recorded and queried

Until the activation ADR is accepted, no data shall be written to `field_descriptors`.

### 2.5 Forward-Compatibility Requirement

The schema must support additional `field_type` values beyond the four initial types without requiring a schema migration:

- **Type constraint:** Use a string type for `field_type`, NOT a database enum. String types are schema-flexible; enums require a migration to add new values.
- **No CHECK constraints on `field_type`:** Validation of allowed types is an application-layer concern, defined in the activation ADR. The database enforces only that the column contains valid JSON.
- **JSONB schema flexibility:** New keys within descriptor objects (e.g., `coefficients`, `basis_function`, `spatial_resolution`) do not require schema changes. JSONB columns are schema-agnostic by design.

**Example:** Adding support for `chemical` field type requires no schema migration — the application simply begins writing objects with `"field_type": "chemical"` in the same `field_descriptors` array.

### 2.6 No Data Validation at Schema Layer

This is a reservation, not an enforcement. The database-level constraint is that `field_descriptors` is either NULL (no data) or valid JSON. No CHECK constraints on field content, no type validation for keys, no range checks on `harmonic_order`. All validation rules are deferred to the activation ADR and enforced at the application layer.

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

- **Small cost:** Adding a JSONB column to cells and entities. On small or empty tables, this is negligible. On production tables with millions of rows, this is an offline ALTER TABLE operation (~few seconds per million rows, depending on storage backend). This cost is paid once at deployment; the benefit is avoiding a more expensive migration later.
- **Application-layer validation:** Data validation for field descriptors must be implemented at the application layer, not the database layer. This is acceptable because validation rules will change as HCI Phase 1 technology evolves. Application-layer validation provides flexibility that database constraints do not.

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

---

## 5. Implementation Constraints

1. **ADR-023 must be accepted before any schema changes are written.** This is a hard gate.
2. **The schema migration requires Dr. Voss's approval before execution.** Flag as `requires_approval: true` in session output.
3. **The column is added as NULL DEFAULT.** No data is written until the activation ADR is accepted.
4. **JSONB columns require the `jsonb` type in PostgreSQL.** If using a different database backend, the equivalent schemaless type is acceptable (e.g., JSON in MySQL 5.7+, or a document type in document databases).
5. **Application code must not attempt to write to `field_descriptors` before the activation ADR is accepted.** Enforce this via code review and, ideally, a database trigger that rejects writes outside of the activation window.

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

*ADR-023 — Harmonic Cell Field Descriptor Schema Reservation — Proposed April 26, 2026*
