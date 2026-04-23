"""
Round 2 — targeted re-validation of the four failing/incomplete checks.
Saves results into existing validation JSON files by merging with round 1.
"""
import json
import time
import re
from pathlib import Path
from collections import Counter

import requests

OUT_DIR = Path(__file__).parent
BBOX = {"south": -33.55, "north": -33.15, "west": 151.15, "east": 151.75}
HEADERS = {"User-Agent": "Harmony-Pillar2-EndpointValidator/1.0"}


def load(name):
    p = OUT_DIR / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def save(name, data):
    (OUT_DIR / f"{name}.json").write_text(json.dumps(data, indent=2, default=str))


# -----------------------------------------------------------------------------
# Fix 1: ArcGIS zoning — correct count query
# -----------------------------------------------------------------------------
def fix_arcgis_count():
    print("\n--- Fix 1: ArcGIS zoning count ---")
    base = "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/EPI_Primary_Planning_Layers/MapServer"
    layer_id = 2
    query_url = f"{base}/{layer_id}/query"
    params = {
        "where": "1=1",
        "geometry": f"{BBOX['west']},{BBOX['south']},{BBOX['east']},{BBOX['north']}",
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "returnCountOnly": "true",
        "f": "json",
    }
    r = requests.get(query_url, params=params, headers=HEADERS, timeout=60)
    data = r.json() if r.status_code == 200 else {}
    count = data.get("count")
    print(f"  true feature count in bbox: {count}")

    # Also test pagination semantics: query with resultOffset=0&resultRecordCount=1000
    params2 = {
        "where": "1=1",
        "geometry": f"{BBOX['west']},{BBOX['south']},{BBOX['east']},{BBOX['north']}",
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "OBJECTID",
        "f": "json",
        "resultOffset": 0,
        "resultRecordCount": 1000,
    }
    r2 = requests.get(query_url, params=params2, headers=HEADERS, timeout=60)
    page_data = r2.json() if r2.status_code == 200 else {}
    exceeded = page_data.get("exceededTransferLimit", False)
    page1_count = len(page_data.get("features", []))
    print(f"  page 1 (1000 records): {page1_count} features, exceededTransferLimit={exceeded}")

    # filter to Central Coast LGA specifically
    params3 = {
        "where": "LGA_NAME = 'Central Coast'",
        "outFields": "*",
        "f": "json",
        "returnCountOnly": "true",
    }
    r3 = requests.get(query_url, params=params3, headers=HEADERS, timeout=60)
    cc_data = r3.json() if r3.status_code == 200 else {}
    cc_count = cc_data.get("count")
    print(f"  filtered by LGA_NAME='Central Coast': {cc_count}")

    report = load("arcgis_rest_zoning")
    report["total_count"] = count
    report["pagination_test"] = {
        "page1_size": page1_count,
        "exceededTransferLimit": exceeded,
        "max_record_count_effective": page1_count,
    }
    report["lga_filtered_count"] = {
        "query": "LGA_NAME = 'Central Coast'",
        "count": cc_count,
    }
    # Schema mismatch documentation
    field_names = [f["name"] for f in report.get("land_zoning_layer", {}).get("fields", [])]
    expected = ["SYM_CODE", "LAY_CLASS", "EPI_NAME", "LGA_NAME", "LAM_ID"]
    report["schema_vs_entity_model"] = {
        "expected_by_entity_schema": expected,
        "present_in_source": [f for f in expected if f in field_names],
        "missing_in_source": [f for f in expected if f not in field_names],
        "note": (
            "LAM_ID does not exist in the EPI_Primary_Planning_Layers MapServer. "
            "Candidate natural keys in the source: OBJECTID (numeric, per-feature), "
            "PCO_REF_KEY (string, planning-instrument scoped). Recommend updating "
            "HARMONY_P2_ENTITY_SCHEMAS.md zoning_area dedup strategy to use "
            "PCO_REF_KEY (or OBJECTID + EPI_NAME composite) in place of LAM_ID."
        ),
    }
    save("arcgis_rest_zoning", report)
    return report


