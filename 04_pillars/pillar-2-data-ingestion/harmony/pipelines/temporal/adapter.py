# Harmony Pillar 2 — M7 Temporal Trigger Layer
# D2: PermitSourceAdapter interface + NSWPlanningPortalAdapter
#
# ADR-016 §2.2  — Pull-based polling
# ADR-016 §2.8  — Multi-source adapter pattern
# Constraint:   NSW-specific logic lives only in NSWPlanningPortalAdapter
# Constraint:   Parameters sent as HTTP HEADERS, not query params (dispatch briefing)
# Constraint:   Minimum 2-second interval between requests to the same endpoint
# Constraint:   No credentials stored — NSW ePlanning API is public
# Constraint:   Geographic scope: Central Coast LGA only

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional

import requests

from harmony.pipelines.temporal.models import EventType, PermitRecord

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — NSW ePlanning API (from dispatch briefing, April 24 2026)
# ---------------------------------------------------------------------------

_NSW_BASE = "https://api.apps1.nsw.gov.au/eplanning/data/v0"

NSW_ENDPOINTS: dict[str, str] = {
    "da":  f"{_NSW_BASE}/OnlineDA",
    "cdc": f"{_NSW_BASE}/OnlineCDC",
    "cc":  f"{_NSW_BASE}/OnlineCC",
    "oc":  f"{_NSW_BASE}/OC",        # Note: /OC not /OnlineOC
}

# Retry schedule: 30s, 120s, 480s (ADR-016 §2.2)
_RETRY_DELAYS = [30, 120, 480]

# Minimum inter-request delay (dispatch briefing — real API contract)
_MIN_REQUEST_INTERVAL_S = 2.0

# Default page size for NSW API
_PAGE_SIZE = 1000


# ---------------------------------------------------------------------------
# Abstract interface — ADR-016 §2.8
# ---------------------------------------------------------------------------

class PermitSourceAdapter(ABC):
    """Generic permit source adapter interface.

    All jurisdiction adapters implement this interface. The state transition
    service and resolver consume PermitRecord / PermitEvent types only and
    are completely agnostic to which adapter produced them.

    Adding a new jurisdiction means implementing a new subclass — the
    transition service and resolver require no modification.
    """

    @abstractmethod
    def poll(
        self,
        since_datetime: Optional[datetime] = None,
    ) -> list[PermitRecord]:
        """Poll the source and return normalised PermitRecord objects.

        Args:
            since_datetime: If provided, only return records updated after
                this datetime. If None, return recent records per the
                adapter's default window.

        Returns:
            List of normalised PermitRecord objects. NSW-specific fields are
            mapped to canonical PermitRecord field names during normalisation.
        """

    @abstractmethod
    def get_permit_polygon(self, permit_id: str) -> Optional[dict]:
        """Return GeoJSON geometry for a permit, if available.

        Returns None if the source does not provide spatial data for this
        permit type (e.g. the DA API has no coordinates).
        """

    @abstractmethod
    def get_permit_address(self, permit_id: str) -> Optional[str]:
        """Return the street address for a permit, if available."""


# ---------------------------------------------------------------------------
# NSW Planning Portal Adapter — ADR-016 §2.8
# All NSW-specific logic is isolated here.
# ---------------------------------------------------------------------------

