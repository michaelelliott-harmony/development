-- Harmony Spatial Operating System — Pillar I — Spatial Substrate
-- Identity Registry Database Schema
--
-- Database: PostgreSQL 14+
-- Schema version: 0.1.3
-- Reference: cell_identity_schema.json, entity_identity_schema.json,
--            identity-schema.md, id_generation_rules.md
--
-- This file defines the canonical schema. For the idempotent migration
-- that creates these objects, see migrations/001_initial_schema.sql.

-- =========================================================================
-- Table 1: identity_registry
-- =========================================================================
-- The root identity table. Every object in the Harmony system has exactly
-- one row here. The canonical_id is the system-wide primary key.

CREATE TABLE identity_registry (
    canonical_id    TEXT        PRIMARY KEY,
    object_type     TEXT        NOT NULL CHECK (object_type IN ('cell', 'entity', 'dataset', 'state', 'contract_anchor')),
    object_domain   TEXT        NOT NULL,
    status          TEXT        NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'deprecated', 'retired')),
    schema_version  TEXT        NOT NULL DEFAULT '0.1.3',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Reserved: temporal versioning (ADR-007, Pillar 4)
    valid_from      TIMESTAMPTZ,
    valid_to        TIMESTAMPTZ,
    version_of      TEXT        REFERENCES identity_registry(canonical_id),
    temporal_status TEXT        CHECK (temporal_status IN ('current', 'historical', 'superseded', 'projected'))
);

-- =========================================================================
-- Table 2: cell_metadata
-- =========================================================================
-- Extended cell metadata. One row per registered cell. Linked to
-- identity_registry via cell_id (which is a canonical_id).

CREATE TABLE cell_metadata (
    cell_id             TEXT        PRIMARY KEY REFERENCES identity_registry(canonical_id),
    cell_key            TEXT        NOT NULL UNIQUE,
    resolution_level    INT         NOT NULL CHECK (resolution_level >= 0 AND resolution_level <= 12),
    parent_cell_id      TEXT        REFERENCES cell_metadata(cell_id),

    -- Cube face grid position (gnomonic projection)
    cube_face           INT         NOT NULL CHECK (cube_face >= 0 AND cube_face <= 5),
    face_grid_u         INT         NOT NULL CHECK (face_grid_u >= 0),
    face_grid_v         INT         NOT NULL CHECK (face_grid_v >= 0),

    -- Spatial geometry (computed from cell position)
    edge_length_m       DOUBLE PRECISION NOT NULL CHECK (edge_length_m > 0),
    area_m2             DOUBLE PRECISION NOT NULL CHECK (area_m2 > 0),
    distortion_factor   DOUBLE PRECISION NOT NULL CHECK (distortion_factor >= 1.0),

    -- Centroid in ECEF (the hash input for cell_key derivation)
    centroid_ecef_x     DOUBLE PRECISION NOT NULL,
    centroid_ecef_y     DOUBLE PRECISION NOT NULL,
    centroid_ecef_z     DOUBLE PRECISION NOT NULL,

    -- Centroid in geodetic coordinates (for human readability and geospatial queries)
    centroid_lat        DOUBLE PRECISION NOT NULL CHECK (centroid_lat >= -90.0 AND centroid_lat <= 90.0),
    centroid_lon        DOUBLE PRECISION NOT NULL CHECK (centroid_lon >= -180.0 AND centroid_lon <= 180.0),

    -- Adjacency: 4 edge-adjacent cell keys in fixed order [+u, -u, +v, -v]
    adjacent_cell_keys  TEXT[]      NOT NULL CHECK (array_length(adjacent_cell_keys, 1) = 4),

    -- Local coordinate frame (ENU origin at centroid)
    local_frame_id      TEXT,

    -- Human-facing identity layers
    human_alias         TEXT,
    alias_namespace     TEXT,
    friendly_name       TEXT,
    known_names         TEXT[]      DEFAULT '{}',
    semantic_labels     TEXT[]      DEFAULT '{}',

    -- Reserved: dual fidelity (Pillar 2)
    fidelity_coverage   JSONB,
    lod_availability    JSONB,
    asset_bundle_count  INT         DEFAULT 0 CHECK (asset_bundle_count >= 0),

    -- Constraint: alias_namespace required if human_alias is set
    CONSTRAINT alias_requires_namespace CHECK (
        (human_alias IS NULL) OR (alias_namespace IS NOT NULL)
    ),

    -- Constraint: face_grid indices must be within resolution bounds
    -- (4^resolution_level - 1 is the max grid index)
    -- Note: This is enforced in application code because PostgreSQL
    -- CHECK constraints cannot reference computed expressions involving
    -- power functions on other columns. The application layer validates
    -- that face_grid_u < 4^resolution_level and face_grid_v < 4^resolution_level.

    -- Constraint: unique grid position per face and resolution
    CONSTRAINT unique_grid_position UNIQUE (cube_face, resolution_level, face_grid_u, face_grid_v)
);

