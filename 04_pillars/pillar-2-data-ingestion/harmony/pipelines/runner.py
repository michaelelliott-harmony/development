# Harmony Pillar 2 — End-to-End Pipeline Runner (Milestone 5)
#
# Wires all components into a single pipeline:
#   read → normalise → validate → assign → dedup → extract → register
#
# Brief §8, Task 8: runner + harmony-ingest CLI.
#
# Fidelity coverage non-negotiable:
#   Every cell and entity carries structural fidelity as "available" and
#   photorealistic as "pending" from day one. Since the Pillar 1 API does
#   not currently expose a PATCH endpoint for cell.fidelity_coverage, this
#   is carried in entity metadata and the Pillar 2 registry.
#   FLAG: Dr. Voss — PATCH /cells/{cell_key}/fidelity endpoint required.

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harmony.pipelines.assign import assign
from harmony.pipelines.dedup import DedupIndex, DedupMatch, LowConfidenceMatch
from harmony.pipelines.extract import extract, ExtractionQuarantine
from harmony.pipelines.manifest import DatasetManifest, load as load_manifest, get_adapter
from harmony.pipelines.normalise import normalise_batch, NormalisationError
from harmony.pipelines.p1_client import Pillar1Client, Pillar1Error
from harmony.pipelines.quarantine import QuarantineStore
from harmony.pipelines.registry import DatasetRegistry
from harmony.pipelines.validate import validate_batch, ValidationReport

log = logging.getLogger(__name__)


class IngestionReport:
    """Full ingestion run report produced by the runner."""

    def __init__(self, run_id: str, manifest: DatasetManifest) -> None:
        self.run_id = run_id
        self.manifest_id = manifest.manifest_id
        self.dataset_name = manifest.get("dataset_name", "unknown")
        self.entity_type = manifest.entity_type
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.completed_at: str | None = None
        self.status = "running"
        self.features_read = 0
        self.features_normalised = 0
        self.features_validated = 0
        self.features_quarantined = 0
        self.features_dedup_skipped = 0
        self.low_confidence_flagged = 0
        self.entities_registered = 0
        self.cells_registered = 0
        self.cells_already_existed = 0
        self.validation_report: dict = {}
        self.quarantine_by_reason: dict = {}
        self.errors: list[str] = []

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "manifest_id": self.manifest_id,
            "dataset_name": self.dataset_name,
            "entity_type": self.entity_type,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "features_read": self.features_read,
            "features_normalised": self.features_normalised,
            "features_validated": self.features_validated,
            "features_quarantined": self.features_quarantined,
            "features_dedup_skipped": self.features_dedup_skipped,
            "low_confidence_flagged": self.low_confidence_flagged,
            "entities_registered": self.entities_registered,
            "cells_registered": self.cells_registered,
            "cells_already_existed": self.cells_already_existed,
            "validation_report": self.validation_report,
            "quarantine_by_reason": self.quarantine_by_reason,
            "errors": self.errors,
        }

    def as_counts(self) -> dict:
        return {
            "features_read": self.features_read,
            "features_normalised": self.features_normalised,
            "features_validated": self.features_validated,
            "features_quarantined": self.features_quarantined,
            "features_dedup_skipped": self.features_dedup_skipped,
            "entities_registered": self.entities_registered,
            "cells_registered": self.cells_registered,
        }


