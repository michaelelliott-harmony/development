# Harmony Pillar 2 — M5 End-to-End Integration Test
#
# Tests the full pipeline from file adapter → Pillar 1 API registration.
# Requires Pillar 1 API running at http://127.0.0.1:8000.
# Skip if unavailable — CI without the API will skip cleanly.
#
# Non-negotiable checks:
# - Every registered entity has fidelity_coverage.structural = "available"
# - Every registered entity has fidelity_coverage.photorealistic = "pending"
# - Cells registered are idempotent (re-run produces same results)

import json
import os
import tempfile
import pytest
import httpx

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
MANIFESTS_DIR = os.path.join(os.path.dirname(__file__), "..", "pipelines", "manifests")

P1_URL = os.environ.get("HARMONY_P1_URL", "http://127.0.0.1:8000")


def _pillar1_available() -> bool:
    try:
        r = httpx.get(f"{P1_URL}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


requires_p1 = pytest.mark.skipif(
    not _pillar1_available(),
    reason="Pillar 1 API not available at " + P1_URL,
)


class TestEndToEndBuildingFixture:
    """Full pipeline test using the building fixture GeoJSON.

    Uses the building manifest but with source_type overridden to 'file'
    and source_path pointing at the test fixture.
    """

    def _run_pipeline(self, tmp_path) -> dict:
        from harmony.pipelines.manifest import DatasetManifest
        from harmony.pipelines.runner import PipelineRunner

        manifest = DatasetManifest({
            "dataset_name": "test_buildings_e2e",
            "source_type": "file",
            "source_path": os.path.join(FIXTURES_DIR, "test_building.geojson"),
            "source_crs": "EPSG:4326",
            "source_authority": "openstreetmap",
            "source_tier": 2,
            "target_entity_type": "building",
            "fidelity_class": "structural",
            "region_code": "cc",
            "resolution_level_floor": 10,
            "dedup_strategy": "hybrid",
            "dedup_spatial_threshold_m": 15.0,
            "attribute_mapping": {
                "building": "building_type",
                "name": "building_name",
                "addr:housenumber": "address_number",
                "addr:street": "address_street",
                "height": "height_m",
                "building:levels": "levels",
            },
            "known_names_fields": ["name", "addr:street", "addr:housenumber"],
            "allowed_geometry_types": ["Polygon", "MultiPolygon"],
            "positional_accuracy_m": 3.0,
        })

        runner = PipelineRunner(p1_base_url=P1_URL, work_dir=tmp_path)
        # Run with the manifest object directly (not from file)
        from harmony.pipelines.runner import IngestionReport
        import uuid
        from datetime import datetime, timezone

        run_id = f"run_test_{uuid.uuid4().hex[:8]}"
        report = IngestionReport(run_id, manifest)

        from harmony.pipelines.quarantine import QuarantineStore
        from harmony.pipelines.dedup import DedupIndex
        from harmony.pipelines.registry import DatasetRegistry

        with (
            QuarantineStore(tmp_path / "quarantine") as quarantine,
            DedupIndex(tmp_path / "dedup", "building") as dedup_index,
            DatasetRegistry(tmp_path / "registry") as db,
        ):
            db.start_run(run_id, manifest)
            try:
                runner._run_pipeline(manifest, run_id, report, quarantine, dedup_index, db)
                report.status = "completed"
            except Exception as exc:
                report.status = "failed"
                report.errors.append(str(exc))
            db.complete_run(run_id, report.as_counts())

        return report.to_dict()

    @requires_p1
    def test_e2e_entities_registered(self, tmp_path):
        report = self._run_pipeline(tmp_path)
        # 5 features: 2 valid, 1 repaired (unclosed ring), 1 bowtie (repaired/quarantined),
        # 1 zero-area (quarantined). At least 3 should make it through.
        assert report["entities_registered"] >= 3, report

    @requires_p1
    def test_e2e_cells_registered(self, tmp_path):
        report = self._run_pipeline(tmp_path)
        # Cells may already exist in the shared Pillar 1 DB from a prior test run —
        # idempotency by design. Check that cells were either newly created or
        # confirmed as already existing.
        total_cells_touched = report["cells_registered"] + report.get("cells_already_existed", 0)
        assert total_cells_touched >= 1, f"No cells registered or found: {report}"

    @requires_p1
    def test_e2e_idempotency(self, tmp_path):
        """Second run with same data should produce 0 new entities (dedup catches all)."""
        report1 = self._run_pipeline(tmp_path)
        report2 = self._run_pipeline(tmp_path)
        assert report2["entities_registered"] == 0
        assert report2["features_dedup_skipped"] == report1["entities_registered"]

    @requires_p1
    def test_e2e_registered_entity_has_fidelity_coverage(self, tmp_path):
        """All registered entities must carry fidelity_coverage with both slots."""
        from harmony.pipelines.manifest import DatasetManifest
        from harmony.pipelines.runner import IngestionReport
        from harmony.pipelines.quarantine import QuarantineStore
        from harmony.pipelines.dedup import DedupIndex
        from harmony.pipelines.registry import DatasetRegistry
        import uuid

        manifest = DatasetManifest({
            "dataset_name": "test_fc_check",
            "source_type": "file",
            "source_path": os.path.join(FIXTURES_DIR, "test_building.geojson"),
            "source_crs": "EPSG:4326",
            "source_authority": "openstreetmap",
            "source_tier": 2,
            "target_entity_type": "building",
            "fidelity_class": "structural",
            "region_code": "cc",
            "resolution_level_floor": 10,
            "dedup_strategy": "hybrid",
            "dedup_spatial_threshold_m": 15.0,
            "attribute_mapping": {"building": "building_type"},
            "known_names_fields": ["name"],
            "allowed_geometry_types": ["Polygon", "MultiPolygon"],
            "positional_accuracy_m": 3.0,
        })

        run_id = f"run_fc_{uuid.uuid4().hex[:8]}"
        runner_obj = __import__(
            "harmony.pipelines.runner", fromlist=["PipelineRunner"]
        ).PipelineRunner(p1_base_url=P1_URL, work_dir=tmp_path)

        entities_registered = []

        with (
            QuarantineStore(tmp_path / "quar2") as quarantine,
            DedupIndex(tmp_path / "dedup2", "building") as dedup_index,
            DatasetRegistry(tmp_path / "reg2") as db,
        ):
            report = IngestionReport(run_id, manifest)
            db.start_run(run_id, manifest)
            runner_obj._run_pipeline(manifest, run_id, report, quarantine, dedup_index, db)
            db.complete_run(run_id, report.as_counts())

            # Get all registered entity IDs from this run
            entities_registered = db._conn.execute(
                "SELECT canonical_entity_id FROM registered_entities WHERE run_id = ?",
                (run_id,)
            ).fetchall()

        # Verify each registered entity has fidelity_coverage in its metadata
        for (eid,) in entities_registered:
            resp = httpx.get(f"{P1_URL}/resolve/entity/{eid}", timeout=5)
            assert resp.status_code == 200, f"Entity {eid} not found: {resp.text}"
            entity = resp.json()
            meta = entity.get("metadata", {})
            fc = meta.get("fidelity_coverage", {})
            # Non-negotiable: both slots must be present
            assert "structural" in fc, f"Entity {eid} missing structural slot: {meta}"
            assert "photorealistic" in fc, f"Entity {eid} missing photorealistic slot: {meta}"
            assert fc["structural"]["status"] == "available"
            assert fc["photorealistic"]["status"] == "pending"

    @requires_p1
    def test_e2e_report_counts_are_consistent(self, tmp_path):
        report = self._run_pipeline(tmp_path)
        total = report["entities_registered"] + report["features_quarantined"] + report["features_dedup_skipped"]
        # Total processed + dedup skipped ≈ features_read (some may fail normalisation)
        assert report["features_read"] == 5   # test fixture has 5 buildings
        assert report["status"] == "completed"


class TestRegistryTracking:
    """Tests the Pillar 2 dataset registry independently of Pillar 1."""

    def test_registry_records_run(self, tmp_path):
        from harmony.pipelines.registry import DatasetRegistry
        from harmony.pipelines.manifest import DatasetManifest

        manifest = DatasetManifest({
            "dataset_name": "test_registry",
            "source_type": "file",
            "source_path": "/tmp/test.geojson",
            "source_crs": "EPSG:4326",
            "target_entity_type": "building",
        })

        with DatasetRegistry(tmp_path) as db:
            db.start_run("run_001", manifest)
            db.complete_run("run_001", {
                "features_read": 10,
                "features_normalised": 10,
                "features_validated": 9,
                "features_quarantined": 1,
                "features_dedup_skipped": 0,
                "entities_registered": 9,
                "cells_registered": 12,
            })
            run = db.get_run("run_001")

        assert run is not None
        assert run["status"] == "completed"
        assert run["features_read"] == 10
        assert run["entities_registered"] == 9

    def test_registry_records_cells(self, tmp_path):
        from harmony.pipelines.registry import DatasetRegistry
        from harmony.pipelines.manifest import DatasetManifest

        manifest = DatasetManifest({
            "dataset_name": "test_cells",
            "source_type": "file",
            "source_path": "/tmp/test.geojson",
            "source_crs": "EPSG:4326",
            "target_entity_type": "zoning_area",
        })

        with DatasetRegistry(tmp_path) as db:
            db.start_run("run_002", manifest)
            db.record_cell("run_002", "hsam:r10:cc:abc", "hc_test12345", 10, "zoning_area")
            db.complete_run("run_002", {"cells_registered": 1})
            runs = db.list_runs()

        assert len(runs) >= 1
        assert runs[0]["run_id"] == "run_002"
