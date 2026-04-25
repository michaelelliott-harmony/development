# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Integration Test Suite — FastAPI Identity Registry API
#
# Exercises every endpoint against a real PostgreSQL database.
# Requires HARMONY_DB_URL to point at a writable harmony_dev instance
# (migrations 001 and 002 already applied).
#
# Each test starts from a clean DB state (see conftest.clean_db).

import pytest


# Canonical Gosford Level 8 waterfront cell — matches sample-central-coast-records.json.
# This is the Session 2 test vector 1 cell.
GOSFORD_L8 = {
    "cell_key": "hsam:r08:cc:g2f39nh7keq4h9f0",
    "resolution_level": 8,
    "cube_face": 1,
    "face_grid_u": 50678,
    "face_grid_v": 8290,
    "region_code": "cc",
}

# Simple non-reserved-prefix namespace for alias tests
CC_NAMESPACE = "au.nsw.central_coast.cells"
CC_PREFIX = "CC"
ENT_NAMESPACE = "au.nsw.central_coast.entities"
ENT_PREFIX = "EN"


# -------------------------------------------------------------------------
# Health
# -------------------------------------------------------------------------

def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["schema_version"] == "0.1.3"
    assert body["database"] == "connected"


# -------------------------------------------------------------------------
# Cells: register + resolve
# -------------------------------------------------------------------------

def test_register_cell_and_resolve_both_paths(client):
    r = client.post("/cells", json=GOSFORD_L8)
    assert r.status_code == 201, r.text
    data = r.json()
    cid = data["canonical_id"]
    assert cid.startswith("hc_")
    assert data["cell_key"] == GOSFORD_L8["cell_key"]
    assert len(data["adjacent_cell_keys"]) == 4

    # Resolve by canonical_id
    r2 = client.get(f"/resolve/cell/{cid}")
    assert r2.status_code == 200
    assert r2.json()["cell_key"] == GOSFORD_L8["cell_key"]

    # Resolve by cell_key
    r3 = client.get(f"/resolve/cell-key/{GOSFORD_L8['cell_key']}")
    assert r3.status_code == 200
    assert r3.json()["canonical_id"] == cid


def test_register_cell_is_idempotent(client):
    r1 = client.post("/cells", json=GOSFORD_L8)
    assert r1.status_code == 201
    first_id = r1.json()["canonical_id"]

    r2 = client.post("/cells", json=GOSFORD_L8)
    assert r2.status_code == 200, "second registration should be idempotent (200 OK)"
    assert r2.json()["canonical_id"] == first_id


def test_resolve_nonexistent_canonical_id_returns_404(client):
    r = client.get("/resolve/cell/hc_abcdef123")
    assert r.status_code == 404
    assert r.json()["error"] == "cell_not_found"


def test_resolve_invalid_cell_key_format_returns_400(client):
    r = client.get("/resolve/cell-key/not-a-cell-key")
    assert r.status_code == 400


def test_cell_input_rejected_when_fields_missing(client):
    r = client.post("/cells", json={"cell_key": "bad"})
    assert r.status_code == 422  # Pydantic validation


# -------------------------------------------------------------------------
# Entities
# -------------------------------------------------------------------------

def test_register_entity_anchored_to_existing_cell(client):
    cid = client.post("/cells", json=GOSFORD_L8).json()["canonical_id"]
    r = client.post("/entities", json={
        "entity_subtype": "bld",
        "primary_cell_id": cid,
        "metadata": {"use": "commercial", "storeys": 3},
        "friendly_name": "Test building",
    })
    assert r.status_code == 201, r.text
    ent = r.json()
    assert ent["canonical_id"].startswith("ent_bld_")
    assert ent["primary_cell_id"] == cid

    # Resolve back
    r2 = client.get(f"/resolve/entity/{ent['canonical_id']}")
    assert r2.status_code == 200
    assert r2.json()["primary_cell_id"] == cid


def test_register_entity_missing_primary_cell_returns_400(client):
    # hc_aaaaaaaaa matches the regex but does not exist
    r = client.post("/entities", json={
        "entity_subtype": "bld",
        "primary_cell_id": "hc_aaaaaaaaa",
    })
    assert r.status_code == 400
    assert r.json()["error"] == "invalid_entity"


