# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Database Connection Module
#
# Thin wrapper around psycopg2's ThreadedConnectionPool. The registry
# and alias services use raw SQL via psycopg2 — this module provides
# the connection context manager they need.
#
# Connection string: HARMONY_DB_URL environment variable.
#     Format: postgresql://user:password@host:port/dbname

import os
import logging
from contextlib import contextmanager
from typing import Optional

import psycopg2
from psycopg2 import pool as pg_pool

logger = logging.getLogger("harmony.api.database")

_POOL: Optional[pg_pool.ThreadedConnectionPool] = None


def _get_db_url() -> str:
    db_url = os.environ.get("HARMONY_DB_URL")
    if not db_url:
        raise RuntimeError(
            "HARMONY_DB_URL environment variable is not set. "
            "Expected format: postgresql://user:password@host:port/dbname"
        )
    return db_url


def init_pool(minconn: int = 1, maxconn: int = 10) -> None:
    """Initialise the global connection pool. Safe to call multiple times."""
    global _POOL
    if _POOL is not None:
        return
    _POOL = pg_pool.ThreadedConnectionPool(minconn, maxconn, _get_db_url())
    logger.info("Initialised DB pool (min=%d, max=%d)", minconn, maxconn)


def close_pool() -> None:
    """Close the pool and all connections. Called on app shutdown."""
    global _POOL
    if _POOL is not None:
        _POOL.closeall()
        _POOL = None
        logger.info("Closed DB pool")


@contextmanager
def get_connection():
    """
    Context manager yielding a pooled psycopg2 connection.

    The caller is responsible for committing or rolling back inside
    the with-block. On exit the connection is returned to the pool
    (with a rollback if still in a transaction, for safety).
    """
    if _POOL is None:
        init_pool()
    assert _POOL is not None

    conn = _POOL.getconn()
    try:
        yield conn
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        _POOL.putconn(conn)


def check_health() -> bool:
    """Execute a trivial query to confirm DB connectivity."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        return False
