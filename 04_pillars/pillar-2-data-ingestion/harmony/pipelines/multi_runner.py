# Harmony Pillar 2 — Multi-Dataset Ingestion Orchestrator (Milestone 6)
#
# Runs all four Central Coast dataset manifests in sequence.
# Verifies cross-dataset coexistence and exercises deduplication.
#
# Brief §8, Task 9:
#   - Ingest all four datasets into the same cell region
#   - Validate entities from different sources coexist correctly
#   - Exercise deduplication across datasets
#   - Produce comprehensive ingestion report

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harmony.pipelines.dedup import DedupIndex
from harmony.pipelines.manifest import DatasetManifest, load as load_manifest
from harmony.pipelines.p1_client import Pillar1Client
from harmony.pipelines.quarantine import QuarantineStore
from harmony.pipelines.registry import DatasetRegistry
from harmony.pipelines.runner import IngestionReport, PipelineRunner

log = logging.getLogger(__name__)


class MultiDatasetReport:
    """Aggregated report across all four Central Coast datasets."""

    def __init__(self, multi_run_id: str) -> None:
        self.multi_run_id = multi_run_id
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.completed_at: str | None = None
        self.status = "running"
        self.per_dataset: dict[str, dict] = {}
        self.coexistence: dict = {}
        self.dedup_summary: dict = {}
        self.errors: list[str] = []

    @property
    def total_entities(self) -> int:
        return sum(r.get("entities_registered", 0) for r in self.per_dataset.values())

    @property
    def total_cells_new(self) -> int:
        return sum(r.get("cells_registered", 0) for r in self.per_dataset.values())

    @property
    def total_dedup_skipped(self) -> int:
        return sum(r.get("features_dedup_skipped", 0) for r in self.per_dataset.values())

    @property
    def total_quarantined(self) -> int:
        return sum(r.get("features_quarantined", 0) for r in self.per_dataset.values())

    def to_dict(self) -> dict:
        return {
            "multi_run_id": self.multi_run_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "summary": {
                "total_entities_registered": self.total_entities,
                "total_new_cells": self.total_cells_new,
                "total_dedup_skipped": self.total_dedup_skipped,
                "total_quarantined": self.total_quarantined,
                "datasets_completed": sum(
                    1 for r in self.per_dataset.values()
                    if r.get("status") == "completed"
                ),
                "datasets_total": len(self.per_dataset),
            },
            "per_dataset": self.per_dataset,
            "coexistence": self.coexistence,
            "dedup_summary": self.dedup_summary,
            "errors": self.errors,
        }


