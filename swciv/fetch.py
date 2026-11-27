"""Download the raw open data used by the build and cache it under data/raw/.

Run `make fetch` only when refreshing; `make build` works offline from the cache.

Sources
- Elevation: Open-Meteo Elevation API (Copernicus DEM GLO-90, CC BY 4.0).
  Sea reads as 0 m.
- Places: OpenStreetMap via Overpass API (ODbL).
"""
from __future__ import annotations

import datetime as dt
import json
import time
import urllib.parse
import urllib.request

from .config import ROOT, load_config
from .hexgrid import build_grid, sample_points

RAW = ROOT / "data" / "raw"
UA = "south-west-civ/0.1 (https://github.com/adamlever/south-west-civ)"
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"
BATCH = 100  # Open-Meteo's per-request coordinate limit


def _get(url: str, data: bytes | None = None, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _retry(fn, attempts: int = 4):
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # network flakiness is expected
            if i == attempts - 1:
                raise
            print(f"  retry after error: {exc}")
            time.sleep(2 * (i + 1))


def fetch_elevation(cfg: dict) -> None:
    bbox, spacing = cfg["bbox"], cfg["hex_spacing_km"]
    cells = build_grid(bbox, spacing)
    points = [(c.id, lon, lat) for c in cells for lon, lat in sample_points(c, bbox, spacing)]
    values: list[float] = []
    for i in range(0, len(points), BATCH):
        chunk = points[i:i + BATCH]
        qs = urllib.parse.urlencode({
            "latitude": ",".join(f"{lat:.5f}" for _, _, lat in chunk),
            "longitude": ",".join(f"{lon:.5f}" for _, lon, _ in chunk),
        })
        body = json.loads(_retry(lambda: _get(f"{ELEVATION_URL}?{qs}")))
        values.extend(body["elevation"])
        print(f"  elevation {len(values)}/{len(points)}", flush=True)
        time.sleep(0.3)
    out: dict[str, list[float]] = {}
    for (cid, _, _), v in zip(points, values):
        out.setdefault(cid, []).append(v)
    payload = {
        "source": "Open-Meteo Elevation API (Copernicus DEM GLO-90), CC BY 4.0",
        "fetched": dt.date.today().isoformat(),
        "spacing_km": spacing,
        "samples_per_cell": "centre + 6 points at 0.6 x radius toward each corner",
        "elevation_m_by_cell": out,
    }
    (RAW / "elevation.json").write_text(json.dumps(payload, separators=(",", ":")))


def fetch_places(cfg: dict) -> None:
    b = cfg["bbox"]
    types = "|".join(cfg["town_place_types"])
    query = (f'[out:json][timeout:60];node["place"~"^({types})$"]'
             f'({b.south},{b.west},{b.north},{b.east});out;')
    data = urllib.parse.urlencode({"data": query}).encode()
    last = None
    for url in OVERPASS_ENDPOINTS:
        try:
            body = json.loads(_retry(lambda: _get(url, data, timeout=60), attempts=2))
            break
        except Exception as exc:
            last = exc
            print(f"  {url} failed: {exc}")
    else:
        raise RuntimeError(f"all Overpass endpoints failed: {last}")
    places = [
        {"osm_id": e["id"], "name": e["tags"].get("name"), "place": e["tags"]["place"],
         "lon": e["lon"], "lat": e["lat"]}
        for e in body["elements"] if e.get("tags", {}).get("name")
    ]
    places.sort(key=lambda p: (p["place"], p["name"]))
    payload = {
        "source": "OpenStreetMap contributors via Overpass API, ODbL",
        "fetched": dt.date.today().isoformat(),
        "places": places,
    }
    (RAW / "places.json").write_text(json.dumps(payload, indent=1))


def main(argv: list[str] | None = None) -> None:
    import sys
    what = (argv if argv is not None else sys.argv[1:]) or ["places", "elevation"]
    RAW.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    if "places" in what:
        print("Fetching places...")
        fetch_places(cfg)
    if "elevation" in what:
        print("Fetching elevation...")
        fetch_elevation(cfg)


if __name__ == "__main__":
    main()
