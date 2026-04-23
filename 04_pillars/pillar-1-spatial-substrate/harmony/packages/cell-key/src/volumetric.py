# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Volumetric Cell Key Module (Stage 2)
#
# Pure-logic module: deterministic derivation, parsing, and validation of
# volumetric (3D) cell keys that extend the Stage 1 surface key format.
#
# Reference: ADR-015 (Adaptive Volumetric Cell Extension, Accepted),
#            ADR-017 (Stage 2 Implementation, Accepted).
# No database, network, or filesystem access.

import re

# --------------------------------------------------------------------------
# Format constants — ADR-015 §2.3
# --------------------------------------------------------------------------

SURFACE_CELL_KEY_PATTERN = (
    r"^hsam:r[0-9]{2}:[a-z]{2,8}:[0-9a-hjkmnp-tv-z]{16}$"
)

# Volumetric = surface key + ":v{alt_min}-{alt_max}" where each altitude is
# an optional minus, digits, a required single decimal place.
VOLUMETRIC_ALT_FRAGMENT = r"-?[0-9]+\.[0-9]"
VOLUMETRIC_CELL_KEY_PATTERN = (
    r"^hsam:r[0-9]{2}:[a-z]{2,8}:[0-9a-hjkmnp-tv-z]{16}"
    r":v(" + VOLUMETRIC_ALT_FRAGMENT + r")-(" + VOLUMETRIC_ALT_FRAGMENT + r")$"
)

_SURFACE_RE = re.compile(SURFACE_CELL_KEY_PATTERN)
_VOLUMETRIC_RE = re.compile(VOLUMETRIC_CELL_KEY_PATTERN)

# --------------------------------------------------------------------------
# Validation bounds — ADR-015 §2.5
# --------------------------------------------------------------------------

ALTITUDE_MIN_LIMIT_M = -11000.0     # seabed floor
ALTITUDE_AVIATION_THRESHOLD_M = 1000.0   # above this is aviation domain
MIN_BAND_THICKNESS_M = 0.5

# The @ separator is reserved for Pillar 4 temporal suffixes. Stage 2 must
# reject it in volumetric keys and must never emit it.
RESERVED_TEMPORAL_SEPARATOR = "@"


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

def validate_altitude_range(alt_min: float, alt_max: float) -> None:
    """
    Validate a candidate altitude range for a volumetric cell.

    Raises ValueError with a specific message on any rule violation.
    Rules — ADR-015 §2.5:
      - both values must be numeric
      - alt_min < alt_max
      - alt_max - alt_min >= 0.5 (band thickness)
      - alt_min >= -11,000m (seabed floor)

    Altitudes above 1,000m are accepted without raising; callers that need
    the aviation_domain flag should consult is_aviation_domain().
    """
    if not isinstance(alt_min, (int, float)) or isinstance(alt_min, bool):
        raise ValueError(
            "altitude_min_m must be numeric, got " + repr(type(alt_min).__name__)
        )
    if not isinstance(alt_max, (int, float)) or isinstance(alt_max, bool):
        raise ValueError(
            "altitude_max_m must be numeric, got " + repr(type(alt_max).__name__)
        )
    if alt_min >= alt_max:
        raise ValueError(
            "altitude_min_m must be strictly less than altitude_max_m "
            "(got min=" + str(alt_min) + ", max=" + str(alt_max) + ")"
        )
    if (alt_max - alt_min) < MIN_BAND_THICKNESS_M:
        raise ValueError(
            "band thickness must be at least "
            + str(MIN_BAND_THICKNESS_M) + "m "
            "(got " + str(alt_max - alt_min) + "m)"
        )
    if alt_min < ALTITUDE_MIN_LIMIT_M:
        raise ValueError(
            "altitude_min_m is out_of_range: "
            + str(alt_min) + "m is below seabed limit "
            + str(ALTITUDE_MIN_LIMIT_M) + "m"
        )


def is_aviation_domain(alt_max: float) -> bool:
    """Return True if the band's upper bound crosses the aviation threshold."""
    return alt_max > ALTITUDE_AVIATION_THRESHOLD_M


# --------------------------------------------------------------------------
# Altitude formatting
# --------------------------------------------------------------------------

def format_altitude(value_m: float) -> str:
    """
    Format an altitude value for inclusion in a volumetric cell key.

    One decimal place, standard minus prefix for negatives, no scientific
    notation. Normalises -0.0 to 0.0 so the format is unique per value.
    """
    if not isinstance(value_m, (int, float)) or isinstance(value_m, bool):
        raise ValueError(
            "altitude value must be numeric, got " + repr(type(value_m).__name__)
        )
    rounded = round(float(value_m), 1)
    if rounded == 0.0:
        rounded = 0.0   # coerce any -0.0 to 0.0
    return f"{rounded:.1f}"


