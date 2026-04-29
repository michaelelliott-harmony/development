# Harmony Pillar 2 — Entity Deduplication Engine (Milestone 4)
#
# Hybrid deduplication: source-system ID matching first, spatial proximity fallback.
# Pillar 2 owns deduplication. Pillar 1 does not.
#
# Brief §8, Task 6; Resolved decision 2:
#   - Match on source-system IDs first (lot/DP for cadastral, OSM way ID for buildings)
#   - Fall back to spatial proximity with type-aware configurable thresholds
#   - Low-confidence matches flagged for human review
#   - Confidence scoring avoids silent false positives in dense urban geometry
#
# DEC-015: Unresolved duplicates → Q6_DUPLICATE_UNRESOLVED quarantine code.

from __future__ import annotations

import hashlib
import json
import logging
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

log = logging.getLogger(__name__)

_DB_FILENAME = "dedup_index.sqlite"

# Confidence thresholds
_HIGH_CONFIDENCE_THRESHOLD = 0.90
_LOW_CONFIDENCE_THRESHOLD = 0.70


class DedupMatch(Exception):
    """Raised when a feature is identified as a duplicate."""

    def __init__(
        self,
        existing_entity_id: str,
        confidence: float,
        match_method: str,
    ) -> None:
        self.existing_entity_id = existing_entity_id
        self.confidence = confidence
        self.match_method = match_method
        super().__init__(
            f"Duplicate: matches {existing_entity_id!r} "
            f"via {match_method} (confidence={confidence:.2f})"
        )


class LowConfidenceMatch(Exception):
    """Raised when a spatial proximity match is below the confidence threshold."""

    def __init__(
        self,
        existing_entity_id: str,
        confidence: float,
        distance_m: float,
    ) -> None:
        self.existing_entity_id = existing_entity_id
        self.confidence = confidence
        self.distance_m = distance_m
        super().__init__(
            f"Low-confidence match: {existing_entity_id!r} "
            f"distance={distance_m:.1f}m confidence={confidence:.2f}"
        )


class DedupIndex:
    """Append-only index of registered entities for deduplication.

    Tracks:
    - source_id → canonical_id (for source-system ID matching)
    - centroid_lat/lon → canonical_id (for spatial proximity fallback)

    SQLite sidecar, per-dataset or per-run as configured.
    """

    def __init__(self, directory: str | Path, entity_type: str) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._entity_type = entity_type
        self._db_path = self._dir / f"dedup_{entity_type}.sqlite"
        self._conn: sqlite3.Connection | None = None
        self._open()

    def _open(self) -> None:
        self._conn = sqlite3.connect(str(self._db_path), isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS entity_index (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_entity_id TEXT NOT NULL,
                source_id           TEXT,
                centroid_lat        REAL,
                centroid_lon        REAL,
                entity_type         TEXT NOT NULL,
                dataset_name        TEXT,
                registered_at       TEXT NOT NULL,
                confidence          REAL NOT NULL DEFAULT 1.0,
                low_confidence_flag INTEGER NOT NULL DEFAULT 0
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_source_id ON entity_index(source_id)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_centroid ON entity_index(centroid_lat, centroid_lon)"
        )

    def register(
        self,
        canonical_entity_id: str,
        source_id: str | None,
        centroid_lat: float | None,
        centroid_lon: float | None,
        dataset_name: str,
        confidence: float = 1.0,
    ) -> None:
        """Record a successfully registered entity in the dedup index."""
        assert self._conn is not None
        self._conn.execute(
            """
            INSERT INTO entity_index
                (canonical_entity_id, source_id, centroid_lat, centroid_lon,
                 entity_type, dataset_name, registered_at, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                canonical_entity_id,
                source_id,
                centroid_lat,
                centroid_lon,
                self._entity_type,
                dataset_name,
                datetime.now(timezone.utc).isoformat(),
                confidence,
            ),
        )

    def check(
        self,
        source_id: str | None,
        centroid_lat: float | None,
        centroid_lon: float | None,
        spatial_threshold_m: float,
        strategy: str,
    ) -> None:
        """Check for duplicates and raise if one is found.

        Parameters
        ----------
        source_id : str or None
            The feature's source-system ID.
        centroid_lat, centroid_lon : float or None
            Centroid of the feature in WGS84.
        spatial_threshold_m : float
            Spatial proximity threshold in metres.
        strategy : str
            "source_id" | "spatial_proximity" | "hybrid"

        Raises
        ------
        DedupMatch
            If a high-confidence duplicate is found.
        LowConfidenceMatch
            If a spatial match is found below the confidence threshold.
        """
        assert self._conn is not None

        # --- Source-system ID matching (preferred) ---
        if strategy in ("source_id", "hybrid") and source_id:
            row = self._conn.execute(
                "SELECT canonical_entity_id FROM entity_index WHERE source_id = ?",
                (source_id,),
            ).fetchone()
            if row:
                raise DedupMatch(
                    existing_entity_id=row[0],
                    confidence=1.0,
                    match_method="source_id",
                )

        # --- Spatial proximity fallback ---
        if strategy in ("spatial_proximity", "hybrid") and centroid_lat is not None and centroid_lon is not None:
            # Convert threshold to approximate degree bounds for a fast query
            lat_delta = spatial_threshold_m / 111_320.0
            lon_delta = spatial_threshold_m / 92_000.0

            candidates = self._conn.execute(
                """
                SELECT canonical_entity_id, centroid_lat, centroid_lon
                FROM entity_index
                WHERE centroid_lat BETWEEN ? AND ?
                  AND centroid_lon BETWEEN ? AND ?
                """,
                (
                    centroid_lat - lat_delta,
                    centroid_lat + lat_delta,
                    centroid_lon - lon_delta,
                    centroid_lon + lon_delta,
                ),
            ).fetchall()

            for eid, clat, clon in candidates:
                dist_m = _geodetic_distance_m(centroid_lat, centroid_lon, clat, clon)
                if dist_m <= spatial_threshold_m:
                    # Confidence decreases as distance approaches the threshold
                    confidence = 1.0 - (dist_m / spatial_threshold_m) * 0.3
                    if confidence >= _HIGH_CONFIDENCE_THRESHOLD:
                        raise DedupMatch(
                            existing_entity_id=eid,
                            confidence=confidence,
                            match_method="spatial_proximity",
                        )
                    elif confidence >= _LOW_CONFIDENCE_THRESHOLD:
                        raise LowConfidenceMatch(
                            existing_entity_id=eid,
                            confidence=confidence,
                            distance_m=dist_m,
                        )

    def total(self) -> int:
        """Return total registered entity count."""
        assert self._conn is not None
        row = self._conn.execute("SELECT COUNT(*) FROM entity_index").fetchone()
        return row[0] if row else 0

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "DedupIndex":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def _geodetic_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate geodetic distance in metres using the Haversine formula."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))
