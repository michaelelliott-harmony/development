# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Pillar 1 Stage 2 — Volumetric Cell Acceptance Suite
#
# Covers the acceptance criteria from the Stage 2 session brief §Acceptance
# Criteria AC1–AC10. Split into three blocks:
#
#   A. Pure-logic tests of the volumetric module (no DB, no server).
#      These run anywhere and validate key derivation, parsing, and
#      validation rules. They close AC3–AC6 and the determinism half of AC5.
#
#   B. HTTP integration tests against a live API server. These require
#      HARMONY_API_URL pointing to a server with migration 003 applied.
#      They close AC1, AC2, AC7, AC8, AC9, and AC10 in their runtime form.
#      Skipped automatically if the server is unreachable.
#
#   C. Forward-compatibility confirmation (AC10). Pure assertion over the
#      schema constants — no infra required.
#
# Usage:
#   # Pure-logic block only:
#   pytest harmony/tests/test_p1_stage2_acceptance.py -v -m "not http"
#
#   # Full suite (requires migration 003 applied and server running):
#   pytest harmony/tests/test_p1_stage2_acceptance.py -v

from __future__ import annotations

import os
import re
import sys
import uuid

import pytest

# --------------------------------------------------------------------------
# Make the volumetric module importable without a full package install
# --------------------------------------------------------------------------

_HERE = os.path.abspath(os.path.dirname(__file__))
_PILLAR_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_CELL_KEY_SRC = os.path.join(_PILLAR_ROOT, "packages", "cell-key", "src")
if _CELL_KEY_SRC not in sys.path:
    sys.path.insert(0, _CELL_KEY_SRC)

import volumetric  # noqa: E402


# --------------------------------------------------------------------------
# Fixtures — reference surface keys from the Stage 1 sample dataset
# --------------------------------------------------------------------------

GOSFORD_WATERFRONT_SURFACE = "hsam:r08:cc:g2f39nh7keq4h9f0"
GOSFORD_CBD_L6_SURFACE = "hsam:r06:cc:za6bzq7gfknrzd5z"


# ==========================================================================
# A. PURE-LOGIC TESTS — volumetric module
# ==========================================================================


