# Harmony Pillar 2 — M7 Temporal Trigger Layer
# D3: Permit-to-Cell Resolver
#
# ADR-016 §2.6 — Address-to-cell resolution hierarchy:
#   1. Spatial intersection   — CC/OC have X/Y coordinates → r10 cell lookup
#   2. Lot/Plan matching      — all endpoints carry Lot + PlanLabel
#   3. Address geocoding      — DA FullAddress → known_names entity index
#   4. Unresolved             — log with full record, never discard
#
# Pillar 1 HTTP API is the only read interface for cell/entity queries.
# GDAL runs in Docker — no GDAL calls in this module (pure Python resolution).

from __future__ import annotations

import logging
import re
import sys
import os
from typing import Optional

import httpx

from harmony.pipelines.temporal.models import (
    EventType,
    PermitEvent,
    PermitRecord,
    ResolutionMethod,
    UnresolvedPermit,
)
from harmony.pipelines.temporal.adapter import PermitSourceAdapter, classify_event

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pillar 1 API base URL — injected at runtime
# ---------------------------------------------------------------------------

_DEFAULT_P1_URL = os.environ.get("HARMONY_P1_URL", "http://localhost:8000")

# Target resolution for spatial cell derivation (building/parcel scale)
_SPATIAL_RESOLUTION = 10  # r10

# ---------------------------------------------------------------------------
# Cell key derivation helper
# We call Pillar 1 for lookups; for key derivation we use the derive.py
# package from Pillar 1 if it is on the path, otherwise we fall back to
# the Pillar 1 resolution API.
# ---------------------------------------------------------------------------

