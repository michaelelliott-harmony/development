# Harmony Pillar 2 — File Source Adapter
#
# Reads GeoJSON, Shapefile, and GeoPackage from local disk.
# Format detected from file extension.
# Used for test fixtures and bulk Data Broker downloads.
#
# DEC-014: source_crs must be declared in config — no auto-detect.

from __future__ import annotations

import os
from typing import Generator

import fiona
from fiona.crs import CRS as FionaCRS

from harmony.pipelines.adapters.base import (
    AdapterConfigError,
    RawFeature,
    SourceAdapter,
)

_SUPPORTED_EXTENSIONS = {".geojson", ".json", ".shp", ".gpkg"}

_TIER_BY_AUTHORITY = {
    "nsw_planning_portal": 1,
    "nsw_spatial_services": 1,
    "openstreetmap": 2,
}


class FileAdapter(SourceAdapter):
    """Read geospatial features from a local file.

    Required config keys:
        source_type: "file"
        source_path: path to the file (absolute or relative to cwd)
        source_crs:  declared CRS as EPSG string, e.g. "EPSG:4326"
        source_authority: who published the data (sets source_tier)

    Optional config keys:
        source_tier: int override (1-4); inferred from source_authority if absent
        source_layer: layer name or index for multi-layer formats (GeoPackage)
    """

    ADAPTER_TYPE = "file"

    def _validate_config(self) -> None:
        for key in ("source_path", "source_crs"):
            if not self._config.get(key):
                raise AdapterConfigError(
                    f"FileAdapter requires '{key}' in source config"
                )

        path = self._config["source_path"]
        if not os.path.exists(path):
            raise AdapterConfigError(
                f"FileAdapter: source_path does not exist: {path!r}"
            )

        ext = os.path.splitext(path)[1].lower()
        if ext not in _SUPPORTED_EXTENSIONS:
            raise AdapterConfigError(
                f"FileAdapter: unsupported file extension {ext!r}. "
                f"Supported: {sorted(_SUPPORTED_EXTENSIONS)}"
            )

    def read(self) -> Generator[RawFeature, None, None]:
        path = self._config["source_path"]
        declared_crs = self._config["source_crs"]
        authority = self._config.get("source_authority", "unknown")
        tier = self._config.get("source_tier") or _TIER_BY_AUTHORITY.get(authority, 2)
        layer = self._config.get("source_layer")

        open_kwargs: dict = {}
        if layer is not None:
            open_kwargs["layer"] = layer

        with fiona.open(path, **open_kwargs) as src:
            for i, feature in enumerate(src):
                geom = dict(feature.geometry.__geo_interface__) if feature.geometry else None
                props = dict(feature.properties or {})

                # Derive a stable source ID from the file path + index.
                # Adapters that carry a natural key (e.g. OSM way ID) override
                # this in their own read(); file features rarely have one.
                feature_id = props.get("id") or props.get("ID") or f"{path}#{i}"

                yield RawFeature(
                    geometry=geom,
                    properties=props,
                    source_crs=declared_crs,
                    source_id=str(feature_id),
                    source_tier=int(tier),
                    adapter_type=self.ADAPTER_TYPE,
                )
