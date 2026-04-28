# Harmony Pillar 2 — M7 Temporal Trigger Layer
# D6: Fidelity Reset Logic
#
# ADR-016 §2.5 — On change_confirmed:
#   photorealistic.status → pending
#   photorealistic.source → null
#   photorealistic.captured_at → null
#
# The PATCH /cells/{cell_key}/fidelity endpoint is live in Pillar 1 (Sprint 2).
# This module provides the standalone reset function for use both by the
# transition service and by the pipeline runner (M5/M6 pattern).
#
# Writes via Pillar 1 HTTP API only. No direct DB access.

from __future__ import annotations

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_DEFAULT_P1_URL = os.environ.get("HARMONY_P1_URL", "http://localhost:8000")


def build_pending_photorealistic_slot() -> dict:
    """Return the fidelity slot dict for a photorealistic reset.

    Per ADR-016 §2.5: all three fields are nulled/reset on change_confirmed.
    """
    return {
        "status": "pending",
        "source": None,
        "captured_at": None,
    }


def read_current_fidelity(cell_key: str, p1_url: str) -> Optional[dict]:
    """Read the current fidelity_coverage from Pillar 1.

    Returns the fidelity_coverage dict or None if unavailable.
    The PATCH /cells/{cell_key}/fidelity endpoint uses full-replacement
    semantics — we must preserve the structural slot when resetting
    the photorealistic slot.
    """
    try:
        resp = requests.get(
            f"{p1_url.rstrip('/')}/resolve/cell-key/{cell_key}",
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("fidelity_coverage")
    except Exception as exc:
        logger.debug("Could not read fidelity for %s: %s", cell_key, exc)
    return None


def reset_photorealistic_fidelity(
    cell_key: str,
    p1_url: str = _DEFAULT_P1_URL,
    structural_override: Optional[dict] = None,
) -> bool:
    """Reset photorealistic fidelity slot to pending via Pillar 1 PATCH API.

    Reads the current structural slot to preserve it (PATCH uses full-
    replacement semantics). If the structural slot cannot be read, falls back
    to a safe default indicating structural data is available.

    Args:
        cell_key: The Harmony cell key to update.
        p1_url: Base URL of the Pillar 1 HTTP API.
        structural_override: Optional override for the structural slot
            (used in tests to avoid a Pillar 1 round-trip).

    Returns:
        True if the PATCH succeeded, False otherwise.
    """
    p1_url = p1_url.rstrip("/")

    # Read current fidelity to preserve structural slot
    if structural_override is not None:
        structural_slot = structural_override
    else:
        current = read_current_fidelity(cell_key, p1_url)
        if current and current.get("structural"):
            structural_slot = current["structural"]
        else:
            # Safe default: structural available (it got us here)
            structural_slot = {
                "status": "available",
                "source": "nsw_cadastral",
                "captured_at": None,
            }

    body = {
        "structural": structural_slot,
        "photorealistic": build_pending_photorealistic_slot(),
    }

    try:
        resp = requests.patch(
            f"{p1_url}/cells/{cell_key}/fidelity",
            json=body,
            timeout=10,
        )
        if resp.status_code in (200, 204):
            logger.info(
                "Fidelity reset applied: %s photorealistic.status → pending",
                cell_key,
            )
            return True
        logger.warning(
            "Fidelity reset PATCH returned HTTP %d for %s: %s",
            resp.status_code,
            cell_key,
            resp.text[:300],
        )
        return False
    except requests.exceptions.RequestException as exc:
        logger.error("Fidelity reset request failed for %s: %s", cell_key, exc)
        return False


def reset_photorealistic_fidelity_batch(
    cell_keys: list[str],
    p1_url: str = _DEFAULT_P1_URL,
) -> dict[str, bool]:
    """Reset photorealistic fidelity for multiple cells.

    Returns a dict mapping cell_key → success boolean.
    Used by the runner after a batch of change_confirmed transitions.
    """
    results: dict[str, bool] = {}
    for cell_key in cell_keys:
        results[cell_key] = reset_photorealistic_fidelity(cell_key, p1_url)
    return results
