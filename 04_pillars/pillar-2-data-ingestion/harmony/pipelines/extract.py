# Harmony Pillar 2 — Entity Extraction (Milestone 4)
#
# Converts validated, normalised features into Harmony entity payloads
# according to the dataset manifest's attribute mapping.
#
# Brief §8, Task 6: Entity extraction + known_names population.
# ADR-018: Every entity carries source_tier, source_id, confidence.
# DEC-013: Provenance fields are system-assigned by the adapter/extractor.
#
# Entity metadata carries all Pillar 2 domain attributes including
# fidelity_coverage (structural + photorealistic slots) since the current
# Pillar 1 API does not expose a write path for cell.fidelity_coverage.
# See: flag raised to Dr. Voss — PATCH /cells/{key}/fidelity needed.

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any

from harmony.pipelines.assign import CellAssignment
from harmony.pipelines.manifest import DatasetManifest
from harmony.pipelines.validate import ValidatedFeature

log = logging.getLogger(__name__)

# Common source field names carrying a per-feature date (ADR-024 §2.5, STD-V05)
_DATE_SOURCE_FIELDS = (
    "observation_date",
    "createdate",
    "start_date",
    "survey_date",
    "capture_date",
)


class ExtractionQuarantine(ValueError):
    """Raised by extract() when a feature must be quarantined rather than registered.

    Callers (runner.py) catch this, call quarantine.add(), and continue the pipeline.

    Attributes
    ----------
    quarantine_reason : str
        One of the six ADR-021 reason codes (Q1–Q6).
    message : str
        Human-readable explanation for the quarantine record.
    """

    def __init__(self, quarantine_reason: str, message: str) -> None:
        self.quarantine_reason = quarantine_reason
        super().__init__(f"{quarantine_reason}: {message}")


