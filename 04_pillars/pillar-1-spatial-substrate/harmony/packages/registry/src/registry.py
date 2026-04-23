# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Identity Registry Service
#
# This module implements the Identity Registry — the single source of truth
# for all Harmony spatial objects. It provides CRUD operations for cells and
# entities, canonical resolution, alias management, and adjacency queries.
#
# Database: PostgreSQL via psycopg2 (no ORM)
# Connection: HARMONY_DB_URL environment variable
# Reference: identity_registry_schema.sql, cell_identity_schema.json,
#            id_generation_rules.md, cell_adjacency_spec.md

import os
import math
import secrets
import re
import logging
from datetime import datetime, timezone
from typing import Optional

import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CROCKFORD_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
SCHEMA_VERSION = "0.2.0"

# ID format patterns (from id_generation_rules.md §9)
# Surface cell keys are unchanged from Stage 1. Volumetric keys add the
# altitude suffix `:v{alt_min}-{alt_max}` — see ADR-015 §2.3.
PATTERNS = {
    "cell": re.compile(r"^hc_[a-z0-9]{9}$"),
    "entity": re.compile(r"^ent_[a-z]{3}_[a-z0-9]{6}$"),
    "dataset": re.compile(r"^ds_[a-z0-9]{8}$"),
    "state": re.compile(r"^st_[a-z0-9]{10}$"),
    "contract_anchor": re.compile(r"^ca_[a-z]{3}_[a-z0-9]{8}$"),
    "cell_key": re.compile(r"^hsam:r[0-9]{2}:[a-z]{2,8}:[0-9a-hjkmnp-tv-z]{16}$"),
    "volumetric_cell_key": re.compile(
        r"^hsam:r[0-9]{2}:[a-z]{2,8}:[0-9a-hjkmnp-tv-z]{16}"
        r":v-?[0-9]+\.[0-9]--?[0-9]+\.[0-9]$"
    ),
    "alias_id": re.compile(r"^al_[a-z0-9]{9}$"),
}

# Reserved token patterns (id_generation_rules.md §8)
RESERVED_PATTERNS = [
    re.compile(r"^(.)\1+$"),        # all same character
    re.compile(r"^test"),
    re.compile(r"^demo"),
    re.compile(r"^null"),
    re.compile(r"^none"),
]

# Maximum collision retry count (id_generation_rules.md §7)
MAX_ID_RETRIES = 3

# WGS84 constants (from derive.py)
WGS84_A = 6378137.0
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = 2.0 * WGS84_F - WGS84_F ** 2

# Mean Earth radius for edge length approximation
MEAN_EARTH_RADIUS = 6371000.0

logger = logging.getLogger("harmony.registry")


# ---------------------------------------------------------------------------
# Connection Management
# ---------------------------------------------------------------------------

def get_connection():
    """
    Create a new database connection from the HARMONY_DB_URL environment
    variable. Returns a psycopg2 connection with autocommit disabled.

    The connection string format is a standard PostgreSQL URI:
        postgresql://user:password@host:port/dbname

    Raises
    ------
    RuntimeError
        If HARMONY_DB_URL is not set.
    psycopg2.Error
        If the connection fails.
    """
    db_url = os.environ.get("HARMONY_DB_URL")
    if not db_url:
        raise RuntimeError(
            "HARMONY_DB_URL environment variable is not set. "
            "Expected format: postgresql://user:password@host:port/dbname"
        )
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    return conn


# ---------------------------------------------------------------------------
# Token Generation
# ---------------------------------------------------------------------------

def _generate_token(length: int) -> str:
    """
    Generate a random token of the specified length using the Crockford
    Base32 alphabet and a CSPRNG source (secrets module).

    Rejects reserved tokens (id_generation_rules.md §8).
    """
    while True:
        raw = secrets.token_bytes(length)
        token = ""
        for byte in raw:
            token += CROCKFORD_ALPHABET[byte % 32]
        token = token[:length]

        # Check against reserved patterns
        is_reserved = any(p.match(token) for p in RESERVED_PATTERNS)
        if not is_reserved:
            return token


def generate_cell_id() -> str:
    """Generate a new cell canonical ID: hc_ + 9-char token."""
    return "hc_" + _generate_token(9)


def generate_entity_id(subtype: str) -> str:
    """Generate a new entity canonical ID: ent_{subtype}_ + 6-char token."""
    if not re.match(r"^[a-z]{3}$", subtype):
        raise ValueError(
            "Entity subtype must be exactly 3 lowercase letters, got "
            + repr(subtype)
        )
    return "ent_" + subtype + "_" + _generate_token(6)


def generate_alias_id() -> str:
    """Generate a new alias ID: al_ + 9-char token."""
    return "al_" + _generate_token(9)


# ---------------------------------------------------------------------------
# Spatial Geometry Helpers
# ---------------------------------------------------------------------------

