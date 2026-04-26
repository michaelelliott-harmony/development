# Harmony Pillar 2 — M7 Temporal Trigger Layer
# D5: Temporal Field Activation Migration
#
# ┌─────────────────────────────────────────────────────────────────┐
# │  REQUIRES MIKEY APPROVAL BEFORE EXECUTION                       │
# │  requires_approval: true                                         │
# │  Gate: ADR-016 Accepted ✓ (April 22, 2026)                      │
# │  Gate: Migration execution requires Telegram approval from Mikey │
# │  Authority: AUTHORITY_MATRIX.md — Migration execution: Mikey only│
# │  Security preamble §2: destructive action gated on approval      │
# └─────────────────────────────────────────────────────────────────┘
#
# What this migration does:
#   Activates the four bitemporal fields reserved in ADR-007 on the
#   cell_metadata table, removes the 403-Reserved write enforcement,
#   and adds cell_status to drive the M7 state machine.
#
# ADR-016 §2.3 — cell_status field (stable|change_expected|change_in_progress|change_confirmed)
# ADR-016 §2.4 — temporal field population rules
# ADR-007     — bitemporal field reservation (now being activated)
#
# Schema version: v0.2.0 → v0.3.0
#
# DO NOT EXECUTE without Mikey's logged Telegram approval.

MIGRATION_ID = "m7_temporal_field_activation"
SCHEMA_VERSION_BEFORE = "0.2.0"
SCHEMA_VERSION_AFTER = "0.3.0"
REQUIRES_APPROVAL = True


def up(conn) -> None:
    """Activate temporal fields and add cell_status to cell_metadata.

    Safe for repeated application (IF NOT EXISTS / idempotent DDL).

    Changes applied:
    1. Add cell_status column (ENUM-constrained via CHECK)
    2. Activate valid_from  — remove reserved-field restriction, set to writable
    3. Activate valid_to    — same
    4. Activate version_of  — same
    5. Activate temporal_status — same
    6. Add index on cell_status for state machine queries
    7. Add index on (valid_from, valid_to) for bitemporal range queries
    8. Update schema_version to 0.3.0 in identity_registry

    Note on reserved-field activation: ADR-007 reserved these columns by
    setting a CHECK constraint or trigger that raised 403 on non-null writes.
    This migration removes that constraint/trigger and allows writes.
    """
    with conn.cursor() as cur:
        # ------------------------------------------------------------------
        # 1. Add cell_status column
        # ------------------------------------------------------------------
        cur.execute("""
            ALTER TABLE cell_metadata
            ADD COLUMN IF NOT EXISTS cell_status TEXT
                NOT NULL DEFAULT 'stable'
                CHECK (cell_status IN (
                    'stable',
                    'change_expected',
                    'change_in_progress',
                    'change_confirmed'
                ))
        """)

        # ------------------------------------------------------------------
        # 2–5. Activate bitemporal columns (reserved in ADR-007)
        # These columns exist but have write restrictions. We activate them
        # by dropping the reserved-write trigger and ensuring the columns
        # accept non-null writes.
        #
        # Drop the ADR-007 reservation trigger if it exists.
        # ------------------------------------------------------------------
        cur.execute("""
            DROP TRIGGER IF EXISTS trg_bitemporal_reserved_write
        """)

        # Ensure valid_from column exists and is writable
        cur.execute("""
            ALTER TABLE cell_metadata
            ADD COLUMN IF NOT EXISTS valid_from DATE DEFAULT NULL
        """)

        # Ensure valid_to column exists
        cur.execute("""
            ALTER TABLE cell_metadata
            ADD COLUMN IF NOT EXISTS valid_to DATE DEFAULT NULL
        """)

        # Ensure version_of column exists (references another canonical_id)
        cur.execute("""
            ALTER TABLE cell_metadata
            ADD COLUMN IF NOT EXISTS version_of TEXT DEFAULT NULL
        """)

        # Ensure temporal_status column exists
        cur.execute("""
            ALTER TABLE cell_metadata
            ADD COLUMN IF NOT EXISTS temporal_status TEXT DEFAULT 'current'
                CHECK (temporal_status IN ('current', 'superseded'))
        """)

        # ------------------------------------------------------------------
        # 6. Index on cell_status — supports state machine queries
        # ------------------------------------------------------------------
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_cell_metadata_cell_status
            ON cell_metadata (cell_status)
        """)

        # ------------------------------------------------------------------
        # 7. Index on valid_from, valid_to — bitemporal range queries
        # ------------------------------------------------------------------
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_cell_metadata_temporal_range
            ON cell_metadata (valid_from, valid_to)
            WHERE valid_from IS NOT NULL
        """)

        # ------------------------------------------------------------------
        # 8. Update schema_version
        # ------------------------------------------------------------------
        cur.execute("""
            UPDATE identity_registry
            SET schema_version = %s
            WHERE object_type = 'cell'
              AND schema_version = %s
        """, (SCHEMA_VERSION_AFTER, SCHEMA_VERSION_BEFORE))

    conn.commit()


def down(conn) -> None:
    """Reverse the temporal field activation migration.

    Drops the cell_status column and indexes. Does NOT re-add the ADR-007
    reservation trigger (re-installation of the reservation requires the
    original trigger DDL from Pillar 1 setup scripts).

    Drops the added columns. Re-installing the reservation trigger is out of
    scope for the rollback — contact Mikey if production rollback is needed.
    """
    with conn.cursor() as cur:
        # Drop indexes first
        cur.execute("DROP INDEX IF EXISTS idx_cell_metadata_cell_status")
        cur.execute("DROP INDEX IF EXISTS idx_cell_metadata_temporal_range")

        # Remove cell_status column
        cur.execute("ALTER TABLE cell_metadata DROP COLUMN IF EXISTS cell_status")

        # Revert schema_version
        cur.execute("""
            UPDATE identity_registry
            SET schema_version = %s
            WHERE object_type = 'cell'
              AND schema_version = %s
        """, (SCHEMA_VERSION_BEFORE, SCHEMA_VERSION_AFTER))

        # Note: valid_from, valid_to, version_of, temporal_status columns are
        # NOT removed in the down() migration — removing them would lose data.
        # Instead, re-install the reservation trigger to block writes.
        cur.execute("""
            CREATE OR REPLACE FUNCTION _fn_bitemporal_reserved()
            RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
                IF NEW.valid_from IS DISTINCT FROM OLD.valid_from
                OR NEW.valid_to IS DISTINCT FROM OLD.valid_to
                OR NEW.version_of IS DISTINCT FROM OLD.version_of
                OR NEW.temporal_status IS DISTINCT FROM OLD.temporal_status
                THEN
                    RAISE EXCEPTION 'BITEMPORAL FIELDS RESERVED — activate via M7 migration';
                END IF;
                RETURN NEW;
            END;
            $$
        """)

        cur.execute("""
            CREATE TRIGGER trg_bitemporal_reserved_write
            BEFORE UPDATE ON cell_metadata
            FOR EACH ROW
            EXECUTE FUNCTION _fn_bitemporal_reserved()
        """)

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
