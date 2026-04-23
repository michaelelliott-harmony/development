# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Alias Service
#
# Implements the Alias Generation Rules (alias_namespace_rules.md §9),
# Namespace Handling, Alias Lifecycle (§6), Ambiguity Resolution (§5),
# and integration hooks for the Identity Registry Service.
#
# Database: PostgreSQL via psycopg2 (no ORM)
# Connection: HARMONY_DB_URL environment variable
# Reference: alias_namespace_rules.md, ADR-006 (alias namespace model),
#            identity-schema.md §3, id_generation_rules.md
#
# Key design principles:
#   - Aliases are counter-based, NOT property-derived (§9)
#   - Case-insensitive lookup, uppercase storage (§2)
#   - Every resolution call MUST specify a namespace (§7.4)
#   - Alias collisions are surfaced, not silently resolved (§5.3)
#   - 180-day grace period on retired alias reuse (§6)

import os
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "0.1.3"

# Alias format: 2-4 uppercase letters + hyphen + 1-6 digits
# Storage: always uppercase. Lookup: case-insensitive.
ALIAS_FORMAT_RE = re.compile(r"^[A-Z]{2,4}-[0-9]{1,6}$")

# Namespace format: country.state.region.object_class[.sub_class]
# All lowercase, dotted, hierarchical.
NAMESPACE_FORMAT_RE = re.compile(r"^[a-z]{2,4}(\.[a-z0-9_]{2,32}){2,5}$")

# Reserved alias prefixes (alias_namespace_rules.md §8)
RESERVED_PREFIXES = frozenset({"TEST", "DEMO", "TMP", "SYS"})

# Reserved top-level namespace segments (§3)
RESERVED_TOP_LEVEL_SEGMENTS = frozenset({"global", "system", "test"})

# Grace period for retired alias reuse (§6)
GRACE_PERIOD_DAYS = 180

# Crockford Base32 alphabet for alias_id generation
CROCKFORD_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"

logger = logging.getLogger("harmony.alias")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class AliasError(Exception):
    """Base exception for alias operations."""
    pass


class AliasConflictError(AliasError):
    """409 Conflict — alias already active or within grace period."""
    def __init__(self, alias: str, namespace: str, reason: str = ""):
        self.alias = alias
        self.namespace = namespace
        self.reason = reason
        super().__init__(
            f"Alias conflict: ({alias}, {namespace})"
            + (f" — {reason}" if reason else "")
        )


class NamespaceRequiredError(AliasError):
    """400 Bad Request — namespace not provided."""
    def __init__(self):
        super().__init__(
            "Namespace required. Aliases are not unique without a namespace. "
            "Provide a namespace parameter."
        )


class NamespaceNotFoundError(AliasError):
    """404 — namespace not registered."""
    def __init__(self, namespace: str):
        self.namespace = namespace
        super().__init__(f"Namespace not registered: {namespace}")


class AliasNotFoundError(AliasError):
    """404 — alias not found in namespace."""
    def __init__(self, alias: str, namespace: str):
        self.alias = alias
        self.namespace = namespace
        super().__init__(f"Alias not found: ({alias}, {namespace})")


class InvalidAliasFormatError(AliasError):
    """400 — alias does not match format regex."""
    def __init__(self, alias: str):
        self.alias = alias
        super().__init__(
            f"Invalid alias format: {alias!r}. "
            f"Expected: ^[A-Z]{{2,4}}-[0-9]{{1,6}}$"
        )


class InvalidNamespaceFormatError(AliasError):
    """400 — namespace does not match format regex."""
    def __init__(self, namespace: str):
        self.namespace = namespace
        super().__init__(
            f"Invalid namespace format: {namespace!r}. "
            f"Expected: ^[a-z]{{2,4}}(\\.[a-z0-9_]{{2,32}}){{2,5}}$"
        )


class ReservedPrefixError(AliasError):
    """400 — alias uses a reserved prefix."""
    def __init__(self, prefix: str):
        self.prefix = prefix
        super().__init__(
            f"Reserved alias prefix: {prefix}. "
            f"Reserved prefixes: {', '.join(sorted(RESERVED_PREFIXES))}"
        )


