# Tests for D4: Cell State Transition Service
#
# Covers: all four state transitions, idempotency, anomaly detection,
#         valid_from population rule, fidelity reset trigger, audit log.

from datetime import date, datetime
from unittest.mock import patch

import pytest

from harmony.pipelines.temporal.models import (
    CellStatus,
    CellTransitionEvent,
    EventType,
    PermitEvent,
    PermitRecord,
    ResolutionMethod,
    VALID_TRANSITIONS,
)
from harmony.pipelines.temporal.transitions import AuditLog, CellTransitionService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CELL_KEY = "hsam:r10:cc:testcellkey12345"


def _permit(
    permit_id="DA/2026/TEST",
    permit_type="da",
    status="Under Assessment",
    event_date=None,
):
    return PermitRecord(
        permit_id=permit_id,
        permit_source="nsw_planning_portal",
        permit_type=permit_type,
        application_status=status,
        event_date=event_date or date(2026, 3, 1),
    )


def _event(permit, event_type, cell_keys=None):
    return PermitEvent(
        permit=permit,
        event_type=event_type,
        cell_keys=cell_keys or [CELL_KEY],
        resolution_method=ResolutionMethod.SPATIAL,
    )


# ---------------------------------------------------------------------------
# State machine transition table
# ---------------------------------------------------------------------------

class TestValidTransitionTable:
    def test_stable_plus_da_lodged_to_change_expected(self):
        assert VALID_TRANSITIONS[(CellStatus.STABLE.value, EventType.DA_LODGED.value)] \
            == CellStatus.CHANGE_EXPECTED.value

    def test_change_expected_plus_da_withdrawn_to_stable(self):
        assert VALID_TRANSITIONS[(CellStatus.CHANGE_EXPECTED.value, EventType.DA_WITHDRAWN.value)] \
            == CellStatus.STABLE.value

    def test_change_expected_plus_da_refused_to_stable(self):
        assert VALID_TRANSITIONS[(CellStatus.CHANGE_EXPECTED.value, EventType.DA_REFUSED.value)] \
            == CellStatus.STABLE.value

    def test_change_expected_plus_cc_issued_to_change_in_progress(self):
        assert VALID_TRANSITIONS[(CellStatus.CHANGE_EXPECTED.value, EventType.CC_ISSUED.value)] \
            == CellStatus.CHANGE_IN_PROGRESS.value

    def test_change_in_progress_plus_oc_issued_to_change_confirmed(self):
        assert VALID_TRANSITIONS[(CellStatus.CHANGE_IN_PROGRESS.value, EventType.OC_ISSUED.value)] \
            == CellStatus.CHANGE_CONFIRMED.value

    def test_no_direct_stable_to_oc(self):
        """There is no valid stable → change_confirmed shortcut."""
        assert (CellStatus.STABLE.value, EventType.OC_ISSUED.value) not in VALID_TRANSITIONS


# ---------------------------------------------------------------------------
# Transition 1: stable → change_expected (DA lodged)
# ---------------------------------------------------------------------------

class TestDALodgedTransition:
    def test_da_lodged_transitions_stable_to_change_expected(self, transition_service):
        permit = _permit(status="Under Assessment")
        event = _event(permit, EventType.DA_LODGED)

        result = transition_service.apply_events([event])

        assert len(result.applied) == 1
        applied = result.applied[0]
        assert applied.previous_status == CellStatus.STABLE.value
        assert applied.new_status == CellStatus.CHANGE_EXPECTED.value

    def test_da_lodged_new_status_in_audit_log(self, transition_service):
        permit = _permit(status="Under Assessment")
        event = _event(permit, EventType.DA_LODGED)

        transition_service.apply_events([event])

        current = transition_service.audit_log.get_current_status(CELL_KEY)
        assert current == CellStatus.CHANGE_EXPECTED.value


# ---------------------------------------------------------------------------
# Transition 2: change_expected → stable (DA withdrawn/refused)
# ---------------------------------------------------------------------------

class TestDAWithdrawnTransition:
    def test_da_withdrawn_transitions_change_expected_to_stable(self, transition_service):
        # Set cell to change_expected first
        da_permit = _permit(permit_id="DA/2026/W001", status="Under Assessment")
        transition_service.apply_events([_event(da_permit, EventType.DA_LODGED)])

        # Withdraw
        withdrawn_permit = _permit(permit_id="DA/2026/W001", status="Withdrawn")
        result = transition_service.apply_events([_event(withdrawn_permit, EventType.DA_WITHDRAWN)])

        assert len(result.applied) == 1
        assert result.applied[0].new_status == CellStatus.STABLE.value

    def test_da_refused_transitions_change_expected_to_stable(self, transition_service):
        da_permit = _permit(permit_id="DA/2026/R001", status="Under Assessment")
        transition_service.apply_events([_event(da_permit, EventType.DA_LODGED)])

        refused_permit = _permit(permit_id="DA/2026/R001", status="Refused")
        result = transition_service.apply_events([_event(refused_permit, EventType.DA_REFUSED)])

        assert len(result.applied) == 1
        assert result.applied[0].new_status == CellStatus.STABLE.value


