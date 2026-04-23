# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# End-to-end test setup.
#
# The e2e suite at `test_end_to_end.py` is pure-HTTP: tests talk to the
# running API only. The DB clean-up below is SETUP, not test code — it
# matches the brief's explicit SETUP step (dropdb / createdb / migrate).
# It uses subprocess + psql rather than Python DB imports to preserve the
# separation between the test harness and the service code under test.

import os
import subprocess

import pytest


def _run_psql(sql: str) -> None:
    """Execute a SQL statement via psql. Raises on non-zero exit."""
    db_url = os.environ.get("HARMONY_DB_URL", "postgresql://localhost:5432/harmony_dev")
    subprocess.run(
        ["psql", db_url, "-v", "ON_ERROR_STOP=1", "-c", sql],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="session", autouse=True)
def _fresh_db():
    """Truncate the registry tables exactly once before the e2e session.

    Running this suite alongside the API unit tests (which re-use the same
    database) would otherwise see stale records from those tests. This
    fixture runs once per session — after it, the e2e tests populate the
    database with their own records via HTTP.
    """
    _run_psql(
        "TRUNCATE alias_table, entity_table, cell_metadata, "
        "alias_namespace_registry, identity_registry "
        "RESTART IDENTITY CASCADE"
    )
    yield