# -----------------------------------------------------------------------------
# Fix 2: WFS cadastre — try portal.spatial.nsw.gov.au
# -----------------------------------------------------------------------------
def fix_wfs_cadastre():
    print("\n--- Fix 2: WFS cadastre (alternate endpoints) ---")
    candidates = [
        # Original
        "https://maps.six.nsw.gov.au/arcgis/services/public/NSW_Cadastre/MapServer/WFSServer",
        "https://maps.six.nsw.gov.au/arcgis/services/public/NSW_Land_Parcel_Property_Theme/MapServer/WFSServer",
        # Alternative portal
        "https://portal.spatial.nsw.gov.au/server/services/NSW_Cadastre/MapServer/WFSServer",
        "https://portal.spatial.nsw.gov.au/server/services/NSW_Land_Parcel_Property_Theme/MapServer/WFSServer",
        # Try ArcGIS REST (cadastre publicly queryable via REST too)
        "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Cadastre/MapServer",
        "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer",
        "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Land_Parcel_Property_Theme/MapServer",
    ]
    probes = []
    for url in candidates:
        print(f"  probing {url}")
        probe = {"url": url}
        is_rest = "/rest/services/" in url
        try:
            if is_rest:
                r = requests.get(url, params={"f": "json"}, headers=HEADERS, timeout=30)
            else:
                r = requests.get(url, params={"service": "WFS", "request": "GetCapabilities", "version": "2.0.0"}, headers=HEADERS, timeout=30)
            probe["http_status"] = r.status_code
            probe["content_type"] = r.headers.get("Content-Type", "")
            probe["body_start"] = r.text[:400]
            if r.status_code == 200:
                if is_rest:
                    try:
                        j = r.json()
                        probe["layers"] = [
                            {"id": l.get("id"), "name": l.get("name"), "type": l.get("type")}
                            for l in j.get("layers", [])
                        ][:40]
                        probe["verdict"] = "rest_live"
                    except Exception as e:
                        probe["parse_error"] = str(e)
                else:
                    # parse FeatureType names
                    names = re.findall(r"<(?:wfs:)?Name>([^<]+)</(?:wfs:)?Name>", r.text)
                    probe["feature_type_names"] = list(dict.fromkeys(names))[:40]
                    probe["verdict"] = "wfs_live"
        except Exception as e:
            probe["error"] = str(e)
        probes.append(probe)

    # Pick first live REST cadastre service and do a sample query
    live_rest = next(
        (p for p in probes if p.get("verdict") == "rest_live" and p.get("layers")),
        None,
    )
    sample = {}
    if live_rest:
        print(f"  live REST endpoint: {live_rest['url']}")
        print(f"  available layers: {[(l.get('id'), l.get('name'), l.get('type')) for l in live_rest['layers']]}")
        # pick a Lot/Parcel layer (exclude *_Labels annotation layers)
        layer = None
        candidates_ordered = []
        for l in live_rest["layers"]:
            name = (l.get("name") or "")
            lower = name.lower()
            if "label" in lower:
                continue
            if lower == "lot":
                candidates_ordered.insert(0, l)
            elif "lot" in lower.split("_") or "parcel" in lower:
                candidates_ordered.append(l)
            elif "cadastre" in lower:
                candidates_ordered.append(l)
        if candidates_ordered:
            layer = candidates_ordered[0]
        if layer:
            print(f"  selected layer: id={layer['id']} name={layer.get('name')}")
            layer_id = layer["id"]
            # Get layer metadata for field list
            meta_url = f"{live_rest['url']}/{layer_id}"
            mr = requests.get(meta_url, params={"f": "json"}, headers=HEADERS, timeout=30)
            if mr.status_code == 200:
                lmeta = mr.json()
                sample["layer"] = {"id": layer_id, "name": layer.get("name"), "geometryType": lmeta.get("geometryType")}
                sample["fields"] = [
                    {"name": f.get("name"), "type": f.get("type"), "alias": f.get("alias")}
                    for f in (lmeta.get("fields") or [])
                ]
                sample["extent"] = lmeta.get("extent")
                sample["maxRecordCount"] = lmeta.get("maxRecordCount")
                sample["layer_meta_note"] = None if lmeta.get("fields") else "Parent MapServer; need sublayer id for field schema"

            # Sample query
            q_url = f"{live_rest['url']}/{layer_id}/query"
            qparams = {
                "where": "1=1",
                "geometry": f"{BBOX['west']},{BBOX['south']},{BBOX['east']},{BBOX['north']}",
                "geometryType": "esriGeometryEnvelope",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",
                "f": "geojson",
                "resultRecordCount": 5,
            }
            qr = requests.get(q_url, params=qparams, headers=HEADERS, timeout=60)
            sample["sample_http_status"] = qr.status_code
            if qr.status_code == 200:
                try:
                    qjson = qr.json()
                    feats = qjson.get("features", [])
                    sample["sample_count"] = len(feats)
                    sample["crs"] = qjson.get("crs") or "EPSG:4326 (geojson)"
                    if feats:
                        first = feats[0]
                        sample["geometry_type"] = first.get("geometry", {}).get("type")
                        sample["sample_feature"] = first
                        props = first.get("properties", {})
                        sample["field_names"] = sorted(props.keys())
                        required = ["lotnumber", "plannumber", "sectionnumber", "cadid", "shapestarea", "planlabel"]
                        sample["required_fields_present"] = {
                            f: any(f.lower() == k.lower() for k in props.keys()) for f in required
                        }
                except Exception as e:
                    sample["parse_error"] = str(e)
                    sample["body"] = qr.text[:500]
            else:
                sample["sample_body_start"] = qr.text[:500]

            # Total count
            cr = requests.get(q_url, params={**qparams, "returnCountOnly": "true", "f": "json"}, timeout=60)
            if cr.status_code == 200:
                sample["total_count"] = cr.json().get("count")

    report = load("wfs_cadastre")
    report["round2_probes"] = probes
    report["round2_sample"] = sample
    if sample.get("sample_count"):
        report["endpoint_used"] = live_rest["url"] + "  (ArcGIS REST — WFS not exposed publicly; REST is the working path)"
        report["access_method"] = "ArcGIS REST (recommended fallback for WFS)"
        report["sample_query"] = {
            "http_status": sample.get("sample_http_status"),
            "feature_count": sample.get("sample_count"),
            "crs": sample.get("crs"),
            "geometry_type": sample.get("geometry_type"),
            "field_names": sample.get("field_names"),
            "required_fields_present": sample.get("required_fields_present"),
            "sample_feature": sample.get("sample_feature"),
        }
    save("wfs_cadastre", report)
    return report


