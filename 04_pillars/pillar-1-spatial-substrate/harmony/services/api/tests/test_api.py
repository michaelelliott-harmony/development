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
