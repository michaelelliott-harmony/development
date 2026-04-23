# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Cell Key Derivation Module
#
# This module implements the deterministic derivation of Harmony cell keys
# from geographic coordinates. It is a pure computation library with no
# database calls, network calls, or file I/O.
#
# Reference: cell_key_derivation_spec.md
# Reference: cell_geometry_spec.md

import math
import struct
import blake3


# ---------------------------------------------------------------------------
# WGS84 Ellipsoid Constants (NIMA TR8350.2, Third Edition)
# These are compile-time constants. They must NOT be looked up at runtime.
# ---------------------------------------------------------------------------

WGS84_A = 6378137.0                        # Semi-major axis (metres)
WGS84_F = 1.0 / 298.257223563              # Flattening
WGS84_B = WGS84_A * (1.0 - WGS84_F)       # Semi-minor axis (metres)
WGS84_E2 = 2.0 * WGS84_F - WGS84_F ** 2   # First eccentricity squared


# ---------------------------------------------------------------------------
# Harmony Cell System Constants
# ---------------------------------------------------------------------------

HARMONY_NAMESPACE = "hsam"
MIN_RESOLUTION = 0
MAX_RESOLUTION = 12
HASH_BYTES = 10     # 80 bits of BLAKE3 output
HASH_CHARS = 16     # 80 bits / 5 bits per Crockford Base32 character

# Crockford Base32 alphabet (lowercase): excludes i, l, o, u
CROCKFORD_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def wgs84_to_ecef(lat: float, lon: float, alt: float = 0.0) -> tuple:
    """
    Convert WGS84 geodetic coordinates to ECEF Cartesian coordinates.

    Uses the standard geodetic-to-ECEF conversion with the WGS84 reference
    ellipsoid. The formulae and constants follow NIMA TR8350.2.

    Parameters
    ----------
    lat : float
        Geodetic latitude in decimal degrees. Range: [-90, 90].
    lon : float
        Geodetic longitude in decimal degrees. Range: [-180, 180].
    alt : float, optional
        Altitude above WGS84 ellipsoid in metres. Default 0.0.
        Note: For cell key derivation, altitude is ignored (cells are 2D).

    Returns
    -------
    tuple of (float, float, float)
        ECEF coordinates (x, y, z) in metres.

    Raises
    ------
    ValueError
        If latitude or longitude is out of valid range.
    """
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        raise ValueError(
            "Latitude and longitude must be numeric. "
            "Got lat=" + repr(type(lat).__name__) + ", lon=" + repr(type(lon).__name__)
        )
    if not (-90.0 <= lat <= 90.0):
        raise ValueError("Latitude must be in [-90, 90], got " + str(lat))
    if not (-180.0 <= lon <= 180.0):
        raise ValueError("Longitude must be in [-180, 180], got " + str(lon))

    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    sin_lat = math.sin(lat_rad)
    cos_lat = math.cos(lat_rad)
    sin_lon = math.sin(lon_rad)
    cos_lon = math.cos(lon_rad)

    # Radius of curvature in the prime vertical
    n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat ** 2)

    x = (n + alt) * cos_lat * cos_lon
    y = (n + alt) * cos_lat * sin_lon
    z = (n * (1.0 - WGS84_E2) + alt) * sin_lat

    return (x, y, z)


