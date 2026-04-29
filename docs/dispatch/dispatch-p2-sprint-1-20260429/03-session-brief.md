# Session Brief — Sprint 1 Execution Plan

**Branch:** `feature/p2-sprint-1-cherry-pick`  
**Base:** `main`  
**Target PR:** against `main`

---

## Phase 1 — Branch Setup

```bash
cd /workspace/development
git checkout main
git pull origin main
git checkout -b feature/p2-sprint-1-cherry-pick
```

---

## Phase 2 — Cherry-Pick Sound Modules from Branch B

Fetch all remotes, then check out the listed paths from Branch B directly
into your working tree. This is a selective file checkout, not a branch merge.

```bash
git fetch origin

# Cherry-pick the sound pipeline modules from Branch B
# All paths are relative to the repository root
git checkout origin/claude/pillar-2-sprint-1-m1m2-ef4b6132 -- \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/adapters/ \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/normalise.py \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/validate.py \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/quarantine.py \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/cell_key.py \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/assign.py \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/manifest.py \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/dedup.py \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/registry.py \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/runner.py \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/p1_client.py \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/extract.py \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/manifests/
```

> **Note — extract.py added by Marcus Webb:**
> `extract.py` is not in the original dispatch instruction's cherry-pick list
> but is a required module: it is imported by `runner.py` and is the direct
> target of Modification 1. Authority: file routing → Marcus Webb.
> Resolution: include it. It is present on Branch B at the path above.

> **Note — manifests/ path corrected by Marcus Webb:**
> The original instruction listed `manifests/` as the cherry-pick path.
> On Branch B, the manifests live at
> `04_pillars/pillar-2-data-ingestion/harmony/pipelines/manifests/`.
> The corrected path above is authoritative.

---

## Phase 3 — Harvest CLI Packaging from Branch A

Check out `setup.py` from Branch A to get the `harmony-ingest` CLI entry point:

```bash
git checkout origin/claude/p2-m1-source-adapters -- \
  04_pillars/pillar-2-data-ingestion/setup.py
```

Verify the entry point is present in `setup.py`:
```
entry_points={
    "console_scripts": [
        "harmony-ingest=harmony.pipelines.cli:cli",
    ]
}
```

If `harmony/pipelines/cli.py` is not present in your working tree (it lives
on Branch A but not Branch B), also check it out:
```bash
git checkout origin/claude/p2-m1-source-adapters -- \
  04_pillars/pillar-2-data-ingestion/harmony/pipelines/cli.py
```

---

## Phase 4 — Apply Five V2.0 Compliance Modifications

Apply modifications in the order listed. Each has a governing ADR.

### MODIFICATION 1 — extract.py
**Standards:** STD-V01, STD-V05, E1  
**ADR:** ADR-024 §2.1 and §2.5

**Change 1a — source_lineage JSONB object (STD-V01)**

Replace the flat `source` field on the entity payload with the structured
`source_lineage` JSONB object. The object must contain all seven sub-fields
as specified in ADR-024 §2.1:

```python
source_lineage = {
    "source_dataset_id":       manifest.get("dataset_name", "unknown"),
    "source_dataset_date":     manifest.get("source_dataset_date"),  # nullable
    "source_organisation":     manifest.source_authority,
    "source_licence":          manifest.get("source_licence", "unknown"),
    "process_steps": [
        {
            "step_name":        "ingest",
            "step_description": f"Harmony P2 ingestion run {run_id}",
            "step_datetime":    datetime.now(timezone.utc).isoformat(),
        }
    ],
    "processing_organisation": "harmony",
    "processing_date":         datetime.now(timezone.utc).isoformat(),
}
```

This replaces any existing flat `source` key in the entity metadata payload.

**Change 1b — valid_from mandatory where source carries feature date (STD-V05)**

After building the entity payload, check if the manifest declares
`carries_feature_dates: true`. If it does:
- Attempt to populate `valid_from` from the feature's properties using the
  temporal field mappings in the manifest (V2.0 brief Section 4.3).
  Common source field names: `observation_date`, `createdate`, `start_date`,
  `survey_date`, `capture_date`.
- If `valid_from` cannot be populated and `carries_feature_dates` is `true`,
  quarantine the feature with reason `Q4_SCHEMA_VIOLATION` and message
  `"valid_from mandatory for date-carrying dataset but no date found in feature"`.
- Do NOT quarantine if `carries_feature_dates` is `false` or absent.

Add `carries_feature_dates` as a boolean property to `DatasetManifest`
in `manifest.py` (defaulting to `False`).

**Change 1c — known_names empty = validation failure (E1)**

The current code treats empty `known_names` as a warning. This must become
a hard validation failure. After building `known_names`:
- If `known_names` is an empty list AND the entity type has known source
  name fields (i.e., the manifest attribute_mapping maps at least one name
  field), quarantine the feature with reason `Q4_SCHEMA_VIOLATION` and
  message `"known_names is empty — mandatory name population failed for
  entity_type={entity_type}"`.
- An entity with no available source names from a dataset that carries names
  cannot be registered.

---

### MODIFICATION 2 — runner.py
**Standards:** STD-V02, F1  
**ADR:** ADR-024 §2.2, ADR-022 D2

**Change 2a — data_quality on asset bundle record (NOT cell record)**

The `data_quality` object belongs on the **asset bundle record**.
Dr. Voss ruling (DEC-020): quality describes the captured representation,
not the spatial container.

In `runner.py`, when the pipeline builds or posts an asset bundle record,
attach the `data_quality` object:

```python
data_quality = {
    "completeness_percent":      None,   # nullable — not assessed at ingestion
    "positional_accuracy_metres": manifest.positional_accuracy_m,
    "last_validated":            None,   # nullable — not assessed at ingestion
}
```