def compute_cell_geometry(cube_face: int, resolution_level: int,
                          face_grid_u: int, face_grid_v: int) -> dict:
    """
    Compute derived spatial geometry fields for a cell given its grid
    position.

    Returns a dict with: edge_length_m, area_m2, distortion_factor,
    centroid_lat, centroid_lon, centroid_ecef_x/y/z, and the UV centre
    coordinates.

    This function duplicates some logic from derive.py but operates from
    grid indices rather than lat/lon. The two paths must produce consistent
    centroids — this is a testable invariant.
    """
    grid_n = 4 ** resolution_level

    # Compute UV centre of the grid cell
    if grid_n == 1:
        u_c = 0.0
        v_c = 0.0
    else:
        u_c = (2.0 * face_grid_u + 1.0) / grid_n - 1.0
        v_c = (2.0 * face_grid_v + 1.0) / grid_n - 1.0

    # Distortion factor: sqrt(1 + u^2 + v^2) (gnomonic projection)
    distortion_factor = math.sqrt(1.0 + u_c * u_c + v_c * v_c)

    # Edge length approximation:
    # Base edge at face centre = R * 2 / 4^r
    # Actual edge ≈ base_edge * distortion_factor
    base_edge = MEAN_EARTH_RADIUS * 2.0 / grid_n if grid_n > 0 else MEAN_EARTH_RADIUS * 2.0
    edge_length_m = base_edge * distortion_factor

    # Area approximation: edge^2 (assuming roughly square cell)
    area_m2 = edge_length_m * edge_length_m

    # Inverse-project (face, u_c, v_c) to unit-sphere direction
    _face_to_dir = [
        lambda u, v: (1.0, u, v),       # Face 0 (+X)
        lambda u, v: (-1.0, u, v),      # Face 1 (-X)
        lambda u, v: (u, 1.0, v),       # Face 2 (+Y)
        lambda u, v: (u, -1.0, v),      # Face 3 (-Y)
        lambda u, v: (u, v, 1.0),       # Face 4 (+Z)
        lambda u, v: (u, v, -1.0),      # Face 5 (-Z)
    ]

    dx, dy, dz = _face_to_dir[cube_face](u_c, v_c)
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    nx, ny, nz = dx / norm, dy / norm, dz / norm

    # Direction to geodetic coordinates
    centroid_lon = math.atan2(ny, nx)
    geocentric_lat = math.asin(max(-1.0, min(1.0, nz)))

    # Geocentric to geodetic latitude correction
    if abs(geocentric_lat) < math.pi / 2 - 1e-10:
        geodetic_lat = math.atan2(math.tan(geocentric_lat), (1.0 - WGS84_E2))
    else:
        geodetic_lat = geocentric_lat

    # Geodetic to ECEF (altitude = 0)
    sin_lat = math.sin(geodetic_lat)
    cos_lat = math.cos(geodetic_lat)
    sin_lon = math.sin(centroid_lon)
    cos_lon = math.cos(centroid_lon)

    n_prime = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat ** 2)

    cx = n_prime * cos_lat * cos_lon
    cy = n_prime * cos_lat * sin_lon
    cz = n_prime * (1.0 - WGS84_E2) * sin_lat

    return {
        "edge_length_m": edge_length_m,
        "area_m2": area_m2,
        "distortion_factor": distortion_factor,
        "centroid_ecef_x": cx,
        "centroid_ecef_y": cy,
        "centroid_ecef_z": cz,
        "centroid_lat": math.degrees(geodetic_lat),
        "centroid_lon": math.degrees(centroid_lon),
        "u_center": u_c,
        "v_center": v_c,
    }


# ---------------------------------------------------------------------------
# Adjacency Computation
# ---------------------------------------------------------------------------

# Boundary transition table from cell_adjacency_spec.md §3.2
# Key: (source_face, edge_direction)
# Value: (dest_face, i_mapping, j_mapping)
# Mappings: 'i' = source i, 'j' = source j, 'N' = max index, '0' = 0
BOUNDARY_TABLE = {
    (0, "+u"): (2, "N", "j"),
    (0, "-u"): (3, "N", "j"),
    (0, "+v"): (4, "N", "i"),
    (0, "-v"): (5, "N", "i"),
    (1, "+u"): (2, "0", "j"),
    (1, "-u"): (3, "0", "j"),
    (1, "+v"): (4, "0", "i"),
    (1, "-v"): (5, "0", "i"),
    (2, "+u"): (0, "N", "j"),
    (2, "-u"): (1, "N", "j"),
    (2, "+v"): (4, "i", "N"),
    (2, "-v"): (5, "i", "N"),
    (3, "+u"): (0, "0", "j"),
    (3, "-u"): (1, "0", "j"),
    (3, "+v"): (4, "i", "0"),
    (3, "-v"): (5, "i", "0"),
    (4, "+u"): (0, "j", "N"),
    (4, "-u"): (1, "j", "N"),
    (4, "+v"): (2, "i", "N"),
    (4, "-v"): (3, "i", "N"),
    (5, "+u"): (0, "j", "0"),
    (5, "-u"): (1, "j", "0"),
    (5, "+v"): (2, "i", "0"),
    (5, "-v"): (3, "i", "0"),
}


def _resolve_mapping(mapping: str, i: int, j: int, n_max: int) -> int:
    """Resolve a boundary table mapping code to a grid index."""
    if mapping == "i":
        return i
    elif mapping == "j":
        return j
    elif mapping == "N":
        return n_max
    elif mapping == "0":
        return 0
    else:
        raise ValueError("Unknown mapping code: " + repr(mapping))


def get_edge_neighbour(
    face: int, resolution: int, i: int, j: int, direction: str
) -> tuple:
    """
    Compute the edge neighbour of a cell in the given direction.

    Parameters
    ----------
    face : int
        Cube face index (0-5).
    resolution : int
        Resolution level (0-12).
    i, j : int
        Grid position on the face.
    direction : str
        One of '+u', '-u', '+v', '-v'.

    Returns
    -------
    tuple of (int, int, int)
        (dest_face, dest_i, dest_j) of the neighbour cell.
    """
    n_max = 4 ** resolution - 1

    # Compute candidate position
    if direction == "+u":
        ni, nj = i + 1, j
    elif direction == "-u":
        ni, nj = i - 1, j
    elif direction == "+v":
        ni, nj = i, j + 1
    elif direction == "-v":
        ni, nj = i, j - 1
    else:
        raise ValueError("Invalid direction: " + repr(direction))

    # Check if within face bounds
    if 0 <= ni <= n_max and 0 <= nj <= n_max:
        return (face, ni, nj)

    # Cross face boundary
    key = (face, direction)
    if key not in BOUNDARY_TABLE:
        raise ValueError(
            "No boundary transition for face=" + str(face)
            + " direction=" + direction
        )

    dest_face, i_map, j_map = BOUNDARY_TABLE[key]
    dest_i = _resolve_mapping(i_map, i, j, n_max)
    dest_j = _resolve_mapping(j_map, i, j, n_max)

    return (dest_face, dest_i, dest_j)


