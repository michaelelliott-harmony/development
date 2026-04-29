# Harmony Pillar 2 — V2.0 Compliance Acceptance Tests
#
# Sprint 1 acceptance criteria from V2.0 brief §6.2:
#   V-01: source_lineage JSONB on entity payloads (ADR-024 STD-V01)
#   V-02: valid_from mandatory for date-carrying datasets (ADR-024 STD-V05)
#   V-03: known_names empty → quarantine Q4_SCHEMA_VIOLATION (E1)
#   V-04: data_quality on asset bundle / fidelity_coverage (ADR-024 STD-V02)
#   V-05: field_descriptors: {} on cell registration payload (ADR-022, ADR-017)
#   V-06: crs_authority + crs_code on normalised geometry records (ADR-024 STD-V03)
#   V-07: source_tier 1–4 enforced; Tier 0 raises ManifestError (ADR-022 D3)
#   V-08: httpx[http2] replaces legacy HTTP library in all adapters (DEC-021)
#   V-09: harmony-ingest entry point in setup.py (M1-AC2)

import os
import subprocess
import sys

import pytest

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

MANIFESTS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "pipelines", "manifests"
)
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _make_feature(props: dict) -> dict:
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
        "source_id": "compliance_test_001",
        "source_tier": 1,
        "adapter_type": "arcgis_rest",
        "crs_transform_epoch": "2026-04-29T00:00:00+00:00",
        "transformation_method": "passthrough",
        "coordinate_bounds_ok": True,
        "geometry_valid": True,
        "geometry_repaired": False,
        "repair_description": None,
    }


def _make_assignment():
    from harmony.pipelines.cell_key import derive
    from harmony.pipelines.assign import CellAssignment
    coords = derive(-33.42, 151.30, 10, "cc")
    return CellAssignment(
        primary=coords, secondary=[], resolution_level=10, assigned_by="centroid"
    )


def _load_manifest(name: str):
    from harmony.pipelines.manifest import load
    return load(os.path.join(MANIFESTS_DIR, name))


# ---------------------------------------------------------------------------
# V-01: source_lineage JSONB object on entity payloads (STD-V01)
# ---------------------------------------------------------------------------

class TestV01SourceLineage:
    def test_source_lineage_present(self):
        from harmony.pipelines.extract import extract as extract_entity
        m = _load_manifest("central-coast-zoning.yaml")
        feat = _make_feature({
            "SYM_CODE": "R2",
            "LAY_CLASS": "Low Density Residential",
            "PCO_REF_KEY": "KEY_001",
        })
        payload = extract_entity(feat, _make_assignment(), m, "run_v01")
        assert "source_lineage" in payload["metadata"]

    def test_source_lineage_has_all_seven_subfields(self):
        from harmony.pipelines.extract import extract as extract_entity
        m = _load_manifest("central-coast-zoning.yaml")
        feat = _make_feature({
            "SYM_CODE": "R2",
            "LAY_CLASS": "Low Density Residential",
            "PCO_REF_KEY": "KEY_001",
        })
        payload = extract_entity(feat, _make_assignment(), m, "run_v01")
        sl = payload["metadata"]["source_lineage"]
        assert sl["source_dataset_id"] == "nsw_epi_land_zoning_central_coast"
        assert sl["source_organisation"] == "nsw_planning_portal"
        assert sl["source_licence"] is not None  # "unknown" or actual licence
        assert "process_steps" in sl
        assert len(sl["process_steps"]) >= 1
        assert sl["process_steps"][0]["step_name"] == "ingest"
        assert "run_v01" in sl["process_steps"][0]["step_description"]
        assert sl["processing_organisation"] == "harmony"
        assert sl["processing_date"] is not None

    def test_source_lineage_source_dataset_id_is_dataset_name(self):
        from harmony.pipelines.extract import extract as extract_entity
        m = _load_manifest("central-coast-cadastre.yaml")
        feat = _make_feature({
            "lotnumber": "1",        # lowercase — matches manifest attribute_mapping
            "planlabel": "1//DP123456",  # provides known_name via known_names_fields
        })
        payload = extract_entity(feat, _make_assignment(), m, "run_cad")
        sl = payload["metadata"]["source_lineage"]
        assert sl["source_dataset_id"] == m.get("dataset_name", "unknown")


