"""Build site/data/grid.geojson from the config and the cached raw data.

Per-cell properties (all real, derived data; nothing is simulated):
  id, q, r        axial hex coordinates
  lon, lat        hex centre
  elev_m          mean Copernicus DEM elevation of the hex's land samples (m)
  land_frac       share of 7 sample points above 0 m (0 = open sea)
  terrain         sea | plains | hills | highlands from elev_m and land_frac
                  (thresholds in config; a simple heuristic, NOT an official
                  classification)
  place, place_type  highest-ranked OSM place inside the hex, if any
Civ-style values (gold, districts, citizens) are NOT here yet: see ROADMAP.
"""
from __future__ import annotations

import json
import math

from .config import ROOT, load_config
from .hexgrid import SQRT3, Projection, build_grid

RAW = ROOT / "data" / "raw"
OUT = ROOT / "site" / "data" / "grid.geojson"
PLACE_RANK = {"city": 0, "town": 1, "village": 2}


def summarise(samples: list[float] | None) -> tuple[float | None, float | None]:
    """(mean land elevation, land fraction) from a cell's sample elevations."""
    if not samples:
        return None, None
    land = [v for v in samples if v > 0]
    mean = round(sum(land) / len(land)) if land else 0
    return mean, round(len(land) / len(samples), 2)


def classify(elev_m: float | None, land_frac: float | None, th: dict) -> str:
    if elev_m is None:
        return "unknown"
    if land_frac == 0:
        return "sea"
    if elev_m <= th["plains_max"]:
        return "plains"
    if elev_m <= th["hills_max"]:
        return "hills"
    return "highlands"


def assign_places(cells, places, spacing_km, proj):
    """Give each place to the hex containing it (= the nearest hex centre).

    Where several places share a hex, the highest-ranked (city > town > village)
    wins, then the first alphabetically.
    """
    row_step = 1.5 * spacing_km / SQRT3
    best: dict[str, dict] = {}
    for p in sorted(places, key=lambda p: (PLACE_RANK[p["place"]], p["name"])):
        px, py = proj.to_km(p["lon"], p["lat"])
        r0 = round(py / row_step)
        nearest = None
        for r in range(r0 - 1, r0 + 2):
            q0 = round(px / spacing_km - r / 2)
            for q in range(q0 - 1, q0 + 2):
                d = math.hypot(px - spacing_km * (q + r / 2), py - r * row_step)
                if nearest is None or d < nearest[0]:
                    nearest = (d, f"{q},{r}")
        if nearest[1] in cells:
            best.setdefault(nearest[1], p)
    return best


def build() -> dict:
    cfg = load_config()
    bbox, spacing = cfg["bbox"], cfg["hex_spacing_km"]
    cells = build_grid(bbox, spacing)
    by_id = {c.id: c for c in cells}
    elev = json.loads((RAW / "elevation.json").read_text())
    places = json.loads((RAW / "places.json").read_text())["places"]
    proj = Projection(*bbox.centre)
    placed = assign_places(by_id, places, spacing, proj)

    features = []
    for c in cells:
        e, land = summarise(elev["elevation_m_by_cell"].get(c.id))
        props = {"id": c.id, "q": c.q, "r": c.r, "elev_m": e, "land_frac": land,
                 "terrain": classify(e, land, cfg["terrain_thresholds_m"]),
                 "lon": round(c.lon, 5), "lat": round(c.lat, 5)}
        if c.id in placed:
            props["place"] = placed[c.id]["name"]
            props["place_type"] = placed[c.id]["place"]
        features.append({"type": "Feature", "properties": props,
                         "geometry": {"type": "Polygon", "coordinates": [[[round(x, 5), round(y, 5)] for x, y in c.ring]]}})
    return {
        "type": "FeatureCollection",
        "metadata": {
            "region": cfg["name"], "hex_spacing_km": spacing,
            "bbox": [bbox.west, bbox.south, bbox.east, bbox.north],
            "sources": [elev["source"], json.loads((RAW / "places.json").read_text())["source"]],
            "note": "Elevation and places are real open data. No Civ values yet (milestone 1+).",
        },
        "features": features,
    }


def main() -> None:
    fc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fc, separators=(",", ":")))
    n = len(fc["features"])
    placed = sum("place" in f["properties"] for f in fc["features"])
    print(f"Wrote {OUT.relative_to(ROOT)}: {n} hexes, {placed} with a place, {OUT.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
