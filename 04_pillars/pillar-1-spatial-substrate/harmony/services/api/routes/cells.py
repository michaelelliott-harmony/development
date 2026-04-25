# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Cell HTTP Endpoints

import json
import re
from fastapi import APIRouter, Query, Response, status
import psycopg2
import psycopg2.extras

from harmony.services.api import _bootstrap  # noqa: F401 — configures sys.path
import registry  # noqa: E402  (sys.path set up by _bootstrap)

from harmony.services.api.database import get_connection
from harmony.services.api.errors import http_error
from harmony.services.api.models import (
    CellCreate,
    CellResponse,
    AdjacencyRingResponse,
    AdjacencyNode,
    VolumetricCellCreate,
    CellAdjacencyResponse,
    VerticalAdjacency,
    FidelityCoverageUpdate,
)

router = APIRouter(tags=["cells"])


# Extract the region segment (e.g. "cc") from either a surface or volumetric
# cell_key. The surface match stops at the 16-char hash; volumetric keys
# append ":v{alt_min}-{alt_max}" which this regex ignores via the optional
# non-capturing group.
_CELL_KEY_RE = re.compile(
    r"^hsam:r(\d{2}):([a-z]{2,8}):([0-9a-hjkmnp-tv-z]{16})"
    r"(?::v-?[0-9]+\.[0-9]--?[0-9]+\.[0-9])?$"
)


def _parse_region(cell_key: str) -> str:
    match = _CELL_KEY_RE.match(cell_key)
    if not match:
        raise http_error(400, "invalid_cell_key", f"Invalid cell_key format: {cell_key}")
    return match.group(2)


def _shape_cell(record: dict) -> dict:
    """Shape a registry record into the CellResponse schema.

    The registry returns three slightly different shapes:
      1. resolve_canonical() — identity fields at top, cell_metadata nested
      2. register_cell() new record — flat dict with nested centroid_ecef
      3. register_cell() idempotent hit — raw cell_metadata row (cell_id key)
    """
    # Case 1: resolve_canonical envelope
    if "cell_metadata" in record:
        meta = record["cell_metadata"] or {}
        return _flatten_meta(record["canonical_id"], meta, record)

    # Case 3: raw cell_metadata row (has cell_id but no nested centroid_ecef)
    if "cell_id" in record and "centroid_ecef" not in record:
        return _flatten_meta(record["cell_id"], record, record)

    # Case 2: register_cell new record — already in response shape
    return record


def _flatten_meta(canonical_id: str, meta: dict, outer: dict) -> dict:
    # Base Stage 1 shape
    out = {
        "canonical_id": canonical_id,
        "cell_key": meta.get("cell_key"),
        "resolution_level": meta.get("resolution_level"),
        "cube_face": meta.get("cube_face"),
        "face_grid_u": meta.get("face_grid_u"),
        "face_grid_v": meta.get("face_grid_v"),
        "edge_length_m": meta.get("edge_length_m"),
        "area_m2": meta.get("area_m2"),
        "distortion_factor": meta.get("distortion_factor"),
        "centroid_ecef": {
            "x": meta.get("centroid_ecef_x"),
            "y": meta.get("centroid_ecef_y"),
            "z": meta.get("centroid_ecef_z"),
        },
        "centroid_geodetic": {
            "latitude": meta.get("centroid_lat"),
            "longitude": meta.get("centroid_lon"),
        },
        "adjacent_cell_keys": list(meta.get("adjacent_cell_keys") or []),
        "parent_cell_id": meta.get("parent_cell_id"),
        "human_alias": meta.get("human_alias"),
        "alias_namespace": meta.get("alias_namespace"),
        "friendly_name": meta.get("friendly_name"),
        "semantic_labels": list(meta.get("semantic_labels") or []),
        "status": outer.get("status", "active"),
        "schema_version": outer.get("schema_version", "0.2.0"),
        "created_at": _iso(outer.get("created_at")),
        "updated_at": _iso(outer.get("updated_at")),
    }
    # Stage 2 — attach volumetric fields only when the cell is volumetric.
    # Surface cell responses remain exactly Stage 1 shape (ADR-015 §2.8).
    if meta.get("is_volumetric"):
        alt_max = meta.get("altitude_max_m")
        out["is_volumetric"] = True
        out["altitude_min_m"] = meta.get("altitude_min_m")
        out["altitude_max_m"] = alt_max
        out["vertical_subdivision_level"] = meta.get("vertical_subdivision_level")
        out["vertical_parent_cell_id"] = meta.get("vertical_parent_cell_id")
        v_adj = meta.get("vertical_adjacent_cell_keys") or {"up": None, "down": None}
        out["vertical_adjacent_cell_keys"] = v_adj
        out["aviation_domain"] = bool(alt_max is not None and alt_max > 1000.0)
    return out


