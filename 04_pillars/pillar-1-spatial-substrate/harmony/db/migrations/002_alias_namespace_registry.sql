-- Harmony Spatial Operating System — Pillar I — Spatial Substrate
-- Migration 002: Alias Namespace Registry + Alias Table Fixes
--
-- Adds the alias_namespace_registry table for per-namespace atomic counters.
-- Updates the alias_table constraint from full UNIQUE to partial UNIQUE
-- (WHERE status = 'active') to support retired alias reuse.
-- Adds case-insensitive index for alias lookup.
--
-- Idempotent — safe to re-run.
-- Target: PostgreSQL 14+
-- Schema version: 0.1.3
-- Reference: alias_namespace_rules.md, ADR-006 (alias namespace model)

BEGIN;

-- =========================================================================
-- 1. Alias Namespace Registry (new table)
-- =========================================================================
-- Per-namespace atomic counter for auto-generated aliases.
-- The counter is incremented atomically and never decremented.
-- Retiring an alias does NOT decrement the counter.

CREATE TABLE IF NOT EXISTS alias_namespace_registry (
    namespace       TEXT        PRIMARY KEY,
    prefix          VARCHAR(4)  NOT NULL CHECK (prefix ~ '^[A-Z]{2,4}$'),
    next_counter    INTEGER     NOT NULL DEFAULT 1 CHECK (next_counter >= 1),
    status          TEXT        NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'retired')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE alias_namespace_registry IS
    'Registered alias namespaces with per-namespace atomic counters for auto-generation. '
    'See alias_namespace_rules.md §9.';

COMMENT ON COLUMN alias_namespace_registry.prefix IS
    'The uppercase letter prefix for auto-generated aliases (e.g., CC).';

COMMENT ON COLUMN alias_namespace_registry.next_counter IS
    'Next counter value to assign. Incremented atomically. Never decremented.';

-- =========================================================================
-- 2. Alias Table Schema Updates
-- =========================================================================

-- 2a. Drop the old full UNIQUE constraint and replace with partial UNIQUE.
-- The partial unique ensures only ONE active binding per (alias, namespace)
-- while allowing multiple retired entries.

-- Check if the old constraint exists and drop it
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'unique_alias_per_namespace'
    ) THEN
        ALTER TABLE alias_table DROP CONSTRAINT unique_alias_per_namespace;
    END IF;
END $$;

-- Create the partial unique index (only active aliases must be unique)
-- Using a unique index rather than a constraint because PostgreSQL
-- partial unique constraints require CREATE UNIQUE INDEX syntax.
DROP INDEX IF EXISTS idx_alias_active_unique;
CREATE UNIQUE INDEX idx_alias_active_unique
    ON alias_table (UPPER(alias), alias_namespace)
    WHERE status = 'active';

-- 2b. Update the status CHECK constraint to use the alias lifecycle
-- states (active, retired) rather than the canonical lifecycle states
-- (active, deprecated, retired).
-- Note: We keep 'deprecated' for backward compat but the alias lifecycle
-- only uses 'active' and 'retired'.

-- 2c. Add case-insensitive index for alias lookup
DROP INDEX IF EXISTS idx_alias_upper_lookup;
CREATE INDEX idx_alias_upper_lookup
    ON alias_table (UPPER(alias), alias_namespace);

-- =========================================================================
-- 3. Indexes on new table
-- =========================================================================

CREATE INDEX IF NOT EXISTS idx_namespace_status
    ON alias_namespace_registry (status);

CREATE INDEX IF NOT EXISTS idx_namespace_prefix
    ON alias_namespace_registry (prefix);

-- =========================================================================
-- 4. Schema version record
-- =========================================================================

INSERT INTO _schema_metadata (key, value)
VALUES ('migration_002_applied_at', now()::TEXT)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

COMMIT;
