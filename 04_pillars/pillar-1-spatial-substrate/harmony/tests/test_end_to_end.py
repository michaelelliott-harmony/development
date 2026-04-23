# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Milestone 6 — End-to-End Acceptance Test Suite
#
# Black-box HTTP tests. No internal Python imports. Every criterion from
# pillar-1-spatial-substrate-stage1-brief.md §9 is validated via the live
# FastAPI server at HARMONY_API_URL (default http://127.0.0.1:8000).
#
# Usage:
#     1. Recreate the dev DB and apply migrations 001 + 002
#     2. Start the server:
#            uvicorn harmony.services.api.main:app --host 127.0.0.1 --port 8000
#     3. Run the suite:
#            pytest harmony/tests/test_end_to_end.py -v
#
# The suite is self-contained: it creates its own namespace and records.
# It truncates the database before the first test via the API's own
# endpoints — no direct DB access. If the pre-existing database contains
# records, tests that rely on disjoint namespaces still behave correctly.

from __future__ import annotations

import os
import re
import uuid

import httpx
import pytest


API_URL = os.environ.get("HARMONY_API_URL", "http://127.0.0.1:8000").rstrip("/")

# Regexes — must match the patterns in cell_identity_schema.json and the
# locked alias_namespace_rules.md §2/§3.
CANONICAL_CELL_RE = re.compile(r"^hc_[a-z0-9]{9}$")
CANONICAL_ENTITY_RE = re.compile(r"^ent_[a-z]{3}_[a-z0-9]{6}$")
CELL_KEY_RE = re.compile(r"^hsam:r[0-9]{2}:[a-z]{2,8}:[0-9a-hjkmnp-tv-z]{16}$")
ALIAS_RE = re.compile(r"^[A-Z]{2,4}-[0-9]{1,6}$")


# A disjoint namespace + prefix per test run so this suite can be re-executed
# without collisions and without needing DB truncation.
# `TE` (Test E2E) is not in the reserved-prefix set {TEST, DEMO, TMP, SYS}.
def _unique_ns() -> str:
    # Unique suffix in the last segment keeps the whole namespace regex-valid.
    return f"au.nsw.central_coast.e2e_{uuid.uuid4().hex[:10]}"


# Sample Central Coast cell coordinates. These are the Session 3 sample
# dataset values — real cells derived from Gosford-area coordinates.
# Using them here also happens to validate the Session 2 derivation against
# the current server.

CELL_GOSFORD_DISTRICT_L4 = {
    "cell_key": "hsam:r04:cc:yfme2b4kb7j69717",
    "resolution_level": 4,
    "cube_face": 1,
    "face_grid_u": 197,
    "face_grid_v": 32,
    "region_code": "cc",
    "friendly_name": "Gosford District (E2E)",
    "semantic_labels": ["Central Coast NSW pilot region"],
}

CELL_GOSFORD_CBD_L6 = {
    "cell_key": "hsam:r06:cc:za6bzq7gfknrzd5z",
    "resolution_level": 6,
    "cube_face": 1,
    "face_grid_u": 3167,
    "face_grid_v": 518,
    "region_code": "cc",
    "friendly_name": "Gosford CBD Neighbourhood (E2E)",
    "semantic_labels": ["Central Coast NSW pilot region"],
}

CELL_GOSFORD_WATERFRONT_L8 = {
    "cell_key": "hsam:r08:cc:g2f39nh7keq4h9f0",
    "resolution_level": 8,
    "cube_face": 1,
    "face_grid_u": 50678,
    "face_grid_v": 8290,
    "region_code": "cc",
    "friendly_name": "Gosford Waterfront Cell (E2E)",
    "semantic_labels": ["Central Coast NSW pilot region", "waterfront"],
}


# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    c = httpx.Client(base_url=API_URL, timeout=10.0)
    r = c.get("/health")
    assert r.status_code == 200, f"API not reachable at {API_URL}: {r.status_code}"
    body = r.json()
    assert body["status"] == "ok" and body["database"] == "connected", body
    yield c
    c.close()


@pytest.fixture(scope="session")
def namespace(client) -> str:
    """Register a disjoint namespace for this test session."""
    ns = _unique_ns()
    r = client.post("/namespaces", json={"namespace": ns, "prefix": "TE"})
    assert r.status_code == 201, f"namespace setup failed: {r.status_code} {r.text}"
    assert r.json()["namespace"] == ns
    assert r.json()["next_counter"] == 1
    return ns


