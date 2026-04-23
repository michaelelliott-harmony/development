"""
Harmony Pillar 2 — Endpoint Validation Script
Validates four programmatic data sources for the Central Coast NSW pilot.
Read-only; produces JSON reports under validation/.
"""
import json
import time
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode, quote

import requests

OUT_DIR = Path(__file__).parent
BBOX = {"south": -33.55, "north": -33.15, "west": 151.15, "east": 151.75}
VALIDATION_DATE = "2026-04-19"
HEADERS = {"User-Agent": "Harmony-Pillar2-EndpointValidator/1.0"}
TIMEOUT = 60


def write_report(name: str, data: dict) -> None:
    path = OUT_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, default=str))
    print(f"  -> wrote {path}")


def http_get(url: str, params: dict | None = None, timeout: int = TIMEOUT) -> requests.Response:
    return requests.get(url, params=params, headers=HEADERS, timeout=timeout)


# --------------------------------------------------------------------------
# Task 1: ArcGIS REST — NSW Planning Portal Land Zoning
# --------------------------------------------------------------------------
def validate_arcgis_zoning() -> dict:
    print("\n=== Task 1: ArcGIS REST — NSW Planning Portal Zoning ===")
    base = "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/EPI_Primary_Planning_Layers/MapServer"
    report: dict = {
        "endpoint": base,
        "service_metadata": {},
        "land_zoning_layer": {},
        "sample_query": {},
        "total_count": None,
        "issues": [],
    }

    # 1) Service metadata
    try:
        r = http_get(base, {"f": "json"})
        report["service_metadata"]["http_status"] = r.status_code
        if r.status_code == 200:
            meta = r.json()
            layers = meta.get("layers", [])
            report["service_metadata"]["service_description"] = meta.get("serviceDescription", "")[:200]
            report["service_metadata"]["layer_summary"] = [
                {"id": l.get("id"), "name": l.get("name"), "type": l.get("type")}
                for l in layers
            ]
            # identify land zoning layer
            zoning_candidates = [
                l for l in layers
                if "zoning" in (l.get("name") or "").lower() or "land_zoning" in (l.get("name") or "").lower()
            ]
            if zoning_candidates:
                zl = zoning_candidates[0]
                report["land_zoning_layer"] = {"id": zl["id"], "name": zl["name"]}
            else:
                report["issues"].append("No layer with 'zoning' in name; inspect layer_summary")
        else:
            report["issues"].append(f"Service metadata returned {r.status_code}")
            return report
    except Exception as e:
        report["issues"].append(f"Service metadata request failed: {e}")
        return report

    layer_id = report["land_zoning_layer"].get("id")
    if layer_id is None:
        # fall back: try each layer to find the zoning one by field presence
        for cand in report["service_metadata"].get("layer_summary", []):
            if cand.get("type") == "Feature Layer":
                layer_id = cand["id"]
                report["land_zoning_layer"] = {"id": cand["id"], "name": cand["name"], "note": "guessed-first-feature-layer"}
                break

    if layer_id is None:
        report["issues"].append("Could not determine any layer id")
        return report

    # 2) Layer metadata
    try:
        lr = http_get(f"{base}/{layer_id}", {"f": "json"})
        if lr.status_code == 200:
            lmeta = lr.json()
            report["land_zoning_layer"]["fields"] = [
                {"name": f.get("name"), "type": f.get("type"), "alias": f.get("alias")}
                for f in lmeta.get("fields", [])
            ]
            report["land_zoning_layer"]["geometryType"] = lmeta.get("geometryType")
            report["land_zoning_layer"]["extent"] = lmeta.get("extent")
            report["land_zoning_layer"]["maxRecordCount"] = lmeta.get("maxRecordCount")
    except Exception as e:
        report["issues"].append(f"Layer metadata request failed: {e}")

    # 3) Sample query
    query_url = f"{base}/{layer_id}/query"
    query_params = {
        "where": "1=1",
        "geometry": f"{BBOX['west']},{BBOX['south']},{BBOX['east']},{BBOX['north']}",
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "f": "geojson",
        "resultRecordCount": 10,
    }
    try:
        qr = http_get(query_url, query_params)
        report["sample_query"]["http_status"] = qr.status_code
        if qr.status_code == 200:
            qdata = qr.json()
            features = qdata.get("features", [])
            report["sample_query"]["feature_count_in_sample"] = len(features)
            report["sample_query"]["crs"] = qdata.get("crs") or "assumed EPSG:4326 (geojson)"
            report["sample_query"]["exceededTransferLimit"] = qdata.get("exceededTransferLimit", False)
            if features:
                first = features[0]
                report["sample_query"]["geometry_type"] = first.get("geometry", {}).get("type")
                report["sample_query"]["sample_feature"] = first
                props = first.get("properties", {})
                report["sample_query"]["field_names"] = sorted(props.keys())
                required = ["SYM_CODE", "LAY_CLASS", "EPI_NAME", "LGA_NAME", "LAM_ID"]
                report["sample_query"]["required_fields_present"] = {
                    f: f in props for f in required
                }
        else:
            report["issues"].append(f"Sample query returned {qr.status_code}: {qr.text[:200]}")
    except Exception as e:
        report["issues"].append(f"Sample query failed: {e}")

    # 4) Total count
    try:
        cr = http_get(query_url, {**query_params, "returnCountOnly": "true", "f": "json"})
        if cr.status_code == 200:
            cdata = cr.json()
            report["total_count"] = cdata.get("count")
    except Exception as e:
        report["issues"].append(f"Count query failed: {e}")

    print(f"  layer_id={layer_id}, sample={report['sample_query'].get('feature_count_in_sample')}, total={report['total_count']}")
    write_report("arcgis_rest_zoning", report)
    return report


