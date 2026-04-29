# Harmony Pillar 2 — Source Adapter Tests
#
# Tests the file adapter against local fixtures.
# ArcGIS REST and OSM adapters are tested with network fixtures (mocked)
# and live connectivity smoke tests (skipped if no network).

import json
import os
import pytest
from unittest.mock import patch, MagicMock

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

from harmony.pipelines.adapters.base import AdapterConfigError
from harmony.pipelines.adapters.file_adapter import FileAdapter
from harmony.pipelines.adapters.arcgis_rest_adapter import ArcGISRESTAdapter
from harmony.pipelines.adapters.osm_adapter import OSMAdapter


# ---------------------------------------------------------------------------
# FileAdapter tests
# ---------------------------------------------------------------------------

class TestFileAdapter:
    def test_reads_geojson_buildings(self):
        path = os.path.join(FIXTURES_DIR, "test_building.geojson")
        adapter = FileAdapter({
            "source_type": "file",
            "source_path": path,
            "source_crs": "EPSG:4326",
            "source_authority": "openstreetmap",
        })
        features = list(adapter.read())
        assert len(features) == 5

    def test_features_have_required_fields(self):
        path = os.path.join(FIXTURES_DIR, "test_building.geojson")
        adapter = FileAdapter({
            "source_type": "file",
            "source_path": path,
            "source_crs": "EPSG:4326",
            "source_authority": "openstreetmap",
        })
        features = list(adapter.read())
        for feat in features:
            assert "geometry" in feat
            assert "properties" in feat
            assert feat["source_crs"] == "EPSG:4326"
            assert "source_id" in feat
            assert feat["source_tier"] == 2  # OSM = Tier 2
            assert feat["adapter_type"] == "file"

    def test_reads_road_geojson(self):
        path = os.path.join(FIXTURES_DIR, "test_road.geojson")
        adapter = FileAdapter({
            "source_type": "file",
            "source_path": path,
            "source_crs": "EPSG:4326",
            "source_authority": "openstreetmap",
        })
        features = list(adapter.read())
        assert len(features) == 3

    def test_missing_source_path_raises(self):
        with pytest.raises(AdapterConfigError, match="source_path"):
            FileAdapter({
                "source_type": "file",
                "source_crs": "EPSG:4326",
            })

    def test_missing_source_crs_raises(self):
        path = os.path.join(FIXTURES_DIR, "test_building.geojson")
        with pytest.raises(AdapterConfigError, match="source_crs"):
            FileAdapter({
                "source_type": "file",
                "source_path": path,
            })

    def test_nonexistent_path_raises(self):
        with pytest.raises(AdapterConfigError, match="does not exist"):
            FileAdapter({
                "source_type": "file",
                "source_path": "/nonexistent/path/file.geojson",
                "source_crs": "EPSG:4326",
            })

    def test_unsupported_extension_raises(self):
        # __file__ is a .py file — not in the supported geospatial extension set
        with pytest.raises(AdapterConfigError, match="unsupported file extension"):
            FileAdapter({
                "source_type": "file",
                "source_path": __file__,
                "source_crs": "EPSG:4326",
            })

    def test_nsw_authority_assigns_tier_1(self):
        path = os.path.join(FIXTURES_DIR, "test_gda2020.geojson")
        adapter = FileAdapter({
            "source_type": "file",
            "source_path": path,
            "source_crs": "EPSG:7844",
            "source_authority": "nsw_spatial_services",
        })
        features = list(adapter.read())
        assert features[0]["source_tier"] == 1

    def test_gda2020_declared_crs_preserved(self):
        path = os.path.join(FIXTURES_DIR, "test_gda2020.geojson")
        adapter = FileAdapter({
            "source_type": "file",
            "source_path": path,
            "source_crs": "EPSG:7844",
            "source_authority": "nsw_spatial_services",
        })
        features = list(adapter.read())
        assert features[0]["source_crs"] == "EPSG:7844"


# ---------------------------------------------------------------------------
# ArcGIS REST adapter tests (mocked)
# ---------------------------------------------------------------------------

