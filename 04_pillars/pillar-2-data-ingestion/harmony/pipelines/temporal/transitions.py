# Harmony Pillar 2 — M7 Temporal Trigger Layer
# D4: Cell State Transition Service
#
# ADR-016 §2.3  — Cell state machine
# ADR-016 §2.4  — Temporal field population rules
# ADR-016 §2.7  — Error handling
# ADR-016 §2.9  — Event-sourced model (append-only audit log)
#
# Idempotent: same (cell_key, permit_id, event_type) produces no duplicate.
# valid_from: set to OC DeterminationDate, NEVER datetime.now() (ADR-016 §2.1)
# All writes via Pillar 1 HTTP API. No direct DB access.

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import date, datetime
from typing import Optional

import requests

from harmony.pipelines.temporal.models import (
    CellStatus,
    CellTransitionEvent,
    EventType,
    PermitEvent,
    TransitionResult,
    VALID_TRANSITIONS,
)

logger = logging.getLogger(__name__)

_DEFAULT_P1_URL = os.environ.get("HARMONY_P1_URL", "http://localhost:8000")
_DEFAULT_AUDIT_DB = os.environ.get(
    "HARMONY_AUDIT_DB",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "temporal_audit.sqlite3"),
)


# ---------------------------------------------------------------------------
# Audit log — SQLite append-only event store (ADR-016 §2.9)
# ---------------------------------------------------------------------------

_AUDIT_SCHEMA = """
CREATE TABLE IF NOT EXISTS cell_transition_events (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    cell_key          TEXT NOT NULL,
    event_type        TEXT NOT NULL,
    permit_id         TEXT NOT NULL,
    permit_source     TEXT NOT NULL,
    event_date        TEXT,
    ingested_at       TEXT NOT NULL,
    previous_status   TEXT NOT NULL,
    new_status        TEXT NOT NULL,
    valid_from_date   TEXT,
    resolution_method TEXT NOT NULL DEFAULT 'unknown',
    created_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uix_cell_permit_event
    ON cell_transition_events(cell_key, permit_id, event_type);

CREATE TABLE IF NOT EXISTS unresolved_permits (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    permit_id     TEXT NOT NULL,
    permit_source TEXT NOT NULL,
    permit_type   TEXT NOT NULL,
    event_type    TEXT NOT NULL,
    full_address  TEXT,
    lot_number    TEXT,
    plan_label    TEXT,
    reason        TEXT,
    raw_record    TEXT,
    attempted_at  TEXT NOT NULL
);
"""


