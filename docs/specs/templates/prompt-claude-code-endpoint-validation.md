# CLAUDE CODE PROMPT — Pillar 2 Endpoint Validation & OSM Data Profiling

Copy everything below this line and paste directly into Claude Code.

---

## Role and Context

You are validating the programmatic data sources for the Harmony Spatial Operating System's Pillar 2 — Data Ingestion Pipeline. Harmony is a GIS platform built on a custom spatial substrate (the Harmony Cell System) that converts the planet into addressable, AI-compatible computational space.

Before the build team writes source adapters, we need to confirm that every API endpoint we plan to connect to is live, returns the expected data structure, and contains sufficient data for the Central Coast NSW pilot region.

This is a read-only validation exercise. You are not building adapters, not ingesting data into Harmony, and not modifying any existing systems. Your only output is structured validation reports.

## Reference Documents

Read the following project files before beginning:

- `HARMONY_P2_ENDPOINT_VALIDATION_BRIEF.md` — the detailed task brief with endpoint URLs, query formats, and expected outputs
- `HARMONY_P2_DATA_INGESTION_PIPELINE_BRIEF_V2_0.docx` — Section 3 (Data Sourcing Strategy) defines the four data sources and their access methods
- `HARMONY_P2_ENTITY_SCHEMAS.md` — defines the fields we need from each source (use this to verify that the API responses contain the expected attributes)

## Central Coast Pilot Bounding Box

All spatial queries use this extent (WGS84 / EPSG:4326):

```
South: -33.55
North: -33.15
West: 151.15
East: 151.75
```

## Environment Setup

```bash
pip install requests owslib fiona shapely pyproj geopandas
mkdir -p validation
```

## Tasks — Execute in Order

### Task 1: Validate NSW Planning Portal — Land Zoning (ArcGIS REST)

**Endpoint:** `https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/EPI_Primary_Planning_Layers/MapServer`

1. Fetch the service metadata by appending `?f=json` to the base URL. Confirm the service is live. List the available layers and identify which layer ID corresponds to Land Zoning.

2. Query that layer for features within the Central Coast bounding box using the ArcGIS REST query format:
   ```
   {base_url}/{layer_id}/query?where=1%3D1&geometry=151.15,-33.55,151.75,-33.15&geometryType=esriGeometryEnvelope&spatialRel=esriSpatialRelIntersects&outFields=*&f=geojson&resultRecordCount=10
   ```

3. From the response, record:
   - HTTP status code
   - Number of features returned in the sample
   - All field names and their types — specifically confirm these exist: zone code (SYM_CODE), zone name (LAY_CLASS), EPI name (EPI_NAME), LGA name (LGA_NAME), and a unique ID field (LAM_ID)
   - Geometry type (expect Polygon or MultiPolygon)
   - Spatial reference / CRS
   - Whether pagination is needed (check for `exceededTransferLimit` in response)
   - Print one complete sample feature with all attributes

4. Estimate total feature count for the Central Coast bounding box by querying with `returnCountOnly=true`.

5. Write results to `validation/arcgis_rest_zoning.json`.

### Task 2: Validate NSW Spatial Services — Cadastre WFS

**Try these endpoints in order:**
- `https://maps.six.nsw.gov.au/arcgis/services/public/NSW_Cadastre/MapServer/WFSServer`
- `https://maps.six.nsw.gov.au/arcgis/services/public/NSW_Land_Parcel_Property_Theme/MapServer/WFSServer`

1. Fetch the WFS GetCapabilities document:
   ```
   {endpoint}?service=WFS&request=GetCapabilities
   ```
   Confirm the service is live. List available feature types and identify the lot/parcel layer.

2. Retrieve the schema for the lot feature type using DescribeFeatureType.

3. Query for features within the Central Coast bounding box:
   ```
   {endpoint}?service=WFS&request=GetFeature&typeName={lot_type}&bbox=-33.55,151.15,-33.15,151.75,EPSG:4326&count=10&outputFormat=application/json
   ```
   Note: if bbox fails with lat,lon order, try lon,lat order: `bbox=151.15,-33.55,151.75,-33.15,EPSG:4326`

4. From the response, record:
   - HTTP status code
   - Number of features returned
   - All field names — specifically confirm: lot number, plan/DP number, section number, CadID, area, plan label
   - Geometry type
   - CRS of returned geometries (expect GDA2020 EPSG:7844 or GDA94 EPSG:4283)
   - Print one complete sample feature

5. If the WFS endpoint requires authentication or returns an error, document the exact error. This is not a blocker for Milestones 1–5 — the fallback is the Data Broker bulk download.

6. Write results to `validation/wfs_cadastre.json`.

### Task 3: Profile OpenStreetMap — Central Coast Buildings and Roads

**Endpoint:** Overpass API at `https://overpass-api.de/api/interpreter`

**Important:** Wait at least 5 seconds between Overpass API requests. Do not send more than 2 requests per 10 seconds.