_ARCGIS_MOCK_PAGE_1 = {
    "features": [
        {
            "geometry": {"type": "Polygon", "coordinates": [[[151.3, -33.4], [151.31, -33.4], [151.31, -33.41], [151.3, -33.41], [151.3, -33.4]]]},
            "properties": {"OBJECTID": 1, "SYM_CODE": "R2", "LAY_CLASS": "Low Density Residential", "PCO_REF_KEY": "KEY001", "LGA_NAME": "Central Coast"},
        },
        {
            "geometry": {"type": "Polygon", "coordinates": [[[151.4, -33.3], [151.41, -33.3], [151.41, -33.31], [151.4, -33.31], [151.4, -33.3]]]},
            "properties": {"OBJECTID": 2, "SYM_CODE": "E1", "LAY_CLASS": "National Parks and Nature Reserves", "PCO_REF_KEY": "KEY002", "LGA_NAME": "Central Coast"},
        },
    ],
    "exceededTransferLimit": False,
}

_ARCGIS_MOCK_COUNT = {"count": 2}


class TestArcGISRESTAdapter:
    def _make_config(self):
        return {
            "source_type": "arcgis_rest",
            "source_url": "https://example.com/arcgis/rest/services/Planning/MapServer/0",
            "source_bbox": [-33.55, 151.15, -33.15, 151.75],
            "source_crs": "EPSG:4326",
            "source_authority": "nsw_planning_portal",
        }

    def test_missing_url_raises(self):
        with pytest.raises(AdapterConfigError, match="source_url"):
            ArcGISRESTAdapter({
                "source_type": "arcgis_rest",
                "source_bbox": [-33.55, 151.15, -33.15, 151.75],
                "source_crs": "EPSG:4326",
            })

    def test_invalid_bbox_raises(self):
        with pytest.raises(AdapterConfigError, match="source_bbox"):
            ArcGISRESTAdapter({
                "source_type": "arcgis_rest",
                "source_url": "https://example.com/arcgis/rest/services/Planning/MapServer/0",
                "source_bbox": [-33.55, 151.15],  # Only 2 elements
                "source_crs": "EPSG:4326",
            })

    def test_reads_features_with_mock(self):
        config = self._make_config()
        adapter = ArcGISRESTAdapter(config)

        def mock_get(url, params=None, timeout=None):
            resp = MagicMock()
            resp.raise_for_status = lambda: None
            if params and params.get("returnCountOnly") == "true":
                resp.json.return_value = _ARCGIS_MOCK_COUNT
            else:
                resp.json.return_value = _ARCGIS_MOCK_PAGE_1
            return resp

        with patch("harmony.pipelines.adapters.arcgis_rest_adapter.httpx.get", side_effect=mock_get):
            features = list(adapter.read())

        assert len(features) == 2
        assert features[0]["source_crs"] == "EPSG:4326"
        assert features[0]["source_tier"] == 1  # NSW = Tier 1
        assert features[0]["adapter_type"] == "arcgis_rest"
        assert features[0]["properties"]["SYM_CODE"] == "R2"

    def test_source_id_from_objectid(self):
        config = self._make_config()
        adapter = ArcGISRESTAdapter(config)

        def mock_get(url, params=None, timeout=None):
            resp = MagicMock()
            resp.raise_for_status = lambda: None
            if params and params.get("returnCountOnly") == "true":
                resp.json.return_value = {"count": 1}
            else:
                resp.json.return_value = {
                    "features": [_ARCGIS_MOCK_PAGE_1["features"][0]],
                    "exceededTransferLimit": False,
                }
            return resp

        with patch("harmony.pipelines.adapters.arcgis_rest_adapter.httpx.get", side_effect=mock_get):
            features = list(adapter.read())

        assert features[0]["source_id"] == "1"  # OBJECTID = 1


# ---------------------------------------------------------------------------
# OSM Adapter tests (mocked)
# ---------------------------------------------------------------------------

_OSM_MOCK_RESPONSE = {
    "elements": [
        # A node (for geometry reconstruction)
        {"type": "node", "id": 100, "lat": -33.420, "lon": 151.300},
        {"type": "node", "id": 101, "lat": -33.420, "lon": 151.301},
        {"type": "node", "id": 102, "lat": -33.421, "lon": 151.301},
        {"type": "node", "id": 103, "lat": -33.421, "lon": 151.300},
        # A building way (closed polygon)
        {
            "type": "way",
            "id": 999001,
            "nodes": [100, 101, 102, 103, 100],
            "tags": {"building": "residential", "name": "OSM Test Building"},
        },
        # A road way (open linestring)
        {"type": "node", "id": 200, "lat": -33.430, "lon": 151.310},
        {"type": "node", "id": 201, "lat": -33.435, "lon": 151.315},
        {
            "type": "way",
            "id": 999002,
            "nodes": [200, 201],
            "tags": {"highway": "residential", "name": "OSM Test Road"},
        },
    ]
}


