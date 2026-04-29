# Harmony Pillar 2 — Geometry Validation Service
#
# Validates WGS84 geometry after CRS normalisation.
# Auto-repairs trivially fixable issues (unclosed rings) with a log entry.
# Quarantines non-repairable failures; pipeline continues.
#
# DEC-015 validation checks (closed set):
#   Q1_GEOMETRY_INVALID   — self-intersection, invalid ring closure
#   Q2_GEOMETRY_DEGENERATE — zero-area polygon, zero-length line, < 3 ring points
#   Q3_CRS_OUT_OF_BOUNDS  — coordinate range failure (done in normalise.py)
#   Q4_SCHEMA_VIOLATION   — geometry type mismatch vs manifest schema
#
# OSM-specific handling:
#   - Unclosed rings auto-repaired (common in raw Overpass responses)
#   - Multipolygon relations with missing outer ring → quarantine Q1

from __future__ import annotations

import logging
from typing import Any

from shapely import is_valid, make_valid
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
    mapping,
    shape,
)
from shapely.validation import explain_validity

from harmony.pipelines.normalise import NormalisedFeature
from harmony.pipelines.quarantine import QuarantineStore

log = logging.getLogger(__name__)

# Minimum coordinate counts per geometry type
_MIN_COORDS = {
    "Point": 1,
    "LineString": 2,
    "Polygon": 4,           # 3 unique + closing point
    "MultiPolygon": 4,
    "MultiLineString": 2,
    "MultiPoint": 1,
    "GeometryCollection": 0,
}


class ValidationReport:
    """Accumulates validation statistics for an ingestion run."""

    def __init__(self) -> None:
        self.total_input = 0
        self.passed = 0
        self.auto_repaired = 0
        self.quarantined = 0
        self.quarantine_by_reason: dict[str, int] = {}
        self.repairs: list[dict] = []

    def record_pass(self) -> None:
        self.total_input += 1
        self.passed += 1

    def record_repair(self, source_id: str, repair_type: str) -> None:
        self.total_input += 1
        self.passed += 1
        self.auto_repaired += 1
        self.repairs.append({"source_id": source_id, "repair": repair_type})

    def record_quarantine(self, reason: str) -> None:
        self.total_input += 1
        self.quarantined += 1
        self.quarantine_by_reason[reason] = self.quarantine_by_reason.get(reason, 0) + 1

    def quarantine_fraction(self) -> float:
        if self.total_input == 0:
            return 0.0
        return self.quarantined / self.total_input

    @property
    def warning_threshold_breached(self) -> bool:
        return self.quarantine_fraction() > 0.05

    def to_dict(self) -> dict:
        return {
            "total_input": self.total_input,
            "passed": self.passed,
            "auto_repaired": self.auto_repaired,
            "quarantined": self.quarantined,
            "quarantine_fraction": round(self.quarantine_fraction(), 4),
            "quarantine_by_reason": self.quarantine_by_reason,
            "repair_log": self.repairs,
            "warning_threshold_breached": self.quarantine_fraction() > 0.05,
        }


class ValidatedFeature(NormalisedFeature, total=False):
    """A NormalisedFeature after geometry validation.

    Additional fields:
        geometry_valid:      True if geometry passed validation (possibly after repair)
        geometry_repaired:   True if auto-repair was applied
        repair_description:  Description of the repair applied, if any
        shapely_wkt:         WKT string of the validated Shapely geometry (debug aid)
    """
    geometry_valid: bool
    geometry_repaired: bool
    repair_description: str | None


def _check_coordinate_count(geom_dict: dict) -> str | None:
    """Return an error message if the geometry has too few coordinates, else None."""
    geom_type = geom_dict.get("type", "Unknown")
    coords = geom_dict.get("coordinates")

    if coords is None:
        return f"Geometry type {geom_type!r} has no coordinates"

    # Guard: coordinates must be a list/tuple, not a string or other scalar
    if not isinstance(coords, (list, tuple)):
        return f"Geometry type {geom_type!r} has non-array coordinates: {type(coords).__name__}"

    minimum = _MIN_COORDS.get(geom_type)
    if minimum is None:
        return None  # Unknown type; let Shapely handle it

    if geom_type == "Point":
        return None  # A point is always valid coordinate-count-wise

    if geom_type == "LineString":
        flat = coords
        if len(flat) < minimum:
            return f"LineString has {len(flat)} points; minimum is {minimum}"

    if geom_type == "Polygon":
        if not coords or not isinstance(coords[0], (list, tuple)) or len(coords[0]) < minimum:
            n = len(coords[0]) if coords and isinstance(coords[0], (list, tuple)) else 0
            return f"Polygon exterior ring has {n} points; minimum is {minimum}"

    return None