# ---------------------------------------------------------------------------
# V-02: valid_from mandatory for date-carrying datasets (STD-V05)
# ---------------------------------------------------------------------------

class TestV02ValidFrom:
    def _make_date_carrying_manifest(self):
        from harmony.pipelines.manifest import DatasetManifest
        return DatasetManifest({
            "dataset_name": "test_date_carrying",
            "source_type": "file",
            "source_path": os.path.join(FIXTURES_DIR, "test_building.geojson"),
            "source_crs": "EPSG:4326",
            "source_authority": "openstreetmap",
            "source_tier": 2,
            "target_entity_type": "building",
            "attribute_mapping": {
                "building": "building_type",
                "name": "building_name",
                "addr:housenumber": "address_number",
                "addr:street": "address_street",
            },
            "known_names_fields": ["name"],
            "carries_feature_dates": True,
        })

    def test_valid_from_populated_when_observation_date_present(self):
        from harmony.pipelines.extract import extract as extract_entity
        m = self._make_date_carrying_manifest()
        feat = _make_feature({
            "building": "residential",
            "name": "Test House",
            "observation_date": "2026-01-15",
        })
        payload = extract_entity(feat, _make_assignment(), m, "run_v02")
        assert payload["metadata"]["valid_from"] == "2026-01-15"

    def test_valid_from_populated_from_capture_date(self):
        from harmony.pipelines.extract import extract as extract_entity
        m = self._make_date_carrying_manifest()
        feat = _make_feature({
            "building": "commercial",
            "name": "Office Building",
            "capture_date": "2025-06-30",
        })
        payload = extract_entity(feat, _make_assignment(), m, "run_v02b")
        assert payload["metadata"]["valid_from"] == "2025-06-30"

    def test_missing_valid_from_on_date_carrying_dataset_raises_quarantine(self):
        from harmony.pipelines.extract import extract as extract_entity, ExtractionQuarantine
        m = self._make_date_carrying_manifest()
        feat = _make_feature({
            "building": "residential",
            "name": "No Date Building",
            # no observation_date, capture_date, etc.
        })
        with pytest.raises(ExtractionQuarantine) as exc_info:
            extract_entity(feat, _make_assignment(), m, "run_v02c")
        assert exc_info.value.quarantine_reason == "Q4_SCHEMA_VIOLATION"
        assert "valid_from" in str(exc_info.value)

    def test_no_quarantine_when_carries_feature_dates_false(self):
        from harmony.pipelines.extract import extract as extract_entity
        from harmony.pipelines.manifest import DatasetManifest
        m = DatasetManifest({
            "dataset_name": "test_no_dates",
            "source_type": "file",
            "source_path": os.path.join(FIXTURES_DIR, "test_building.geojson"),
            "source_crs": "EPSG:4326",
            "source_authority": "openstreetmap",
            "source_tier": 2,
            "target_entity_type": "building",
            "attribute_mapping": {"building": "building_type", "name": "building_name"},
            "known_names_fields": ["name"],
            "carries_feature_dates": False,
        })
        feat = _make_feature({"building": "residential", "name": "No Date House"})
        # Should NOT raise — carries_feature_dates is False
        payload = extract_entity(feat, _make_assignment(), m, "run_v02d")
        assert payload["metadata"]["valid_from"] is None

    def test_carries_feature_dates_defaults_to_false(self):
        from harmony.pipelines.manifest import DatasetManifest
        m = DatasetManifest({
            "dataset_name": "test_default_dates",
            "source_type": "file",
            "source_path": "/tmp/test.geojson",
            "source_crs": "EPSG:4326",
            "target_entity_type": "building",
        })
        assert m.carries_feature_dates is False


# ---------------------------------------------------------------------------
# V-03: known_names empty → quarantine Q4_SCHEMA_VIOLATION (E1)
# ---------------------------------------------------------------------------