# -----------------------------------------------------------------------------
# Fix 3: OSM — longer timeout + quarter-sub-bboxes for counts
# -----------------------------------------------------------------------------
def overpass(query, retries=2, pause=6):
    url = "https://overpass-api.de/api/interpreter"
    for attempt in range(retries):
        time.sleep(pause)
        try:
            r = requests.post(url, data={"data": query}, headers=HEADERS, timeout=300)
            if r.status_code == 200:
                try:
                    return 200, r.json()
                except Exception:
                    return 200, r.text[:500]
            else:
                if attempt + 1 < retries:
                    print(f"    {r.status_code}, retrying...")
                    pause = 30
                    continue
                return r.status_code, r.text[:500]
        except Exception as e:
            if attempt + 1 < retries:
                pause = 30
                continue
            return 0, str(e)
    return 0, "exhausted"


def fix_osm_counts():
    print("\n--- Fix 3: OSM counts (longer timeout + quadrants) ---")
    report = load("osm_central_coast")

    # Quadrants to split the bbox
    mid_lat = (BBOX["south"] + BBOX["north"]) / 2
    mid_lon = (BBOX["west"] + BBOX["east"]) / 2
    quadrants = [
        ("SW", BBOX["south"], BBOX["west"], mid_lat, mid_lon),
        ("SE", BBOX["south"], mid_lon, mid_lat, BBOX["east"]),
        ("NW", mid_lat, BBOX["west"], BBOX["north"], mid_lon),
        ("NE", mid_lat, mid_lon, BBOX["north"], BBOX["east"]),
    ]

    b_total = 0
    b_failed = False
    print("  buildings by quadrant:")
    for name, s, w, n, e in quadrants:
        q = f'[out:json][timeout:300];way["building"]({s},{w},{n},{e});out count;'
        status, data = overpass(q, retries=2, pause=7)
        if status == 200 and isinstance(data, dict):
            for el in data.get("elements", []):
                if el.get("type") == "count":
                    tags = el.get("tags", {})
                    n_ways = int(tags.get("ways") or tags.get("total") or 0)
                    b_total += n_ways
                    print(f"    {name}: {n_ways} buildings")
        else:
            b_failed = True
            print(f"    {name}: FAILED ({status})")
            break

    if not b_failed:
        report["buildings"]["count"] = b_total
        report["buildings"]["count_method"] = "summed over 4 quadrants"

    r_total = 0
    r_failed = False
    print("  roads by quadrant:")
    for name, s, w, n, e in quadrants:
        q = f'[out:json][timeout:300];way["highway"]({s},{w},{n},{e});out count;'
        status, data = overpass(q, retries=2, pause=7)
        if status == 200 and isinstance(data, dict):
            for el in data.get("elements", []):
                if el.get("type") == "count":
                    tags = el.get("tags", {})
                    n_ways = int(tags.get("ways") or tags.get("total") or 0)
                    r_total += n_ways
                    print(f"    {name}: {n_ways} roads")
        else:
            r_failed = True
            print(f"    {name}: FAILED ({status})")
            break

    if not r_failed:
        report["roads"]["count"] = r_total
        report["roads"]["count_method"] = "summed over 4 quadrants"

    # Refresh coverage assessment
    b = report["buildings"]
    r_ = report["roads"]
    report["coverage_assessment"] = {
        "total_buildings": b.get("count"),
        "buildings_named_pct": b.get("tag_coverage_pct", {}).get("name"),
        "buildings_height_or_levels_pct": max(
            b.get("tag_coverage_pct", {}).get("height", 0),
            b.get("tag_coverage_pct", {}).get("building:levels", 0),
        ) if b.get("tag_coverage_pct") else None,
        "total_roads": r_.get("count"),
        "roads_named_pct": r_.get("tag_coverage_pct", {}).get("name"),
        "roads_surface_pct": r_.get("tag_coverage_pct", {}).get("surface"),
        "road_classification_breakdown": r_.get("classification_breakdown"),
    }

    # Drop the huge building_sample_first payload (354k nodes) which bloats the report
    if "sample_first" in report.get("buildings", {}):
        sf = report["buildings"]["sample_first"]
        if isinstance(sf, dict) and "nodes" in sf:
            report["buildings"]["sample_first"] = {
                "type": sf.get("type"),
                "id": sf.get("id"),
                "tags": sf.get("tags"),
                "node_count": len(sf.get("nodes", [])),
            }

    save("osm_central_coast", report)
    return report


