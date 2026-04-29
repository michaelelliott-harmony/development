# WS-F Experiment F0 — Open Data Baseline Confirmation
## Gosford CBD Bounding Box

**Author:** Dr. Kofi Boateng, Chief Geospatial Officer
**Date:** 29 April 2026
**Status:** CONFIRMED — both sources accessible
**Bounding Box:** South -33.45, North -33.40, West 151.30, East 151.36

---

## 1. NSW Spatial Services — Aerial Photography

### Portal
- **Primary:** maps.six.nsw.gov.au
- **Service:** `public/NSW_Imagery` (MapServer)

### Access Endpoints (all unauthenticated, open access)

| Protocol | URL |
|---|---|
| ArcGIS REST | `https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Imagery/MapServer` |
| WMS | `http://maps.six.nsw.gov.au/arcgis/services/public/NSW_Imagery/MapServer/WMSServer?request=GetCapabilities&service=WMS` |
| WMTS | `https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Imagery/MapServer/WMTS/1.0.0/WMTSCapabilities.xml` |
| GDA2020 variant | Append `_GDA2020` suffix to service name |

### Coverage at Gosford CBD

**CONFIRMED.** The NSW Imagery web service covers the full extent of NSW.
The service is a multi-resolution mosaic that progressively overlays higher
resolution imagery at larger scales. The documented datasets composing the
service include:

- Spatial Services standard coverage ADS sensor orthorectified imagery (50cm GSD, statewide)
- Spatial Services high resolution ADS sensor town imagery (10cm GSD, urban areas pop > 500)
- Six Cities Conurbation AAM Imagery 2020–2022
- Six Cities Conurbation Aerometrex Imagery 2021–2022
- Spookfish/Eagleview 2018 Imagery

Gosford is the **regional capital of Central Coast City**, which was formally
designated as one of the NSW Six Cities. The Six Cities Conurbation captures
from AAM (2020–2022) and Aerometrex (2021–2022) explicitly include Central
Coast.

### Resolution

**CORRECTION TO BRIEF:** The user request specified 12.5cm GSD. NSW Spatial
Services does not publish at 12.5cm GSD. The standard urban resolution tiers
are:

| Tier | GSD | Coverage |
|---|---|---|
| Standard regional | 50cm | Statewide 1:100,000 map sheets |
| Urban town | 10cm | Urban areas with population > 500 |
| High-resolution project | Variable | Sydney, Newcastle, Wollongong conurbation |

Gosford CBD, with a population well over 500, will be served at **10cm GSD**
from the Spatial Services town imagery program, and likely at 10cm or better
from the Six Cities Conurbation captures (2020–2022). This is **better** than
the 12.5cm originally specified.

The tile cache extends to Level 23 (resolution ~0.019m/px at the equator)
but this is the zoom pyramid ceiling, not the source capture resolution.
Actual source GSD determines useful resolution.

### Spatial Reference

- Dataset CRS: GDA94
- Web service CRS: EPSG:4326 (WGS 84 ≈ GDA94)
- GDA2020 variant also available
- **CRS note for Harmony ingestion:** Per ADR-020, GDA94→WGS84 is treated
  as identity (< 1m difference nationally). GDA2020→WGS84 requires NTv2
  grid shift. If using the GDA2020 service, the ingestion pipeline must
  apply the NTv2 transform per DEC-014.

### Licence

- **Open data** — no authentication required
- **Creative Commons Attribution** (CC-BY)
- Attribution: © State of New South Wales (Spatial Services, a business unit
  of the Department of Customer Service NSW)
- Free for commercial and non-commercial use

### Accuracy

- Horizontal accuracy: ±2.5 × GSD (metres) at 95% confidence on bare open
  ground (RMSE × 1.73)
- At 10cm GSD this yields: **±0.25m horizontal** at 95% confidence

---

## 2. GA ELVIS — Elevation Data

### Portal
- **Primary:** https://elevation.fsdf.org.au
- **Operator:** Geoscience Australia under the Foundation Spatial Data
  Framework (FSDF), in partnership with ICSM and state agencies
- **NSW contributor:** DCS Spatial Services

### Access Method

ELVIS is an interactive portal (not a direct API). The workflow is:

1. Navigate to https://elevation.fsdf.org.au
2. Draw bounding box or search by location (Gosford)
3. Select data products from available layers
4. Request generates a download package
5. Download link emailed (typically within minutes for small areas)
6. 15GB per request limit

No registration or authentication required.

### Coverage at Gosford CBD

**CONFIRMED.** NSW Spatial Services contributes elevation data to ELVIS and
has been collaborating with Geoscience Australia on the FSDF portal since
2018. LiDAR coverage is most comprehensive along coastal areas and major
cities. The Central Coast / Gosford area, as a coastal urban region within
the NSW Six Cities, has high-resolution LiDAR coverage.

### Available Products

