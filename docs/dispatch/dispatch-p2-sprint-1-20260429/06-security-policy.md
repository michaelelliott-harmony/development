# Security Policy — Sprint 1

Read `agents/security/SECURITY_POLICY.md` for the full policy.
The points below are the most relevant to your work this sprint.

---

## Non-Negotiables

**No secrets in code.** API keys, database credentials, tokens — none of
these appear in source code, test fixtures, log output, or commit messages.
Use environment variables. Reference `.env.example` only.

**No direct database access.** All writes to Pillar 1 go via the HTTP API
(`Pillar1Client`). No direct PostgreSQL connections from the ingestion pipeline.

**No external API write connections without Elena's approval.** The ingestion
pipeline reads from external sources; it does not write to them. If you need
to test against a live NSW endpoint, use read-only calls only.

**`httpx[http2]` is required.** This is both a security and operational
requirement: the egress proxy enforces HTTP/2 for NSW government endpoints.
Using `requests` will produce 503 errors and also bypasses the proxy's
connection policy. Never revert to `requests`.

---

## Adapter Security Rules

- All adapter HTTP calls use `httpx` with the egress proxy configuration
- Timeout all external HTTP calls (never hang indefinitely)
- Do not log raw API responses at INFO level — log feature counts only
- Validate source data before processing — never pass unsanitised external
  data directly to a Harmony API call
- `source_crs` must come from the manifest config, not from the source data

---

## Test Fixtures

- Test fixtures use local GeoJSON files, not live endpoints
- If a test needs to mock an external HTTP call, use `httpx` mock/test utilities
- Never commit credentials even in test fixtures or conftest.py