def _iso(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


@router.post(
    "/cells",
    response_model=CellResponse,
    responses={
        200: {"description": "Cell already exists (idempotent)"},
        201: {"description": "Cell created"},
        400: {"description": "Invalid input"},
    },
    summary="Register a cell",
)
def create_cell(body: CellCreate, response: Response):
    with get_connection() as conn:
        # Idempotent check: does this cell_key already exist?
        with conn.cursor() as cur:
            cur.execute(
                "SELECT cell_id FROM cell_metadata WHERE cell_key = %s",
                (body.cell_key,),
            )
            existed = cur.fetchone() is not None

        try:
            record = registry.register_cell(
                conn,
                cell_key=body.cell_key,
                resolution_level=body.resolution_level,
                cube_face=body.cube_face,
                face_grid_u=body.face_grid_u,
                face_grid_v=body.face_grid_v,
                region_code=body.region_code,
                parent_cell_id=body.parent_cell_id,
                human_alias=body.human_alias,
                alias_namespace=body.alias_namespace,
                friendly_name=body.friendly_name,
                semantic_labels=body.semantic_labels,
            )
        except ValueError as exc:
            raise http_error(400, "invalid_cell", str(exc))
        except psycopg2.Error as exc:
            conn.rollback()
            raise http_error(400, "cell_persistence_error", exc.diag.message_primary if exc.diag else "Database error")

    # register_cell returns the existing record unmodified on collision —
    # we use the pre-check flag to set the response status code.
    response.status_code = status.HTTP_200_OK if existed else status.HTTP_201_CREATED
    return _shape_cell(record)


@router.get(
    "/resolve/cell/{canonical_id}",
    response_model=CellResponse,
    responses={404: {"description": "Cell not found"}},
    summary="Resolve a cell by canonical_id",
)
def resolve_cell(canonical_id: str):
    if not registry.PATTERNS["cell"].match(canonical_id):
        raise http_error(400, "invalid_canonical_id", f"Invalid cell canonical_id: {canonical_id}")

    with get_connection() as conn:
        record = registry.resolve_canonical(conn, canonical_id)
    if record is None or record.get("object_type") != "cell":
        raise http_error(404, "cell_not_found", f"No cell with canonical_id {canonical_id}")
    return _shape_cell(record)


@router.get(
    "/resolve/cell-key/{cell_key}",
    response_model=CellResponse,
    responses={404: {"description": "Cell not found"}, 400: {"description": "Invalid cell_key"}},
    summary="Resolve a cell by cell_key",
)
def resolve_cell_key(cell_key: str):
    if not registry.PATTERNS["cell_key"].match(cell_key):
        raise http_error(400, "invalid_cell_key", f"Invalid cell_key format: {cell_key}")

    with get_connection() as conn:
        try:
            record = registry.resolve_cell_key(conn, cell_key)
        except ValueError as exc:
            raise http_error(400, "invalid_cell_key", str(exc))
    if record is None:
        raise http_error(404, "cell_not_found", f"No cell with cell_key {cell_key}")
    return _shape_cell(record)


@router.get(
    "/cells/{cell_key}/adjacency",
    # Union of Stage 1 ring shape and Stage 2 vertical shape — declared as
    # CellAdjacencyResponse for the volumetric path; Stage 1 ring remains
    # selectable via depth. See ADR-015 §2.8.
    responses={
        400: {"description": "Invalid depth or cell_key"},
        404: {"description": "Cell not found"},
    },
    summary="Query the adjacency of a cell",
)
def adjacency_ring(
    cell_key: str,
    depth: int = Query(1, description="Ring order (1, 2, or 3)"),
):
    # Accept both surface and volumetric cell_keys.
    is_vol = registry.PATTERNS["volumetric_cell_key"].match(cell_key) is not None
    is_surf = registry.PATTERNS["cell_key"].match(cell_key) is not None
    if not (is_vol or is_surf):
        raise http_error(400, "invalid_cell_key", f"Invalid cell_key format: {cell_key}")

    region_code = _parse_region(cell_key)

    with get_connection() as conn:
        # For volumetric keys we go direct to cell_metadata (the Stage 1
        # resolve_cell_key path matches only surface keys).
        if is_vol:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(
                    "SELECT * FROM cell_metadata WHERE cell_key = %s",
                    (cell_key,),
                )
                row = cur.fetchone()
            if row is None:
                raise http_error(404, "cell_not_found",
                                 f"No cell with cell_key {cell_key}")
            meta = dict(row)
        else:
            record = registry.resolve_cell_key(conn, cell_key)
            if record is None:
                raise http_error(404, "cell_not_found",
                                 f"No cell with cell_key {cell_key}")
            meta = record.get("cell_metadata") or {}

    # Volumetric cells: return the Stage 2 shape with lateral + vertical
    # neighbours. Depth is ignored for the vertical axis (only ±1 band).
    if meta.get("is_volumetric"):
        lateral = list(meta.get("adjacent_cell_keys") or [])
        v = meta.get("vertical_adjacent_cell_keys") or {"up": None, "down": None}
        return {
            "cell_key": cell_key,
            "is_volumetric": True,
            "lateral": lateral,
            "vertical": {"up": v.get("up"), "down": v.get("down")},
        }

    # Surface cells: unchanged Stage 1 ring response. No vertical field.
    if depth not in (1, 2, 3):
        raise http_error(400, "invalid_depth", "depth must be 1, 2, or 3")
    try:
        ring = registry.get_adjacency_ring(
            meta["cube_face"],
            meta["resolution_level"],
            meta["face_grid_u"],
            meta["face_grid_v"],
            depth,
            region_code,
        )
    except ValueError as exc:
        raise http_error(400, "adjacency_failed", str(exc))

    return {
        "cell_key": cell_key,
        "depth": depth,
        "ring": [AdjacencyNode(**node) for node in ring],
    }


# -------------------------------------------------------------------------
# Stage 2 — volumetric cell subdivision (ADR-015 §2.8)
# -------------------------------------------------------------------------

@router.post(
    "/cells/volumetric",
    response_model=CellResponse,
    responses={
        201: {"description": "Volumetric cell created"},
        200: {"description": "Volumetric cell already exists (idempotent)"},
        400: {"description": "Invalid input or altitude range"},
        404: {"description": "Parent surface cell not found"},
    },
    summary="Register a volumetric (3D) cell as a vertical subdivision of a surface cell",
)
def create_volumetric_cell(body: VolumetricCellCreate, response: Response):
    with get_connection() as conn:
        # Idempotency pre-check: derive the volumetric key and see if it
        # already exists in cell_metadata.
        import psycopg2 as _psyco
        import psycopg2.extras as _extras
        try:
            import volumetric as _vol
        except ImportError:
            _vol = None

        parent_key = None
        with conn.cursor() as cur:
            cur.execute(
                "SELECT cell_key, is_volumetric FROM cell_metadata WHERE cell_id = %s",
                (body.surface_cell_id,),
            )
            prow = cur.fetchone()
            if prow is None:
                raise http_error(
                    404, "parent_cell_not_found",
                    f"Surface cell not found: {body.surface_cell_id}",
                )
            parent_key, parent_is_vol = prow
            if parent_is_vol:
                raise http_error(
                    400, "invalid_parent",
                    "Cannot subdivide a volumetric cell (no nested subdivision in Stage 2)",
                )

        existed = False
        if _vol is not None:
            try:
                derived = _vol.derive_volumetric_cell_key(
                    parent_key, body.altitude_min_m, body.altitude_max_m
                )
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM cell_metadata WHERE cell_key = %s",
                        (derived,),
                    )
                    existed = cur.fetchone() is not None
            except ValueError:
                # Validation failures surface from register_volumetric_cell
                pass

        try:
            record = registry.register_volumetric_cell(
                conn,
                surface_cell_id=body.surface_cell_id,
                altitude_min_m=body.altitude_min_m,
                altitude_max_m=body.altitude_max_m,
                vertical_subdivision_level=body.vertical_subdivision_level,
                human_alias=body.human_alias,
                alias_namespace=body.alias_namespace,
                friendly_name=body.friendly_name,
                semantic_labels=body.semantic_labels,
            )
        except ValueError as exc:
            raise http_error(400, "invalid_volumetric_cell", str(exc))
        except _psyco.Error as exc:
            conn.rollback()
            raise http_error(
                400, "cell_persistence_error",
                exc.diag.message_primary if exc.diag else "Database error",
            )

    response.status_code = status.HTTP_200_OK if existed else status.HTTP_201_CREATED
    return _shape_cell(record)