def _ensure_ring_closed(ring: list) -> tuple[list, bool]:
    """Ensure a coordinate ring is closed. Returns (ring, was_repaired)."""
    if len(ring) < 2:
        return ring, False
    if ring[0] != ring[-1]:
        return ring + [ring[0]], True
    return ring, False


def _repair_unclosed_rings(geom_dict: dict) -> tuple[dict, bool, str]:
    """Attempt to close unclosed rings in Polygon/MultiPolygon geometry.

    Returns (repaired_geom_dict, was_repaired, repair_description).
    This is the only auto-repair Pillar 2 applies.
    """
    geom_type = geom_dict.get("type")
    coords = geom_dict.get("coordinates")
    repaired = False
    description = ""

    if geom_type == "Polygon" and coords:
        new_rings = []
        for ring in coords:
            closed, fixed = _ensure_ring_closed(ring)
            new_rings.append(closed)
            if fixed:
                repaired = True
        if repaired:
            description = "Unclosed ring(s) closed"
        return {"type": "Polygon", "coordinates": new_rings}, repaired, description

    if geom_type == "MultiPolygon" and coords:
        new_polys = []
        for poly in coords:
            new_rings = []
            for ring in poly:
                closed, fixed = _ensure_ring_closed(ring)
                new_rings.append(closed)
                if fixed:
                    repaired = True
            new_polys.append(new_rings)
        if repaired:
            description = "Unclosed ring(s) closed in MultiPolygon"
        return {"type": "MultiPolygon", "coordinates": new_polys}, repaired, description

    return geom_dict, False, ""


def _check_allowed_type(geom_dict: dict, allowed_types: list[str] | None) -> str | None:
    """Return an error if the geometry type is not in the allowed set."""
    if not allowed_types:
        return None
    geom_type = geom_dict.get("type", "Unknown")
    if geom_type not in allowed_types:
        return (
            f"Geometry type {geom_type!r} not allowed by manifest; "
            f"expected one of {allowed_types}"
        )
    return None


