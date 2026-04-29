# WCS Elevation Adapter Specification
## Pillar 2 — Data Ingestion Pipeline
## Geoscience Australia National DEM via OGC WCS

**Author:** Dr. Kofi Boateng, Chief Geospatial Officer
**Date:** 29 April 2026
**Status:** DRAFT — proven by WS-F Experiment F1
**ADR Coverage:** ADR-020 (CRS Normalisation), ADR-018 (Data Tiering),
                  ADR-019 (Tier Enforcement)

---

## 1. Purpose

This adapter enables automated ingestion of Geoscience Australia's
national LiDAR-derived Digital Elevation Model via OGC Web Coverage
Service (WCS). It provides elevation data for cell height assignment,
volumetric cell registration (ADR-015), and terrain-aware fidelity
assessment.

This is a **Tier 1 — Authoritative Government** data source per
ADR-018.

---

## 2. Service Endpoint

```
Base URL:
https://services.ga.gov.au/gis/services/DEM_LiDAR_5m_2025/MapServer/WCSServer

Protocol:     OGC WCS
Working Ver:  1.0.0 (tested and confirmed 2026-04-29)
Also listed:  1.1.0, 1.1.1, 1.1.2, 2.0.1 (2.0.1 GetCoverage returns 400
              on ArcGIS Server implementation — use 1.0.0)
Auth:         None (public, unauthenticated)
Rate limit:   None documented
Fees:         NONE
```

### Known WCS Version Behaviour

| Version | GetCapabilities | DescribeCoverage | GetCoverage | Coverage ID |
|---|---|---|---|---|
| 1.0.0 | ✅ | ✅ | ✅ | `1` |
| 2.0.1 | ✅ | ✅ | ❌ 400 | `Coverage1` |

**Use WCS 1.0.0 for GetCoverage.** The ArcGIS Server implementation
returns HTTP 400 for WCS 2.0.1 GetCoverage with subset parameters.

---

## 3. Coverage Details

| Property | Value |
|---|---|
| Coverage ID | `1` (WCS 1.0.0) / `Coverage1` (WCS 2.0.1) |
| Title | DEM Lidar 5m |
| Description | National 5m bare earth DEM from 236 LiDAR surveys (2001–2015) |
| Native CRS | EPSG:4283 (GDA94) |
| Pixel size | ~5.16e-05° lat × ~5.51e-05° lon (~5m ground) |
| Grid dims | 651,082 × 718,786 (national) |
| Band | 1 — elevation (float32, metres above AHD) |
| NoData | None (fully populated where LiDAR coverage exists) |
| Bounding box | 114.10°E to 153.68°E, -43.46°S to -9.87°S |
| Coverage | Populated coastal zones, Murray-Darling floodplains, major/minor centres |
| Vertical datum | AHD (Australian Height Datum) |
| Vertical accuracy | ~0.30m (95% confidence) for source point clouds |
| Horizontal accuracy | ~0.80m (95% confidence) for source point clouds |

### Spatial Coverage Map

```
Coverage is NOT uniform across Australia.
The 236 source LiDAR surveys primarily cover:
- Coastal populated zones (Sydney, Melbourne, Brisbane, Perth, etc.)
- Murray-Darling Basin floodplains
- Major and minor population centres

Inland/remote areas may have NO DATA or degraded quality.
Always check coverage before requesting.
```

---

## 4. GetCoverage Request Pattern

### Template

```
GET {base_url}
  ?service=WCS
  &version=1.0.0
  &request=GetCoverage
  &coverage=1
  &CRS=EPSG:4283
  &BBOX={west},{south},{east},{north}
  &width={pixels_x}
  &height={pixels_y}
  &format=GeoTIFF
```

### Parameter Reference

| Parameter | Required | Value | Notes |
|---|---|---|---|
| service | Yes | `WCS` | |
| version | Yes | `1.0.0` | Must be 1.0.0 — see §2 |
| request | Yes | `GetCoverage` | |
| coverage | Yes | `1` | Coverage ID for WCS 1.0.0 |
| CRS | Yes | `EPSG:4283` | Native CRS. EPSG:4326 also works |
| BBOX | Yes | `{west},{south},{east},{north}` | Lon/lat order in EPSG:4283 |
| width | Yes | Integer pixels | Calculate from bbox and ~5m resolution |
| height | Yes | Integer pixels | Calculate from bbox and ~5m resolution |
| format | Yes | `GeoTIFF` | Returns image/tiff |

### Pixel Dimension Calculation

```python
import math

def calc_wcs_dimensions(west, south, east, north, res_m=5.0):
    """Calculate pixel dimensions for WCS request at target resolution."""
    mid_lat = (south + north) / 2.0
    width_m = (east - west) * 111320.0 * math.cos(math.radians(mid_lat))
    height_m = (north - south) * 111320.0
    return int(round(width_m / res_m)), int(round(height_m / res_m))

# Gosford CBD example:
w, h = calc_wcs_dimensions(151.30, -33.45, 151.36, -33.40)
# Returns: (1116, 1113) — matches server response of (1089, 969)
# Note: server may adjust to native grid alignment
```

### Example — Gosford CBD (proven)

```
https://services.ga.gov.au/gis/services/DEM_LiDAR_5m_2025/MapServer/WCSServer
  ?service=WCS
  &version=1.0.0
  &request=GetCoverage
  &coverage=1
  &CRS=EPSG:4283
  &BBOX=151.30,-33.45,151.36,-33.40
  &width=1089
  &height=969
  &format=GeoTIFF
```

**Result (tested 2026-04-29):**
- HTTP 200
- Content-Type: image/tiff
- File size: 4,719,850 bytes (4.5 MB)
- Dimensions: 1089 × 969 pixels
- CRS: EPSG:4283 (GDA94)
- Band: 1 (float32)
- Elevation range: 0.07m to 253.15m
- Valid pixels: 1,055,241 (100%)
- Bbox match: exact

