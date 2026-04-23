-- Harmony Spatial Operating System — Pillar I — Spatial Substrate
-- Migration 001: Initial Schema
--
-- Idempotent migration — safe to re-run. Uses IF NOT EXISTS on all
-- CREATE statements and DO blocks for conditional operations.
--
-- Target: PostgreSQL 14+
-- Schema version: 0.1.3
-- Reference: identity_registry_schema.sql

BEGIN;

-- =========================================================================
-- 1. Tables
-- =========================================================================

CREATE TABLE IF NOT EXISTS identity_registry (
    canonical_id    TEXT        PRIMARY KEY,
    object_type     TEXT        NOT NULL CHECK (object_type IN ('cell', 'entity', 'dataset', 'state', 'contract_anchor')),
    object_domain   TEXT        NOT NULL,
    status          TEXT        NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'deprecated', 'retired')),
    schema_version  TEXT        NOT NULL DEFAULT '0.1.3',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_from      TIMESTAMPTZ,
    valid_to        TIMESTAMPTZ,
    version_of      TEXT        REFERENCES identity_registry(canonical_id),
    temporal_status TEXT        CHECK (temporal_status IN ('current', 'historical', 'superseded', 'projected'))
);

CREATE TABLE IF NOT EXISTS cell_metadata (
    cell_id             TEXT        PRIMARY KEY REFERENCES identity_registry(canonical_id),
    cell_key            TEXT        NOT NULL UNIQUE,
    resolution_level    INT         NOT NULL CHECK (resolution_level >= 0 AND resolution_level <= 12),
    parent_cell_id      TEXT        REFERENCES cell_metadata(cell_id),
    cube_face           INT         NOT NULL CHECK (cube_face >= 0 AND cube_face <= 5),
    face_grid_u         INT         NOT NULL CHECK (face_grid_u >= 0),
    face_grid_v         INT         NOT NULL CHECK (face_grid_v >= 0),
    edge_length_m       DOUBLE PRECISION NOT NULL CHECK (edge_length_m > 0),
    area_m2             DOUBLE PRECISION NOT NULL CHECK (area_m2 > 0),
    distortion_factor   DOUBLE PRECISION NOT NULL CHECK (distortion_factor >= 1.0),
    centroid_ecef_x     DOUBLE PRECISION NOT NULL,
    centroid_ecef_y     DOUBLE PRECISION NOT NULL,
    centroid_ecef_z     DOUBLE PRECISION NOT NULL,
    centroid_lat        DOUBLE PRECISION NOT NULL CHECK (centroid_lat >= -90.0 AND centroid_lat <= 90.0),
    centroid_lon        DOUBLE PRECISION NOT NULL CHECK (centroid_lon >= -180.0 AND centroid_lon <= 180.0),
    adjacent_cell_keys  TEXT[]      NOT NULL CHECK (array_length(adjacent_cell_keys, 1) = 4),
    local_frame_id      TEXT,
    human_alias         TEXT,
    alias_namespace     TEXT,
    friendly_name       TEXT,
    known_names         TEXT[]      DEFAULT '{}',
    semantic_labels     TEXT[]      DEFAULT '{}',
    fidelity_coverage   JSONB,
    lod_availability    JSONB,
    asset_bundle_count  INT         DEFAULT 0 CHECK (asset_bundle_count >= 0),
    CONSTRAINT alias_requires_namespace CHECK (
        (human_alias IS NULL) OR (alias_namespace IS NOT NULL)
    ),
    CONSTRAINT unique_grid_position UNIQUE (cube_face, resolution_level, face_grid_u, face_grid_v)
);

CREATE TABLE IF NOT EXISTS alias_table (
    alias_id        TEXT        PRIMARY KEY,
    alias           TEXT        NOT NULL,
    alias_namespace TEXT        NOT NULL,
    canonical_id    TEXT        NOT NULL REFERENCES identity_registry(canonical_id),
    status          TEXT        NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'retired')),
    effective_from  TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to    TIMESTAMPTZ,
    CONSTRAINT unique_alias_per_namespace UNIQUE (alias, alias_namespace)
);

CREATE TABLE IF NOT EXISTS entity_table (
    entity_id       TEXT        PRIMARY KEY REFERENCES identity_registry(canonical_id),
    entity_subtype  TEXT        NOT NULL CHECK (entity_subtype ~ '^[a-z]{3}$'),
    primary_cell_id TEXT        REFERENCES cell_metadata(cell_id),
    secondary_cell_ids TEXT[]   DEFAULT '{}',
    metadata        JSONB       DEFAULT '{}',
    human_alias     TEXT,
    alias_namespace TEXT,
    friendly_name   TEXT,
    known_names     TEXT[]      DEFAULT '{}',
    semantic_labels TEXT[]      DEFAULT '{}',
    CONSTRAINT entity_alias_requires_namespace CHECK (
        (human_alias IS NULL) OR (alias_namespace IS NOT NULL)
    )
);

-- =========================================================================
-- 2. Indexes
-- =========================================================================

CREATE INDEX IF NOT EXISTS idx_cell_resolution ON cell_metadata (resolution_level);
CREATE INDEX IF NOT EXISTS idx_cell_parent ON cell_metadata (parent_cell_id);
CREATE INDEX IF NOT EXISTS idx_cell_face_grid ON cell_metadata (cube_face, face_grid_u, face_grid_v);
CREATE INDEX IF NOT EXISTS idx_cell_adjacent_keys ON cell_metadata USING GIN (adjacent_cell_keys);
CREATE INDEX IF NOT EXISTS idx_alias_resolution ON alias_table (alias_namespace, alias);
CREATE INDEX IF NOT EXISTS idx_alias_canonical ON alias_table (canonical_id);
CREATE INDEX IF NOT EXISTS idx_entity_primary_cell ON entity_table (primary_cell_id);
CREATE INDEX IF NOT EXISTS idx_identity_object_type ON identity_registry (object_type);
CREATE INDEX IF NOT EXISTS idx_cell_centroid_geo ON cell_metadata (centroid_lat, centroid_lon);

-- =========================================================================
-- 3. Functions and Triggers
-- =========================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop and recreate trigger (idempotent)
DROP TRIGGER IF EXISTS trg_identity_registry_updated_at ON identity_registry;
CREATE TRIGGER trg_identity_registry_updated_at
    BEFORE UPDATE ON identity_registry
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =========================================================================
-- 4. Schema version record
-- =========================================================================

-- Insert a schema version marker into a one-row metadata table
CREATE TABLE IF NOT EXISTS _schema_metadata (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);

INSERT INTO _schema_metadata (key, value)
VALUES ('schema_version', '0.1.3')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

INSERT INTO _schema_metadata (key, value)
VALUES ('migration_001_applied_at', now()::TEXT)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

COMMIT;
