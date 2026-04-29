# Harmony Pillar 2 — CRS Normalisation Service
#
# Reprojects raw features to WGS84 (EPSG:4326).
# Canonical CRS is WGS84; all geometry stored in Harmony is WGS84.
#
# DEC-014 (ADR-020 — Proposed):
#   - source_crs must be declared; auto-detect is refused.
#   - Missing CRS → refuse (Q3_CRS_OUT_OF_BOUNDS quarantine reason).
#   - GDA2020→WGS84 uses NTv2 grid shift (GDA94_GDA2020_conformal.gsb).
#   - Falls back to Helmert when grid file is absent; logs transformation_method.
#   - Every record carries: source_crs, crs_transform_epoch, transformation_method.
#   - OSM data (EPSG:4326) passes through with transformation_method = "passthrough".

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any

from pyproj import Transformer
from pyproj.exceptions import CRSError
from shapely.geometry import mapping, shape

from harmony.pipelines.adapters.base import RawFeature

log = logging.getLogger(__name__)

# Target CRS for all Harmony geometry
_TARGET_CRS = "EPSG:4326"

# Known NTv2 grid file names in PROJ data directories
_NTV2_FILENAMES = (
    "GDA94_GDA2020_conformal.gsb",
    "GDA94_GDA2020_conformal_and_distortion.gsb",
)

# Supported input CRS codes that require transformation
_KNOWN_CRS = {
    "EPSG:4326",  # WGS84 — passthrough
    "EPSG:4283",  # GDA94
    "EPSG:7844",  # GDA2020
    "EPSG:3857",  # Web Mercator (sometimes returned by ArcGIS)
    "EPSG:28356", # MGA zone 56 (GDA94)
    "EPSG:7856",  # MGA zone 56 (GDA2020)
}


class NormalisationError(ValueError):
    """Raised when normalisation cannot proceed due to missing or invalid CRS."""


class NormalisedFeature(RawFeature, total=False):
    """A RawFeature after CRS normalisation to WGS84.

    Additional fields added by the normaliser:
        geometry_wgs84:       GeoJSON geometry in WGS84
        crs_transform_epoch:  ISO-8601 timestamp of transformation
        transformation_method: "passthrough" | "ntv2" | "helmert_fallback" | "proj_default"
        coordinate_bounds_ok: True if all coordinates are within WGS84 valid range
        crs_authority:        CRS registry authority — always "EPSG" (ADR-024 STD-V03)
        crs_code:             CRS code within the authority registry — always 4326
    """
    geometry_wgs84: dict | None
    crs_transform_epoch: str
    transformation_method: str
    coordinate_bounds_ok: bool
    crs_authority: str
    crs_code: int


def _find_ntv2_grid_file() -> str | None:
    """Look for the Australian NTv2 grid shift file in PROJ data directories."""
    from pyproj.datadir import get_data_dir
    search_dirs = [get_data_dir()]

    # Also check environment variable PROJ_DATA / PROJ_LIB
    for env_var in ("PROJ_DATA", "PROJ_LIB"):
        val = os.environ.get(env_var)
        if val:
            search_dirs.extend(val.split(os.pathsep))

    for directory in search_dirs:
        for fname in _NTV2_FILENAMES:
            candidate = os.path.join(directory, fname)
            if os.path.isfile(candidate):
                return candidate
    return None


def _make_transformer(source_crs: str) -> tuple[Transformer, str]:
    """Build a pyproj Transformer and return (transformer, transformation_method).

    For GDA2020 and GDA94, attempts to use the NTv2 grid file first.
    Falls back to the PROJ default transformer with a warning.
    """
    if source_crs == _TARGET_CRS:
        return None, "passthrough"

    ntv2_path = _find_ntv2_grid_file()

    if ntv2_path and source_crs in ("EPSG:7844", "EPSG:4283"):
        # Build a PROJ pipeline that forces the NTv2 grid shift.
        # EPSG:7844 (GDA2020) -> GDA94 via inverse NTv2 -> WGS84 via identity
        # EPSG:4283 (GDA94) -> GDA2020 via NTv2 -> WGS84 via identity
        # Since GDA2020 ≈ ITRF2014 ≈ WGS84 at <1cm, the GDA94->GDA2020 shift
        # is the primary correction needed. GDA2020->WGS84 is a no-op at this scale.
        try:
            if source_crs == "EPSG:4283":
                # GDA94 → GDA2020 (NTv2) → WGS84 (identity)
                pipeline = (
                    f"+proj=pipeline "
                    f"+step +proj=unitconvert +xy_in=deg +xy_out=rad "
                    f"+step +proj=hgridshift +grids={ntv2_path} "
                    f"+step +proj=unitconvert +xy_in=rad +xy_out=deg"
                )
            else:
                # GDA2020 → GDA94 (inverse NTv2) → WGS84 (identity)
                pipeline = (
                    f"+proj=pipeline "
                    f"+step +proj=unitconvert +xy_in=deg +xy_out=rad "
                    f"+step +proj=hgridshift +grids={ntv2_path} +inv "
                    f"+step +proj=unitconvert +xy_in=rad +xy_out=deg"
                )
            t = Transformer.from_pipeline(pipeline)
            log.debug("NTv2 transformer built from %s", ntv2_path)
            return t, "ntv2"
        except CRSError as exc:
            log.warning("NTv2 pipeline failed (%s); falling back to Helmert", exc)

    # Helmert / PROJ default transformer
    try:
        t = Transformer.from_crs(source_crs, _TARGET_CRS, always_xy=True)
        method = "helmert_fallback" if source_crs in ("EPSG:7844", "EPSG:4283") else "proj_default"
        if method == "helmert_fallback":
            log.warning(
                "Using Helmert fallback for %s→WGS84. "
                "Bundle GDA94_GDA2020_conformal.gsb in the container for NTv2 accuracy. "
                "Residual error at Central Coast: ~0.2m vs <1cm with NTv2.",
                source_crs,
            )
        return t, method
    except CRSError as exc:
        raise NormalisationError(f"Cannot build transformer for {source_crs!r}: {exc}") from exc


