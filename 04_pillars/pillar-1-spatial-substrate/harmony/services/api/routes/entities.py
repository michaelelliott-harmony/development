# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Entity HTTP Endpoints

from fastapi import APIRouter, Response, status
import psycopg2

from harmony.services.api import _bootstrap  # noqa: F401
import registry  # noqa: E402

from harmony.services.api.database import get_connection
from harmony.services.api.errors import http_error
from harmony.services.api.models import EntityCreate, EntityResponse

router = APIRouter(tags=["entities"])


def _iso(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _shape_entity(record: dict) -> dict:
    """Shape a resolve_canonical() entity record into EntityResponse form."""
    if "entity_metadata" in record:
        meta = record["entity_metadata"] or {}
        canonical_id = record["canonical_id"]
        return {
            "canonical_id": canonical_id,
            "entity_subtype": meta.get("entity_subtype"),
            "primary_cell_id": meta.get("primary_cell_id"),
            "secondary_cell_ids": list(meta.get("secondary_cell_ids") or []),
            "metadata": dict(meta.get("metadata") or {}),
            "human_alias": meta.get("human_alias"),
            "alias_namespace": meta.get("alias_namespace"),
            "friendly_name": meta.get("friendly_name"),
            "semantic_labels": list(meta.get("semantic_labels") or []),
            "status": record.get("status", "active"),
            "schema_version": record.get("schema_version", "0.1.3"),
            "created_at": _iso(record.get("created_at")),
            "updated_at": _iso(record.get("updated_at")),
        }
    # register_entity returns a dict keyed on "entity_id"
    rec = dict(record)
    rec.setdefault("canonical_id", rec.pop("entity_id", None))
    return rec


@router.post(
    "/entities",
    response_model=EntityResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"description": "Invalid input or primary cell missing"}},
    summary="Register an entity",
)
def create_entity(body: EntityCreate, response: Response):
    with get_connection() as conn:
        try:
            record = registry.register_entity(
                conn,
                entity_subtype=body.entity_subtype,
                primary_cell_id=body.primary_cell_id,
                metadata=body.metadata,
                secondary_cell_ids=body.secondary_cell_ids,
                human_alias=body.human_alias,
                alias_namespace=body.alias_namespace,
                friendly_name=body.friendly_name,
                semantic_labels=body.semantic_labels,
            )
        except ValueError as exc:
            conn.rollback()
            raise http_error(400, "invalid_entity", str(exc))
        except psycopg2.Error as exc:
            conn.rollback()
            raise http_error(
                400,
                "entity_persistence_error",
                exc.diag.message_primary if exc.diag else "Database error",
            )

    response.status_code = status.HTTP_201_CREATED
    return _shape_entity(record)


@router.get(
    "/resolve/entity/{canonical_id}",
    response_model=EntityResponse,
    responses={404: {"description": "Entity not found"}},
    summary="Resolve an entity by canonical_id",
)
def resolve_entity(canonical_id: str):
    if not registry.PATTERNS["entity"].match(canonical_id):
        raise http_error(400, "invalid_canonical_id", f"Invalid entity canonical_id: {canonical_id}")

    with get_connection() as conn:
        record = registry.resolve_canonical(conn, canonical_id)
    if record is None or record.get("object_type") != "entity":
        raise http_error(404, "entity_not_found", f"No entity with canonical_id {canonical_id}")
    return _shape_entity(record)