1. Query building count:
   ```
   [out:json][timeout:60];
   way["building"](-33.55,151.15,-33.15,151.75);
   out count;
   ```

2. Retrieve 20 sample buildings with tags and geometry:
   ```
   [out:json][timeout:120];
   way["building"](-33.55,151.15,-33.15,151.75);
   out body 20;
   >;
   out skel qt;
   ```
   
   From the sample, calculate tag frequency for: `building` (type breakdown), `name`, `addr:street`, `addr:housenumber`, `height`, `building:levels`, `roof:shape`.

3. Query road segment count:
   ```
   [out:json][timeout:60];
   way["highway"](-33.55,151.15,-33.15,151.75);
   out count;
   ```

4. Retrieve 20 sample road segments with tags:
   ```
   [out:json][timeout:120];
   way["highway"](-33.55,151.15,-33.15,151.75);
   out body 20;
   >;
   out skel qt;
   ```
   
   From the sample, calculate: `highway` classification breakdown (motorway, primary, secondary, tertiary, residential, etc.), `name` presence, `surface` presence, `lanes` presence, `maxspeed` presence.

5. Produce a coverage assessment:
   - Total buildings found
   - Percentage with name tags
   - Percentage with height or levels data
   - Total road segments found
   - Breakdown by highway classification
   - Percentage of roads with name tags
   - Percentage with surface data

6. Write results to `validation/osm_central_coast.json`.

### Task 4: Validate NSW Planning Portal — DA/CDC/PCC APIs (Milestone 7 Pre-Check)

**These APIs may require Data Broker access. Attempt the public endpoints — if they fail, document the failure.**

**Endpoint candidates:**
- DA API: `https://api.apps1.nsw.gov.au/eplanning/data/v0/OnlineDA`
- CDC API: `https://api.apps1.nsw.gov.au/eplanning/data/v0/OnlineCDC`
- PCC API: `https://api.apps1.nsw.gov.au/eplanning/data/v0/OnlinePCC`

1. For each endpoint, attempt a GET request with a Central Coast filter:
   ```
   GET {endpoint}?filters={"CouncilName":"Central Coast Council"}&page=1&pagesize=5
   ```
   
   If that format doesn't work, try:
   ```
   GET {endpoint}?CouncilName=Central%20Coast%20Council&PageSize=5&PageNumber=1
   ```

2. If any endpoint responds successfully:
   - Record the complete response structure
   - Confirm that these fields exist: application number, application type, status, lodgement date, determination date, address, lot/plan reference
   - Print one complete sample record
   - Test date filtering if possible

3. If endpoints return 401, 403, or connection errors:
   - Document the exact error for each endpoint
   - Note that access confirmation is pending via Data Broker email (sent April 20, 2026)
   - This does NOT block Milestones 1–6; it only affects Milestone 7

4. Write results to `validation/planning_portal_apis.json`.

### Task 5: Produce Summary Report

Combine all validation results into a single summary report:

```python
summary = {
    "validation_date": "2026-04-19",
    "pilot_region": "Central Coast NSW",
    "bounding_box": {
        "south": -33.55, "north": -33.15,
        "west": 151.15, "east": 151.75
    },
    "endpoints": {
        "arcgis_rest_zoning": {
            "status": "live|error|auth_required",
            "feature_count": 0,
            "fields_confirmed": [],
            "fields_missing": [],
            "crs": "",
            "pagination_required": False,
            "issues": []
        },
        "wfs_cadastre": {
            "status": "...",
            "feature_count": 0,
            "fields_confirmed": [],
            "fields_missing": [],
            "crs": "",
            "issues": []
        },
        "osm_buildings": {
            "status": "...",
            "feature_count": 0,
            "tag_coverage": {},
            "issues": []
        },
        "osm_roads": {
            "status": "...",
            "feature_count": 0,
            "classification_breakdown": {},
            "tag_coverage": {},
            "issues": []
        },
        "planning_portal_da": {"status": "...", "issues": []},
        "planning_portal_cdc": {"status": "...", "issues": []},
        "planning_portal_pcc": {"status": "...", "issues": []}
    },
    "sprint_1_readiness": "ready|blocked|partial",
    "blockers": [],
    "recommendations": []
}
```

Save to `validation/endpoint_validation_summary.json`.

**Print a plain-language summary to stdout** that answers:
1. Which endpoints are live and returning expected data?
2. Which endpoints are blocked or returning unexpected structures?
3. Is the OSM coverage sufficient for the Central Coast pilot?
4. Do the field schemas match what the entity schemas expect?
5. Can Sprint 1 proceed?
6. What issues need to be resolved before Milestone 7?

## Constraints

- Do not store any API credentials. All endpoints tested here are public.
- Do not attempt to bypass rate limits or authentication. If an endpoint requires auth, document it and move on.
- Do not write any data to any external service. This is read-only.
- Wait at least 5 seconds between Overpass API requests.
- Save all output files to the `validation/` directory.

## On Completion

Print the full summary report and explicitly state whether the Pillar 2 build team can proceed with Sprint 1.
