# WS-F Research Environment Specification
## Gosford CBD 3DGS Reconstruction — Compute, Data, and Pipeline

**Author:** Dr. Kofi Boateng, Chief Geospatial Officer
**Date:** 29 April 2026
**Status:** SPECIFICATION — ready for procurement
**Depends on:** WS-F F0 (data baseline), WS-F F1 (data pull), DEC-023 (Option C)
**Consumed by:** Mikey (procurement), future technical co-founder (inheritance)

---

## 1. Purpose

This document specifies the research environment required to execute
WS-F Experiment F2 — the baseline 3D Gaussian Splatting (3DGS)
reconstruction of Gosford CBD from open data sources confirmed in F0
and pulled in F1.

F2 is the first step toward the demo overlay described in DEC-023
(Option C) and tested at experiential checkpoint P3-EC2. The output
is a `.ply` Gaussian splat file covering the Gosford CBD core,
renderable in a WebGPU viewer.

This is a research environment, not a production pipeline. The goal
is to establish whether the open data we have — nadir aerial imagery
and elevation data — produces a reconstruction of sufficient quality
to justify further investment in the pipeline. Honesty about what
the data can and cannot produce matters more than optimism.

---

## 2. Source Data Summary

Confirmed and validated in WS-F F0 and F1. All CC-BY licensed.

| Source | Resolution | Format | Size (Gosford bbox) | Status |
|---|---|---|---|---|
| NSW Spatial Services aerial imagery | 10cm GSD | JPEG via WMS/WMTS/ArcGIS REST | ~2–5 GB at native res for full bbox | Endpoints confirmed, F1 |
| GA 5m DEM (WCS) | ~5m | GeoTIFF, EPSG:4283 | 4.5 MB | Downloaded and validated, F1 |
| GA/ELVIS 1m DEM | 1m | GeoTIFF | ~30–80 MB | Available via portal, instructions filed |
| LiDAR point cloud (ELVIS) | 2–8 pts/m² | LAZ (compressed LAS) | ~370–620 MB | Available via portal, instructions filed |

**Bounding box (full):** S -33.45, N -33.40, W 151.30, E 151.36
(~5.6 km × 5.6 km, ~31 km²)

**CBD core sub-region (F2 target):** S -33.427, N -33.420, W 151.335, E 151.345
(~830 m × 780 m, ~0.65 km²)

The CBD core sub-region centres on the Mann Street / Gosford train
station area — the same location as the Gosford Observation reference
site (ADR-016). F2 targets the core, not the full bbox. The full bbox
is an F3/F4 scaling target.

---

## 3. The Honest Constraint

Before specifying hardware, the fundamental data constraint must be
stated plainly.

**We have nadir (top-down) aerial imagery and elevation data. We do
not have multi-view oblique imagery with known camera poses.**

3DGS training requires multi-view images — the same scene observed
from multiple angles with known camera positions. Ortho-rectified
aerial imagery is a single projection to a flat plane. You cannot
train a traditional 3DGS model from a single ortho image.

What we *can* do:

1. Build a textured 2.5D mesh from the LiDAR point cloud + DEM,
   draped with aerial imagery
2. Generate synthetic camera views from that mesh
3. Use those synthetic views + the LiDAR point cloud to initialise
   and train a 3DGS model
4. Export the trained model as a `.ply` splat file

What this produces:

- **Good:** Terrain, building rooftops, vegetation canopy, road
  surfaces — everything visible from above
- **Inferred:** Building facades, vertical surfaces, undercut
  geometry — interpolated from LiDAR structure, not from observed
  texture. Facades will show plausible but not photorealistic detail.
- **Absent:** Interior visibility, occluded surfaces, fine signage

This is a 2.5D+ reconstruction, not a full 3D capture. It is
sufficient for the P3-EC2 experiential checkpoint (descent from
orbital to street level on the Gosford pilot region) and for
demonstrating the substrate integration pipeline. It is not
sufficient for photorealistic street-level navigation.

Photorealistic street-level requires oblique aerial or drone-captured
multi-view imagery. That is a procurement decision for after F2
validates the pipeline.

---

## 4. Minimum GPU Requirements

3DGS training is CUDA-only. The reference implementation (Kerbl et
al., SIGGRAPH 2023) and all production-quality derivatives (gsplat,
nerfstudio splatfacto) require NVIDIA GPUs with CUDA compute
capability ≥ 7.0 (Volta architecture or newer).