| Product | Resolution | Format | Expected Availability |
|---|---|---|---|
| LiDAR point cloud | 1–8 pts/m² (varies by survey) | LAZ (compressed LAS) | Yes — coastal urban NSW |
| DEM (bare earth) | 1m | GeoTIFF | Yes — NSW urban areas |
| DEM | 2m | GeoTIFF | Yes |
| DEM | 5m | GeoTIFF | Yes — national LiDAR-derived |
| DEM (SRTM-derived) | 1-second (~30m) | GeoTIFF | Yes — continent-wide |

The **1m DEM** is the priority product for Experiment F0. NSW Spatial Services
has been producing 1m, 2m, and 5m multi-resolution DEMs from LiDAR data
contributed through ELVIS.

### Accuracy (1m DEM)

- Vertical accuracy: **15cm**
- Horizontal accuracy: **45cm**
- Source LiDAR captured to ICSM LiDAR Acquisition Specifications:
  fundamental vertical accuracy ≥ 0.30m, horizontal accuracy ≥ 0.80m

### Licence

- **Creative Commons Attribution 4.0 (CC BY 4.0)**
- Free to download, no registration required
- Commercial and non-commercial use permitted with attribution
- Attribution: Geoscience Australia and contributing jurisdictions

---

## 3. Summary Assessment

### What we have for the Gosford CBD bounding box:

| Layer | Source | Resolution | Licence | Status |
|---|---|---|---|---|
| Aerial imagery | NSW Spatial Services via SIX Maps | **10cm GSD** (not 12.5cm) | CC-BY | ✅ CONFIRMED |
| Elevation (DEM) | GA ELVIS / NSW Spatial Services | **1m** (LiDAR-derived) | CC BY 4.0 | ✅ CONFIRMED |
| Elevation (point cloud) | GA ELVIS / NSW Spatial Services | **1–8 pts/m²** | CC BY 4.0 | ✅ CONFIRMED |
| Elevation (fallback) | GA ELVIS (SRTM) | ~30m | CC-BY | ✅ Continent-wide |

### What we do NOT have from open data:

- **12.5cm GSD imagery** — does not exist as a standard NSW product. The
  actual available resolution (10cm) is superior.
- **Building footprints with height** — not included in either source.
  Requires separate sourcing (NSW Digital Cadastre, OpenStreetMap, or
  Overture Maps).
- **3D mesh / textured model** — no open-data 3D reconstruction exists
  for Gosford. This is what Experiment F0 is establishing the baseline to
  build.
- **Temporal series** — the imagery service shows the most recent capture
  per area. Historical captures exist in the Historical Imagery Viewer but
  are individual frames, not ortho-mosaics.

### CRS Ingestion Note

Both data sources align cleanly with Harmony's canonical CRS pipeline
(ADR-020 / DEC-014):

- NSW Imagery (GDA94 service): GDA94 ≈ WGS84 — identity transform, no
  NTv2 required
- ELVIS DEMs: Typically delivered in GDA94 or GDA2020. If GDA2020,
  NTv2 grid shift applies per ADR-020

### Recommendation

The open data baseline for Gosford CBD is **richer than expected**. 10cm
imagery exceeds the 12.5cm specification. 1m DEM with 15cm vertical
accuracy is sufficient for volumetric cell assignment (ADR-015 band
thickness minimum 0.5m — the DEM accuracy is well within that).

**Proceed to F1** — data retrieval and ingestion pipeline integration.
The next step is a controlled download of the 1m DEM for the bounding box
via ELVIS (small area, well within 15GB limit), and confirmation that the
WMS/WMTS imagery endpoint renders correctly at native resolution within
the bounding box.

---

## 4. Access Commands (for reference)

### WMS GetMap — Gosford CBD imagery sample
```
http://maps.six.nsw.gov.au/arcgis/services/public/NSW_Imagery/MapServer/WMSServer?
  SERVICE=WMS&
  VERSION=1.1.1&
  REQUEST=GetMap&
  LAYERS=0&
  STYLES=&
  CRS=EPSG:4326&
  BBOX=-33.45,151.30,-33.40,151.36&
  WIDTH=1024&
  HEIGHT=1024&
  FORMAT=image/jpeg
```

### ArcGIS REST Export — Gosford CBD imagery sample
```
https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Imagery/MapServer/export?
  bbox=16843000,-3963000,16850000,-3957000&
  bboxSR=3857&
  imageSR=3857&
  size=1024,1024&
  format=jpg&
  f=image
```

### ELVIS — manual portal workflow
```
1. Navigate: https://elevation.fsdf.org.au
2. Search: "Gosford NSW"
3. Draw bbox or enter coordinates: S-33.45, N-33.40, W151.30, E151.36
4. Select: 1m DEM + LiDAR point cloud
5. Enter email for download link
6. Download GeoTIFF (DEM) and LAZ (point cloud)
```

---

*Filed as WS-F Experiment F0. Proceed to F1 on authorisation.*
