# WS-F Experiment F1 — Data Directory
## Gosford CBD 5m DEM + Elevation Data

This directory contains data artifacts from WS-F Experiment F1.

**Binary files (`.tif`, `.laz`) are gitignored per project convention.**
Reproduce them using the commands below.

---

## Reproduce: gosford-dem-5m.tif (Path A — WCS)

Tested and confirmed 2026-04-29. Returns a 4.7 MB GeoTIFF.

```bash
curl -o gosford-dem-5m.tif \
  "https://services.ga.gov.au/gis/services/DEM_LiDAR_5m_2025/MapServer/WCSServer?service=WCS&version=1.0.0&request=GetCoverage&coverage=1&CRS=EPSG:4283&BBOX=151.30,-33.45,151.36,-33.40&width=1089&height=969&format=GeoTIFF"
```

### Expected Result

| Property | Value |
|---|---|
| HTTP status | 200 |
| File size | 4,719,850 bytes |
| Dimensions | 1089 × 969 pixels |
| CRS | EPSG:4283 (GDA94) |
| Band | 1 (float32, metres above AHD) |
| Elevation range | 0.07 m – 253.15 m |
| Valid pixels | 1,055,241 (100%) |
| Bbox | W 151.30, S -33.45, E 151.36, N -33.40 |

### Validation

```python
import rasterio
with rasterio.open("gosford-dem-5m.tif") as ds:
    assert ds.crs.to_epsg() == 4283
    assert ds.width == 1089 and ds.height == 969
    assert abs(ds.bounds.left - 151.30) < 0.001
    data = ds.read(1)
    assert data.min() > -10 and data.max() < 300
    print("✅ Valid")
```

---

## Path B — ELVIS 1m DEM + LiDAR (manual)

See `ELVIS-1m-download-instructions.md` in this directory.

Expected output files after manual download:
- `gosford-dem-1m.tif` — 1m DEM GeoTIFF (~30–80 MB)
- `gosford-pointcloud.laz` — LiDAR point cloud (~370–620 MB)

---

## Data Source

- **Provider:** Geoscience Australia / NSW Spatial Services
- **Licence:** Creative Commons Attribution 4.0 (CC BY 4.0)
- **Attribution:** © Commonwealth of Australia (Geoscience Australia) 2025