def _derive_cell_key_from_latlon(lat: float, lon: float, p1_url: str) -> Optional[str]:
    """Resolve a lat/lon coordinate to a Harmony cell key at r10.

    Primary: derive cell key directly using Pillar 1 derive module if
    it is accessible on the Python path.
    Fallback: query Pillar 1 /resolve/latlon endpoint if available.
    """
    # Attempt to use Pillar 1 derive.py directly (when running inside
    # the container with the full Pillar 1 package on sys.path).
    try:
        # sys.path injection for monorepo — Pillar 1 package location
        _p1_src = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "..",
            "pillar-1-spatial-substrate", "harmony", "packages", "cell-key", "src"
        )
        if _p1_src not in sys.path:
            sys.path.insert(0, _p1_src)
        import derive  # type: ignore[import]
        result = derive.derive_cell_key(lat=lat, lon=lon, resolution=_SPATIAL_RESOLUTION, region="cc")
        if result and isinstance(result, str):
            return result
    except Exception as exc:
        logger.debug("derive module unavailable, using API fallback: %s", exc)

    # Fallback: query the Pillar 1 API for the cell at these coordinates
    try:
        resp = httpx.get(
            f"{p1_url}/resolve/latlon",
            params={"lat": lat, "lon": lon, "resolution": _SPATIAL_RESOLUTION},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("cell_key")
    except Exception as exc:
        logger.debug("Pillar 1 latlon resolution API unavailable: %s", exc)

    return None


def _query_entities_by_lot_plan(
    lot_number: str,
    plan_label: str,
    p1_url: str,
) -> list[str]:
    """Query Pillar 1 entities for cells matching a lot/plan composite key.

    Searches the entity registry for cadastral_lot entities whose known_names
    contain the lot+plan string (e.g. "Lot 1 DP787786").

    Returns list of cell_key strings.
    """
    composite = _build_lot_plan_key(lot_number, plan_label)
    if not composite:
        return []

    try:
        resp = httpx.get(
            f"{p1_url}/resolve/known-name",
            params={"q": composite, "entity_subtype": "lot"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            entities = data if isinstance(data, list) else data.get("entities", [])
            cell_keys = []
            for ent in entities:
                pk = ent.get("primary_cell_id") or ent.get("cell_key")
                if pk:
                    cell_keys.append(pk)
                cell_keys.extend(ent.get("secondary_cell_ids", []))
            return list(set(cell_keys))
    except Exception as exc:
        logger.debug("Pillar 1 lot/plan lookup failed: %s", exc)

    return []


def _query_entities_by_address(address: str, p1_url: str) -> list[str]:
    """Query Pillar 1 entities for cells matching a street address string.

    Uses the known_names index on building and road_segment entities.
    Returns list of cell_key strings.
    """
    if not address or not address.strip():
        return []

    try:
        resp = httpx.get(
            f"{p1_url}/resolve/known-name",
            params={"q": address.strip()},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            entities = data if isinstance(data, list) else data.get("entities", [])
            cell_keys = []
            for ent in entities:
                pk = ent.get("primary_cell_id") or ent.get("cell_key")
                if pk:
                    cell_keys.append(pk)
                cell_keys.extend(ent.get("secondary_cell_ids", []))
            return list(set(cell_keys))
    except Exception as exc:
        logger.debug("Pillar 1 address lookup failed: %s", exc)

    return []


def _build_lot_plan_key(lot_number: str, plan_label: str) -> Optional[str]:
    """Build the lot+plan composite string matching the known_names format.

    Entity schema (p2-entity-schemas.md §cadastral_lot): known_names includes
    "Lot {lot_number} {plan_type}{plan_number}" and the raw plan_label.

    Returns None if inputs are insufficient to build the key.
    """
    if not lot_number or not plan_label:
        return None

    pl = plan_label.strip()
    lot = lot_number.strip()

    # Extract plan type prefix and plan number from plan_label
    # e.g. "DP787786" → type="DP", number="787786"
    m = re.match(r"^([A-Za-z]+)(\d+)$", pl)
    if m:
        plan_type, plan_number = m.group(1).upper(), m.group(2)
        return f"Lot {lot} {plan_type}{plan_number}"

    # Fallback: return the raw plan_label for the known_names search
    return pl


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

class PermitCellResolver:
    """Resolves PermitRecord objects to Harmony Cell keys.

    Implements the four-level resolution hierarchy from ADR-016 §2.6 and
    the dispatch briefing. Unresolved permits are logged, never discarded.
    """

    def __init__(self, p1_url: str = _DEFAULT_P1_URL) -> None:
        self.p1_url = p1_url.rstrip("/")

    def resolve_batch(
        self,
        records: list[PermitRecord],
        adapter: PermitSourceAdapter,
    ) -> tuple[list[PermitEvent], list[UnresolvedPermit]]:
        """Resolve a batch of PermitRecords.

        Returns:
            (resolved_events, unresolved_permits)
            resolved_events: PermitEvent objects with cell_keys populated.
            unresolved_permits: PermitRecord objects that could not be resolved.
        """
        resolved: list[PermitEvent] = []
        unresolved: list[UnresolvedPermit] = []

        for record in records:
            event_type = classify_event(record)
            if event_type is None:
                # This permit status does not map to a state machine event
                logger.debug(
                    "Permit %s (type=%s, status=%s) does not map to a state machine event — skipping",
                    record.permit_id,
                    record.permit_type,
                    record.application_status,
                )
                continue

            cell_keys, method = self._resolve_one(record, adapter)

            if cell_keys:
                resolved.append(PermitEvent(
                    permit=record,
                    event_type=event_type,
                    cell_keys=cell_keys,
                    resolution_method=method,
                ))
                logger.debug(
                    "Permit %s resolved via %s → %d cell(s)",
                    record.permit_id,
                    method.value,
                    len(cell_keys),
                )
            else:
                unresolved.append(UnresolvedPermit(
                    permit=record,
                    event_type=event_type,
                    reason="All resolution methods exhausted — no matching cell found",
                ))
                logger.warning(
                    "Permit %s UNRESOLVED (type=%s, address=%s, lot=%s/%s)",
                    record.permit_id,
                    record.permit_type,
                    record.full_address,
                    record.lot_number,
                    record.plan_label,
                )

        return resolved, unresolved

    def _resolve_one(
        self,
        record: PermitRecord,
        adapter: PermitSourceAdapter,
    ) -> tuple[list[str], ResolutionMethod]:
        """Attempt resolution through the hierarchy. Returns (cell_keys, method).

        Returns ([], ResolutionMethod.UNRESOLVED) when all paths fail.
        """
        # ------------------------------------------------------------------
        # Level 1: Spatial intersection — CC/OC carry X/Y coordinates
        # ------------------------------------------------------------------
        if record.x_coord is not None and record.y_coord is not None:
            cell_key = _derive_cell_key_from_latlon(
                lat=record.y_coord,   # Y = latitude (northing in WGS84)
                lon=record.x_coord,   # X = longitude (easting in WGS84)
                p1_url=self.p1_url,
            )
            if cell_key:
                return [cell_key], ResolutionMethod.SPATIAL

            # Also check the adapter polygon (if richer geometry available)
            geom = adapter.get_permit_polygon(record.permit_id)
            if geom and geom.get("type") == "Point":
                coords = geom.get("coordinates", [])
                if len(coords) == 2:
                    cell_key = _derive_cell_key_from_latlon(
                        lat=coords[1], lon=coords[0], p1_url=self.p1_url
                    )
                    if cell_key:
                        return [cell_key], ResolutionMethod.SPATIAL

        # ------------------------------------------------------------------
        # Level 2: Lot/Plan matching — all endpoints carry Lot + PlanLabel
        # ------------------------------------------------------------------
        if record.lot_number and record.plan_label:
            cell_keys = _query_entities_by_lot_plan(
                lot_number=record.lot_number,
                plan_label=record.plan_label,
                p1_url=self.p1_url,
            )
            if cell_keys:
                return cell_keys, ResolutionMethod.LOT_PLAN

        # ------------------------------------------------------------------
        # Level 3: Address geocoding — DA FullAddress against known_names
        # ------------------------------------------------------------------
        address = adapter.get_permit_address(record.permit_id)
        if address:
            cell_keys = _query_entities_by_address(address, self.p1_url)
            if cell_keys:
                return cell_keys, ResolutionMethod.ADDRESS

        # ------------------------------------------------------------------
        # Level 4: Unresolved — log, never discard (ADR-016 §2.6)
        # ------------------------------------------------------------------
        return [], ResolutionMethod.UNRESOLVED
