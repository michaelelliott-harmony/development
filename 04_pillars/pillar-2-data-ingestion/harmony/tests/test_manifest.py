# Harmony Pillar 2 — Manifest + Extract + Dedup Tests (M4)

import os
import pytest
from harmony.pipelines.manifest import load, ManifestError, DatasetManifest
from harmony.pipelines.extract import extract as extract_entity
from harmony.pipelines.dedup import DedupIndex, DedupMatch, LowConfidenceMatch

MANIFESTS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "pipelines", "manifests"
)


class TestManifestLoading:
    def test_loads_zoning_manifest(self):
        m = load(os.path.join(MANIFESTS_DIR, "central-coast-zoning.yaml"))
        assert m.source_type == "arcgis_rest"
        assert m.entity_type == "zoning_area"
        assert m.entity_subtype_code == "zon"
        assert m.source_tier == 1
        assert m.resolution_floor == 6

    def test_loads_cadastre_manifest(self):
        m = load(os.path.join(MANIFESTS_DIR, "central-coast-cadastre.yaml"))
        assert m.source_type == "arcgis_rest"
        assert m.entity_type == "cadastral_lot"
        assert m.entity_subtype_code == "cad"
        assert m.resolution_floor == 8

    def test_loads_buildings_manifest(self):
        m = load(os.path.join(MANIFESTS_DIR, "central-coast-buildings-osm.yaml"))
        assert m.source_type == "osm_overpass"
        assert m.entity_type == "building"
        assert m.entity_subtype_code == "bld"
        assert m.source_tier == 2
        assert m.resolution_floor == 10

    def test_loads_roads_manifest(self):
        m = load(os.path.join(MANIFESTS_DIR, "central-coast-roads-osm.yaml"))
        assert m.source_type == "osm_overpass"
        assert m.entity_type == "road_segment"
        assert m.entity_subtype_code == "rod"
        assert m.resolution_floor == 8

    def test_all_four_manifests_have_source_crs(self):
        for fname in [
            "central-coast-zoning.yaml",
            "central-coast-cadastre.yaml",
            "central-coast-buildings-osm.yaml",
            "central-coast-roads-osm.yaml",
        ]:
            m = load(os.path.join(MANIFESTS_DIR, fname))
            assert m["source_crs"], f"{fname} is missing source_crs"

    def test_invalid_source_type_raises(self):
        with pytest.raises(ManifestError, match="source_type"):
            DatasetManifest({
                "source_type": "wfs",
                "target_entity_type": "zoning_area",
                "source_crs": "EPSG:4326",
            })

    def test_invalid_entity_type_raises(self):
        with pytest.raises(ManifestError, match="target_entity_type"):
            DatasetManifest({
                "source_type": "file",
                "target_entity_type": "unknown_type",
                "source_crs": "EPSG:4326",
                "source_path": "/tmp/test.geojson",
            })

    def test_missing_source_crs_raises(self):
        with pytest.raises(ManifestError, match="source_crs"):
            DatasetManifest({
                "source_type": "file",
                "target_entity_type": "building",
                "source_path": "/tmp/test.geojson",
            })

    def test_file_without_source_path_raises(self):
        with pytest.raises(ManifestError, match="source_path"):
            DatasetManifest({
                "source_type": "file",
                "target_entity_type": "building",
                "source_crs": "EPSG:4326",
            })