def compute_cell_centroid(x: float, y: float, z: float, resolution: int) -> tuple:
    """
    Compute the deterministic cell centroid in ECEF for the cell containing
    the given ECEF point at the specified resolution level.

    The algorithm projects the point onto the enclosing cube face (gnomonic
    projection), snaps to the resolution grid, computes the grid cell centre,
    and inverse-projects back to ECEF on the WGS84 ellipsoid.

    Parameters
    ----------
    x, y, z : float
        ECEF coordinates in metres.
    resolution : int
        Resolution level, 0-12. Determines grid density (4^r per axis per face).

    Returns
    -------
    tuple of (float, float, float)
        ECEF centroid coordinates (cx, cy, cz) in metres, on the WGS84
        ellipsoid surface (altitude = 0).

    Raises
    ------
    ValueError
        If resolution is out of range or coordinates are at the origin.
    """
    if not isinstance(resolution, int) or not (MIN_RESOLUTION <= resolution <= MAX_RESOLUTION):
        raise ValueError(
            "Resolution must be an integer in ["
            + str(MIN_RESOLUTION) + ", " + str(MAX_RESOLUTION)
            + "], got " + repr(resolution)
        )

    # Normalise to unit sphere direction
    norm = math.sqrt(x * x + y * y + z * z)
    if norm == 0:
        raise ValueError("Cannot derive cell centroid for the origin point (0, 0, 0)")
    nx, ny, nz = x / norm, y / norm, z / norm

    # Project onto cube face
    face, u, v = _project_to_cube_face(nx, ny, nz)

    # Snap to resolution grid
    grid_n = 4 ** resolution
    if grid_n == 1:
        # Level 0: one cell per face, centroid is face centre
        i, j = 0, 0
    else:
        i = int(math.floor((u + 1.0) / 2.0 * grid_n))
        j = int(math.floor((v + 1.0) / 2.0 * grid_n))
        i = max(0, min(i, grid_n - 1))
        j = max(0, min(j, grid_n - 1))

    # Compute grid cell centre in UV space
    u_c = (2.0 * i + 1.0) / grid_n - 1.0
    v_c = (2.0 * j + 1.0) / grid_n - 1.0

    # Inverse-project to unit sphere direction
    dir_x, dir_y, dir_z = _cube_face_to_direction(face, u_c, v_c)

    # Convert sphere direction to geodetic coordinates, then to ECEF at alt=0
    centroid_lon = math.atan2(dir_y, dir_x)
    geocentric_lat = math.asin(max(-1.0, min(1.0, dir_z)))

    # Convert geocentric latitude to geodetic latitude
    if abs(geocentric_lat) < math.pi / 2 - 1e-10:
        geodetic_lat = math.atan2(math.tan(geocentric_lat), (1.0 - WGS84_E2))
    else:
        geodetic_lat = geocentric_lat

    sin_lat = math.sin(geodetic_lat)
    cos_lat = math.cos(geodetic_lat)
    sin_lon = math.sin(centroid_lon)
    cos_lon = math.cos(centroid_lon)

    n_prime = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat ** 2)

    cx = n_prime * cos_lat * cos_lon
    cy = n_prime * cos_lat * sin_lon
    cz = n_prime * (1.0 - WGS84_E2) * sin_lat

    return (cx, cy, cz)


def build_hash_input(cx: float, cy: float, cz: float, resolution: int) -> bytes:
    """
    Construct the exact byte sequence fed into BLAKE3 for cell key derivation.

    The byte layout is fixed at 29 bytes:
        [0:4]   "hsam"  — UTF-8 namespace prefix
        [4:12]  cx      — IEEE 754 double, little-endian
        [12:20] cy      — IEEE 754 double, little-endian
        [20:28] cz      — IEEE 754 double, little-endian
        [28:29] resolution — unsigned 8-bit integer

    Parameters
    ----------
    cx, cy, cz : float
        ECEF centroid coordinates in metres.
    resolution : int
        Resolution level, 0-12.

    Returns
    -------
    bytes
        The 29-byte hash input.
    """
    namespace_bytes = HARMONY_NAMESPACE.encode("utf-8")   # 4 bytes
    cx_bytes = struct.pack("<d", cx)                        # 8 bytes
    cy_bytes = struct.pack("<d", cy)                        # 8 bytes
    cz_bytes = struct.pack("<d", cz)                        # 8 bytes
    resolution_byte = struct.pack("B", resolution)          # 1 byte

    return namespace_bytes + cx_bytes + cy_bytes + cz_bytes + resolution_byte