class TestOSMAdapter:
    def _make_config(self):
        return {
            "source_type": "osm_overpass",
            "source_query": '[out:json];way["building"]({{bbox}});(._;>;);out body;',
            "source_bbox": [-33.55, 151.15, -33.15, 151.75],
        }

    def test_missing_query_raises(self):
        with pytest.raises(AdapterConfigError, match="source_query"):
            OSMAdapter({
                "source_type": "osm_overpass",
                "source_bbox": [-33.55, 151.15, -33.15, 151.75],
            })

    def test_missing_bbox_raises(self):
        with pytest.raises(AdapterConfigError, match="source_bbox"):
            OSMAdapter({
                "source_type": "osm_overpass",
                "source_query": '[out:json];way["building"]({{bbox}});(._;>;);out body;',
            })

    def test_bbox_substitution(self):
        config = self._make_config()
        adapter = OSMAdapter(config)
        query = adapter._build_query()
        assert "{{bbox}}" not in query
        assert "-33.55,151.15,-33.15,151.75" in query

    def test_reads_features_with_mock(self):
        config = self._make_config()
        adapter = OSMAdapter(config)

        def mock_post(url, data=None, timeout=None):
            resp = MagicMock()
            resp.raise_for_status = lambda: None
            resp.json.return_value = _OSM_MOCK_RESPONSE
            return resp

        with patch("harmony.pipelines.adapters.osm_adapter.httpx.post", side_effect=mock_post), \
             patch("harmony.pipelines.adapters.osm_adapter._rate_limit"):
            features = list(adapter.read())

        # Should yield 2 way features.
        # Nodes without tags (skeleton nodes for way geometry) are not yielded.
        way_features = [f for f in features if f.get("source_id", "").startswith("osm:way/")]
        assert len(way_features) == 2

    def test_building_way_becomes_polygon(self):
        config = self._make_config()
        adapter = OSMAdapter(config)

        def mock_post(url, data=None, timeout=None):
            resp = MagicMock()
            resp.raise_for_status = lambda: None
            resp.json.return_value = _OSM_MOCK_RESPONSE
            return resp

        with patch("harmony.pipelines.adapters.osm_adapter.httpx.post", side_effect=mock_post), \
             patch("harmony.pipelines.adapters.osm_adapter._rate_limit"):
            features = list(adapter.read())

        building = next(f for f in features if f.get("properties", {}).get("building"))
        assert building["geometry"]["type"] == "Polygon"
        assert building["source_crs"] == "EPSG:4326"
        assert building["source_tier"] == 2
        assert building["source_id"] == "osm:way/999001"

    def test_road_way_becomes_linestring(self):
        config = self._make_config()
        adapter = OSMAdapter(config)

        def mock_post(url, data=None, timeout=None):
            resp = MagicMock()
            resp.raise_for_status = lambda: None
            resp.json.return_value = _OSM_MOCK_RESPONSE
            return resp

        with patch("harmony.pipelines.adapters.osm_adapter.httpx.post", side_effect=mock_post), \
             patch("harmony.pipelines.adapters.osm_adapter._rate_limit"):
            features = list(adapter.read())

        road = next(f for f in features if f.get("properties", {}).get("highway"))
        assert road["geometry"]["type"] == "LineString"
        assert road["source_id"] == "osm:way/999002"

    def test_osm_crs_always_4326(self):
        config = self._make_config()
        adapter = OSMAdapter(config)

        def mock_post(url, data=None, timeout=None):
            resp = MagicMock()
            resp.raise_for_status = lambda: None
            resp.json.return_value = _OSM_MOCK_RESPONSE
            return resp

        with patch("harmony.pipelines.adapters.osm_adapter.httpx.post", side_effect=mock_post), \
             patch("harmony.pipelines.adapters.osm_adapter._rate_limit"):
            features = list(adapter.read())

        for feat in features:
            assert feat["source_crs"] == "EPSG:4326"
