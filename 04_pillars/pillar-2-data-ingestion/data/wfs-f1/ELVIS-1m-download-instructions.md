# ELVIS 1m DEM + LiDAR Download Instructions
## WS-F Experiment F1 — Path B (Manual)

**Bounding Box:** South -33.45, North -33.40, West 151.30, East 151.36
**Target Area:** Gosford CBD, Central Coast NSW

---

## Prerequisites

- Web browser (any modern browser)
- Email address for receiving download links

---

## Steps

### 1. Open the ELVIS Portal

Navigate to: **https://elevation.fsdf.org.au**

Dismiss the welcome dialog if shown.

### 2. Navigate to Gosford

Use the search bar in the top-right to search for **"Gosford NSW"**.
The map will centre on the Gosford area.

Zoom in until you can see the Gosford CBD waterfront area clearly.

### 3. Check Available Layers

Click the **Layers** button in the top menu bar.

Enable the following layers to verify coverage:
- **DEM** — shows DEM coverage footprints
- **Point Cloud** — shows LiDAR point cloud coverage footprints

Confirm that blue/green shading covers the Gosford CBD area.
Central Coast is a coastal urban area and should have full coverage.

### 4. Order Data

Click **"Order Data"** (or the equivalent download/order button in
the top menu).

The portal will prompt you to define an area of interest.

### 5. Draw the Bounding Box

Draw a rectangle covering the following coordinates:

| Corner | Latitude | Longitude |
|---|---|---|
| South-West | -33.45 | 151.30 |
| North-East | -33.40 | 151.36 |

If the portal provides a coordinate entry mode, use these values
directly. Otherwise, draw the rectangle manually over Gosford CBD
covering from Brisbane Water to the west/south and extending east
past the train station area.

### 6. Select Products

From the available products list, select:

- [x] **1m DEM** (Digital Elevation Model, 1-metre resolution)
- [x] **Point Cloud** (LiDAR point cloud, LAZ format)

Deselect any other products (5m DEM, bathymetry, etc.) — we already
have the 5m DEM from the WCS endpoint (Path A).

### 7. Submit Order

Enter your email address when prompted.

Click **Submit** or **Order**.

### 8. Note the Estimated Size

Before submitting, the portal may show an estimated download size.
**Record this value.**

Expected estimates for this bounding box:
- 1m DEM: ~30–80 MB (compressed GeoTIFF)
- LiDAR point cloud: ~370–620 MB (LAZ)
- Total: ~0.5–1.0 GB

The 15 GB per-request limit will not be reached.

### 9. Download

Download links will be emailed within a few minutes for small areas.

If the email does not arrive within 30 minutes, check spam/junk folders.

Save downloaded files to this directory:
```
04_pillars/pillar-2-data-ingestion/data/wfs-f1/
```

Expected filenames (actual names may vary):
```
gosford-dem-1m.tif       (1m DEM GeoTIFF)
gosford-pointcloud.laz   (LiDAR point cloud LAZ)
```

### 10. Validation

After download, verify the files:

**For the 1m DEM GeoTIFF:**
```python
import rasterio
with rasterio.open("gosford-dem-1m.tif") as ds:
    print(f"CRS: {ds.crs}")           # Expect EPSG:4283 (GDA94)
    print(f"Size: {ds.width}x{ds.height}")  # Expect ~5580 x 5565
    print(f"Bounds: {ds.bounds}")      # Expect our bbox
    data = ds.read(1)
    print(f"Elev range: {data.min():.1f} to {data.max():.1f} m")
```

**For the LiDAR LAZ:**
```bash
# Using pdal or lasinfo
pdal info gosford-pointcloud.laz --summary
# Should show point count, bbox matching our area,
# CRS in GDA94 or GDA2020, and classification codes
```

---

## Licence

All ELVIS data is licensed under **Creative Commons Attribution 4.0
(CC BY 4.0)**. Attribution required to Geoscience Australia and
contributing state jurisdictions (NSW Spatial Services).

---

*Filed as WS-F Experiment F1 Path B instructions.*