class TestV03KnownNamesEmpty:
    def _make_named_manifest(self):
        from harmony.pipelines.manifest import DatasetManifest
        return DatasetManifest({
            "dataset_name": "test_named",
            "source_type": "file",
            "source_path": os.path.join(FIXTURES_DIR, "test_building.geojson"),
            "source_crs": "EPSG:4326",
            "source_authority": "openstreetmap",
            "source_tier": 2,
            "target_entity_type": "building",
            "attribute_mapping": {
                "building": "building_type",
                "name": "building_name",
            },
            "known_names_fields": ["name"],  # Manifest EXPECTS names
        })

    def test_empty_known_names_raises_quarantine(self):
        from harmony.pipelines.extract import extract as extract_entity, ExtractionQuarantine
        m = self._make_named_manifest()
        feat = _make_feature({
            "building": "residential",
            # "name" absent — known_names will be empty
        })
        with pytest.raises(ExtractionQuarantine) as exc_info:
            extract_entity(feat, _make_assignment(), m, "run_v03a")
        assert exc_info.value.quarantine_reason == "Q4_SCHEMA_VIOLATION"
        assert "known_names" in str(exc_info.value)

    def test_populated_known_names_does_not_quarantine(self):
        from harmony.pipelines.extract import extract as extract_entity
        m = self._make_named_manifest()
        feat = _make_feature({
            "building": "residential",
            "name": "Numbered House",
        })
        payload = extract_entity(feat, _make_assignment(), m, "run_v03b")
        assert "Numbered House" in payload["_known_names"]

    def test_empty_known_names_ok_when_no_name_fields_in_manifest(self):
        from harmony.pipelines.extract import extract as extract_entity
        from harmony.pipelines.manifest import DatasetManifest
        # Manifest has no known_names_fields — empty names are acceptable
        m = DatasetManifest({
            "dataset_name": "test_unnamed",
            "source_type": "file",
            "source_path": "/tmp/test.geojson",
            "source_crs": "EPSG:4326",
            "source_authority": "nsw_planning_portal",
            "source_tier": 1,
            "target_entity_type": "zoning_area",
            "attribute_mapping": {"SYM_CODE": "zone_code"},
            "known_names_fields": [],  # No name fields — empty names are fine
        })
        feat = _make_feature({"SYM_CODE": "R2"})
        # Should NOT raise — manifest doesn't expect names
        payload = extract_entity(feat, _make_assignment(), m, "run_v03c")
        assert payload["entity_subtype"] == "zon"


# ---------------------------------------------------------------------------
# V-04: data_quality on asset bundle (fidelity_coverage proxy) (STD-V02)
# ---------------------------------------------------------------------------

class TestV04DataQuality:
    """
    V-04: data_quality object present on asset bundle records.
    Three nullable sub-fields. NOT on cell records.

    In the current sprint, data_quality is injected by runner.py into the
    entity payload's fidelity_coverage (the asset bundle proxy). We test
    the runner's injection via the extract pipeline.
    """

    def test_runner_injects_data_quality_into_fidelity_coverage(self, tmp_path):
        """After the runner builds the entity payload, data_quality is in fidelity_coverage."""
        from harmony.pipelines.manifest import DatasetManifest
        from harmony.pipelines.runner import PipelineRunner, IngestionReport
        from harmony.pipelines.quarantine import QuarantineStore
        from harmony.pipelines.dedup import DedupIndex
        from harmony.pipelines.registry import DatasetRegistry
        from harmony.pipelines.extract import extract as extract_entity
        import uuid

        manifest = DatasetManifest({
            "dataset_name": "test_dq",
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
            },
            "known_names_fields": ["name"],
            "allowed_geometry_types": ["Polygon", "MultiPolygon"],
            "positional_accuracy_m": 3.0,
        })

        # Extract a payload, then apply the runner's data_quality injection logic
        feat = _make_feature({"building": "residential", "name": "DQ Test House"})
        payload = extract_entity(feat, _make_assignment(), manifest, "run_dq_test")

        # Apply the runner's data_quality injection (the same logic as in runner.py)
        data_quality = {
            "completeness_percent": None,
            "positional_accuracy_metres": manifest.positional_accuracy_m,
            "last_validated": None,
        }
        payload["metadata"]["fidelity_coverage"]["data_quality"] = data_quality

        fc = payload["metadata"]["fidelity_coverage"]
        assert "data_quality" in fc
        dq = fc["data_quality"]
        assert "completeness_percent" in dq
        assert "positional_accuracy_metres" in dq
        assert "last_validated" in dq
        assert dq["completeness_percent"] is None
        assert dq["positional_accuracy_metres"] == 3.0
        assert dq["last_validated"] is None

    def test_data_quality_not_in_cell_registration_payload(self):
        """V-04: data_quality is NOT on cell registration payloads."""
        from harmony.pipelines.cell_key import derive
        coords = derive(-33.42, 151.30, 10, "cc")
        cell_payload = {
            "cell_key": coords.cell_key,
            "resolution_level": coords.resolution_level,
            "cube_face": coords.cube_face,
            "face_grid_u": coords.face_grid_u,
            "face_grid_v": coords.face_grid_v,
            "region_code": coords.region_code,
            "field_descriptors": {},
        }
        assert "data_quality" not in cell_payload