The VRAM bottleneck is Gaussian densification during training —
Gaussians are adaptively split and cloned, and the working set
grows unpredictably. The CBD core sub-region at 0.65 km² with
LiDAR initialization will produce 5–15 million Gaussians at
convergence.

### 4.1 Minimum (will work, will be slow)

| Component | Requirement |
|---|---|
| GPU | NVIDIA, CUDA compute ≥ 7.0 |
| VRAM | 16 GB |
| GPU models | RTX 4080 (16 GB), RTX A4000 (16 GB), V100 (16 GB) |
| System RAM | 32 GB |
| Storage | 200 GB SSD (NVMe preferred) |
| CPU | 8 cores (image decoding and point cloud preprocessing are CPU-bound) |

At 16 GB VRAM the CBD core must be subdivided into 4–6 tiles,
each trained independently and merged. This adds pipeline
complexity and produces visible seam artefacts at tile boundaries
that require post-processing (overlap-blend or boundary
optimisation). Training time approximately doubles versus a
single-pass approach.

### 4.2 Recommended (single-pass on CBD core)

| Component | Requirement |
|---|---|
| GPU | NVIDIA, CUDA compute ≥ 8.0 |
| VRAM | 24 GB |
| GPU models | RTX 4090 (24 GB), RTX A5000 (24 GB), A10G (24 GB), L40 (48 GB) |
| System RAM | 64 GB |
| Storage | 500 GB NVMe SSD |
| CPU | 16 cores |

At 24 GB the CBD core can be processed in a single pass or 2
tiles with generous overlap. This is the configuration to target
for F2.

### 4.3 Ideal (full bbox, future phases)

| Component | Requirement |
|---|---|
| GPU | NVIDIA, CUDA compute ≥ 8.0 |
| VRAM | 48 GB |
| GPU models | A6000 (48 GB), L40 (48 GB), A100 (40/80 GB) |
| System RAM | 128 GB |
| Storage | 2 TB NVMe SSD |
| CPU | 32 cores |

At 48 GB the full bbox can be tiled into 8–12 blocks with
comfortable margins. This is the configuration for scaling
beyond F2 to F3/F4.

### 4.4 What will not work

- AMD GPUs — no CUDA, no 3DGS training. ROCm support is
  experimental in gsplat and not production-ready.
- Apple Silicon — MPS backend exists in nerfstudio for NeRF
  but 3DGS training on MPS is not supported. Rendering only.
- GPUs with < 12 GB VRAM — densification will OOM on any
  meaningful scene.
- CPU-only — not feasible. Training time would be measured in
  weeks, not hours.

---

## 5. Recommended Library Stack

### 5.1 Core Reconstruction Pipeline

| Layer | Library | Version | Licence | Purpose |
|---|---|---|---|---|
| **3DGS training** | gsplat | ≥ 1.0 | Apache 2.0 | CUDA-accelerated Gaussian splatting kernels. The production-quality open-source 3DGS library. Maintained by the nerfstudio team. |
| **Training framework** | nerfstudio | ≥ 1.1 | Apache 2.0 | Data loading, training loop, evaluation, export. The `splatfacto` method wraps gsplat and provides the full training pipeline. Config-driven — no custom training loop code needed for baseline. |
| **SfM (if needed)** | COLMAP | ≥ 3.9 | BSD | Structure-from-Motion for camera pose estimation. Required only if we generate synthetic multi-view images and need to recover poses. If poses are generated programmatically (which is the recommended approach for synthetic views), COLMAP is optional. |
| **Point cloud processing** | PDAL | ≥ 2.6 | BSD | Point Data Abstraction Library. Industry standard for LiDAR processing — filtering, classification, reprojection, format conversion. Required for LAZ → LAS → PLY pipeline. |
| **Point cloud analysis** | Open3D | ≥ 0.18 | MIT | 3D data processing — point cloud colorisation, mesh reconstruction (Poisson), normal estimation. Python bindings. |
| **Mesh generation** | Open3D or PoissonRecon | — | MIT / MIT | Poisson surface reconstruction from oriented point cloud. Open3D wraps this; standalone PoissonRecon binary is faster for large scenes. |

