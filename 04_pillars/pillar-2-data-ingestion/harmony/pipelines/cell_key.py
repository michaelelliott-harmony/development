# Harmony Pillar 2 — Cell Key Computation
#
# Pure-math cell key derivation vendored from Pillar 1's derive.py spec.
# Pillar 2 does NOT import Pillar 1 modules directly per the non-negotiables.
# This module replicates only the mathematical functions needed to compute
# cell keys and grid coordinates for cell registration.
#
# Reference: 04_pillars/pillar-1-spatial-substrate/harmony/packages/cell-key/src/derive.py
# Any change to the Pillar 1 derivation spec must be mirrored here.

from __future__ import annotations

import math
import struct
import blake3

# ---------------------------------------------------------------------------
# WGS84 Constants (NIMA TR8350.2, Third Edition) — must match Pillar 1 exactly
# ---------------------------------------------------------------------------

WGS84_A = 6378137.0
WGS84_F = 1.0 / 298.257223563
WGS84_B = WGS84_A * (1.0 - WGS84_F)
WGS84_E2 = 2.0 * WGS84_F - WGS84_F ** 2

HARMONY_NAMESPACE = "hsam"
MIN_RESOLUTION = 0
MAX_RESOLUTION = 12
HASH_BYTES = 10
HASH_CHARS = 16

CROCKFORD_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"

# Approximate Earth surface area in m²
EARTH_SURFACE_M2 = 5.1006e14  # 510.06 million km²


class CellCoordinates:
    """All information needed to register a cell via the Pillar 1 API."""
    __slots__ = (
        "cell_key", "resolution_level", "cube_face",
        "face_grid_u", "face_grid_v", "region_code",
        "centroid_lat", "centroid_lon",
    )

    def __init__(
        self,
        cell_key: str,
        resolution_level: int,
        cube_face: int,
        face_grid_u: int,
        face_grid_v: int,
        region_code: str,
        centroid_lat: float,
        centroid_lon: float,
    ) -> None:
        self.cell_key = cell_key
        self.resolution_level = resolution_level
        self.cube_face = cube_face
        self.face_grid_u = face_grid_u
        self.face_grid_v = face_grid_v
        self.region_code = region_code
        self.centroid_lat = centroid_lat
        self.centroid_lon = centroid_lon


def cell_edge_m(resolution: int) -> float:
    """Approximate cell edge length in metres at the given resolution.

    Derived from: each cube face has (4^r)² cells, 6 faces total.
    Approximate because of gnomonic distortion (up to 2.3× at face corners).
    Returns the geometric mean edge length for planning purposes.
    """
    cells_per_face = (4 ** resolution) ** 2
    cell_area_m2 = EARTH_SURFACE_M2 / (6 * cells_per_face)
    return math.sqrt(cell_area_m2)


def adaptive_resolution(
    bbox_diagonal_m: float,
    floor_level: int,
) -> int:
    """Choose the geometry-adaptive resolution level for a feature.

    Target: cell edge ≈ bbox_diagonal / 16 (entity spans ~16-256 cells),
    but never below floor_level and never above MAX_RESOLUTION.

    Parameters
    ----------
    bbox_diagonal_m : float
        Diagonal of the feature's bounding box in metres.
    floor_level : int
        Minimum resolution level from the dataset manifest.
    """
    if bbox_diagonal_m <= 0:
        return max(floor_level, MAX_RESOLUTION)

    # R such that cell_edge_m(R) ≈ bbox_diagonal_m / 16
    # cell_edge = sqrt(EARTH_M2 / (6 × 16^R))
    # Solving: R = log(EARTH_M2 / (6 × (bbox/16)²)) / (2 × log(4))
    target_edge = bbox_diagonal_m / 16.0
    if target_edge <= 0:
        return MAX_RESOLUTION
    r = math.log(EARTH_SURFACE_M2 / (6.0 * target_edge ** 2)) / (2.0 * math.log(4.0))
    r_int = int(math.floor(r))
    r_int = max(floor_level, min(MAX_RESOLUTION, r_int))
    return r_int


