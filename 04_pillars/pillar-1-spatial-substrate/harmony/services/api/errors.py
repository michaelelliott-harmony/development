# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Consistent HTTP error envelope for the API layer.
#
# Error responses follow: {"error": "<code>", "detail": "<message>"}.
# Internal database state, connection strings, and stack traces are
# never exposed in responses.

from fastapi import HTTPException
from fastapi.responses import JSONResponse


def error_response(status_code: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": code, "detail": detail},
    )


def http_error(status_code: int, code: str, detail: str) -> HTTPException:
    """Build an HTTPException whose detail is the error envelope dict."""
    return HTTPException(
        status_code=status_code,
        detail={"error": code, "detail": detail},
    )
