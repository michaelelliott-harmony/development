# Harmony Spatial Operating System — Pillar I — Spatial Substrate

# ADR-012: Alias Generation Architecture

| Field | Value |
|-------|-------|
| **Title** | Alias Generation Architecture |
| **Status** | Accepted |
| **Date** | April 2026 |
| **Pillar** | 1 — Spatial Substrate |
| **Milestone** | 2 — Identity Services |
| **Deciders** | Mikey (Founder/PM), Architecture Lead (Builder Agent 1), Alias Systems Engineer (Builder Agent 3) |
| **Schema Version Affected** | 0.1.3 |
| **Related** | ADR-001 (Layered Identity), ADR-006 (Alias Namespace Model) |
| **Implements** | `alias_namespace_rules.md` §9 |

---

## Context

ADR-006 established that aliases live in hierarchical dotted namespaces and that the `(alias, namespace)` tuple — not the alias alone — is the unit of identity at the alias layer. It deliberately deferred the question of *how aliases are generated*.

The alias format is `<PREFIX>-<NUMBER>` (regex `^[A-Z]{2,4}-[0-9]{1,6}$`). The number component could be derived in several ways: from properties of the object being aliased, from a hash of the canonical ID, from a random pool, or from a sequential counter. The choice has consequences for collision rates, operational simplicity, human memorability, and the ability to reason about alias ordering.

Two concrete requirements constrain the decision:

1. **Aliases carry no semantic meaning.** They are a usability layer for humans to reference objects without typing opaque canonical IDs. Any meaning implied by the alias (e.g., "CC-421 is the 421st cell registered") is coincidental and must not be relied upon by any service.

2. **Aliases must be unique within a namespace at any point in time.** The generation mechanism must guarantee that two concurrent registrations in the same namespace never produce the same alias.

---

## Decision

Alias generation uses a **per-namespace atomic counter** stored in the `alias_namespace_registry` table.

### Mechanism

Each registered namespace holds a `prefix` (2–4 uppercase letters) and a `next_counter` (integer, starts at 1). When an alias is auto-generated:

```sql
UPDATE alias_namespace_registry
   SET next_counter = next_counter + 1
 WHERE namespace = $1
   AND status = 'active'
RETURNING prefix, next_counter - 1 AS assigned_counter;
```

The `UPDATE ... RETURNING` is atomic: PostgreSQL guarantees that concurrent transactions each receive a distinct counter value. The resulting alias is `{prefix}-{assigned_counter}`.

### Registration Order