def compute_adjacent_cell_keys(
    face: int, resolution: int, i: int, j: int, region_code: str
) -> list:
    """
    Compute the 4 edge-adjacent cell keys for a cell.

    Uses the boundary transition table for inter-face adjacency and
    the derive module for cell_key computation.

    Parameters
    ----------
    face, resolution, i, j : int
        Cell address tuple.
    region_code : str
        Region code for cell_key derivation.

    Returns
    -------
    list of str
        4 cell_keys in order [+u, -u, +v, -v].
    """
    # Import here to avoid circular imports
    import sys
    import importlib

    # The derive module path depends on the deployment
    # Try to import from the cell-key package
    try:
        from harmony.packages.cellkey.src.derive import derive_cell_key
    except ImportError:
        # Fallback: try relative import or sys.path manipulation
        # In the Harmony package structure, derive.py is at:
        # harmony/packages/cell-key/src/derive.py
        _derive_module = None
        for path_candidate in sys.path:
            try:
                spec = importlib.util.spec_from_file_location(
                    "derive",
                    os.path.join(path_candidate, "derive.py")
                )
                if spec and spec.loader:
                    _derive_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(_derive_module)
                    break
            except (FileNotFoundError, AttributeError):
                continue

        if _derive_module is None:
            raise ImportError(
                "Cannot import derive module. Ensure harmony/packages/"
                "cell-key/src/ is on sys.path or PYTHONPATH."
            )
        derive_cell_key = _derive_module.derive_cell_key

    directions = ["+u", "-u", "+v", "-v"]
    adjacent_keys = []

    for direction in directions:
        dest_face, dest_i, dest_j = get_edge_neighbour(
            face, resolution, i, j, direction
        )
        # Compute the neighbour's centroid geodetic coordinates
        geo = compute_cell_geometry(dest_face, resolution, dest_i, dest_j)
        # Derive the cell_key from the centroid
        key = derive_cell_key(
            geo["centroid_lat"], geo["centroid_lon"],
            resolution, region_code
        )
        adjacent_keys.append(key)

    return adjacent_keys


def get_adjacency_ring(
    face: int, resolution: int, i: int, j: int,
    ring_order: int, region_code: str
) -> list:
    """
    Compute the adjacency ring of the specified order around a cell.

    Parameters
    ----------
    face, resolution, i, j : int
        Cell address tuple.
    ring_order : int
        Ring order (k). Must be >= 1.
    region_code : str
        Region code for cell_key derivation.

    Returns
    -------
    list of dict
        Each dict has: face, i, j, cell_key.
    """
    if ring_order < 1:
        raise ValueError("Ring order must be >= 1, got " + str(ring_order))

    ring = []
    for di in range(-ring_order, ring_order + 1):
        for dj in range(-ring_order, ring_order + 1):
            if max(abs(di), abs(dj)) != ring_order:
                continue
            dest = _resolve_neighbour_offset(face, resolution, i, j, di, dj)
            if dest is not None:
                ring.append(dest)

    # Derive cell_keys for ring members
    try:
        from harmony.packages.cellkey.src.derive import derive_cell_key
    except ImportError:
        import sys
        import importlib
        _derive_module = None
        for path_candidate in sys.path:
            try:
                spec = importlib.util.spec_from_file_location(
                    "derive",
                    os.path.join(path_candidate, "derive.py")
                )
                if spec and spec.loader:
                    _derive_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(_derive_module)
                    break
            except (FileNotFoundError, AttributeError):
                continue
        if _derive_module:
            derive_cell_key = _derive_module.derive_cell_key
        else:
            derive_cell_key = None

    results = []
    for dest_face, dest_i, dest_j in ring:
        geo = compute_cell_geometry(dest_face, resolution, dest_i, dest_j)
        cell_key = None
        if derive_cell_key:
            cell_key = derive_cell_key(
                geo["centroid_lat"], geo["centroid_lon"],
                resolution, region_code
            )
        results.append({
            "face": dest_face,
            "i": dest_i,
            "j": dest_j,
            "cell_key": cell_key,
        })

    return results


def _resolve_neighbour_offset(
    face: int, resolution: int, i: int, j: int, di: int, dj: int
) -> Optional[tuple]:
    """
    Resolve a grid offset (di, dj) from a cell, handling face boundary
    crossings. Returns (dest_face, dest_i, dest_j) or None if the
    offset cannot be resolved (should not happen for valid inputs).
    """
    n_max = 4 ** resolution - 1
    ni = i + di
    nj = j + dj

    # Simple case: both in bounds
    if 0 <= ni <= n_max and 0 <= nj <= n_max:
        return (face, ni, nj)

    # Step through the offset one cell at a time
    current_face = face
    current_i = i
    current_j = j

    # Resolve u-axis offset
    remaining_u = di
    while remaining_u != 0:
        step = 1 if remaining_u > 0 else -1
        direction = "+u" if step > 0 else "-u"
        dest_face, dest_i, dest_j = get_edge_neighbour(
            current_face, resolution, current_i, current_j, direction
        )
        current_face = dest_face
        current_i = dest_i
        current_j = dest_j
        remaining_u -= step

    # Resolve v-axis offset from the u-resolved position
    remaining_v = dj
    while remaining_v != 0:
        step = 1 if remaining_v > 0 else -1
        direction = "+v" if step > 0 else "-v"
        dest_face, dest_i, dest_j = get_edge_neighbour(
            current_face, resolution, current_i, current_j, direction
        )
        current_face = dest_face
        current_i = dest_i
        current_j = dest_j
        remaining_v -= step

    return (current_face, current_i, current_j)


# ---------------------------------------------------------------------------
# Registry Operations
# ---------------------------------------------------------------------------

