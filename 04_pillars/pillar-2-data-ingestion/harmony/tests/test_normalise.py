# Harmony Pillar 2 — CRS Normalisation Tests
#
# DEC-014 requirements:
# - WGS84 passes through unchanged (transformation_method = "passthrough")
# - GDA2020 / GDA94 transform to WGS84
# - Missing source_crs raises NormalisationError (no defaults, no auto-detect)
# - Post-transform coordinates validated within WGS84 bounds
# - transformation_method logged on every record

import pytest
from harmony.pipelines.normalise import (
    NormalisationError,
    normalise,
    normalise_batch,
    _TARGET_CRS,
)
from harmony.pipelines.adapters.base import RawFeature


_DEFAULT_GEOM = {
    "type": "Polygon",
    "coordinates": [[
        [151.30, -33.42],
        [151.31, -33.42],
        [151.31, -33.43],
        [151.30, -33.43],
        [151.30, -33.42],
    ]]
}


def _make_feature(crs: str, geom: dict | None = _DEFAULT_GEOM) -> RawFeature:
    return RawFeature(
        geometry=geom,
        properties={"test": "yes"},
        source_crs=crs,
        source_id="test_001",
        source_tier=2,
        adapter_type="file",
    )


class TestPassthrough:
    def test_wgs84_passthrough(self):
        feat = _make_feature("EPSG:4326")
        result = normalise(feat)
        assert result["transformation_method"] == "passthrough"
        assert result["geometry_wgs84"] == feat["geometry"]
        assert result["coordinate_bounds_ok"] is True

    def test_passthrough_does_not_modify_coordinates(self):
        geom = {
            "type": "Point",
            "coordinates": [151.5, -33.4],
        }
        feat = _make_feature("EPSG:4326", geom)
        result = normalise(feat)
        assert result["geometry_wgs84"]["coordinates"] == [151.5, -33.4]

    def test_crs_transform_epoch_set(self):
        feat = _make_feature("EPSG:4326")
        result = normalise(feat)
        assert "crs_transform_epoch" in result
        assert result["crs_transform_epoch"]  # non-empty


class TestMissingCRS:
    def test_missing_crs_raises(self):
        feat = {
            "geometry": {"type": "Point", "coordinates": [151.5, -33.4]},
            "properties": {},
            "source_id": "no_crs_001",
            "source_tier": 2,
            "adapter_type": "file",
        }
        with pytest.raises(NormalisationError, match="source_crs"):
            normalise(feat)

    def test_empty_crs_raises(self):
        feat = _make_feature("EPSG:4326")
        feat["source_crs"] = ""
        with pytest.raises(NormalisationError):
            normalise(feat)


class TestGDA2020Transform:
    def test_gda2020_transforms_to_wgs84(self):
        # GDA2020 (EPSG:7844) coordinates for Central Coast
        # At this scale, GDA2020 ≈ WGS84, so the output should be very close
        feat = _make_feature("EPSG:7844")
        result = normalise(feat)
        # Should have a transformation_method set (ntv2 or helmert_fallback)
        assert result["transformation_method"] in ("ntv2", "helmert_fallback", "proj_default")
        assert result["coordinate_bounds_ok"] is True
        # Coordinates should be in valid WGS84 range
        wgs84_geom = result["geometry_wgs84"]
        assert wgs84_geom is not None
        for ring in wgs84_geom["coordinates"]:
            for lon, lat in ring:
                assert -180 <= lon <= 180
                assert -90 <= lat <= 90

    def test_gda2020_coordinates_close_to_input(self):
        # GDA2020 is within ~0.2m of WGS84 in Australia
        # So output lon/lat should be very close to input
        feat = _make_feature("EPSG:7844")
        result = normalise(feat)
        in_lon = feat["geometry"]["coordinates"][0][0][0]
        out_lon = result["geometry_wgs84"]["coordinates"][0][0][0]
        # Within 0.01 degrees (~1km) — generous tolerance for Helmert fallback
        assert abs(out_lon - in_lon) < 0.01


class TestGDA94Transform:
    def test_gda94_transforms_to_wgs84(self):
        feat = _make_feature("EPSG:4283")
        result = normalise(feat)
        assert result["transformation_method"] in ("ntv2", "helmert_fallback", "proj_default")
        assert result["coordinate_bounds_ok"] is True

    def test_gda94_coordinates_in_bounds(self):
        feat = _make_feature("EPSG:4283")
        result = normalise(feat)
        wgs84_geom = result["geometry_wgs84"]
        for ring in wgs84_geom["coordinates"]:
            for lon, lat in ring:
                assert -180 <= lon <= 180
                assert -90 <= lat <= 90


class TestWebMercatorTransform:
    def test_web_mercator_transforms_to_wgs84(self):
        # Web Mercator point for Sydney area (approx)
        feat = _make_feature("EPSG:3857", geom={
            "type": "Point",
            "coordinates": [16828100.0, -3961100.0],  # approx Sydney in Web Mercator
        })
        result = normalise(feat)
        assert result["transformation_method"] in ("proj_default",)
        wgs84 = result["geometry_wgs84"]
        # Sydney should be around lon=151, lat=-33
        lon, lat = wgs84["coordinates"]
        assert 150 < lon < 153
        assert -35 < lat < -31


class TestNullGeometry:
    def test_null_geometry_passes_through(self):
        feat = _make_feature("EPSG:4326", geom=None)  # None is now correctly passed
        result = normalise(feat)
        assert result["geometry_wgs84"] is None
        assert result["coordinate_bounds_ok"] is True


class TestOutOfBoundsCoordinates:
    def test_out_of_bounds_coordinates_flagged(self):
        # Simulate a post-transform result with impossible coordinates
        feat = _make_feature("EPSG:4326", geom={
            "type": "Point",
            "coordinates": [999.0, -33.4],  # impossible longitude
        })
        result = normalise(feat)
        # Passthrough won't validate — coordinate_bounds_ok should be False
        assert result["coordinate_bounds_ok"] is False


class TestBatchNormalisation:
    def test_batch_collects_errors_separately(self):
        features = [
            _make_feature("EPSG:4326"),
            {"geometry": {"type": "Point", "coordinates": [151.5, -33.4]},
             "properties": {}, "source_id": "bad", "source_tier": 2, "adapter_type": "file"},
            _make_feature("EPSG:4326"),
        ]
        normalised, errors = normalise_batch(features)
        assert len(normalised) == 2
        assert len(errors) == 1
        assert errors[0]["quarantine_reason"] == "Q3_CRS_OUT_OF_BOUNDS"

    def test_batch_all_valid(self):
        features = [_make_feature("EPSG:4326") for _ in range(3)]
        normalised, errors = normalise_batch(features)
        assert len(normalised) == 3
        assert len(errors) == 0
