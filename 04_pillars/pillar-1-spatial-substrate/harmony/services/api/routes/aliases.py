# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Alias and Namespace HTTP Endpoints

from typing import Optional

from fastapi import APIRouter, Query, Response, status
import psycopg2

from harmony.services.api import _bootstrap  # noqa: F401
import alias_service  # noqa: E402
from alias_service import (  # noqa: E402
    AliasConflictError,
    AliasNotFoundError,
    NamespaceNotFoundError,
    NamespaceRequiredError,
    InvalidAliasFormatError,
    InvalidNamespaceFormatError,
    ReservedPrefixError,
)

from harmony.services.api.database import get_connection
from harmony.services.api.errors import http_error
from harmony.services.api.models import (
    AliasBindRequest,
    AliasBindResponse,
    AliasResolveResponse,
    AliasRetireRequest,
    AliasRetireResponse,
    NamespaceCreate,
    NamespaceResponse,
)

router = APIRouter(tags=["aliases"])


@router.get(
    "/resolve/alias",
    response_model=AliasResolveResponse,
    responses={
        400: {"description": "namespace query parameter is required"},
        404: {"description": "Alias not found"},
    },
    summary="Resolve an alias within a namespace",
)
def resolve_alias(
    alias: str = Query(..., description="Alias string, case-insensitive"),
    namespace: Optional[str] = Query(
        None,
        description="Fully qualified namespace (required — the service never guesses)",
    ),
    include_retired: bool = Query(False, description="Include retired aliases"),
):
    if namespace is None or namespace == "":
        raise http_error(
            400,
            "namespace_required",
            "Aliases are not unique without a namespace. Provide ?namespace=...",
        )

    with get_connection() as conn:
        try:
            result = alias_service.resolve_alias(
                conn, alias, namespace=namespace, include_retired=include_retired
            )
        except NamespaceRequiredError as exc:
            raise http_error(400, "namespace_required", str(exc))
        except InvalidAliasFormatError as exc:
            raise http_error(400, "invalid_alias_format", str(exc))
        except InvalidNamespaceFormatError as exc:
            raise http_error(400, "invalid_namespace_format", str(exc))
        except AliasNotFoundError as exc:
            raise http_error(404, "alias_not_found", str(exc))
    return result


@router.post(
    "/aliases",
    response_model=AliasBindResponse,
    responses={
        201: {"description": "Alias bound"},
        400: {"description": "Invalid alias or namespace"},
        404: {"description": "Namespace not registered"},
        409: {"description": "Alias already active in this namespace"},
    },
    summary="Bind an alias to a canonical_id",
)
def bind_alias(body: AliasBindRequest, response: Response):
    with get_connection() as conn:
        try:
            result = alias_service.bind_alias(
                conn,
                canonical_id=body.canonical_id,
                alias=body.alias,
                namespace=body.alias_namespace,
            )
        except InvalidAliasFormatError as exc:
            raise http_error(400, "invalid_alias_format", str(exc))
        except InvalidNamespaceFormatError as exc:
            raise http_error(400, "invalid_namespace_format", str(exc))
        except ReservedPrefixError as exc:
            raise http_error(400, "reserved_prefix", str(exc))
        except NamespaceNotFoundError as exc:
            raise http_error(404, "namespace_not_found", str(exc))
        except AliasConflictError as exc:
            raise http_error(409, "alias_conflict", str(exc))
        except psycopg2.Error as exc:
            conn.rollback()
            raise http_error(
                400,
                "alias_persistence_error",
                exc.diag.message_primary if exc.diag else "Database error",
            )

    response.status_code = status.HTTP_201_CREATED
    return result


@router.post(
    "/aliases/retire",
    response_model=AliasRetireResponse,
    responses={
        200: {"description": "Alias retired"},
        404: {"description": "Alias not found or not active"},
    },
    summary="Retire an active alias",
)
def retire_alias(body: AliasRetireRequest):
    with get_connection() as conn:
        try:
            result = alias_service.retire_alias(
                conn, alias=body.alias, namespace=body.alias_namespace
            )
        except InvalidAliasFormatError as exc:
            raise http_error(400, "invalid_alias_format", str(exc))
        except InvalidNamespaceFormatError as exc:
            raise http_error(400, "invalid_namespace_format", str(exc))
        except AliasNotFoundError as exc:
            raise http_error(404, "alias_not_found", str(exc))
    return result


@router.post(
    "/namespaces",
    response_model=NamespaceResponse,
    responses={
        201: {"description": "Namespace registered"},
        400: {"description": "Invalid format"},
        409: {"description": "Namespace already exists"},
    },
    summary="Register a new alias namespace",
)
def register_namespace(body: NamespaceCreate, response: Response):
    with get_connection() as conn:
        try:
            result = alias_service.register_namespace(
                conn,
                namespace=body.namespace,
                prefix=body.prefix,
                initial_counter=body.initial_counter,
            )
        except InvalidNamespaceFormatError as exc:
            raise http_error(400, "invalid_namespace_format", str(exc))
        except ReservedPrefixError as exc:
            raise http_error(400, "reserved_prefix", str(exc))
        except ValueError as exc:
            raise http_error(400, "invalid_namespace", str(exc))
        except AliasConflictError as exc:
            raise http_error(409, "namespace_conflict", str(exc))

    response.status_code = status.HTTP_201_CREATED
    return result
