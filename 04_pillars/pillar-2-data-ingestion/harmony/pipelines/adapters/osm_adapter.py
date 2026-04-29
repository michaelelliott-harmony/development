# Harmony Pillar 2 — OSM Overpass Source Adapter
#
# Queries the OpenStreetMap Overpass API with tag and bounding box filters.
# Converts OSM nodes/ways/relations to GeoJSON features.
#
# ADR-018: OSM = Tier 2 (Open Authoritative)
# Brief §3, Gap Risk 6: Min 5-second interval between requests.
# p2-entity-schemas.md: Buildings are OSM ways; roads are OSM ways.
#
# OSM data is always EPSG:4326 — no CRS transform required.
# source_crs is set to "EPSG:4326" unconditionally for all OSM features.

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

_OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"
_MIN_REQUEST_INTERVAL = 5.0   # seconds — Overpass rate limit requirement
_REQUEST_TIMEOUT = 120        # seconds — Overpass queries can be slow
_RETRY_DELAYS = (30, 90, 270)

_last_request_time: float = 0.0


def _rate_limit() -> None:
    """Block until the minimum interval since the last Overpass request has elapsed."""
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.monotonic()


class OSMAdapter(SourceAdapter):
    """Read features from the OpenStreetMap Overpass API.

    Required config keys:
        source_type:  "osm_overpass"
        source_query: Overpass QL query string. Use {{bbox}} placeholder
                      for the bounding box, e.g.:
                      '[out:json];way["building"]({{bbox}});(._;>;);out body;'
        source_bbox:  [south, west, north, east] in WGS84

    Optional config keys:
        source_endpoint: Overpass API URL (default: overpass-api.de)
        entity_type:     hint for downstream processing ("building", "road")
    """

    ADAPTER_TYPE = "osm_overpass"
    OSM_CRS = "EPSG:4326"
    SOURCE_TIER = 2  # Open Authoritative per ADR-018

    def _validate_config(self) -> None:
        for key in ("source_query", "source_bbox"):
            if not self._config.get(key):
                raise AdapterConfigError(
                    f"OSMAdapter requires '{key}' in source config"
                )
        bbox = self._config["source_bbox"]
        if not (isinstance(bbox, (list, tuple)) and len(bbox) == 4):
            raise AdapterConfigError(
                "source_bbox must be [south, west, north, east]"
            )

    def _build_query(self) -> str:
        south, west, north, east = self._config["source_bbox"]
        bbox_str = f"{south},{west},{north},{east}"
        return self._config["source_query"].replace("{{bbox}}", bbox_str)

    def read(self) -> Generator[RawFeature, None, None]:
        query = self._build_query()
        endpoint = self._config.get("source_endpoint", _OVERPASS_ENDPOINT)

        _rate_limit()
        raw = self._fetch_with_retry(endpoint, query)

        elements = raw.get("elements", [])
        log.info("OSMAdapter: received %d elements", len(elements))

        # Build a node coordinate index for way geometry reconstruction
        node_coords: dict[int, tuple[float, float]] = {}
        for el in elements:
            if el.get("type") == "node" and "lat" in el and "lon" in el:
                node_coords[el["id"]] = (el["lon"], el["lat"])

        for el in elements:
            el_type = el.get("type")
            if el_type == "node":
                # Only emit nodes that carry tags — skeleton nodes (fetched via
                # `(._;>;)` for way geometry reconstruction) have no tags and
                # should not be yielded as standalone features.
                if not el.get("tags"):
                    continue
                feature = self._node_to_feature(el)
            elif el_type == "way":
                feature = self._way_to_feature(el, node_coords)
            elif el_type == "relation":
                feature = self._relation_to_feature(el, node_coords)
            else:
                continue

            if feature is not None:
                yield feature

    def _node_to_feature(self, el: dict) -> RawFeature | None:
        lat = el.get("lat")
        lon = el.get("lon")
        if lat is None or lon is None:
            return None

        return RawFeature(
            geometry={"type": "Point", "coordinates": [lon, lat]},
            properties=el.get("tags", {}),
            source_crs=self.OSM_CRS,
            source_id=f"osm:node/{el['id']}",
            source_tier=self.SOURCE_TIER,
            adapter_type=self.ADAPTER_TYPE,
        )

    def _way_to_feature(
        self, el: dict, node_coords: dict[int, tuple[float, float]]
    ) -> RawFeature | None:
        node_refs = el.get("nodes", [])
        if len(node_refs) < 2:
            return None

        coords = []
        missing = 0
        for ref in node_refs:
            coord = node_coords.get(ref)
            if coord is None:
                missing += 1
                continue
            coords.append(list(coord))

        if missing > 0:
            log.debug("OSMAdapter way/%d: %d node refs missing coordinates", el["id"], missing)

        if len(coords) < 2:
            return None

        tags = el.get("tags", {})

        # Closed ways with a building/landuse/area tag are polygons
        is_closed = (
            len(node_refs) >= 4
            and node_refs[0] == node_refs[-1]
            and (
                "building" in tags
                or "landuse" in tags
                or "natural" in tags
                or "area" in tags
                or tags.get("area") == "yes"
            )
        )

        if is_closed:
            # Ensure ring is closed in coordinate list
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            geometry = {"type": "Polygon", "coordinates": [coords]}
        else:
            geometry = {"type": "LineString", "coordinates": coords}

        return RawFeature(
            geometry=geometry,
            properties=tags,
            source_crs=self.OSM_CRS,
            source_id=f"osm:way/{el['id']}",
            source_tier=self.SOURCE_TIER,
            adapter_type=self.ADAPTER_TYPE,
        )

    def _relation_to_feature(
        self, el: dict, node_coords: dict[int, tuple[float, float]]
    ) -> RawFeature | None:
        """Convert a multipolygon relation to a GeoJSON MultiPolygon.

        Only processes relations with type=multipolygon. Other relation
        types are skipped. Member ways must already be in node_coords.
        """
        tags = el.get("tags", {})
        if tags.get("type") != "multipolygon":
            return None

        outer_rings = []
        inner_rings = []

        for member in el.get("members", []):
            if member.get("type") != "way":
                continue
            role = member.get("role", "outer")
            way_nodes = member.get("nodes", [])
            if not way_nodes:
                continue

            coords = [list(node_coords[n]) for n in way_nodes if n in node_coords]
            if len(coords) < 3:
                continue

            if coords[0] != coords[-1]:
                coords.append(coords[0])

            if role == "outer":
                outer_rings.append(coords)
            elif role == "inner":
                inner_rings.append(coords)

        if not outer_rings:
            return None

        # Simple case: one outer ring
        if len(outer_rings) == 1:
            geometry = {
                "type": "Polygon",
                "coordinates": [outer_rings[0]] + inner_rings,
            }
        else:
            geometry = {
                "type": "MultiPolygon",
                "coordinates": [[ring] for ring in outer_rings],
            }

        return RawFeature(
            geometry=geometry,
            properties=tags,
            source_crs=self.OSM_CRS,
            source_id=f"osm:relation/{el['id']}",
            source_tier=self.SOURCE_TIER,
            adapter_type=self.ADAPTER_TYPE,
        )

    def _fetch_with_retry(self, endpoint: str, query: str) -> dict:
        last_exc: Exception | None = None
        for attempt, delay in enumerate((*_RETRY_DELAYS, None), start=1):
            try:
                resp = httpx.post(
                    endpoint,
                    data={"data": query},
                    timeout=_REQUEST_TIMEOUT,
                )
                resp.raise_for_status()
                return resp.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if delay is None:
                    break
                log.warning(
                    "OSMAdapter: attempt %d failed (%s), retrying in %ds",
                    attempt,
                    exc,
                    delay,
                )
                _rate_limit()
                time.sleep(delay)

        raise AdapterConnectionError(
            f"OSMAdapter: Overpass API unavailable after {len(_RETRY_DELAYS) + 1} attempts: {last_exc}"
        )