def extract(
    feature: ValidatedFeature,
    assignment: CellAssignment,
    manifest: DatasetManifest,
    run_id: str,
) -> dict:
    """Build the Harmony entity payload for a single feature.

    Parameters
    ----------
    feature : ValidatedFeature
        Validated, normalised feature from the pipeline.
    assignment : CellAssignment
        Primary + secondary cell coordinates from the cell assignment engine.
    manifest : DatasetManifest
        The dataset manifest governing this ingestion run.
    run_id : str
        Ingestion run identifier (for provenance).

    Returns
    -------
    dict
        A dict ready to pass to Pillar1Client.register_entity().
        Includes: entity_subtype, primary_cell_id, secondary_cell_ids,
        metadata (all domain attributes + provenance + fidelity_coverage),
        friendly_name, semantic_labels.
    """
    props = feature.get("properties") or {}
    entity_type = manifest.entity_type
    mapping = manifest.attribute_mapping

    # --- Map source attributes to Harmony domain fields ---
    domain_attrs: dict[str, Any] = {}
    for src_field, harmony_field in mapping.items():
        val = props.get(src_field)
        if val is not None:
            domain_attrs[harmony_field] = _coerce_value(harmony_field, val, entity_type)

    # --- Entity-type-specific post-processing ---
    if entity_type == "cadastral_lot":
        domain_attrs = _process_cadastral(domain_attrs, props)
    elif entity_type == "road_segment":
        domain_attrs = _process_road(domain_attrs, props)
    elif entity_type == "building":
        domain_attrs = _process_building(domain_attrs, props)

    # --- known_names ---
    known_names = _build_known_names(props, manifest, entity_type)

    # --- Change 1c (E1): known_names empty = validation failure ---
    # If the manifest declares name fields for this entity type but no names
    # could be populated from the feature, quarantine — cannot register a
    # nameless entity from a dataset that is supposed to carry names.
    if not known_names and manifest.known_names_fields:
        raise ExtractionQuarantine(
            "Q4_SCHEMA_VIOLATION",
            f"known_names is empty — mandatory name population failed for "
            f"entity_type={entity_type}",
        )

    # --- friendly_name ---
    friendly_name = _build_friendly_name(domain_attrs, entity_type)

    # --- semantic_labels ---
    semantic_labels = _build_semantic_labels(entity_type, domain_attrs)

    # --- Change 1b (STD-V05): valid_from mandatory when source carries feature date ---
    # ADR-024 §2.5: if manifest.carries_feature_dates is True, valid_from must be
    # populated from the source feature. Records without it go to quarantine Q4.
    valid_from: str | None = None
    if manifest.carries_feature_dates:
        valid_from = _get_valid_from(props, domain_attrs)
        if valid_from is None:
            raise ExtractionQuarantine(
                "Q4_SCHEMA_VIOLATION",
                "valid_from mandatory for date-carrying dataset but no date found in feature",
            )

    # --- Change 1a (STD-V01): source_lineage structured JSONB object ---
    # ADR-024 §2.1 / ISO 19115 ANZLIC lineage requirement.
    # Flat provenance fields (source_authority, source_dataset, ingested_at)
    # are retained during the migration window per ADR-024 §5.
    now_iso = datetime.now(timezone.utc).isoformat()
    source_lineage: dict[str, Any] = {
        "source_dataset_id": manifest.get("dataset_name", "unknown"),
        "source_dataset_date": manifest.get("source_dataset_date"),
        "source_organisation": manifest.source_authority,
        "source_licence": manifest.get("source_licence", "unknown"),
        "process_steps": [
            {
                "step_name": "ingest",
                "step_description": f"Harmony P2 ingestion run {run_id}",
                "step_datetime": now_iso,
            }
        ],
        "processing_organisation": "harmony",
        "processing_date": now_iso,
    }

    # --- Fidelity coverage (carried in entity metadata per current API gap) ---
    observation_date = domain_attrs.get("observation_date") or None
    captured_at = str(observation_date) if observation_date else None
    fidelity_coverage = {
        "structural": {
            "status": "available",
            "source": manifest.source_authority,
            "captured_at": captured_at,
        },
        "photorealistic": {
            "status": "pending",
            "source": None,
            "captured_at": None,
        },
    }

    # --- Full metadata for the entity record ---
    metadata: dict[str, Any] = {
        # Domain attributes
        **domain_attrs,
        # Provenance (DEC-013, ADR-018) — flat fields retained during migration window
        "source_tier": manifest.source_tier,
        "source_authority": manifest.source_authority,
        "source_dataset": manifest.get("dataset_name", "unknown"),
        "source_feature_id": feature.get("source_id"),
        "confidence": 1.0 if manifest.source_tier == 1 else 0.85,
        # ADR-024 §2.1 STD-V01: structured lineage JSONB object
        "source_lineage": source_lineage,
        # Geometry metadata
        "entity_type": entity_type,
        "fidelity_class": manifest.fidelity_class,
        "positional_accuracy_m": manifest.positional_accuracy_m,
        "geometry_wgs84": feature.get("geometry_wgs84"),
        "transformation_method": feature.get("transformation_method"),
        "crs_transform_epoch": feature.get("crs_transform_epoch"),
        # Fidelity coverage (stored here until Pillar 1 PATCH endpoint available)
        "fidelity_coverage": fidelity_coverage,
        # Cell assignment
        "resolution_level": assignment.resolution_level,
        "primary_cell_key": assignment.primary.cell_key,
        "secondary_cell_keys": [c.cell_key for c in assignment.secondary],
        "cell_assigned_by": assignment.assigned_by,
        # Ingestion provenance (flat, retained for backward compat)
        "schema_version": "1.0",
        "ingested_at": now_iso,
        "ingestion_run_id": run_id,
        # ADR-024 §2.5 STD-V05: valid_from (None when source has no per-feature dates)
        "valid_from": valid_from,
        # known_names mirrored here for queryability
        "known_names": known_names,
    }

    return {
        "entity_subtype": manifest.entity_subtype_code,
        "primary_cell_id": None,    # filled by runner after cell registration
        "secondary_cell_ids": [],   # filled by runner after cell registration
        "metadata": metadata,
        "friendly_name": friendly_name,
        "semantic_labels": semantic_labels,
        # known_names is passed to the alias registration step separately
        "_known_names": known_names,
        "_assignment": assignment,
    }


# ---------------------------------------------------------------------------
# Entity-type-specific processing
# ---------------------------------------------------------------------------

def _process_cadastral(attrs: dict, props: dict) -> dict:
    """Derive plan_type and plan_number from planlabel."""
    plan_label = attrs.get("plan_label") or props.get("planlabel") or ""
    if plan_label:
        # planlabel format: "{lot}//{plan_type}{plan_number}" e.g. "1//DP123456"
        parts = plan_label.replace("//", "/").split("/")
        plan_part = parts[-1] if parts else ""
        if plan_part:
            # Extract alphabetic prefix (plan_type) and numeric suffix (plan_number)
            i = 0
            while i < len(plan_part) and plan_part[i].isalpha():
                i += 1
            if i > 0:
                attrs["plan_type"] = plan_part[:i]
                attrs["plan_number"] = plan_part[i:] if i < len(plan_part) else ""
    return attrs


def _process_road(attrs: dict, props: dict) -> dict:
    """Normalise boolean OSM tags and parse speed limits."""
    for bool_field in ("is_oneway", "is_bridge", "is_tunnel", "is_lit"):
        val = attrs.get(bool_field)
        if val is not None:
            attrs[bool_field] = _osm_bool(val)

    # Parse speed limit (may include units like "50 mph" or just "60")
    speed = attrs.get("speed_limit_kmh")
    if speed is not None:
        attrs["speed_limit_kmh"] = _parse_speed(speed)

    # Parse lane count
    lanes = attrs.get("lane_count")
    if lanes is not None:
        try:
            attrs["lane_count"] = int(lanes)
        except (ValueError, TypeError):
            del attrs["lane_count"]

    return attrs