class NSWPlanningPortalAdapter(PermitSourceAdapter):
    """Adapter for the NSW ePlanning API — DA, CDC, CC, and OC endpoints.

    Polls all four endpoints with Central Coast Council filter. Normalises
    NSW field names to canonical PermitRecord fields. Implements retry with
    exponential backoff per ADR-016 §2.7.

    Critical implementation notes:
    - Parameters are HTTP HEADERS, not query parameters (dispatch briefing)
    - Minimum 2-second delay between requests to the same endpoint
    - No credentials — all NSW ePlanning endpoints are public
    """

    def __init__(
        self,
        council_name: str = "Central Coast Council",
        page_size: int = _PAGE_SIZE,
        min_request_interval_s: float = _MIN_REQUEST_INTERVAL_S,
        timeout_s: int = 30,
    ) -> None:
        self.council_name = council_name
        self.page_size = page_size
        self.min_request_interval_s = min_request_interval_s
        self.timeout_s = timeout_s
        self._last_request_time: dict[str, float] = {}
        # Internal permit cache for address/polygon lookup by permit_id
        self._record_cache: dict[str, dict] = {}

    # -----------------------------------------------------------------------
    # Public interface
    # -----------------------------------------------------------------------

    def poll(
        self,
        since_datetime: Optional[datetime] = None,
    ) -> list[PermitRecord]:
        """Poll all four NSW ePlanning endpoints and return normalised records.

        Polls DA, CDC, CC, and OC in sequence with the council name filter.
        Applies date filter if since_datetime is provided.
        """
        records: list[PermitRecord] = []

        date_filter: dict = {}
        if since_datetime is not None:
            date_str = since_datetime.strftime("%Y-%m-%d")
            date_filter = {
                "LodgementDateFrom": date_str,
                "DeterminationDateFrom": date_str,
            }

        for permit_type, endpoint_key in [
            ("da", "da"),
            ("cdc", "cdc"),
            ("cc", "cc"),
            ("oc", "oc"),
        ]:
            try:
                raw_records = self._poll_endpoint(
                    endpoint_key=endpoint_key,
                    extra_filters=date_filter,
                )
                for raw in raw_records:
                    self._record_cache[raw.get("PlanningPortalApplicationNumber", "")] = raw
                    record = self._normalise(raw, permit_type)
                    if record is not None:
                        records.append(record)
            except Exception as exc:
                logger.error(
                    "Failed to poll NSW ePlanning %s endpoint after retries: %s",
                    endpoint_key,
                    exc,
                )

        logger.info(
            "NSW ePlanning poll complete: %d total permit records across DA/CDC/CC/OC",
            len(records),
        )
        return records

    def get_permit_polygon(self, permit_id: str) -> Optional[dict]:
        """Return a GeoJSON Point geometry for CC/OC permits that carry X/Y.

        DA permits have no coordinates — returns None for those.
        """
        raw = self._record_cache.get(permit_id)
        if raw is None:
            return None
        x = raw.get("X")
        y = raw.get("Y")
        if x is not None and y is not None:
            try:
                return {
                    "type": "Point",
                    "coordinates": [float(x), float(y)],
                }
            except (TypeError, ValueError):
                return None
        return None

    def get_permit_address(self, permit_id: str) -> Optional[str]:
        """Return street address for a permit.

        DA records use the FullAddress field. CC/OC records reconstruct
        from StreetNumber1 + StreetName + Suburb + Postcode.
        """
        raw = self._record_cache.get(permit_id)
        if raw is None:
            return None

        # DA API: has FullAddress directly
        if raw.get("FullAddress"):
            return str(raw["FullAddress"]).strip()

        # CC/OC: reconstruct from components
        parts = [
            raw.get("StreetNumber1", ""),
            raw.get("StreetName", ""),
            raw.get("Suburb", ""),
            raw.get("Postcode", ""),
        ]
        assembled = " ".join(str(p) for p in parts if p).strip()
        return assembled if assembled else None

    # -----------------------------------------------------------------------
    # Private polling machinery
    # -----------------------------------------------------------------------

    def _poll_endpoint(
        self,
        endpoint_key: str,
        extra_filters: Optional[dict] = None,
    ) -> list[dict]:
        """Paginate through one NSW ePlanning endpoint and return all raw records."""
        all_records: list[dict] = []
        page = 1

        while True:
            raw_page = self._fetch_page(
                endpoint_key=endpoint_key,
                page_number=page,
                extra_filters=extra_filters or {},
            )
            if raw_page is None:
                # Unrecoverable after retries — stop pagination for this endpoint
                break

            items = raw_page if isinstance(raw_page, list) else []
            all_records.extend(items)

            # NSW API returns empty list when pages are exhausted
            if len(items) < self.page_size:
                break

            page += 1

        logger.debug(
            "NSW ePlanning %s: retrieved %d records over %d page(s)",
            endpoint_key,
            len(all_records),
            page,
        )
        return all_records

    def _fetch_page(
        self,
        endpoint_key: str,
        page_number: int,
        extra_filters: dict,
    ) -> Optional[list]:
        """Fetch one page from the NSW API with retry and backoff.

        Per dispatch briefing: parameters are HTTP HEADERS, not query params.
        Retry up to 3 times with backoff schedule [30s, 120s, 480s].
        """
        url = NSW_ENDPOINTS[endpoint_key]

        filters: dict = {"CouncilName": [self.council_name]}
        filters.update(extra_filters)

        headers = {
            "PageSize": str(self.page_size),
            "PageNumber": str(page_number),
            "filters": json.dumps(filters),
        }

        self._respect_rate_limit(endpoint_key)

        for attempt, retry_delay in enumerate([0] + _RETRY_DELAYS):
            if retry_delay > 0:
                logger.warning(
                    "NSW ePlanning %s page %d: retry %d/%d after %ds",
                    endpoint_key,
                    page_number,
                    attempt,
                    len(_RETRY_DELAYS),
                    retry_delay,
                )
                time.sleep(retry_delay)

            try:
                response = requests.get(url, headers=headers, timeout=self.timeout_s)
                self._last_request_time[endpoint_key] = time.monotonic()

                if response.status_code == 200:
                    data = response.json()
                    # NSW API wraps results — handle both list and dict responses
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        # Common wrapper patterns: {"Application": [...]}
                        for key in ("Application", "Result", "Data", "Items"):
                            if key in data and isinstance(data[key], list):
                                return data[key]
                        # Return first list value found
                        for v in data.values():
                            if isinstance(v, list):
                                return v
                    return []

                logger.warning(
                    "NSW ePlanning %s page %d: HTTP %d — %s",
                    endpoint_key,
                    page_number,
                    response.status_code,
                    response.text[:200],
                )

            except requests.exceptions.Timeout:
                logger.warning(
                    "NSW ePlanning %s page %d: timeout (attempt %d)",
                    endpoint_key,
                    page_number,
                    attempt + 1,
                )
            except requests.exceptions.RequestException as exc:
                logger.warning(
                    "NSW ePlanning %s page %d: request error (attempt %d): %s",
                    endpoint_key,
                    page_number,
                    attempt + 1,
                    exc,
                )

        logger.error(
            "NSW ePlanning %s page %d: all %d retry attempts exhausted — marking as deferred",
            endpoint_key,
            page_number,
            len(_RETRY_DELAYS),
        )
        return None

    def _respect_rate_limit(self, endpoint_key: str) -> None:
        """Enforce the minimum inter-request interval for a given endpoint."""
        last = self._last_request_time.get(endpoint_key)
        if last is not None:
            elapsed = time.monotonic() - last
            if elapsed < self.min_request_interval_s:
                time.sleep(self.min_request_interval_s - elapsed)

    # -----------------------------------------------------------------------
    # Normalisation — NSW fields → canonical PermitRecord
    # -----------------------------------------------------------------------

    def _normalise(self, raw: dict, permit_type: str) -> Optional[PermitRecord]:
        """Map NSW API field names to canonical PermitRecord fields.

        NSW API field mapping per dispatch briefing (April 24, 2026):
          DA:  PlanningPortalApplicationNumber, ApplicationStatus, FullAddress,
               LotNumber, PlanLabel, LodgementDate, DeterminationDate
          CC:  PlanningPortalApplicationNumber, ApplicationStatus, X, Y,
               Lot, PlanLabel, StreetName, StreetNumber1, Suburb, Postcode,
               DeterminationDate
          OC:  Same structure as CC. OC DeterminationDate → valid_from.
        """
        permit_id = raw.get("PlanningPortalApplicationNumber")
        if not permit_id:
            logger.debug("Skipping record with no PlanningPortalApplicationNumber")
            return None

        application_status = raw.get("ApplicationStatus", "")

        # Determine event_date: prefer DeterminationDate if present, else LodgementDate
        event_date: Optional[date] = None
        for field_name in ("DeterminationDate", "LodgementDate"):
            raw_date = raw.get(field_name)
            if raw_date:
                event_date = self._parse_date(raw_date)
                if event_date is not None:
                    break

        # Lot number field differs between DA and CC/OC endpoints
        lot_number = raw.get("LotNumber") or raw.get("Lot")

        return PermitRecord(
            permit_id=str(permit_id),
            permit_source="nsw_planning_portal",
            permit_type=permit_type,
            application_status=application_status,
            event_date=event_date,
            full_address=raw.get("FullAddress"),
            lot_number=str(lot_number) if lot_number else None,
            plan_label=raw.get("PlanLabel"),
            x_coord=self._parse_float(raw.get("X")),
            y_coord=self._parse_float(raw.get("Y")),
            raw_record=raw,
        )

    @staticmethod
    def _parse_date(value: object) -> Optional[date]:
        """Parse a date string from the NSW API. Handles ISO and DD/MM/YYYY."""
        if value is None:
            return None
        s = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_float(value: object) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