def test_resolve_nonexistent_entity_returns_404(client):
    r = client.get("/resolve/entity/ent_bld_zzzzzz")
    assert r.status_code == 404


# -------------------------------------------------------------------------
# Aliases
# -------------------------------------------------------------------------

def test_bind_and_resolve_alias(client):
    # Register a cell to bind to
    cid = client.post("/cells", json=GOSFORD_L8).json()["canonical_id"]
    # Register the namespace
    assert client.post("/namespaces", json={"namespace": CC_NAMESPACE, "prefix": CC_PREFIX}).status_code == 201
    # Bind the alias
    r = client.post("/aliases", json={
        "canonical_id": cid,
        "alias": "CC-421",
        "alias_namespace": CC_NAMESPACE,
    })
    assert r.status_code == 201, r.text
    assert r.json()["canonical_id"] == cid

    # Resolve it
    r2 = client.get("/resolve/alias", params={"alias": "CC-421", "namespace": CC_NAMESPACE})
    assert r2.status_code == 200
    assert r2.json()["canonical_id"] == cid
    assert r2.json()["alias_status"] == "active"


def test_bind_duplicate_alias_in_same_namespace_returns_409(client):
    cid = client.post("/cells", json=GOSFORD_L8).json()["canonical_id"]
    client.post("/namespaces", json={"namespace": CC_NAMESPACE, "prefix": CC_PREFIX})
    client.post("/aliases", json={
        "canonical_id": cid, "alias": "CC-9", "alias_namespace": CC_NAMESPACE,
    })
    # Register a second cell under a distinct cell_key to bind to
    other = dict(GOSFORD_L8)
    other.update({"cell_key": "hsam:r08:cc:fdbez2t74v8xvxwj",
                  "face_grid_u": 50679, "face_grid_v": 8290})
    cid2 = client.post("/cells", json=other).json()["canonical_id"]

    r = client.post("/aliases", json={
        "canonical_id": cid2, "alias": "CC-9", "alias_namespace": CC_NAMESPACE,
    })
    assert r.status_code == 409
    assert r.json()["error"] == "alias_conflict"


def test_resolve_alias_without_namespace_returns_400(client):
    r = client.get("/resolve/alias", params={"alias": "CC-421"})
    assert r.status_code == 400
    assert r.json()["error"] == "namespace_required"


def test_resolve_unknown_alias_returns_404(client):
    client.post("/namespaces", json={"namespace": CC_NAMESPACE, "prefix": CC_PREFIX})
    r = client.get("/resolve/alias", params={"alias": "ZZ-999", "namespace": CC_NAMESPACE})
    assert r.status_code == 404


def test_retire_alias_then_resolve_returns_404(client):
    cid = client.post("/cells", json=GOSFORD_L8).json()["canonical_id"]
    client.post("/namespaces", json={"namespace": CC_NAMESPACE, "prefix": CC_PREFIX})
    client.post("/aliases", json={
        "canonical_id": cid, "alias": "CC-12", "alias_namespace": CC_NAMESPACE,
    })
    r = client.post("/aliases/retire", json={
        "alias": "CC-12", "alias_namespace": CC_NAMESPACE,
    })
    assert r.status_code == 200
    assert r.json()["status"] == "retired"

    # Active-only lookup should now 404
    r2 = client.get("/resolve/alias", params={"alias": "CC-12", "namespace": CC_NAMESPACE})
    assert r2.status_code == 404


# -------------------------------------------------------------------------
# Namespaces
# -------------------------------------------------------------------------

def test_register_namespace_initialises_counter(client):
    r = client.post("/namespaces", json={"namespace": CC_NAMESPACE, "prefix": CC_PREFIX})
    assert r.status_code == 201
    body = r.json()
    assert body["namespace"] == CC_NAMESPACE
    assert body["prefix"] == CC_PREFIX
    assert body["next_counter"] == 1
    assert body["status"] == "active"


def test_register_namespace_with_initial_counter(client):
    r = client.post("/namespaces", json={
        "namespace": CC_NAMESPACE, "prefix": CC_PREFIX, "initial_counter": 422,
    })
    assert r.status_code == 201
    assert r.json()["next_counter"] == 422


def test_duplicate_namespace_returns_409(client):
    client.post("/namespaces", json={"namespace": CC_NAMESPACE, "prefix": CC_PREFIX})
    r = client.post("/namespaces", json={"namespace": CC_NAMESPACE, "prefix": "CX"})
    assert r.status_code == 409


