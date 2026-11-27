"""Pointy-top hex grid over a lon/lat bounding box.

Projection: local equirectangular, scaled by cos(mid-latitude). Across the
~2 degree SW WA box the east-west scale error is about +/-1.5%, which is fine
for a 5 km game grid. Swap in an equal-area CRS (e.g. EPSG:3577) when we scale
to all of WA or Australia.

`spacing_km` is the centre-to-centre distance between neighbouring hexes.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

EARTH_RADIUS_KM = 6371.0088
KM_PER_DEG_LAT = math.pi * EARTH_RADIUS_KM / 180.0
SQRT3 = math.sqrt(3.0)


@dataclass(frozen=True)
class Bbox:
    west: float
    south: float
    east: float
    north: float

    def contains(self, lon: float, lat: float) -> bool:
        return self.west <= lon <= self.east and self.south <= lat <= self.north

    @property
    def centre(self) -> tuple[float, float]:
        return (self.west + self.east) / 2, (self.south + self.north) / 2


class Projection:
    """Local km <-> lon/lat, origin at the bbox centre."""

    def __init__(self, lon0: float, lat0: float):
        self.lon0, self.lat0 = lon0, lat0
        self.km_per_deg_lon = KM_PER_DEG_LAT * math.cos(math.radians(lat0))

    def to_km(self, lon: float, lat: float) -> tuple[float, float]:
        return ((lon - self.lon0) * self.km_per_deg_lon, (lat - self.lat0) * KM_PER_DEG_LAT)

    def to_lonlat(self, x: float, y: float) -> tuple[float, float]:
        return (self.lon0 + x / self.km_per_deg_lon, self.lat0 + y / KM_PER_DEG_LAT)


@dataclass(frozen=True)
class Hex:
    q: int
    r: int
    lon: float
    lat: float
    ring: list  # closed [lon, lat] polygon ring

    @property
    def id(self) -> str:
        return f"{self.q},{self.r}"


def hex_corners_km(cx: float, cy: float, radius_km: float) -> list[tuple[float, float]]:
    return [
        (cx + radius_km * math.cos(math.radians(60 * i - 30)),
         cy + radius_km * math.sin(math.radians(60 * i - 30)))
        for i in range(6)
    ]


def build_grid(bbox: Bbox, spacing_km: float) -> list[Hex]:
    """Return every hex whose centre lies inside `bbox`."""
    proj = Projection(*bbox.centre)
    radius = spacing_km / SQRT3          # centre-to-corner
    row_step = 1.5 * radius
    x_min, y_min = proj.to_km(bbox.west, bbox.south)
    x_max, y_max = proj.to_km(bbox.east, bbox.north)

    cells: list[Hex] = []
    r_lo, r_hi = math.floor(y_min / row_step) - 1, math.ceil(y_max / row_step) + 1
    for r in range(r_lo, r_hi + 1):
        y = r * row_step
        q_lo = math.floor(x_min / spacing_km - r / 2) - 1
        q_hi = math.ceil(x_max / spacing_km - r / 2) + 1
        for q in range(q_lo, q_hi + 1):
            x = spacing_km * (q + r / 2)
            lon, lat = proj.to_lonlat(x, y)
            if not bbox.contains(lon, lat):
                continue
            ring = [list(proj.to_lonlat(px, py)) for px, py in hex_corners_km(x, y, radius)]
            ring.append(ring[0])
            cells.append(Hex(q, r, lon, lat, ring))
    return cells


def hex_area_km2(spacing_km: float) -> float:
    return SQRT3 / 2 * spacing_km ** 2


def sample_points(cell: Hex, bbox: Bbox, spacing_km: float, frac: float = 0.6) -> list[tuple[float, float]]:
    """Seven (lon, lat) sample points per hex: the centre plus six points at
    `frac` of the way to each corner. Used to estimate land share and mean
    elevation instead of trusting one pixel."""
    proj = Projection(*bbox.centre)
    radius = spacing_km / SQRT3
    cx, cy = proj.to_km(cell.lon, cell.lat)
    pts = [(cell.lon, cell.lat)]
    pts += [proj.to_lonlat(x, y) for x, y in hex_corners_km(cx, cy, radius * frac)]
    return pts