# ---------------------------------------------------------------------------
# Event classification — maps NSW permit records to EventType
# per the event-to-state mapping table in the dispatch briefing
# ---------------------------------------------------------------------------

def classify_event(record: PermitRecord) -> Optional[EventType]:
    """Determine the EventType for a normalised PermitRecord.

    Mapping per dispatch briefing (April 24 2026):
      DA + Under Assessment  → da_lodged
      DA + Withdrawn         → da_withdrawn
      DA + Refused           → da_refused
      CC (any new record)    → cc_issued
      OC (any new record)    → oc_issued

    Returns None if the record does not map to a state machine event
    (e.g. a DA in an unrecognised status that we do not act on).
    """
    ptype = record.permit_type.lower()
    status = record.application_status.strip()

    if ptype == "da":
        if status == "Under Assessment":
            return EventType.DA_LODGED
        if status == "Withdrawn":
            return EventType.DA_WITHDRAWN
        if status == "Refused":
            return EventType.DA_REFUSED
        # Determined DAs are not re-mapped to an event here — the downstream
        # CC/OC records carry the construction and completion events.
        return None

    if ptype == "cdc":
        # CDC (Complying Development Certificate) treated as CC equivalent
        return EventType.CC_ISSUED

    if ptype == "cc":
        return EventType.CC_ISSUED

    if ptype == "oc":
        return EventType.OC_ISSUED

    return None