def derive(lat: float, lon: float, resolution: int, region_code: str) -> CellCoordinates:
    """Derive all cell registration parameters for a geographic coordinate.

    Parameters
    ----------
    lat, lon : float
        WGS84 coordinate in decimal degrees.
    resolution : int
        Harmony resolution level 0-12.
    region_code : str
        Lowercase alphabetic region code, e.g. "cc" for Central Coast.

    Returns
    -------
    CellCoordinates
        All fields needed for POST /cells.
    """
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Latitude out of range: {lat}")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Longitude out of range: {lon}")
    if not (MIN_RESOLUTION <= resolution <= MAX_RESOLUTION):
        raise ValueError(f"Resolution out of range: {resolution}")

    # Step 1: WGS84 → ECEF (alt = 0)
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)
    sin_lat, cos_lat = math.sin(lat_r), math.cos(lat_r)
    sin_lon, cos_lon = math.sin(lon_r), math.cos(lon_r)
    n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat ** 2)
    x = n * cos_lat * cos_lon
    y = n * cos_lat * sin_lon
    z = n * (1.0 - WGS84_E2) * sin_lat

    # Step 2: Normalise to unit sphere
    norm = math.sqrt(x * x + y * y + z * z)
    nx, ny, nz = x / norm, y / norm, z / norm

    # Step 3: Project to cube face
    face, u, v = _project_to_cube_face(nx, ny, nz)

    # Step 4: Snap to resolution grid
    grid_n = 4 ** resolution
    if grid_n == 1:
        gi, gj = 0, 0
    else:
        gi = int(math.floor((u + 1.0) / 2.0 * grid_n))
        gj = int(math.floor((v + 1.0) / 2.0 * grid_n))
        gi = max(0, min(gi, grid_n - 1))
        gj = max(0, min(gj, grid_n - 1))

    # Step 5: Compute grid cell centre in UV space
    u_c = (2.0 * gi + 1.0) / grid_n - 1.0
    v_c = (2.0 * gj + 1.0) / grid_n - 1.0

    # Step 6: Inverse-project to unit sphere direction
    dir_x, dir_y, dir_z = _cube_face_to_direction(face, u_c, v_c)

    # Step 7: Unit sphere → geodetic centroid
    centroid_lon_r = math.atan2(dir_y, dir_x)
    geocentric_lat = math.asin(max(-1.0, min(1.0, dir_z)))
    if abs(geocentric_lat) < math.pi / 2 - 1e-10:
        geodetic_lat = math.atan2(math.tan(geocentric_lat), 1.0 - WGS84_E2)
    else:
        geodetic_lat = geocentric_lat
    sin_gl = math.sin(geodetic_lat)
    cos_gl = math.cos(geodetic_lat)
    n_prime = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_gl ** 2)
    cx = n_prime * cos_gl * math.cos(centroid_lon_r)
    cy = n_prime * cos_gl * math.sin(centroid_lon_r)
    cz = n_prime * (1.0 - WGS84_E2) * sin_gl

    # Step 8: Build hash input and BLAKE3 hash
    hash_input = (
        HARMONY_NAMESPACE.encode("utf-8")
        + struct.pack("<d", cx)
        + struct.pack("<d", cy)
        + struct.pack("<d", cz)
        + struct.pack("B", resolution)
    )
    digest = blake3.blake3(hash_input).digest(length=HASH_BYTES)
    hash_fragment = _crockford_base32_encode(digest)[:HASH_CHARS]

    cell_key = f"{HARMONY_NAMESPACE}:r{resolution:02d}:{region_code}:{hash_fragment}"

    centroid_lat = math.degrees(geodetic_lat)
    centroid_lon = math.degrees(centroid_lon_r)

    return CellCoordinates(
        cell_key=cell_key,
        resolution_level=resolution,
        cube_face=face,
        face_grid_u=gi,
        face_grid_v=gj,
        region_code=region_code,
        centroid_lat=centroid_lat,
        centroid_lon=centroid_lon,
    )


def _project_to_cube_face(nx: float, ny: float, nz: float) -> tuple:
    ax, ay, az = abs(nx), abs(ny), abs(nz)
    if ax >= ay and ax >= az:
        face = 0 if nx >= 0 else 1
        u, v = ny / ax, nz / ax
    elif ay >= ax and ay >= az:
        face = 2 if ny >= 0 else 3
        u, v = nx / ay, nz / ay
    else:
        face = 4 if nz >= 0 else 5
        u, v = nx / az, ny / az
    return face, u, v


def _cube_face_to_direction(face: int, u: float, v: float) -> tuple:
    if face == 0:
        dx, dy, dz = 1.0, u, v
    elif face == 1:
        dx, dy, dz = -1.0, u, v
    elif face == 2:
        dx, dy, dz = u, 1.0, v
    elif face == 3:
        dx, dy, dz = u, -1.0, v
    elif face == 4:
        dx, dy, dz = u, v, 1.0
    else:
        dx, dy, dz = u, v, -1.0
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    return dx / norm, dy / norm, dz / norm


def _crockford_base32_encode(data: bytes) -> str:
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
    if bits_in_buffer > 0:
        index = (bit_buffer << (5 - bits_in_buffer)) & 0x1F
        result.append(CROCKFORD_ALPHABET[index])
    return "".join(result)