class TestVolumetricKeyDerivation:
    """AC3, AC4, AC5 (determinism), AC6 — key derivation and validation."""

    def test_ac4_volumetric_key_format_ground_floor(self):
        key = volumetric.derive_volumetric_cell_key(
            GOSFORD_WATERFRONT_SURFACE, 0.0, 3.5
        )
        assert key == "hsam:r08:cc:g2f39nh7keq4h9f0:v0.0-3.5"

    def test_ac4_volumetric_key_format_first_floor(self):
        key = volumetric.derive_volumetric_cell_key(
            GOSFORD_WATERFRONT_SURFACE, 3.5, 7.0
        )
        assert key == "hsam:r08:cc:g2f39nh7keq4h9f0:v3.5-7.0"

    def test_ac4_volumetric_key_format_underwater(self):
        key = volumetric.derive_volumetric_cell_key(
            GOSFORD_WATERFRONT_SURFACE, -45.0, 0.0
        )
        assert key == "hsam:r08:cc:g2f39nh7keq4h9f0:v-45.0-0.0"

    def test_ac4_volumetric_key_format_uav_corridor(self):
        key = volumetric.derive_volumetric_cell_key(
            GOSFORD_WATERFRONT_SURFACE, 30.0, 100.0
        )
        assert key == "hsam:r08:cc:g2f39nh7keq4h9f0:v30.0-100.0"

    def test_ac5_determinism_three_times(self):
        """Same inputs × 3 must produce identical output."""
        k1 = volumetric.derive_volumetric_cell_key(
            GOSFORD_WATERFRONT_SURFACE, 3.5, 7.0
        )
        k2 = volumetric.derive_volumetric_cell_key(
            GOSFORD_WATERFRONT_SURFACE, 3.5, 7.0
        )
        k3 = volumetric.derive_volumetric_cell_key(
            GOSFORD_WATERFRONT_SURFACE, 3.5, 7.0
        )
        assert k1 == k2 == k3

    def test_ac5_determinism_negative_altitude_three_times(self):
        k1 = volumetric.derive_volumetric_cell_key(
            GOSFORD_CBD_L6_SURFACE, -45.0, 0.0
        )
        k2 = volumetric.derive_volumetric_cell_key(
            GOSFORD_CBD_L6_SURFACE, -45.0, 0.0
        )
        k3 = volumetric.derive_volumetric_cell_key(
            GOSFORD_CBD_L6_SURFACE, -45.0, 0.0
        )
        assert k1 == k2 == k3

    def test_ac5_determinism_aviation_corridor_three_times(self):
        k1 = volumetric.derive_volumetric_cell_key(
            GOSFORD_CBD_L6_SURFACE, 30.0, 100.0
        )
        k2 = volumetric.derive_volumetric_cell_key(
            GOSFORD_CBD_L6_SURFACE, 30.0, 100.0
        )
        k3 = volumetric.derive_volumetric_cell_key(
            GOSFORD_CBD_L6_SURFACE, 30.0, 100.0
        )
        assert k1 == k2 == k3

    def test_ac4_pattern_regex(self):
        """The volumetric regex must match generated keys and reject surface keys."""
        key = volumetric.derive_volumetric_cell_key(
            GOSFORD_WATERFRONT_SURFACE, 0.0, 3.5
        )
        assert re.match(volumetric.VOLUMETRIC_CELL_KEY_PATTERN, key)
        assert not re.match(
            volumetric.VOLUMETRIC_CELL_KEY_PATTERN, GOSFORD_WATERFRONT_SURFACE
        )
        assert re.match(volumetric.SURFACE_CELL_KEY_PATTERN, GOSFORD_WATERFRONT_SURFACE)
        assert not re.match(volumetric.SURFACE_CELL_KEY_PATTERN, key)


class TestVolumetricKeyParsing:

    def test_parse_round_trip_positive(self):
        key = "hsam:r08:cc:g2f39nh7keq4h9f0:v3.5-7.0"
        parsed = volumetric.parse_volumetric_cell_key(key)
        assert parsed["surface_cell_key"] == "hsam:r08:cc:g2f39nh7keq4h9f0"
        assert parsed["altitude_min_m"] == 3.5
        assert parsed["altitude_max_m"] == 7.0
        assert parsed["region_code"] == "cc"
        assert parsed["resolution"] == 8
        assert parsed["hash_fragment"] == "g2f39nh7keq4h9f0"

    def test_parse_round_trip_negative(self):
        key = "hsam:r08:cc:g2f39nh7keq4h9f0:v-45.0-0.0"
        parsed = volumetric.parse_volumetric_cell_key(key)
        assert parsed["altitude_min_m"] == -45.0
        assert parsed["altitude_max_m"] == 0.0

    def test_parse_round_trip_aviation(self):
        key = "hsam:r08:cc:g2f39nh7keq4h9f0:v30.0-100.0"
        parsed = volumetric.parse_volumetric_cell_key(key)
        assert parsed["altitude_min_m"] == 30.0
        assert parsed["altitude_max_m"] == 100.0

    def test_parse_rejects_surface_key(self):
        with pytest.raises(ValueError, match="not a valid volumetric key"):
            volumetric.parse_volumetric_cell_key(GOSFORD_WATERFRONT_SURFACE)

    def test_parse_rejects_reserved_temporal_separator(self):
        with pytest.raises(ValueError, match="reserved '@' temporal separator"):
            volumetric.parse_volumetric_cell_key(
                "hsam:r08:cc:g2f39nh7keq4h9f0:v0.0-3.5@2026-04-20"
            )


