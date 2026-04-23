# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# FastAPI Application — Identity Registry API (Milestone 5)
#
# This is the HTTP contract that all other Harmony pillars consume.
# It exposes the identity registry and alias services as REST endpoints:
#
#     POST /cells, POST /entities, POST /aliases, POST /namespaces
#     GET  /resolve/cell/{id}, /resolve/cell-key/{key}, /resolve/entity/{id}
#     GET  /resolve/alias?alias=...&namespace=...
#     GET  /cells/{cell_key}/adjacency?depth={1|2|3}
#     POST /aliases/retire
#     GET  /health
#
# Authentication is intentionally out of scope for v0.1.3 (see ADR-013).
# The endpoint structure is designed to accept an auth middleware later
# without breaking changes.

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from harmony.services.api import _bootstrap  # noqa: F401 — configures sys.path
from harmony.services.api.database import init_pool, close_pool, check_health
from harmony.services.api.models import HealthResponse
from harmony.services.api.routes import aliases as aliases_routes
from harmony.services.api.routes import cells as cells_routes
from harmony.services.api.routes import entities as entities_routes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("harmony.api")

SCHEMA_VERSION = "0.2.0"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_pool()
    logger.info("Harmony Identity Registry API started (schema v%s)", SCHEMA_VERSION)
    yield
    close_pool()


app = FastAPI(
    title="Harmony Identity Registry API",
    version=SCHEMA_VERSION,
    description=(
        "REST API for the Harmony Spatial Substrate Identity Registry. "
        "Register cells, register entities, manage aliases and namespaces, "
        "and resolve identities by canonical_id, cell_key, or alias. "
        "Every alias resolution call requires a namespace — the service "
        "never guesses (alias_namespace_rules.md §7.4)."
    ),
    lifespan=lifespan,
    openapi_tags=[
        {"name": "cells", "description": "Register and resolve cells; query adjacency rings."},
        {"name": "entities", "description": "Register and resolve entities anchored to cells."},
        {"name": "aliases", "description": "Bind, retire, and resolve aliases. Manage namespaces."},
        {"name": "system", "description": "Health and system information."},
    ],
)

# CORS — permissive for local development; tighten before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------------
# Error handlers — ensure every error response uses the common envelope.
# -------------------------------------------------------------------------

@app.exception_handler(StarletteHTTPException)
async def _http_exception_handler(_request: Request, exc: StarletteHTTPException):
    # If the detail is already our envelope dict, return it directly.
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "detail": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(_request: Request, exc: RequestValidationError):
    # Flatten Pydantic errors into a short human-readable message.
    errs = exc.errors()
    summary = "; ".join(
        f"{'.'.join(str(p) for p in e.get('loc', ()))}: {e.get('msg', '')}".strip()
        for e in errs
    ) or "Invalid request"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "validation_error", "detail": summary},
    )


@app.exception_handler(Exception)
async def _unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "internal_server_error", "detail": "Unexpected server error"},
    )


# -------------------------------------------------------------------------
# Health check
# -------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    db_ok = check_health()
    return {
        "status": "ok" if db_ok else "degraded",
        "schema_version": SCHEMA_VERSION,
        "database": "connected" if db_ok else "unavailable",
    }


# -------------------------------------------------------------------------
# Route registration
# -------------------------------------------------------------------------

app.include_router(cells_routes.router)
app.include_router(entities_routes.router)
app.include_router(aliases_routes.router)