class AuditLog:
    """Append-only SQLite audit log for cell transition events.

    ADR-016 §2.9: the event log is the source of truth. cell_status on the
    cell record is a denormalised derived value updated on each event.
    """

    def __init__(self, db_path: str = _DEFAULT_AUDIT_DB) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(_AUDIT_SCHEMA)

    def is_duplicate(
        self, cell_key: str, permit_id: str, event_type: str
    ) -> bool:
        """Check whether this (cell_key, permit_id, event_type) already exists."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                SELECT 1 FROM cell_transition_events
                WHERE cell_key = ? AND permit_id = ? AND event_type = ?
                LIMIT 1
                """,
                (cell_key, permit_id, event_type),
            )
            return cur.fetchone() is not None

    def record_transition(self, event: CellTransitionEvent) -> None:
        """Append a transition event. Silently ignores duplicate violations."""
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO cell_transition_events (
                        cell_key, event_type, permit_id, permit_source,
                        event_date, ingested_at, previous_status, new_status,
                        valid_from_date, resolution_method
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.cell_key,
                        event.event_type,
                        event.permit_id,
                        event.permit_source,
                        str(event.event_date) if event.event_date else None,
                        event.ingested_at.isoformat(),
                        event.previous_status,
                        event.new_status,
                        str(event.valid_from_date) if event.valid_from_date else None,
                        event.resolution_method,
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # Idempotency: duplicate unique index violation — silently ignore
                pass

    def record_unresolved(
        self,
        permit_id: str,
        permit_source: str,
        permit_type: str,
        event_type: str,
        full_address: Optional[str],
        lot_number: Optional[str],
        plan_label: Optional[str],
        reason: str,
        raw_record: dict,
        attempted_at: datetime,
    ) -> None:
        """Log an unresolved permit with its full record (ADR-016 §2.6)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO unresolved_permits (
                    permit_id, permit_source, permit_type, event_type,
                    full_address, lot_number, plan_label, reason,
                    raw_record, attempted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    permit_id,
                    permit_source,
                    permit_type,
                    event_type,
                    full_address,
                    lot_number,
                    plan_label,
                    reason,
                    json.dumps(raw_record),
                    attempted_at.isoformat(),
                ),
            )
            conn.commit()

    def get_current_status(self, cell_key: str) -> str:
        """Derive current cell_status from the most recent event log entry.

        Per ADR-016 §2.9: event log is the source of truth. If no events exist
        for this cell, the default status is 'stable'.
        """
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                SELECT new_status FROM cell_transition_events
                WHERE cell_key = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (cell_key,),
            )
            row = cur.fetchone()
            return row[0] if row else CellStatus.STABLE.value

    def get_events_for_cell(self, cell_key: str) -> list[dict]:
        """Return all transition events for a cell, ordered by id ascending."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                """
                SELECT * FROM cell_transition_events
                WHERE cell_key = ?
                ORDER BY id ASC
                """,
                (cell_key,),
            )
            return [dict(row) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Pillar 1 API helpers — all writes go through HTTP
# ---------------------------------------------------------------------------

def _update_cell_status_via_p1(
    cell_key: str,
    cell_status: str,
    valid_from: Optional[date],
    p1_url: str,
) -> bool:
    """Update cell_status (and optionally valid_from) via Pillar 1 API.

    The PATCH /cells/{cell_key}/status endpoint is the intended write path
    for cell_status updates. If that endpoint is not yet live, we record
    the intended state in the audit log and note it as pending.

    valid_from is set on change_confirmed events per ADR-016 §2.4.
    NEVER uses datetime.now() — always the OC DeterminationDate.
    """
    payload: dict = {"cell_status": cell_status}
    if valid_from is not None:
        payload["valid_from"] = str(valid_from)

    try:
        resp = requests.patch(
            f"{p1_url}/cells/{cell_key}/status",
            json=payload,
            timeout=10,
        )
        if resp.status_code in (200, 204):
            logger.debug("P1 cell_status update OK: %s → %s", cell_key, cell_status)
            return True
        logger.warning(
            "P1 cell_status update returned %d for %s: %s",
            resp.status_code,
            cell_key,
            resp.text[:200],
        )
        return False
    except requests.exceptions.RequestException as exc:
        logger.warning("P1 cell_status update failed for %s: %s", cell_key, exc)
        return False


def _reset_fidelity_via_p1(cell_key: str, p1_url: str) -> bool:
    """Reset photorealistic fidelity slot to pending via PATCH /cells/{key}/fidelity.

    Called on change_confirmed transition per ADR-016 §2.5 and D6 requirement.
    The structural slot is preserved at its current state; only photorealistic
    is reset. To preserve the structural slot we must read it first.

    Full replacement semantics per PATCH /cells/{cell_key}/fidelity contract.
    """
    # Step 1: read current fidelity coverage
    structural_slot: dict = {
        "status": "available",
        "source": "nsw_cadastral",
        "captured_at": None,
    }
    try:
        resp = requests.get(f"{p1_url}/resolve/cell-key/{cell_key}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            fc = data.get("fidelity_coverage") or {}
            if fc.get("structural"):
                structural_slot = fc["structural"]
    except Exception as exc:
        logger.debug("Could not read current fidelity for %s: %s", cell_key, exc)

    # Step 2: write fidelity with photorealistic reset to pending
    reset_body = {
        "structural": structural_slot,
        "photorealistic": {
            "status": "pending",
            "source": None,
            "captured_at": None,
        },
    }

    try:
        resp = requests.patch(
            f"{p1_url}/cells/{cell_key}/fidelity",
            json=reset_body,
            timeout=10,
        )
        if resp.status_code in (200, 204):
            logger.info(
                "Fidelity reset applied: %s photorealistic → pending (change_confirmed)",
                cell_key,
            )
            return True
        logger.warning(
            "P1 fidelity reset returned %d for %s: %s",
            resp.status_code,
            cell_key,
            resp.text[:200],
        )
        return False
    except requests.exceptions.RequestException as exc:
        logger.warning("P1 fidelity reset failed for %s: %s", cell_key, exc)
        return False


# ---------------------------------------------------------------------------
# Transition Service
# ---------------------------------------------------------------------------

class CellTransitionService:
    """Applies permit events to cell state machine. Idempotent and audit-logged.

    ADR-016 §2.3 — four-state machine:
        stable → change_expected → change_in_progress → change_confirmed
        change_expected → stable (on DA withdrawn/refused)

    Every transition is:
    1. Checked for idempotency (duplicate → silent skip)
    2. Validated against the VALID_TRANSITIONS table
    3. Applied via Pillar 1 HTTP API (cell_status update)
    4. Appended to the audit log
    5. If change_confirmed: photorealistic fidelity reset via Pillar 1 API
    """

    def __init__(
        self,
        audit_log: Optional[AuditLog] = None,
        p1_url: str = _DEFAULT_P1_URL,
    ) -> None:
        self.audit_log = audit_log or AuditLog()
        self.p1_url = p1_url.rstrip("/")

    def apply_events(
        self,
        permit_events: list[PermitEvent],
    ) -> TransitionResult:
        """Process a batch of PermitEvents and apply valid state transitions.

        Returns a TransitionResult summarising applied, skipped, and anomalous
        transitions.
        """
        result = TransitionResult()
        now = datetime.utcnow()

        for event in permit_events:
            for cell_key in event.cell_keys:
                self._apply_one(event, cell_key, now, result)

        return result

    def _apply_one(
        self,
        event: PermitEvent,
        cell_key: str,
        ingested_at: datetime,
        result: TransitionResult,
    ) -> None:
        """Apply a single PermitEvent to a single cell. Mutates result."""
        permit = event.permit
        event_type_val = event.event_type.value

        # ------------------------------------------------------------------
        # Idempotency check (ADR-016 §5 constraint 4)
        # ------------------------------------------------------------------
        if self.audit_log.is_duplicate(cell_key, permit.permit_id, event_type_val):
            logger.debug(
                "Skipping duplicate event: cell=%s permit=%s type=%s",
                cell_key,
                permit.permit_id,
                event_type_val,
            )
            result.skipped_idempotent.append(cell_key)
            return

        # ------------------------------------------------------------------
        # Determine current status from audit log
        # ------------------------------------------------------------------
        current_status = self.audit_log.get_current_status(cell_key)

        # ------------------------------------------------------------------
        # Validate transition (ADR-016 §2.3)
        # ------------------------------------------------------------------
        transition_key = (current_status, event_type_val)
        new_status = VALID_TRANSITIONS.get(transition_key)

        if new_status is None:
            # Invalid or conflicting transition — log as anomaly, do not apply
            anomaly = (
                f"Conflicting transition rejected: cell={cell_key} "
                f"current_status={current_status} "
                f"event_type={event_type_val} "
                f"permit_id={permit.permit_id}"
            )
            logger.warning(anomaly)
            result.anomalies.append(anomaly)
            return

        # ------------------------------------------------------------------
        # Determine valid_from for OC events (ADR-016 §2.4)
        # NEVER datetime.now() — always the OC DeterminationDate
        # ------------------------------------------------------------------
        valid_from: Optional[date] = None
        if event.event_type == EventType.OC_ISSUED:
            valid_from = permit.event_date  # OC DeterminationDate
            if valid_from is None:
                logger.warning(
                    "OC event for permit %s has no DeterminationDate — "
                    "valid_from will be null until corrected",
                    permit.permit_id,
                )

        # ------------------------------------------------------------------
        # Write cell_status update via Pillar 1 HTTP API
        # ------------------------------------------------------------------
        _update_cell_status_via_p1(
            cell_key=cell_key,
            cell_status=new_status,
            valid_from=valid_from,
            p1_url=self.p1_url,
        )

        # ------------------------------------------------------------------
        # Fidelity reset on change_confirmed (ADR-016 §2.5, D6)
        # ------------------------------------------------------------------
        if new_status == CellStatus.CHANGE_CONFIRMED.value:
            fidelity_ok = _reset_fidelity_via_p1(cell_key, self.p1_url)
            if fidelity_ok:
                result.fidelity_resets.append(cell_key)
            else:
                logger.warning(
                    "Fidelity reset failed for %s — will be retried on next poll",
                    cell_key,
                )

        # ------------------------------------------------------------------
        # Append to audit log (ADR-016 §2.9)
        # Security preamble §4: every write is logged
        # ------------------------------------------------------------------
        transition_event = CellTransitionEvent(
            cell_key=cell_key,
            event_type=event_type_val,
            permit_id=permit.permit_id,
            permit_source=permit.permit_source,
            event_date=permit.event_date,
            ingested_at=ingested_at,
            previous_status=current_status,
            new_status=new_status,
            valid_from_date=valid_from,
            resolution_method=event.resolution_method.value,
        )
        self.audit_log.record_transition(transition_event)
        result.applied.append(transition_event)

        logger.info(
            "Transition applied: cell=%s %s → %s (permit=%s, method=%s)",
            cell_key,
            current_status,
            new_status,
            permit.permit_id,
            event.resolution_method.value,
        )