class MultiDatasetRunner:
    """Orchestrates ingestion of all four Central Coast datasets.

    Parameters
    ----------
    p1_base_url : str, optional
        Pillar 1 API base URL.
    work_dir : str or Path, optional
        Working directory for quarantine, dedup, and registry files.
        Each dataset gets its own dedup index; they share the quarantine
        store and registry.
    """

    def __init__(
        self,
        p1_base_url: str | None = None,
        work_dir: str | Path | None = None,
    ) -> None:
        self._p1_url = p1_base_url
        self._work_dir = Path(work_dir or "./harmony_work")
        self._work_dir.mkdir(parents=True, exist_ok=True)
        self._runner = PipelineRunner(p1_base_url=p1_base_url, work_dir=self._work_dir)
        self._p1 = Pillar1Client(base_url=p1_base_url)

    def run_all(
        self,
        manifests: list[DatasetManifest],
        run_id: str | None = None,
    ) -> MultiDatasetReport:
        """Ingest all datasets and produce a comprehensive report.

        Parameters
        ----------
        manifests : list[DatasetManifest]
            The four dataset manifests to ingest.
        run_id : str, optional
            Multi-run identifier. Generated if not provided.

        Returns
        -------
        MultiDatasetReport
        """
        multi_run_id = run_id or f"multi_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:8]}"
        report = MultiDatasetReport(multi_run_id)

        log.info("=== M6 Multi-Dataset Ingestion Run: %s ===", multi_run_id)
        log.info("Datasets: %s", [m.get("dataset_name") for m in manifests])

        # Pre-flight: Pillar 1 health check
        try:
            health = self._p1.health()
            log.info("Pillar 1 health: %s", health)
        except Exception as exc:
            msg = f"Pillar 1 health check failed: {exc}"
            log.error(msg)
            report.status = "failed"
            report.errors.append(msg)
            return report

        quarantine_dir = self._work_dir / "quarantine_m6"
        registry_dir = self._work_dir / "registry_m6"
        dedup_dir = self._work_dir / "dedup_m6"

        with (
            QuarantineStore(quarantine_dir) as quarantine,
            DatasetRegistry(registry_dir) as db,
        ):
            # --- Ingest each dataset in sequence ---
            for manifest in manifests:
                dataset_name = manifest.get("dataset_name", "unknown")
                entity_type = manifest.entity_type
                log.info("--- Ingesting dataset: %s (%s) ---", dataset_name, entity_type)

                per_run_id = f"{multi_run_id}_{entity_type}"
                per_report = IngestionReport(per_run_id, manifest)

                with DedupIndex(dedup_dir, entity_type) as dedup_index:
                    db.start_run(per_run_id, manifest)
                    try:
                        self._runner._run_pipeline(
                            manifest, per_run_id, per_report, quarantine, dedup_index, db
                        )
                        per_report.status = "completed"
                    except Exception as exc:
                        msg = f"Dataset {dataset_name} failed: {exc}"
                        log.exception(msg)
                        per_report.status = "failed"
                        per_report.errors.append(msg)
                        report.errors.append(msg)

                    per_report.quarantine_by_reason = quarantine.counts_by_reason()
                    db.complete_run(
                        per_run_id,
                        per_report.as_counts(),
                        quarantine_by_reason=per_report.quarantine_by_reason,
                        error_message="; ".join(per_report.errors) if per_report.errors else None,
                    )

                report.per_dataset[entity_type] = per_report.to_dict()
                log.info(
                    "  %s: read=%d validated=%d entities=%d cells_new=%d dedup_skipped=%d quarantined=%d",
                    entity_type,
                    per_report.features_read,
                    per_report.features_validated,
                    per_report.entities_registered,
                    per_report.cells_registered,
                    per_report.features_dedup_skipped,
                    per_report.features_quarantined,
                )

            # --- Cross-dataset coexistence verification ---
            report.coexistence = self._verify_coexistence(db, multi_run_id)
            report.dedup_summary = self._build_dedup_summary(report.per_dataset)

        report.completed_at = datetime.now(timezone.utc).isoformat()
        all_completed = all(
            r.get("status") == "completed" for r in report.per_dataset.values()
        )
        report.status = "completed" if all_completed else "partial"

        log.info(
            "=== M6 complete: %s | datasets=%d/%d | entities=%d | cells_new=%d | dedup_skipped=%d ===",
            report.status,
            report.to_dict()["summary"]["datasets_completed"],
            len(manifests),
            report.total_entities,
            report.total_cells_new,
            report.total_dedup_skipped,
        )

        return report

    def _verify_coexistence(self, db: DatasetRegistry, multi_run_id: str) -> dict:
        """Query the Pillar 2 registry to find cells shared by multiple entity types.

        Coexistence is confirmed when the same cell_key appears in registered_cells
        with 2+ different entity_types across the runs in this multi-run.
        """
        assert db._conn is not None

        # Find all cells registered in any run of this multi-run
        rows = db._conn.execute("""
            SELECT cell_key, GROUP_CONCAT(DISTINCT entity_type) as types, COUNT(DISTINCT entity_type) as type_count
            FROM registered_cells
            WHERE run_id LIKE ?
            GROUP BY cell_key
            ORDER BY type_count DESC
        """, (f"{multi_run_id}%",)).fetchall()

        multi_type_cells = [
            {"cell_key": row[0], "entity_types": row[1].split(","), "type_count": row[2]}
            for row in rows if row[2] > 1
        ]

        # Total cells registered across all datasets in this run
        total_cells = db._conn.execute(
            "SELECT COUNT(DISTINCT cell_key) FROM registered_cells WHERE run_id LIKE ?",
            (f"{multi_run_id}%",)
        ).fetchone()[0]

        # Cells per entity type
        type_counts = db._conn.execute("""
            SELECT entity_type, COUNT(DISTINCT cell_key) as cell_count
            FROM registered_cells
            WHERE run_id LIKE ?
            GROUP BY entity_type
        """, (f"{multi_run_id}%",)).fetchall()

        result = {
            "status": "pass" if multi_type_cells else "no_overlap_detected",
            "total_unique_cells_across_datasets": total_cells,
            "cells_with_multiple_entity_types": len(multi_type_cells),
            "multi_type_cell_examples": multi_type_cells[:10],
            "cells_by_entity_type": {row[0]: row[1] for row in type_counts},
        }

        if multi_type_cells:
            log.info(
                "Coexistence verified: %d cells carry entities from 2+ dataset types",
                len(multi_type_cells),
            )
        else:
            log.warning("No cells found with multiple entity types — datasets may occupy different cells at their assigned resolutions")

        return result

    def _build_dedup_summary(self, per_dataset: dict) -> dict:
        """Summarise deduplication activity across all datasets."""
        return {
            "by_dataset": {
                entity_type: {
                    "features_dedup_skipped": r.get("features_dedup_skipped", 0),
                    "low_confidence_flagged": r.get("low_confidence_flagged", 0),
                }
                for entity_type, r in per_dataset.items()
            },
            "total_dedup_skipped": sum(
                r.get("features_dedup_skipped", 0) for r in per_dataset.values()
            ),
            "note": (
                "Dedup is per-entity-type. Source-system ID matching is the primary "
                "strategy for Tier 1 sources (zoning: PCO_REF_KEY, cadastral: cadid). "
                "Spatial proximity is the fallback for Tier 2 OSM sources."
            ),
        }