# --------------------------------------------------------------------------
# Task 2: WFS — NSW Cadastre
# --------------------------------------------------------------------------
def validate_wfs_cadastre() -> dict:
    print("\n=== Task 2: WFS — NSW Cadastre ===")
    candidates = [
        "https://maps.six.nsw.gov.au/arcgis/services/public/NSW_Cadastre/MapServer/WFSServer",
        "https://maps.six.nsw.gov.au/arcgis/services/public/NSW_Land_Parcel_Property_Theme/MapServer/WFSServer",
    ]
    report: dict = {
        "endpoint_candidates": candidates,
        "endpoint_used": None,
        "capabilities_status": None,
        "feature_types": [],
        "lot_feature_type": None,
        "describe_feature_type": {},
        "sample_query": {},
        "issues": [],
    }

    chosen = None
    for url in candidates:
        try:
            r = http_get(url, {"service": "WFS", "request": "GetCapabilities"})
            report["capabilities_status"] = r.status_code
            if r.status_code == 200 and "<" in r.text[:200]:
                chosen = url
                report["endpoint_used"] = url
                # crude XML scan for FeatureType/Name
                import re
                names = re.findall(r"<(?:Name|wfs:Name)>([^<]+)</(?:Name|wfs:Name)>", r.text)
                report["feature_types"] = list(dict.fromkeys(names))[:40]
                # pick one that looks like lot/parcel/cadastre
                for n in names:
                    lower = n.lower()
                    if "lot" in lower or "parcel" in lower or "cadastre" in lower:
                        report["lot_feature_type"] = n
                        break
                if not report["lot_feature_type"] and names:
                    report["lot_feature_type"] = names[0]
                    report["issues"].append(f"No obvious lot/parcel type; first name used: {names[0]}")
                break
            else:
                report["issues"].append(f"Candidate {url} returned {r.status_code}")
        except Exception as e:
            report["issues"].append(f"Candidate {url} failed: {e}")

    if not chosen:
        report["issues"].append("No WFS candidate responded successfully")
        write_report("wfs_cadastre", report)
        return report

    # DescribeFeatureType
    lot_type = report["lot_feature_type"]
    if lot_type:
        try:
            dr = http_get(chosen, {
                "service": "WFS", "request": "DescribeFeatureType", "typeName": lot_type,
            })
            report["describe_feature_type"]["http_status"] = dr.status_code
            if dr.status_code == 200:
                # Extract element names from XSD
                import re
                elements = re.findall(r'<xs:element name="([^"]+)"\s+type="([^"]+)"', dr.text)
                if not elements:
                    elements = re.findall(r'<xsd:element name="([^"]+)"\s+type="([^"]+)"', dr.text)
                if not elements:
                    elements = re.findall(r'<element name="([^"]+)"\s+type="([^"]+)"', dr.text)
                report["describe_feature_type"]["fields"] = [
                    {"name": n, "type": t} for n, t in elements
                ]
        except Exception as e:
            report["issues"].append(f"DescribeFeatureType failed: {e}")

    # GetFeature — try lat,lon then lon,lat
    if lot_type:
        for bbox_order, label in [
            (f"{BBOX['south']},{BBOX['west']},{BBOX['north']},{BBOX['east']},EPSG:4326", "lat,lon"),
            (f"{BBOX['west']},{BBOX['south']},{BBOX['east']},{BBOX['north']},EPSG:4326", "lon,lat"),
        ]:
            try:
                gr = http_get(chosen, {
                    "service": "WFS",
                    "request": "GetFeature",
                    "typeName": lot_type,
                    "bbox": bbox_order,
                    "count": 10,
                    "outputFormat": "application/json",
                })
                report["sample_query"][f"bbox_order_{label}"] = {
                    "http_status": gr.status_code,
                    "response_start": gr.text[:300],
                }
                if gr.status_code == 200 and gr.text.strip().startswith("{"):
                    try:
                        gjson = gr.json()
                        features = gjson.get("features", [])
                        report["sample_query"]["feature_count"] = len(features)
                        report["sample_query"]["bbox_order_used"] = label
                        report["sample_query"]["crs"] = gjson.get("crs")
                        if features:
                            first = features[0]
                            report["sample_query"]["geometry_type"] = first.get("geometry", {}).get("type")
                            report["sample_query"]["sample_feature"] = first
                            props = first.get("properties", {})
                            report["sample_query"]["field_names"] = sorted(props.keys())
                            required = ["lotnumber", "plannumber", "sectionnumber", "cadid", "shapestarea", "planlabel"]
                            report["sample_query"]["required_fields_present"] = {
                                f: any(f.lower() == k.lower() for k in props.keys()) for f in required
                            }
                        break
                    except Exception as pe:
                        report["sample_query"][f"bbox_order_{label}"]["parse_error"] = str(pe)
            except Exception as e:
                report["issues"].append(f"GetFeature ({label}) failed: {e}")

    print(f"  endpoint={chosen}, lot_type={report['lot_feature_type']}, sample_count={report['sample_query'].get('feature_count')}")
    write_report("wfs_cadastre", report)
    return report


