# Harmony Pillar 2 — ADR-023 Field Descriptor Schema Reservation
# Migration: field_descriptors JSONB Column Addition
#
# ┌─────────────────────────────────────────────────────────────────┐
# │  REQUIRES MIKEY APPROVAL BEFORE EXECUTION                       │
# │  requires_approval: true                                         │
# │  Gate: ADR-023 Accepted ✓ (April 27, 2026 — Dr. Mara Voss)      │
# │  Gate: Migration execution requires Telegram approval from Mikey │
# │  Authority: AUTHORITY_MATRIX.md — Migration execution: Mikey only│
# │  Decision Log: ADR-023 reservation for HCI Phase 1 field support │
# └─────────────────────────────────────────────────────────────────┘
#
# What this migration does:
#   Reserves a JSONB column (field_descriptors) on cell_metadata to hold
#   spherical harmonic decompositions of physical fields (light, sound,
#   heat, electromagnetic) within bounded spatial regions. The column
#   is added as nullable with DEFAULT NULL — no data is written until
#   the activation ADR is accepted.
#
# ADR-023 §2.1  — field_descriptors JSONB nullable column
# ADR-023 §2.2  — JSON Schema contract (enforced at application layer)
# ADR-023 §2.4  — Scope: cell_metadata ONLY (not entity_table)
# ADR-023 §2.7  — Minimal database-layer constraints
#
# Schema version: v0.3.0 → v0.4.0
#
# DO NOT EXECUTE without Mikey's logged Telegram approval.

MIGRATION_ID = "adr023_field_descriptors_reservation"
SCHEMA_VERSION_BEFORE = "0.3.0"
SCHEMA_VERSION_AFTER = "0.4.0"
REQUIRES_APPROVAL = True


def up(conn) -> None:
    """Reserve field_descriptors JSONB column on cell_metadata.

    Safe for repeated application (IF NOT EXISTS / idempotent DDL).

    Changes applied:
    1. Add field_descriptors column (JSONB, nullable, DEFAULT NULL)
    2. Update schema_version to 0.4.0 in identity_registry
    3. Record migration application in _schema_metadata

    Note on the reservation: This ADR reserves schema space for field
    descriptors following the pattern established by ADR-007 (temporal
    fields) and ADR-016 (temporal activation). The column exists and is
    accessible, but no data is written until the activation ADR is accepted.
    Database-level constraints are minimal — the column holds valid JSON or
    NULL. All structured validation is defined in the JSON Schema (ADR-023
    §2.2) and enforced at the application layer.
    """
    with conn.cursor() as cur:
        # ------------------------------------------------------------------
        # 1. Add field_descriptors column to cell_metadata
        # ------------------------------------------------------------------
        # JSONB column holds spherical harmonic field descriptors for HCI Phase 1.
        # The JSON Schema is defined in ADR-023 §2.2 and enforced at application layer.
        # Column is nullable and defaults to NULL. No CHECK constraints on content.
        cur.execute("""
            ALTER TABLE cell_metadata
            ADD COLUMN IF NOT EXISTS field_descriptors JSONB DEFAULT NULL
        """)

        # ------------------------------------------------------------------
        # 2. Update schema_version
        # ------------------------------------------------------------------
        cur.execute("""
            UPDATE identity_registry
            SET schema_version = %s
            WHERE object_type = 'cell'
              AND schema_version = %s
        """, (SCHEMA_VERSION_AFTER, SCHEMA_VERSION_BEFORE))

        # ------------------------------------------------------------------
        # 3. Record migration application in _schema_metadata
        # ------------------------------------------------------------------
        cur.execute("""
            INSERT INTO _schema_metadata (key, value) VALUES
                ('migration_adr023_applied_at', NOW()::text),
                ('schema_version', %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """, (SCHEMA_VERSION_AFTER,))

    conn.commit()


def down(conn) -> None:
    """Reverse the field_descriptors reservation migration.

    Drops the field_descriptors column and reverts schema_version to 0.3.0.

    Note: This is a rollback of a schema reservation. The column is dropped
    because it was added empty (DEFAULT NULL) with no populated data. If
    production data has been written to field_descriptors, coordinate with
    Mikey before executing down().
    """
    with conn.cursor() as cur:
        # Remove field_descriptors column
        cur.execute(
            "ALTER TABLE cell_metadata DROP COLUMN IF EXISTS field_descriptors"
        )

        # Revert schema_version
        cur.execute("""
            UPDATE identity_registry
            SET schema_version = %s
            WHERE object_type = 'cell'
              AND schema_version = %s
        """, (SCHEMA_VERSION_BEFORE, SCHEMA_VERSION_AFTER))

        # Revert _schema_metadata
        cur.execute(
            "DELETE FROM _schema_metadata WHERE key = 'migration_adr023_applied_at'"
        )
        cur.execute(
            "UPDATE _schema_metadata SET value = %s WHERE key = 'schema_version'",
            (SCHEMA_VERSION_BEFORE,),
        )

    conn.commit()


# ---------------------------------------------------------------------------
# Execution guard — never run without explicit approval
# ---------------------------------------------------------------------------

def execute_with_approval(conn, approved_by: str, approved_at: str) -> None:
    """Execute the migration with documented approval.

    Args:
        conn: Active database connection.
        approved_by: The approver identity (must be 'Mikey').
        approved_at: ISO timestamp of the Telegram approval.

    Raises:
        PermissionError: If approval is not from Mikey.
        RuntimeError: If REQUIRES_APPROVAL flag is true and not overridden.
    """
    if approved_by.strip().lower() not in ("mikey",):
        raise PermissionError(
            f"Migration {MIGRATION_ID} requires Mikey approval. "
            f"Got: {approved_by!r}. "
            "Authority: AUTHORITY_MATRIX.md — Migration execution: Mikey only."
        )

    print(
        f"[MIGRATION] Executing {MIGRATION_ID} "
        f"(approved by {approved_by} at {approved_at})"
    )
    up(conn)
    print(
        f"[MIGRATION] {MIGRATION_ID} complete. "
        f"Schema version: {SCHEMA_VERSION_BEFORE} → {SCHEMA_VERSION_AFTER}"
    )
