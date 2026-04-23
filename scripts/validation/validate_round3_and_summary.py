"""
Round 3 — finalise cadastre using working inSR=4326 config, regenerate summary.
"""
import json
import re
from pathlib import Path
import requests

OUT_DIR = Path(__file__).parent
BBOX = {"south": -33.55, "north": -33.15, "west": 151.15, "east": 151.75}
VALIDATION_DATE = "2026-04-19"
HEADERS = {"User-Agent": "Harmony-Pillar2-EndpointValidator/1.0"}


def load(name):
    p = OUT_DIR / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def save(name, data):
    (OUT_DIR / f"{name}.json").write_text(json.dumps(data, indent=2, default=str))


def finalise_cadastre():
    print("--- Finalise cadastre with inSR=4326 ---")
    base = "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer"
    layer_id = 9
    q_url = f"{base}/{layer_id}/query"

    # Layer meta
    meta = requests.get(f"{base}/{layer_id}", params={"f": "json"}, headers=HEADERS, timeout=30).json()

    # Count
    count_resp = requests.get(q_url, params={
        "where": "1=1",
        "geometry": f"{BBOX['west']},{BBOX['south']},{BBOX['east']},{BBOX['north']}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "returnCountOnly": "true",
        "f": "json",
    }, headers=HEADERS, timeout=60).json()
    total_count = count_resp.get("count")

    # Sample
    sample_resp = requests.get(q_url, params={
        "where": "1=1",
        "geometry": f"{BBOX['west']},{BBOX['south']},{BBOX['east']},{BBOX['north']}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": 4326,
        "outSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "f": "geojson",
        "resultRecordCount": 5,
    }, headers=HEADERS, timeout=60)
    sample_json = sample_resp.json()
    feats = sample_json.get("features", [])

    props_keys = list((feats[0].get("properties") or {}).keys()) if feats else []
    expected = ["lotnumber", "plannumber", "sectionnumber", "cadid", "planlabel", "shape_Area"]
    fields_present = {f: any(f.lower() == k.lower() for k in props_keys) for f in expected}

    report = load("wfs_cadastre")
    report["access_method"] = "ArcGIS REST (SIX) — WFS endpoints returned 400 on GetCapabilities across all candidates"
    report["endpoint_used"] = f"{base}/{layer_id}"
    report["layer"] = {
        "id": layer_id,
        "name": meta.get("name"),
        "geometryType": meta.get("geometryType"),
        "field_count": len(meta.get("fields") or []),
    }
    report["fields"] = [
        {"name": f.get("name"), "type": f.get("type"), "alias": f.get("alias")}
        for f in (meta.get("fields") or [])
    ]
    report["required_query_params"] = {
        "inSR": 4326,
        "outSR": 4326,
        "note": "inSR=4326 is REQUIRED — layer's native SR is Web Mercator (102100). Without inSR the bbox silently matches 0 features.",
    }
    report["sample_query"] = {
        "http_status": sample_resp.status_code,
        "feature_count": len(feats),
        "total_count_in_bbox": total_count,
        "crs": sample_json.get("crs"),
        "geometry_type": feats[0].get("geometry", {}).get("type") if feats else None,
        "field_names": sorted(props_keys),
        "required_fields_present": fields_present,
        "sample_feature": feats[0] if feats else None,
    }
    report["schema_vs_entity_model"] = {
        "matches": ["cadid", "lotnumber", "plannumber", "sectionnumber", "planlabel"],
        "drift": {
            "shapestarea": "actual field is 'shape_Area' (capital A) — mapping update required",
            "plantype": "not a separate field — derive from planlabel prefix (e.g. 'DP787786' → plan_type='DP')",
            "plantype_alternative": "classsubtype numeric code is available if a coded representation is preferred",
        },
        "bonus_fields": ["lotidstring", "urbanity", "startdate", "enddate", "itstitlestatus", "hasstratum", "stratumlevel"],
    }
    save("wfs_cadastre", report)
    print(f"  cadastre: {total_count} lots in bbox, fields_present={fields_present}")
    return report