class TestAltitudeValidation:
    """AC6 — altitude validation rejects invalid ranges."""

    def test_ac6_rejects_min_equal_max(self):
        with pytest.raises(ValueError, match="strictly less than"):
            volumetric.validate_altitude_range(5.0, 5.0)

    def test_ac6_rejects_min_greater_than_max(self):
        with pytest.raises(ValueError, match="strictly less than"):
            volumetric.validate_altitude_range(7.0, 5.0)

    def test_ac6_rejects_band_thinner_than_half_metre(self):
        with pytest.raises(ValueError, match="thickness"):
            volumetric.validate_altitude_range(0.0, 0.3)

    def test_ac6_accepts_exactly_half_metre_band(self):
        volumetric.validate_altitude_range(0.0, 0.5)
        # passes — no raise

    def test_ac6_rejects_below_seabed_floor(self):
        with pytest.raises(ValueError, match="out_of_range"):
            volumetric.validate_altitude_range(-11500.0, -11000.5)

    def test_ac6_accepts_exactly_at_seabed_floor(self):
        volumetric.validate_altitude_range(-11000.0, -10000.0)

    def test_ac6_accepts_aviation_band(self):
        # Above 1,000m is accepted, not rejected
        volumetric.validate_altitude_range(30.0, 5000.0)
        assert volumetric.is_aviation_domain(5000.0)

    def test_ac6_rejects_non_numeric_altitude(self):
        with pytest.raises(ValueError):
            volumetric.validate_altitude_range("hello", 5.0)   # type: ignore[arg-type]

    def test_ac6_rejects_boolean_altitude(self):
        with pytest.raises(ValueError):
            volumetric.validate_altitude_range(True, 5.0)     # type: ignore[arg-type]


class TestKeyDerivationEdgeCases:

    def test_derive_rejects_malformed_surface_key(self):
        with pytest.raises(ValueError, match="does not match Stage 1 format"):
            volumetric.derive_volumetric_cell_key("not-a-cell-key", 0.0, 3.5)

    def test_derive_rejects_already_volumetric_surface_key(self):
        with pytest.raises(ValueError, match="already volumetric"):
            volumetric.derive_volumetric_cell_key(
                "hsam:r08:cc:g2f39nh7keq4h9f0:v0.0-3.5", 3.5, 7.0
            )

    def test_derive_rejects_temporal_suffix_in_input(self):
        with pytest.raises(ValueError, match="reserved '@' separator"):
            volumetric.derive_volumetric_cell_key(
                "hsam:r08:cc:g2f39nh7keq4h9f0@2026-04-20", 0.0, 3.5
            )


class TestDiscriminators:

    def test_is_volumetric_true_for_volumetric_key(self):
        assert volumetric.is_volumetric_key(
            "hsam:r08:cc:g2f39nh7keq4h9f0:v0.0-3.5"
        )

    def test_is_volumetric_false_for_surface_key(self):
        assert not volumetric.is_volumetric_key(GOSFORD_WATERFRONT_SURFACE)

    def test_is_surface_true_for_surface_key(self):
        assert volumetric.is_surface_key(GOSFORD_WATERFRONT_SURFACE)

    def test_is_surface_false_for_volumetric_key(self):
        assert not volumetric.is_surface_key(
            "hsam:r08:cc:g2f39nh7keq4h9f0:v0.0-3.5"
        )

    def test_both_false_for_temporal_suffix(self):
        """Neither discriminator accepts the reserved @-suffix form."""
        k = "hsam:r08:cc:g2f39nh7keq4h9f0:v0.0-3.5@2026-04-20"
        assert not volumetric.is_volumetric_key(k)
        assert not volumetric.is_surface_key(k)


# ==========================================================================
# C. FORWARD-COMPATIBILITY CONFIRMATION (AC10)
# ==========================================================================


