# Harmony Pillar 2 — Source Adapter Base Interface
#
# Every source adapter implements SourceAdapter and emits RawFeature dicts.
# Adapters are pure readers — no Harmony semantics, no normalisation.
# Normalisation (CRS, geometry) is handled by downstream pipeline stages.
#
# ADR-018: All adapters must set source_tier, source_id fields in metadata.
# DEC-013: Provenance fields are system-assigned by the adapter layer.
# DEC-014: Adapters must declare source_crs — never auto-detect.

from __future__ import annotations

import abc
from typing import Any, Generator, TypedDict


class RawFeature(TypedDict, total=False):
    """A raw feature as emitted by any source adapter.

    The geometry key holds a GeoJSON geometry dict (or None if the source
    provides no geometry). Properties holds source-native attribute names
    and values — no Harmony field mapping applied at this stage.

    source_crs is the declared CRS for this feature. Per DEC-014, this must
    always be explicitly set by the adapter — never auto-detected. If the
    adapter cannot determine the CRS from the source config, it raises
    AdapterConfigError before emitting any features.
    """
    geometry: dict | None          # GeoJSON geometry object
    properties: dict[str, Any]     # Raw source attributes, unmapped
    source_crs: str                # EPSG code string, e.g. "EPSG:4326"
    source_id: str                 # Adapter-assigned feature identifier
    source_tier: int               # Data tier 1-4 per ADR-018
    adapter_type: str              # e.g. "file", "arcgis_rest", "osm_overpass"


class AdapterConfigError(ValueError):
    """Raised when a source config is missing required fields."""


class AdapterConnectionError(IOError):
    """Raised when the adapter cannot reach its data source."""


class SourceAdapter(abc.ABC):
    """Abstract base class for all Harmony Pillar 2 source adapters.

    Each concrete adapter handles one access pattern (file I/O, ArcGIS REST,
    OSM Overpass, etc.) and yields RawFeature dicts from its source.

    The adapter does NOT:
    - Transform coordinates
    - Validate geometry
    - Map source fields to Harmony fields
    - Write to the Pillar 1 API

    Parameters
    ----------
    source_config : dict
        The source section of a dataset manifest. The adapter validates the
        config fields it requires and raises AdapterConfigError if required
        fields are missing.
    """

    def __init__(self, source_config: dict) -> None:
        self._config = source_config
        self._validate_config()

    @abc.abstractmethod
    def _validate_config(self) -> None:
        """Validate the source config. Raise AdapterConfigError on failure."""

    @abc.abstractmethod
    def read(self) -> Generator[RawFeature, None, None]:
        """Yield raw features from the source, one at a time.

        Raises
        ------
        AdapterConnectionError
            If the source cannot be reached.
        AdapterConfigError
            If config is discovered to be invalid during reading.
        """

    @property
    def source_type(self) -> str:
        """Return the adapter's source_type string."""
        return self._config.get("source_type", "unknown")
