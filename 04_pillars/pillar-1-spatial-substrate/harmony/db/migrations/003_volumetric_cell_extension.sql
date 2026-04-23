-- Harmony Spatial Operating System — Pillar I — Spatial Substrate
-- Migration 003: Volumetric Cell Extension (Stage 2)
--
-- Schema version: 0.1.3 → 0.2.0
-- Reference: ADR-015 (Adaptive Volumetric Cell Extension, Accepted),
--            ADR-017 (Stage 2 Implementation, Accepted).
--
-- Idempotent, additive, backward compatible.
-- Every Stage 1 row automatically satisfies the new schema because the
-- is_volumetric discriminator defaults to FALSE and all altitude fields
-- are nullable.
--
-- Produced only — NOT EXECUTED.
-- Execution requires Mikey's explicit approval per the Harmony safety policy.
-- Pair this migration with `003_volumetric_cell_extension_down.sql` (below,
-- commented) for reversibility.
--
-- Target: PostgreSQL 14+
-- Date: 2026-04-20

BEGIN;

-- =========================================================================
-- 1. Altitude and vertical subdivision fields on cell_metadata
-- =========================================================================

ALTER TABLE cell_metadata
    ADD COLUMN IF NOT EXISTS is_volumetric              BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE cell_metadata
    ADD COLUMN IF NOT EXISTS altitude_min_m             DOUBLE PRECISION DEFAULT NULL;

ALTER TABLE cell_metadata
    ADD COLUMN IF NOT EXISTS altitude_max_m             DOUBLE PRECISION DEFAULT NULL;

ALTER TABLE cell_metadata
    ADD COLUMN IF NOT EXISTS vertical_subdivision_level INTEGER DEFAULT NULL;

ALTER TABLE cell_metadata
    ADD COLUMN IF NOT EXISTS vertical_parent_cell_id    TEXT DEFAULT NULL
        REFERENCES cell_metadata(cell_id);

ALTER TABLE cell_metadata
    ADD COLUMN IF NOT EXISTS vertical_child_cell_ids    JSONB DEFAULT NULL;

ALTER TABLE cell_metadata
    ADD COLUMN IF NOT EXISTS vertical_adjacent_cell_keys JSONB DEFAULT NULL;

-- =========================================================================
-- 2. CHECK constraints enforcing the surface/volumetric discriminator
--    (wrapped in DO blocks for idempotent re-runs)
-- =========================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_cell_volumetric_has_altitude'
    ) THEN
        ALTER TABLE cell_metadata
            ADD CONSTRAINT ck_cell_volumetric_has_altitude
            CHECK (
                NOT is_volumetric
                OR (altitude_min_m IS NOT NULL AND altitude_max_m IS NOT NULL)
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_cell_surface_null_altitude'
    ) THEN
        ALTER TABLE cell_metadata
            ADD CONSTRAINT ck_cell_surface_null_altitude
            CHECK (
                is_volumetric
                OR (altitude_min_m IS NULL AND altitude_max_m IS NULL)
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_cell_altitude_range_ordered'
    ) THEN
        ALTER TABLE cell_metadata
            ADD CONSTRAINT ck_cell_altitude_range_ordered
            CHECK (
                altitude_min_m IS NULL
                OR altitude_max_m IS NULL
                OR altitude_min_m < altitude_max_m
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_cell_altitude_min_thickness'
    ) THEN
        ALTER TABLE cell_metadata
            ADD CONSTRAINT ck_cell_altitude_min_thickness
            CHECK (
                altitude_min_m IS NULL
                OR altitude_max_m IS NULL
                OR (altitude_max_m - altitude_min_m) >= 0.5
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_cell_altitude_seabed_floor'
    ) THEN
        ALTER TABLE cell_metadata
            ADD CONSTRAINT ck_cell_altitude_seabed_floor
            CHECK (altitude_min_m IS NULL OR altitude_min_m >= -11000.0);
    END IF;
END $$;

