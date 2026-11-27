import json
import math
import unittest

from swciv.build import OUT, build, classify, summarise
from swciv.config import load_config
from swciv.hexgrid import SQRT3, Projection, build_grid, hex_area_km2


class HexGridTests(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.spacing = self.cfg["hex_spacing_km"]
        self.cells = build_grid(self.cfg["bbox"], self.spacing)

    def test_centres_inside_bbox_and_unique(self):
        bbox = self.cfg["bbox"]
        self.assertTrue(all(bbox.contains(c.lon, c.lat) for c in self.cells))
        self.assertEqual(len({c.id for c in self.cells}), len(self.cells))

    def test_neighbour_spacing_matches_config(self):
        proj = Projection(*self.cfg["bbox"].centre)
        by_id = {c.id: c for c in self.cells}
        checked = 0
        for c in self.cells:
            for dq, dr in ((1, 0), (0, 1), (-1, 1)):
                n = by_id.get(f"{c.q + dq},{c.r + dr}")
                if n:
                    (x1, y1), (x2, y2) = proj.to_km(c.lon, c.lat), proj.to_km(n.lon, n.lat)
                    self.assertAlmostEqual(math.hypot(x2 - x1, y2 - y1), self.spacing, places=3)
                    checked += 1
        self.assertGreater(checked, 1000)

    def test_cell_count_matches_expected_area(self):
        b, proj = self.cfg["bbox"], Projection(*self.cfg["bbox"].centre)
        (x0, y0), (x1, y1) = proj.to_km(b.west, b.south), proj.to_km(b.east, b.north)
        expected = (x1 - x0) * (y1 - y0) / hex_area_km2(self.spacing)
        self.assertLess(abs(len(self.cells) - expected) / expected, 0.03)

    def test_polygon_is_closed_hexagon(self):
        ring = self.cells[0].ring
        self.assertEqual(len(ring), 7)
        self.assertEqual(ring[0], ring[-1])


class ClassifyTests(unittest.TestCase):
    th = {"plains_max": 100, "hills_max": 250}

    def test_summarise_and_classify(self):
        self.assertEqual(summarise([0, 0, 0]), (0, 0.0))
        self.assertEqual(summarise([0, 10, 30]), (20, 0.67))
        self.assertEqual(classify(0, 0.0, self.th), "sea")
        self.assertEqual(classify(4, 0.14, self.th), "plains")  # coastal hex stays land
        self.assertEqual(classify(180, 1.0, self.th), "hills")
        self.assertEqual(classify(300, 1.0, self.th), "highlands")


class BuildTests(unittest.TestCase):
    def test_build_output_schema(self):
        fc = build()
        self.assertEqual(fc["type"], "FeatureCollection")
        self.assertGreater(len(fc["features"]), 1000)
        names = {f["properties"].get("place") for f in fc["features"]}
        for town in ("Busselton", "Margaret River", "Bunbury", "Dunsborough"):
            self.assertIn(town, names)
        for f in fc["features"]:
            self.assertIn(f["properties"]["terrain"], {"sea", "plains", "hills", "highlands"})


if __name__ == "__main__":
    unittest.main()
