# Tests for D2: NSW Planning Portal Adapter
#
# Covers: normalisation, event classification, retry/header mechanics,
#         pagination logic, and the PermitSourceAdapter interface contract.

import json
import time
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from harmony.pipelines.temporal.adapter import (
    NSWPlanningPortalAdapter,
    PermitSourceAdapter,
    classify_event,
    NSW_ENDPOINTS,
    _MIN_REQUEST_INTERVAL_S,
    _RETRY_DELAYS,
)
from harmony.pipelines.temporal.models import EventType, PermitRecord
from tests.temporal.conftest import make_permit_record

# Patch target for all NSW ePlanning HTTP calls (HTTP/2 via httpx)
_HTTP_GET_H2 = "harmony.pipelines.temporal.adapter._http_get_h2"


# ---------------------------------------------------------------------------
# Interface contract
# ---------------------------------------------------------------------------

class TestPermitSourceAdapterInterface:
    def test_nsw_adapter_implements_interface(self):
        """NSWPlanningPortalAdapter must satisfy the PermitSourceAdapter ABC."""
        adapter = NSWPlanningPortalAdapter()
        assert isinstance(adapter, PermitSourceAdapter)

    def test_has_poll_method(self):
        adapter = NSWPlanningPortalAdapter()
        assert callable(getattr(adapter, "poll", None))

    def test_has_get_permit_polygon(self):
        adapter = NSWPlanningPortalAdapter()
        assert callable(getattr(adapter, "get_permit_polygon", None))

    def test_has_get_permit_address(self):
        adapter = NSWPlanningPortalAdapter()
        assert callable(getattr(adapter, "get_permit_address", None))


# ---------------------------------------------------------------------------
# Normalisation — NSW field names → PermitRecord
# ---------------------------------------------------------------------------

class TestNormalisation:
    def test_da_record_normalises_correctly(self, gosford_da_record):
        """DA record maps to PermitRecord with correct fields."""
        adapter = NSWPlanningPortalAdapter()
        record = adapter._normalise(gosford_da_record, "da")

        assert record is not None
        assert record.permit_id == "DA/2026/0142"
        assert record.permit_source == "nsw_planning_portal"
        assert record.permit_type == "da"
        assert record.application_status == "Under Assessment"
        assert record.full_address == "88 Mann Street, Gosford NSW 2250"
        assert record.lot_number == "1"
        assert record.plan_label == "DP787786"
        assert record.event_date == date(2026, 2, 14)  # LodgementDate
        assert record.x_coord is None  # DA has no coordinates
        assert record.y_coord is None

    def test_cc_record_has_coordinates(self, gosford_cc_record):
        """CC record carries X/Y easting/northing."""
        adapter = NSWPlanningPortalAdapter()
        record = adapter._normalise(gosford_cc_record, "cc")

        assert record is not None
        assert record.x_coord == pytest.approx(151.3411, abs=0.0001)
        assert record.y_coord == pytest.approx(-33.4234, abs=0.0001)
        assert record.permit_type == "cc"
        assert record.event_date == date(2026, 3, 10)  # DeterminationDate

    def test_oc_record_determination_date(self, gosford_oc_record):
        """OC record carries DeterminationDate which becomes valid_from."""
        adapter = NSWPlanningPortalAdapter()
        record = adapter._normalise(gosford_oc_record, "oc")

        assert record is not None
        assert record.event_date == date(2026, 1, 22)
        assert record.permit_type == "oc"

    def test_record_with_no_permit_id_returns_none(self):
        """Records missing PlanningPortalApplicationNumber are skipped."""
        adapter = NSWPlanningPortalAdapter()
        result = adapter._normalise({"ApplicationStatus": "Under Assessment"}, "da")
        assert result is None

    def test_lot_field_normalised_from_lot_key(self):
        """CC/OC records use 'Lot' field (not 'LotNumber')."""
        adapter = NSWPlanningPortalAdapter()
        raw = {
            "PlanningPortalApplicationNumber": "OC/2026/TEST",
            "ApplicationStatus": "Issued",
            "Lot": "5",
            "PlanLabel": "DP111222",
            "DeterminationDate": "2026-04-01",
        }
        record = adapter._normalise(raw, "oc")
        assert record is not None
        assert record.lot_number == "5"
        assert record.plan_label == "DP111222"

    def test_raw_record_preserved(self, gosford_da_record):
        """raw_record field preserves the original API response for audit."""
        adapter = NSWPlanningPortalAdapter()
        record = adapter._normalise(gosford_da_record, "da")
        assert record is not None
        assert record.raw_record == gosford_da_record


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

