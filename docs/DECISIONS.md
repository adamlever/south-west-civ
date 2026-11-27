# Decisions log

| Date | Decision | Why |
|---|---|---|
| 2026-11-27 | Python standard library only | Zero setup, easy for anyone to run. Add geopandas/shapely at milestone 1 when polygons need overlay maths. |
| 2026-11-27 | 5 km hexes, pointy-top | Separates the Capes towns, about 1,800 hexes, plays well in a browser. |
| 2026-11-27 | Commit `data/raw` and `grid.geojson` | Both are small (under 1 MB), so the repo builds and views offline and results are reproducible. |
| 2026-11-27 | 7 elevation samples per hex | One centre pixel misclassifies coastal hexes as sea. |
| 2026-11-27 | No Civ values until real sources are wired in | Never fabricate data. |
| 2026-11-27 | Private repo, no Pages | Free-plan Pages needs a public repo. |
