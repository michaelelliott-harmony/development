# Harmony Pillar 2 — Dataset Registry (SQLite MVP)
#
# Records all ingestion runs with full provenance:
#   - Dataset manifests (JSON snapshot)
#   - Ingestion run history (timestamps, feature counts, status)
#   - Quarantine summaries per run
#   - Entity registration counts
#   - Fidelity coverage tracking (structural: populated cells and entities)
#   - Version lineage (which run superseded which)
#
# Brief §8, Task 8: dataset registry for provenance.
# Production deployment may migrate this to PostgreSQL alongside Pillar 1.

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_DB_FILENAME = "p2_registry.sqlite"


class DatasetRegistry:
    """Pillar 2 dataset and ingestion run registry.

    Parameters
    ----------
    directory : str or Path
        Directory for the SQLite database file.
    """

    def __init__(self, directory: str | Path) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._dir / _DB_FILENAME
        self._conn: sqlite3.Connection | None = None
        self._open()

    def _open(self) -> None:
        self._conn = sqlite3.connect(str(self._db_path), isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS ingestion_runs (
                run_id              TEXT PRIMARY KEY,
                manifest_id         TEXT NOT NULL,
                manifest_json       TEXT NOT NULL,
                dataset_name        TEXT NOT NULL,
                entity_type         TEXT NOT NULL,
                source_type         TEXT NOT NULL,
                source_tier         INTEGER NOT NULL,
                started_at          TEXT NOT NULL,
                completed_at        TEXT,
                status              TEXT NOT NULL DEFAULT 'running',
                features_read       INTEGER DEFAULT 0,
                features_normalised INTEGER DEFAULT 0,
                features_validated  INTEGER DEFAULT 0,
                features_quarantined INTEGER DEFAULT 0,
                features_dedup_skipped INTEGER DEFAULT 0,
                entities_registered INTEGER DEFAULT 0,
                cells_registered    INTEGER DEFAULT 0,
                quarantine_by_reason TEXT DEFAULT '{}',
                error_message       TEXT,
                notes               TEXT
            );

            CREATE TABLE IF NOT EXISTS registered_cells (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id              TEXT NOT NULL,
                cell_key            TEXT NOT NULL,
                canonical_cell_id   TEXT NOT NULL,
                resolution_level    INTEGER NOT NULL,
                entity_type         TEXT NOT NULL,
                fidelity_structural INTEGER NOT NULL DEFAULT 0,
                registered_at       TEXT NOT NULL,
                UNIQUE(cell_key, run_id)
            );

            CREATE TABLE IF NOT EXISTS registered_entities (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id              TEXT NOT NULL,
                canonical_entity_id TEXT NOT NULL,
                source_id           TEXT,
                entity_type         TEXT NOT NULL,
                primary_cell_key    TEXT,
                secondary_cell_count INTEGER DEFAULT 0,
                registered_at       TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_runs_dataset ON ingestion_runs(dataset_name);
            CREATE INDEX IF NOT EXISTS idx_cells_run ON registered_cells(run_id);
            CREATE INDEX IF NOT EXISTS idx_entities_run ON registered_entities(run_id);
            CREATE INDEX IF NOT EXISTS idx_entities_source ON registered_entities(source_id);
        """)

    def start_run(self, run_id: str, manifest) -> None:
        """Record the start of an ingestion run."""
        assert self._conn is not None
        manifest_json = json.dumps(manifest._data, default=str)
        self._conn.execute(
            """
            INSERT OR REPLACE INTO ingestion_runs
                (run_id, manifest_id, manifest_json, dataset_name, entity_type,
                 source_type, source_tier, started_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'running')
            """,
            (
                run_id,
                manifest.manifest_id,
                manifest_json,
                manifest.get("dataset_name", "unknown"),
                manifest.entity_type,
                manifest.source_type,
                manifest.source_tier,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    def complete_run(
        self,
        run_id: str,
        counts: dict,
        quarantine_by_reason: dict | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update a run to completed or failed status."""
        assert self._conn is not None
        status = "failed" if error_message else "completed"
        self._conn.execute(
            """
            UPDATE ingestion_runs SET
                completed_at = ?,
                status = ?,
                features_read = ?,
                features_normalised = ?,
                features_validated = ?,
                features_quarantined = ?,
                features_dedup_skipped = ?,
                entities_registered = ?,
                cells_registered = ?,
                quarantine_by_reason = ?,
                error_message = ?
            WHERE run_id = ?
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                status,
                counts.get("features_read", 0),
                counts.get("features_normalised", 0),
                counts.get("features_validated", 0),
                counts.get("features_quarantined", 0),
                counts.get("features_dedup_skipped", 0),
                counts.get("entities_registered", 0),
                counts.get("cells_registered", 0),
                json.dumps(quarantine_by_reason or {}),
                error_message,
                run_id,
            ),
        )

    def record_cell(
        self,
        run_id: str,
        cell_key: str,
        canonical_cell_id: str,
        resolution_level: int,
        entity_type: str,
    ) -> None:
        """Record a registered cell."""
        assert self._conn is not None
        self._conn.execute(
            """
            INSERT OR IGNORE INTO registered_cells
                (run_id, cell_key, canonical_cell_id, resolution_level,
                 entity_type, fidelity_structural, registered_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """,
            (
                run_id, cell_key, canonical_cell_id, resolution_level,
                entity_type, datetime.now(timezone.utc).isoformat(),
            ),
        )

    def record_entity(
        self,
        run_id: str,
        canonical_entity_id: str,
        source_id: str | None,
        entity_type: str,
        primary_cell_key: str | None,
        secondary_cell_count: int,
    ) -> None:
        """Record a registered entity."""
        assert self._conn is not None
        self._conn.execute(
            """
            INSERT INTO registered_entities
                (run_id, canonical_entity_id, source_id, entity_type,
                 primary_cell_key, secondary_cell_count, registered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, canonical_entity_id, source_id, entity_type,
                primary_cell_key, secondary_cell_count,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    def get_run(self, run_id: str) -> dict | None:
        """Return the ingestion run record or None."""
        assert self._conn is not None
        row = self._conn.execute(
            "SELECT * FROM ingestion_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_runs(self, dataset_name: str | None = None, limit: int = 20) -> list[dict]:
        """List recent ingestion runs."""
        assert self._conn is not None
        if dataset_name:
            rows = self._conn.execute(
                "SELECT * FROM ingestion_runs WHERE dataset_name = ? ORDER BY started_at DESC LIMIT ?",
                (dataset_name, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM ingestion_runs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "DatasetRegistry":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