# --------------------------------------------------------------------------
# Task 3: OSM Overpass — Buildings and Roads
# --------------------------------------------------------------------------
def overpass_query(query: str, pause: float = 6.0) -> tuple[int, dict | str]:
    url = "https://overpass-api.de/api/interpreter"
    time.sleep(pause)
    r = requests.post(url, data={"data": query}, headers=HEADERS, timeout=180)
    if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("application/json"):
        return r.status_code, r.json()
    return r.status_code, r.text[:500]


def validate_osm() -> dict:
    print("\n=== Task 3: OSM Overpass — Buildings & Roads ===")
    report: dict = {
        "endpoint": "https://overpass-api.de/api/interpreter",
        "buildings": {"issues": []},
        "roads": {"issues": []},
    }
    bbox = f"{BBOX['south']},{BBOX['west']},{BBOX['north']},{BBOX['east']}"

    # Buildings — count
    print("  building count query...")
    status, data = overpass_query(
        f'[out:json][timeout:60];way["building"]({bbox});out count;',
        pause=1.0,
    )
    report["buildings"]["count_status"] = status
    if isinstance(data, dict):
        total = None
        for el in data.get("elements", []):
            if el.get("type") == "count":
                tags = el.get("tags", {})
                total = int(tags.get("ways") or tags.get("total") or 0)
        report["buildings"]["count"] = total
    else:
        report["buildings"]["count_error"] = data

    # Buildings — sample 20
    print("  building sample (waiting 6s)...")
    status, data = overpass_query(
        f'[out:json][timeout:120];way["building"]({bbox});out body 20;>;out skel qt;',
    )
    report["buildings"]["sample_status"] = status
    if isinstance(data, dict):
        elements = data.get("elements", [])
        ways = [e for e in elements if e.get("type") == "way"]
        nodes = [e for e in elements if e.get("type") == "node"]
        report["buildings"]["sample_way_count"] = len(ways)
        report["buildings"]["sample_node_count"] = len(nodes)
        tag_counter: Counter = Counter()
        building_types: Counter = Counter()
        fields_of_interest = ["building", "name", "addr:street", "addr:housenumber",
                              "addr:postcode", "addr:suburb", "height",
                              "building:levels", "roof:shape", "start_date"]
        for w in ways:
            tags = w.get("tags", {})
            for f in fields_of_interest:
                if f in tags:
                    tag_counter[f] += 1
            if "building" in tags:
                building_types[tags["building"]] += 1
        total_sample = max(len(ways), 1)
        report["buildings"]["tag_coverage_pct"] = {
            f: round(100 * tag_counter[f] / total_sample, 1) for f in fields_of_interest
        }
        report["buildings"]["building_type_distribution"] = dict(building_types)
        if ways:
            report["buildings"]["sample_first"] = ways[0]
    else:
        report["buildings"]["sample_error"] = data

    # Roads — count
    print("  road count (waiting 6s)...")
    status, data = overpass_query(
        f'[out:json][timeout:60];way["highway"]({bbox});out count;',
    )
    report["roads"]["count_status"] = status
    if isinstance(data, dict):
        total = None
        for el in data.get("elements", []):
            if el.get("type") == "count":
                tags = el.get("tags", {})
                total = int(tags.get("ways") or tags.get("total") or 0)
        report["roads"]["count"] = total
    else:
        report["roads"]["count_error"] = data

    # Roads — sample + classification breakdown (fuller sample for classification)
    print("  road classification breakdown (waiting 6s)...")
    # pull tags-only for all roads (light payload) to get classification distribution
    status, data = overpass_query(
        f'[out:json][timeout:120];way["highway"]({bbox});out tags;',
    )
    report["roads"]["classification_query_status"] = status
    if isinstance(data, dict):
        ways = [e for e in data.get("elements", []) if e.get("type") == "way"]
        highway_counter: Counter = Counter()
        tag_counter: Counter = Counter()
        fields_of_interest = ["highway", "name", "ref", "surface", "lanes",
                              "maxspeed", "oneway", "bridge", "tunnel", "lit"]
        for w in ways:
            tags = w.get("tags", {})
            if "highway" in tags:
                highway_counter[tags["highway"]] += 1
            for f in fields_of_interest:
                if f in tags:
                    tag_counter[f] += 1
        total_ways = max(len(ways), 1)
        report["roads"]["total_ways_seen"] = len(ways)
        report["roads"]["classification_breakdown"] = dict(highway_counter.most_common())
        report["roads"]["tag_coverage_pct"] = {
            f: round(100 * tag_counter[f] / total_ways, 1) for f in fields_of_interest
        }
    else:
        report["roads"]["classification_error"] = data

    # Roads — sample 20 with geometry
    print("  road sample with geometry (waiting 6s)...")
    status, data = overpass_query(
        f'[out:json][timeout:120];way["highway"]({bbox});out body 20;>;out skel qt;',
    )
    report["roads"]["sample_status"] = status
    if isinstance(data, dict):
        elements = data.get("elements", [])
        ways = [e for e in elements if e.get("type") == "way"]
        if ways:
            report["roads"]["sample_first"] = ways[0]

    # Coverage assessment
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

    print(f"  buildings={b.get('count')}, roads={r_.get('count')}")
    write_report("osm_central_coast", report)
    return report


