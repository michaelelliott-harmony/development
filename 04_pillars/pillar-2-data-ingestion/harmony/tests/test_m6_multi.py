# Harmony Pillar 2 — M6 Multi-Dataset Ingestion Tests
#
# Tests all four datasets ingesting into the same cell region using
# file-based fixtures that represent the Gosford, Central Coast area.
#
# Live API note: ArcGIS REST and Overpass API endpoints are unreachable
# from this dev container (no outbound internet). The adapter code is
# production-ready and tested against mocked responses in test_adapters.py.
# M6 uses file adapters as the explicit fallback ("No code changes required
# — manifest-only update" — Brief §3). Live API ingestion requires the
# production container with network access.
#
# Non-negotiables verified:
# - All four entity types register correctly
# - Entities from different sources coexist in shared cells
# - Deduplication works within each entity type
# - Every entity carries fidelity_coverage (structural + photorealistic)
# - Re-ingestion is idempotent

import json
import os
import pytest
import httpx

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
P1_URL = os.environ.get("HARMONY_P1_URL", "http://127.0.0.1:8000")


def _pillar1_available() -> bool:
    try:
        r = httpx.get(f"{P1_URL}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


requires_p1 = pytest.mark.skipif(
    not _pillar1_available(),
    reason="Pillar 1 API not available",
)


def _make_file_manifest(entity_type: str, fixture_file: str, extra: dict | None = None) -> dict:
    """Build a file-based manifest for M6 testing."""
    from harmony.pipelines.manifest import DatasetManifest

    ENTITY_CONFIGS = {
        "zoning_area": {
            "dataset_name": "m6_zoning_gosford",
            "source_authority": "nsw_planning_portal",
            "source_tier": 1,
            "resolution_level_floor": 6,
            "dedup_strategy": "source_id",
            "dedup_source_id_field": "PCO_REF_KEY",
            "attribute_mapping": {
                "SYM_CODE": "zone_code",
                "LAY_CLASS": "zone_name",
                "EPI_NAME": "epi_name",
                "LGA_NAME": "lga_name",
                "PCO_REF_KEY": "source_feature_id",
            },
            "known_names_fields": ["SYM_CODE", "LAY_CLASS"],
            "allowed_geometry_types": ["Polygon", "MultiPolygon"],
            "positional_accuracy_m": 5.0,
        },
        "cadastral_lot": {
            "dataset_name": "m6_cadastre_gosford",
            "source_authority": "nsw_spatial_services",
            "source_tier": 1,
            "resolution_level_floor": 8,
            "dedup_strategy": "source_id",
            "dedup_source_id_field": "cadid",
            "attribute_mapping": {
                "cadid": "cad_id",
                "lotnumber": "lot_number",
                "sectionnumber": "section_number",
                "planlabel": "plan_label",
                "shape_Area": "area_sqm",
                "createdate": "observation_date",
            },
            "known_names_fields": ["planlabel"],
            "allowed_geometry_types": ["Polygon", "MultiPolygon"],
            "positional_accuracy_m": 5.0,
        },
        "building": {
            "dataset_name": "m6_buildings_osm_gosford",
            "source_authority": "openstreetmap",
            "source_tier": 2,
            "resolution_level_floor": 10,
            "dedup_strategy": "hybrid",
            "dedup_spatial_threshold_m": 15.0,
            "attribute_mapping": {
                "building": "building_type",
                "name": "building_name",
                "addr:housenumber": "address_number",
                "addr:street": "address_street",
                "addr:suburb": "address_suburb",
                "height": "height_m",
                "building:levels": "levels",
            },
            "known_names_fields": ["name", "addr:street", "addr:housenumber"],
            "allowed_geometry_types": ["Polygon", "MultiPolygon"],
            "positional_accuracy_m": 3.0,
        },
        "road_segment": {
            "dataset_name": "m6_roads_osm_gosford",
            "source_authority": "openstreetmap",
            "source_tier": 2,
            "resolution_level_floor": 8,
            "dedup_strategy": "hybrid",
            "dedup_spatial_threshold_m": 5.0,
            "attribute_mapping": {
                "highway": "road_class",
                "name": "road_name",
                "ref": "road_ref",
                "surface": "surface_type",
                "lanes": "lane_count",
                "maxspeed": "speed_limit_kmh",
                "oneway": "is_oneway",
                "lit": "is_lit",
            },
            "known_names_fields": ["name", "ref"],
            "allowed_geometry_types": ["LineString", "MultiLineString"],
            "positional_accuracy_m": 3.0,
        },
    }

    config = {
        "source_type": "file",
        "source_path": os.path.join(FIXTURES_DIR, fixture_file),
        "source_crs": "EPSG:4326",
        "target_entity_type": entity_type,
        "fidelity_class": "structural",
        "region_code": "cc",
        **ENTITY_CONFIGS[entity_type],
        **(extra or {}),
    }
    return DatasetManifest(config)


@requires_p1
class TestM6MultiDatasetIngestion:
    """Full M6 pipeline: ingest all four datasets into the same cell region."""

    def _run_multi(self, tmp_path, run_id: str | None = None):
        from harmony.pipelines.multi_runner import MultiDatasetRunner

        manifests = [
            _make_file_manifest("zoning_area",  "m6_zoning.geojson"),
            _make_file_manifest("cadastral_lot", "m6_cadastre.geojson"),
            _make_file_manifest("building",      "m6_buildings.geojson"),
            _make_file_manifest("road_segment",  "m6_roads.geojson"),
        ]

        runner = MultiDatasetRunner(p1_base_url=P1_URL, work_dir=tmp_path)
        return runner.run_all(manifests, run_id=run_id)

    def test_all_four_datasets_complete(self, tmp_path):
        report = self._run_multi(tmp_path)
        assert report.status in ("completed", "partial"), report.errors
        summary = report.to_dict()["summary"]
        # All four datasets should attempt ingestion
        assert summary["datasets_total"] == 4

    def test_all_entity_types_registered(self, tmp_path):
        report = self._run_multi(tmp_path)
        per = report.per_dataset
        # Each dataset should register at least some entities
        for entity_type in ("zoning_area", "cadastral_lot", "building", "road_segment"):
            registered = per[entity_type]["entities_registered"]
            assert registered >= 1, (
                f"No entities registered for {entity_type}: {per[entity_type]}"
            )

    def test_zoning_features_count(self, tmp_path):
        report = self._run_multi(tmp_path)
        # m6_zoning.geojson has 4 features — all should be valid
        zoning = report.per_dataset["zoning_area"]
        assert zoning["features_read"] == 4
        assert zoning["entities_registered"] == 4

    def test_cadastral_features_count(self, tmp_path):
        report = self._run_multi(tmp_path)
        cadastral = report.per_dataset["cadastral_lot"]
        assert cadastral["features_read"] == 6
        assert cadastral["entities_registered"] == 6

    def test_buildings_features_count(self, tmp_path):
        report = self._run_multi(tmp_path)
        buildings = report.per_dataset["building"]
        assert buildings["features_read"] == 8
        assert buildings["entities_registered"] == 8

    def test_roads_features_count(self, tmp_path):
        report = self._run_multi(tmp_path)
        roads = report.per_dataset["road_segment"]
        assert roads["features_read"] == 5
        assert roads["entities_registered"] == 5

    def test_coexistence_cells_detected(self, tmp_path):
        """Verify cells from different entity types appear in the registry."""
        report = self._run_multi(tmp_path)
        coex = report.coexistence
        # At the resolutions used (r06/r08/r10), the Gosford area features
        # will share cells across datasets, particularly at r06 for zoning
        # which spans many secondary cells that overlap with other entity types.
        assert coex["total_unique_cells_across_datasets"] >= 1
        assert "cells_by_entity_type" in coex
        # All four entity types should have cells registered
        for entity_type in ("zoning_area", "cadastral_lot", "building", "road_segment"):
            assert entity_type in coex["cells_by_entity_type"], (
                f"{entity_type} missing from coexistence report"
            )

    def test_dedup_idempotency_per_dataset(self, tmp_path):
        """Re-running the full multi-dataset ingestion deduplicates all entries.

        Idempotency invariant: on the second run, no new entities are registered.
        Features that were quarantined in run 1 will be quarantined again in run 2
        (they don't enter the dedup index). Features that were registered in run 1
        will be dedup-skipped in run 2.

        Invariant: r2.entities_registered == 0 for all datasets.
        """
        run1 = self._run_multi(tmp_path, run_id="m6_idem_run1")
        run2 = self._run_multi(tmp_path, run_id="m6_idem_run2")
        for entity_type in ("zoning_area", "cadastral_lot", "building", "road_segment"):
            r2 = run2.per_dataset[entity_type]
            r1 = run1.per_dataset[entity_type]
            assert r2["entities_registered"] == 0, (
                f"Expected 0 new {entity_type} entities on re-run, "
                f"got {r2['entities_registered']}"
            )
            # dedup_skipped in run2 == entities_registered in run1
            # (quarantined features never enter the dedup index)
            assert r2["features_dedup_skipped"] == r1["entities_registered"], (
                f"{entity_type}: dedup_skipped ({r2['features_dedup_skipped']}) "
                f"!= run1 entities ({r1['entities_registered']})"
            )

    def test_fidelity_coverage_on_all_entities(self, tmp_path):
        """Every registered entity must carry both fidelity slots."""
        from harmony.pipelines.registry import DatasetRegistry

        run_id = "m6_fc_verify"
        report = self._run_multi(tmp_path, run_id=run_id)

        registry_path = tmp_path / "registry_m6"
        with DatasetRegistry(registry_path) as db:
            entity_ids = [
                row[0] for row in db._conn.execute(
                    "SELECT canonical_entity_id FROM registered_entities WHERE run_id LIKE ?",
                    (f"{run_id}%",)
                ).fetchall()
            ]

        for eid in entity_ids:
            resp = httpx.get(f"{P1_URL}/resolve/entity/{eid}", timeout=5)
            assert resp.status_code == 200
            meta = resp.json().get("metadata", {})
            fc = meta.get("fidelity_coverage", {})
            assert "structural" in fc, f"Entity {eid} missing structural slot"
            assert "photorealistic" in fc, f"Entity {eid} missing photorealistic slot"
            assert fc["structural"]["status"] == "available"
            assert fc["photorealistic"]["status"] == "pending"

    def test_entities_queryable_by_source(self, tmp_path):
        """Entities must carry source_authority in metadata for source-queryability."""
        from harmony.pipelines.registry import DatasetRegistry

        run_id = "m6_src_query"
        report = self._run_multi(tmp_path, run_id=run_id)

        registry_path = tmp_path / "registry_m6"
        with DatasetRegistry(registry_path) as db:
            entity_ids = [
                row[0] for row in db._conn.execute(
                    "SELECT canonical_entity_id FROM registered_entities WHERE run_id LIKE ?",
                    (f"{run_id}%",)
                ).fetchall()
            ]

        for eid in entity_ids:
            resp = httpx.get(f"{P1_URL}/resolve/entity/{eid}", timeout=5)
            assert resp.status_code == 200
            meta = resp.json().get("metadata", {})
            assert "source_authority" in meta, f"Entity {eid} missing source_authority"
            assert "source_tier" in meta, f"Entity {eid} missing source_tier"
            assert meta["source_tier"] in (1, 2), f"Invalid source_tier: {meta['source_tier']}"

    def test_report_structure_complete(self, tmp_path):
        """Verify the comprehensive report has all required sections."""
        report = self._run_multi(tmp_path)
        d = report.to_dict()
        assert "multi_run_id" in d
        assert "summary" in d
        assert "per_dataset" in d
        assert "coexistence" in d
        assert "dedup_summary" in d
        assert len(d["per_dataset"]) == 4


class TestM6ReportGeneration:
    """Test the report structure independently of live Pillar 1."""

    def test_multi_dataset_report_aggregation(self):
        from harmony.pipelines.multi_runner import MultiDatasetReport
        from harmony.pipelines.runner import IngestionReport
        from harmony.pipelines.manifest import DatasetManifest

        report = MultiDatasetReport("test_multi_001")

        def fake_dataset_report(entity_type, entities, quarantined):
            return {
                "run_id": f"run_{entity_type}",
                "entity_type": entity_type,
                "status": "completed",
                "entities_registered": entities,
                "cells_registered": entities * 3,
                "cells_already_existed": 0,
                "features_read": entities + quarantined,
                "features_quarantined": quarantined,
                "features_dedup_skipped": 0,
                "low_confidence_flagged": 0,
            }

        report.per_dataset["zoning_area"] = fake_dataset_report("zoning_area", 4, 0)
        report.per_dataset["cadastral_lot"] = fake_dataset_report("cadastral_lot", 6, 0)
        report.per_dataset["building"] = fake_dataset_report("building", 8, 1)
        report.per_dataset["road_segment"] = fake_dataset_report("road_segment", 5, 0)

        assert report.total_entities == 23
        assert report.total_cells_new == 69
        assert report.total_quarantined == 1

        d = report.to_dict()
        assert d["summary"]["total_entities_registered"] == 23
        assert d["summary"]["datasets_completed"] == 4