def _transform_coordinates(
    transformer: Transformer,
    coords: list | tuple,
    depth: int = 0,
) -> list:
    """Recursively transform a coordinate array at any nesting depth."""
    if not coords:
        return []

    # Check if this level contains actual coordinate pairs/triples
    if isinstance(coords[0], (int, float)):
        # A single [x, y] or [x, y, z] coordinate
        x, y = float(coords[0]), float(coords[1])
        new_x, new_y = transformer.transform(x, y)
        if len(coords) > 2:
            return [new_x, new_y, float(coords[2])]
        return [new_x, new_y]

    # Array of sub-arrays — recurse
    return [_transform_coordinates(transformer, c, depth + 1) for c in coords]


def _validate_wgs84_bounds(geom_dict: dict) -> bool:
    """Check that all coordinates in a GeoJSON geometry are within WGS84 valid range."""
    geom_type = geom_dict.get("type", "")
    coords = geom_dict.get("coordinates")

    if coords is None:
        return geom_type == "GeometryCollection"

    def check(c: Any) -> bool:
        if isinstance(c[0], (int, float)):
            lon, lat = float(c[0]), float(c[1])
            return -180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0
        return all(check(sub) for sub in c)

    try:
        return check(coords)
    except (IndexError, TypeError):
        return False


# Cache transformers to avoid rebuilding for each feature
_transformer_cache: dict[str, tuple[Transformer | None, str]] = {}


def normalise(feature: RawFeature) -> NormalisedFeature:
    """Reproject a RawFeature's geometry to WGS84.

    Parameters
    ----------
    feature:
        A RawFeature as emitted by any SourceAdapter. Must have source_crs set.

    Returns
    -------
    NormalisedFeature
        The input feature with geometry_wgs84 and transform metadata added.

    Raises
    ------
    NormalisationError
        If source_crs is missing (DEC-014: refuse, do not default).
        If the CRS string is unparseable.
    """
    source_crs = feature.get("source_crs")
    if not source_crs:
        raise NormalisationError(
            "Feature has no source_crs — DEC-014 requires explicit CRS declaration. "
            f"source_id={feature.get('source_id')!r}"
        )

    if source_crs not in _transformer_cache:
        _transformer_cache[source_crs] = _make_transformer(source_crs)

    transformer, method = _transformer_cache[source_crs]
    epoch = datetime.now(timezone.utc).isoformat()

    # geometry may be under "geometry" or "geometry_wgs84" — adapters set "geometry"
    geom = feature.get("geometry")
    if geom is None:
        result = dict(feature)
        result["geometry_wgs84"] = None
        result["crs_transform_epoch"] = epoch
        result["transformation_method"] = method
        result["coordinate_bounds_ok"] = True
        result["crs_authority"] = "EPSG"
        result["crs_code"] = 4326
        return result  # type: ignore[return-value]

    if method == "passthrough":
        geom_wgs84 = geom
    else:
        geom_type = geom.get("type")
        coords = geom.get("coordinates")

        if coords is None:
            return NormalisedFeature(
                **feature,
                geometry_wgs84=None,
                crs_transform_epoch=epoch,
                transformation_method=method,
                coordinate_bounds_ok=False,
                crs_authority="EPSG",
                crs_code=4326,
            )

        try:
            new_coords = _transform_coordinates(transformer, coords)
        except Exception as exc:
            raise NormalisationError(
                f"Coordinate transformation failed for source_id={feature.get('source_id')!r}: {exc}"
            ) from exc

        geom_wgs84 = {"type": geom_type, "coordinates": new_coords}

    bounds_ok = _validate_wgs84_bounds(geom_wgs84)

    result = dict(feature)
    result["geometry_wgs84"] = geom_wgs84
    result["crs_transform_epoch"] = epoch
    result["transformation_method"] = method
    result["coordinate_bounds_ok"] = bounds_ok
    result["crs_authority"] = "EPSG"
    result["crs_code"] = 4326

    return result  # type: ignore[return-value]


def normalise_batch(
    features: list[RawFeature],
) -> tuple[list[NormalisedFeature], list[dict]]:
    """Normalise a list of features, collecting errors separately.

    Returns
    -------
    (normalised, errors)
        normalised: list of successfully normalised features
        errors: list of dicts with keys (feature, error, quarantine_reason)
    """
    normalised = []
    errors = []

    for feat in features:
        try:
            n = normalise(feat)
            if not n.get("coordinate_bounds_ok", True):
                errors.append({
                    "feature": feat,
                    "error": "Coordinates out of WGS84 bounds after transformation",
                    "quarantine_reason": "Q3_CRS_OUT_OF_BOUNDS",
                })
            else:
                normalised.append(n)
        except NormalisationError as exc:
            errors.append({
                "feature": feat,
                "error": str(exc),
                "quarantine_reason": "Q3_CRS_OUT_OF_BOUNDS",
            })

    return normalised, errors
