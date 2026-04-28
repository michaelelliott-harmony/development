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
    # Apply M7 cell_status DDL to the test DB if not already present.
    # The M7 migration (m7_temporal_field_activation.py) is produced and
    # covers production gating. This IF NOT EXISTS block ensures the dev/test
    # DB has the column before the status endpoint tests run.
    # ADR-016 §2.3 — four-value CHECK matches migration DDL exactly.
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE cell_metadata
                ADD COLUMN IF NOT EXISTS cell_status TEXT
                    NOT NULL DEFAULT 'stable'
                    CHECK (cell_status IN (
                        'stable',
                        'change_expected',
                        'change_in_progress',
                        'change_confirmed'
                    ))
            """)
        conn.commit()
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
