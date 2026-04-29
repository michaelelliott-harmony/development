# Harmony Pillar 2 — Dataset Manifest System
#
# YAML manifests describe a data source and how to process it.
# This module handles loading, validation, and adapter dispatch.
#
# Brief §8, Task 5: manifest supports source_types:
#   "file" | "arcgis_rest" | "osm_overpass"
# (WFS adapter not built — WFS endpoints return 400 on NSW sources.)
#
# DEC-014: every manifest must declare source_crs explicitly.

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)

# Valid source types
VALID_SOURCE_TYPES = {"file", "arcgis_rest", "osm_overpass"}

# Valid entity types (determines entity_subtype and attribute mapping)
VALID_ENTITY_TYPES = {"zoning_area", "cadastral_lot", "building", "road_segment"}

# Entity subtype codes — exactly 3 lowercase letters per Pillar 1 constraint
ENTITY_SUBTYPE_CODES = {
    "zoning_area": "zon",
    "cadastral_lot": "cad",
    "building": "bld",
    "road_segment": "rod",
}

# Default resolution floor per entity type (p2-entity-schemas.md)
DEFAULT_RESOLUTION_FLOOR = {
    "zoning_area": 6,
    "cadastral_lot": 8,
    "building": 10,
    "road_segment": 8,
}

# Valid dedup strategies
VALID_DEDUP_STRATEGIES = {"source_id", "spatial_proximity", "hybrid"}


class ManifestError(ValueError):
    """Raised when a manifest is invalid."""


class DatasetManifest:
    """A validated dataset manifest.

    Attributes are exposed as a flat dict-like object. Access via
    manifest["key"] or manifest.get("key", default).
    """

    def __init__(self, data: dict, manifest_path: str | None = None) -> None:
        self._data = data
        self._path = manifest_path
        self._validate()

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    @property
    def manifest_id(self) -> str:
        """Stable identifier for this manifest (SHA-256 of canonical JSON)."""
        canonical = json.dumps(self._data, sort_keys=True, default=str)
        return "mf_" + hashlib.sha256(canonical.encode()).hexdigest()[:12]

    @property
    def source_type(self) -> str:
        return self._data["source_type"]

    @property
    def entity_type(self) -> str:
        return self._data["target_entity_type"]

    @property
    def entity_subtype_code(self) -> str:
        return ENTITY_SUBTYPE_CODES[self.entity_type]

    @property
    def resolution_floor(self) -> int:
        return self._data.get(
            "resolution_level_floor",
            DEFAULT_RESOLUTION_FLOOR[self.entity_type],
        )

    @property
    def region_code(self) -> str:
        return self._data.get("region_code", "cc")

    @property
    def attribute_mapping(self) -> dict[str, str]:
        return self._data.get("attribute_mapping", {})

    @property
    def known_names_fields(self) -> list[str]:
        return self._data.get("known_names_fields", [])

    @property
    def dedup_strategy(self) -> str:
        return self._data.get("dedup_strategy", "hybrid")

    @property
    def dedup_source_id_field(self) -> str | None:
        return self._data.get("dedup_source_id_field")

    @property
    def dedup_spatial_threshold_m(self) -> float:
        return float(self._data.get("dedup_spatial_threshold_m", 15.0))

    @property
    def source_tier(self) -> int:
        return int(self._data.get("source_tier", 1))

    @property
    def source_authority(self) -> str:
        return self._data.get("source_authority", "unknown")

    @property
    def fidelity_class(self) -> str:
        return self._data.get("fidelity_class", "structural")

    @property
    def positional_accuracy_m(self) -> float:
        return float(self._data.get("positional_accuracy_m", 5.0))

    @property
    def carries_feature_dates(self) -> bool:
        """True if the source dataset provides a per-feature date field.

        ADR-024 §2.5 / STD-V05: when True, valid_from is mandatory on every
        ingested entity record. Records missing valid_from are quarantined
        with Q4_SCHEMA_VIOLATION.
        """
        return bool(self._data.get("carries_feature_dates", False))

    @property
    def allowed_geometry_types(self) -> list[str] | None:
        return self._data.get("allowed_geometry_types")

    def _validate(self) -> None:
        data = self._data

        # Required fields
        for field in ("source_type", "target_entity_type", "source_crs"):
            if not data.get(field):
                raise ManifestError(f"Manifest missing required field: '{field}'")

        if data["source_type"] not in VALID_SOURCE_TYPES:
            raise ManifestError(
                f"Invalid source_type {data['source_type']!r}. "
                f"Must be one of: {sorted(VALID_SOURCE_TYPES)}"
            )

        if data["target_entity_type"] not in VALID_ENTITY_TYPES:
            raise ManifestError(
                f"Invalid target_entity_type {data['target_entity_type']!r}. "
                f"Must be one of: {sorted(VALID_ENTITY_TYPES)}"
            )

        # Source-type specific required fields
        if data["source_type"] == "file" and not data.get("source_path"):
            raise ManifestError("File manifests require 'source_path'")

        if data["source_type"] == "arcgis_rest":
            for f in ("source_url", "source_bbox"):
                if not data.get(f):
                    raise ManifestError(f"ArcGIS REST manifests require '{f}'")

        if data["source_type"] == "osm_overpass":
            for f in ("source_query", "source_bbox"):
                if not data.get(f):
                    raise ManifestError(f"OSM Overpass manifests require '{f}'")

        # Source tier range — ADR-022 D3, ADR-018: tiers are 1–4; Tier 0 does not exist
        tier = data.get("source_tier")
        if tier is not None:
            tier_int = int(tier)
            if tier_int < 1 or tier_int > 4:
                raise ManifestError(
                    f"source_tier must be 1–4 per ADR-018. "
                    f"Got {tier_int!r}. Tier 0 is not assignable."
                )

        # Dedup strategy
        strat = data.get("dedup_strategy", "hybrid")
        if strat not in VALID_DEDUP_STRATEGIES:
            raise ManifestError(
                f"Invalid dedup_strategy {strat!r}. "
                f"Must be one of: {sorted(VALID_DEDUP_STRATEGIES)}"
            )

        # Resolution floor
        floor = data.get("resolution_level_floor")
        if floor is not None and not (0 <= int(floor) <= 12):
            raise ManifestError(f"resolution_level_floor must be 0-12, got {floor}")