The full alias binding sequence (locked per the Architecture Lead's brief) is:

1. **Validate alias format** — must match `^[A-Z]{2,4}-[0-9]{1,6}$` after uppercase normalisation.
2. **Reject reserved prefixes** — `TEST`, `DEMO`, `TMP`, `SYS` are forbidden in production namespaces.
3. **Validate namespace format** — must match `^[a-z]{2,4}(\.[a-z0-9_]{2,32}){2,5}$` after lowercase normalisation.
4. **Verify namespace is registered** — the namespace must exist in `alias_namespace_registry` with `status = 'active'`.
5. **Check active collision** — no active alias with the same `(UPPER(alias), namespace)` tuple may exist.
6. **Check grace period** — if a retired alias with the same tuple exists and was retired fewer than 180 days ago, reject with `409 Conflict` and report days remaining.
7. **Insert binding** — write the new row to `alias_table` with `status = 'active'`.

For auto-generation, step 1 is satisfied by construction (the counter mechanism always produces valid aliases) and step 5 is satisfied by the atomic counter (no two calls receive the same number). Manual assignment follows the same sequence but with a caller-provided alias.

### Counter Properties

- **Monotonically increasing.** The counter is never decremented, even when an alias is retired. This prevents counter reuse and guarantees that `CC-422` is always minted after `CC-421`.
- **Atomic.** PostgreSQL row-level locking on `UPDATE ... RETURNING` ensures no two transactions receive the same counter value.
- **Namespace-scoped.** Each namespace has its own independent counter. `au.nsw.central_coast.cells` at counter 422 has no relationship to `au.qld.cairns_coast.cells` at counter 17.
- **Not a sequence number.** Gaps are expected and normal. If `CC-420` is minted and then `CC-421` is minted but the transaction rolls back, the next successful alias is `CC-422`. The missing `CC-421` is not a bug.

### Table Definition

```sql
CREATE TABLE alias_namespace_registry (
    namespace       TEXT        PRIMARY KEY,
    prefix          VARCHAR(4)  NOT NULL CHECK (prefix ~ '^[A-Z]{2,4}$'),
    next_counter    INTEGER     NOT NULL DEFAULT 1 CHECK (next_counter >= 1),
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active', 'retired')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Lifecycle Integration

The alias lifecycle (free → active → retired) interacts with the counter as follows:

| Event | Counter Effect |
|-------|----------------|
| Auto-generate alias | Counter incremented by 1 |
| Manual bind alias | Counter unchanged |
| Retire alias | Counter unchanged |
| Reuse alias after grace period | Counter unchanged (reuse binds the old alias string, not a new one) |

The counter only advances on auto-generation. All other lifecycle transitions leave it untouched.

---

## Consequences

### Positive

- **Zero collision risk on auto-generation.** The atomic counter guarantees uniqueness within a namespace without any retry logic or conflict resolution.
- **Operationally simple.** One integer column, one UPDATE statement, no external dependencies (no distributed lock, no UUID library, no hash function).
- **Predictable alias density.** The counter value gives operators an approximate count of how many aliases have been minted in a namespace, useful for capacity planning and monitoring.
- **Human-friendly output.** Sequential numbers are easy to communicate verbally ("CC four twenty-one") and easy to type. No ambiguous characters, no case sensitivity in the number portion.
- **Consistent with the locked spec.** Implements `alias_namespace_rules.md` §9 exactly as written.

### Negative

- **Counter value leaks ordering information.** An observer can infer that `CC-422` was registered after `CC-421`. This is a minor information disclosure, mitigated by the fact that aliases are a public usability layer and not a security boundary (§10 of `alias_namespace_rules.md`).
- **Single point of serialisation per namespace.** Under extreme concurrent load, the `UPDATE ... RETURNING` on a single counter row creates a serialisation bottleneck for that namespace. Mitigated by the fact that alias registration is a low-frequency operation (registering new cells/entities, not reading them) and PostgreSQL handles row-level lock contention efficiently at the expected scale.
- **Counter exhaustion at 999,999.** The alias format allows a maximum 6-digit number, capping each namespace at 999,999 auto-generated aliases. At the expected registration rate this is not a concern for years; if approached, the mitigation is to create sub-namespaces (e.g., `au.nsw.central_coast.cells.coastal`) with their own counters.

### Neutral

- Gaps in the counter sequence are expected and not a defect. Rolled-back transactions, skipped manual assignments, and retired aliases all produce gaps. No system should assume the alias number space is dense.

---

## Alternatives Considered

### A. Property-Derived Aliases

Derive the alias number from properties of the object (e.g., hash of cell_key, resolution level, grid position).

**Rejected because:** this couples the alias to the object's internal structure. If the cell_key derivation changes, all aliases become inconsistent. It also violates the spec's explicit statement that aliases carry no semantic meaning and are a usability layer only.

### B. Random Number Generation

Generate a random number in the range [1, 999999] and retry on collision.

**Rejected because:** as the namespace fills, collision probability increases and the retry loop becomes expensive. At 50% fill (500,000 aliases), roughly half of random draws collide. The counter approach has O(1) cost regardless of fill level.

### C. UUID-Based Alias IDs

Use a UUID or ULID as the alias number component.

**Rejected because:** UUIDs are not human-friendly. The entire purpose of the alias layer is short, memorable references. `CC-421` is verbally communicable; `CC-a7f3b9c2` is not. (Note: the alias *record* ID `alias_id` does use a random token — `al_` prefix + 9-char Crockford Base32 — but this is an internal key, not the human-facing alias.)

### D. Global Counter (Single Counter for All Namespaces)

Use one global counter shared across all namespaces.

**Rejected because:** this creates cross-namespace coupling. Registrations in `au.qld.cairns_coast.cells` would advance the counter for `au.nsw.central_coast.cells`, producing confusing gaps. It also creates a single global serialisation point. Per-namespace counters are independent and parallel.

### E. PostgreSQL SEQUENCE Object

Use a PostgreSQL `SEQUENCE` per namespace instead of a counter column.

**Rejected because:** sequences are DDL objects — creating one per namespace requires dynamic DDL (`CREATE SEQUENCE ...`), which complicates migrations, testing, and namespace provisioning. A counter column in a regular table is DML-managed, works within normal transactions, and is trivially portable to other databases if needed.

---

## Implementation Notes

- The `alias_namespace_registry` table is created by migration `002_alias_namespace_registry.sql`.
- The alias service is implemented in `harmony/packages/alias/src/alias_service.py`.
- The `auto_generate_alias()` function performs the atomic `UPDATE ... RETURNING` and constructs the alias string.
- The `bind_alias()` function implements the full 7-step registration order.
- The `auto_bind_alias()` convenience function combines auto-generation with binding in a single call.
- Reserved prefixes (`TEST`, `DEMO`, `TMP`, `SYS`) are validated at format-check time, before any database access.
- The 180-day grace period is enforced in application code, not in the database, consistent with ADR-006's implementation notes.
- The test suite at `harmony/packages/alias/tests/test_alias_service.py` covers format validation, namespace validation, counter properties, reserved prefix rejection, grace period arithmetic, and the full registration flow with mocked database connections.

---

*ADR-012 — Locked*