def register_cell(
    conn,
    cell_key: str,
    resolution_level: int,
    cube_face: int,
    face_grid_u: int,
    face_grid_v: int,
    region_code: str,
    parent_cell_id: Optional[str] = None,
    human_alias: Optional[str] = None,
    alias_namespace: Optional[str] = None,
    auto_alias_namespace: Optional[str] = None,
    friendly_name: Optional[str] = None,
    semantic_labels: Optional[list] = None,
) -> dict:
    """
    Register a cell in the Identity Registry. Idempotent — if a cell
    with the same cell_key already exists, returns the existing record
    without modification.

    Parameters
    ----------
    conn : psycopg2 connection
        Database connection.
    cell_key : str
        Deterministic cell key (from derive_cell_key).
    resolution_level : int
        Resolution level 0-12.
    cube_face : int
        Cube face index 0-5.
    face_grid_u, face_grid_v : int
        Grid position on the face.
    region_code : str
        Region code for adjacency computation.
    parent_cell_id : str, optional
        Canonical ID of the parent cell.
    human_alias : str, optional
        Manual alias (e.g. 'CC-421'). Requires alias_namespace.
    alias_namespace : str, optional
        Namespace for manual alias.
    auto_alias_namespace : str, optional
        If provided, auto-generate an alias in this namespace using
        the per-namespace counter (alias_namespace_rules.md §9).
        Mutually exclusive with human_alias.
    friendly_name : str, optional
        Human-readable descriptive name.
    semantic_labels : list of str, optional
        Semantic classification labels.

    Returns
    -------
    dict
        The cell record including canonical_id, cell_key, and all metadata.

    Raises
    ------
    ValueError
        If input validation fails.
    psycopg2.Error
        If a database error occurs.
    """
    # Validate inputs
    if not PATTERNS["cell_key"].match(cell_key):
        raise ValueError("Invalid cell_key format: " + repr(cell_key))
    if not (0 <= resolution_level <= 12):
        raise ValueError("Resolution must be 0-12, got " + str(resolution_level))
    if not (0 <= cube_face <= 5):
        raise ValueError("Cube face must be 0-5, got " + str(cube_face))

    grid_max = 4 ** resolution_level - 1
    if not (0 <= face_grid_u <= grid_max):
        raise ValueError(
            "face_grid_u must be 0-" + str(grid_max) + ", got " + str(face_grid_u)
        )
    if not (0 <= face_grid_v <= grid_max):
        raise ValueError(
            "face_grid_v must be 0-" + str(grid_max) + ", got " + str(face_grid_v)
        )

    # Check for existing cell_key (idempotent registration)
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            "SELECT cell_id, cell_key FROM cell_metadata WHERE cell_key = %s",
            (cell_key,)
        )
        existing = cur.fetchone()
        if existing:
            logger.info(
                "Cell already registered: cell_key=%s cell_id=%s",
                cell_key, existing["cell_id"]
            )
            # Fetch full record
            return _fetch_cell_record(cur, existing["cell_id"])

    # Compute spatial geometry
    geo = compute_cell_geometry(cube_face, resolution_level, face_grid_u, face_grid_v)

    # Compute adjacency
    adjacent_keys = compute_adjacent_cell_keys(
        cube_face, resolution_level, face_grid_u, face_grid_v, region_code
    )

    # Generate canonical ID with collision handling
    canonical_id = None
    for attempt in range(MAX_ID_RETRIES):
        candidate = generate_cell_id()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM identity_registry WHERE canonical_id = %s",
                (candidate,)
            )
            if cur.fetchone() is None:
                canonical_id = candidate
                break
        logger.warning("Cell ID collision on attempt %d: %s", attempt + 1, candidate)

    if canonical_id is None:
        raise RuntimeError(
            "Failed to generate unique cell ID after "
            + str(MAX_ID_RETRIES) + " attempts. System error."
        )

    now = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        # Insert into identity_registry
        cur.execute(
            """
            INSERT INTO identity_registry
                (canonical_id, object_type, object_domain, status,
                 schema_version, created_at, updated_at)
            VALUES (%s, 'cell', 'spatial.substrate.cell', 'active',
                    %s, %s, %s)
            """,
            (canonical_id, SCHEMA_VERSION, now, now)
        )

        # Insert into cell_metadata
        cur.execute(
            """
            INSERT INTO cell_metadata
                (cell_id, cell_key, resolution_level, parent_cell_id,
                 cube_face, face_grid_u, face_grid_v,
                 edge_length_m, area_m2, distortion_factor,
                 centroid_ecef_x, centroid_ecef_y, centroid_ecef_z,
                 centroid_lat, centroid_lon,
                 adjacent_cell_keys,
                 human_alias, alias_namespace, friendly_name,
                 semantic_labels)
            VALUES (%s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s,
                    %s, %s, %s,
                    %s)
            """,
            (canonical_id, cell_key, resolution_level, parent_cell_id,
             cube_face, face_grid_u, face_grid_v,
             geo["edge_length_m"], geo["area_m2"], geo["distortion_factor"],
             geo["centroid_ecef_x"], geo["centroid_ecef_y"], geo["centroid_ecef_z"],
             geo["centroid_lat"], geo["centroid_lon"],
             adjacent_keys,
             human_alias, alias_namespace, friendly_name,
             semantic_labels or [])
        )

        # Alias handling: manual alias, auto-alias, or neither
        # Uses alias_service for proper lifecycle and counter management.
        bound_alias = None
        bound_namespace = None

        if human_alias and alias_namespace:
            # Manual alias binding via alias_table
            alias_id = generate_alias_id()
            normalised_alias = human_alias.upper()
            cur.execute(
                """
                INSERT INTO alias_table
                    (alias_id, alias, alias_namespace, canonical_id,
                     status, effective_from)
                VALUES (%s, %s, %s, %s, 'active', %s)
                """,
                (alias_id, normalised_alias, alias_namespace, canonical_id, now)
            )
            bound_alias = normalised_alias
            bound_namespace = alias_namespace
        elif auto_alias_namespace:
            # Auto-generate via namespace counter
            # Import alias_service for auto_generate_alias
            try:
                from harmony.packages.alias.src.alias_service import (
                    auto_generate_alias, _generate_alias_id as gen_aid
                )
                generated = auto_generate_alias(conn, auto_alias_namespace)
                aid = gen_aid()
                cur.execute(
                    """
                    INSERT INTO alias_table
                        (alias_id, alias, alias_namespace, canonical_id,
                         status, effective_from)
                    VALUES (%s, %s, %s, %s, 'active', %s)
                    """,
                    (aid, generated, auto_alias_namespace, canonical_id, now)
                )
                bound_alias = generated
                bound_namespace = auto_alias_namespace
            except ImportError:
                logger.warning(
                    "alias_service not available — skipping auto-alias for %s",
                    canonical_id
                )

        # Update cell_metadata with the alias if one was bound
        if bound_alias:
            cur.execute(
                """
                UPDATE cell_metadata
                SET human_alias = %s, alias_namespace = %s
                WHERE cell_id = %s
                """,
                (bound_alias, bound_namespace, canonical_id)
            )

    conn.commit()

    logger.info("Registered cell: cell_id=%s cell_key=%s", canonical_id, cell_key)

    return {
        "canonical_id": canonical_id,
        "cell_key": cell_key,
        "resolution_level": resolution_level,
        "cube_face": cube_face,
        "face_grid_u": face_grid_u,
        "face_grid_v": face_grid_v,
        "edge_length_m": geo["edge_length_m"],
        "area_m2": geo["area_m2"],
        "distortion_factor": geo["distortion_factor"],
        "centroid_ecef": {
            "x": geo["centroid_ecef_x"],
            "y": geo["centroid_ecef_y"],
            "z": geo["centroid_ecef_z"],
        },
        "centroid_geodetic": {
            "latitude": geo["centroid_lat"],
            "longitude": geo["centroid_lon"],
        },
        "adjacent_cell_keys": adjacent_keys,
        "parent_cell_id": parent_cell_id,
        "human_alias": bound_alias or human_alias,
        "alias_namespace": bound_namespace or alias_namespace,
        "friendly_name": friendly_name,
        "semantic_labels": semantic_labels or [],
        "status": "active",
        "schema_version": SCHEMA_VERSION,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


def register_entity(
    conn,
    entity_subtype: str,
    primary_cell_id: str,
    metadata: Optional[dict] = None,
    secondary_cell_ids: Optional[list] = None,
    human_alias: Optional[str] = None,
    alias_namespace: Optional[str] = None,
    auto_alias_namespace: Optional[str] = None,
    friendly_name: Optional[str] = None,
    semantic_labels: Optional[list] = None,
) -> dict:
    """
    Register an entity in the Identity Registry.

    Entity IDs are NOT idempotent against content. The same building
    registered twice produces two entity IDs. Deduplication is the
    responsibility of the ingestion pipeline (Pillar 2).

    Parameters
    ----------
    conn : psycopg2 connection
    entity_subtype : str
        3-letter subtype code (e.g., 'bld' for building).
    primary_cell_id : str
        Canonical ID of the primary cell this entity is anchored to.
    metadata : dict, optional
        Arbitrary metadata as JSONB.
    secondary_cell_ids : list of str, optional
        Additional cells this entity spans.
    human_alias, alias_namespace, friendly_name : str, optional
    semantic_labels : list of str, optional

    Returns
    -------
    dict
        The entity record including entity_id.
    """
    if not re.match(r"^[a-z]{3}$", entity_subtype):
        raise ValueError(
            "Entity subtype must be exactly 3 lowercase letters, got "
            + repr(entity_subtype)
        )
    if not PATTERNS["cell"].match(primary_cell_id):
        raise ValueError("Invalid primary_cell_id format: " + repr(primary_cell_id))

    # Verify primary cell exists
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM cell_metadata WHERE cell_id = %s",
            (primary_cell_id,)
        )
        if cur.fetchone() is None:
            raise ValueError(
                "Primary cell not found in registry: " + primary_cell_id
            )

    # Generate entity ID with collision handling
    entity_id = None
    for attempt in range(MAX_ID_RETRIES):
        candidate = generate_entity_id(entity_subtype)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM identity_registry WHERE canonical_id = %s",
                (candidate,)
            )
            if cur.fetchone() is None:
                entity_id = candidate
                break
        logger.warning(
            "Entity ID collision on attempt %d: %s", attempt + 1, candidate
        )

    if entity_id is None:
        raise RuntimeError(
            "Failed to generate unique entity ID after "
            + str(MAX_ID_RETRIES) + " attempts."
        )

    now = datetime.now(timezone.utc)
    domain = "spatial.substrate.entity." + entity_subtype

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO identity_registry
                (canonical_id, object_type, object_domain, status,
                 schema_version, created_at, updated_at)
            VALUES (%s, 'entity', %s, 'active', %s, %s, %s)
            """,
            (entity_id, domain, SCHEMA_VERSION, now, now)
        )

        cur.execute(
            """
            INSERT INTO entity_table
                (entity_id, entity_subtype, primary_cell_id,
                 secondary_cell_ids, metadata,
                 human_alias, alias_namespace, friendly_name,
                 known_names, semantic_labels)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (entity_id, entity_subtype, primary_cell_id,
             secondary_cell_ids or [], psycopg2.extras.Json(metadata or {}),
             human_alias, alias_namespace, friendly_name,
             [], semantic_labels or [])
        )

        # Alias handling: manual, auto, or neither
        bound_alias = None
        bound_namespace = None

        if human_alias and alias_namespace:
            alias_id = generate_alias_id()
            normalised_alias = human_alias.upper()
            cur.execute(
                """
                INSERT INTO alias_table
                    (alias_id, alias, alias_namespace, canonical_id,
                     status, effective_from)
                VALUES (%s, %s, %s, %s, 'active', %s)
                """,
                (alias_id, normalised_alias, alias_namespace, entity_id, now)
            )
            bound_alias = normalised_alias
            bound_namespace = alias_namespace
        elif auto_alias_namespace:
            try:
                from harmony.packages.alias.src.alias_service import (
                    auto_generate_alias, _generate_alias_id as gen_aid
                )
                generated = auto_generate_alias(conn, auto_alias_namespace)
                aid = gen_aid()
                cur.execute(
                    """
                    INSERT INTO alias_table
                        (alias_id, alias, alias_namespace, canonical_id,
                         status, effective_from)
                    VALUES (%s, %s, %s, %s, 'active', %s)
                    """,
                    (aid, generated, auto_alias_namespace, entity_id, now)
                )
                bound_alias = generated
                bound_namespace = auto_alias_namespace
            except ImportError:
                logger.warning(
                    "alias_service not available — skipping auto-alias for %s",
                    entity_id
                )

        if bound_alias:
            cur.execute(
                """
                UPDATE entity_table
                SET human_alias = %s, alias_namespace = %s
                WHERE entity_id = %s
                """,
                (bound_alias, bound_namespace, entity_id)
            )

    conn.commit()

    logger.info("Registered entity: entity_id=%s subtype=%s", entity_id, entity_subtype)

    return {
        "entity_id": entity_id,
        "entity_subtype": entity_subtype,
        "primary_cell_id": primary_cell_id,
        "secondary_cell_ids": secondary_cell_ids or [],
        "metadata": metadata or {},
        "human_alias": bound_alias or human_alias,
        "alias_namespace": bound_namespace or alias_namespace,
        "friendly_name": friendly_name,
        "semantic_labels": semantic_labels or [],
        "status": "active",
        "schema_version": SCHEMA_VERSION,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


# ---------------------------------------------------------------------------
# Resolution Operations
# ---------------------------------------------------------------------------

def resolve_canonical(conn, canonical_id: str) -> Optional[dict]:
    """
    Resolve a canonical ID to its full record.

    Returns the complete identity + metadata record, or None if not found.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Get identity record
        cur.execute(
            "SELECT * FROM identity_registry WHERE canonical_id = %s",
            (canonical_id,)
        )
        identity = cur.fetchone()
        if identity is None:
            return None

        result = dict(identity)

        # Fetch type-specific metadata
        if identity["object_type"] == "cell":
            result["cell_metadata"] = _fetch_cell_record(cur, canonical_id)
        elif identity["object_type"] == "entity":
            cur.execute(
                "SELECT * FROM entity_table WHERE entity_id = %s",
                (canonical_id,)
            )
            entity = cur.fetchone()
            if entity:
                result["entity_metadata"] = dict(entity)

        return result


def resolve_alias(
    conn, alias: str, namespace: str
) -> Optional[dict]:
    """
    Resolve a human alias to its canonical record.

    Parameters
    ----------
    conn : psycopg2 connection
    alias : str
        The human alias (e.g., "CC-421").
    namespace : str
        The alias namespace.

    Returns
    -------
    dict or None
        The resolved identity record, or None if the alias is not found
        or not active.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """
            SELECT canonical_id FROM alias_table
            WHERE alias = %s AND alias_namespace = %s AND status = 'active'
            ORDER BY effective_from DESC
            LIMIT 1
            """,
            (alias, namespace)
        )
        row = cur.fetchone()
        if row is None:
            return None

        return resolve_canonical(conn, row["canonical_id"])