### 5.2 Geospatial Data Handling

| Library | Version | Licence | Purpose |
|---|---|---|---|
| **GDAL** | ≥ 3.8 | MIT/X | Raster and vector geospatial data translation. Underpins everything. |
| **rasterio** | ≥ 1.3 | BSD | Pythonic GDAL wrapper for raster I/O. DEM and imagery handling. |
| **pyproj** | ≥ 3.6 | MIT | CRS transformations. GDA94 → WGS84, GDA94 → MGA Zone 56. Aligns with ADR-020. |
| **Fiona** | ≥ 1.9 | BSD | Vector data I/O (building footprints if sourced from Overture/OSM). |
| **OWSLib** | ≥ 0.31 | BSD | OGC WMS/WCS client for automated imagery and DEM retrieval. |
| **Pillow** | ≥ 10.0 | MIT-like | Image I/O — tile stitching, format conversion. |

### 5.3 Environment

| Component | Specification |
|---|---|
| Python | 3.10 or 3.11 (nerfstudio dependency ceiling) |
| CUDA Toolkit | 11.8 or 12.1 (match nerfstudio's tested configurations) |
| PyTorch | ≥ 2.1 with CUDA support |
| OS | Ubuntu 22.04 LTS (all cloud GPU instances default to this) |
| Container | Docker recommended — nerfstudio publishes official images: `dromni/nerfstudio:1.1.0` |

### 5.4 Alternatives Considered and Rejected

| Alternative | Why rejected |
|---|---|
| Original 3DGS repo (graphdeco-inria/gaussian-splatting) | Functional but research-grade — no config system, no pipeline abstraction, harder to extend. gsplat/nerfstudio is the maintained successor. |
| 3DGS-based commercial tools (Polycam, Luma) | Require multi-view input we don't have. Cloud-only. No export control. Not suitable for substrate integration research. |
| NeRF (vanilla) | Slower training, slower rendering, no explicit geometry. 3DGS supersedes for our use case. |
| Instant-NGP (NVIDIA) | Fast but rendering-focused, limited export to Gaussian format, less active community than gsplat. |
| PhotogrammetryKit / Meshroom | Require multi-view images. We have nadir-only. Same constraint as COLMAP. |

---

## 6. Input Format Requirements

### 6.1 NSW Aerial Imagery — Conversion Pipeline

**Source:** WMS/WMTS/ArcGIS REST tiles (JPEG, EPSG:4326 / GDA94)

**Target format for reconstruction:** Georeferenced GeoTIFF mosaic in MGA Zone 56 (EPSG:28356)

**Steps:**

1. **Tile download.** Use OWSLib or direct ArcGIS REST export to
   download the CBD core sub-region at native 10cm GSD. At
   830m × 780m and 10cm resolution this is ~8,300 × 7,800 pixels
   — a single 1024×1024 tile at the maximum server export size
   will not cover it. Download as a grid of overlapping tiles
   (e.g., 20 × 20 tiles at 1024×1024 each) and stitch.

2. **Stitch to single GeoTIFF.** Use `gdal_merge.py` or `rasterio`
   to merge tiles into one georeferenced GeoTIFF. Preserve EPSG:4326
   coordinates in the GeoTIFF header.

3. **Reproject to MGA Zone 56.** All reconstruction work uses
   projected metric coordinates, not geographic degrees. MGA Zone 56
   (EPSG:28356) is the correct zone for Gosford (151°E longitude).
   Use `gdalwarp -t_srs EPSG:28356`.

4. **Export as PNG/JPEG for nerfstudio.** nerfstudio expects standard
   image files, not GeoTIFF. Export the reprojected mosaic as a
   high-resolution PNG. Retain the GeoTIFF for coordinate reference
   — the PNG is for training input only.

**Output:** `gosford-cbd-aerial-mga56.tif` (georeferenced, ~500 MB)
and `gosford-cbd-aerial.png` (for training input, ~200 MB)

### 6.2 GA DEM — Conversion Pipeline

**Source:** GeoTIFF, EPSG:4283 (GDA94), float32, single band

**Target format:** GeoTIFF in MGA Zone 56 (EPSG:28356), resampled
to match aerial imagery resolution where needed

**Steps:**

1. **5m DEM (already downloaded).** Reproject from EPSG:4283 to
   EPSG:28356 using `gdalwarp`. Resampling method: bilinear for
   continuous elevation surface.

2. **1m DEM (requires manual ELVIS download).** Same reprojection.
   The 1m DEM is preferred for the reconstruction — 5× better
   resolution means sharper terrain and more detectable building
   edges. If 1m is not available in time, 5m is acceptable for
   the F2 baseline.

3. **Clip to CBD core sub-region.** Use `gdalwarp -te` with the
   MGA Zone 56 equivalent of the CBD core coordinates.

**Output:** `gosford-cbd-dem-1m-mga56.tif` or
`gosford-cbd-dem-5m-mga56.tif`

### 6.3 LiDAR Point Cloud — Conversion Pipeline

**Source:** LAZ (compressed LAS), expected CRS: GDA94 / MGA Zone 56
or GDA2020 / MGA Zone 56

**Target format:** PLY (XYZ + RGB), MGA Zone 56 with elevation in
AHD metres

This is the most important input for F2. The LiDAR provides the 3D
structure that aerial imagery alone cannot.

**Steps:**

1. **Decompress LAZ → LAS.** Use PDAL or `laszip`.

2. **Inspect and verify CRS.** Use `pdal info --metadata` to confirm
   the embedded CRS. NSW Spatial Services LiDAR is typically in
   GDA94 / MGA Zone 56 (EPSG:28356) or GDA2020 / MGA Zone 56
   (EPSG:7856). If GDA2020, reproject to GDA94 MGA Zone 56 per
   ADR-020 noting that NTv2 grid shift may apply per DEC-014.

3. **Filter by classification.** ASPRS LAS classification codes:
   - Class 2 (Ground) — terrain surface
   - Class 6 (Building) — building rooftops and walls
   - Class 3 (Low Vegetation), 4 (Medium Vegetation),
     5 (High Vegetation) — tree canopy
   - Discard class 7 (Noise), class 12 (Overlap)

   Use PDAL filters:
   ```
   pdal translate input.laz filtered.las \
     --filter filters.range \
     --filters.range.limits="Classification[2:6]"
   ```

4. **Clip to CBD core sub-region.** Use PDAL `filters.crop` with
   the MGA Zone 56 bounding box.

5. **Compute normals.** Required for Poisson surface reconstruction
   and for 3DGS initialisation quality. Use Open3D
   `estimate_normals()` with a search radius of 1–2m (2–4× the
   mean point spacing).

6. **Colorize from aerial imagery.** For each LiDAR point, sample
   the aerial GeoTIFF at the point's XY position to assign RGB.
   Use Open3D or a custom PDAL pipeline with `filters.colorization`.
   Points occluded in the aerial image (e.g., under tree canopy)
   will receive canopy colour, not ground colour — this is correct
   for the visual reconstruction.

7. **Export as PLY.** The PLY file with XYZ + Normal + RGB is the
   primary initialisation input for 3DGS training.

**Output:** `gosford-cbd-lidar-colored.ply` (~200–500 MB)

**Estimated point count for CBD core:** At 4 pts/m² over 0.65 km²:
~2.6 million points. This is a comfortable initialisation size for
3DGS.

### 6.4 Format Summary Table

| Input | Source Format | Target Format | Target CRS | Tool |
|---|---|---|---|---|
| Aerial imagery | JPEG tiles via WMS | GeoTIFF → PNG | EPSG:28356 | GDAL, OWSLib, rasterio |
| 5m DEM | GeoTIFF EPSG:4283 | GeoTIFF | EPSG:28356 | gdalwarp |
| 1m DEM | GeoTIFF (ELVIS) | GeoTIFF | EPSG:28356 | gdalwarp |
| LiDAR | LAZ | PLY (XYZ+RGB+Normal) | EPSG:28356 | PDAL, Open3D |

---

## 7. F2 Reconstruction Pipeline — Step by Step

This is the end-to-end pipeline from raw inputs to `.ply` splat
output.

### Phase 1 — Data Preparation (CPU-bound, no GPU required)

| Step | Input | Output | Tool | Est. Time |
|---|---|---|---|---|
| 1a. Download aerial tiles | WMS endpoint | JPEG tiles | OWSLib / requests | 30–60 min |
| 1b. Stitch and reproject | JPEG tiles | `aerial-mga56.tif` | GDAL | 15 min |
| 1c. Reproject DEM | GeoTIFF 4283 | `dem-mga56.tif` | gdalwarp | 5 min |
| 1d. Decompress + filter LiDAR | LAZ | Filtered LAS | PDAL | 15–30 min |
| 1e. Clip to CBD core | Full-extent files | Clipped files | GDAL, PDAL | 5 min |
| 1f. Colorize point cloud | LAS + aerial TIF | Colored PLY | Open3D / PDAL | 30–60 min |
| 1g. Compute normals | Colored PLY | PLY with normals | Open3D | 15–30 min |

**Phase 1 total: ~2–3 hours.** Can run on any machine with 32 GB RAM.

### Phase 2 — Mesh Generation and Synthetic Views (CPU + minimal GPU)

| Step | Input | Output | Tool | Est. Time |
|---|---|---|---|---|
| 2a. Poisson surface reconstruction | PLY with normals | Textured mesh (OBJ/PLY) | Open3D / PoissonRecon | 30–60 min |
| 2b. Drape aerial texture onto mesh | Mesh + aerial TIF | UV-mapped textured mesh | Open3D / Blender (scripted) | 30–60 min |
| 2c. Generate synthetic camera poses | Mesh bounds | `transforms.json` | Custom Python script | 10 min |
| 2d. Render synthetic views | Textured mesh + poses | 200–500 PNG images | Open3D / Blender / pyrender | 60–120 min |

**Phase 2 total: ~2–4 hours.**

Synthetic view generation (step 2c) is the critical design decision.
The camera positions must cover:

- **Nadir views** at varying altitudes (500m, 200m, 100m, 50m) —
  these are close to the source data and anchor the reconstruction
- **Oblique views** at 30°, 45°, 60° from horizontal — these force
  the 3DGS model to learn facade and vertical-surface appearance
  from the mesh interpolation
- **Street-level views** at 1.5–2m height — these validate the
  reconstruction from the perspective P3-EC2 will test

A grid of ~200–500 views provides sufficient coverage for the CBD
core. More views improve quality at the cost of training time.

### Phase 3 — 3DGS Training (GPU-bound)

| Step | Input | Output | Tool | Est. Time (24 GB GPU) |
|---|---|---|---|---|
| 3a. Initialise from point cloud | Colored PLY | Initial Gaussians | nerfstudio splatfacto | 5 min |
| 3b. Train (30,000 iterations) | Synthetic images + poses + init PLY | Trained model checkpoint | nerfstudio splatfacto | 45–90 min |
| 3c. Evaluate (PSNR, SSIM, LPIPS) | Held-out test views | Quality metrics | nerfstudio eval | 10 min |
| 3d. Export splat file | Trained checkpoint | `gosford-cbd.ply` | nerfstudio export | 5 min |

**Phase 3 total: ~1–2 hours on a 24 GB GPU.**

If the CBD core requires tiling (at 16 GB VRAM), multiply by the
number of tiles (4–6) plus 30 minutes for boundary blending.

### Phase 4 — Validation and Post-Processing

| Step | Input | Output | Tool | Est. Time |
|---|---|---|---|---|
| 4a. Visual inspection | Exported PLY | Pass/fail assessment | Web viewer (antimatter15/splat or similar) | 30 min |
| 4b. Coordinate verification | PLY centroids | Comparison with known Harmony cell keys | Custom script | 15 min |
| 4c. Splat count and size audit | PLY file | Stats report | Python / ply parser | 10 min |
| 4d. Compress for delivery | Raw PLY | Compressed PLY | Standard compression | 5 min |

**Phase 4 total: ~1 hour.**

---

## 8. Estimated Total Compute Time — F2 Baseline

### Single-pass (24 GB VRAM, recommended configuration)

| Phase | Duration | Resource |
|---|---|---|
| Phase 1 — Data prep | 2–3 hours | CPU only (any machine) |
| Phase 2 — Mesh + synthetic views | 2–4 hours | CPU + minimal GPU |
| Phase 3 — 3DGS training | 1–2 hours | GPU (24 GB VRAM) |
| Phase 4 — Validation | 1 hour | CPU only |
| **Total** | **6–10 hours** | |

### Tiled approach (16 GB VRAM, minimum configuration)

| Phase | Duration | Resource |
|---|---|---|
| Phase 1 — Data prep | 2–3 hours | CPU only |
| Phase 2 — Mesh + synthetic views | 3–5 hours | CPU + minimal GPU |
| Phase 3 — 3DGS training (×5 tiles) | 4–8 hours | GPU (16 GB VRAM) |
| Phase 3b — Boundary blending | 1–2 hours | GPU |
| Phase 4 — Validation | 1 hour | CPU only |
| **Total** | **11–19 hours** | |

### Contingency

Add 50% for iteration — the first run will require parameter
tuning (Gaussian densification thresholds, learning rate, synthetic
view distribution). A realistic F2 campaign including two full
iterations:

- **Recommended config:** ~15–20 hours total wall clock
- **Minimum config:** ~25–35 hours total wall clock

The GPU-hours billed are a subset of wall clock time. Phases 1
and 4 do not require a GPU instance. Provision the GPU instance
only for Phases 2d (if using GPU rendering for synthetic views)
and Phase 3. Estimated billable GPU time: **4–8 hours** at the
recommended tier.

---

## 9. Cloud Compute Options

### 9.1 Recommended: Lambda Labs

Lambda Labs offers the best VRAM-per-dollar for research workloads.
No long-term commitment. On-demand hourly billing. Pre-built deep
learning images with CUDA, PyTorch, and nerfstudio dependencies.

| Instance | GPU | VRAM | vCPU | RAM | Storage | On-Demand $/hr |
|---|---|---|---|---|---|---|
| gpu_1x_a6000 | 1× A6000 | 48 GB | 14 | 46 GB | 200 GB SSD | ~$0.80 |
| gpu_1x_a100 | 1× A100 | 40 GB | 30 | 200 GB | 512 GB SSD | ~$1.10 |
| gpu_1x_a10 | 1× A10 | 24 GB | 30 | 200 GB | 1.4 TB SSD | ~$0.60 |
| gpu_1x_h100 | 1× H100 | 80 GB | 26 | 200 GB | 1 TB SSD | ~$2.49 |

**Recommendation:** `gpu_1x_a6000` at ~$0.80/hr.
48 GB VRAM handles the CBD core in a single pass with room for
experimentation. Estimated F2 cost: **$6–16** (8–20 GPU-hours).

**Availability note:** Lambda Labs GPU availability fluctuates.
A6000 instances are generally more available than A100/H100.
Check availability at provisioning time. If A6000 is unavailable,
A100 at $1.10/hr is the next choice.

### 9.2 Alternative: AWS

AWS offers the most mature ecosystem but higher per-hour cost
for equivalent GPU capability.

| Instance | GPU | VRAM | vCPU | RAM | On-Demand $/hr | Spot $/hr (est.) |
|---|---|---|---|---|---|---|
| g5.4xlarge | 1× A10G | 24 GB | 16 | 64 GB | $1.62 | ~$0.65 |
| g5.2xlarge | 1× A10G | 24 GB | 8 | 32 GB | $1.21 | ~$0.49 |
| g6.2xlarge | 1× L4 | 24 GB | 8 | 32 GB | $0.98 | ~$0.39 |
| p4d.24xlarge | 8× A100 | 320 GB | 96 | 1152 GB | $32.77 | ~$14.07 |

**Recommendation if AWS required:** `g5.4xlarge` on-demand.
The 64 GB system RAM matters — LiDAR processing is memory-hungry.
Spot instances are viable for F2 (research workload, checkpointing
is straightforward in nerfstudio).

Estimated F2 cost on AWS: **$13–32** (8–20 GPU-hours at $1.62/hr).

**Avoid `p3` instances** — the V100 (16 GB VRAM) is a previous
generation and costs more per VRAM-GB than the A10G. The V100's
Tensor Cores are also less efficient for the mixed-precision
operations gsplat uses.

### 9.3 Alternative: GCP

| Instance | GPU | VRAM | vCPU | RAM | On-Demand $/hr |
|---|---|---|---|---|---|
| g2-standard-8 | 1× L4 | 24 GB | 8 | 32 GB | $0.84 |
| g2-standard-16 | 1× L4 | 24 GB | 16 | 64 GB | $1.07 |
| a2-highgpu-1g | 1× A100 | 40 GB | 12 | 85 GB | $3.67 |

**Recommendation if GCP required:** `g2-standard-16`.
Competitive pricing, adequate for F2.

Estimated F2 cost on GCP: **$9–21** (8–20 GPU-hours at $1.07/hr).

### 9.4 Cost Summary

| Provider | Instance | F2 Estimated Cost | Notes |
|---|---|---|---|
| Lambda Labs | gpu_1x_a6000 | **$6–16** | Best value. 48 GB VRAM. |
| GCP | g2-standard-16 | $9–21 | Good value. 24 GB VRAM. |
| AWS | g5.4xlarge | $13–32 | Most mature. 24 GB VRAM. |
| Lambda Labs | gpu_1x_h100 | $20–50 | Overkill but fastest. |

**For F2, the total compute cost is under $50 on any provider.**
This is a research experiment, not a large-scale training run.
The cost is trivial. The selection should be driven by availability
and setup convenience, not price optimisation.

---

## 10. Data Download Plan — Manual Steps Before GPU Provisioning

These steps require a human operator (Mikey) and do not require
a GPU instance. Complete before provisioning cloud compute.

### Step 1 — ELVIS 1m DEM + LiDAR Download

Follow the instructions already filed at:
`04_pillars/pillar-2-data-ingestion/data/wfs-f1/ELVIS-1m-download-instructions.md`

**Modify the bounding box** to the CBD core sub-region:
S -33.427, N -33.420, W 151.335, E 151.345

Expected outputs:
- `gosford-cbd-dem-1m.tif` (~5–10 MB for the core sub-region)
- `gosford-cbd-pointcloud.laz` (~50–100 MB for the core sub-region)

### Step 2 — Verify 5m DEM Already Downloaded

The 5m DEM for the full bbox was downloaded in F1 and is
reproducible via:
`04_pillars/pillar-2-data-ingestion/data/wfs-f1/README.md`

### Step 3 — Upload Data to Cloud Instance

Once the GPU instance is provisioned, `scp` or `rsync` the
downloaded files to the instance. Total transfer: < 1 GB.

---

## 11. Output Specification — What F2 Produces

| Deliverable | Format | Estimated Size | Purpose |
|---|---|---|---|
| `gosford-cbd.ply` | PLY (3DGS splat file) | 50–200 MB | Primary reconstruction output. Renderable in any WebGPU 3DGS viewer. |
| `gosford-cbd-metrics.json` | JSON | < 1 KB | PSNR, SSIM, LPIPS scores against held-out synthetic test views. |
| `gosford-cbd-training-config.yaml` | YAML | < 10 KB | nerfstudio config used for training. Reproducibility record. |
| `ws-f-experiment-f2-report.md` | Markdown | — | F2 experiment report with quality assessment and honest evaluation of reconstruction fidelity. |
| Coordinate verification | CSV | < 10 KB | Five reference points (Mann Street, train station, waterfront, two intersections) with WGS84 coordinates, compared against the reconstruction's corresponding splat centroids. Confirms spatial alignment with the Harmony Cell System. |

### Output quality expectations (honest)

- **Top-down views:** Good. Source data is top-down; this is where
  reconstruction fidelity will be highest.
- **45° oblique views:** Moderate. LiDAR structure provides
  building volume; texture on angled surfaces is interpolated.
- **Street-level views:** Low-to-moderate. Facades are inferred,
  not captured. Vegetation is volumetric blobs, not resolved trees.
  Roads and footpaths will look correct from above but blurry at
  ground level.
- **Motion through the scene:** The 3DGS representation should
  produce smooth, continuous rendering at interactive frame rates
  (30+ fps) on a WebGPU-capable device. This is the property that
  matters most for the P3-EC2 checkpoint — continuity of descent,
  not texture sharpness.

---

## 12. What F2 Does Not Attempt

- **Production pipeline integration.** F2 is a standalone
  reconstruction experiment. Integration with the Pillar 2
  ingestion pipeline and Pillar 1 cell registry is an F3 task.
- **Real-time streaming.** The output `.ply` is a static asset.
  Integration with the Live Substrate Service (Dr. Lin Park) is
  post-F2.
- **Full bbox reconstruction.** The full 31 km² bbox is an F3/F4
  target. F2 proves the pipeline on 0.65 km².
- **Facade-quality photorealism.** Requires oblique or ground-level
  imagery we do not have from open data. A separate procurement
  decision.
- **Temporal reconstruction.** Single-epoch capture only. Temporal
  change detection (HCI Phase 2) is a research programme milestone,
  not an F2 objective.

---

## 13. Procurement Checklist — What Mikey Needs to Do

| # | Action | Blocking? | Time Required |
|---|---|---|---|
| 1 | Download 1m DEM + LiDAR from ELVIS for CBD core bbox | Yes — F2 input | 30 min (portal workflow + email wait) |
| 2 | Create Lambda Labs account (or select alternative provider) | Yes — compute | 15 min |
| 3 | Provision `gpu_1x_a6000` instance (or equivalent) | Yes — compute | 10 min |
| 4 | Install nerfstudio via Docker (`docker pull dromni/nerfstudio:1.1.0`) | Yes — environment | 15 min |
| 5 | Install PDAL + GDAL + Open3D in the instance environment | Yes — data prep | 20 min |
| 6 | Upload ELVIS downloads + F1 5m DEM to instance | Yes — data | 10 min |
| 7 | Run Phase 1 data preparation pipeline | Yes — training input | 2–3 hours |
| 8 | Run Phase 2 mesh + synthetic views | Yes — training input | 2–4 hours |
| 9 | Run Phase 3 3DGS training | Yes — output | 1–2 hours |
| 10 | Download `.ply` output + metrics | Yes — deliverable | 10 min |
| 11 | Terminate GPU instance | Cost control | 2 min |

**Total estimated effort:** One focused day from procurement to output.

---

## 14. Technical Co-Founder Inheritance Notes

This section is written for the person who inherits this work.

**What you are inheriting:**

- A spatial substrate (Pillar 1) that assigns stable identities to
  regions of space using the Harmony Cell System
- A data ingestion pipeline (Pillar 2, in progress) that normalises
  geospatial data from Australian government open data sources
- A rendering architecture (Pillar 3, pre-dispatch) with a two-track
  strategy: Track 1 (progressive mesh, production) and Track 2
  (Gaussian splatting, research/demo)
- The WS-F experiment series proving that open data can produce a
  3DGS reconstruction suitable for a fundraise demo
- DEC-023 establishing that the demo experience uses reconstructed
  imagery as an overlay on the production substrate

**Where to start:**

1. Read `docs/specs/CURRENT_SPEC.md` → follow to the master spec
2. Read `docs/specs/DECISION_LOG.md` — every decision since V1.0
3. Read the F0 and F1 reports in `docs/reports/ws-f-experiment-*`
4. Execute this spec — procure the environment, run the pipeline,
   evaluate the output
5. Write the F2 report with an honest assessment of reconstruction
   quality and a recommendation on whether to invest in oblique
   imagery capture for F3

**What you should question:**

- Whether synthetic views from a textured mesh produce sufficient
  training signal for convincing 3DGS. This is the core hypothesis
  of F2. It might not work. If it doesn't, the fallback is direct
  point-cloud-to-splat conversion (lower quality, no training, but
  guaranteed to produce output).
- Whether 10cm nadir aerial imagery provides enough texture
  variation for the Gaussian model to learn meaningful appearance
  on non-nadir surfaces. Buildings with uniform rooftops may
  produce uninformative Gaussians on facades.
- Whether the LiDAR point density (2–8 pts/m²) is sufficient for
  building facades. Most LiDAR returns will be from rooftops and
  terrain — facade points depend on sensor angle and building
  geometry.

These are the honest unknowns. F2 resolves them experimentally.

---

**HARMONY UPDATE:** WS-F Research Environment Specification produced.
Covers GPU requirements (24 GB VRAM recommended, NVIDIA CUDA ≥ 7.0),
library stack (nerfstudio/gsplat/PDAL/GDAL/Open3D), input format
conversion pipelines for NSW aerial + GA DEM + ELVIS LiDAR, estimated
6–10 hours compute on recommended config, Lambda Labs A6000 at
~$0.80/hr recommended (F2 total cost < $50). CBD core sub-region
defined (0.65 km²). Honest constraint documented: nadir-only imagery
produces 2.5D+ reconstruction, not full 3D. Filed as
`docs/specs/WS-F-RESEARCH-ENVIRONMENT-SPEC.md`.
