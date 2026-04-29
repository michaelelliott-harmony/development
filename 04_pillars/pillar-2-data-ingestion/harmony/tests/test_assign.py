# Harmony Pillar 2 — Cell Assignment Tests (M3)
#
# Tests: geometry-adaptive resolution, primary cell computation,
# secondary cell enumeration, manifest floor enforcement.

import math
import pytest
from harmony.pipelines.cell_key import derive, cell_edge_m, adaptive_resolution
from harmony.pipelines.assign import assign, CellAssignment


def _make_validated(geom: dict) -> dict:
    """Build a minimal ValidatedFeature for assignment testing."""
    return {
        "geometry": geom,
        "geometry_wgs84": geom,
        "properties": {},
        "source_crs": "EPSG:4326",
        "source_id": "test",
        "source_tier": 2,
        "adapter_type": "file",
        "crs_transform_epoch": "2026-04-25T00:00:00+00:00",
        "transformation_method": "passthrough",
        "coordinate_bounds_ok": True,
        "geometry_valid": True,
        "geometry_repaired": False,
        "repair_description": None,
    }


class TestCellEdgeLengths:
    def test_r06_is_roughly_2km(self):
        edge = cell_edge_m(6)
        assert 1500 < edge < 3500

    def test_r08_is_roughly_140m(self):
        edge = cell_edge_m(8)
        assert 80 < edge < 250

    def test_r10_is_roughly_9m(self):
        edge = cell_edge_m(10)
        assert 5 < edge < 20

    def test_resolution_decreases_monotonically(self):
        edges = [cell_edge_m(r) for r in range(6, 13)]
        for i in range(len(edges) - 1):
            assert edges[i] > edges[i + 1]


class TestAdaptiveResolution:
    def test_small_building_50m_floor6(self):
        r = adaptive_resolution(50, floor_level=6)
        # A 50m bbox should resolve to r10 (building scale)
        assert r >= 10

    def test_large_zoning_5000m_floor6(self):
        r = adaptive_resolution(5000, floor_level=6)
        # A 5km bbox should resolve to ~r07, but floor keeps it at r06
        assert r >= 6

    def test_floor_respected(self):
        # Very small feature — without floor would go to r12
        r = adaptive_resolution(1, floor_level=8)
        assert r >= 8

    def test_max_resolution_capped(self):
        r = adaptive_resolution(0.001, floor_level=6)
        assert r <= 12

    def test_zero_diagonal_returns_max(self):
        # Zero diagonal → degenerate; returns max resolution (not floor)
        r = adaptive_resolution(0, floor_level=6)
        assert r == 12


class TestDeriveFunction:
    def test_central_coast_matches_pillar1(self):
        # Verify our vendored derive() matches Pillar 1's derive.py exactly
        import sys
        sys.path.insert(0, '/workspace/development/04_pillars/pillar-1-spatial-substrate/harmony/packages/cell-key/src')
        import derive as p1_derive
        for lat, lon, res in [(-33.4, 151.5, 8), (-33.2, 151.3, 10), (-33.55, 151.75, 6)]:
            p1_key = p1_derive.derive_cell_key(lat, lon, res, "cc")
            p2_coords = derive(lat, lon, res, "cc")
            assert p2_coords.cell_key == p1_key, (
                f"Key mismatch at ({lat},{lon}) r{res}: p1={p1_key} p2={p2_coords.cell_key}"
            )

    def test_returns_correct_region_code(self):
        coords = derive(-33.4, 151.5, 8, "cc")
        assert coords.region_code == "cc"
        assert ":cc:" in coords.cell_key

    def test_cube_face_and_grid_within_range(self):
        coords = derive(-33.4, 151.5, 8, "cc")
        assert 0 <= coords.cube_face <= 5
        grid_n = 4 ** 8
        assert 0 <= coords.face_grid_u < grid_n
        assert 0 <= coords.face_grid_v < grid_n

    def test_centroid_lat_lon_in_bounds(self):
        coords = derive(-33.4, 151.5, 10, "cc")
        assert -90 <= coords.centroid_lat <= 90
        assert -180 <= coords.centroid_lon <= 180


class TestPolygonAssignment:
    def _make_building_polygon(self):
        # Small building polygon (~30m × 20m) at Central Coast
        return {
            "type": "Polygon",
            "coordinates": [[
                [151.3000, -33.4200],
                [151.3003, -33.4200],
                [151.3003, -33.4202],
                [151.3000, -33.4202],
                [151.3000, -33.4200],
            ]]
        }

    def test_polygon_primary_by_centroid(self):
        geom = self._make_building_polygon()
        feat = _make_validated(geom)
        result = assign(feat, resolution_floor=10, region_code="cc")
        assert result is not None
        assert result.assigned_by == "centroid"

    def test_resolution_at_floor(self):
        geom = self._make_building_polygon()
        feat = _make_validated(geom)
        result = assign(feat, resolution_floor=10, region_code="cc")
        assert result is not None
        assert result.resolution_level >= 10

    def test_primary_cell_has_valid_key(self):
        geom = self._make_building_polygon()
        feat = _make_validated(geom)
        result = assign(feat, resolution_floor=10, region_code="cc")
        assert result is not None
        key = result.primary.cell_key
        assert key.startswith("hsam:r")
        assert ":cc:" in key

    def test_secondary_cells_all_unique(self):
        geom = self._make_building_polygon()
        feat = _make_validated(geom)
        result = assign(feat, resolution_floor=10, region_code="cc")
        assert result is not None
        all_keys = [result.primary.cell_key] + [c.cell_key for c in result.secondary]
        assert len(all_keys) == len(set(all_keys))

    def test_large_polygon_has_multiple_cells(self):
        # A large zoning polygon (~5km × 5km)
        geom = {
            "type": "Polygon",
            "coordinates": [[
                [151.20, -33.50],
                [151.25, -33.50],
                [151.25, -33.55],
                [151.20, -33.55],
                [151.20, -33.50],
            ]]
        }
        feat = _make_validated(geom)
        result = assign(feat, resolution_floor=6, region_code="cc")
        assert result is not None
        total_cells = 1 + len(result.secondary)
        assert total_cells > 1


class TestLineAssignment:
    def _make_road_line(self):
        # A road segment of ~1km
        return {
            "type": "LineString",
            "coordinates": [
                [151.300, -33.420],
                [151.310, -33.420],
                [151.320, -33.415],
            ]
        }

    def test_linestring_primary_by_midpoint(self):
        geom = self._make_road_line()
        feat = _make_validated(geom)
        result = assign(feat, resolution_floor=8, region_code="cc")
        assert result is not None
        assert result.assigned_by == "midpoint"

    def test_road_at_r08_or_above(self):
        geom = self._make_road_line()
        feat = _make_validated(geom)
        result = assign(feat, resolution_floor=8, region_code="cc")
        assert result is not None
        assert result.resolution_level >= 8


class TestNullGeometryAssignment:
    def test_null_geometry_returns_none(self):
        feat = _make_validated(None)
        result = assign(feat, resolution_floor=10, region_code="cc")
        assert result is None