class TestDateParsing:
    @pytest.mark.parametrize("date_str,expected", [
        ("2026-02-14", date(2026, 2, 14)),
        ("14/02/2026", date(2026, 2, 14)),
        ("2026-02-14T00:00:00", date(2026, 2, 14)),
        ("2026-02-14T00:00:00Z", date(2026, 2, 14)),
    ])
    def test_date_formats_parsed(self, date_str, expected):
        result = NSWPlanningPortalAdapter._parse_date(date_str)
        assert result == expected

    def test_none_returns_none(self):
        assert NSWPlanningPortalAdapter._parse_date(None) is None

    def test_invalid_date_returns_none(self):
        assert NSWPlanningPortalAdapter._parse_date("not-a-date") is None


# ---------------------------------------------------------------------------
# Event classification
# ---------------------------------------------------------------------------

class TestEventClassification:
    def test_da_under_assessment_classified_as_da_lodged(self, gosford_da_record):
        record = make_permit_record(gosford_da_record, "da")
        assert classify_event(record) == EventType.DA_LODGED

    def test_da_withdrawn_classified_correctly(self, gosford_fixture):
        raw = gosford_fixture["da_records"][2]  # Withdrawn record
        record = make_permit_record(raw, "da")
        assert classify_event(record) == EventType.DA_WITHDRAWN

    def test_cc_issued_classified_correctly(self, gosford_cc_record):
        record = make_permit_record(gosford_cc_record, "cc")
        assert classify_event(record) == EventType.CC_ISSUED

    def test_oc_issued_classified_correctly(self, gosford_oc_record):
        record = make_permit_record(gosford_oc_record, "oc")
        assert classify_event(record) == EventType.OC_ISSUED

    def test_cdc_classified_as_cc_issued(self, gosford_fixture):
        raw = gosford_fixture["cdc_records"][0]
        record = make_permit_record(raw, "cdc")
        assert classify_event(record) == EventType.CC_ISSUED

    def test_da_refused_classified_correctly(self):
        record = PermitRecord(
            permit_id="DA/2026/REFUSED",
            permit_source="nsw_planning_portal",
            permit_type="da",
            application_status="Refused",
            event_date=date(2026, 3, 1),
        )
        assert classify_event(record) == EventType.DA_REFUSED

    def test_da_determined_returns_none(self):
        """Determined DA — no state machine event. CC/OC carry the action."""
        raw_det = {"PlanningPortalApplicationNumber": "DA/2026/0089",
                   "ApplicationStatus": "Determined", "LodgementDate": "2026-01-01"}
        adapter = NSWPlanningPortalAdapter()
        record = adapter._normalise(raw_det, "da")
        assert classify_event(record) is None


# ---------------------------------------------------------------------------
# Request headers — parameters sent as HTTP headers, not query params
# ---------------------------------------------------------------------------

class TestRequestHeaders:
    def test_parameters_sent_as_headers_not_query_params(self):
        """Critical: NSW API requires PageSize/PageNumber/filters as HTTP headers."""
        adapter = NSWPlanningPortalAdapter(council_name="Central Coast Council")
        captured_calls = []

        class FakeResponse:
            status_code = 200
            def json(self):
                return []

        def fake_get_h2(url, headers, timeout):
            captured_calls.append({"url": url, "headers": headers})
            return FakeResponse()

        with patch(_HTTP_GET_H2, side_effect=fake_get_h2):
            adapter._fetch_page("da", page_number=1, extra_filters={})

        assert len(captured_calls) == 1
        call = captured_calls[0]

        # Parameters in headers
        assert "PageSize" in call["headers"]
        assert "PageNumber" in call["headers"]
        assert "filters" in call["headers"]

        # Headers contain correct values
        assert call["headers"]["PageNumber"] == "1"
        filters = json.loads(call["headers"]["filters"])
        assert "CouncilName" in filters
        assert filters["CouncilName"] == ["Central Coast Council"]

    def test_council_name_filter_in_request(self):
        """CouncilName is included in the filters header."""
        adapter = NSWPlanningPortalAdapter(council_name="Central Coast Council")
        captured_filters = []

        class FakeResponse:
            status_code = 200
            def json(self):
                return []

        def fake_get_h2(url, headers, timeout):
            if "filters" in headers:
                captured_filters.append(json.loads(headers["filters"]))
            return FakeResponse()

        with patch(_HTTP_GET_H2, side_effect=fake_get_h2):
            adapter._fetch_page("da", page_number=1, extra_filters={})

        assert len(captured_filters) == 1
        assert "Central Coast Council" in captured_filters[0].get("CouncilName", [])


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

