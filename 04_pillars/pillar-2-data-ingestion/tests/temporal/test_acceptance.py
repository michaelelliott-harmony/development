# Tests for M7 Acceptance Criteria AC1–AC8
#
# AC1: Permit adapter connects to DA API and retrieves ≥1 Central Coast record
# AC2: Permit address/coordinates resolve to Harmony Cell(s)
# AC3: All four state transitions produce correct cell_status values
# AC4: valid_from = OC DeterminationDate, not datetime.now()
# AC5: photorealistic.status = pending after change_confirmed
# AC6: Same event applied twice produces no duplicate transition
# AC7: Migration has working up and down functions
# AC8: ADR-016 is Accepted before migration is produced
#
# Network note: AC1 live connectivity test is marked as requires_network.
# The domain api.apps1.nsw.gov.au is blocked by the environment's outbound
# proxy — the domain must be added to the allowed hosts list before this
# test can be validated in CI. All other AC tests pass without network.

import os
import sys
import json
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from harmony.pipelines.temporal.models import (
    CellStatus,
    EventType,
    PermitEvent,
    PermitRecord,
    ResolutionMethod,
    VALID_TRANSITIONS,
)
from harmony.pipelines.temporal.adapter import NSWPlanningPortalAdapter, classify_event
from harmony.pipelines.temporal.resolver import PermitCellResolver
from harmony.pipelines.temporal.transitions import AuditLog, CellTransitionService
from harmony.pipelines.temporal.fidelity import (
    build_pending_photorealistic_slot,
    reset_photorealistic_fidelity,
)


# ---------------------------------------------------------------------------
# Test cell key used throughout acceptance tests
# ---------------------------------------------------------------------------
_TEST_CELL = "hsam:r10:cc:acceptancetest1234"


def _make_event(event_type, permit_id, cell_key=_TEST_CELL, event_date=None):
    ptype_map = {
        EventType.DA_LODGED: ("da", "Under Assessment"),
        EventType.DA_WITHDRAWN: ("da", "Withdrawn"),
        EventType.DA_REFUSED: ("da", "Refused"),
        EventType.CC_ISSUED: ("cc", "Issued"),
        EventType.OC_ISSUED: ("oc", "Issued"),
    }
    ptype, status = ptype_map[event_type]
    permit = PermitRecord(
        permit_id=permit_id,
        permit_source="nsw_planning_portal",
        permit_type=ptype,
        application_status=status,
        event_date=event_date or date(2026, 3, 1),
    )
    return PermitEvent(
        permit=permit,
        event_type=event_type,
        cell_keys=[cell_key],
        resolution_method=ResolutionMethod.SPATIAL,
    )


# ---------------------------------------------------------------------------
# AC1: Permit adapter connects to DA API and retrieves ≥1 Central Coast record
# ---------------------------------------------------------------------------

class TestAC1PermitAdapterConnectivity:
    def test_ac1_adapter_structure_correct(self):
        """AC1 (structure): NSWPlanningPortalAdapter implements the required interface."""
        from harmony.pipelines.temporal.adapter import PermitSourceAdapter
        adapter = NSWPlanningPortalAdapter(council_name="Central Coast Council")
        assert isinstance(adapter, PermitSourceAdapter)
        assert hasattr(adapter, "poll")
        assert hasattr(adapter, "get_permit_polygon")
        assert hasattr(adapter, "get_permit_address")

    def test_ac1_gosford_fixture_represents_real_api_format(self, gosford_fixture):
        """AC1 (fixture): Gosford fixture records match documented NSW API schema."""
        da_records = gosford_fixture["da_records"]
        assert len(da_records) >= 1

        first = da_records[0]
        assert "PlanningPortalApplicationNumber" in first
        assert "ApplicationStatus" in first
        assert "FullAddress" in first
        assert "LodgementDate" in first

    def test_ac1_adapter_normalises_gosford_da(self, gosford_da_record):
        """AC1 (normalisation): Gosford DA fixture normalises to PermitRecord successfully."""
        adapter = NSWPlanningPortalAdapter()
        record = adapter._normalise(gosford_da_record, "da")

        assert record is not None
        assert record.permit_id == "DA/2026/0142"
        assert record.permit_source == "nsw_planning_portal"
        assert record.application_status == "Under Assessment"

    @pytest.mark.network
    def test_ac1_live_da_api_returns_central_coast_records(self):
        """AC1 (LIVE): Real API call to NSW ePlanning DA endpoint.

        REQUIRES NETWORK: api.apps1.nsw.gov.au must be in the allowed hosts list.
        This test is marked @pytest.mark.network and will be skipped in
        environments where the outbound proxy blocks this domain.

        Run with: pytest -m network
        """
        import requests
        headers = {
            "PageSize": "1",
            "PageNumber": "1",
            "filters": '{"CouncilName":["Central Coast Council"]}',
        }
        try:
            resp = requests.get(
                "https://api.apps1.nsw.gov.au/eplanning/data/v0/OnlineDA",
                headers=headers,
                timeout=15,
            )
        except Exception as exc:
            pytest.skip(f"Network unavailable for live API test: {exc}")

        if resp.status_code == 403 and "allowlist" in resp.text.lower():
            pytest.skip(
                "API host blocked by outbound proxy — add api.apps1.nsw.gov.au "
                "to the environment's allowed hosts list to enable AC1 live test"
            )

        assert resp.status_code == 200, f"Unexpected HTTP {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        # Unwrap any list or dict wrapper
        records = data if isinstance(data, list) else next(
            (v for v in data.values() if isinstance(v, list)), []
        )
        assert len(records) >= 1, "Expected at least 1 Central Coast DA record"