# ---------------------------------------------------------------------------
# Validation Helpers
# ---------------------------------------------------------------------------

def validate_alias_format(alias: str) -> str:
    """
    Validate and normalise an alias string.

    Aliases are stored uppercase. Input is normalised to uppercase
    before validation (case-insensitive lookup per §2).

    Returns the normalised (uppercase) alias.

    Raises
    ------
    InvalidAliasFormatError
        If the alias does not match ^[A-Z]{2,4}-[0-9]{1,6}$.
    ReservedPrefixError
        If the alias prefix is reserved (TEST, DEMO, TMP, SYS).
    """
    normalised = alias.upper()
    if not ALIAS_FORMAT_RE.match(normalised):
        raise InvalidAliasFormatError(alias)

    # Check reserved prefix
    prefix = normalised.split("-")[0]
    if prefix in RESERVED_PREFIXES:
        raise ReservedPrefixError(prefix)

    return normalised


def validate_namespace_format(namespace: str) -> str:
    """
    Validate a namespace string.

    Namespaces are always lowercase. Input is normalised to lowercase.

    Returns the normalised namespace.

    Raises
    ------
    InvalidNamespaceFormatError
        If the namespace does not match the format regex.
    """
    normalised = namespace.lower()
    if not NAMESPACE_FORMAT_RE.match(normalised):
        raise InvalidNamespaceFormatError(namespace)
    return normalised


def _extract_prefix(alias: str) -> str:
    """Extract the letter prefix from an alias (e.g., 'CC' from 'CC-421')."""
    return alias.split("-")[0]


def _extract_number(alias: str) -> int:
    """Extract the numeric part from an alias (e.g., 421 from 'CC-421')."""
    return int(alias.split("-")[1])


# ---------------------------------------------------------------------------
# Alias ID Generation
# ---------------------------------------------------------------------------

def _generate_alias_id() -> str:
    """Generate a new alias record ID: al_ + 9-char Crockford Base32 token."""
    import secrets
    raw = secrets.token_bytes(9)
    token = "".join(CROCKFORD_ALPHABET[b % 32] for b in raw)[:9]
    return "al_" + token


# ---------------------------------------------------------------------------
# Namespace Registry Operations
# ---------------------------------------------------------------------------

def register_namespace(
    conn,
    namespace: str,
    prefix: str,
    initial_counter: int = 1,
) -> dict:
    """
    Register a new namespace in the alias_namespace_registry.

    Namespaces are registered entities — creating a new namespace requires
    this explicit registration call. Unregistered namespaces cannot be used
    for alias binding.

    Parameters
    ----------
    conn : psycopg2 connection
    namespace : str
        Fully qualified namespace (e.g., 'au.nsw.central_coast.cells').
    prefix : str
        2-4 uppercase letter prefix for auto-generated aliases in this
        namespace (e.g., 'CC').
    initial_counter : int
        Starting counter value (default 1).

    Returns
    -------
    dict
        The namespace registration record.

    Raises
    ------
    InvalidNamespaceFormatError
        If namespace format is invalid.
    AliasConflictError
        If namespace is already registered.
    ValueError
        If prefix is invalid.
    """
    namespace = validate_namespace_format(namespace)

    # Validate prefix
    prefix = prefix.upper()
    if not re.match(r"^[A-Z]{2,4}$", prefix):
        raise ValueError(
            f"Prefix must be 2-4 uppercase letters, got {prefix!r}"
        )
    if prefix in RESERVED_PREFIXES:
        raise ReservedPrefixError(prefix)

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Check if already registered
        cur.execute(
            "SELECT namespace FROM alias_namespace_registry WHERE namespace = %s",
            (namespace,)
        )
        if cur.fetchone():
            raise AliasConflictError(
                prefix, namespace,
                reason="Namespace already registered"
            )

        now = datetime.now(timezone.utc)
        cur.execute(
            """
            INSERT INTO alias_namespace_registry
                (namespace, prefix, next_counter, status, created_at)
            VALUES (%s, %s, %s, 'active', %s)
            """,
            (namespace, prefix, initial_counter, now)
        )

    conn.commit()
    logger.info("Registered namespace: %s (prefix=%s)", namespace, prefix)

    return {
        "namespace": namespace,
        "prefix": prefix,
        "next_counter": initial_counter,
        "status": "active",
        "created_at": now.isoformat(),
    }