@pytest.fixture(scope="session")
def registered_cells(client) -> dict:
    """Register the three Central Coast cells and return id mappings."""
    cells = {
        "L4": CELL_GOSFORD_DISTRICT_L4,
        "L6": CELL_GOSFORD_CBD_L6,
        "L8": CELL_GOSFORD_WATERFRONT_L8,
    }
    results = {}
    for label, payload in cells.items():
        r = client.post("/cells", json=payload)
        assert r.status_code in (200, 201), f"{label} register failed: {r.status_code} {r.text}"
        data = r.json()
        results[label] = {
            "canonical_id": data["canonical_id"],
            "cell_key": data["cell_key"],
            "payload": payload,
            "first_status": r.status_code,
        }
    return results


# -------------------------------------------------------------------------
# Test 1 — Register cells and verify cell_id + cell_key linkage
# (Acceptance criterion AC3: Cell has BOTH canonical ID and deterministic cell_key)
# -------------------------------------------------------------------------

def test_1_register_cells_have_canonical_id_and_cell_key(client, registered_cells):
    for label, info in registered_cells.items():
        cid = info["canonical_id"]
        key = info["cell_key"]

        assert CANONICAL_CELL_RE.match(cid), f"{label} canonical_id malformed: {cid}"
        assert CELL_KEY_RE.match(key), f"{label} cell_key malformed: {key}"

        # Resolve by canonical_id
        r = client.get(f"/resolve/cell/{cid}")
        assert r.status_code == 200, r.text
        rec_by_id = r.json()
        assert rec_by_id["canonical_id"] == cid
        assert rec_by_id["cell_key"] == key

        # Resolve by cell_key — must return the same canonical_id
        r = client.get(f"/resolve/cell-key/{key}")
        assert r.status_code == 200, r.text
        rec_by_key = r.json()
        assert rec_by_key["canonical_id"] == cid
        assert rec_by_key["cell_key"] == key


# -------------------------------------------------------------------------
# Test 2 — Idempotent cell registration
# (AC3 determinism proof)
# -------------------------------------------------------------------------

def test_2_cell_registration_is_idempotent(client, registered_cells):
    info = registered_cells["L8"]
    r = client.post("/cells", json=info["payload"])
    # Second registration must be 200 (existing) not 201 (new)
    assert r.status_code == 200, (
        f"expected 200 on re-registration, got {r.status_code}. "
        "If 201, either cell_key derivation is non-deterministic or the "
        "idempotency check is broken."
    )
    data = r.json()
    assert data["canonical_id"] == info["canonical_id"]
    assert data["cell_key"] == info["cell_key"]


# -------------------------------------------------------------------------
# Test 3 — Register entities anchored to cells
# (AC4: Entity links to primary and secondary cells)
# -------------------------------------------------------------------------

@pytest.fixture(scope="session")
def registered_entities(client, registered_cells) -> dict:
    """Register a building, a parcel, and a road-span entity."""
    building = client.post("/entities", json={
        "entity_subtype": "bld",
        "primary_cell_id": registered_cells["L8"]["canonical_id"],
        "metadata": {"use": "commercial", "storeys": 3},
        "friendly_name": "Waterfront Building A (E2E)",
    })
    assert building.status_code == 201, building.text

    parcel = client.post("/entities", json={
        "entity_subtype": "prc",
        "primary_cell_id": registered_cells["L6"]["canonical_id"],
        "metadata": {"lot": "12", "plan": "DP1234567"},
        "friendly_name": "CBD Parcel Lot 12 (E2E)",
    })
    assert parcel.status_code == 201, parcel.text

    # Road spans L6 and L8
    road = client.post("/entities", json={
        "entity_subtype": "rod",
        "primary_cell_id": registered_cells["L4"]["canonical_id"],
        "secondary_cell_ids": [
            registered_cells["L6"]["canonical_id"],
            registered_cells["L8"]["canonical_id"],
        ],
        "metadata": {"road_name": "Terrigal Drive"},
        "friendly_name": "Terrigal Drive Segment (E2E)",
    })
    assert road.status_code == 201, road.text

    return {
        "building": building.json(),
        "parcel": parcel.json(),
        "road": road.json(),
    }


