# Harmony API test configuration
#
# Fixtures:
#   _pool       — session-scoped DB pool lifecycle
#   clean_db    — per-test truncation of all registry tables
#   client      — FastAPI TestClient

import os
import sys

import pytest

# Ensure imports work from any cwd
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

os.environ.setdefault("HARMONY_DB_URL", "postgresql://localhost:5432/harmony_dev")

from fastapi.testclient import TestClient  # noqa: E402

from harmony.services.api.main import app  # noqa: E402
from harmony.services.api.database import get_connection, init_pool, close_pool  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _pool():
    init_pool()
    yield
    close_pool()


@pytest.fixture(autouse=True)
def clean_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE alias_table, entity_table, cell_metadata, "
                "alias_namespace_registry, identity_registry "
                "RESTART IDENTITY CASCADE"
            )
        conn.commit()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