-- =========================================================================
-- 3. Replace Stage 1 unique_grid_position constraint with a partial unique
--    index that applies to surface cells only.
--
-- Stage 1 enforced: UNIQUE (cube_face, resolution_level, face_grid_u, face_grid_v)
-- Stage 2 intent:  a single surface cell per grid position, but multiple
--                  volumetric children (altitude bands) are permitted and
--                  share the parent's grid position.
--
-- The new invariant: a grid position is unique among surface cells only.
-- Volumetric cells do not compete for grid uniqueness.
-- =========================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'unique_grid_position'
    ) THEN
        ALTER TABLE cell_metadata DROP CONSTRAINT unique_grid_position;
    END IF;
END $$;

DROP INDEX IF EXISTS idx_cell_unique_surface_grid;
CREATE UNIQUE INDEX idx_cell_unique_surface_grid
    ON cell_metadata (cube_face, resolution_level, face_grid_u, face_grid_v)
    WHERE is_volumetric = FALSE;

-- =========================================================================
-- 4. Indexes
-- =========================================================================

CREATE INDEX IF NOT EXISTS idx_cell_is_volumetric
    ON cell_metadata (is_volumetric);

CREATE INDEX IF NOT EXISTS idx_cell_vertical_parent
    ON cell_metadata (vertical_parent_cell_id)
    WHERE vertical_parent_cell_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_cell_altitude_range
    ON cell_metadata (altitude_min_m, altitude_max_m)
    WHERE is_volumetric = TRUE;

-- =========================================================================
-- 5. Schema version bump
-- =========================================================================

INSERT INTO _schema_metadata (key, value)
VALUES ('schema_version', '0.2.0')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

INSERT INTO _schema_metadata (key, value)
VALUES ('migration_003_applied_at', now()::TEXT)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

COMMIT;

-- =========================================================================
-- DOWN MIGRATION — reverse the Stage 2 changes.
-- Uncomment and execute manually only with Mikey's approval.
-- =========================================================================
--
-- BEGIN;
--
-- ALTER TABLE cell_metadata
--     DROP CONSTRAINT IF EXISTS ck_cell_volumetric_has_altitude,
--     DROP CONSTRAINT IF EXISTS ck_cell_surface_null_altitude,
--     DROP CONSTRAINT IF EXISTS ck_cell_altitude_range_ordered,
--     DROP CONSTRAINT IF EXISTS ck_cell_altitude_min_thickness,
--     DROP CONSTRAINT IF EXISTS ck_cell_altitude_seabed_floor;
--
-- DROP INDEX IF EXISTS idx_cell_altitude_range;
-- DROP INDEX IF EXISTS idx_cell_vertical_parent;
-- DROP INDEX IF EXISTS idx_cell_is_volumetric;
-- DROP INDEX IF EXISTS idx_cell_unique_surface_grid;
--
-- -- Restore the Stage 1 full-uniqueness constraint. Only safe if no
-- -- volumetric cells exist at down-migration time.
-- ALTER TABLE cell_metadata
--     ADD CONSTRAINT unique_grid_position
--     UNIQUE (cube_face, resolution_level, face_grid_u, face_grid_v);
--
-- ALTER TABLE cell_metadata
--     DROP COLUMN IF EXISTS vertical_adjacent_cell_keys,
--     DROP COLUMN IF EXISTS vertical_child_cell_ids,
--     DROP COLUMN IF EXISTS vertical_parent_cell_id,
--     DROP COLUMN IF EXISTS vertical_subdivision_level,
--     DROP COLUMN IF EXISTS altitude_max_m,
--     DROP COLUMN IF EXISTS altitude_min_m,
--     DROP COLUMN IF EXISTS is_volumetric;
--
-- UPDATE _schema_metadata SET value = '0.1.3' WHERE key = 'schema_version';
-- DELETE FROM _schema_metadata WHERE key = 'migration_003_applied_at';
--
-- COMMIT;