def validate(
    feature: NormalisedFeature,
    quarantine: QuarantineStore,
    report: ValidationReport,
    allowed_types: list[str] | None = None,
) -> ValidatedFeature | None:
    """Validate a normalised feature's WGS84 geometry.

    Trivially fixable issues (unclosed rings) are auto-repaired with a log entry.
    All other failures quarantine the feature and return None.
    Pipeline continues regardless.

    Parameters
    ----------
    feature : NormalisedFeature
        Feature with geometry_wgs84 set.
    quarantine : QuarantineStore
        The active quarantine store for this run.
    report : ValidationReport
        Accumulates statistics across the batch.
    allowed_types : list[str] | None
        If provided, geometry type must be in this list. Mismatch → Q4.

    Returns
    -------
    ValidatedFeature or None
        None if the feature was quarantined.
    """
    source_id = feature.get("source_id", "<unknown>")
    geom = feature.get("geometry_wgs84")

    # Features with no geometry pass through (some source types are attribute-only)
    if geom is None:
        report.record_pass()
        return _wrap(feature, valid=True, repaired=False, repair_desc=None)

    # --- Geometry type check ---
    type_error = _check_allowed_type(geom, allowed_types)
    if type_error:
        quarantine.add(feature, "Q4_SCHEMA_VIOLATION", type_error)
        report.record_quarantine("Q4_SCHEMA_VIOLATION")
        log.debug("Q4 quarantine source_id=%r: %s", source_id, type_error)
        return None

    # --- Coordinate count check ---
    count_error = _check_coordinate_count(geom)
    if count_error:
        quarantine.add(feature, "Q2_GEOMETRY_DEGENERATE", count_error)
        report.record_quarantine("Q2_GEOMETRY_DEGENERATE")
        log.debug("Q2 quarantine source_id=%r: %s", source_id, count_error)
        return None

    # --- Auto-repair unclosed rings before handing to Shapely ---
    geom, was_repaired, repair_desc = _repair_unclosed_rings(geom)
    if was_repaired:
        feature = dict(feature)  # type: ignore[assignment]
        feature["geometry_wgs84"] = geom

    # --- Shapely validity check ---
    try:
        shp = shape(geom)
    except Exception as exc:
        msg = f"Cannot construct Shapely geometry: {exc}"
        quarantine.add(feature, "Q1_GEOMETRY_INVALID", msg)
        report.record_quarantine("Q1_GEOMETRY_INVALID")
        log.debug("Q1 quarantine source_id=%r: %s", source_id, msg)
        return None

    if not is_valid(shp):
        reason = explain_validity(shp)

        # Attempt make_valid (Shapely 2.x) for self-intersecting polygons
        try:
            fixed = make_valid(shp)
            if is_valid(fixed):
                geom = mapping(fixed)
                feature = dict(feature)  # type: ignore[assignment]
                feature["geometry_wgs84"] = dict(geom)
                was_repaired = True
                repair_desc = f"make_valid applied ({reason})"
                log.debug("Auto-repaired source_id=%r via make_valid: %s", source_id, reason)
            else:
                quarantine.add(
                    feature,
                    "Q1_GEOMETRY_INVALID",
                    f"Invalid geometry (make_valid could not fix): {reason}",
                )
                report.record_quarantine("Q1_GEOMETRY_INVALID")
                return None
        except Exception as exc:
            quarantine.add(
                feature,
                "Q1_GEOMETRY_INVALID",
                f"Invalid geometry and make_valid raised: {exc}: {reason}",
            )
            report.record_quarantine("Q1_GEOMETRY_INVALID")
            return None

    # --- Zero-area / zero-length degenerate check ---
    if hasattr(shp, "area") and shp.area == 0 and shp.geom_type in ("Polygon", "MultiPolygon"):
        msg = "Zero-area polygon"
        quarantine.add(feature, "Q2_GEOMETRY_DEGENERATE", msg)
        report.record_quarantine("Q2_GEOMETRY_DEGENERATE")
        log.debug("Q2 quarantine source_id=%r: %s", source_id, msg)
        return None

    if hasattr(shp, "length") and shp.length == 0 and shp.geom_type in ("LineString", "MultiLineString"):
        msg = "Zero-length line"
        quarantine.add(feature, "Q2_GEOMETRY_DEGENERATE", msg)
        report.record_quarantine("Q2_GEOMETRY_DEGENERATE")
        log.debug("Q2 quarantine source_id=%r: %s", source_id, msg)
        return None

    # --- Passed ---
    if was_repaired:
        report.record_repair(source_id, repair_desc or "ring_closure")
        log.debug("Auto-repaired source_id=%r: %s", source_id, repair_desc)
    else:
        report.record_pass()

    return _wrap(
        feature,
        valid=True,
        repaired=was_repaired,
        repair_desc=repair_desc if was_repaired else None,
    )


def validate_batch(
    features: list[NormalisedFeature],
    quarantine: QuarantineStore,
    allowed_types: list[str] | None = None,
) -> tuple[list[ValidatedFeature], ValidationReport]:
    """Validate a list of normalised features.

    Returns
    -------
    (validated, report)
        validated: features that passed (possibly auto-repaired)
        report:    statistics across the batch
    """
    report = ValidationReport()
    validated = []

    for feat in features:
        result = validate(feat, quarantine, report, allowed_types)
        if result is not None:
            validated.append(result)

    if report.quarantine_fraction() > 0.05:
        log.warning(
            "Quarantine fraction %.1f%% exceeds 5%% threshold — human review required. "
            "Breakdown: %s",
            report.quarantine_fraction() * 100,
            report.quarantine_by_reason,
        )

    return validated, report


def _wrap(
    feature: NormalisedFeature,
    valid: bool,
    repaired: bool,
    repair_desc: str | None,
) -> ValidatedFeature:
    result = dict(feature)
    result["geometry_valid"] = valid
    result["geometry_repaired"] = repaired
    result["repair_description"] = repair_desc
    return result  # type: ignore[return-value]