-- =========================================================================
-- Table 3: alias_table
-- =========================================================================
-- Alias resolution table. Maps human-friendly aliases to canonical IDs.
-- Supports temporal validity for alias rotation.

CREATE TABLE alias_table (
    alias_id        TEXT        PRIMARY KEY,
    alias           TEXT        NOT NULL,
    alias_namespace TEXT        NOT NULL,
    canonical_id    TEXT        NOT NULL REFERENCES identity_registry(canonical_id),
    status          TEXT        NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'retired')),
    effective_from  TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to    TIMESTAMPTZ,

    -- Note: uniqueness enforced via partial unique INDEX (not constraint)
    -- to allow multiple retired entries for the same (alias, namespace).
    -- See migration 002.
);

-- Partial unique index: only ONE active binding per (alias, namespace)
CREATE UNIQUE INDEX idx_alias_active_unique
    ON alias_table (UPPER(alias), alias_namespace)
    WHERE status = 'active';

-- =========================================================================
-- Table 5: alias_namespace_registry
-- =========================================================================
-- Per-namespace atomic counter for auto-generated aliases.
-- See alias_namespace_rules.md §9.

CREATE TABLE alias_namespace_registry (
    namespace       TEXT        PRIMARY KEY,
    prefix          VARCHAR(4)  NOT NULL CHECK (prefix ~ '^[A-Z]{2,4}$'),
    next_counter    INTEGER     NOT NULL DEFAULT 1 CHECK (next_counter >= 1),
    status          TEXT        NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'retired')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================================================================
-- Table 6: entity_table
-- =========================================================================
-- Entity records. Entities are non-cell spatial objects (buildings,
-- roads, sensors, etc.) anchored to one or more cells.

CREATE TABLE entity_table (
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

    -- Constraint: alias_namespace required if human_alias is set
    CONSTRAINT entity_alias_requires_namespace CHECK (
        (human_alias IS NULL) OR (alias_namespace IS NOT NULL)
    )
);

-- =========================================================================
-- Indexes
-- =========================================================================

-- Index 1: cell_key lookup (already UNIQUE on column, but explicit for clarity)
-- The UNIQUE constraint on cell_metadata.cell_key creates an implicit unique index.

-- Index 2: resolution level queries (e.g., "all Level 8 cells")
CREATE INDEX idx_cell_resolution ON cell_metadata (resolution_level);

-- Index 3: parent cell lookup (e.g., "all children of cell X")
CREATE INDEX idx_cell_parent ON cell_metadata (parent_cell_id);

-- Index 4: cube face + grid position (spatial queries within a face)
CREATE INDEX idx_cell_face_grid ON cell_metadata (cube_face, face_grid_u, face_grid_v);

-- Index 5: GIN index on adjacent_cell_keys (e.g., "all cells adjacent to key X")
CREATE INDEX idx_cell_adjacent_keys ON cell_metadata USING GIN (adjacent_cell_keys);

-- Index 6: alias resolution (namespace + alias for fast lookup)
CREATE INDEX idx_alias_resolution ON alias_table (alias_namespace, alias);

-- Index 7: canonical ID lookup on alias table
CREATE INDEX idx_alias_canonical ON alias_table (canonical_id);

-- Index 8: entity primary cell lookup
CREATE INDEX idx_entity_primary_cell ON entity_table (primary_cell_id);

-- Index 9: identity registry object type filter
CREATE INDEX idx_identity_object_type ON identity_registry (object_type);

-- Index 10: geodetic centroid for bounding-box queries
CREATE INDEX idx_cell_centroid_geo ON cell_metadata (centroid_lat, centroid_lon);

-- =========================================================================
-- Updated-at trigger
-- =========================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_identity_registry_updated_at
    BEFORE UPDATE ON identity_registry
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =========================================================================
-- Comments
-- =========================================================================

COMMENT ON TABLE identity_registry IS 'Root identity table for all Harmony objects. Every canonical_id in the system has exactly one row here.';
COMMENT ON TABLE cell_metadata IS 'Extended cell metadata including spatial geometry, grid position, and adjacency. One row per registered cell.';
COMMENT ON TABLE alias_table IS 'Maps human-friendly aliases to canonical IDs with temporal validity.';
COMMENT ON TABLE entity_table IS 'Non-cell spatial objects (buildings, roads, sensors) anchored to cells.';
COMMENT ON COLUMN cell_metadata.adjacent_cell_keys IS 'Edge-adjacent cell keys in fixed order: [+u, -u, +v, -v]. See cell_adjacency_spec.md.';
COMMENT ON COLUMN cell_metadata.distortion_factor IS 'Linear gnomonic distortion factor: sqrt(1 + u_c^2 + v_c^2). 1.0 at face centre, ~2.3 at corners.';