def test_3_entities_anchor_to_primary_and_secondary_cells(
    client, registered_cells, registered_entities,
):
    # Every entity has a valid canonical_id and its primary_cell_id resolves
    for label, ent in registered_entities.items():
        assert CANONICAL_ENTITY_RE.match(ent["canonical_id"]), (
            f"{label} canonical_id malformed: {ent['canonical_id']}"
        )
        primary_id = ent["primary_cell_id"]
        r = client.get(f"/resolve/cell/{primary_id}")
        assert r.status_code == 200, (
            f"{label}.primary_cell_id {primary_id} does not resolve: {r.status_code}"
        )
        assert r.json()["canonical_id"] == primary_id

    # Specific linkages
    assert registered_entities["building"]["primary_cell_id"] == registered_cells["L8"]["canonical_id"]
    assert registered_entities["parcel"]["primary_cell_id"] == registered_cells["L6"]["canonical_id"]

    # Road has two secondary cells that must also resolve
    road = registered_entities["road"]
    road_resolved = client.get(f"/resolve/entity/{road['canonical_id']}").json()
    assert road_resolved["primary_cell_id"] == registered_cells["L4"]["canonical_id"]
    secondaries = road_resolved.get("secondary_cell_ids") or []
    assert len(secondaries) == 2, f"expected 2 secondaries, got {secondaries}"
    for sec_id in secondaries:
        r = client.get(f"/resolve/cell/{sec_id}")
        assert r.status_code == 200, f"secondary {sec_id} does not resolve"
    # Secondary ids must be L6 and L8 (order-insensitive)
    assert set(secondaries) == {
        registered_cells["L6"]["canonical_id"],
        registered_cells["L8"]["canonical_id"],
    }


# -------------------------------------------------------------------------
# Test 4 — Register a namespace and bind aliases to cells
# (AC1: Alias resolves to canonical ID)
# -------------------------------------------------------------------------

@pytest.fixture(scope="session")
def bound_aliases(client, namespace, registered_cells) -> dict:
    """Bind TE-1, TE-2, TE-3 to the three cells (manual assignment using the
    namespace's prefix, matching §9 of alias_namespace_rules.md). The
    namespace counter remains at 1 — manual binding does not advance it —
    but the prefix TE is the one registered for this namespace."""
    aliases = {"L4": "TE-1", "L6": "TE-2", "L8": "TE-3"}
    for label, alias in aliases.items():
        cid = registered_cells[label]["canonical_id"]
        r = client.post(
            "/aliases",
            json={"canonical_id": cid, "alias": alias, "alias_namespace": namespace},
        )
        assert r.status_code == 201, f"{alias} bind failed: {r.status_code} {r.text}"
    return aliases


def test_4_aliases_bind_and_resolve(client, namespace, registered_cells, bound_aliases):
    for label, alias in bound_aliases.items():
        assert ALIAS_RE.match(alias), f"{alias} does not match alias regex"
        r = client.get("/resolve/alias", params={"alias": alias, "namespace": namespace})
        assert r.status_code == 200, r.text
        resolved = r.json()
        assert resolved["canonical_id"] == registered_cells[label]["canonical_id"]
        assert resolved["alias_status"] == "active"
        assert resolved["namespace"] == namespace


# -------------------------------------------------------------------------
# Test 5 — Full resolution chain: alias → canonical → entity → cell
# (AC2 + end-to-end)
# -------------------------------------------------------------------------

