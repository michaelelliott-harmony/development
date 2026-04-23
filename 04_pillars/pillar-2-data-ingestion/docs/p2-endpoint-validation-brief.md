# HARMONY — Pillar 2: API Endpoint Validation & OSM Data Profiling
## Claude Code Task Brief
**Date:** April 19, 2026
**Priority:** Pre-Sprint 1 — de-risks all four programmatic adapters before build begins
**Estimated Duration:** 1–2 hours
**Dependencies:** None — all endpoints are publicly accessible

---

## Objective

Validate that the three programmatic data sources identified for Pillar 2 are accessible, return expected data structures, and contain sufficient coverage for the Central Coast pilot region. This task produces a structured validation report that confirms (or flags issues with) each endpoint before the build team writes adapters against them.

---

## Central Coast Bounding Box

All queries use this geographic extent:

```
South: -33.55
North: -33.15
West: 151.15
East: 151.75
```

EPSG:4326 (WGS84) unless the endpoint requires a different CRS.

---

## Task 1: Validate NSW Planning Portal — Land Zoning ArcGIS REST

**Endpoint:** `https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/EPI_Primary_Planning_Layers/MapServer`

**Steps:**

1. Fetch the service metadata (append `?f=json` to the base URL). Confirm the service is live and inspect the list of available layers. Identify which layer ID corresponds to "Land Zoning."

2. Query the Land Zoning layer for features within the Central Coast bounding box. Use the ArcGIS REST query format:
   ```
   {base_url}/{layer_id}/query?where=1%3D1&geometry={west},{south},{east},{north}&geometryType=esriGeometryEnvelope&spatialRel=esriSpatialRelIntersects&outFields=*&f=geojson&resultRecordCount=10
   ```

3. Inspect the response. Record:
   - HTTP status code
   - Number of features returned
   - Field names and types (especially: zone code, zone name, EPI name, LGA name)
   - Geometry type (expect Polygon or MultiPolygon)
   - Spatial reference / CRS of returned geometries
   - Whether pagination is needed (check `exceededTransferLimit` in response)
   - A sample feature (first one) with all attributes

4. Test pagination: query with `resultOffset=0&resultRecordCount=100`, then `resultOffset=100&resultRecordCount=100`. Confirm offset works and features don't duplicate.

5. Estimate total feature count for Central Coast by querying with `returnCountOnly=true`.

**Output:** Write a JSON report to `validation/arcgis_rest_zoning.json` containing: endpoint status, layer ID, field schema, sample feature, total feature count, pagination support, CRS, and any issues found.

---

## Task 2: Validate NSW Spatial Services — Cadastre WFS

**Endpoint candidates (try in order):**
- `https://maps.six.nsw.gov.au/arcgis/services/public/NSW_Cadastre/MapServer/WFSServer`
- `https://maps.six.nsw.gov.au/arcgis/services/public/NSW_Land_Parcel_Property_Theme/MapServer/WFSServer`

**Steps:**

1. Fetch the WFS GetCapabilities document:
   ```
   {endpoint}?service=WFS&request=GetCapabilities
   ```
   Confirm the service is live. Identify available feature types (look for lot/parcel layers).

2. Retrieve the schema for the lot feature type:
   ```
   {endpoint}?service=WFS&request=DescribeFeatureType&typeName={lot_feature_type}
   ```
   Record all field names and types.

3. Query for features within the Central Coast bounding box:
   ```
   {endpoint}?service=WFS&request=GetFeature&typeName={lot_feature_type}&bbox=-33.55,151.15,-33.15,151.75,EPSG:4326&count=10&outputFormat=application/json
   ```
   Note: bbox parameter order may be lat,lon or lon,lat depending on the service — try both if the first fails.

4. Inspect the response. Record:
   - HTTP status code
   - Number of features returned
   - Field names (especially: lot number, DP number, plan type, CadID, area)
   - Geometry type
   - CRS of returned geometries (expect GDA2020 EPSG:7844 or GDA94 EPSG:4283)
   - A sample feature with all attributes

5. If the WFS endpoint requires authentication or returns an error, document the error and note this as a blocker — the fallback is the Data Broker bulk download.

**Output:** Write a JSON report to `validation/wfs_cadastre.json` with the same structure as Task 1.

---

## Task 3: Validate and Profile OpenStreetMap — Central Coast

**Endpoint:** Overpass API at `https://overpass-api.de/api/interpreter`

**Steps:**

1. Query for building count in the Central Coast bounding box:
   ```
   [out:json][timeout:60];
   way["building"](-33.55,151.15,-33.15,151.75);
   out count;
   ```
   Record the total building count.