# --------------------------------------------------------------------------
# Derivation and parsing
# --------------------------------------------------------------------------

def derive_volumetric_cell_key(
    surface_cell_key: str, alt_min: float, alt_max: float
) -> str:
    """
    Build the deterministic volumetric cell key for a (surface, band) tuple.

    Determinism rule — ADR-015 §2.3:
        same (surface_cell_key, alt_min, alt_max) always produces same key.

    Parameters
    ----------
    surface_cell_key : str
        A Stage 1 surface cell key. Must match SURFACE_CELL_KEY_PATTERN.
    alt_min, alt_max : float
        Band bounds in metres. Validated with validate_altitude_range.

    Returns
    -------
    str
        The volumetric cell key. Matches VOLUMETRIC_CELL_KEY_PATTERN.

    Raises
    ------
    ValueError
        If the surface key is malformed or already volumetric, or the
        altitude range is invalid.
    """
    if not isinstance(surface_cell_key, str):
        raise ValueError(
            "surface_cell_key must be a string, got "
            + type(surface_cell_key).__name__
        )
    if RESERVED_TEMPORAL_SEPARATOR in surface_cell_key:
        raise ValueError(
            "surface_cell_key contains reserved '@' separator; "
            "temporal suffix is not implemented in Stage 2"
        )
    if _VOLUMETRIC_RE.match(surface_cell_key):
        raise ValueError(
            "surface_cell_key is already volumetric; "
            "nested subdivision is not supported in Stage 2"
        )
    if not _SURFACE_RE.match(surface_cell_key):
        raise ValueError(
            "surface_cell_key does not match Stage 1 format: "
            + repr(surface_cell_key)
        )

    validate_altitude_range(alt_min, alt_max)

    return (
        surface_cell_key
        + ":v"
        + format_altitude(alt_min)
        + "-"
        + format_altitude(alt_max)
    )


def parse_volumetric_cell_key(cell_key: str) -> dict:
    """
    Parse a volumetric cell key into its constituent components.

    Returns a dict with:
        namespace, resolution, region_code, hash_fragment,
        surface_cell_key, altitude_min_m, altitude_max_m

    Raises ValueError on any format violation, including a reserved `@`
    temporal separator.
    """
    if not isinstance(cell_key, str):
        raise ValueError(
            "cell_key must be a string, got " + type(cell_key).__name__
        )
    if RESERVED_TEMPORAL_SEPARATOR in cell_key:
        raise ValueError(
            "cell_key contains reserved '@' temporal separator; "
            "Stage 2 does not implement the temporal suffix"
        )

    match = _VOLUMETRIC_RE.match(cell_key)
    if match is None:
        raise ValueError(
            "cell_key is not a valid volumetric key: " + repr(cell_key)
        )

    surface_part = cell_key.rsplit(":v", 1)[0]
    surface_match = _SURFACE_RE.match(surface_part)
    if surface_match is None:
        raise ValueError(
            "derived surface portion is not a valid surface key: "
            + repr(surface_part)
        )

    alt_min_str = match.group(1)
    alt_max_str = match.group(2)

    try:
        alt_min = float(alt_min_str)
        alt_max = float(alt_max_str)
    except ValueError as exc:
        raise ValueError("invalid altitude in cell_key: " + str(exc))

    _, resolution_str, region_code, hash_fragment = surface_part.split(":")

    return {
        "namespace": "hsam",
        "resolution": int(resolution_str[1:]),
        "region_code": region_code,
        "hash_fragment": hash_fragment,
        "surface_cell_key": surface_part,
        "altitude_min_m": alt_min,
        "altitude_max_m": alt_max,
    }


def is_volumetric_key(cell_key: str) -> bool:
    """True if cell_key matches the volumetric format. False otherwise."""
    if not isinstance(cell_key, str):
        return False
    if RESERVED_TEMPORAL_SEPARATOR in cell_key:
        return False
    return _VOLUMETRIC_RE.match(cell_key) is not None


def is_surface_key(cell_key: str) -> bool:
    """True if cell_key matches the Stage 1 surface format. False otherwise."""
    if not isinstance(cell_key, str):
        return False
    if RESERVED_TEMPORAL_SEPARATOR in cell_key:
        return False
    return _SURFACE_RE.match(cell_key) is not None