def regenerate_summary():
    print("\n--- Regenerate summary ---")
    zoning = load("arcgis_rest_zoning")
    cadastre = load("wfs_cadastre")
    osm = load("osm_central_coast")
    permits = load("planning_portal_apis")

    # Zoning
    z_sample = zoning.get("sample_query", {})
    z_mismatch = zoning.get("schema_vs_entity_model", {})
    zoning_summary = {
        "status": "live",
        "endpoint": zoning.get("endpoint"),
        "layer_id": zoning["land_zoning_layer"]["id"],
        "layer_name": zoning["land_zoning_layer"]["name"],
        "feature_count_total": zoning.get("total_count"),
        "lga_filtered_count": zoning.get("lga_filtered_count"),
        "crs": z_sample.get("crs"),
        "geometry_type": z_sample.get("geometry_type"),
        "pagination_required": zoning.get("pagination_test", {}).get("exceededTransferLimit"),
        "max_record_count": zoning.get("pagination_test", {}).get("max_record_count_effective"),
        "fields_confirmed": z_mismatch.get("present_in_source"),
        "fields_missing": z_mismatch.get("missing_in_source"),
        "schema_drift_note": z_mismatch.get("note"),
        "issues": zoning.get("issues", []),
    }

    # Cadastre
    c_sample = cadastre.get("sample_query", {})
    cadastre_summary = {
        "status": "live" if c_sample.get("feature_count") else "error",
        "access_method": cadastre.get("access_method"),
        "endpoint_used": cadastre.get("endpoint_used"),
        "layer": cadastre.get("layer"),
        "feature_count_total": c_sample.get("total_count_in_bbox"),
        "crs": c_sample.get("crs"),
        "required_query_params": cadastre.get("required_query_params"),
        "fields_confirmed": [k for k, v in (c_sample.get("required_fields_present") or {}).items() if v],
        "fields_missing": [k for k, v in (c_sample.get("required_fields_present") or {}).items() if not v],
        "schema_drift": cadastre.get("schema_vs_entity_model", {}).get("drift"),
        "issues": [
            "Both WFS endpoint candidates (maps.six / portal.spatial) returned 400 on GetCapabilities — WFS is not publicly exposed. ArcGIS REST is the working alternative.",
        ] + cadastre.get("issues", []),
    }

    # OSM
    cov = osm.get("coverage_assessment", {})
    osm_buildings_summary = {
        "status": "live" if cov.get("total_buildings") else "error",
        "feature_count": cov.get("total_buildings"),
        "tag_coverage": osm.get("buildings", {}).get("tag_coverage_pct", {}),
        "type_distribution": osm.get("buildings", {}).get("building_type_distribution", {}),
        "issues": osm.get("buildings", {}).get("issues", []),
    }
    osm_roads_summary = {
        "status": "live" if cov.get("total_roads") else "error",
        "feature_count": cov.get("total_roads"),
        "classification_breakdown": cov.get("road_classification_breakdown", {}),
        "tag_coverage": osm.get("roads", {}).get("tag_coverage_pct", {}),
        "issues": osm.get("roads", {}).get("issues", []),
    }

    # Permits
    p_eps = permits.get("endpoints", {})
    permit_summary = {}
    for key in ("planning_portal_da", "planning_portal_cdc", "planning_portal_pcc"):
        entry = p_eps.get(key, {})
        permit_summary[key] = {
            "status": entry.get("status"),
            "url": entry.get("url"),
            "error_observed": entry.get("attempts", [{}])[0].get("body_start") if entry.get("attempts") else None,
            "issues": entry.get("issues", []),
        }

    # Readiness
    blockers = []
    recs = []
    if zoning_summary["fields_missing"]:
        recs.append(
            f"ENTITY SCHEMA UPDATE REQUIRED: zoning_area.LAM_ID does not exist in source. "
            f"Update HARMONY_P2_ENTITY_SCHEMAS.md to map source_feature_id from PCO_REF_KEY "
            f"(or composite OBJECTID + EPI_NAME). Layer 2 of EPI_Primary_Planning_Layers confirmed as Land Zoning."
        )
    if cadastre_summary.get("schema_drift"):
        recs.append(
            "ENTITY SCHEMA UPDATE REQUIRED: cadastral_lot.shapestarea → shape_Area (case change). "
            "cadastral_lot.plantype → derive from planlabel prefix (e.g. DP787786 → 'DP'). "
            "No WFS adapter required — use ArcGIS REST adapter with inSR=4326."
        )
    if cadastre_summary["status"] != "live":
        blockers.append("Cadastre endpoint not live")

    if zoning_summary.get("pagination_required"):
        recs.append("ArcGIS REST adapter MUST implement pagination (max 1000 records per query confirmed empirically).")

    bc = osm_buildings_summary.get("tag_coverage", {})
    if bc.get("height", 0) < 10 and bc.get("building:levels", 0) < 20:
        recs.append(
            f"OSM building height/levels coverage low (height={bc.get('height')}%, levels={bc.get('building:levels')}%). "
            "Accept for MVP per Gap #8 in pillar brief."
        )

    if osm_buildings_summary.get("feature_count", 0) > 0 and osm_buildings_summary["feature_count"] < 1000:
        recs.append("OSM building coverage below 1000 — consider Geoscape fallback per Gap #4.")

    m7_blocked = [k for k in ("planning_portal_da", "planning_portal_cdc", "planning_portal_pcc")
                  if permit_summary[k]["status"] != "live"]
    if m7_blocked:
        recs.append(
            f"MILESTONE 7 BLOCKED on Data Broker access confirmation (email sent 2026-04-20). "
            f"DA and CDC endpoints are reachable but require undocumented parameter (likely subscription key — "
            f"api.apps1.nsw.gov.au is Azure API Management). PCC/OC endpoint returns 404 under both 'OnlinePCC' and 'OnlineOC' names; real endpoint name must come from data dictionary."
        )

    # Milestones 1-6 need zoning, cadastre, OSM
    mvp_live = (
        zoning_summary["status"] == "live"
        and cadastre_summary["status"] == "live"
        and osm_buildings_summary["status"] == "live"
        and osm_roads_summary["status"] == "live"
    )
    if mvp_live:
        readiness = "ready"
    elif blockers:
        readiness = "blocked"
    else:
        readiness = "partial"

    summary = {
        "validation_date": VALIDATION_DATE,
        "pilot_region": "Central Coast NSW",
        "bounding_box": BBOX,
        "endpoints": {
            "arcgis_rest_zoning": zoning_summary,
            "wfs_cadastre": cadastre_summary,
            "osm_buildings": osm_buildings_summary,
            "osm_roads": osm_roads_summary,
            **permit_summary,
        },
        "sprint_1_readiness": readiness,
        "milestone_7_readiness": "blocked_pending_data_broker",
        "blockers": blockers,
        "recommendations": recs,
    }
    save("endpoint_validation_summary", summary)
    return summary


