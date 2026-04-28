# Test fixtures and shared configuration for M7 temporal trigger tests.
#
# All tests work against the structured Gosford DA fixture (fixtures/gosford_da_fixture.json)
# and an in-memory SQLite audit log. No live API calls required in unit tests.
# AC1 (live connectivity) is tested separately in test_acceptance.py and is
# marked as requiring network access.

import json
import os
import sys
import tempfile
from datetime import date
from typing import Optional

import pytest

# Ensure the pipelines package is on the path
_P2_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _P2_ROOT not in sys.path:
    sys.path.insert(0, _P2_ROOT)

from harmony.pipelines.temporal.models import (
    CellStatus,
    EventType,
    PermitRecord,
    ResolutionMethod,
)
from harmony.pipelines.temporal.adapter import NSWPlanningPortalAdapter
from harmony.pipelines.temporal.transitions import AuditLog, CellTransitionService


# ---------------------------------------------------------------------------
# Fixture: load Gosford DA fixture data
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def gosford_fixture() -> dict:
    fixture_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "fixtures", "gosford_da_fixture.json"
    )
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def gosford_da_record(gosford_fixture) -> dict:
    """The Mann Street Gosford DA record — primary Gosford test case."""
    return gosford_fixture["da_records"][0]


@pytest.fixture(scope="session")
def gosford_cc_record(gosford_fixture) -> dict:
    return gosford_fixture["cc_records"][0]


@pytest.fixture(scope="session")
def gosford_oc_record(gosford_fixture) -> dict:
    return gosford_fixture["oc_records"][0]


# ---------------------------------------------------------------------------
# Fixture: in-memory audit log for isolated test runs
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_audit_log(tmp_path) -> AuditLog:
    """An AuditLog backed by a temporary file. Isolated per test."""
    db_path = str(tmp_path / "test_audit.sqlite3")
    return AuditLog(db_path=db_path)


# ---------------------------------------------------------------------------
# Fixture: transition service with no live Pillar 1 (offline mode)
# ---------------------------------------------------------------------------

@pytest.fixture
def transition_service(temp_audit_log, monkeypatch) -> CellTransitionService:
    """A CellTransitionService with Pillar 1 API calls stubbed out."""
    monkeypatch.setattr(
        "harmony.pipelines.temporal.transitions._update_cell_status_via_p1",
        lambda cell_key, cell_status, valid_from, p1_url: True,
    )
    monkeypatch.setattr(
        "harmony.pipelines.temporal.transitions._reset_fidelity_via_p1",
        lambda cell_key, p1_url: True,
    )
    return CellTransitionService(
        audit_log=temp_audit_log,
        p1_url="http://p1-stub",
    )


# ---------------------------------------------------------------------------
# Helper: build a PermitRecord from a raw NSW API dict
# ---------------------------------------------------------------------------

def make_permit_record(raw: dict, permit_type: str) -> PermitRecord:
    adapter = NSWPlanningPortalAdapter()
    record = adapter._normalise(raw, permit_type)
    assert record is not None, f"Failed to normalise fixture record: {raw}"
    return record


# ---------------------------------------------------------------------------
# Fixture: canonical Gosford DA PermitRecord
# ---------------------------------------------------------------------------

@pytest.fixture
def gosford_da_permit(gosford_da_record) -> PermitRecord:
    return make_permit_record(gosford_da_record, "da")


@pytest.fixture
def gosford_cc_permit(gosford_cc_record) -> PermitRecord:
    return make_permit_record(gosford_cc_record, "cc")


@pytest.fixture
def gosford_oc_permit(gosford_oc_record) -> PermitRecord:
    return make_permit_record(gosford_oc_record, "oc")