# -------------------------------------------------------------------------
# Fidelity coverage update — PATCH /cells/{cell_key}/fidelity
# Dr. Voss Option B: purpose-built, narrow, validated at API + DB layers.
# Full replacement semantics — no merge. Pillar 2 is the primary consumer.
# -------------------------------------------------------------------------

@router.patch(
    "/cells/{cell_key}/fidelity",
    response_model=CellResponse,
    responses={
        200: {"description": "Fidelity coverage updated — full replacement applied"},
        404: {"description": "Cell not found"},
        422: {"description": "Validation failed"},
    },
    summary="Update fidelity coverage for a cell (full replacement)",
)
def update_cell_fidelity(cell_key: str, body: FidelityCoverageUpdate):
    """Replace the fidelity_coverage JSONB field on the cell identified by
    cell_key.  Both structural and photorealistic objects are required.
    Full replacement — calling with the same body twice produces the same
    result (idempotent by construction).
    """
    fidelity_json = json.dumps(body.model_dump())

    with get_connection() as conn:
        # Lookup + update in a single round-trip via RETURNING. JOIN against
        # identity_registry so the response carries status/schema_version/
        # created_at/updated_at without a second query.
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                UPDATE cell_metadata cm
                SET    fidelity_coverage = %s::jsonb
                FROM   identity_registry ir
                WHERE  ir.canonical_id = cm.cell_id
                  AND  cm.cell_key     = %s
                RETURNING
                    cm.*,
                    ir.status,
                    ir.schema_version,
                    ir.created_at,
                    ir.updated_at
                """,
                (fidelity_json, cell_key),
            )
            row = cur.fetchone()

        if row is None:
            raise http_error(404, "cell_not_found", f"No cell with cell_key {cell_key}")

        conn.commit()

    meta = dict(row)
    shaped = _flatten_meta(meta["cell_id"], meta, meta)
    shaped["fidelity_coverage"] = body.model_dump()
    return shaped