2. Retrieve a sample of 20 buildings with full geometry and tags:
   ```
   [out:json][timeout:60];
   way["building"](-33.55,151.15,-33.15,151.75);
   out body 20;
   >;
   out skel qt;
   ```
   Inspect the tag distribution. Record which tags are present and their frequency across the sample: `building`, `name`, `addr:street`, `addr:housenumber`, `height`, `building:levels`, `roof:shape`.

3. Query for road count in the Central Coast bounding box:
   ```
   [out:json][timeout:60];
   way["highway"](-33.55,151.15,-33.15,151.75);
   out count;
   ```
   Record the total road segment count.

4. Retrieve a sample of 20 road segments with tags:
   ```
   [out:json][timeout:60];
   way["highway"](-33.55,151.15,-33.15,151.75);
   out body 20;
   >;
   out skel qt;
   ```
   Record tag distribution: `highway` (classification), `name`, `surface`, `lanes`, `maxspeed`, `oneway`, `bridge`, `tunnel`.

5. Produce a coverage assessment:
   - Total buildings found
   - Percentage with name tags
   - Percentage with height/levels data
   - Total road segments found
   - Breakdown by highway classification (primary, secondary, tertiary, residential, etc.)
   - Percentage with name tags
   - Percentage with surface data

**Output:** Write a JSON report to `validation/osm_central_coast.json` containing: building count, building tag distribution, road count, road classification breakdown, sample features, and a coverage assessment summary.

---

## Task 4: Validate NSW Planning Portal — DA/CDC/PCC APIs (Milestone 7 pre-check)

**Note:** These APIs may require Data Broker access. Attempt the public endpoints; if they fail, document the failure and note that access confirmation is pending.

**Endpoint candidates:**
- DA API: Check `https://api.apps1.nsw.gov.au/eplanning/data/v0/OnlineDA` (documented endpoint from the data dictionary)
- CDC API: Similar pattern — check the open data portal page for the endpoint URL
- PCC API: Similar pattern

**Steps:**

1. Attempt to fetch the DA API with a simple query for Central Coast LGA:
   ```
   GET {da_endpoint}?filters={"CouncilName":"Central Coast Council"}&page=1&pagesize=5
   ```

2. If the endpoint responds:
   - Record the response structure (field names, data types)
   - Confirm that the following fields exist: application number, application type, status, lodgement date, determination date, lot/section/plan, address, coordinates or polygon
   - Record a sample DA record
   - Test filtering by date range
   - Confirm that Central Coast DAs are present

3. If the endpoint returns 401/403 or an error:
   - Document the error
   - Note that access is pending via the Data Broker email (sent April 20)
   - This does not block Milestones 1–6; it only blocks Milestone 7

**Output:** Write a JSON report to `validation/planning_portal_apis.json` containing: endpoint status for each API (DA, CDC, PCC), field schema if accessible, sample records, and any authentication or access issues.

---

## Task 5: Produce Summary Report

Combine all four validation reports into a single summary:

```json
{
  "validation_date": "2026-04-19",
  "pilot_region": "Central Coast NSW",
  "bounding_box": {"south": -33.55, "north": -33.15, "west": 151.15, "east": 151.75},
  "endpoints": {
    "arcgis_rest_zoning": {"status": "...", "feature_count": ..., "issues": [...]},
    "wfs_cadastre": {"status": "...", "feature_count": ..., "issues": [...]},
    "osm_buildings": {"status": "...", "feature_count": ..., "issues": [...]},
    "osm_roads": {"status": "...", "feature_count": ..., "issues": [...]},
    "planning_portal_da": {"status": "...", "issues": [...]},
    "planning_portal_cdc": {"status": "...", "issues": [...]},
    "planning_portal_pcc": {"status": "...", "issues": [...]}
  },
  "sprint_1_readiness": "...",
  "blockers": [...]
}
```

Save to `validation/endpoint_validation_summary.json`.

**Print a plain-language summary to stdout** covering: which endpoints are live, which are blocked, what the data looks like, and whether Sprint 1 can proceed.

---

## Environment Setup

```bash
pip install requests owslib fiona shapely pyproj geopandas
```

No API keys or credentials should be required for any of these endpoints. If any endpoint requires authentication, document this and do not attempt to bypass — flag it as a blocker.

---

## What This Task Does NOT Do

- Does not build the adapters — those are built in CoWork Sprint 1
- Does not ingest any data into Harmony Cells — that is Milestone 5
- Does not modify any Pillar 1 data or schema
- Does not create manifests — those are built in CoWork Task 5

This is a read-only validation and profiling exercise. Its only output is the validation reports.

---

*HARMONY Pillar 2 — Endpoint Validation Brief — April 2026*
