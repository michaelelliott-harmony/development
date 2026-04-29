# WS-F Experiment F1 — Data Pull Complete
## Gosford CBD Bounding Box

**Author:** Dr. Kofi Boateng, Chief Geospatial Officer
**Date:** 29 April 2026
**Status:** PATH A COMPLETE — Path B documented for manual execution
**Bounding Box:** South -33.45, North -33.40, West 151.30, East 151.36

---

## Executive Summary

Path A (WCS automated elevation pull) is **complete and validated**.
The 5m DEM for Gosford CBD has been downloaded, validated, and the
adapter specification documented for Pillar 2 integration.

Path B (ELVIS 1m DEM + LiDAR) is **documented and ready** for manual
execution by a human operator.

---

## Path A — WCS GetCoverage: COMPLETE ✅

### Request Executed

```bash
curl -o gosford-dem-5m.tif \
  "https://services.ga.gov.au/gis/services/DEM_LiDAR_5m_2025/MapServer/WCSServer
   ?service=WCS&version=1.0.0&request=GetCoverage&coverage=1
   &CRS=EPSG:4283&BBOX=151.30,-33.45,151.36,-33.40
   &width=1089&height=969&format=GeoTIFF"
```

### WCS Version Note

The GA ArcGIS Server WCS implementation has a version-specific quirk:

| Version | GetCoverage | Coverage ID |
|---|---|---|
| WCS 1.0.0 | ✅ HTTP 200 | `1` |
| WCS 2.0.1 | ❌ HTTP 400 | `Coverage1` |

WCS 2.0.1 `GetCapabilities` and `DescribeCoverage` work correctly, but
`GetCoverage` returns HTTP 400 regardless of subset parameter formatting.
This is an ArcGIS Server implementation limitation, not an OGC standard
issue. **WCS 1.0.0 is the working protocol for data retrieval.**

This is documented in the adapter spec for the Pillar 2 team.

### Validated Result

| Property | Value |
|---|---|
| HTTP status | 200 |
| Content-Type | image/tiff |
| File size | 4,719,850 bytes (4.5 MB) |
| Dimensions | 1,089 × 969 pixels |
| CRS | EPSG:4283 (GDA94) |
| Band count | 1 (float32) |
| Elevation min | 0.07 m |
| Elevation max | 253.15 m |
| Elevation mean | 50.80 m |
| Elevation median | 17.76 m |
| Std deviation | 62.72 m |
| Valid pixels | 1,055,241 (100.0%) |
| NoData pixels | 0 |
| Bbox W | 151.300000° (exact match) |
| Bbox E | 151.360000° (exact match) |
| Bbox S | -33.450000° (exact match) |
| Bbox N | -33.400000° (exact match) |
| Centre pixel | 15.51 m at (151.33°, -33.425°) |

### Elevation Data Assessment

The statistics are geographically plausible for Gosford CBD:

- **Median 17.76m** — consistent with low-lying CBD near Brisbane Water
- **Min 0.07m** — waterfront/shoreline areas
- **Max 253.15m** — hills to the west/south of the CBD (Rumbalara Reserve
  area reaches ~200m; surrounding ridgelines reach higher)
- **100% valid** — full LiDAR coverage, no gaps
- **Centre pixel 15.51m** — reasonable for mid-CBD area near the train
  station, slightly elevated above the waterfront

### Compatibility with ADR-015 (Volumetric Cells)

The 5m DEM accuracy (vertical ~0.30m at 95% confidence) is well within
the ADR-015 volumetric band minimum thickness of 0.5m. Elevation values
from this DEM can be used directly for:

- Surface cell height assignment
- Volumetric cell band boundary determination
- Terrain-relative altitude calculations for vertical stacking

---

## Path B — ELVIS Manual Download: DOCUMENTED ✅

Instructions filed at:
```
04_pillars/pillar-2-data-ingestion/data/wfs-f1/ELVIS-1m-download-instructions.md
```

Awaiting manual execution. Expected outputs:
- 1m DEM GeoTIFF (~30–80 MB)
- LiDAR point cloud LAZ (~370–620 MB)

---

## Files Produced

| File | Location | Purpose |
|---|---|---|
| `gosford-dem-5m.tif` | `data/wfs-f1/` | 5m DEM (gitignored; reproduce via README) |
| `README.md` | `data/wfs-f1/` | Reproduction instructions for binary |
| `ELVIS-1m-download-instructions.md` | `data/wfs-f1/` | Path B manual workflow |
| `wcs-elevation-adapter-spec.md` | `docs/` | Pillar 2 WCS adapter specification |
| `ws-f-experiment-f1-data-pull-20260429.md` | `docs/reports/` | This report |

---

## Next Steps

1. **Manual execution of Path B** — human operator downloads 1m DEM +
   LiDAR from ELVIS portal
2. **Pillar 2 integration** — Dr. Adeyemi's team implements the WCS
   adapter per the specification
3. **Imagery endpoint integration** — NSW Spatial Services WMS/WMTS
   adapter for aerial photography (separate adapter spec needed)
4. **Cell registration** — Feed validated elevation data into Harmony
   cell metadata via `PATCH /cells/{cell_key}/fidelity`

---

*WS-F Experiment F1 Path A complete. Path B documented. Adapter spec filed.*

**HARMONY UPDATE:** WS-F F1 Path A executed — 5m DEM downloaded and validated
for Gosford CBD bbox via GA WCS 1.0.0. WCS adapter spec filed. ELVIS 1m
instructions filed. NSW imagery endpoint confirmed at 10cm GSD. Three
deliverables committed: data README, ELVIS instructions, WCS adapter spec.