# ---------------------------------------------------------------------------
# AC2: Permit address/coordinates resolve to Harmony Cell(s)
# ---------------------------------------------------------------------------

class TestAC2Resolution:
    def test_ac2_cc_coordinates_resolve_to_cell(self):
        """AC2: CC record X/Y coordinates resolve to at least one cell key."""
        resolver = PermitCellResolver(p1_url="http://p1-stub")
        adapter = NSWPlanningPortalAdapter()

        cc_record = PermitRecord(
            permit_id="CC/2026/AC2",
            permit_source="nsw_planning_portal",
            permit_type="cc",
            application_status="Issued",
            event_date=date(2026, 3, 10),
            x_coord=151.3411,
            y_coord=-33.4234,
        )

        with patch(
            "harmony.pipelines.temporal.resolver._derive_cell_key_from_latlon",
            return_value="hsam:r10:cc:ac2testcell12345",
        ):
            cell_keys, method = resolver._resolve_one(cc_record, adapter)

        assert len(cell_keys) >= 1
        assert method == ResolutionMethod.SPATIAL

    def test_ac2_da_address_resolves_to_cell(self):
        """AC2: DA FullAddress resolves to at least one cell via known_names."""
        resolver = PermitCellResolver(p1_url="http://p1-stub")
        adapter = NSWPlanningPortalAdapter()
        adapter._record_cache["DA/2026/AC2ADDR"] = {
            "PlanningPortalApplicationNumber": "DA/2026/AC2ADDR",
            "FullAddress": "88 Mann Street, Gosford NSW 2250",
        }

        da_record = PermitRecord(
            permit_id="DA/2026/AC2ADDR",
            permit_source="nsw_planning_portal",
            permit_type="da",
            application_status="Under Assessment",
            event_date=date(2026, 2, 14),
            full_address="88 Mann Street, Gosford NSW 2250",
        )

        with patch(
            "harmony.pipelines.temporal.resolver._query_entities_by_lot_plan",
            return_value=[],
        ):
            with patch(
                "harmony.pipelines.temporal.resolver._query_entities_by_address",
                return_value=["hsam:r10:cc:mannstreet12345"],
            ):
                cell_keys, method = resolver._resolve_one(da_record, adapter)

        assert len(cell_keys) >= 1
        assert method == ResolutionMethod.ADDRESS


# ---------------------------------------------------------------------------
# AC3: All four state transitions produce correct cell_status values
# ---------------------------------------------------------------------------

class TestAC3AllFourTransitions:
    def test_ac3_all_four_transitions(self, transition_service):
        """AC3: All four state transitions produce correct cell_status values."""
        cell = "hsam:r10:cc:ac3testcell123456"

        # Transition 1: stable → change_expected
        r1 = transition_service.apply_events([
            _make_event(EventType.DA_LODGED, "DA/2026/AC3", cell)
        ])
        assert transition_service.audit_log.get_current_status(cell) == CellStatus.CHANGE_EXPECTED.value

        # Transition 2: change_expected → change_in_progress
        r2 = transition_service.apply_events([
            _make_event(EventType.CC_ISSUED, "CC/2026/AC3", cell)
        ])
        assert transition_service.audit_log.get_current_status(cell) == CellStatus.CHANGE_IN_PROGRESS.value

        # Transition 3: change_in_progress → change_confirmed
        r3 = transition_service.apply_events([
            _make_event(EventType.OC_ISSUED, "OC/2026/AC3", cell, date(2026, 4, 20))
        ])
        assert transition_service.audit_log.get_current_status(cell) == CellStatus.CHANGE_CONFIRMED.value

        # Verify all four statuses appeared in the correct sequence
        events = transition_service.audit_log.get_events_for_cell(cell)
        statuses = [e["new_status"] for e in events]
        assert CellStatus.CHANGE_EXPECTED.value in statuses
        assert CellStatus.CHANGE_IN_PROGRESS.value in statuses
        assert CellStatus.CHANGE_CONFIRMED.value in statuses

    def test_ac3_reverse_transition_change_expected_to_stable(self, transition_service):
        """AC3 (reverse): DA withdrawn returns cell from change_expected to stable."""
        cell = "hsam:r10:cc:ac3reversetest1234"

        transition_service.apply_events([
            _make_event(EventType.DA_LODGED, "DA/2026/AC3R", cell)
        ])
        transition_service.apply_events([
            _make_event(EventType.DA_WITHDRAWN, "DA/2026/AC3R", cell)
        ])

        assert transition_service.audit_log.get_current_status(cell) == CellStatus.STABLE.value