Do NOT add `data_quality` to cell records or entity metadata.

**Change 2b — field_descriptors on cell payload**

When building the cell registration payload in `_register_cell()`, add:

```python
payload["field_descriptors"] = {}   # empty JSONB — must not be populated at ingestion
```

This satisfies ADR-023 / ADR-017: `field_descriptors` must be present as
empty JSONB and must not be populated by the ingestion pipeline.

---

### MODIFICATION 3 — normalise.py
**Standards:** STD-V03  
**ADR:** ADR-024 §2.3

Add `crs_authority` and `crs_code` to the normalised geometry record.
These fields go on the geometry record output from `normalise()`.

In the `normalise()` function, after building the result dict, add:

```python
result["crs_authority"] = "EPSG"
result["crs_code"] = 4326
```

These are constants — Harmony is a single-CRS system. Every normalised
geometry record declares its CRS via the authority+code compact form
per ISO 19111.

Also update the `NormalisedFeature` TypedDict in `normalise.py` to
include these two fields:
```python
crs_authority: str
crs_code: int
```

And update `RawFeature` or `NormalisedFeature` in `adapters/base.py` if
the downstream geometry record contract is defined there.

---

### MODIFICATION 4 — manifest.py
**Standards:** ADR-022 D3 (Tier range), ADR-018  
**Reference:** ADR-022 §D3: "Source tiers are 1–4 per ADR-018 (Tier 0 does not exist)"

In `DatasetManifest._validate()`, add enforcement of the source_tier range:

```python
tier = data.get("source_tier")
if tier is not None:
    tier_int = int(tier)
    if tier_int < 1 or tier_int > 4:
        raise ManifestError(
            f"source_tier must be 1–4 per ADR-018. "
            f"Got {tier_int!r}. Tier 0 is not assignable."
        )
```

This enforces the hard rule: **Tier 0 must not be assignable**. Any manifest
with `source_tier: 0` or `source_tier: 5` or higher will fail validation
before any features are processed.

Also add the `carries_feature_dates` property needed by Modification 1:

```python
@property
def carries_feature_dates(self) -> bool:
    return bool(self._data.get("carries_feature_dates", False))
```

---

### MODIFICATION 5 — All Adapters (DEC-021)
**Standards:** DEC-021 (egress proxy HTTP/2 enforcement)  
**Files:** `adapters/arcgis_rest_adapter.py`, `adapters/osm_adapter.py`,
           `adapters/file_adapter.py` (if it uses requests), any other
           adapter that imports `requests`

**Replace ALL occurrences of `import requests` with `import httpx`.**

This is a **hard requirement, not a preference**:
- The egress proxy enforces HTTP/2 for all NSW government endpoints
- `requests` produces HTTP 503 on NSW Planning Portal and NSW Spatial Services
- `httpx[http2]` is the required transport

**In every adapter, replace:**
```python
import requests
```
**with:**
```python
import httpx
```

**And replace all call sites:**
- `requests.get(url, ...)` → `httpx.get(url, ...)`
- `requests.Session()` → `httpx.Client()`
- `session.get(url, ...)` → `client.get(url, ...)`
- Response handling is API-compatible; `.json()`, `.status_code`,
  `.raise_for_status()` all work identically

**In setup.py**, replace the `requests` dependency with `httpx[http2]`:
```python
# Remove:
"requests>=2.31.0,<3",
# Add:
"httpx[http2]>=0.27.0,<1",
```

Verify after the change that no `import requests` remains anywhere in
`04_pillars/pillar-2-data-ingestion/`:
```bash
grep -r "import requests" 04_pillars/pillar-2-data-ingestion/
```
This must return no results.

---

## Phase 5 — Run the Full Test Suite

From `04_pillars/pillar-2-data-ingestion/`:

```bash
pip install -e ".[dev]"
pytest --tb=short -v
```

All tests must pass. The Sprint 1 acceptance criteria from V2.0 brief
§6.2 are your bar. See file `04-acceptance-criteria.md` in this dispatch
for the complete list.

If tests fail:
1. Fix the failure — do not skip tests
2. If a test expects old behaviour that the compliance modifications
   change (e.g., a test expecting flat `source` field), update the test
   to expect the new `source_lineage` structure
3. Document every test update in your session report

---

## Phase 6 — Commit and Open PR

```bash
git add 04_pillars/pillar-2-data-ingestion/
git commit -m "feat(p2-sprint-1): cherry-pick Branch B + 5 V2.0 compliance modifications

- Cherry-pick pipeline modules from origin/claude/pillar-2-sprint-1-m1m2-ef4b6132
- Harvest CLI packaging (setup.py) from origin/claude/p2-m1-source-adapters
- MOD1: extract.py — source_lineage JSONB (ADR-024 STD-V01), valid_from
  mandatory (STD-V05), known_names empty = validation failure (E1)
- MOD2: runner.py — data_quality on asset bundle (ADR-024 STD-V02),
  field_descriptors empty JSONB on cell payload (ADR-022)
- MOD3: normalise.py — crs_authority + crs_code on geometry records (ADR-024 STD-V03)
- MOD4: manifest.py — source_tier range 1-4 enforced, Tier 0 not assignable (ADR-022)
- MOD5: All adapters — requests → httpx[http2] (DEC-021, egress proxy requirement)

Resolves Sprint 1 blockers. All Sprint 1 AC (Section 6.2) passing.
ADRs: ADR-022, ADR-024. DEC: DEC-017, DEC-021."

git push -u origin feature/p2-sprint-1-cherry-pick
```

Open a PR against `main`. PR description must include:
- Summary of all five modifications and their governing ADRs
- Test results (number passing)
- Any decisions made during the session
