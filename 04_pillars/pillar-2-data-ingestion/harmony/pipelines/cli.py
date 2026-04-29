# Harmony Spatial Operating System — Pillar 2 — Data Ingestion Pipeline
#
# CLI entry point: harmony-ingest
#
# Usage:
#   harmony-ingest read <manifest.yaml>   — print feature count + sample
#   harmony-ingest health                  — check Pillar 1 API is reachable

import json
import sys

import click
import yaml

from .manifest import load as load_manifest, ManifestError, get_adapter
from .adapters.base import AdapterConfigError, AdapterConnectionError


@click.group()
def cli() -> None:
    """Harmony Pillar 2 — Data Ingestion Pipeline CLI."""


@cli.command("read")
@click.argument("manifest_path", type=click.Path(exists=True, readable=True))
@click.option(
    "--sample", default=1, show_default=True,
    help="Number of sample features to print."
)
@click.option(
    "--max-features", default=None, type=int,
    help="Stop after reading this many features (for profiling large sources)."
)
def read_command(manifest_path: str, sample: int, max_features: int | None) -> None:
    """
    Connect to a data source and print feature count + sample geometries.

    MANIFEST_PATH: Path to a YAML dataset manifest file.

    Exit codes:
      0 — source connected and features returned
      1 — configuration error
      2 — connection error
    """
    try:
        manifest = load_manifest(manifest_path)
    except (ManifestError, FileNotFoundError) as exc:
        click.echo(f"ERROR: Failed to load manifest {manifest_path!r}: {exc}", err=True)
        sys.exit(1)

    source_type = manifest.source_type
    click.echo(f"Connecting to source: {source_type} ...")

    try:
        adapter = get_adapter(manifest)
    except (AdapterConfigError, ManifestError) as exc:
        click.echo(f"ERROR: Adapter configuration error: {exc}", err=True)
        sys.exit(1)

    count = 0
    samples: list[dict] = []

    try:
        for feature in adapter.read():
            count += 1
            if len(samples) < sample:
                geom = feature.get("geometry") or {}
                samples.append({
                    "source_id": feature.get("source_id"),
                    "source_crs": feature.get("source_crs"),
                    "geometry_type": geom.get("type"),
                    "property_keys": sorted((feature.get("properties") or {}).keys()),
                })
            if max_features is not None and count >= max_features:
                click.echo(f"  (stopped at --max-features={max_features})")
                break
    except AdapterConnectionError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(2)

    click.echo(f"\nFeature count: {count}")
    click.echo(f"\nSample features ({min(sample, count)} of {count}):")
    for i, s in enumerate(samples, 1):
        click.echo(f"\n  Feature {i}:")
        click.echo(f"    source_id:     {s['source_id']}")
        click.echo(f"    source_crs:    {s['source_crs']}")
        click.echo(f"    geometry_type: {s['geometry_type']}")
        click.echo(f"    properties:    {s['property_keys']}")


@cli.command("health")
@click.option(
    "--pillar1-url", default="http://localhost:8000",
    show_default=True,
    help="Pillar 1 HTTP API base URL."
)
def health_command(pillar1_url: str) -> None:
    """Check that the Pillar 1 HTTP API is reachable."""
    import httpx

    url = f"{pillar1_url.rstrip('/')}/health"
    try:
        resp = httpx.get(url, timeout=10)
        if resp.status_code == 200:
            click.echo(f"Pillar 1 API: OK ({url})")
            click.echo(json.dumps(resp.json(), indent=2))
        else:
            click.echo(
                f"WARNING: Pillar 1 API returned HTTP {resp.status_code} "
                f"at {url}",
                err=True,
            )
            sys.exit(1)
    except httpx.RequestError as exc:
        click.echo(f"ERROR: Cannot reach Pillar 1 API at {url}: {exc}", err=True)
        sys.exit(2)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _geometry_preview(geometry: dict) -> str:
    """Return a compact preview of a geometry for display."""
    geo_type = geometry.get("type", "?")
    coords = geometry.get("coordinates")
    if coords is None:
        return f"{geo_type} (no coordinates)"
    if geo_type == "Point":
        return f"Point({coords[0]:.6f}, {coords[1]:.6f})"
    if geo_type == "LineString" and coords:
        first = coords[0]
        return f"LineString({len(coords)} nodes, first: {first[0]:.6f}, {first[1]:.6f})"
    if geo_type == "Polygon" and coords:
        ring = coords[0]
        return f"Polygon({len(ring)} vertices, first: {ring[0][0]:.6f}, {ring[0][1]:.6f})"
    if geo_type in ("MultiPolygon", "MultiLineString"):
        return f"{geo_type}({len(coords)} parts)"
    return f"{geo_type}(...)"


if __name__ == "__main__":
    cli()