def test_5_end_to_end_chain_alias_to_entity(
    client, namespace, registered_cells, bound_aliases, registered_entities,
):
    # Step 1 — Resolve alias -> cell canonical_id
    start_alias = "TE-3"     # bound to the L8 waterfront cell
    r = client.get("/resolve/alias", params={"alias": start_alias, "namespace": namespace})
    assert r.status_code == 200
    cell_id = r.json()["canonical_id"]
    assert cell_id == registered_cells["L8"]["canonical_id"]

    # Step 2 — Resolve canonical_id -> full cell record
    r = client.get(f"/resolve/cell/{cell_id}")
    assert r.status_code == 200
    cell = r.json()
    for field in (
        "canonical_id", "cell_key", "resolution_level", "cube_face",
        "face_grid_u", "face_grid_v", "edge_length_m", "area_m2",
        "distortion_factor", "centroid_ecef", "centroid_geodetic",
        "adjacent_cell_keys", "friendly_name", "semantic_labels",
        "status", "schema_version", "created_at", "updated_at",
    ):
        assert field in cell, f"cell record missing field: {field}"
    assert len(cell["adjacent_cell_keys"]) == 4
    assert cell["friendly_name"] == "Gosford Waterfront Cell (E2E)"
    assert "Central Coast NSW pilot region" in cell["semantic_labels"]

    # Step 3 — Query adjacency ring at depth 1. This cell is non-boundary
    # (u=50678, v=8290 at r=8 where max=65535), so the ring MUST be exactly
    # 8 cells per cell_adjacency_spec.md §4.1 (8k formula for k=1).
    r = client.get(f"/cells/{cell['cell_key']}/adjacency", params={"depth": 1})
    assert r.status_code == 200
    ring = r.json()["ring"]
    assert len(ring) == 8, (
        f"expected 8k=8 cells in ring-1 for non-boundary cell, got {len(ring)}. "
        "If this cell has become a boundary case the test cell must be revisited."
    )
    for node in ring:
        assert CELL_KEY_RE.match(node["cell_key"])

    # Step 4 — Back-link check: the entities we registered whose
    # primary_cell_id == this cell. The cell→entity direction is not a
    # public endpoint (see SESSION_06_SUMMARY §"Design note"), so we use
    # the canonical forward direction: each entity must point back to the cell.
    expected_entity_ids = {
        registered_entities["building"]["canonical_id"],  # primary = L8
    }
    for ent_id in expected_entity_ids:
        r = client.get(f"/resolve/entity/{ent_id}")
        assert r.status_code == 200
        ent = r.json()
        assert ent["primary_cell_id"] == cell_id, (
            f"bidirectional link broken: entity {ent_id} primary_cell_id "
            f"{ent['primary_cell_id']} != cell {cell_id}"
        )
        assert ent["canonical_id"].startswith("ent_")

    # Step 5 — Secondary-cell reverse link via the road entity.
    # The road's secondary_cell_ids should include the waterfront cell.
    road_id = registered_entities["road"]["canonical_id"]
    road = client.get(f"/resolve/entity/{road_id}").json()
    assert cell_id in road["secondary_cell_ids"], (
        "end-to-end secondary linkage broken: road does not list the "
        "L8 waterfront as a secondary cell"
    )


# -------------------------------------------------------------------------
# Test 6 — Alias can change without breaking canonical identity
# (AC5)
# -------------------------------------------------------------------------

def test_6_alias_change_preserves_canonical_identity(
    client, namespace, registered_cells, bound_aliases,
):
    cell_id = registered_cells["L8"]["canonical_id"]
    original_alias = "TE-3"
    new_alias = "TE-999"

    # Snapshot the cell record before the alias churn.
    before = client.get(f"/resolve/cell/{cell_id}").json()

    # Bind the new alias.
    r = client.post("/aliases", json={
        "canonical_id": cell_id, "alias": new_alias, "alias_namespace": namespace,
    })
    assert r.status_code == 201, r.text

    # New alias resolves to the same canonical_id.
    r = client.get("/resolve/alias", params={"alias": new_alias, "namespace": namespace})
    assert r.status_code == 200
    assert r.json()["canonical_id"] == cell_id

    # Retire the original alias.
    r = client.post("/aliases/retire", json={
        "alias": original_alias, "alias_namespace": namespace,
    })
    assert r.status_code == 200
    assert r.json()["status"] == "retired"

    # Retired alias now 404 without include_retired.
    r = client.get("/resolve/alias", params={"alias": original_alias, "namespace": namespace})
    assert r.status_code == 404

    # New alias still resolves.
    r = client.get("/resolve/alias", params={"alias": new_alias, "namespace": namespace})
    assert r.status_code == 200
    assert r.json()["canonical_id"] == cell_id

    # Cell record is unchanged — canonical_id, cell_key, centroid all identical.
    after = client.get(f"/resolve/cell/{cell_id}").json()
    for field in ("canonical_id", "cell_key", "cube_face", "face_grid_u",
                  "face_grid_v", "edge_length_m", "centroid_ecef",
                  "centroid_geodetic", "adjacent_cell_keys"):
        assert before[field] == after[field], (
            f"alias churn affected cell.{field}: {before[field]} -> {after[field]}"
        )


# -------------------------------------------------------------------------
# Test 7 — Lifecycle states are enforced
# (AC6)
# -------------------------------------------------------------------------

def test_7_lifecycle_and_referential_integrity(client, registered_cells):
    # Every registered cell is active.
    for info in registered_cells.values():
        rec = client.get(f"/resolve/cell/{info['canonical_id']}").json()
        assert rec["status"] == "active", f"cell {info['canonical_id']} not active: {rec['status']}"

    # Entity referencing a non-existent (but format-valid) cell_id must be rejected.
    r = client.post("/entities", json={
        "entity_subtype": "bld",
        "primary_cell_id": "hc_aaaaaaaaa",  # 9 chars, matches regex, does not exist
    })
    assert r.status_code == 400, (
        f"expected 400 on non-existent primary cell ref, got {r.status_code}. "
        "Referential integrity not enforced."
    )
    assert r.json()["error"] == "invalid_entity"