# --------------------------------------------------------------------------
# Task 4: NSW Planning Portal DA/CDC/PCC APIs
# --------------------------------------------------------------------------
def validate_planning_portal_apis() -> dict:
    print("\n=== Task 4: NSW Planning Portal DA/CDC/PCC APIs ===")
    endpoints = {
        "planning_portal_da": "https://api.apps1.nsw.gov.au/eplanning/data/v0/OnlineDA",
        "planning_portal_cdc": "https://api.apps1.nsw.gov.au/eplanning/data/v0/OnlineCDC",
        "planning_portal_pcc": "https://api.apps1.nsw.gov.au/eplanning/data/v0/OnlinePCC",
    }
    report: dict = {"endpoints": {}}

    for key, url in endpoints.items():
        print(f"  testing {key}...")
        per = {"url": url, "attempts": [], "issues": []}
        # Attempt 1: filters-JSON query
        try:
            filt = json.dumps({"CouncilName": "Central Coast Council"})
            r = http_get(url, {"filters": filt, "page": 1, "pagesize": 5}, timeout=30)
            per["attempts"].append({
                "style": "filters-json",
                "http_status": r.status_code,
                "body_start": r.text[:500],
            })
            if r.status_code == 200:
                try:
                    per["attempts"][-1]["json_parsed"] = True
                    payload = r.json()
                    per["attempts"][-1]["response_keys"] = list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
                    # try to extract a sample record
                    for k in ("Application", "Applications", "items", "data", "results"):
                        if isinstance(payload, dict) and k in payload:
                            val = payload[k]
                            if isinstance(val, list) and val:
                                per["attempts"][-1]["sample_record"] = val[0]
                                per["attempts"][-1]["sample_keys"] = list(val[0].keys()) if isinstance(val[0], dict) else None
                                break
                except Exception as pe:
                    per["attempts"][-1]["parse_error"] = str(pe)
        except Exception as e:
            per["issues"].append(f"filters-json request failed: {e}")

        # Attempt 2: flat query string
        try:
            r = http_get(url, {"CouncilName": "Central Coast Council", "PageSize": 5, "PageNumber": 1}, timeout=30)
            per["attempts"].append({
                "style": "flat-params",
                "http_status": r.status_code,
                "body_start": r.text[:500],
            })
        except Exception as e:
            per["issues"].append(f"flat-params request failed: {e}")

        # Determine summary status
        statuses = [a.get("http_status") for a in per["attempts"]]
        if 200 in statuses:
            per["status"] = "live"
        elif any(s in (401, 403) for s in statuses):
            per["status"] = "auth_required"
        elif any(s in (404,) for s in statuses):
            per["status"] = "not_found"
        elif any(s is None for s in statuses):
            per["status"] = "connection_error"
        else:
            per["status"] = f"error_{statuses}"
        report["endpoints"][key] = per

    report["note"] = "Access confirmation pending via Data Broker email sent 2026-04-20. Failures here only affect Milestone 7."
    write_report("planning_portal_apis", report)
    return report