class TestForwardCompatibility:
    """AC10 — schema and key format must not foreclose 4D temporal model."""

    def test_ac10_reserved_temporal_separator_constant(self):
        """The module exposes the reserved separator as a constant."""
        assert volumetric.RESERVED_TEMPORAL_SEPARATOR == "@"

    def test_ac10_volumetric_key_never_emits_temporal_separator(self):
        """No generated volumetric key may contain the @ separator."""
        for band in [(0.0, 3.5), (-45.0, 0.0), (30.0, 100.0), (0.0, 5000.0)]:
            key = volumetric.derive_volumetric_cell_key(
                GOSFORD_WATERFRONT_SURFACE, band[0], band[1]
            )
            assert "@" not in key

    def test_ac10_parser_rejects_temporal_separator(self):
        """Parser must reject any volumetric key with an @-suffix."""
        with pytest.raises(ValueError):
            volumetric.parse_volumetric_cell_key(
                "hsam:r08:cc:g2f39nh7keq4h9f0:v0.0-3.5@2026-04-20"
            )

    def test_ac10_temporal_suffix_would_be_appendable_to_any_key(self):
        """
        Demonstrates forward compatibility: given a volumetric key K,
        appending '@{date}' yields a parse-recognisable (but rejected-by-
        Stage-2) candidate 4D form. The 3D key is a prefix of the 4D form —
        this is the structural guarantee that 3D does not foreclose 4D.
        """
        k = volumetric.derive_volumetric_cell_key(
            GOSFORD_WATERFRONT_SURFACE, 0.0, 3.5
        )
        future_4d = k + "@2026-04-20"
        # The 3D key is a proper prefix of the 4D form — 4D can be stripped
        # cleanly without disturbing the volumetric identity.
        assert future_4d.startswith(k)
        assert future_4d.split("@", 1)[0] == k


# ==========================================================================
# B. HTTP INTEGRATION TESTS — require live API + migration 003 applied
# ==========================================================================
#
# These tests exercise the AC1/AC2/AC7/AC8/AC9 criteria against the live
# FastAPI server. They are marked `http` and are skipped when the server
# is not reachable. Run with:
#
#   pytest harmony/tests/test_p1_stage2_acceptance.py -v -m http
#
# Prerequisites:
#   1. Migration 003 applied
#   2. Server running on HARMONY_API_URL (default http://127.0.0.1:8000)


try:
    import httpx  # noqa: F401
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False


def _api_url() -> str:
    return os.environ.get("HARMONY_API_URL", "http://127.0.0.1:8000").rstrip("/")


def _server_reachable() -> bool:
    if not _HTTPX_AVAILABLE:
        return False
    try:
        import httpx as _httpx
        r = _httpx.get(_api_url() + "/health", timeout=1.0)
        return r.status_code == 200
    except Exception:
        return False


pytestmark_http = pytest.mark.skipif(
    not _server_reachable(),
    reason="HARMONY_API_URL server not reachable; skipping HTTP suite",
)