class TestEntityExtraction:
    def _make_feature(self, props: dict) -> dict:
        return {
            "geometry_wgs84": {
                "type": "Polygon",
                "coordinates": [[
                    [151.30, -33.42], [151.31, -33.42],
                    [151.31, -33.43], [151.30, -33.43], [151.30, -33.42],
                ]]
            },
            "properties": props,
            "source_crs": "EPSG:4326",
            "source_id": "test_001",
            "source_tier": 1,
            "adapter_type": "arcgis_rest",
            "crs_transform_epoch": "2026-04-25T00:00:00+00:00",
            "transformation_method": "passthrough",
            "coordinate_bounds_ok": True,
            "geometry_valid": True,
            "geometry_repaired": False,
            "repair_description": None,
        }

    def _make_assignment(self):
        from harmony.pipelines.cell_key import derive, CellCoordinates
        from harmony.pipelines.assign import CellAssignment
        coords = derive(-33.42, 151.30, 10, "cc")
        return CellAssignment(primary=coords, secondary=[], resolution_level=10, assigned_by="centroid")

    def test_zoning_extraction(self):
        m = load(os.path.join(MANIFESTS_DIR, "central-coast-zoning.yaml"))
        feat = self._make_feature({
            "SYM_CODE": "R2",
            "LAY_CLASS": "Low Density Residential",
            "EPI_NAME": "Central Coast LEP 2022",
            "LGA_NAME": "Central Coast",
            "PCO_REF_KEY": "KEY_001",
        })
        assignment = self._make_assignment()
        payload = extract_entity(feat, assignment, m, "run_test")

        assert payload["entity_subtype"] == "zon"
        assert payload["metadata"]["zone_code"] == "R2"
        assert payload["metadata"]["zone_name"] == "Low Density Residential"
        assert "R2" in payload["_known_names"]
        assert payload["metadata"]["source_tier"] == 1
        assert payload["metadata"]["fidelity_coverage"]["structural"]["status"] == "available"
        assert payload["metadata"]["fidelity_coverage"]["photorealistic"]["status"] == "pending"

    def test_building_extraction(self):
        m = load(os.path.join(MANIFESTS_DIR, "central-coast-buildings-osm.yaml"))
        feat = self._make_feature({
            "building": "residential",
            "name": "Test House",
            "addr:housenumber": "42",
            "addr:street": "Ocean Drive",
            "height": "8.5",
            "building:levels": "2",
        })
        assignment = self._make_assignment()
        payload = extract_entity(feat, assignment, m, "run_test")

        assert payload["entity_subtype"] == "bld"
        assert payload["metadata"]["building_type"] == "residential"
        assert payload["metadata"]["height_m"] == 8.5
        assert payload["metadata"]["levels"] == 2
        assert "Test House" in payload["_known_names"]
        assert "42 Ocean Drive" in payload["_known_names"]
        assert payload["metadata"]["source_tier"] == 2

    def test_road_extraction_boolean_normalisation(self):
        m = load(os.path.join(MANIFESTS_DIR, "central-coast-roads-osm.yaml"))
        feat = self._make_feature({
            "highway": "primary",
            "name": "Pacific Highway",
            "oneway": "yes",
            "bridge": "no",
            "maxspeed": "80",
            "lanes": "4",
        })
        assignment = self._make_assignment()
        payload = extract_entity(feat, assignment, m, "run_test")

        assert payload["entity_subtype"] == "rod"
        assert payload["metadata"]["road_class"] == "primary"
        assert payload["metadata"]["is_oneway"] is True
        assert payload["metadata"]["is_bridge"] is False
        assert payload["metadata"]["speed_limit_kmh"] == 80
        assert payload["metadata"]["lane_count"] == 4
        assert "Pacific Highway" in payload["_known_names"]

    def test_fidelity_coverage_always_present(self):
        m = load(os.path.join(MANIFESTS_DIR, "central-coast-zoning.yaml"))
        feat = self._make_feature({"SYM_CODE": "E1", "LAY_CLASS": "National Parks", "PCO_REF_KEY": "K2"})
        payload = extract_entity(feat, self._make_assignment(), m, "run_test")
        fc = payload["metadata"]["fidelity_coverage"]
        # Non-negotiable: both slots must always be present
        assert "structural" in fc
        assert "photorealistic" in fc
        assert fc["structural"]["status"] == "available"
        assert fc["photorealistic"]["status"] == "pending"


class TestDeduplication:
    def test_source_id_match_raises_dedup(self, tmp_path):
        with DedupIndex(tmp_path, "building") as idx:
            idx.register("hent_abc123", "osm:way/12345", -33.42, 151.30, "test_dataset")
            with pytest.raises(DedupMatch) as exc_info:
                idx.check(
                    source_id="osm:way/12345",
                    centroid_lat=-33.42,
                    centroid_lon=151.30,
                    spatial_threshold_m=15.0,
                    strategy="source_id",
                )
            assert exc_info.value.match_method == "source_id"
            assert exc_info.value.confidence == 1.0

    def test_different_source_id_passes(self, tmp_path):
        with DedupIndex(tmp_path, "building") as idx:
            idx.register("hent_abc123", "osm:way/12345", -33.42, 151.30, "test_dataset")
            # Should not raise
            idx.check(
                source_id="osm:way/99999",
                centroid_lat=-33.42,
                centroid_lon=151.30,
                spatial_threshold_m=15.0,
                strategy="source_id",
            )

    def test_spatial_proximity_close_raises(self, tmp_path):
        with DedupIndex(tmp_path, "building") as idx:
            idx.register("hent_abc123", "osm:way/12345", -33.42000, 151.30000, "test")
            # 3m away — within 15m threshold
            with pytest.raises(DedupMatch) as exc_info:
                idx.check(
                    source_id="osm:way/99999",
                    centroid_lat=-33.42003,   # ~3m north
                    centroid_lon=151.30000,
                    spatial_threshold_m=15.0,
                    strategy="spatial_proximity",
                )
            assert exc_info.value.match_method == "spatial_proximity"

    def test_spatial_proximity_far_passes(self, tmp_path):
        with DedupIndex(tmp_path, "building") as idx:
            idx.register("hent_abc123", "osm:way/12345", -33.42000, 151.30000, "test")
            # 200m away — beyond 15m threshold
            idx.check(
                source_id="osm:way/99999",
                centroid_lat=-33.4218,   # ~200m south
                centroid_lon=151.30000,
                spatial_threshold_m=15.0,
                strategy="spatial_proximity",
            )  # Should not raise

    def test_hybrid_strategy_source_id_wins(self, tmp_path):
        """source_id match takes priority over spatial in hybrid mode."""
        with DedupIndex(tmp_path, "building") as idx:
            idx.register("hent_abc123", "osm:way/12345", -33.42000, 151.30000, "test")
            with pytest.raises(DedupMatch) as exc_info:
                idx.check(
                    source_id="osm:way/12345",
                    centroid_lat=-33.50000,  # Far away spatially
                    centroid_lon=152.00000,
                    spatial_threshold_m=15.0,
                    strategy="hybrid",
                )
            assert exc_info.value.match_method == "source_id"
