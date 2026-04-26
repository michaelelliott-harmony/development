# Tests for D3: Permit-to-Cell Resolver
#
# Covers: all four resolution paths (spatial, lot/plan, address, unresolved),
#         batch resolution, and integration with the adapter interface.

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from harmony.pipelines.temporal.models import (
    EventType,
    PermitRecord,
    ResolutionMethod,
    UnresolvedPermit,
)
from harmony.pipelines.temporal.adapter import NSWPlanningPortalAdapter
from harmony.pipelines.temporal.resolver import (
    PermitCellResolver,
    _build_lot_plan_key,
    _derive_cell_key_from_latlon,
)


# ---------------------------------------------------------------------------
# Helper: build a minimal PermitRecord
# ---------------------------------------------------------------------------

def _da_record(
    permit_id="DA/2026/TEST",
    status="Under Assessment",
    full_address=None,
    lot=None,
    plan=None,
    x=None,
    y=None,
):
    return PermitRecord(
        permit_id=permit_id,
        permit_source="nsw_planning_portal",
        permit_type="da",
        application_status=status,
        event_date=date(2026, 1, 1),
        full_address=full_address,
        lot_number=lot,
        plan_label=plan,
        x_coord=x,
        y_coord=y,
    )


def _oc_record(permit_id="OC/2026/TEST", x=151.3411, y=-33.4234, lot=None, plan=None):
    return PermitRecord(
        permit_id=permit_id,
        permit_source="nsw_planning_portal",
        permit_type="oc",
        application_status="Issued",
        event_date=date(2026, 3, 15),
        x_coord=x,
        y_coord=y,
        lot_number=lot,
        plan_label=plan,
    )


# ---------------------------------------------------------------------------
# Lot/plan key builder
# ---------------------------------------------------------------------------

class TestBuildLotPlanKey:
    def test_standard_dp_plan(self):
        key = _build_lot_plan_key("1", "DP787786")
        assert key == "Lot 1 DP787786"

    def test_sp_plan(self):
        key = _build_lot_plan_key("42", "SP99887")
        assert key == "Lot 42 SP99887"

    def test_none_lot_returns_none(self):
        assert _build_lot_plan_key(None, "DP123456") is None

    def test_none_plan_returns_none(self):
        assert _build_lot_plan_key("1", None) is None

    def test_both_none_returns_none(self):
        assert _build_lot_plan_key(None, None) is None

    def test_malformed_plan_returns_fallback(self):
        """Non-standard plan label falls back to the raw label."""
        key = _build_lot_plan_key("5", "CUSTOM-PLAN")
        assert key is not None  # Returns fallback, not None


# ---------------------------------------------------------------------------
# Resolution hierarchy — Level 1: Spatial
# ---------------------------------------------------------------------------

class TestSpatialResolution:
    def test_oc_with_xy_resolves_via_spatial(self):
        """CC/OC records with X/Y should resolve via spatial path."""
        resolver = PermitCellResolver(p1_url="http://p1-stub")
        adapter = NSWPlanningPortalAdapter()

        record = _oc_record(x=151.3411, y=-33.4234)
        expected_key = "hsam:r10:cc:testcell1234567"

        with patch(
            "harmony.pipelines.temporal.resolver._derive_cell_key_from_latlon",
            return_value=expected_key,
        ):
            cell_keys, method = resolver._resolve_one(record, adapter)

        assert method == ResolutionMethod.SPATIAL
        assert expected_key in cell_keys

    def test_record_without_xy_skips_spatial(self):
        """DA records without X/Y do not attempt spatial resolution."""
        resolver = PermitCellResolver(p1_url="http://p1-stub")
        adapter = NSWPlanningPortalAdapter()
        record = _da_record(full_address="88 Mann Street Gosford")

        # Pre-populate cache so get_permit_address returns the address
        adapter._record_cache[record.permit_id] = {
            "PlanningPortalApplicationNumber": record.permit_id,
            "FullAddress": "88 Mann Street Gosford",
        }

        derive_called = []
        with patch(
            "harmony.pipelines.temporal.resolver._derive_cell_key_from_latlon",
            side_effect=lambda *a, **kw: derive_called.append(True) or None,
        ):
            with patch(
                "harmony.pipelines.temporal.resolver._query_entities_by_address",
                return_value=["hsam:r10:cc:foundbyaddress123"],
            ):
                cell_keys, method = resolver._resolve_one(record, adapter)

        # Spatial resolution not called — DA has no X/Y
        assert len(derive_called) == 0
        assert method == ResolutionMethod.ADDRESS


# ---------------------------------------------------------------------------
# Resolution hierarchy — Level 2: Lot/Plan
# ---------------------------------------------------------------------------