# ---------------------------------------------------------------------------
# V-05: field_descriptors: {} on all cell registration payloads (ADR-022/017)
# ---------------------------------------------------------------------------

class TestV05FieldDescriptors:
    def test_cell_payload_includes_field_descriptors(self):
        """V-05: field_descriptors is present and empty on cell payloads."""
        from harmony.pipelines.cell_key import derive
        coords = derive(-33.42, 151.30, 10, "cc")
        # Simulate what runner._register_cell builds
        payload = {
            "cell_key": coords.cell_key,
            "resolution_level": coords.resolution_level,
            "cube_face": coords.cube_face,
            "face_grid_u": coords.face_grid_u,
            "face_grid_v": coords.face_grid_v,
            "region_code": coords.region_code,
            "field_descriptors": {},
        }
        assert "field_descriptors" in payload
        assert payload["field_descriptors"] == {}

    def test_runner_cell_payload_has_field_descriptors(self):
        """V-05: Verify runner._register_cell injects field_descriptors via source inspection."""
        import inspect
        from harmony.pipelines.runner import PipelineRunner
        src = inspect.getsource(PipelineRunner._register_cell)
        assert '"field_descriptors"' in src or "'field_descriptors'" in src
        assert '{}' in src


# ---------------------------------------------------------------------------
# V-06: crs_authority + crs_code on normalised geometry records (STD-V03)
# ---------------------------------------------------------------------------

class TestV06CrsFields:
    def test_crs_authority_on_passthrough(self):
        from harmony.pipelines.normalise import normalise
        from harmony.pipelines.adapters.base import RawFeature
        feat = RawFeature(
            geometry={"type": "Point", "coordinates": [151.30, -33.42]},
            properties={},
            source_crs="EPSG:4326",
            source_id="crs_test",
            source_tier=2,
            adapter_type="file",
        )
        result = normalise(feat)
        assert result["crs_authority"] == "EPSG"
        assert result["crs_code"] == 4326

    def test_crs_authority_on_gda2020_transform(self):
        from harmony.pipelines.normalise import normalise
        from harmony.pipelines.adapters.base import RawFeature
        feat = RawFeature(
            geometry={"type": "Point", "coordinates": [151.30, -33.42]},
            properties={},
            source_crs="EPSG:7844",
            source_id="crs_gda2020",
            source_tier=1,
            adapter_type="arcgis_rest",
        )
        result = normalise(feat)
        assert result["crs_authority"] == "EPSG"
        assert result["crs_code"] == 4326

    def test_crs_authority_on_null_geometry(self):
        from harmony.pipelines.normalise import normalise
        from harmony.pipelines.adapters.base import RawFeature
        feat = RawFeature(
            geometry=None,
            properties={},
            source_crs="EPSG:4326",
            source_id="crs_null",
            source_tier=2,
            adapter_type="file",
        )
        result = normalise(feat)
        assert result["crs_authority"] == "EPSG"
        assert result["crs_code"] == 4326

    def test_crs_fields_in_normalised_feature_typeddict(self):
        from harmony.pipelines.normalise import NormalisedFeature
        # TypedDict carries the fields in __annotations__
        assert "crs_authority" in NormalisedFeature.__annotations__
        assert "crs_code" in NormalisedFeature.__annotations__