def resolve_cell_key(conn, cell_key: str) -> Optional[dict]:
    """
    Resolve a cell_key to its full record.

    This is the primary lookup path for spatial operations — given
    a deterministically derived cell_key, find the registered cell.
    """
    if not PATTERNS["cell_key"].match(cell_key):
        raise ValueError("Invalid cell_key format: " + repr(cell_key))

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            "SELECT cell_id FROM cell_metadata WHERE cell_key = %s",
            (cell_key,)
        )
        row = cur.fetchone()
        if row is None:
            return None

        return resolve_canonical(conn, row["cell_id"])


def _fetch_cell_record(cur, cell_id: str) -> dict:
    """Fetch the complete cell metadata record."""
    cur.execute(
        "SELECT * FROM cell_metadata WHERE cell_id = %s",
        (cell_id,)
    )
    row = cur.fetchone()
    if row is None:
        return {}
    return dict(row)


# ---------------------------------------------------------------------------
# Query Operations
# ---------------------------------------------------------------------------

def get_cells_by_resolution(
    conn, resolution_level: int, limit: int = 100, offset: int = 0
) -> list:
    """
    Retrieve cells at a specific resolution level.

    Returns a list of cell records, ordered by cell_key.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """
            SELECT * FROM cell_metadata
            WHERE resolution_level = %s
            ORDER BY cell_key
            LIMIT %s OFFSET %s
            """,
            (resolution_level, limit, offset)
        )
        return [dict(row) for row in cur.fetchall()]


def get_children(conn, parent_cell_id: str) -> list:
    """
    Retrieve all child cells of a given parent.

    Returns up to 16 cell records (the children at resolution + 1).
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """
            SELECT * FROM cell_metadata
            WHERE parent_cell_id = %s
            ORDER BY face_grid_u, face_grid_v
            """,
            (parent_cell_id,)
        )
        return [dict(row) for row in cur.fetchall()]