@pytest.mark.http
@pytestmark_http
class TestStage2HttpIntegration:
    """AC1, AC2, AC7, AC8 — HTTP surface behaviour."""

    @pytest.fixture(scope="class")
    def surface_cell(self):
        """Register a surface cell for these tests. Reused across cases.

        Uses the known-valid Gosford Waterfront L8 fixture from
        `test_end_to_end.py` — a pre-computed cell_key + grid position
        that the server accepts. POST /cells is idempotent on cell_key,
        so repeated runs reuse the same record.
        """
        import httpx
        surface_body = {
            "cell_key": "hsam:r08:cc:g2f39nh7keq4h9f0",
            "resolution_level": 8,
            "cube_face": 1,
            "face_grid_u": 50678,
            "face_grid_v": 8290,
            "region_code": "cc",
            "friendly_name": "Stage2 test surface (Gosford Waterfront L8)",
        }
        r = httpx.post(_api_url() + "/cells", json=surface_body, timeout=5.0)
        if r.status_code not in (200, 201):
            pytest.skip(
                "Unable to create surface cell for Stage 2 HTTP tests: "
                + r.text
            )
        return r.json()

    def test_ac1_stage1_surface_cell_adjacency_unchanged(self, surface_cell):
        """Surface cell adjacency must return the Stage 1 ring shape,
        with no vertical field."""
        import httpx
        cell_key = surface_cell["cell_key"]
        r = httpx.get(f"{_api_url()}/cells/{cell_key}/adjacency?depth=1")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "ring" in body
        assert "vertical" not in body

    def test_ac2_volumetric_cell_registration(self, surface_cell):
        import httpx
        vol_body = {
            "surface_cell_id": surface_cell["canonical_id"],
            "altitude_min_m": 0.0,
            "altitude_max_m": 3.5,
            "friendly_name": "Stage2 ground floor",
        }
        r = httpx.post(_api_url() + "/cells/volumetric", json=vol_body)
        assert r.status_code in (200, 201), r.text
        body = r.json()
        assert body["is_volumetric"] is True
        assert body["altitude_min_m"] == 0.0
        assert body["altitude_max_m"] == 3.5
        assert body["cell_key"].endswith(":v0.0-3.5")

    def test_ac7_vertical_adjacency_resolves(self, surface_cell):
        """Register ground + first floor, confirm up/down neighbours resolve."""
        import httpx
        parent = surface_cell["canonical_id"]
        httpx.post(
            _api_url() + "/cells/volumetric",
            json={"surface_cell_id": parent, "altitude_min_m": 0.0, "altitude_max_m": 3.5},
        )
        r2 = httpx.post(
            _api_url() + "/cells/volumetric",
            json={"surface_cell_id": parent, "altitude_min_m": 3.5, "altitude_max_m": 7.0},
        )
        assert r2.status_code in (200, 201)
        first_floor_key = r2.json()["cell_key"]
        # Now check ground floor has first floor as its up-neighbour
        ground_key = r2.json()["cell_key"].replace(":v3.5-7.0", ":v0.0-3.5")
        r3 = httpx.get(f"{_api_url()}/cells/{ground_key}/adjacency")
        assert r3.status_code == 200, r3.text
        body = r3.json()
        assert body["is_volumetric"] is True
        assert body["vertical"]["up"] == first_floor_key
        assert body["vertical"]["down"] is None

    def test_ac8_surface_cell_adjacency_has_no_vertical_key(self, surface_cell):
        """AC8 — surface adjacency endpoint response unchanged, no vertical key."""
        import httpx
        r = httpx.get(f"{_api_url()}/cells/{surface_cell['cell_key']}/adjacency")
        body = r.json()
        assert "vertical" not in body

    def test_ac2_rejects_invalid_altitude_range(self, surface_cell):
        """Validation rejects thin bands."""
        import httpx
        r = httpx.post(
            _api_url() + "/cells/volumetric",
            json={
                "surface_cell_id": surface_cell["canonical_id"],
                "altitude_min_m": 0.0,
                "altitude_max_m": 0.3,
            },
        )
        assert r.status_code == 400


# ==========================================================================
# AC9 — migration file has both up and down functions
# ==========================================================================


class TestMigrationShape:

    def test_ac9_migration_file_exists_and_has_down_block(self):
        migration_path = os.path.abspath(
            os.path.join(_PILLAR_ROOT, "db", "migrations",
                         "003_volumetric_cell_extension.sql")
        )
        assert os.path.exists(migration_path), (
            "Stage 2 migration missing: " + migration_path
        )
        contents = open(migration_path).read()
        # Up block: ADD COLUMN and CHECK constraints
        assert "ADD COLUMN IF NOT EXISTS is_volumetric" in contents
        assert "altitude_min_m" in contents
        assert "vertical_adjacent_cell_keys" in contents
        # Down block: reverses the changes (commented out for safety)
        assert "DOWN MIGRATION" in contents
        assert "DROP COLUMN IF EXISTS is_volumetric" in contents
        assert "DROP COLUMN IF EXISTS altitude_min_m" in contents