class PipelineRunner:
    """End-to-end Pillar 2 ingestion pipeline.

    Parameters
    ----------
    p1_base_url : str, optional
        Pillar 1 API base URL. Defaults to HARMONY_P1_URL env var or
        http://127.0.0.1:8000.
    work_dir : str or Path, optional
        Working directory for quarantine, dedup index, and registry files.
        Defaults to ./harmony_work/.
    """

    def __init__(
        self,
        p1_base_url: str | None = None,
        work_dir: str | Path | None = None,
    ) -> None:
        self._p1 = Pillar1Client(base_url=p1_base_url)
        self._work_dir = Path(work_dir or "./harmony_work")
        self._work_dir.mkdir(parents=True, exist_ok=True)

    def run(self, manifest_path: str | Path) -> IngestionReport:
        """Execute the full pipeline for a given manifest.

        Parameters
        ----------
        manifest_path : str or Path
            Path to the YAML dataset manifest.

        Returns
        -------
        IngestionReport
            Full statistics and provenance for this run.
        """
        manifest = load_manifest(manifest_path)
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:8]}"
        report = IngestionReport(run_id, manifest)

        log.info("=== Pillar 2 ingestion run %s ===", run_id)
        log.info("Dataset: %s | Entity type: %s | Source: %s",
                 manifest.get("dataset_name"), manifest.entity_type, manifest.source_type)

        # --- Pre-flight: Pillar 1 health check ---
        try:
            health = self._p1.health()
            log.info("Pillar 1 health: %s", health)
        except Exception as exc:
            msg = f"Pillar 1 health check failed: {exc}"
            log.error(msg)
            report.status = "failed"
            report.errors.append(msg)
            return report

        quarantine_dir = self._work_dir / "quarantine"
        dedup_dir = self._work_dir / "dedup"
        registry_dir = self._work_dir / "registry"

        with (
            QuarantineStore(quarantine_dir) as quarantine,
            DedupIndex(dedup_dir, manifest.entity_type) as dedup_index,
            DatasetRegistry(registry_dir) as db,
        ):
            db.start_run(run_id, manifest)

            try:
                self._run_pipeline(manifest, run_id, report, quarantine, dedup_index, db)
                report.status = "completed"
            except Exception as exc:
                msg = f"Pipeline error: {exc}"
                log.exception(msg)
                report.status = "failed"
                report.errors.append(msg)

            report.completed_at = datetime.now(timezone.utc).isoformat()
            report.quarantine_by_reason = quarantine.counts_by_reason()
            db.complete_run(
                run_id,
                report.as_counts(),
                quarantine_by_reason=report.quarantine_by_reason,
                error_message="; ".join(report.errors) if report.errors else None,
            )

        log.info(
            "Run %s %s — read=%d normalised=%d validated=%d quarantined=%d "
            "dedup_skipped=%d entities=%d cells=%d",
            run_id, report.status,
            report.features_read, report.features_normalised,
            report.features_validated, report.features_quarantined,
            report.features_dedup_skipped, report.entities_registered,
            report.cells_registered,
        )
        return report

    def _run_pipeline(
        self,
        manifest: DatasetManifest,
        run_id: str,
        report: IngestionReport,
        quarantine: QuarantineStore,
        dedup_index: DedupIndex,
        db: DatasetRegistry,
    ) -> None:
        """Execute the pipeline stages."""
        adapter = get_adapter(manifest)
        val_report = ValidationReport()

        for raw_feature in adapter.read():
            report.features_read += 1

            # --- Stage 1: CRS normalisation ---
            try:
                normalised_list, norm_errors = normalise_batch([raw_feature])
            except Exception as exc:
                quarantine.add(raw_feature, "Q3_CRS_OUT_OF_BOUNDS", str(exc))
                report.features_quarantined += 1
                continue

            for err in norm_errors:
                quarantine.add(err["feature"], err["quarantine_reason"], err["error"])
                report.features_quarantined += 1

            if not normalised_list:
                continue
            normalised = normalised_list[0]
            report.features_normalised += 1

            # --- Stage 2: Geometry validation ---
            validated = _validate_one(normalised, quarantine, val_report, manifest)
            if validated is None:
                report.features_quarantined += 1
                continue
            report.features_validated += 1

            # --- Stage 3: Cell assignment (M3) ---
            assignment = assign(
                validated,
                resolution_floor=manifest.resolution_floor,
                region_code=manifest.region_code,
            )
            if assignment is None:
                log.debug("No geometry for %r — skipping cell assignment", raw_feature.get("source_id"))
                continue

            # --- Stage 4: Deduplication check (M4) ---
            # Use the actual Shapely geometry centroid for dedup, NOT the
            # Harmony cell centroid. Two features whose midpoints fall in the
            # same cell share an identical cell centroid (Haversine distance = 0),
            # which would produce a false positive at any spatial threshold.
            source_id = raw_feature.get("source_id")
            geom_wgs84 = validated.get("geometry_wgs84")
            actual_centroid_lat: float | None = None
            actual_centroid_lon: float | None = None
            if geom_wgs84:
                try:
                    from shapely.geometry import shape as _shape
                    _shp = _shape(geom_wgs84)
                    _c = _shp.centroid
                    actual_centroid_lat = _c.y
                    actual_centroid_lon = _c.x
                except Exception:
                    pass  # dedup will skip spatial check if centroid unavailable

            try:
                dedup_index.check(
                    source_id=source_id,
                    centroid_lat=actual_centroid_lat,
                    centroid_lon=actual_centroid_lon,
                    spatial_threshold_m=manifest.dedup_spatial_threshold_m,
                    strategy=manifest.dedup_strategy,
                )
            except DedupMatch as dup:
                log.debug(
                    "Dedup: %r matches existing entity %r via %s (confidence=%.2f)",
                    source_id, dup.existing_entity_id, dup.match_method, dup.confidence,
                )
                report.features_dedup_skipped += 1
                continue
            except LowConfidenceMatch as low:
                log.warning(
                    "Low-confidence dedup match: %r ~ %r distance=%.1fm confidence=%.2f — flagged",
                    source_id, low.existing_entity_id, low.distance_m, low.confidence,
                )
                report.low_confidence_flagged += 1
                # Proceed with registration — flagged in report

            # --- Stage 5: Register cells via Pillar 1 API ---
            primary_canonical_id = self._register_cell(
                assignment.primary, manifest, run_id, db, report
            )
            if primary_canonical_id is None:
                continue  # Cell registration failed — logged; skip entity

            secondary_canonical_ids = []
            for sec_coords in assignment.secondary:
                sec_id = self._register_cell(sec_coords, manifest, run_id, db, report)
                if sec_id:
                    secondary_canonical_ids.append(sec_id)

            # --- Stage 6: Extract entity payload (M4) ---
            try:
                entity_payload = extract(validated, assignment, manifest, run_id)
            except ExtractionQuarantine as exc:
                quarantine.add(validated, exc.quarantine_reason, str(exc))
                report.features_quarantined += 1
                log.debug(
                    "Extraction quarantine for %r: %s",
                    source_id,
                    exc,
                )
                continue

            # Fill in the actual cell canonical IDs from registration
            entity_payload["primary_cell_id"] = primary_canonical_id
            entity_payload["secondary_cell_ids"] = secondary_canonical_ids

            # ADR-024 §2.2 STD-V02: data_quality belongs on the asset bundle record.
            # fidelity_coverage is the asset bundle proxy until a dedicated endpoint
            # exists. Attach data_quality to fidelity_coverage — NOT to cell records.
            data_quality = {
                "completeness_percent": None,
                "positional_accuracy_metres": manifest.positional_accuracy_m,
                "last_validated": None,
            }
            entity_payload["metadata"]["fidelity_coverage"]["data_quality"] = data_quality

            # Remove internal-only keys
            known_names = entity_payload.pop("_known_names", [])
            entity_payload.pop("_assignment", None)

            # --- Stage 7: Register entity via Pillar 1 API ---
            try:
                canonical_entity_id = self._p1.register_entity(entity_payload)
            except Pillar1Error as exc:
                quarantine.add(validated, "Q4_SCHEMA_VIOLATION", f"Entity registration failed: {exc}")
                report.features_quarantined += 1
                log.error("Entity registration failed for %r: %s", source_id, exc)
                continue

            report.entities_registered += 1

            # Record in dedup index and registry
            dedup_index.register(
                canonical_entity_id=canonical_entity_id,
                source_id=source_id,
                centroid_lat=actual_centroid_lat,
                centroid_lon=actual_centroid_lon,
                dataset_name=manifest.get("dataset_name", "unknown"),
            )
            db.record_entity(
                run_id=run_id,
                canonical_entity_id=canonical_entity_id,
                source_id=source_id,
                entity_type=manifest.entity_type,
                primary_cell_key=assignment.primary.cell_key,
                secondary_cell_count=len(secondary_canonical_ids),
            )

        report.validation_report = val_report.to_dict()

    def _register_cell(
        self,
        coords,
        manifest: DatasetManifest,
        run_id: str,
        db: DatasetRegistry,
        report: IngestionReport,
    ) -> str | None:
        """Register a single cell via Pillar 1 API and record it.

        Returns the canonical_id of the cell, or None on failure.
        """
        payload = {
            "cell_key": coords.cell_key,
            "resolution_level": coords.resolution_level,
            "cube_face": coords.cube_face,
            "face_grid_u": coords.face_grid_u,
            "face_grid_v": coords.face_grid_v,
            "region_code": coords.region_code,
            # ADR-022 / ADR-017: field_descriptors must be present as empty JSONB
            # at ingestion time and must NOT be populated by the ingestion pipeline.
            "field_descriptors": {},
        }

        try:
            canonical_cell_id, created = self._p1.register_cell(payload)
        except Pillar1Error as exc:
            log.error("Cell registration failed for %r: %s", coords.cell_key, exc)
            return None

        if created:
            report.cells_registered += 1
        else:
            report.cells_already_existed += 1

        # --- FIDELITY PATCH HOOK (DEC-017) ---
        # PATCH /cells/{cell_key}/fidelity is now live in Pillar 1 per DEC-017.
        # ADR-022 dual-fidelity non-negotiable: every cell carries both structural
        # (available) and photorealistic (pending) slots from day one.
        try:
            self._p1.patch_cell_fidelity(
                cell_key=coords.cell_key,
                fidelity_coverage={
                    "structural": {
                        "status": "available",
                        "source_tier": manifest.source_tier,
                        "confidence": 1.0 if manifest.source_tier == 1 else 0.85,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    "photorealistic": {
                        "status": "pending",
                        "source_tier": None,
                        "confidence": 0.0,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                },
            )
        except Pillar1Error as exc:
            # Non-fatal: log and continue. Cell is registered; fidelity will be
            # retried on next ingestion run.
            log.warning(
                "Fidelity PATCH failed for cell %r: %s (non-fatal — continuing)",
                coords.cell_key,
                exc,
            )

        db.record_cell(
            run_id=run_id,
            cell_key=coords.cell_key,
            canonical_cell_id=canonical_cell_id,
            resolution_level=coords.resolution_level,
            entity_type=manifest.entity_type,
        )

        return canonical_cell_id


def _validate_one(normalised, quarantine, val_report, manifest):
    """Validate a single normalised feature."""
    from harmony.pipelines.validate import validate
    return validate(
        normalised,
        quarantine,
        val_report,
        allowed_types=manifest.allowed_geometry_types,
    )