def get_entities_in_cell(conn, cell_id: str) -> list:
    """
    Retrieve all entities anchored to a given cell.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """
            SELECT e.*, ir.status as identity_status
            FROM entity_table e
            JOIN identity_registry ir ON e.entity_id = ir.canonical_id
            WHERE e.primary_cell_id = %s
            ORDER BY e.entity_id
            """,
            (cell_id,)
        )
        return [dict(row) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Volumetric Cell Operations (Stage 2 — ADR-015, ADR-017)
# ---------------------------------------------------------------------------
#
# Volumetric cells represent a specific altitude band on top of a surface
# (Stage 1) cell. Surface cells are unchanged; the discriminator is
# cell_metadata.is_volumetric.
#
# Only functions in this section touch the new altitude / vertical_* columns.
# Stage 1 code paths are untouched and continue to resolve surface cells as
# before.

def _import_volumetric_module():
    """Import the volumetric module from the cell-key package."""
    try:
        import volumetric  # cell-key src on sys.path via _bootstrap
        return volumetric
    except ImportError:
        import sys
        import importlib
        here_candidates = [
            os.path.join(os.path.dirname(__file__), "..", "..",
                         "cell-key", "src", "volumetric.py"),
        ]
        for cand in here_candidates:
            cand = os.path.abspath(cand)
            if os.path.exists(cand):
                spec = importlib.util.spec_from_file_location("volumetric", cand)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                sys.modules["volumetric"] = mod
                return mod
        raise ImportError(
            "Cannot locate volumetric module. Expected at "
            "harmony/packages/cell-key/src/volumetric.py"
        )


def register_volumetric_cell(
    conn,
    surface_cell_id: str,
    altitude_min_m: float,
    altitude_max_m: float,
    vertical_subdivision_level: Optional[int] = None,
    human_alias: Optional[str] = None,
    alias_namespace: Optional[str] = None,
    friendly_name: Optional[str] = None,
    semantic_labels: Optional[list] = None,
) -> dict:
    """
    Register a volumetric (3D) cell as a vertical subdivision of an existing
    surface cell.

    The surface cell must already be registered (Stage 1 semantics). The
    volumetric cell inherits the surface cell's cube face / grid position
    and adds an altitude band with deterministic key derivation.

    Idempotent on (surface_cell_key, alt_min, alt_max): if a volumetric cell
    already exists for the same band, the existing record is returned.

    Parameters
    ----------
    conn : psycopg2 connection
    surface_cell_id : str
        Canonical ID of the parent surface cell (e.g., 'hc_abc123xyz').
    altitude_min_m, altitude_max_m : float
        Band bounds in metres (WGS84 ellipsoid reference). Negative for
        underwater. Validated against ADR-015 §2.5 rules.
    vertical_subdivision_level : int, optional
        Ordinal of this band within the parent surface column. Defaults to
        the count of existing volumetric children plus one.
    human_alias, alias_namespace, friendly_name : str, optional
    semantic_labels : list of str, optional

    Returns
    -------
    dict
        The volumetric cell record. Shape is the Stage 1 cell dict plus:
            is_volumetric, altitude_min_m, altitude_max_m,
            vertical_subdivision_level, vertical_parent_cell_id,
            vertical_adjacent_cell_keys, aviation_domain.

    Raises
    ------
    ValueError
        Invalid surface cell, invalid altitude range, or attempt to
        subdivide a cell that is itself volumetric.
    """
    if not PATTERNS["cell"].match(surface_cell_id):
        raise ValueError(
            "Invalid surface_cell_id format: " + repr(surface_cell_id)
        )

    volumetric = _import_volumetric_module()
    volumetric.validate_altitude_range(altitude_min_m, altitude_max_m)

    # Look up the parent surface cell
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            "SELECT * FROM cell_metadata WHERE cell_id = %s",
            (surface_cell_id,)
        )
        parent = cur.fetchone()
        if parent is None:
            raise ValueError(
                "Parent surface cell not found: " + surface_cell_id
            )
        if parent["is_volumetric"]:
            raise ValueError(
                "Cannot subdivide a volumetric cell (Stage 2 does not "
                "support nested subdivision): " + surface_cell_id
            )

        surface_cell_key = parent["cell_key"]
        # Derive the volumetric key deterministically
        volumetric_key = volumetric.derive_volumetric_cell_key(
            surface_cell_key, altitude_min_m, altitude_max_m
        )

        # Idempotent: does this (surface, band) already exist?
        cur.execute(
            "SELECT cell_id FROM cell_metadata WHERE cell_key = %s",
            (volumetric_key,)
        )
        existing = cur.fetchone()
        if existing:
            logger.info(
                "Volumetric cell already registered: cell_key=%s cell_id=%s",
                volumetric_key, existing["cell_id"]
            )
            return _fetch_volumetric_record(cur, existing["cell_id"])

        # Determine subdivision level if not provided
        if vertical_subdivision_level is None:
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM cell_metadata
                WHERE vertical_parent_cell_id = %s
                """,
                (surface_cell_id,)
            )
            row = cur.fetchone()
            vertical_subdivision_level = (row["n"] if row else 0) + 1

    # Generate canonical ID (same allocation scheme as Stage 1 cells)
    canonical_id = None
    for attempt in range(MAX_ID_RETRIES):
        candidate = generate_cell_id()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM identity_registry WHERE canonical_id = %s",
                (candidate,)
            )
            if cur.fetchone() is None:
                canonical_id = candidate
                break
        logger.warning(
            "Volumetric cell ID collision on attempt %d: %s",
            attempt + 1, candidate
        )
    if canonical_id is None:
        raise RuntimeError(
            "Failed to generate unique volumetric cell ID after "
            + str(MAX_ID_RETRIES) + " attempts."
        )

    now = datetime.now(timezone.utc)

    # Compute vertical adjacency — look up sibling bands in the same column
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Up-neighbour: band whose alt_min equals this cell's alt_max
        cur.execute(
            """
            SELECT cell_key FROM cell_metadata
            WHERE vertical_parent_cell_id = %s
              AND is_volumetric = TRUE
              AND altitude_min_m = %s
            """,
            (surface_cell_id, altitude_max_m)
        )
        up_row = cur.fetchone()
        up_neighbour = up_row["cell_key"] if up_row else None

        # Down-neighbour: band whose alt_max equals this cell's alt_min
        cur.execute(
            """
            SELECT cell_key FROM cell_metadata
            WHERE vertical_parent_cell_id = %s
              AND is_volumetric = TRUE
              AND altitude_max_m = %s
            """,
            (surface_cell_id, altitude_min_m)
        )
        down_row = cur.fetchone()
        down_neighbour = down_row["cell_key"] if down_row else None

        vertical_adjacent = {"up": up_neighbour, "down": down_neighbour}

        # Volumetric cells inherit their surface cell's lateral adjacency.
        # The cell_metadata schema requires adjacent_cell_keys to have
        # exactly 4 entries (Stage 1 invariant). We reuse the parent's
        # lateral neighbours — same cube face, same grid, same band.
        inherited_lateral = list(parent["adjacent_cell_keys"] or [])

        # Insert identity record
        cur.execute(
            """
            INSERT INTO identity_registry
                (canonical_id, object_type, object_domain, status,
                 schema_version, created_at, updated_at)
            VALUES (%s, 'cell', 'spatial.substrate.cell', 'active',
                    %s, %s, %s)
            """,
            (canonical_id, SCHEMA_VERSION, now, now)
        )

        # Volumetric rows inherit the parent's grid position. Migration 003
        # replaces the Stage 1 UNIQUE(grid) constraint with a partial unique
        # index that applies only to surface rows, so multiple volumetric
        # children can share the parent's grid position.
        cur.execute(
            """
            INSERT INTO cell_metadata
                (cell_id, cell_key, resolution_level, parent_cell_id,
                 cube_face, face_grid_u, face_grid_v,
                 edge_length_m, area_m2, distortion_factor,
                 centroid_ecef_x, centroid_ecef_y, centroid_ecef_z,
                 centroid_lat, centroid_lon,
                 adjacent_cell_keys,
                 human_alias, alias_namespace, friendly_name,
                 semantic_labels,
                 is_volumetric, altitude_min_m, altitude_max_m,
                 vertical_subdivision_level, vertical_parent_cell_id,
                 vertical_adjacent_cell_keys)
            VALUES (%s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s,
                    %s, %s, %s,
                    %s,
                    TRUE, %s, %s,
                    %s, %s,
                    %s)
            """,
            (canonical_id, volumetric_key, parent["resolution_level"],
             parent["parent_cell_id"],
             parent["cube_face"], parent["face_grid_u"], parent["face_grid_v"],
             parent["edge_length_m"], parent["area_m2"],
             parent["distortion_factor"],
             parent["centroid_ecef_x"], parent["centroid_ecef_y"],
             parent["centroid_ecef_z"],
             parent["centroid_lat"], parent["centroid_lon"],
             inherited_lateral,
             human_alias, alias_namespace, friendly_name,
             semantic_labels or [],
             altitude_min_m, altitude_max_m,
             vertical_subdivision_level, surface_cell_id,
             psycopg2.extras.Json(vertical_adjacent))
        )

        # Backfill the sibling neighbours' vertical_adjacent_cell_keys so
        # adjacency is bidirectional and precomputed.
        if up_neighbour:
            cur.execute(
                """
                UPDATE cell_metadata
                SET vertical_adjacent_cell_keys =
                    jsonb_set(
                        COALESCE(vertical_adjacent_cell_keys, '{}'::jsonb),
                        '{down}', to_jsonb(%s::text), true
                    )
                WHERE cell_key = %s
                """,
                (volumetric_key, up_neighbour)
            )
        if down_neighbour:
            cur.execute(
                """
                UPDATE cell_metadata
                SET vertical_adjacent_cell_keys =
                    jsonb_set(
                        COALESCE(vertical_adjacent_cell_keys, '{}'::jsonb),
                        '{up}', to_jsonb(%s::text), true
                    )
                WHERE cell_key = %s
                """,
                (volumetric_key, down_neighbour)
            )

    conn.commit()

    logger.info(
        "Registered volumetric cell: cell_id=%s cell_key=%s band=[%s, %s]m",
        canonical_id, volumetric_key, altitude_min_m, altitude_max_m
    )

    return {
        "canonical_id": canonical_id,
        "cell_key": volumetric_key,
        "is_volumetric": True,
        "resolution_level": parent["resolution_level"],
        "cube_face": parent["cube_face"],
        "face_grid_u": parent["face_grid_u"],
        "face_grid_v": parent["face_grid_v"],
        "edge_length_m": parent["edge_length_m"],
        "area_m2": parent["area_m2"],
        "distortion_factor": parent["distortion_factor"],
        "centroid_ecef": {
            "x": parent["centroid_ecef_x"],
            "y": parent["centroid_ecef_y"],
            "z": parent["centroid_ecef_z"],
        },
        "centroid_geodetic": {
            "latitude": parent["centroid_lat"],
            "longitude": parent["centroid_lon"],
        },
        "adjacent_cell_keys": inherited_lateral,
        "vertical_adjacent_cell_keys": vertical_adjacent,
        "altitude_min_m": altitude_min_m,
        "altitude_max_m": altitude_max_m,
        "vertical_subdivision_level": vertical_subdivision_level,
        "vertical_parent_cell_id": surface_cell_id,
        "aviation_domain": volumetric.is_aviation_domain(altitude_max_m),
        "parent_cell_id": parent["parent_cell_id"],
        "human_alias": human_alias,
        "alias_namespace": alias_namespace,
        "friendly_name": friendly_name,
        "semantic_labels": semantic_labels or [],
        "status": "active",
        "schema_version": SCHEMA_VERSION,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


def resolve_vertical_adjacency(conn, cell_key: str) -> Optional[dict]:
    """
    Resolve vertical adjacency for a volumetric cell.

    Returns a dict with lateral (4-entry list) and vertical ({up, down})
    neighbours. Returns None if the cell is not found. Returns {"lateral":
    [...], "vertical": None} if the cell is a surface cell — surface cells
    have no vertical adjacency shape per ADR-015 §2.8.
    """
    if not (PATTERNS["cell_key"].match(cell_key)
            or PATTERNS["volumetric_cell_key"].match(cell_key)):
        raise ValueError("Invalid cell_key format: " + repr(cell_key))

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """
            SELECT cell_id, is_volumetric, adjacent_cell_keys,
                   vertical_adjacent_cell_keys
            FROM cell_metadata
            WHERE cell_key = %s
            """,
            (cell_key,)
        )
        row = cur.fetchone()
        if row is None:
            return None

        lateral = list(row["adjacent_cell_keys"] or [])
        if not row["is_volumetric"]:
            return {"lateral": lateral, "vertical": None}

        vertical = row["vertical_adjacent_cell_keys"] or {"up": None, "down": None}
        return {"lateral": lateral, "vertical": vertical}


def _fetch_volumetric_record(cur, cell_id: str) -> dict:
    """Fetch a full cell row and shape it as a volumetric dict."""
    cur.execute(
        "SELECT * FROM cell_metadata WHERE cell_id = %s",
        (cell_id,)
    )
    row = cur.fetchone()
    if row is None:
        return {}
    record = dict(row)
    # Flatten the synthesised response shape used by register_volumetric_cell
    record["canonical_id"] = record.pop("cell_id")
    record["centroid_ecef"] = {
        "x": record.get("centroid_ecef_x"),
        "y": record.get("centroid_ecef_y"),
        "z": record.get("centroid_ecef_z"),
    }
    record["centroid_geodetic"] = {
        "latitude": record.get("centroid_lat"),
        "longitude": record.get("centroid_lon"),
    }
    record["adjacent_cell_keys"] = list(record.get("adjacent_cell_keys") or [])
    return record