# --------------------------------------------------------------------------
# Task 5: Summary
# --------------------------------------------------------------------------
def produce_summary(zoning, cadastre, osm, permits) -> dict:
    print("\n=== Task 5: Summary Report ===")

    # Zoning summary
    z_sample = zoning.get("sample_query", {})
    z_present = z_sample.get("required_fields_present", {})
    z_fields_confirmed = [f for f, ok in z_present.items() if ok]
    z_fields_missing = [f for f, ok in z_present.items() if not ok]
    z_status = "live" if z_sample.get("http_status") == 200 and z_sample.get("feature_count_in_sample") else "error"
    zoning_summary = {
        "status": z_status,
        "layer_id": zoning.get("land_zoning_layer", {}).get("id"),
        "layer_name": zoning.get("land_zoning_layer", {}).get("name"),
        "feature_count_total": zoning.get("total_count"),
        "feature_count_sample": z_sample.get("feature_count_in_sample"),
        "fields_confirmed": z_fields_confirmed,
        "fields_missing": z_fields_missing,
        "crs": z_sample.get("crs"),
        "pagination_required": z_sample.get("exceededTransferLimit"),
        "issues": zoning.get("issues", []),
    }

    # Cadastre summary
    c_sample = cadastre.get("sample_query", {})
    c_present = c_sample.get("required_fields_present", {})
    cad_status = "live" if c_sample.get("feature_count") else (
        "error" if cadastre.get("issues") else "blocked"
    )
    cadastre_summary = {
        "status": cad_status,
        "endpoint_used": cadastre.get("endpoint_used"),
        "lot_feature_type": cadastre.get("lot_feature_type"),
        "feature_count_sample": c_sample.get("feature_count"),
        "fields_confirmed": [f for f, ok in c_present.items() if ok],
        "fields_missing": [f for f, ok in c_present.items() if not ok],
        "crs": c_sample.get("crs"),
        "bbox_order_used": c_sample.get("bbox_order_used"),
        "issues": cadastre.get("issues", []),
    }

    # OSM summaries
    cov = osm.get("coverage_assessment", {})
    osm_b_status = "live" if osm.get("buildings", {}).get("count") else "error"
    osm_r_status = "live" if osm.get("roads", {}).get("count") else "error"
    osm_buildings_summary = {
        "status": osm_b_status,
        "feature_count": cov.get("total_buildings"),
        "tag_coverage": osm.get("buildings", {}).get("tag_coverage_pct", {}),
        "type_distribution": osm.get("buildings", {}).get("building_type_distribution", {}),
        "issues": osm.get("buildings", {}).get("issues", []),
    }
    osm_roads_summary = {
        "status": osm_r_status,
        "feature_count": cov.get("total_roads"),
        "classification_breakdown": cov.get("road_classification_breakdown", {}),
        "tag_coverage": osm.get("roads", {}).get("tag_coverage_pct", {}),
        "issues": osm.get("roads", {}).get("issues", []),
    }

    # Permit APIs
    permit_endpoints = permits.get("endpoints", {})

    summary = {
        "validation_date": VALIDATION_DATE,
        "pilot_region": "Central Coast NSW",
        "bounding_box": BBOX,
        "endpoints": {
            "arcgis_rest_zoning": zoning_summary,
            "wfs_cadastre": cadastre_summary,
            "osm_buildings": osm_buildings_summary,
            "osm_roads": osm_roads_summary,
            "planning_portal_da": {"status": permit_endpoints.get("planning_portal_da", {}).get("status"), "issues": permit_endpoints.get("planning_portal_da", {}).get("issues", [])},
            "planning_portal_cdc": {"status": permit_endpoints.get("planning_portal_cdc", {}).get("status"), "issues": permit_endpoints.get("planning_portal_cdc", {}).get("issues", [])},
            "planning_portal_pcc": {"status": permit_endpoints.get("planning_portal_pcc", {}).get("status"), "issues": permit_endpoints.get("planning_portal_pcc", {}).get("issues", [])},
        },
    }

    # Sprint 1 readiness — Milestones 1–6 only depend on zoning/cadastre/OSM
    blockers = []
    recommendations = []
    if zoning_summary["status"] != "live":
        blockers.append("ArcGIS REST zoning endpoint not live")
    if cadastre_summary["status"] != "live":
        blockers.append("WFS cadastre endpoint not live — fallback to Data Broker bulk download")
    if osm_buildings_summary["status"] != "live":
        blockers.append("OSM buildings query failed")
    if osm_roads_summary["status"] != "live":
        blockers.append("OSM roads query failed")

    if zoning_summary.get("fields_missing"):
        recommendations.append(f"Zoning fields missing in sample: {zoning_summary['fields_missing']} — verify against full layer schema")
    if cadastre_summary.get("fields_missing"):
        recommendations.append(f"Cadastre fields missing: {cadastre_summary['fields_missing']} — may be naming differences")
    if cov.get("buildings_named_pct", 0) and cov["buildings_named_pct"] < 10:
        recommendations.append("OSM building 'name' tag coverage is low — expected for residential-heavy area")
    if cov.get("buildings_height_or_levels_pct", 0) < 10:
        recommendations.append("OSM building height/levels coverage <10% — accept for MVP, note in schema positional_accuracy")

    m7_blockers = [k for k in ("planning_portal_da", "planning_portal_cdc", "planning_portal_pcc")
                   if permit_endpoints.get(k, {}).get("status") != "live"]
    if m7_blockers:
        recommendations.append(f"Milestone 7 endpoints not publicly accessible: {m7_blockers} — await Data Broker access confirmation")

    if not blockers:
        summary["sprint_1_readiness"] = "ready"
    elif len(blockers) <= 1 and "cadastre" in blockers[0].lower():
        summary["sprint_1_readiness"] = "partial"
    else:
        summary["sprint_1_readiness"] = "blocked"

    summary["blockers"] = blockers
    summary["recommendations"] = recommendations

    write_report("endpoint_validation_summary", summary)
    return summary


