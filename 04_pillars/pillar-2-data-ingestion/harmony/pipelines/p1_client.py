# Harmony Pillar 2 — Pillar 1 HTTP API Client
#
# Thin wrapper around the Pillar 1 HTTP API.
# This is the ONLY write interface to the Harmony cell registry.
# Never write directly to the database. Never import Pillar 1 modules.
#
# Endpoints used:
#   GET  /health               — confirm Pillar 1 running before any session
#   POST /cells                — idempotent cell registration
#   POST /entities             — entity registration (Pillar 2 owns dedup)
#   POST /aliases              — bind human alias

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

log = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "http://127.0.0.1:8000"
_REQUEST_TIMEOUT = 15
_RETRY_DELAYS = (2, 6, 18)


class Pillar1Error(RuntimeError):
    """Raised when the Pillar 1 API returns an unexpected error."""

    def __init__(self, status_code: int, body: dict | str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"Pillar 1 API error {status_code}: {body}")


class Pillar1Client:
    """HTTP client for the Pillar 1 Identity Registry API.

    Parameters
    ----------
    base_url : str
        Base URL of the Pillar 1 API, e.g. "http://127.0.0.1:8000".
        Defaults to the HARMONY_P1_URL environment variable, then
        "http://127.0.0.1:8000".
    """

    def __init__(self, base_url: str | None = None) -> None:
        self._base = (
            base_url
            or os.environ.get("HARMONY_P1_URL", _DEFAULT_BASE_URL)
        ).rstrip("/")
        self._client = httpx.Client(
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "harmony-pillar2/0.1",
            },
            timeout=_REQUEST_TIMEOUT,
        )

    def health(self) -> dict:
        """GET /health — confirm Pillar 1 is running."""
        resp = self._get("/health")
        return resp

    def register_cell(self, payload: dict) -> tuple[str, bool]:
        """POST /cells — idempotent cell registration.

        Returns
        -------
        (canonical_id, created)
            canonical_id: the cell's canonical ID
            created: True if newly created, False if already existed
        """
        resp, status_code = self._post("/cells", payload)
        canonical_id = resp.get("canonical_id")
        if not canonical_id:
            raise Pillar1Error(200, f"POST /cells returned no canonical_id: {resp}")
        return canonical_id, (status_code == 201)

    def register_entity(self, payload: dict) -> str:
        """POST /entities — entity registration.

        Returns
        -------
        str
            The entity's canonical_id.
        """
        resp, status_code = self._post("/entities", payload)
        canonical_id = resp.get("canonical_id")
        if not canonical_id:
            raise Pillar1Error(201, f"POST /entities returned no canonical_id: {resp}")
        return canonical_id

    def register_alias(self, payload: dict) -> dict:
        """POST /aliases — bind a human alias to a canonical_id."""
        resp, _ = self._post("/aliases", payload)
        return resp

    def patch_cell_fidelity(self, cell_key: str, fidelity_coverage: dict) -> dict:
        """PATCH /cells/{cell_key}/fidelity — set fidelity_coverage on a cell.

        DEC-017: purpose-built PATCH endpoint, full replacement semantics,
        validated at API and database layers. Live in Pillar 1 as of Sprint 1.
        """
        url = self._base + f"/cells/{cell_key}/fidelity"
        last_exc: Exception | None = None
        for attempt, delay in enumerate((*_RETRY_DELAYS, None), start=1):
            try:
                resp = self._client.patch(url, json=fidelity_coverage)
                if resp.status_code in (200, 201):
                    return resp.json()
                try:
                    body = resp.json()
                except Exception:
                    body = resp.text
                raise Pillar1Error(resp.status_code, body)
            except Pillar1Error:
                raise
            except httpx.RequestError as exc:
                last_exc = exc
                if delay is None:
                    break
                log.warning(
                    "P1 PATCH /cells/%s/fidelity attempt %d failed: %s; retry in %ds",
                    cell_key, attempt, exc, delay,
                )
                time.sleep(delay)
        raise Pillar1Error(0, f"PATCH /cells/{cell_key}/fidelity failed after retries: {last_exc}")

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def _get(self, path: str) -> dict:
        url = self._base + path
        last_exc: Exception | None = None
        for attempt, delay in enumerate((*_RETRY_DELAYS, None), start=1):
            try:
                resp = self._client.get(url)
                resp.raise_for_status()
                return resp.json()
            except httpx.RequestError as exc:
                last_exc = exc
                if delay is None:
                    break
                log.warning("P1 GET %s attempt %d failed: %s; retry in %ds", path, attempt, exc, delay)
                time.sleep(delay)
        raise Pillar1Error(0, f"GET {path} failed after retries: {last_exc}")

    def _post(self, path: str, payload: dict) -> tuple[dict, int]:
        url = self._base + path
        last_exc: Exception | None = None
        for attempt, delay in enumerate((*_RETRY_DELAYS, None), start=1):
            try:
                resp = self._client.post(url, json=payload)
                if resp.status_code in (200, 201):
                    return resp.json(), resp.status_code
                # 4xx — do not retry; surface the error
                try:
                    body = resp.json()
                except Exception:
                    body = resp.text
                raise Pillar1Error(resp.status_code, body)
            except Pillar1Error:
                raise
            except httpx.RequestError as exc:
                last_exc = exc
                if delay is None:
                    break
                log.warning("P1 POST %s attempt %d failed: %s; retry in %ds", path, attempt, exc, delay)
                time.sleep(delay)
        raise Pillar1Error(0, f"POST {path} failed after retries: {last_exc}")
