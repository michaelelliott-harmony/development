# Harmony Pillar 2 — Cell Assignment Engine (Milestone 3)
#
# Maps validated WGS84 geometry to Harmony Cell keys.
# Computes primary cell (centroid/midpoint) and secondary cells
# (all cells the geometry intersects) at a geometry-adaptive resolution.
#
# Brief §8, Task 7: geometry-adaptive resolution with manifest floor.
# Resolved decision 3: primary by centroid (polygon) or midpoint (line).
# Resolved decision 6: geometry-adaptive with manifest default as floor.
#
# Cell registration is performed via the Pillar 1 HTTP API (POST /cells).
# This module handles the mapping; the runner handles registration.

from __future__ import annotations

import logging
import math
from typing import NamedTuple

from shapely.geometry import shape, Point, LineString, MultiPoint

from harmony.pipelines.cell_key import (
    CellCoordinates,
    adaptive_resolution,
    cell_edge_m,
    derive,
)
from harmony.pipelines.validate import ValidatedFeature

log = logging.getLogger(__name__)

# Maximum secondary cells per feature — cap to avoid pathological cases with
# very large features (e.g. an entire LGA zoning polygon at r10)
MAX_SECONDARY_CELLS = 512

# Metres-per-degree constants (approximate at Central Coast lat ≈ -33°)
_M_PER_DEG_LAT = 111_320.0
_M_PER_DEG_LON = 92_000.0   # cos(-33°) × 111320


class CellAssignment(NamedTuple):
    """Result of assigning a feature to Harmony cells."""
    primary: CellCoordinates
    secondary: list[CellCoordinates]
    resolution_level: int
    assigned_by: str   # "centroid" | "midpoint" | "point"


def assign(
    feature: ValidatedFeature,
    resolution_floor: int,
    region_code: str,
) -> CellAssignment | None:
    """Compute the primary and secondary cell assignments for a feature.

    Parameters
    ----------
    feature : ValidatedFeature
        A validated, normalised feature with `geometry_wgs84` set.
    resolution_floor : int
        Minimum resolution level from the dataset manifest.
    region_code : str
        Harmony region code, e.g. "cc" for Central Coast.

    Returns
    -------
    CellAssignment or None
        None if the feature has no geometry (attribute-only features).
    """
    geom_dict = feature.get("geometry_wgs84")
    if geom_dict is None:
        return None

    try:
        shp = shape(geom_dict)
    except Exception as exc:
        log.warning("assign: cannot construct Shapely geometry for %r: %s",
                    feature.get("source_id"), exc)
        return None

    geom_type = shp.geom_type

    # Step 1: Compute bounding box diagonal in metres
    minx, miny, maxx, maxy = shp.bounds
    diagonal_m = math.sqrt(
        ((maxx - minx) * _M_PER_DEG_LON) ** 2
        + ((maxy - miny) * _M_PER_DEG_LAT) ** 2
    )

    # Step 2: Geometry-adaptive resolution
    resolution = adaptive_resolution(diagonal_m, resolution_floor)
    log.debug(
        "assign: %r bbox_diagonal=%.0fm → r%02d (floor=r%02d)",
        feature.get("source_id"), diagonal_m, resolution, resolution_floor,
    )

    # Step 3: Compute primary cell from centroid or midpoint
    if geom_type in ("Polygon", "MultiPolygon"):
        primary_point = shp.centroid
        assigned_by = "centroid"
    elif geom_type in ("LineString", "MultiLineString"):
        primary_point = shp.interpolate(0.5, normalized=True)
        assigned_by = "midpoint"
    elif geom_type in ("Point", "MultiPoint"):
        primary_point = shp.centroid
        assigned_by = "point"
    else:
        primary_point = shp.centroid
        assigned_by = "centroid"

    primary_coords = derive(primary_point.y, primary_point.x, resolution, region_code)

    # Step 4: Enumerate all intersecting cells (secondary cells)
    all_coords = _enumerate_cells(shp, resolution, region_code)

    # Separate primary from secondary, deduplicate
    secondary: list[CellCoordinates] = []
    seen_keys: set[str] = {primary_coords.cell_key}

    for c in all_coords:
        if c.cell_key not in seen_keys:
            seen_keys.add(c.cell_key)
            secondary.append(c)

    if len(secondary) > MAX_SECONDARY_CELLS:
        log.warning(
            "assign: %r has %d secondary cells at r%02d — capping at %d",
            feature.get("source_id"), len(secondary), resolution, MAX_SECONDARY_CELLS,
        )
        secondary = secondary[:MAX_SECONDARY_CELLS]

    return CellAssignment(
        primary=primary_coords,
        secondary=secondary,
        resolution_level=resolution,
        assigned_by=assigned_by,
    )


def _enumerate_cells(
    shp,
    resolution: int,
    region_code: str,
) -> list[CellCoordinates]:
    """Enumerate all cells at `resolution` that the geometry intersects.

    Samples the geometry's bounding box at a grid spacing of half the
    cell edge length, then filters to points that fall within (or on)
    the geometry using Shapely's `contains` / `intersects` predicates.
    """
    edge_m = cell_edge_m(resolution)
    step_m = max(edge_m / 2.0, 1.0)   # Sample at half the cell edge

    # Convert step to degrees (approximate at Central Coast latitude)
    step_lat = step_m / _M_PER_DEG_LAT
    step_lon = step_m / _M_PER_DEG_LON

    minx, miny, maxx, maxy = shp.bounds

    # Expand bbox slightly to catch edge-touching cells
    minx -= step_lon
    miny -= step_lat
    maxx += step_lon
    maxy += step_lat

    # Cap grid to avoid pathological cases
    n_lat = int(math.ceil((maxy - miny) / step_lat)) + 1
    n_lon = int(math.ceil((maxx - minx) / step_lon)) + 1

    # If the grid is too large, increase step size
    if n_lat * n_lon > MAX_SECONDARY_CELLS * 4:
        scale = math.sqrt((n_lat * n_lon) / (MAX_SECONDARY_CELLS * 4))
        step_lat *= scale
        step_lon *= scale
        n_lat = int(math.ceil((maxy - miny) / step_lat)) + 1
        n_lon = int(math.ceil((maxx - minx) / step_lon)) + 1

    coords: list[CellCoordinates] = []
    seen: set[str] = set()

    lat = miny
    while lat <= maxy:
        lon = minx
        while lon <= maxx:
            # Clamp to valid range
            clat = max(-90.0, min(90.0, lat))
            clon = max(-180.0, min(180.0, lon))

            pt = Point(clon, clat)
            if shp.intersects(pt) or shp.distance(pt) < step_m / _M_PER_DEG_LAT:
                try:
                    c = derive(clat, clon, resolution, region_code)
                    if c.cell_key not in seen:
                        seen.add(c.cell_key)
                        coords.append(c)
                except ValueError:
                    pass

            lon += step_lon
        lat += step_lat

    return coords