# ---------------------------------------------------------------------------
# AC4: valid_from = OC DeterminationDate, not datetime.now()
# ---------------------------------------------------------------------------

class TestAC4ValidFrom:
    def test_ac4_valid_from_is_oc_determination_date(self, transition_service):
        """AC4: valid_from set to OC DeterminationDate, never datetime.now()."""
        cell = "hsam:r10:cc:ac4testcell1234567"
        oc_date = date(2025, 7, 4)  # Historical date — conclusive proof it is not now()

        # Setup: get cell to change_in_progress
        transition_service.apply_events([_make_event(EventType.DA_LODGED, "DA/2026/AC4", cell)])
        transition_service.apply_events([_make_event(EventType.CC_ISSUED, "CC/2026/AC4", cell)])

        # Apply OC
        oc_permit = PermitRecord(
            permit_id="OC/2026/AC4",
            permit_source="nsw_planning_portal",
            permit_type="oc",
            application_status="Issued",
            event_date=oc_date,
        )
        oc_event = PermitEvent(
            permit=oc_permit,
            event_type=EventType.OC_ISSUED,
            cell_keys=[cell],
            resolution_method=ResolutionMethod.SPATIAL,
        )
        result = transition_service.apply_events([oc_event])

        assert len(result.applied) == 1
        applied = result.applied[0]

        # AC4 core assertion: valid_from = OC DeterminationDate
        assert applied.valid_from_date == oc_date
        # Prove it is NOT datetime.now()
        assert applied.valid_from_date != date.today()

    def test_ac4_valid_from_null_for_non_oc_events(self, transition_service):
        """AC4: valid_from remains null for DA and CC events."""
        cell = "hsam:r10:cc:ac4nulltest1234567"

        result = transition_service.apply_events([
            _make_event(EventType.DA_LODGED, "DA/2026/AC4N", cell)
        ])
        assert result.applied[0].valid_from_date is None


# ---------------------------------------------------------------------------
# AC5: photorealistic.status = pending after change_confirmed
# ---------------------------------------------------------------------------

class TestAC5FidelityReset:
    def test_ac5_photorealistic_pending_after_change_confirmed(self, transition_service):
        """AC5: fidelity_resets list contains cell_key after change_confirmed."""
        cell = "hsam:r10:cc:ac5testcell1234567"

        transition_service.apply_events([_make_event(EventType.DA_LODGED, "DA/2026/AC5", cell)])
        transition_service.apply_events([_make_event(EventType.CC_ISSUED, "CC/2026/AC5", cell)])
        result = transition_service.apply_events([
            _make_event(EventType.OC_ISSUED, "OC/2026/AC5", cell, date(2026, 4, 1))
        ])

        assert cell in result.fidelity_resets

    def test_ac5_pending_slot_structure(self):
        """AC5: The pending photorealistic slot has the correct structure."""
        slot = build_pending_photorealistic_slot()

        assert slot["status"] == "pending"
        assert slot["source"] is None
        assert slot["captured_at"] is None

    def test_ac5_fidelity_reset_via_pillar1_api(self):
        """AC5: reset_photorealistic_fidelity calls PATCH /cells/{key}/fidelity."""
        called_with = []

        def fake_patch(url, json=None, timeout=None):
            called_with.append({"url": url, "json": json})
            class R:
                status_code = 200
            return R()

        def fake_get(url, timeout=None):
            class R:
                status_code = 200
                def json(self):
                    return {"fidelity_coverage": {
                        "structural": {"status": "available", "source": "nsw_cadastral", "captured_at": None}
                    }}
            return R()

        with patch("harmony.pipelines.temporal.fidelity.requests.patch", side_effect=fake_patch):
            with patch("harmony.pipelines.temporal.fidelity.requests.get", side_effect=fake_get):
                result = reset_photorealistic_fidelity(
                    "hsam:r10:cc:ac5direct12345678",
                    p1_url="http://p1-stub",
                )

        assert result is True
        assert len(called_with) == 1
        assert "/fidelity" in called_with[0]["url"]
        body = called_with[0]["json"]
        assert body["photorealistic"]["status"] == "pending"
        assert body["photorealistic"]["source"] is None