def _process_building(attrs: dict, props: dict) -> dict:
    """Parse building height and levels."""
    height = attrs.get("height_m")
    if height is not None:
        try:
            attrs["height_m"] = float(str(height).replace("m", "").strip())
        except (ValueError, TypeError):
            del attrs["height_m"]

    levels = attrs.get("levels")
    if levels is not None:
        try:
            attrs["levels"] = int(levels)
        except (ValueError, TypeError):
            del attrs["levels"]

    return attrs


def _osm_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).lower() in ("yes", "true", "1")


def _parse_speed(val: Any) -> int | None:
    try:
        s = str(val).lower().replace("km/h", "").replace("kph", "").strip()
        if "mph" in s:
            return int(float(s.replace("mph", "").strip()) * 1.60934)
        return int(float(s))
    except (ValueError, TypeError):
        return None


def _build_known_names(
    props: dict,
    manifest: DatasetManifest,
    entity_type: str,
) -> list[str]:
    """Build the known_names list from the source attributes."""
    names: list[str] = []

    for field in manifest.known_names_fields:
        val = props.get(field)
        if val and str(val).strip():
            name = str(val).strip()
            if name not in names:
                names.append(name)

    # Entity-type-specific derivations
    if entity_type == "cadastral_lot":
        lot = props.get("lotnumber")
        plan = props.get("planlabel", "")
        if lot and plan:
            # "Lot 1 DP123456" style
            parts = plan.replace("//", "/").split("/")
            plan_part = parts[-1] if parts else plan
            name = f"Lot {lot} {plan_part}"
            if name not in names:
                names.append(name)

    elif entity_type == "building":
        # "{number} {street}" combined address
        number = props.get("addr:housenumber", "")
        street = props.get("addr:street", "")
        if number and street:
            combined = f"{number} {street}".strip()
            if combined not in names:
                names.append(combined)

    return names


def _build_friendly_name(domain_attrs: dict, entity_type: str) -> str | None:
    """Build a human-readable friendly_name for the entity."""
    if entity_type == "zoning_area":
        code = domain_attrs.get("zone_code", "")
        name = domain_attrs.get("zone_name", "")
        if code and name:
            return f"{code} — {name}"
        return code or name or None

    if entity_type == "cadastral_lot":
        return domain_attrs.get("plan_label") or None

    if entity_type == "building":
        bname = domain_attrs.get("building_name")
        if bname:
            return str(bname)
        addr_n = domain_attrs.get("address_number", "")
        addr_s = domain_attrs.get("address_street", "")
        if addr_n and addr_s:
            return f"{addr_n} {addr_s}"
        return None

    if entity_type == "road_segment":
        name = domain_attrs.get("road_name")
        ref = domain_attrs.get("road_ref")
        road_class = domain_attrs.get("road_class", "")
        if name:
            return name
        if ref:
            return ref
        return road_class or None

    return None


def _build_semantic_labels(entity_type: str, domain_attrs: dict) -> list[str]:
    """Build semantic labels for the entity."""
    labels = [entity_type]

    if entity_type == "zoning_area":
        zone_code = domain_attrs.get("zone_code", "")
        if zone_code.startswith("R"):
            labels.append("residential_zone")
        elif zone_code.startswith("B") or zone_code.startswith("E2"):
            labels.append("commercial_zone")
        elif zone_code.startswith("IN"):
            labels.append("industrial_zone")
        elif zone_code.startswith("E") or zone_code.startswith("RU"):
            labels.append("environmental_zone")

    elif entity_type == "building":
        btype = domain_attrs.get("building_type", "")
        if btype not in ("yes", ""):
            labels.append(f"building_{btype}")

    elif entity_type == "road_segment":
        rclass = domain_attrs.get("road_class", "")
        if rclass:
            labels.append(f"highway_{rclass}")

    return labels


def _get_valid_from(props: dict, domain_attrs: dict) -> str | None:
    """Attempt to derive a valid_from date from feature properties.

    Checks domain attributes (already mapped) then raw source properties
    using the common temporal field names defined in ADR-024 §2.5.

    Returns
    -------
    str or None
        ISO-format date/datetime string if found, None otherwise.
    """
    # Check domain_attrs first — observation_date may already be mapped
    obs = domain_attrs.get("observation_date")
    if obs is not None:
        return str(obs)

    # Check raw source properties for known temporal field names
    for field in _DATE_SOURCE_FIELDS:
        val = props.get(field)
        if val is not None and str(val).strip():
            return str(val).strip()

    return None


def _coerce_value(harmony_field: str, val: Any, entity_type: str) -> Any:
    """Light type coercion based on known field types."""
    if val is None:
        return None

    float_fields = {"area_sqm", "height_m", "positional_accuracy_m"}
    int_fields = {"lane_count", "levels", "speed_limit_kmh"}

    if harmony_field in float_fields:
        try:
            return float(val)
        except (ValueError, TypeError):
            return val

    if harmony_field in int_fields:
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return val

    return val