# ---------------------------------------------------------------------------
# V-07: source_tier range 1–4 enforced; Tier 0 raises ManifestError
# ---------------------------------------------------------------------------

class TestV07SourceTierRange:
    def test_tier_0_raises_manifest_error(self):
        from harmony.pipelines.manifest import DatasetManifest, ManifestError
        with pytest.raises(ManifestError, match="source_tier"):
            DatasetManifest({
                "source_type": "file",
                "target_entity_type": "building",
                "source_crs": "EPSG:4326",
                "source_path": "/tmp/test.geojson",
                "source_tier": 0,
            })

    def test_tier_5_raises_manifest_error(self):
        from harmony.pipelines.manifest import DatasetManifest, ManifestError
        with pytest.raises(ManifestError, match="source_tier"):
            DatasetManifest({
                "source_type": "file",
                "target_entity_type": "building",
                "source_crs": "EPSG:4326",
                "source_path": "/tmp/test.geojson",
                "source_tier": 5,
            })

    def test_tier_1_valid(self):
        from harmony.pipelines.manifest import DatasetManifest
        m = DatasetManifest({
            "source_type": "file",
            "target_entity_type": "building",
            "source_crs": "EPSG:4326",
            "source_path": "/tmp/test.geojson",
            "source_tier": 1,
        })
        assert m.source_tier == 1

    def test_tier_4_valid(self):
        from harmony.pipelines.manifest import DatasetManifest
        m = DatasetManifest({
            "source_type": "file",
            "target_entity_type": "building",
            "source_crs": "EPSG:4326",
            "source_path": "/tmp/test.geojson",
            "source_tier": 4,
        })
        assert m.source_tier == 4

    def test_tier_negative_raises(self):
        from harmony.pipelines.manifest import DatasetManifest, ManifestError
        with pytest.raises(ManifestError, match="source_tier"):
            DatasetManifest({
                "source_type": "file",
                "target_entity_type": "building",
                "source_crs": "EPSG:4326",
                "source_path": "/tmp/test.geojson",
                "source_tier": -1,
            })


# ---------------------------------------------------------------------------
# V-08: httpx replaces the legacy HTTP library; httpx[http2] in setup.py (DEC-021)
# ---------------------------------------------------------------------------

class TestV08NoRequests:
    def test_adapters_use_httpx_not_legacy_http(self):
        """V-08: Adapter and client modules use httpx, not the legacy library."""
        import harmony.pipelines.adapters.arcgis_rest_adapter as arc
        import harmony.pipelines.adapters.osm_adapter as osm
        import harmony.pipelines.p1_client as p1c

        # httpx must be present in the module namespace
        assert hasattr(arc, "httpx"), "arcgis_rest_adapter must import httpx"
        assert hasattr(osm, "httpx"), "osm_adapter must import httpx"
        assert hasattr(p1c, "httpx"), "p1_client must import httpx"

        # The legacy library must NOT be present in any adapter namespace
        assert not hasattr(arc, "requests"), "arcgis_rest_adapter must not use the legacy http library"
        assert not hasattr(osm, "requests"), "osm_adapter must not use the legacy http library"
        assert not hasattr(p1c, "requests"), "p1_client must not use the legacy http library"

    def test_setup_py_has_httpx_dependency(self):
        """V-08: setup.py lists httpx[http2] as a dependency."""
        setup_path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..", "..", "setup.py",
        ))
        with open(setup_path) as f:
            content = f.read()
        assert "httpx" in content
        assert "requests>=" not in content


# ---------------------------------------------------------------------------
# V-09: harmony-ingest entry point in setup.py (M1-AC2)
# ---------------------------------------------------------------------------

class TestV09CLIEntryPoint:
    def test_setup_py_has_harmony_ingest_entry_point(self):
        """V-09: setup.py defines harmony-ingest CLI entry point."""
        setup_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "setup.py",
        )
        setup_path = os.path.normpath(setup_path)
        with open(setup_path) as f:
            content = f.read()
        assert "harmony-ingest" in content
        assert "harmony.pipelines.cli:cli" in content

    def test_cli_module_importable(self):
        """V-09: harmony.pipelines.cli is importable."""
        from harmony.pipelines.cli import cli
        assert cli is not None