# ---------------------------------------------------------------------------
# Transition 3: change_expected → change_in_progress (CC issued)
# ---------------------------------------------------------------------------

class TestCCIssuedTransition:
    def test_cc_issued_transitions_to_change_in_progress(self, transition_service):
        da = _permit(permit_id="DA/2026/P001", status="Under Assessment")
        transition_service.apply_events([_event(da, EventType.DA_LODGED)])

        cc = _permit(permit_id="CC/2026/P001", permit_type="cc", status="Issued")
        result = transition_service.apply_events([_event(cc, EventType.CC_ISSUED)])

        assert len(result.applied) == 1
        assert result.applied[0].previous_status == CellStatus.CHANGE_EXPECTED.value
        assert result.applied[0].new_status == CellStatus.CHANGE_IN_PROGRESS.value


# ---------------------------------------------------------------------------
# Transition 4: change_in_progress → change_confirmed (OC issued)
# ---------------------------------------------------------------------------

class TestOCIssuedTransition:
    def _setup_cell_in_progress(self, service):
        da = _permit(permit_id="DA/2026/O001", status="Under Assessment")
        service.apply_events([_event(da, EventType.DA_LODGED)])
        cc = _permit(permit_id="CC/2026/O001", permit_type="cc", status="Issued")
        service.apply_events([_event(cc, EventType.CC_ISSUED)])

    def test_oc_issued_transitions_to_change_confirmed(self, transition_service):
        self._setup_cell_in_progress(transition_service)

        oc_date = date(2026, 4, 15)
        oc = _permit(
            permit_id="OC/2026/O001",
            permit_type="oc",
            status="Issued",
            event_date=oc_date,
        )
        result = transition_service.apply_events([_event(oc, EventType.OC_ISSUED)])

        assert len(result.applied) == 1
        applied = result.applied[0]
        assert applied.previous_status == CellStatus.CHANGE_IN_PROGRESS.value
        assert applied.new_status == CellStatus.CHANGE_CONFIRMED.value

    def test_valid_from_set_to_oc_determination_date_not_now(self, transition_service):
        """AC4: valid_from = OC DeterminationDate, NEVER datetime.now()."""
        self._setup_cell_in_progress(transition_service)

        oc_determination_date = date(2025, 12, 22)  # Historical date — proves it's not now()
        oc = _permit(
            permit_id="OC/2026/O001",
            permit_type="oc",
            status="Issued",
            event_date=oc_determination_date,
        )
        result = transition_service.apply_events([_event(oc, EventType.OC_ISSUED)])

        assert len(result.applied) == 1
        applied = result.applied[0]
        # valid_from must be the OC DeterminationDate, not today
        assert applied.valid_from_date == oc_determination_date
        assert applied.valid_from_date != date.today()

    def test_fidelity_reset_triggered_on_change_confirmed(self, transition_service):
        """AC5: photorealistic.status = pending after change_confirmed."""
        self._setup_cell_in_progress(transition_service)

        oc = _permit(
            permit_id="OC/2026/O001",
            permit_type="oc",
            status="Issued",
            event_date=date(2026, 4, 15),
        )
        result = transition_service.apply_events([_event(oc, EventType.OC_ISSUED)])

        # The fidelity reset is triggered (mocked in the fixture to return True)
        assert CELL_KEY in result.fidelity_resets

    def test_non_oc_event_does_not_set_valid_from(self, transition_service):
        """valid_from is null for non-OC events."""
        da = _permit(permit_id="DA/2026/VF001", status="Under Assessment")
        result = transition_service.apply_events([_event(da, EventType.DA_LODGED)])

        assert len(result.applied) == 1
        assert result.applied[0].valid_from_date is None


# ---------------------------------------------------------------------------
# Idempotency (AC6)
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_same_event_twice_produces_no_duplicate_transition(self, transition_service):
        """AC6: Applying the same event twice must not create a second transition."""
        permit = _permit(permit_id="DA/2026/IDEM001", status="Under Assessment")
        event = _event(permit, EventType.DA_LODGED)

        result1 = transition_service.apply_events([event])
        result2 = transition_service.apply_events([event])

        assert len(result1.applied) == 1
        assert len(result2.applied) == 0
        assert CELL_KEY in result2.skipped_idempotent

    def test_idempotent_skip_does_not_change_state(self, transition_service):
        """After a duplicate, the cell status remains as set by the first application."""
        permit = _permit(permit_id="DA/2026/IDEM002", status="Under Assessment")
        event = _event(permit, EventType.DA_LODGED)

        transition_service.apply_events([event])
        transition_service.apply_events([event])

        status = transition_service.audit_log.get_current_status(CELL_KEY)
        assert status == CellStatus.CHANGE_EXPECTED.value

    def test_same_event_three_times_still_idempotent(self, transition_service):
        """Idempotency holds for N applications."""
        permit = _permit(permit_id="DA/2026/IDEM003", status="Under Assessment")
        event = _event(permit, EventType.DA_LODGED)

        for _ in range(3):
            transition_service.apply_events([event])

        events = transition_service.audit_log.get_events_for_cell(CELL_KEY)
        assert len(events) == 1