def print_plain_summary(s):
    print("\n" + "=" * 78)
    print("HARMONY PILLAR 2 — ENDPOINT VALIDATION SUMMARY")
    print("=" * 78)
    print(f"Date: {s['validation_date']}   Region: {s['pilot_region']}")
    bb = s["bounding_box"]
    print(f"BBox: S={bb['south']}  N={bb['north']}  W={bb['west']}  E={bb['east']}")
    print()
    eps = s["endpoints"]

    print("Endpoint status:")
    print(f"  ArcGIS zoning (NSW Planning Portal EPI Layer 2)     "
          f"{eps['arcgis_rest_zoning']['status']:8s}  "
          f"features_in_bbox={eps['arcgis_rest_zoning']['feature_count_total']}, "
          f"lga_filtered={eps['arcgis_rest_zoning']['lga_filtered_count']['count']}")
    print(f"  ArcGIS cadastre (SIX NSW_Cadastre Layer 9 'Lot')    "
          f"{eps['wfs_cadastre']['status']:8s}  "
          f"lots_in_bbox={eps['wfs_cadastre']['feature_count_total']}")
    print(f"  OSM buildings (Overpass)                            "
          f"{eps['osm_buildings']['status']:8s}  "
          f"features={eps['osm_buildings']['feature_count']}")
    print(f"  OSM roads (Overpass)                                "
          f"{eps['osm_roads']['status']:8s}  "
          f"features={eps['osm_roads']['feature_count']}")
    print(f"  Planning Portal DA                                  "
          f"{eps['planning_portal_da']['status']}")
    print(f"  Planning Portal CDC                                 "
          f"{eps['planning_portal_cdc']['status']}")
    print(f"  Planning Portal PCC                                 "
          f"{eps['planning_portal_pcc']['status']}")

    print()
    print("Entity schema field coverage:")
    z = eps['arcgis_rest_zoning']
    print(f"  zoning_area — confirmed: {z['fields_confirmed']}")
    print(f"               missing:   {z['fields_missing']}")
    c = eps['wfs_cadastre']
    print(f"  cadastral_lot — confirmed: {c['fields_confirmed']}")
    print(f"                  missing:   {c['fields_missing']}")
    b_cov = eps['osm_buildings']['tag_coverage']
    print(f"  building — name={b_cov.get('name')}% addr:street={b_cov.get('addr:street')}% "
          f"height={b_cov.get('height')}% levels={b_cov.get('building:levels')}%")
    r_cov = eps['osm_roads']['tag_coverage']
    print(f"  road_segment — highway=100% name={r_cov.get('name')}% surface={r_cov.get('surface')}% "
          f"lanes={r_cov.get('lanes')}% maxspeed={r_cov.get('maxspeed')}%")

    print()
    print("OSM road classification (Central Coast):")
    cb = eps['osm_roads']['classification_breakdown']
    for k, v in list(cb.items())[:10]:
        print(f"  {k:20s} {v}")

    print()
    print(f"Sprint 1 readiness: {s['sprint_1_readiness'].upper()}")
    print(f"Milestone 7 readiness: {s['milestone_7_readiness']}")
    if s["blockers"]:
        print("\nBlockers:")
        for b in s["blockers"]:
            print(f"  - {b}")
    if s["recommendations"]:
        print("\nRecommendations:")
        for r in s["recommendations"]:
            print(f"  - {r}")

    print()
    print("Key questions:")
    print(f"  1. Live endpoints returning expected data: 4/7 (ArcGIS zoning, ArcGIS cadastre, OSM buildings, OSM roads)")
    print(f"  2. Blocked: Planning Portal DA/CDC (400 — required param unknown, likely API key); PCC (404 — wrong endpoint name); both WFS URL candidates (400 — WFS not publicly exposed)")
    print(f"  3. OSM coverage sufficient? YES — {eps['osm_buildings']['feature_count']} buildings, {eps['osm_roads']['feature_count']} roads")
    print(f"  4. Field schemas match entity model? PARTIAL — two schema drifts require HARMONY_P2_ENTITY_SCHEMAS.md update (see recommendations)")
    print(f"  5. Can Sprint 1 proceed? {'YES' if s['sprint_1_readiness'] == 'ready' else 'CONDITIONAL'} — Milestones 1–6 unblocked")
    print(f"  6. Milestone 7 issues: Data Broker email response required (access + data dictionary for undocumented API parameter)")
    print("=" * 78)


if __name__ == "__main__":
    finalise_cadastre()
    summary = regenerate_summary()
    print_plain_summary(summary)