def get_namespace(conn, namespace: str) -> Optional[dict]:
    """
    Look up a registered namespace.

    Returns the namespace record or None if not found.
    """
    namespace = namespace.lower()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            "SELECT * FROM alias_namespace_registry WHERE namespace = %s",
            (namespace,)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def list_namespaces(conn, status: str = "active") -> list:
    """List all registered namespaces with the given status."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """
            SELECT * FROM alias_namespace_registry
            WHERE status = %s
            ORDER BY namespace
            """,
            (status,)
        )
        return [dict(row) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Auto-Generation (alias_namespace_rules.md §9)
# ---------------------------------------------------------------------------

def auto_generate_alias(conn, namespace: str) -> str:
    """
    Auto-generate the next alias in a namespace using the atomic counter.

    The counter is held in alias_namespace_registry, incremented atomically,
    and never decremented. Retiring an alias does NOT decrement the counter.

    Parameters
    ----------
    conn : psycopg2 connection
    namespace : str
        The target namespace.

    Returns
    -------
    str
        The generated alias (e.g., 'CC-422'). Uppercase.

    Raises
    ------
    NamespaceNotFoundError
        If the namespace is not registered.
    """
    namespace = validate_namespace_format(namespace)

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Atomic increment using UPDATE ... RETURNING
        cur.execute(
            """
            UPDATE alias_namespace_registry
            SET next_counter = next_counter + 1
            WHERE namespace = %s AND status = 'active'
            RETURNING prefix, next_counter - 1 AS assigned_counter
            """,
            (namespace,)
        )
        row = cur.fetchone()
        if row is None:
            raise NamespaceNotFoundError(namespace)

        alias = f"{row['prefix']}-{row['assigned_counter']}"

    # Note: we do NOT commit here — the caller controls the transaction
    # boundary so the counter increment is part of the same transaction
    # as the alias binding.
    return alias


# ---------------------------------------------------------------------------
# Alias Binding (Registration)
# ---------------------------------------------------------------------------

def bind_alias(
    conn,
    canonical_id: str,
    alias: str,
    namespace: str,
) -> dict:
    """
    Bind an alias to a canonical ID within a namespace.

    This is the core alias registration operation. It implements the
    registration order from the locked spec:

    1. Validate alias matches format regex
    2. Validate namespace is registered
    3. Attempt atomic INSERT with partial unique constraint:
       UNIQUE (alias, alias_namespace) WHERE status = 'active'
    4. On collision → raise AliasConflictError (409)
    5. On success → return bound tuple

    Parameters
    ----------
    conn : psycopg2 connection
    canonical_id : str
        The canonical ID to bind (must exist in identity_registry).
    alias : str
        The alias string (e.g., 'CC-421'). Normalised to uppercase.
    namespace : str
        The target namespace.

    Returns
    -------
    dict
        The alias binding record.

    Raises
    ------
    InvalidAliasFormatError, ReservedPrefixError
        If alias format is invalid.
    NamespaceNotFoundError
        If namespace is not registered.
    AliasConflictError
        If alias is already active in namespace, or retired within
        the 180-day grace period.
    """
    alias = validate_alias_format(alias)
    namespace = validate_namespace_format(namespace)

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Step 2: Validate namespace is registered
        cur.execute(
            "SELECT 1 FROM alias_namespace_registry WHERE namespace = %s AND status = 'active'",
            (namespace,)
        )
        if cur.fetchone() is None:
            raise NamespaceNotFoundError(namespace)

        # Step 3a: Check for active alias (collision)
        cur.execute(
            """
            SELECT alias_id, canonical_id FROM alias_table
            WHERE UPPER(alias) = %s AND alias_namespace = %s AND status = 'active'
            """,
            (alias, namespace)
        )
        existing = cur.fetchone()
        if existing:
            if existing["canonical_id"] == canonical_id:
                # Idempotent — same binding already exists
                logger.info(
                    "Alias already bound: (%s, %s) -> %s",
                    alias, namespace, canonical_id
                )
                return {
                    "alias_id": existing["alias_id"],
                    "alias": alias,
                    "namespace": namespace,
                    "canonical_id": canonical_id,
                    "status": "active",
                    "created": False,
                }
            raise AliasConflictError(
                alias, namespace,
                reason=f"Already active, bound to {existing['canonical_id']}"
            )

        # Step 3b: Check for retired alias within grace period
        cur.execute(
            """
            SELECT effective_to FROM alias_table
            WHERE UPPER(alias) = %s AND alias_namespace = %s AND status = 'retired'
            ORDER BY effective_to DESC
            LIMIT 1
            """,
            (alias, namespace)
        )
        retired = cur.fetchone()
        if retired and retired["effective_to"]:
            grace_end = retired["effective_to"] + timedelta(days=GRACE_PERIOD_DAYS)
            now = datetime.now(timezone.utc)
            if now < grace_end:
                days_remaining = (grace_end - now).days
                raise AliasConflictError(
                    alias, namespace,
                    reason=(
                        f"Retired within grace period. "
                        f"Reuse available after {grace_end.date().isoformat()} "
                        f"({days_remaining} days remaining)"
                    )
                )

        # Step 4: Insert the binding
        alias_id = _generate_alias_id()
        now = datetime.now(timezone.utc)

        cur.execute(
            """
            INSERT INTO alias_table
                (alias_id, alias, alias_namespace, canonical_id,
                 status, effective_from, effective_to)
            VALUES (%s, %s, %s, %s, 'active', %s, NULL)
            """,
            (alias_id, alias, namespace, canonical_id, now)
        )

    conn.commit()
    logger.info("Bound alias: (%s, %s) -> %s", alias, namespace, canonical_id)

    return {
        "alias_id": alias_id,
        "alias": alias,
        "namespace": namespace,
        "canonical_id": canonical_id,
        "status": "active",
        "effective_from": now.isoformat(),
        "created": True,
    }


def auto_bind_alias(
    conn,
    canonical_id: str,
    namespace: str,
) -> dict:
    """
    Auto-generate and bind an alias for a canonical ID.

    Combines auto_generate_alias and bind_alias in a single transaction.

    Parameters
    ----------
    conn : psycopg2 connection
    canonical_id : str
    namespace : str

    Returns
    -------
    dict
        The alias binding record (includes the generated alias).
    """
    alias = auto_generate_alias(conn, namespace)
    return bind_alias(conn, canonical_id, alias, namespace)


# ---------------------------------------------------------------------------
# Alias Lifecycle (alias_namespace_rules.md §6)
# ---------------------------------------------------------------------------

def retire_alias(
    conn,
    alias: str,
    namespace: str,
) -> dict:
    """
    Retire an active alias. The alias transitions from 'active' to 'retired'.

    The retired alias remains in the database for historical lookup.
    The alias may be reused after the 180-day grace period (§6).

    Retiring an alias does NOT decrement the namespace counter.

    Parameters
    ----------
    conn : psycopg2 connection
    alias : str
    namespace : str

    Returns
    -------
    dict
        The updated alias record.

    Raises
    ------
    AliasNotFoundError
        If no active alias exists with this (alias, namespace) tuple.
    """
    alias = validate_alias_format(alias)
    namespace = validate_namespace_format(namespace)
    now = datetime.now(timezone.utc)

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """
            UPDATE alias_table
            SET status = 'retired', effective_to = %s
            WHERE UPPER(alias) = %s AND alias_namespace = %s AND status = 'active'
            RETURNING alias_id, canonical_id
            """,
            (now, alias, namespace)
        )
        row = cur.fetchone()
        if row is None:
            raise AliasNotFoundError(alias, namespace)

    conn.commit()
    logger.info("Retired alias: (%s, %s)", alias, namespace)

    return {
        "alias_id": row["alias_id"],
        "alias": alias,
        "namespace": namespace,
        "canonical_id": row["canonical_id"],
        "status": "retired",
        "effective_to": now.isoformat(),
    }


# ---------------------------------------------------------------------------
# Alias Resolution (alias_namespace_rules.md §7)
# ---------------------------------------------------------------------------

def resolve_alias(
    conn,
    alias: str,
    namespace: Optional[str] = None,
    include_retired: bool = False,
) -> dict:
    """
    Resolve an alias to a canonical ID.

    Parameters
    ----------
    conn : psycopg2 connection
    alias : str
        The alias to resolve (case-insensitive).
    namespace : str or None
        The namespace to resolve in. REQUIRED — omitting raises
        NamespaceRequiredError (400 Bad Request).
    include_retired : bool
        If True, also resolve retired aliases (§7.2).

    Returns
    -------
    dict
        Resolution result with canonical_id and alias_status.

    Raises
    ------
    NamespaceRequiredError
        If namespace is None.
    AliasNotFoundError
        If the alias is not found (or is retired and include_retired=False).
    """
    if namespace is None:
        raise NamespaceRequiredError()

    alias_upper = alias.upper()
    namespace = validate_namespace_format(namespace)

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        if include_retired:
            # Return most recent binding (active first, then retired)
            cur.execute(
                """
                SELECT alias_id, alias, canonical_id, status,
                       effective_from, effective_to
                FROM alias_table
                WHERE UPPER(alias) = %s AND alias_namespace = %s
                ORDER BY
                    CASE status WHEN 'active' THEN 0 ELSE 1 END,
                    effective_from DESC
                LIMIT 1
                """,
                (alias_upper, namespace)
            )
        else:
            # Active only
            cur.execute(
                """
                SELECT alias_id, alias, canonical_id, status,
                       effective_from, effective_to
                FROM alias_table
                WHERE UPPER(alias) = %s AND alias_namespace = %s
                      AND status = 'active'
                LIMIT 1
                """,
                (alias_upper, namespace)
            )

        row = cur.fetchone()
        if row is None:
            raise AliasNotFoundError(alias, namespace)

        result = {
            "canonical_id": row["canonical_id"],
            "alias": row["alias"],
            "alias_status": row["status"],
            "namespace": namespace,
            "effective_from": row["effective_from"].isoformat() if row["effective_from"] else None,
        }
        if row["status"] == "retired":
            result["effective_to"] = (
                row["effective_to"].isoformat() if row["effective_to"] else None
            )
            result["successor"] = None  # Future: chain lookup
        return result


def resolve_alias_history(
    conn,
    alias: str,
    namespace: str,
) -> list:
    """
    Return the full binding history of an alias in a namespace.

    Returns all bindings (active and retired) in chronological order.
    """
    alias_upper = alias.upper()
    namespace = validate_namespace_format(namespace)

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """
            SELECT alias_id, alias, canonical_id, status,
                   effective_from, effective_to
            FROM alias_table
            WHERE UPPER(alias) = %s AND alias_namespace = %s
            ORDER BY effective_from ASC
            """,
            (alias_upper, namespace)
        )
        return [dict(row) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Query Operations
# ---------------------------------------------------------------------------

def get_aliases_for_canonical(
    conn,
    canonical_id: str,
    status: Optional[str] = None,
) -> list:
    """
    Retrieve all aliases bound to a canonical ID.

    Parameters
    ----------
    conn : psycopg2 connection
    canonical_id : str
    status : str or None
        Filter by status ('active', 'retired'). None returns all.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        if status:
            cur.execute(
                """
                SELECT * FROM alias_table
                WHERE canonical_id = %s AND status = %s
                ORDER BY alias_namespace, alias
                """,
                (canonical_id, status)
            )
        else:
            cur.execute(
                """
                SELECT * FROM alias_table
                WHERE canonical_id = %s
                ORDER BY alias_namespace, alias
                """,
                (canonical_id,)
            )
        return [dict(row) for row in cur.fetchall()]


def list_aliases_in_namespace(
    conn,
    namespace: str,
    status: str = "active",
    limit: int = 100,
    offset: int = 0,
) -> list:
    """List all aliases in a namespace, ordered by alias."""
    namespace = validate_namespace_format(namespace)
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """
            SELECT * FROM alias_table
            WHERE alias_namespace = %s AND status = %s
            ORDER BY alias
            LIMIT %s OFFSET %s
            """,
            (namespace, status, limit, offset)
        )
        return [dict(row) for row in cur.fetchall()]