# ---------------------------------------------------------------------------
# Anomaly handling
# ---------------------------------------------------------------------------

class TestAnomalyHandling:
    def test_conflicting_transition_logged_as_anomaly(self, transition_service):
        """ADR-016 §2.7: conflicting transitions are logged as anomalies, not applied."""
        # No prior transition — cell is in stable state
        # Attempting OC directly from stable (no valid transition) → anomaly
        oc = _permit(permit_id="OC/2026/ANOM001", permit_type="oc", status="Issued")
        result = transition_service.apply_events([_event(oc, EventType.OC_ISSUED)])

        assert len(result.applied) == 0
        assert len(result.anomalies) == 1
        assert "ANOM001" in result.anomalies[0] or CELL_KEY in result.anomalies[0]

    def test_anomaly_does_not_change_cell_status(self, transition_service):
        """Cell status remains stable when a conflicting transition is rejected."""
        oc = _permit(permit_id="OC/2026/ANOM002", permit_type="oc", status="Issued")
        transition_service.apply_events([_event(oc, EventType.OC_ISSUED)])

        status = transition_service.audit_log.get_current_status(CELL_KEY)
        assert status == CellStatus.STABLE.value


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

class TestAuditLog:
    def test_audit_log_records_all_transitions(self, transition_service):
        """All four transitions are recorded in the audit log."""
        cell = "hsam:r10:cc:auditlogtest12345"

        da = _permit(permit_id="DA/2026/A001", status="Under Assessment")
        cc = _permit(permit_id="CC/2026/A001", permit_type="cc", status="Issued")
        oc = _permit(permit_id="OC/2026/A001", permit_type="oc", status="Issued",
                     event_date=date(2026, 4, 20))

        transition_service.apply_events([_event(da, EventType.DA_LODGED, [cell])])
        transition_service.apply_events([_event(cc, EventType.CC_ISSUED, [cell])])
        transition_service.apply_events([_event(oc, EventType.OC_ISSUED, [cell])])

        events = transition_service.audit_log.get_events_for_cell(cell)
        assert len(events) == 3
        assert events[0]["new_status"] == CellStatus.CHANGE_EXPECTED.value
        assert events[1]["new_status"] == CellStatus.CHANGE_IN_PROGRESS.value
        assert events[2]["new_status"] == CellStatus.CHANGE_CONFIRMED.value

    def test_audit_log_records_permit_source(self, transition_service):
        """permit_source is recorded in the audit log entry."""
        permit = _permit(permit_id="DA/2026/SRC001", status="Under Assessment")
        transition_service.apply_events([_event(permit, EventType.DA_LODGED)])

        events = transition_service.audit_log.get_events_for_cell(CELL_KEY)
        assert events[0]["permit_source"] == "nsw_planning_portal"

    def test_audit_log_get_current_status_defaults_to_stable(self, temp_audit_log):
        """Cells with no events default to stable status."""
        status = temp_audit_log.get_current_status("hsam:r10:cc:newcell12345678")
        assert status == CellStatus.STABLE.value

    def test_duplicate_detection_works(self, temp_audit_log):
        """is_duplicate returns True for recorded events."""
        event = CellTransitionEvent(
            cell_key="hsam:r10:cc:dupcell1234567",
            event_type=EventType.DA_LODGED.value,
            permit_id="DA/2026/DUP001",
            permit_source="nsw_planning_portal",
            event_date=date(2026, 1, 1),
            ingested_at=datetime.utcnow(),
            previous_status=CellStatus.STABLE.value,
            new_status=CellStatus.CHANGE_EXPECTED.value,
        )
        temp_audit_log.record_transition(event)

        assert temp_audit_log.is_duplicate(
            "hsam:r10:cc:dupcell1234567",
            "DA/2026/DUP001",
            EventType.DA_LODGED.value,
        )

    def test_unresolved_permits_logged_not_discarded(self, temp_audit_log):
        """Unresolved permits are logged to the audit log (ADR-016 §2.6)."""
        temp_audit_log.record_unresolved(
            permit_id="DA/2026/UNRES001",
            permit_source="nsw_planning_portal",
            permit_type="da",
            event_type="da_lodged",
            full_address="Unknown Street, Unknown NSW",
            lot_number=None,
            plan_label=None,
            reason="All resolution methods exhausted",
            raw_record={"PlanningPortalApplicationNumber": "DA/2026/UNRES001"},
            attempted_at=datetime.utcnow(),
        )
        # Verify it was stored — check the DB directly
        import sqlite3
        with sqlite3.connect(temp_audit_log.db_path) as conn:
            cur = conn.execute(
                "SELECT permit_id FROM unresolved_permits WHERE permit_id = ?",
                ("DA/2026/UNRES001",),
            )
            row = cur.fetchone()
        assert row is not None
        assert row[0] == "DA/2026/UNRES001"
