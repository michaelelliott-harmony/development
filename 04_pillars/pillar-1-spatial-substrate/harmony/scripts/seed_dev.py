#!/usr/bin/env python3
# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Dev Seed Script
#
# Loads harmony/data/sample-central-coast-records.json into the local
# Harmony database via the HTTP API. Registers the namespaces required
# by the sample records first, then the 5 cells, then the 3 entities.
# Each registration is verified by round-tripping the canonical_id back
# through the resolve endpoint.
#
# Usage:
#     # In one terminal:
#     uvicorn harmony.services.api.main:app --reload
#
#     # In another:
#     python harmony/scripts/seed_dev.py
#
# Environment:
#     HARMONY_API_URL — base URL of the API (default: http://localhost:8000)

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx


_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA_PATH = _REPO_ROOT / "harmony" / "data" / "sample-central-coast-records.json"
_API_URL = os.environ.get("HARMONY_API_URL", "http://localhost:8000").rstrip("/")


def _log(msg: str) -> None:
    print(msg, flush=True)


def _require_server() -> None:
    try:
        r = httpx.get(f"{_API_URL}/health", timeout=3.0)
    except httpx.RequestError as exc:
        _log(f"ERROR — cannot reach {_API_URL}: {exc}")
        sys.exit(2)
    if r.status_code != 200:
        _log(f"ERROR — /health returned {r.status_code}")
        sys.exit(2)
    _log(f"Connected to API at {_API_URL} — {r.json()}")


def _ensure_namespace(ns: str, prefix: str) -> None:
    r = httpx.post(f"{_API_URL}/namespaces", json={"namespace": ns, "prefix": prefix})
    if r.status_code == 201:
        _log(f"  registered namespace {ns} (prefix={prefix})")
    elif r.status_code == 409:
        _log(f"  namespace {ns} already exists")
    else:
        _log(f"  FAILED to register namespace {ns}: {r.status_code} {r.text}")


def _register_cell(record: dict) -> str:
    cell_key = record["cell_key"]
    payload = {
        "cell_key": cell_key,
        "resolution_level": record["resolution_level"],
        "cube_face": record["cube_face"],
        "face_grid_u": record["face_grid_u"],
        "face_grid_v": record["face_grid_v"],
        "region_code": cell_key.split(":")[2],
        "friendly_name": record.get("friendly_name"),
        "semantic_labels": record.get("semantic_labels") or None,
    }
    # Skip alias during cell creation — we bind aliases explicitly afterwards
    # so the namespaces are definitely registered first.
    r = httpx.post(f"{_API_URL}/cells", json={k: v for k, v in payload.items() if v is not None})
    if r.status_code not in (200, 201):
        raise RuntimeError(f"cell registration failed: {r.status_code} {r.text}")
    canonical_id = r.json()["canonical_id"]

    # Round-trip verification
    v = httpx.get(f"{_API_URL}/resolve/cell/{canonical_id}")
    if v.status_code != 200 or v.json()["cell_key"] != cell_key:
        raise RuntimeError(f"cell round-trip failed: {canonical_id} -> {v.status_code}")
    _log(f"  cell {cell_key} -> {canonical_id} (verified)")
    return canonical_id


def _register_entity(record: dict, cell_key_to_id: dict[str, str]) -> str:
    primary_cell_key = record["primary_cell_key"]
    primary_cell_id = cell_key_to_id.get(primary_cell_key)
    if primary_cell_id is None:
        raise RuntimeError(f"no cell registered for {primary_cell_key}")
    payload = {
        "entity_subtype": record["entity_subtype"],
        "primary_cell_id": primary_cell_id,
        "metadata": record.get("metadata") or {},
        "friendly_name": record.get("friendly_name"),
        "semantic_labels": record.get("semantic_labels") or None,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    r = httpx.post(f"{_API_URL}/entities", json=payload)
    if r.status_code != 201:
        raise RuntimeError(f"entity registration failed: {r.status_code} {r.text}")
    canonical_id = r.json()["canonical_id"]

    v = httpx.get(f"{_API_URL}/resolve/entity/{canonical_id}")
    if v.status_code != 200 or v.json()["primary_cell_id"] != primary_cell_id:
        raise RuntimeError(f"entity round-trip failed: {canonical_id} -> {v.status_code}")
    _log(f"  entity {record['entity_id']} -> {canonical_id} (verified)")
    return canonical_id


def _bind_alias(canonical_id: str, alias: str, namespace: str) -> None:
    r = httpx.post(
        f"{_API_URL}/aliases",
        json={"canonical_id": canonical_id, "alias": alias, "alias_namespace": namespace},
    )
    if r.status_code == 201:
        _log(f"  bound alias {alias} ({namespace}) -> {canonical_id}")
    elif r.status_code == 409:
        _log(f"  alias {alias} ({namespace}) already bound")
    else:
        _log(f"  alias bind failed for {alias}: {r.status_code} {r.text}")


def main() -> int:
    _require_server()
    _log(f"Loading seed data from {_DATA_PATH}")
    with open(_DATA_PATH, "r") as f:
        records = json.load(f)

    cells = [r for r in records if r.get("object_type") == "cell"]
    entities = [r for r in records if r.get("object_type") == "entity"]
    _log(f"Found {len(cells)} cells and {len(entities)} entities")

    # Register all unique namespaces up front. The sample file's cell namespaces
    # (cc.au.nsw.cc) live alongside the entity namespace.
    namespaces = {
        ns: prefix
        for ns, prefix in [
            ("cc.au.nsw.cc", "CC"),
            ("au.nsw.central_coast.entities", "EN"),
        ]
    }
    _log("Registering namespaces")
    for ns, prefix in namespaces.items():
        _ensure_namespace(ns, prefix)

    _log("Registering cells")
    cell_key_to_id: dict[str, str] = {}
    for record in cells:
        cid = _register_cell(record)
        cell_key_to_id[record["cell_key"]] = cid
        # Bind manual alias if present in the sample file
        if record.get("human_alias"):
            _bind_alias(cid, record["human_alias"], record["alias_namespace"])

    _log("Registering entities")
    for record in entities:
        eid = _register_entity(record, cell_key_to_id)
        if record.get("human_alias"):
            _bind_alias(eid, record["human_alias"], record["alias_namespace"])

    _log(f"\nSeed complete — {len(cells)} cells + {len(entities)} entities registered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