def derive_cell_key(
    lat: float,
    lon: float,
    resolution: int,
    region_code: str,
    alt: float = 0.0,
) -> str:
    """
    Derive the deterministic Harmony cell key for a geographic coordinate.

    This is the primary entry point for the module. It computes the cell_key
    by converting coordinates to ECEF, computing the deterministic cell
    centroid, hashing with BLAKE3, and formatting as a Harmony cell key string.

    The cell key format is:
        hsam:r{level:02d}:{region_code}:{hash_fragment}

    Parameters
    ----------
    lat : float
        WGS84 latitude in decimal degrees. Range: [-90, 90].
    lon : float
        WGS84 longitude in decimal degrees. Range: [-180, 180].
    resolution : int
        Resolution level, 0-12.
    region_code : str
        Harmony region code (e.g., "cc" for Central Coast NSW, "gbl" for
        global fallback). Must be non-empty lowercase alphabetic.
    alt : float, optional
        Altitude in metres. Ignored for cell key derivation (cells are 2D).
        Default 0.0.

    Returns
    -------
    str
        The complete cell key string.

    Raises
    ------
    ValueError
        If any input parameter is invalid.
    """
    if not isinstance(resolution, int) or not (MIN_RESOLUTION <= resolution <= MAX_RESOLUTION):
        raise ValueError(
            "Resolution must be an integer in ["
            + str(MIN_RESOLUTION) + ", " + str(MAX_RESOLUTION)
            + "], got " + repr(resolution)
        )
    if not isinstance(region_code, str) or len(region_code) == 0:
        raise ValueError("Region code must be a non-empty string, got " + repr(region_code))
    if not region_code.isalpha() or not region_code.islower():
        raise ValueError(
            "Region code must be lowercase alphabetic, got " + repr(region_code)
        )

    # Step 1: WGS84 to ECEF (altitude forced to 0 — cells are 2D)
    ecef_x, ecef_y, ecef_z = wgs84_to_ecef(lat, lon, alt=0.0)

    # Step 2: Compute deterministic cell centroid in ECEF
    cx, cy, cz = compute_cell_centroid(ecef_x, ecef_y, ecef_z, resolution)

    # Step 3: Build hash input (29 bytes)
    hash_input = build_hash_input(cx, cy, cz, resolution)

    # Step 4: BLAKE3 hash, take first HASH_BYTES bytes
    digest = blake3.blake3(hash_input).digest(length=HASH_BYTES)

    # Step 5: Encode as Crockford Base32, truncate to HASH_CHARS
    hash_fragment = _crockford_base32_encode(digest)[:HASH_CHARS]

    # Step 6: Assemble cell key
    level_str = "r" + str(resolution).zfill(2)
    cell_key = (
        HARMONY_NAMESPACE + ":" + level_str + ":" + region_code + ":" + hash_fragment
    )

    return cell_key


