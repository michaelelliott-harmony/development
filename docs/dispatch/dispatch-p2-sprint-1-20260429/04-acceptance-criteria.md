# Sprint 1 Acceptance Criteria
## Source: V2.0 Brief §6.2 + V2.0 Compliance Modifications

All criteria below must pass before the PR is opened.

---

## M1 — Source Adapters and CLI

| ID | Criterion | How to Verify |
|---|---|---|
| M1-AC1 | Five source adapters operational: GeoPackage/Shapefile/GeoJSON (file), ArcGIS REST, Overpass/OSM | Run adapter unit tests; all green |
| M1-AC2 | `harmony-ingest` CLI functional via `setup.py` entry point | `pip install -e .` then `harmony-ingest --help` returns usage |
| M1-AC3 | Manifests present for all four Central Coast datasets: buildings, cadastre, roads, zoning | `ls harmony/pipelines/manifests/` shows four YAML files |
| M1-AC4 | Live endpoint validation: NSW Planning Portal (3,866 features), NSW Spatial Services (133,943 features), OSM buildings (47,319), OSM roads (32,712) | Integration tests or endpoint validation script |

---

## M2 — CRS Normalisation

| ID | Criterion | How to Verify |
|---|---|---|
| M2-AC1 | GDA2020 and GDA94 to WGS84 via NTv2 grid. `always_xy=True` confirmed | Normalise test fixture with EPSG:7844 and EPSG:4283 inputs; verify transformation_method = "ntv2" when grid file present |
| M2-AC2 | `source_crs` preserved on output record. `crs_authority` and `crs_code` fields populated (STD-V03) | Inspect normalised feature: `crs_authority == 'EPSG'`, `crs_code == 4326` |
| M2-AC3 | Gosford CBD reference point (lon=151.3428, lat=−33.4271) transformation verified | Assert transformed WGS84 output matches reference within 0.001° |

---

## M3 — Geometry Validation and Quarantine

| ID | Criterion | How to Verify |
|---|---|---|
| M3-AC1 | Seven validation checks in order. Auto-repair for minor issues with 1% area delta guard on `buffer(0)` | Validation test suite; confirmed by test_validate.py |
| M3-AC2 | Quarantine partition active with six reason codes (Q1–Q6). 90-day retention per ADR-021 | QuarantineStore test; confirm all six codes accepted; confirm retention metadata present |
| M3-AC3 | `ValidationReport` includes `threshold_exceeded` flag. Default quarantine rate threshold: 5% | Pass a batch with >5% quarantine rate; verify `threshold_exceeded = True` in report |

---

## V2.0 Compliance — Five Modifications

| ID | Criterion | Governing Reference |
|---|---|---|
| V-01 | `source_lineage` JSONB object present on all entity payloads. All seven sub-fields present. `source` flat field is NOT the sole provenance mechanism | ADR-024 §2.1, STD-V01 |
| V-02 | `valid_from` populated for features from date-carrying datasets. Features missing `valid_from` from a `carries_feature_dates: true` dataset are quarantined with Q4_SCHEMA_VIOLATION | ADR-024 §2.5, STD-V05 |
| V-03 | Empty `known_names` for an entity type that maps name fields → quarantine Q4_SCHEMA_VIOLATION (not a warning) | E1 |
| V-04 | `data_quality` object present on asset bundle records. Three nullable sub-fields. NOT on cell records | ADR-024 §2.2, STD-V02, DEC-020 |
| V-05 | `field_descriptors: {}` (empty JSONB) present on all cell registration payloads. Not populated at ingestion | ADR-022, ADR-017 |
| V-06 | `crs_authority = 'EPSG'` and `crs_code = 4326` present on all normalised geometry records | ADR-024 §2.3, STD-V03 |
| V-07 | `source_tier` range 1–4 enforced in manifest loader. Manifest with `source_tier: 0` raises ManifestError | ADR-022 D3, ADR-018 |
| V-08 | No `import requests` in any adapter file. All HTTP calls via `httpx`. `httpx[http2]` in setup.py | DEC-021 |
| V-09 | `harmony-ingest` entry point present and functional in `setup.py` | M1-AC2 (confirmed from Branch A) |

---

## Test Suite Gate

Before opening the PR:

```bash
grep -r "import requests" 04_pillars/pillar-2-data-ingestion/
# Must return: no output

cd 04_pillars/pillar-2-data-ingestion
pytest --tb=short -v 2>&1 | tail -20
# Must show: no FAILED, no ERROR
```

All acceptance criteria above must be met. No partial credit.