# -------------------------------------------------------------------------
# Test 8 — Namespace collisions are handled
# (AC7)
# -------------------------------------------------------------------------

def test_8_namespace_collisions_and_cross_namespace_independence(
    client, namespace, registered_cells,
):
    cid_L4 = registered_cells["L4"]["canonical_id"]

    # Within the same namespace, a second binding of an active alias → 409.
    r = client.post("/aliases", json={
        "canonical_id": cid_L4, "alias": "TE-1", "alias_namespace": namespace,
    })
    # TE-1 was bound to L4 in Test 4 — re-binding to the same canonical_id
    # with the same tuple is idempotent (201). Rebinding to a DIFFERENT
    # canonical_id must fail 409. Use L6 to force a true collision.
    cid_L6 = registered_cells["L6"]["canonical_id"]
    r_conflict = client.post("/aliases", json={
        "canonical_id": cid_L6, "alias": "TE-1", "alias_namespace": namespace,
    })
    assert r_conflict.status_code == 409, (
        f"expected 409 on active-alias collision, got {r_conflict.status_code}: {r_conflict.text}"
    )
    assert r_conflict.json()["error"] == "alias_conflict"

    # Cross-namespace independence: the same alias string in a different
    # namespace must succeed and point to a different canonical_id.
    other_ns = _unique_ns()
    r = client.post("/namespaces", json={"namespace": other_ns, "prefix": "TE"})
    assert r.status_code == 201

    r = client.post("/aliases", json={
        "canonical_id": cid_L6, "alias": "TE-1", "alias_namespace": other_ns,
    })
    assert r.status_code == 201, r.text

    # Both resolve to DIFFERENT canonical_ids.
    a = client.get("/resolve/alias", params={"alias": "TE-1", "namespace": namespace}).json()
    b = client.get("/resolve/alias", params={"alias": "TE-1", "namespace": other_ns}).json()
    assert a["canonical_id"] == cid_L4
    assert b["canonical_id"] == cid_L6
    assert a["canonical_id"] != b["canonical_id"]


# -------------------------------------------------------------------------
# Test 9 — Registry acts as single source of truth
# (AC8)
# -------------------------------------------------------------------------

def test_9_registry_is_single_source_of_truth(
    client, namespace, registered_cells,
):
    """Resolve the same cell via canonical_id, cell_key, and alias.
    All three paths must return identical records."""
    cid = registered_cells["L4"]["canonical_id"]
    ckey = registered_cells["L4"]["cell_key"]
    # TE-1 is still the active alias on L4 (we did not retire it in Test 6
    # — only TE-3 was churned).

    by_id = client.get(f"/resolve/cell/{cid}").json()

    by_key = client.get(f"/resolve/cell-key/{ckey}").json()

    # Alias resolution returns the alias-resolution envelope (with alias_status
    # etc.). Chain through to the cell record via its canonical_id to compare.
    alias_env = client.get("/resolve/alias", params={
        "alias": "TE-1", "namespace": namespace,
    }).json()
    by_alias_cid = alias_env["canonical_id"]
    by_alias = client.get(f"/resolve/cell/{by_alias_cid}").json()

    # Stable fields must match across all three paths.
    for field in (
        "canonical_id", "cell_key", "resolution_level", "cube_face",
        "face_grid_u", "face_grid_v", "edge_length_m", "area_m2",
        "distortion_factor", "centroid_ecef", "centroid_geodetic",
        "adjacent_cell_keys", "friendly_name", "semantic_labels",
        "status", "schema_version",
    ):
        assert by_id[field] == by_key[field], f"id vs key differ on {field}"
        assert by_id[field] == by_alias[field], f"id vs alias differ on {field}"


# -------------------------------------------------------------------------
# Test 10 — Resolve alias without namespace returns 400
# (alias_namespace_rules.md §7.4 — non-negotiable design rule)
# -------------------------------------------------------------------------

def test_10_resolve_alias_without_namespace_returns_400(client):
    r = client.get("/resolve/alias", params={"alias": "TE-1"})
    assert r.status_code == 400
    body = r.json()
    assert body["error"] == "namespace_required"
    assert "namespace" in body["detail"].lower()
