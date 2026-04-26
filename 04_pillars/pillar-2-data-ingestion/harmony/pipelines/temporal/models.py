# Harmony Pillar 2 — M7 Temporal Trigger Layer
# Internal data models shared across adapter, resolver, and transition service.
#
# ADR-016 §2.8 — PermitSourceAdapter interface
# ADR-016 §2.9 — Event-sourced model
# Security preamble v1.0 — no secrets in models

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class EventType(str, Enum):
    DA_LODGED = "da_lodged"
    DA_WITHDRAWN = "da_withdrawn"
    DA_REFUSED = "da_refused"
    CC_ISSUED = "cc_issued"
    OC_ISSUED = "oc_issued"


class CellStatus(str, Enum):
    STABLE = "stable"
    CHANGE_EXPECTED = "change_expected"
    CHANGE_IN_PROGRESS = "change_in_progress"
    CHANGE_CONFIRMED = "change_confirmed"


class ResolutionMethod(str, Enum):
    SPATIAL = "spatial"
    LOT_PLAN = "lot_plan"
    ADDRESS = "address"
    UNRESOLVED = "unresolved"


# ---------------------------------------------------------------------------
# Raw permit record — normalised output from any PermitSourceAdapter
# ---------------------------------------------------------------------------

@dataclass
class PermitRecord:
    """A normalised permit record from any source adapter.

    NSW-specific fields are mapped to these canonical names during adapter
    normalisation. The resolver and transition service consume this type only;
    they are agnostic to the originating adapter.

    ADR-016 §2.8 — jurisdiction-agnostic event format.
    """
    permit_id: str                          # Unique identifier (e.g. DA/2026/0142)
    permit_source: str                      # Adapter identifier (e.g. nsw_planning_portal)
    permit_type: str                        # da | cdc | cc | oc
    application_status: str                 # Raw status string from source
    event_date: Optional[date]              # LodgementDate or DeterminationDate
    full_address: Optional[str] = None      # Street address (DA only)
    lot_number: Optional[str] = None        # Lot reference
    plan_label: Optional[str] = None        # Plan label (e.g. DP787786)
    x_coord: Optional[float] = None         # Easting (CC/OC, WGS84-approximated)
    y_coord: Optional[float] = None         # Northing (CC/OC, WGS84-approximated)
    raw_record: dict = field(default_factory=dict)  # Full source record for audit


# ---------------------------------------------------------------------------
# Resolved permit event — after permit-to-cell resolution
# ---------------------------------------------------------------------------

@dataclass
class PermitEvent:
    """A permit record that has been resolved to one or more Harmony cells.

    This is the unit the transition service consumes. The cell_keys list may
    contain 1..N cells. resolution_method records how the cell was found.

    ADR-016 §2.9 — event log entry structure.
    """
    permit: PermitRecord
    event_type: EventType
    cell_keys: list[str]                    # Resolved Harmony cell keys
    resolution_method: ResolutionMethod
    ingested_at: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Cell transition event — persisted to the append-only audit log
# ---------------------------------------------------------------------------

@dataclass
class CellTransitionEvent:
    """An individual cell state transition, as logged to the audit trail.

    ADR-016 §2.9 — append-only event log schema. The cell_status field on
    the cell record is a denormalised derived value; this log is the source
    of truth.
    """
    cell_key: str
    event_type: str                         # EventType string value
    permit_id: str
    permit_source: str
    event_date: Optional[date]
    ingested_at: datetime
    previous_status: str                    # CellStatus string value
    new_status: str                         # CellStatus string value
    valid_from_date: Optional[date] = None  # Set on oc_issued events (ADR-016 §2.4)
    resolution_method: str = "unknown"


# ---------------------------------------------------------------------------
# Unresolved permit — logged to audit trail when all resolution paths fail
# ---------------------------------------------------------------------------

@dataclass
class UnresolvedPermit:
    """A permit record that could not be resolved to any Harmony cell.

    Per ADR-016 §2.6: never discarded. Logged with the full permit record
    so it can be resolved after additional data is ingested.
    """
    permit: PermitRecord
    event_type: EventType
    attempted_at: datetime = field(default_factory=datetime.utcnow)
    reason: str = ""


# ---------------------------------------------------------------------------
# Transition result — returned by the transition service
# ---------------------------------------------------------------------------

@dataclass
class TransitionResult:
    applied: list[CellTransitionEvent] = field(default_factory=list)
    skipped_idempotent: list[str] = field(default_factory=list)  # cell_keys
    anomalies: list[str] = field(default_factory=list)           # descriptions
    fidelity_resets: list[str] = field(default_factory=list)     # cell_keys reset


# ---------------------------------------------------------------------------
# Valid state machine transitions (ADR-016 §2.3)
# ---------------------------------------------------------------------------

# Maps (current_status, event_type) → new_status
# Conflicting or undefined transitions are rejected as anomalies.
VALID_TRANSITIONS: dict[tuple[str, str], str] = {
    (CellStatus.STABLE.value,              EventType.DA_LODGED.value):    CellStatus.CHANGE_EXPECTED.value,
    (CellStatus.CHANGE_EXPECTED.value,     EventType.DA_WITHDRAWN.value): CellStatus.STABLE.value,
    (CellStatus.CHANGE_EXPECTED.value,     EventType.DA_REFUSED.value):   CellStatus.STABLE.value,
    (CellStatus.CHANGE_EXPECTED.value,     EventType.CC_ISSUED.value):    CellStatus.CHANGE_IN_PROGRESS.value,
    (CellStatus.CHANGE_IN_PROGRESS.value,  EventType.OC_ISSUED.value):    CellStatus.CHANGE_CONFIRMED.value,
}