def print_plain_summary(s: dict) -> None:
    print("\n" + "=" * 78)
    print("HARMONY PILLAR 2 — ENDPOINT VALIDATION SUMMARY")
    print("=" * 78)
    print(f"Date: {s['validation_date']}  Region: {s['pilot_region']}")
    print(f"BBox: S={s['bounding_box']['south']} N={s['bounding_box']['north']} "
          f"W={s['bounding_box']['west']} E={s['bounding_box']['east']}")
    print()
    eps = s["endpoints"]

    def line(label, data):
        st = data.get("status", "?")
        extra = []
        if "feature_count" in data and data.get("feature_count") is not None:
            extra.append(f"features={data['feature_count']}")
        if "feature_count_total" in data and data.get("feature_count_total") is not None:
            extra.append(f"total={data['feature_count_total']}")
        if data.get("crs"):
            extra.append(f"crs={data['crs']}")
        print(f"  {label:30s} {st:16s} {' '.join(extra)}")

    print("Endpoints:")
    line("ArcGIS zoning", eps["arcgis_rest_zoning"])
    line("WFS cadastre", eps["wfs_cadastre"])
    line("OSM buildings", eps["osm_buildings"])
    line("OSM roads", eps["osm_roads"])
    line("Planning Portal DA", eps["planning_portal_da"])
    line("Planning Portal CDC", eps["planning_portal_cdc"])
    line("Planning Portal PCC", eps["planning_portal_pcc"])

    print(f"\nSprint 1 readiness: {s['sprint_1_readiness'].upper()}")
    if s["blockers"]:
        print("\nBlockers:")
        for b in s["blockers"]:
            print(f"  - {b}")
    if s["recommendations"]:
        print("\nRecommendations:")
        for r in s["recommendations"]:
            print(f"  - {r}")

    # Key questions
    print("\nKey questions answered:")
    print(f"  1. Endpoints live? {sum(1 for e in eps.values() if e.get('status') == 'live')}/7")
    print(f"  2. ArcGIS zoning fields match entity schema? {'YES' if not eps['arcgis_rest_zoning'].get('fields_missing') else 'PARTIAL — missing ' + str(eps['arcgis_rest_zoning']['fields_missing'])}")
    print(f"  3. Cadastre fields match? {'YES' if not eps['wfs_cadastre'].get('fields_missing') else 'PARTIAL — missing ' + str(eps['wfs_cadastre'].get('fields_missing'))}")
    print(f"  4. OSM coverage: buildings={eps['osm_buildings'].get('feature_count')}, roads={eps['osm_roads'].get('feature_count')}")
    print(f"  5. Milestones 1–6 path: {'CLEAR' if s['sprint_1_readiness'] in ('ready', 'partial') else 'BLOCKED'}")
    print(f"  6. Milestone 7 readiness: {'PENDING — ' + ','.join(k for k in ('planning_portal_da','planning_portal_cdc','planning_portal_pcc') if eps[k].get('status') != 'live') or 'READY'}")
    print("=" * 78 + "\n")


def main() -> int:
    try:
        zoning = validate_arcgis_zoning()
    except Exception as e:
        print(f"Zoning validation crashed: {e}")
        zoning = {"issues": [f"crash: {e}"]}

    try:
        cadastre = validate_wfs_cadastre()
    except Exception as e:
        print(f"Cadastre validation crashed: {e}")
        cadastre = {"issues": [f"crash: {e}"]}

    try:
        osm = validate_osm()
    except Exception as e:
        print(f"OSM validation crashed: {e}")
        osm = {"issues": [f"crash: {e}"], "buildings": {}, "roads": {}}

    try:
        permits = validate_planning_portal_apis()
    except Exception as e:
        print(f"Permit API validation crashed: {e}")
        permits = {"endpoints": {}}

    summary = produce_summary(zoning, cadastre, osm, permits)
    print_plain_summary(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