# -----------------------------------------------------------------------------
# Fix 4: Planning Portal APIs — try proper filter schema
# -----------------------------------------------------------------------------
def fix_planning_portal():
    print("\n--- Fix 4: Planning Portal APIs (structured filters) ---")
    endpoints = {
        "planning_portal_da": "https://api.apps1.nsw.gov.au/eplanning/data/v0/OnlineDA",
        "planning_portal_cdc": "https://api.apps1.nsw.gov.au/eplanning/data/v0/OnlineCDC",
        # PCC returned 404 — try alternate casing
        "planning_portal_pcc": "https://api.apps1.nsw.gov.au/eplanning/data/v0/OnlineOC",  # Occupation Cert
    }
    attempts = []

    # Variant A: array councilname + date range (most common NSW ePlanning shape)
    filter_variants = [
        {
            "label": "array-council-with-date-range",
            "filters": {
                "CouncilName": ["Central Coast Council"],
                "LodgementDateFrom": "2025-01-01",
                "LodgementDateTo": "2026-04-20",
            },
        },
        {
            "label": "array-council-no-dates",
            "filters": {"CouncilName": ["Central Coast Council"]},
        },
        {
            "label": "string-council-with-date-range",
            "filters": {
                "CouncilName": "Central Coast Council",
                "LodgementDateFrom": "2025-01-01",
                "LodgementDateTo": "2026-04-20",
            },
        },
        {
            "label": "date-range-only",
            "filters": {
                "LodgementDateFrom": "2026-01-01",
                "LodgementDateTo": "2026-04-20",
            },
        },
    ]

    report = {"endpoints": {}}
    for key, url in endpoints.items():
        print(f"  testing {key} ({url})")
        per = {"url": url, "attempts": []}
        success = False
        for variant in filter_variants:
            if success:
                break
            try:
                r = requests.get(
                    url,
                    params={
                        "filters": json.dumps(variant["filters"]),
                        "page": 1,
                        "pagesize": 5,
                    },
                    headers=HEADERS,
                    timeout=30,
                )
                attempt = {
                    "variant": variant["label"],
                    "http_status": r.status_code,
                    "body_start": r.text[:400],
                }
                if r.status_code == 200:
                    try:
                        payload = r.json()
                        attempt["response_keys"] = list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
                        # extract sample record
                        for k in ("Application", "Applications", "items", "data", "results", "Results"):
                            if isinstance(payload, dict) and k in payload:
                                val = payload[k]
                                if isinstance(val, list) and val:
                                    attempt["sample_record_keys"] = list(val[0].keys()) if isinstance(val[0], dict) else None
                                    attempt["sample_record"] = val[0]
                                    break
                            elif isinstance(payload, list) and payload:
                                attempt["sample_record"] = payload[0]
                                attempt["sample_record_keys"] = list(payload[0].keys()) if isinstance(payload[0], dict) else None
                                break
                        success = True
                    except Exception as e:
                        attempt["parse_error"] = str(e)
                per["attempts"].append(attempt)
            except Exception as e:
                per["attempts"].append({"variant": variant["label"], "error": str(e)})

        # Classify status
        statuses = [a.get("http_status") for a in per["attempts"]]
        if 200 in statuses:
            per["status"] = "live"
        elif any(s in (401, 403) for s in statuses):
            per["status"] = "auth_required"
        elif all(s == 404 for s in statuses):
            per["status"] = "not_found"
        elif all(s == 400 for s in statuses if s is not None):
            per["status"] = "bad_request_all_variants"
        else:
            per["status"] = f"error_{statuses}"
        report["endpoints"][key] = per

    report["note"] = (
        "PCC endpoint name 'OnlinePCC' returns 404 — attempted OnlineOC (Occupation Certificate) "
        "as the likely real endpoint. Full resolution requires NSW data dictionary from Data Broker."
    )
    save("planning_portal_apis", report)
    return report


if __name__ == "__main__":
    fix_arcgis_count()
    fix_wfs_cadastre()
    fix_osm_counts()
    fix_planning_portal()
    print("\nRound 2 complete. Regenerate summary next.")