def load(path: str | Path) -> DatasetManifest:
    """Load and validate a manifest from a YAML file.

    Parameters
    ----------
    path : str or Path
        Path to the YAML manifest file.

    Returns
    -------
    DatasetManifest
        The validated manifest.

    Raises
    ------
    ManifestError
        If the file cannot be read or the manifest is invalid.
    FileNotFoundError
        If the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    try:
        with open(path) as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise ManifestError(f"YAML parse error in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ManifestError(f"Manifest must be a YAML mapping, got {type(data).__name__}")

    return DatasetManifest(data, manifest_path=str(path))


def get_adapter(manifest: DatasetManifest):
    """Instantiate the appropriate SourceAdapter for the given manifest.

    Returns
    -------
    SourceAdapter instance
        Ready to call .read() on.
    """
    source_type = manifest.source_type

    # Build source_config from manifest fields
    source_config: dict = {
        "source_type": source_type,
        "source_crs": manifest["source_crs"],
        "source_authority": manifest.source_authority,
        "source_tier": manifest.source_tier,
    }

    if source_type == "file":
        from harmony.pipelines.adapters.file_adapter import FileAdapter
        source_config["source_path"] = manifest["source_path"]
        if manifest.get("source_layer") is not None:
            source_config["source_layer"] = manifest["source_layer"]
        return FileAdapter(source_config)

    if source_type == "arcgis_rest":
        from harmony.pipelines.adapters.arcgis_rest_adapter import ArcGISRESTAdapter
        source_config["source_url"] = manifest["source_url"]
        source_config["source_bbox"] = manifest["source_bbox"]
        for opt in ("source_page_size", "source_out_sr", "source_where"):
            if manifest.get(opt) is not None:
                source_config[opt] = manifest[opt]
        return ArcGISRESTAdapter(source_config)

    if source_type == "osm_overpass":
        from harmony.pipelines.adapters.osm_adapter import OSMAdapter
        source_config["source_query"] = manifest["source_query"]
        source_config["source_bbox"] = manifest["source_bbox"]
        if manifest.get("source_endpoint"):
            source_config["source_endpoint"] = manifest["source_endpoint"]
        source_config["entity_type"] = manifest.entity_type
        return OSMAdapter(source_config)

    raise ManifestError(f"No adapter implemented for source_type {source_type!r}")