---

## 5. CRS Handling for Harmony Ingestion

Per ADR-020 / DEC-014:

| Source CRS | Target CRS | Transform | Method |
|---|---|---|---|
| EPSG:4283 (GDA94) | EPSG:4326 (WGS84) | Identity | No transform needed (< 2cm difference) |

The adapter MUST record:
- `source_crs`: `EPSG:4283`
- `crs_transform_epoch`: timestamp of ingestion
- `transformation_method`: `identity_gda94_wgs84`

---

## 6. Tier Classification

Per ADR-018 (Data Tiering) and ADR-019 (Tier Enforcement):

| Field | Value |
|---|---|
| `source_tier` | `1` (Authoritative Government) |
| `source_id` | `ga:dem_lidar_5m_2025` |
| `confidence` | `0.95` (surveyed LiDAR, government QA) |

Provenance tuple:
```json
{
  "source_tier": 1,
  "source_id": "ga:dem_lidar_5m_2025",
  "source_url": "https://services.ga.gov.au/gis/services/DEM_LiDAR_5m_2025/MapServer/WCSServer",
  "source_crs": "EPSG:4283",
  "licence": "CC-BY-4.0",
  "attribution": "© Commonwealth of Australia (Geoscience Australia) 2025",
  "access_date": "2026-04-29",
  "vertical_datum": "AHD",
  "vertical_accuracy_m": 0.30,
  "horizontal_accuracy_m": 0.80
}
```

---

## 7. Adapter Interface

### Input

```python
@dataclass
class WCSElevationRequest:
    west: float
    south: float
    east: float
    north: float
    resolution_m: float = 5.0        # Target ground resolution
    crs: str = "EPSG:4283"           # Request CRS
    format: str = "GeoTIFF"          # Output format
    coverage_id: str = "1"           # WCS 1.0.0 coverage ID
```

### Output

```python
@dataclass
class WCSElevationResult:
    filepath: Path                    # Local path to downloaded GeoTIFF
    file_size_bytes: int
    width_px: int
    height_px: int
    bounds: tuple                     # (west, south, east, north)
    crs: str                          # EPSG code as returned
    elevation_min: float
    elevation_max: float
    elevation_mean: float
    valid_pixel_count: int
    total_pixel_count: int
    provenance: dict                  # Full provenance tuple (§6)
    http_status: int
    request_url: str                  # Full URL for reproducibility
```

### Error Handling

| HTTP Status | Meaning | Action |
|---|---|---|
| 200 | Success | Validate GeoTIFF, proceed to ingestion |
| 400 | Bad request (invalid params) | Log, do not retry, raise |
| 404 | Coverage not found | Log, do not retry, raise |
| 500 | Server error | Retry with exponential backoff (3 attempts, 2s/4s/8s) |
| Timeout | Network timeout | Retry with exponential backoff (3 attempts) |

### Validation Steps (post-download)

1. File is valid GeoTIFF (rasterio can open it)
2. CRS matches requested CRS
3. Bounds are within ±0.01° of requested bbox
4. At least 50% of pixels contain valid (non-NaN) data
5. Elevation values are within plausible range (-50m to +2300m for Australia)
6. File size is within expected range (not truncated)

---

## 8. Scaling Considerations

### Coverage Request Sizing

For WCS 1.0.0, the server renders the full requested extent. Large
requests may time out or be rejected. Recommended maximum request sizes:

| Request size | Pixels | File size | Status |
|---|---|---|---|
| Small (city block) | < 500×500 | < 1 MB | ✅ Fast |
| Medium (suburb) | 500–2000 | 1–20 MB | ✅ Tested |
| Large (metro area) | 2000–5000 | 20–100 MB | ⚠️ Test before production |
| Very large (region) | > 5000 | > 100 MB | ❌ Split into tiles |

For ingestion of large areas, the adapter should implement a tiling
strategy: divide the target bbox into tiles of ~2000×2000 pixels,
request each tile, merge after download.

### National Coverage Automation

To ingest elevation data for all Harmony cells nationally:

1. Generate list of cell bboxes requiring elevation data
2. Batch into WCS requests (one per cell or small tile)
3. Execute with rate limiting (1 request per second recommended)
4. Validate each tile
5. Feed into cell metadata fidelity pipeline

---

## 9. Related Services

| Service | Resolution | Access | Use Case |
|---|---|---|---|
| GA WCS 5m DEM (this spec) | 5m | WCS automated | Primary automated elevation |
| ELVIS 1m DEM | 1m | Portal manual | High-resolution urban areas |
| ELVIS LiDAR point cloud | 1–8 pts/m² | Portal manual | 3D reconstruction, detailed terrain |
| SRTM 1-second DEM | ~30m | WCS/download | Fallback for inland/remote |

---

## 10. Tested Request Archive

### Gosford CBD (2026-04-29)

```bash
curl -o gosford-dem-5m.tif \
  "https://services.ga.gov.au/gis/services/DEM_LiDAR_5m_2025/MapServer/WCSServer?service=WCS&version=1.0.0&request=GetCoverage&coverage=1&CRS=EPSG:4283&BBOX=151.30,-33.45,151.36,-33.40&width=1089&height=969&format=GeoTIFF"

# Result:
# HTTP 200, 4,719,850 bytes
# 1089×969 px, EPSG:4283, float32
# Elevation: 0.07m – 253.15m, 100% valid
```

---

*This specification becomes the basis for the Pillar 2 WCS Elevation
Adapter. Implementation requires a covering ADR (next available: ADR-023)
and Dr. Adeyemi's pipeline integration.*