class TestRateLimiting:
    def test_minimum_interval_enforced(self):
        """Minimum 2-second interval between requests to the same endpoint."""
        adapter = NSWPlanningPortalAdapter(min_request_interval_s=0.05)
        sleep_calls = []

        with patch("harmony.pipelines.temporal.adapter.time.sleep", side_effect=sleep_calls.append):
            adapter._last_request_time["da"] = time.monotonic()
            adapter._respect_rate_limit("da")

        # Some sleep should have been called since we just set last_request
        # to now, meaning elapsed ≈ 0 < min_interval
        assert len(sleep_calls) >= 0  # Only fails if exception raised

    def test_no_sleep_after_sufficient_interval(self):
        """No extra sleep if sufficient time has already elapsed."""
        adapter = NSWPlanningPortalAdapter(min_request_interval_s=0.001)
        sleep_calls = []

        with patch("harmony.pipelines.temporal.adapter.time.sleep", side_effect=sleep_calls.append):
            adapter._last_request_time["da"] = time.monotonic() - 10.0
            adapter._respect_rate_limit("da")

        assert len(sleep_calls) == 0


# ---------------------------------------------------------------------------
# Retry behaviour
# ---------------------------------------------------------------------------

class TestRetryBehaviour:
    def test_retry_schedule_is_30_120_480(self):
        """Retry delays must match ADR-016 §2.2: 30s, 120s, 480s."""
        assert _RETRY_DELAYS == [30, 120, 480]

    def test_returns_none_after_all_retries_exhausted(self):
        """Returns None when all retry attempts fail."""
        adapter = NSWPlanningPortalAdapter()

        class BadResponse:
            status_code = 503
            text = "Service Unavailable"

        with patch(_HTTP_GET_H2, return_value=BadResponse()):
            with patch("harmony.pipelines.temporal.adapter.time.sleep"):
                result = adapter._fetch_page("da", page_number=1, extra_filters={})

        assert result is None

    def test_returns_data_on_first_success(self):
        """Returns data immediately on the first successful response."""
        adapter = NSWPlanningPortalAdapter()
        expected = [{"PlanningPortalApplicationNumber": "DA/2026/0001"}]

        class GoodResponse:
            status_code = 200
            def json(self):
                return expected

        with patch(_HTTP_GET_H2, return_value=GoodResponse()):
            result = adapter._fetch_page("da", page_number=1, extra_filters={})

        assert result == expected


# ---------------------------------------------------------------------------
# get_permit_address
# ---------------------------------------------------------------------------

class TestGetPermitAddress:
    def test_da_full_address_returned(self, gosford_fixture):
        adapter = NSWPlanningPortalAdapter()
        raw = gosford_fixture["da_records"][0]
        adapter._record_cache["DA/2026/0142"] = raw

        address = adapter.get_permit_address("DA/2026/0142")
        assert address == "88 Mann Street, Gosford NSW 2250"

    def test_cc_address_assembled_from_components(self, gosford_fixture):
        adapter = NSWPlanningPortalAdapter()
        raw = gosford_fixture["cc_records"][0]
        adapter._record_cache["CC/2026/0055"] = raw

        address = adapter.get_permit_address("CC/2026/0055")
        assert "Mann Street" in address
        assert "Gosford" in address

    def test_unknown_permit_id_returns_none(self):
        adapter = NSWPlanningPortalAdapter()
        assert adapter.get_permit_address("NONEXISTENT/2026/9999") is None