class TestLotPlanResolution:
    def test_lot_plan_resolves_when_spatial_fails(self):
        """Falls back to lot/plan matching when no X/Y is available."""
        resolver = PermitCellResolver(p1_url="http://p1-stub")
        adapter = NSWPlanningPortalAdapter()
        record = _da_record(lot="1", plan="DP787786")

        with patch(
            "harmony.pipelines.temporal.resolver._query_entities_by_lot_plan",
            return_value=["hsam:r10:cc:lotplanresolved123"],
        ):
            cell_keys, method = resolver._resolve_one(record, adapter)

        assert method == ResolutionMethod.LOT_PLAN
        assert "hsam:r10:cc:lotplanresolved123" in cell_keys


# ---------------------------------------------------------------------------
# Resolution hierarchy — Level 3: Address
# ---------------------------------------------------------------------------

class TestAddressResolution:
    def test_address_resolution_when_lot_plan_fails(self):
        """Falls back to address matching when lot/plan resolution finds nothing."""
        resolver = PermitCellResolver(p1_url="http://p1-stub")
        adapter = NSWPlanningPortalAdapter()
        adapter._record_cache["DA/2026/TEST"] = {
            "PlanningPortalApplicationNumber": "DA/2026/TEST",
            "FullAddress": "88 Mann Street, Gosford NSW 2250",
        }
        record = _da_record(full_address="88 Mann Street, Gosford NSW 2250")

        with patch(
            "harmony.pipelines.temporal.resolver._query_entities_by_lot_plan",
            return_value=[],
        ):
            with patch(
                "harmony.pipelines.temporal.resolver._query_entities_by_address",
                return_value=["hsam:r10:cc:addrresolved1234"],
            ):
                cell_keys, method = resolver._resolve_one(record, adapter)

        assert method == ResolutionMethod.ADDRESS
        assert "hsam:r10:cc:addrresolved1234" in cell_keys


# ---------------------------------------------------------------------------
# Resolution hierarchy — Level 4: Unresolved
# ---------------------------------------------------------------------------

class TestUnresolvedResolution:
    def test_unresolved_when_all_paths_fail(self):
        """Permit is marked unresolved when spatial, lot/plan, and address all fail."""
        resolver = PermitCellResolver(p1_url="http://p1-stub")
        adapter = NSWPlanningPortalAdapter()
        record = _da_record()  # No address, no lot, no XY

        with patch(
            "harmony.pipelines.temporal.resolver._query_entities_by_lot_plan",
            return_value=[],
        ):
            with patch(
                "harmony.pipelines.temporal.resolver._query_entities_by_address",
                return_value=[],
            ):
                cell_keys, method = resolver._resolve_one(record, adapter)

        assert method == ResolutionMethod.UNRESOLVED
        assert cell_keys == []


# ---------------------------------------------------------------------------
# Batch resolution
# ---------------------------------------------------------------------------

class TestBatchResolution:
    def test_batch_separates_resolved_and_unresolved(self):
        """resolve_batch returns both resolved events and unresolved permits."""
        resolver = PermitCellResolver(p1_url="http://p1-stub")
        adapter = NSWPlanningPortalAdapter()

        resolved_record = _oc_record(x=151.34, y=-33.42)
        unresolved_record = _da_record(permit_id="DA/2026/NORESOLUTION")

        with patch(
            "harmony.pipelines.temporal.resolver._derive_cell_key_from_latlon",
            return_value="hsam:r10:cc:spatialkey1234567",
        ):
            with patch(
                "harmony.pipelines.temporal.resolver._query_entities_by_lot_plan",
                return_value=[],
            ):
                with patch(
                    "harmony.pipelines.temporal.resolver._query_entities_by_address",
                    return_value=[],
                ):
                    resolved, unresolved = resolver.resolve_batch(
                        [resolved_record, unresolved_record], adapter
                    )

        assert len(resolved) == 1
        assert len(unresolved) == 1
        assert resolved[0].permit.permit_id == "OC/2026/TEST"
        assert unresolved[0].permit.permit_id == "DA/2026/NORESOLUTION"

    def test_batch_skips_non_event_permits(self):
        """Permits with no state machine event type (Determined DAs) are skipped."""
        resolver = PermitCellResolver(p1_url="http://p1-stub")
        adapter = NSWPlanningPortalAdapter()

        determined_record = PermitRecord(
            permit_id="DA/2026/DETERMINED",
            permit_source="nsw_planning_portal",
            permit_type="da",
            application_status="Determined",
            event_date=date(2026, 1, 1),
        )

        resolved, unresolved = resolver.resolve_batch([determined_record], adapter)

        assert len(resolved) == 0
        assert len(unresolved) == 0

    def test_resolved_event_carries_event_type(self):
        """Resolved PermitEvent has the correct event_type from classification."""
        resolver = PermitCellResolver(p1_url="http://p1-stub")
        adapter = NSWPlanningPortalAdapter()

        oc = _oc_record(x=151.34, y=-33.42)

        with patch(
            "harmony.pipelines.temporal.resolver._derive_cell_key_from_latlon",
            return_value="hsam:r10:cc:spatialkey1234567",
        ):
            resolved, _ = resolver.resolve_batch([oc], adapter)

        assert len(resolved) == 1
        assert resolved[0].event_type == EventType.OC_ISSUED