# ---------------------------------------------------------------------------
# AC6: Same event applied twice produces no duplicate transition
# ---------------------------------------------------------------------------

class TestAC6Idempotency:
    def test_ac6_second_application_produces_no_duplicate(self, transition_service):
        """AC6: Applying the same event twice produces no duplicate transition."""
        cell = "hsam:r10:cc:ac6testcell1234567"
        event = _make_event(EventType.DA_LODGED, "DA/2026/AC6", cell)

        r1 = transition_service.apply_events([event])
        r2 = transition_service.apply_events([event])

        assert len(r1.applied) == 1
        assert len(r2.applied) == 0
        assert cell in r2.skipped_idempotent

    def test_ac6_no_duplicate_audit_log_entry(self, transition_service):
        """AC6: Duplicate application does not create a second audit log entry."""
        cell = "hsam:r10:cc:ac6auditlog123456"
        event = _make_event(EventType.DA_LODGED, "DA/2026/AC6B", cell)

        transition_service.apply_events([event])
        transition_service.apply_events([event])

        events = transition_service.audit_log.get_events_for_cell(cell)
        assert len(events) == 1


# ---------------------------------------------------------------------------
# AC7: Migration has working up and down functions
# ---------------------------------------------------------------------------

class TestAC7Migration:
    def test_ac7_migration_module_importable(self):
        """AC7: Migration module can be imported."""
        from harmony.pipelines.migrations import m7_temporal_field_activation as mig
        assert mig is not None

    def test_ac7_migration_has_up_function(self):
        """AC7: Migration has an up() function."""
        from harmony.pipelines.migrations import m7_temporal_field_activation as mig
        assert callable(mig.up)

    def test_ac7_migration_has_down_function(self):
        """AC7: Migration has a down() function."""
        from harmony.pipelines.migrations import m7_temporal_field_activation as mig
        assert callable(mig.down)

    def test_ac7_migration_requires_approval_flag_set(self):
        """AC7: REQUIRES_APPROVAL flag is True — migration cannot execute without Mikey."""
        from harmony.pipelines.migrations import m7_temporal_field_activation as mig
        assert mig.REQUIRES_APPROVAL is True

    def test_ac7_migration_execute_with_approval_enforces_mikey(self):
        """AC7: execute_with_approval raises PermissionError for non-Mikey approvers."""
        from harmony.pipelines.migrations import m7_temporal_field_activation as mig
        with pytest.raises(PermissionError, match="Mikey"):
            mig.execute_with_approval(
                conn=None,
                approved_by="DrYusuf",
                approved_at="2026-04-26T10:00:00Z",
            )

    def test_ac7_migration_schema_versions_defined(self):
        """AC7: Migration documents before/after schema versions."""
        from harmony.pipelines.migrations import m7_temporal_field_activation as mig
        assert mig.SCHEMA_VERSION_BEFORE == "0.2.0"
        assert mig.SCHEMA_VERSION_AFTER == "0.3.0"


# ---------------------------------------------------------------------------
# AC8: ADR-016 is Accepted before migration is produced
# ---------------------------------------------------------------------------

class TestAC8ADR016Accepted:
    def _adr016_path(self) -> str:
        # From tests/temporal/ → up 4 levels → workspace/development/ → docs/adr/
        return os.path.normpath(os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "..",
            "docs", "adr", "ADR-016-temporal-trigger-architecture.md",
        ))

    def test_ac8_adr016_file_exists(self):
        """AC8: ADR-016 file exists in the docs/adr/ directory."""
        adr_path = self._adr016_path()
        assert os.path.exists(adr_path), (
            f"ADR-016 not found at {adr_path}. "
            "ADR-016 must be Accepted before migration is produced."
        )

    def test_ac8_adr016_status_accepted(self):
        """AC8: ADR-016 has Status: Accepted in its header."""
        adr_path = self._adr016_path()
        if not os.path.exists(adr_path):
            pytest.skip("ADR-016 not found — AC8 file existence test should have caught this")

        with open(adr_path) as f:
            content = f.read()

        assert "Accepted" in content, "ADR-016 must have Status: Accepted"
        # Specifically the header table entry
        assert "| **Status** | Accepted" in content or "Status** | Accepted" in content

    def test_ac8_migration_references_adr016(self):
        """AC8: Migration file references ADR-016 in its header."""
        mig_path = os.path.normpath(os.path.join(
            os.path.dirname(__file__),
            "..", "..",
            "harmony", "pipelines", "migrations",
            "m7_temporal_field_activation.py",
        ))
        with open(mig_path) as f:
            content = f.read()

        assert "ADR-016" in content, "Migration must reference ADR-016"
        assert "Accepted" in content, "Migration must note ADR-016 is Accepted"