# -------------------------------------------------------------------------
# Adjacency ring
# -------------------------------------------------------------------------

@pytest.mark.parametrize("depth,expected_count", [(1, 8), (2, 16), (3, 24)])
def test_adjacency_ring_depth(client, depth, expected_count):
    client.post("/cells", json=GOSFORD_L8)
    r = client.get(
        f"/cells/{GOSFORD_L8['cell_key']}/adjacency",
        params={"depth": depth},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["depth"] == depth
    assert len(body["ring"]) == expected_count


def test_adjacency_ring_depth_4_returns_400(client):
    client.post("/cells", json=GOSFORD_L8)
    r = client.get(
        f"/cells/{GOSFORD_L8['cell_key']}/adjacency",
        params={"depth": 4},
    )
    assert r.status_code == 400
    assert r.json()["error"] == "invalid_depth"


def test_adjacency_ring_for_unknown_cell_returns_404(client):
    # Valid-format cell_key that has never been registered
    unknown = "hsam:r08:cc:0000000000000000"
    r = client.get(f"/cells/{unknown}/adjacency", params={"depth": 1})
    assert r.status_code == 404


# Non-boundary cell guard — pins the spec's "exactly 8k cells" claim.
# The Level 8 Gosford cell (cube_face=1, u=50678, v=8290) is 8290 cells
# from the nearest face edge; at k<=3 its ring is entirely intra-face.
# cell_adjacency_spec.md §4.1 says "containing exactly 8k cells" for
# non-boundary rings. This test fails if get_adjacency_ring drifts away
# from the 8k formula.
@pytest.mark.parametrize("depth,spec_count", [(1, 8), (2, 16), (3, 24)])
def test_adjacency_ring_matches_spec_8k_formula_non_boundary(client, depth, spec_count):
    client.post("/cells", json=GOSFORD_L8)
    r = client.get(
        f"/cells/{GOSFORD_L8['cell_key']}/adjacency",
        params={"depth": depth},
    )
    assert r.status_code == 200
    ring = r.json()["ring"]
    assert len(ring) == spec_count, f"spec §4.1 requires exactly 8k={spec_count} cells at depth {depth}"
    # All ring members must be on the same face (this is a non-boundary cell)
    faces = {node["face"] for node in ring}
    assert faces == {GOSFORD_L8["cube_face"]}, (
        f"non-boundary ring crossed a face boundary: faces={faces}. "
        "Test-cell placement must be revisited."
    )


# -------------------------------------------------------------------------
# Fidelity coverage — PATCH /cells/{cell_key}/fidelity
# 7 cases per session brief: happy path, 404, missing fields, invalid
# status, available+null source, idempotency, full replacement.
# -------------------------------------------------------------------------

VALID_FIDELITY = {
    "structural": {
        "status": "available",
        "source": "nsw_planning_portal",
        "captured_at": "2026-04-25",
    },
    "photorealistic": {
        "status": "pending",
        "source": None,
        "captured_at": None,
    },
}


def test_patch_fidelity_happy_path(client):
    # TC1 — happy path: valid body → 200, fidelity_coverage persisted.
    cid = client.post("/cells", json=GOSFORD_L8).json()["canonical_id"]
    cell_key = GOSFORD_L8["cell_key"]

    r = client.patch(f"/cells/{cell_key}/fidelity", json=VALID_FIDELITY)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["canonical_id"] == cid
    assert body["cell_key"] == cell_key
    fc = body["fidelity_coverage"]
    assert fc["structural"]["status"] == "available"
    assert fc["structural"]["source"] == "nsw_planning_portal"
    assert fc["photorealistic"]["status"] == "pending"
    assert fc["photorealistic"]["source"] is None


def test_patch_fidelity_cell_not_found_returns_404(client):
    # TC2 — cell_key does not exist → 404.
    unknown_key = "hsam:r08:cc:0000000000000000"
    r = client.patch(f"/cells/{unknown_key}/fidelity", json=VALID_FIDELITY)
    assert r.status_code == 404
    assert r.json()["error"] == "cell_not_found"


def test_patch_fidelity_missing_structural_returns_422(client):
    # TC3a — structural missing → 422.
    client.post("/cells", json=GOSFORD_L8)
    cell_key = GOSFORD_L8["cell_key"]
    body = {"photorealistic": VALID_FIDELITY["photorealistic"]}
    r = client.patch(f"/cells/{cell_key}/fidelity", json=body)
    assert r.status_code == 422


def test_patch_fidelity_missing_photorealistic_returns_422(client):
    # TC3b — photorealistic missing → 422.
    client.post("/cells", json=GOSFORD_L8)
    cell_key = GOSFORD_L8["cell_key"]
    body = {"structural": VALID_FIDELITY["structural"]}
    r = client.patch(f"/cells/{cell_key}/fidelity", json=body)
    assert r.status_code == 422


def test_patch_fidelity_invalid_structural_status_returns_422(client):
    # TC4 — invalid status value → 422.
    client.post("/cells", json=GOSFORD_L8)
    cell_key = GOSFORD_L8["cell_key"]
    body = {
        "structural": {"status": "fully_mapped", "source": None, "captured_at": None},
        "photorealistic": VALID_FIDELITY["photorealistic"],
    }
    r = client.patch(f"/cells/{cell_key}/fidelity", json=body)
    assert r.status_code == 422


def test_patch_fidelity_invalid_photorealistic_status_returns_422(client):
    # TC4b — invalid photorealistic status value → 422.
    client.post("/cells", json=GOSFORD_L8)
    cell_key = GOSFORD_L8["cell_key"]
    body = {
        "structural": VALID_FIDELITY["structural"],
        "photorealistic": {"status": "scanned", "source": None, "captured_at": None},
    }
    r = client.patch(f"/cells/{cell_key}/fidelity", json=body)
    assert r.status_code == 422


def test_patch_fidelity_available_with_null_source_returns_422(client):
    # TC5 — status=available but source=null → 422 (rule: available requires source).
    client.post("/cells", json=GOSFORD_L8)
    cell_key = GOSFORD_L8["cell_key"]
    body = {
        "structural": {"status": "available", "source": None, "captured_at": None},
        "photorealistic": VALID_FIDELITY["photorealistic"],
    }
    r = client.patch(f"/cells/{cell_key}/fidelity", json=body)
    assert r.status_code == 422


def test_patch_fidelity_idempotent(client):
    # TC6 — same PATCH twice produces the same result.
    client.post("/cells", json=GOSFORD_L8)
    cell_key = GOSFORD_L8["cell_key"]

    r1 = client.patch(f"/cells/{cell_key}/fidelity", json=VALID_FIDELITY)
    assert r1.status_code == 200
    r2 = client.patch(f"/cells/{cell_key}/fidelity", json=VALID_FIDELITY)
    assert r2.status_code == 200
    assert r1.json()["fidelity_coverage"] == r2.json()["fidelity_coverage"]


def test_patch_fidelity_full_replacement(client):
    # TC7 — second PATCH with different values fully replaces first (no merge).
    client.post("/cells", json=GOSFORD_L8)
    cell_key = GOSFORD_L8["cell_key"]

    first = {
        "structural": {"status": "available", "source": "source_a", "captured_at": "2026-01-01"},
        "photorealistic": {"status": "pending", "source": None, "captured_at": None},
    }
    second = {
        "structural": {"status": "unavailable", "source": None, "captured_at": None},
        "photorealistic": {
            "status": "available",
            "source": "photogrammetry_pipeline",
            "captured_at": "2026-04-25",
        },
    }

    r1 = client.patch(f"/cells/{cell_key}/fidelity", json=first)
    assert r1.status_code == 200
    assert r1.json()["fidelity_coverage"]["structural"]["status"] == "unavailable" \
        or r1.json()["fidelity_coverage"]["structural"]["source"] == "source_a"

    r2 = client.patch(f"/cells/{cell_key}/fidelity", json=second)
    assert r2.status_code == 200
    fc = r2.json()["fidelity_coverage"]
    # Full replacement: structural must reflect second body, not first.
    assert fc["structural"]["status"] == "unavailable"
    assert fc["structural"]["source"] is None
    assert fc["photorealistic"]["status"] == "available"
    assert fc["photorealistic"]["source"] == "photogrammetry_pipeline"
    # "source_a" must not survive — it was overwritten.
    assert fc["structural"].get("source") != "source_a"
