# Harmony Pillar 2 — Quarantine Model
#
# DEC-015 (ADR-021 — Proposed):
#   - Quarantine is a separate physical partition, not a flag on main tables.
#   - Six closed reason codes.
#   - 90-day retention.
#   - Pipeline continues on quarantine — batch does not abort.
#   - Ingestion report tallies main-vs-quarantine counts by reason.
#
# In this pipeline stage, quarantine is a SQLite sidecar (MVP).
# Production deployment uses separate DB partitions per DEC-015.

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# Closed set of reason codes per DEC-015
QUARANTINE_REASONS = frozenset({
    "Q1_GEOMETRY_INVALID",       # Self-intersection, ring unclosable, etc.
    "Q2_GEOMETRY_DEGENERATE",    # Zero-area polygon, zero-length line, point cluster
    "Q3_CRS_OUT_OF_BOUNDS",      # Coordinates outside WGS84 valid range
    "Q4_SCHEMA_VIOLATION",       # Missing required field per entity schema
    "Q5_PROVENANCE_INCOMPLETE",  # source_tier, source_id, or confidence missing
    "Q6_DUPLICATE_UNRESOLVED",   # Spatial dedup produced unresolvable ambiguity
})

_QUARANTINE_RETENTION_DAYS = 90
_DB_FILENAME = "quarantine.sqlite"


class QuarantineStore:
    """Append-only inbox for features that failed validation or normalisation.

    Per DEC-015, quarantined records are invisible to all read paths.
    They are held in a sidecar SQLite database for MVP; production uses
    separate physical partitions in PostgreSQL.

    Parameters
    ----------
    directory : str or Path
        Directory in which to create (or open) the quarantine database.
    """

    def __init__(self, directory: str | Path) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._dir / _DB_FILENAME
        self._conn: sqlite3.Connection | None = None
        self._open()

    def _open(self) -> None:
        self._conn = sqlite3.connect(str(self._db_path), isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS quarantine (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                quarantined_at  TEXT NOT NULL,
                reason_code     TEXT NOT NULL,
                source_id       TEXT,
                source_tier     INTEGER,
                adapter_type    TEXT,
                source_crs      TEXT,
                error_detail    TEXT NOT NULL,
                feature_hash    TEXT NOT NULL,
                feature_json    TEXT NOT NULL,
                expires_at      TEXT NOT NULL,
                reviewed        INTEGER NOT NULL DEFAULT 0
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_reason ON quarantine(reason_code)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_expires ON quarantine(expires_at)"
        )

    def add(
        self,
        feature: dict,
        reason_code: str,
        error_detail: str,
    ) -> None:
        """Write a feature to the quarantine store.

        Parameters
        ----------
        feature : dict
            The raw or normalised feature dict as-produced by the adapter
            or normaliser. Stored as JSON.
        reason_code : str
            One of the six closed QUARANTINE_REASONS codes.
        error_detail : str
            Human-readable explanation of why the feature was quarantined.

        Raises
        ------
        ValueError
            If reason_code is not one of the six valid codes.
        """
        if reason_code not in QUARANTINE_REASONS:
            raise ValueError(
                f"Invalid quarantine reason {reason_code!r}. "
                f"Must be one of: {sorted(QUARANTINE_REASONS)}"
            )

        now = datetime.now(timezone.utc)
        expires = now.replace(year=now.year + 1) if now.month <= 3 else now  # approx
        # More precisely: 90 days
        import datetime as dt_module
        expires_at = (now + dt_module.timedelta(days=_QUARANTINE_RETENTION_DAYS)).isoformat()

        feature_json = json.dumps(feature, default=str)
        feature_hash = hashlib.sha256(feature_json.encode()).hexdigest()

        assert self._conn is not None
        self._conn.execute(
            """
            INSERT INTO quarantine
                (quarantined_at, reason_code, source_id, source_tier, adapter_type,
                 source_crs, error_detail, feature_hash, feature_json, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now.isoformat(),
                reason_code,
                feature.get("source_id"),
                feature.get("source_tier"),
                feature.get("adapter_type"),
                feature.get("source_crs"),
                error_detail,
                feature_hash,
                feature_json,
                expires_at,
            ),
        )
        log.debug(
            "Quarantined feature source_id=%r reason=%s",
            feature.get("source_id"),
            reason_code,
        )

    def counts_by_reason(self) -> dict[str, int]:
        """Return quarantine counts grouped by reason code."""
        assert self._conn is not None
        rows = self._conn.execute(
            "SELECT reason_code, COUNT(*) FROM quarantine WHERE reviewed=0 GROUP BY reason_code"
        ).fetchall()
        return {row[0]: row[1] for row in rows}

    def total(self) -> int:
        """Return total unreviewed quarantine count."""
        assert self._conn is not None
        row = self._conn.execute(
            "SELECT COUNT(*) FROM quarantine WHERE reviewed=0"
        ).fetchone()
        return row[0] if row else 0

    def purge_expired(self) -> int:
        """Hard-delete records past their 90-day retention window.

        Returns the number of records purged.
        """
        assert self._conn is not None
        now = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            "DELETE FROM quarantine WHERE expires_at < ?", (now,)
        )
        count = cur.rowcount
        if count:
            log.info("QuarantineStore: purged %d expired records", count)
        return count

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "QuarantineStore":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
