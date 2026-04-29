# Harmony Pillar 2 — ArcGIS REST Source Adapter
#
# Queries ArcGIS MapServer REST endpoints with bounding box filtering
# and automatic pagination via resultOffset / resultRecordCount.
#
# Covers:
#   - NSW Planning Portal — Land Zoning (EPI_Primary_Planning_Layers)
#   - NSW Spatial Services — DCDB Cadastre (maps.six.nsw.gov.au, layer 9)
#
# DEC-014: source_crs declared in config; never auto-detected.
# Brief §5, Gap Risk 5: Must paginate; validate total count vs retrieved.

from __future__ import annotations

import logging
import time
from typing import Generator

import httpx

from harmony.pipelines.adapters.base import (
    AdapterConfigError,
    AdapterConnectionError,
    RawFeature,
    SourceAdapter,
)

log = logging.getLogger(__name__)

_DEFAULT_PAGE_SIZE = 1000
_REQUEST_TIMEOUT = 30
_RETRY_DELAYS = (5, 15, 45)   # seconds between retries


class ArcGISRESTAdapter(SourceAdapter):
    """Read features from an ArcGIS MapServer REST endpoint.

    Required config keys:
        source_type:      "arcgis_rest"
        source_url:       MapServer layer URL ending in /{layer_id}
                          e.g. "https://…/MapServer/0"
        source_bbox:      [south, west, north, east] in source_crs
        source_crs:       declared input CRS, e.g. "EPSG:4326"
        source_authority: publisher name (determines source_tier)

    Optional config keys:
        source_tier:      int override (1-4)
        source_page_size: features per page (default 1_000)
        source_out_sr:    output spatial reference WKID (default 4326)
        source_where:     SQL WHERE clause (default "1=1")
    """

    ADAPTER_TYPE = "arcgis_rest"

    def _validate_config(self) -> None:
        for key in ("source_url", "source_bbox", "source_crs"):
            if not self._config.get(key):
                raise AdapterConfigError(
                    f"ArcGISRESTAdapter requires '{key}' in source config"
                )
        bbox = self._config["source_bbox"]
        if not (isinstance(bbox, (list, tuple)) and len(bbox) == 4):
            raise AdapterConfigError(
                "source_bbox must be [south, west, north, east]"
            )

    def _build_query_url(self) -> str:
        url = self._config["source_url"].rstrip("/")
        if not url.endswith("/query"):
            url = url + "/query"
        return url

    def _bbox_geometry(self) -> str:
        south, west, north, east = self._config["source_bbox"]
        return f"{west},{south},{east},{north}"

    def _get_total_count(self, query_url: str, where: str, bbox: str) -> int | None:
        """Query the server for total feature count."""
        params = {
            "where": where,
            "geometry": bbox,
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "inSR": "4326",
            "returnCountOnly": "true",
            "f": "json",
        }
        try:
            resp = httpx.get(query_url, params=params, timeout=_REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return data.get("count")
        except Exception as exc:
            log.warning("Could not retrieve feature count: %s", exc)
            return None

    def read(self) -> Generator[RawFeature, None, None]:
        query_url = self._build_query_url()
        bbox = self._bbox_geometry()
        where = self._config.get("source_where", "1=1")
        page_size = int(self._config.get("source_page_size", _DEFAULT_PAGE_SIZE))
        out_sr = int(self._config.get("source_out_sr", 4326))
        declared_crs = self._config["source_crs"]
        authority = self._config.get("source_authority", "unknown")
        tier = self._config.get("source_tier") or (1 if "nsw" in authority.lower() else 2)

        total = self._get_total_count(query_url, where, bbox)
        if total is not None:
            log.info("ArcGISRESTAdapter: server reports %d total features", total)

        offset = 0
        retrieved = 0

        while True:
            params = {
                "where": where,
                "geometry": bbox,
                "geometryType": "esriGeometryEnvelope",
                "spatialRel": "esriSpatialRelIntersects",
                "inSR": "4326",
                "outSR": str(out_sr),
                "outFields": "*",
                "resultOffset": str(offset),
                "resultRecordCount": str(page_size),
                "f": "geojson",
            }

            data = self._fetch_with_retry(query_url, params)

            features = data.get("features", [])
            if not features:
                break

            for feat in features:
                geom = feat.get("geometry")
                props = feat.get("properties") or {}
                # ArcGIS OBJECTID is the most stable internal ID available
                feature_id = props.get("OBJECTID") or props.get("objectid") or f"{offset}+{retrieved}"

                yield RawFeature(
                    geometry=geom,
                    properties=props,
                    source_crs=declared_crs,
                    source_id=str(feature_id),
                    source_tier=int(tier),
                    adapter_type=self.ADAPTER_TYPE,
                )
                retrieved += 1

            offset += len(features)

            exceeded = data.get("exceededTransferLimit", False)
            if not exceeded and len(features) < page_size:
                # Last page — server sent fewer features than requested
                break

            log.debug("ArcGISRESTAdapter: fetched %d features so far", retrieved)
            # Respectful pacing between pages
            time.sleep(0.5)

        if total is not None and retrieved != total:
            log.warning(
                "ArcGISRESTAdapter: server reported %d features but retrieved %d",
                total,
                retrieved,
            )

        log.info("ArcGISRESTAdapter: completed — %d features retrieved", retrieved)

    def _fetch_with_retry(self, url: str, params: dict) -> dict:
        last_exc: Exception | None = None
        for attempt, delay in enumerate((*_RETRY_DELAYS, None), start=1):
            try:
                resp = httpx.get(url, params=params, timeout=_REQUEST_TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if delay is None:
                    break
                log.warning(
                    "ArcGISRESTAdapter: attempt %d failed (%s), retrying in %ds",
                    attempt,
                    exc,
                    delay,
                )
                time.sleep(delay)

        raise AdapterConnectionError(
            f"ArcGISRESTAdapter: failed after {len(_RETRY_DELAYS) + 1} attempts: {last_exc}"
        )