def parse_cell_key(cell_key: str) -> dict:
    """
    Parse a Harmony cell key string into its constituent components.

    Parameters
    ----------
    cell_key : str
        A Harmony cell key string (e.g., "hsam:r08:cc:g2f39nh7keq4h9f0").

    Returns
    -------
    dict
        {
            "namespace": str,       # Always "hsam"
            "resolution": int,      # 0-12
            "region_code": str,     # e.g., "cc"
            "hash_fragment": str    # 16-char Crockford Base32 string
        }

    Raises
    ------
    ValueError
        If the cell key format is invalid.
    """
    if not isinstance(cell_key, str):
        raise ValueError("Cell key must be a string, got " + type(cell_key).__name__)

    parts = cell_key.split(":")
    if len(parts) != 4:
        raise ValueError(
            "Cell key must have exactly 4 colon-separated components, got "
            + str(len(parts)) + ": " + repr(cell_key)
        )

    namespace, resolution_str, region_code, hash_fragment = parts

    if namespace != HARMONY_NAMESPACE:
        raise ValueError(
            "Cell key namespace must be '" + HARMONY_NAMESPACE
            + "', got " + repr(namespace)
        )

    if not resolution_str.startswith("r"):
        raise ValueError(
            "Resolution component must start with 'r', got " + repr(resolution_str)
        )

    try:
        resolution = int(resolution_str[1:])
    except ValueError:
        raise ValueError(
            "Resolution must be a valid integer, got " + repr(resolution_str)
        )

    if not (MIN_RESOLUTION <= resolution <= MAX_RESOLUTION):
        raise ValueError(
            "Resolution must be in [" + str(MIN_RESOLUTION) + ", "
            + str(MAX_RESOLUTION) + "], got " + str(resolution)
        )

    # Validate hash fragment characters
    valid_chars = set(CROCKFORD_ALPHABET)
    invalid = set(hash_fragment) - valid_chars
    if invalid:
        raise ValueError(
            "Hash fragment contains invalid Crockford Base32 characters: "
            + repr(invalid)
        )

    return {
        "namespace": namespace,
        "resolution": resolution,
        "region_code": region_code,
        "hash_fragment": hash_fragment,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _project_to_cube_face(nx: float, ny: float, nz: float) -> tuple:
    """
    Project a unit-sphere direction onto the enclosing cube face
    using gnomonic projection.

    Returns (face_index, u, v) where face_index is 0-5 and u, v
    are in [-1, 1].

    Face assignment:
        0: +X  (nx dominant, non-negative)
        1: -X  (nx dominant, negative)
        2: +Y  (ny dominant, non-negative)
        3: -Y  (ny dominant, negative)
        4: +Z  (nz dominant, non-negative)
        5: -Z  (nz dominant, negative)

    Tie-breaking: X beats Y beats Z (lowest index wins).
    """
    ax, ay, az = abs(nx), abs(ny), abs(nz)

    if ax >= ay and ax >= az:
        face = 0 if nx >= 0 else 1
        u = ny / ax
        v = nz / ax
    elif ay >= ax and ay >= az:
        face = 2 if ny >= 0 else 3
        u = nx / ay
        v = nz / ay
    else:
        face = 4 if nz >= 0 else 5
        u = nx / az
        v = ny / az

    return (face, u, v)


def _cube_face_to_direction(face: int, u: float, v: float) -> tuple:
    """
    Inverse of cube face projection: convert (face, u, v) back to a
    normalised unit-sphere direction (nx, ny, nz).
    """
    if face == 0:      # +X
        dx, dy, dz = 1.0, u, v
    elif face == 1:    # -X
        dx, dy, dz = -1.0, u, v
    elif face == 2:    # +Y
        dx, dy, dz = u, 1.0, v
    elif face == 3:    # -Y
        dx, dy, dz = u, -1.0, v
    elif face == 4:    # +Z
        dx, dy, dz = u, v, 1.0
    elif face == 5:    # -Z
        dx, dy, dz = u, v, -1.0
    else:
        raise ValueError("Invalid face index: " + str(face))

    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    return (dx / norm, dy / norm, dz / norm)


def _crockford_base32_encode(data: bytes) -> str:
    """
    Encode bytes to lowercase Crockford Base32 string.

    Processes 5 bits at a time from the input byte sequence.
    Remaining bits (if any) are left-padded with zeros.
    """
    result = []
    bit_buffer = 0
    bits_in_buffer = 0

    for byte in data:
        bit_buffer = (bit_buffer << 8) | byte
        bits_in_buffer += 8

        while bits_in_buffer >= 5:
            bits_in_buffer -= 5
            index = (bit_buffer >> bits_in_buffer) & 0x1F
            result.append(CROCKFORD_ALPHABET[index])

    # Handle remaining bits
    if bits_in_buffer > 0:
        index = (bit_buffer << (5 - bits_in_buffer)) & 0x1F
        result.append(CROCKFORD_ALPHABET[index])

    return "".join(result)
