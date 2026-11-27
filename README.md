# South West Civ

An Australian take on [Andrej Karpathy's US Civ map](https://karpathy.ai/usaciv/): real public data translated into Civilization terms on a hex grid. This one starts in **South West WA** (Capes, Busselton, Augusta-Margaret River, Bunbury and the wider south-west corner), with room to scale to WA, then Australia.

> **Status: milestone 0.** A working hex grid, one real layer (elevation) and real place names, in a static viewer. There are **no Civ values yet** (gold, districts, citizens). Nothing in the repo is simulated or made up.

## Vision

Every hex tells a true story about the place it covers. Gold is the local economy, districts are what a town really does for a living, citizens are its workers, and wonders are chosen by published rules, not vibes. Lenses (terrain, economy, fire risk, tourism) and "advisors" explain what the data says.

## Civ-to-data mapping (plan)

| Civ concept | Real-world source | Status |
|---|---|---|
| Terrain (plains, hills, highlands, sea) | Copernicus DEM elevation | **Done (heuristic)** |
| Cities | OpenStreetMap place nodes (city, town, village) | **Done** (names only) |
| Citizens | ABS Census workforce by place of work (SA2/SA1) | Planned |
| Districts | Local industry mix (ANZSIC industry of employment), top specialisations per city | Planned |
| Gold | Estimated local output from jobs x industry value-added. ABS publishes GDP by state only, so this is an estimate and will be labelled as one | Planned |
| Production / power | AEMO generators and Geoscience Australia mines | Planned |
| Culture / wonders | Parks (CAPAD), tourism visitors, heritage sites, chosen by published rules | Planned |
| Hazards | DBCA fire history, BoM climate | Planned |

## Data sources

Verified to exist at the time of writing. Check each licence before reuse.

| Source | Use | Link |
|---|---|---|
| **Used now:** Copernicus DEM GLO-90, via Open-Meteo Elevation API (CC BY 4.0) | Elevation | [open-meteo.com/en/docs/elevation-api](https://open-meteo.com/en/docs/elevation-api) |
| **Used now:** OpenStreetMap contributors, via Overpass API (ODbL) | Place names | [openstreetmap.org/copyright](https://www.openstreetmap.org/copyright) |
| ABS Census DataPacks | Population, workforce, industry | [abs.gov.au/census/find-census-data/datapacks](https://www.abs.gov.au/census/find-census-data/datapacks) |
| ABS ASGS Edition 3 boundaries | SA1/SA2/LGA polygons to aggregate onto hexes | [abs.gov.au ... asgs-edition-3](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026) |
| ABS Data by Region and Regional Population | Regional economy and population series | [dbr.abs.gov.au](https://dbr.abs.gov.au/), [regional population](https://www.abs.gov.au/statistics/people/population/regional-population) |
| ABS Data API | Programmatic ABS access | [data api guide](https://www.abs.gov.au/about/data-services/application-programming-interfaces-apis/data-api-user-guide) |
| Jobs and Skills Australia | Labour market and industry data | [jobsandskills.gov.au/data](https://www.jobsandskills.gov.au/data) |
| Geoscience Australia | Elevation (national DEMs) and mineral resources | [elevation](https://www.ga.gov.au/scientific-topics/national-location-information/digital-elevation-data), [FSDF elevation](https://elevation.fsdf.org.au/), [minerals](https://www.ga.gov.au/scientific-topics/minerals) |
| Bureau of Meteorology | Climate data | [bom.gov.au/climate/data-services](https://www.bom.gov.au/climate/data-services/) |
| AEMO | Generator locations (generation information, SWIS and NEM) | [aemo.com.au](https://www.aemo.com.au/) |
| CAPAD (DCCEEW) | Protected areas and national parks | [dcceew.gov.au ... capad](https://www.dcceew.gov.au/environment/land/nrs/science/capad) |
| DBCA Fire History (DBCA-060) | Historic fire footprints | [data.wa.gov.au dataset](https://catalogue.data.wa.gov.au/dataset/dbca-fire-history) |
| WA open data catalogue | Many WA government datasets | [catalogue.data.wa.gov.au](https://catalogue.data.wa.gov.au/) |
| Landgate SLIP | WA spatial layers (cadastre, roads, etc.) | [landgate.wa.gov.au ... slip](https://www.landgate.wa.gov.au/location-data-and-services/programs-and-initiatives/slip/) |
| Tourism WA research | Visitor data | [tourism.wa.gov.au research](https://www.tourism.wa.gov.au/Markets-and-research/Pages/Tourism-research.aspx) |

Note: the elevation API is a free, rate-limited service. For production-scale work, switch to the Geoscience Australia DEM downloads.

## Architecture

```
config/region.json   region bbox, hex size, terrain thresholds
swciv/hexgrid.py     pointy-top hex maths, local projection, sample points
swciv/fetch.py       slow, networked: APIs -> data/raw/*.json (committed cache)
swciv/build.py       fast, offline: config + raw -> site/data/grid.geojson
site/                static Leaflet viewer (no build step)
tests/               stdlib unittest
```

Pipeline: `fetch` (rarely) then `build` (always offline and reproducible) then the viewer reads one GeoJSON file. Python standard library only, so there is nothing to install.

**Hex size: 5 km centre to centre (about 21.7 km² per hex).** Karpathy uses 25 km for a whole country. The SW corner is about 165 x 235 km, and 5 km gives about 1,800 hexes: fine enough that Busselton, Dunsborough, Margaret River and Augusta land in separate hexes, coarse enough to stay light in a browser and to estimate from SA2-level census data. Change `hex_spacing_km` in the config to try another size (then re-run `make fetch`).

Each hex samples elevation at 7 points (centre plus six), because a single centre pixel puts coastal towns like Bunbury in the sea. Terrain is a simple height heuristic (plains up to 100 m, hills up to 250 m, then highlands), not an official classification. Projection is local equirectangular (about 1.5% error across the region); move to an equal-area CRS when the region grows.

## Run it

Needs Python 3.10+ and nothing else.

```sh
make test     # unit tests
make build    # rebuild site/data/grid.geojson from the cached data (offline)
make serve    # open http://localhost:8000
make fetch    # optional: refresh data/raw from the live APIs (slow)
```

GitHub Pages would work for `site/` once the repo is public (or on a paid plan).

## Roadmap

| # | Milestone | State |
|---|---|---|
| 0 | Hex grid, config, elevation and places, static viewer, tests | **This commit** |
| 1 | Download ASGS boundaries and Census DataPacks, aggregate population and jobs onto hexes (areal weighting) | Next |
| 2 | Citizens and districts from industry-of-employment; city detail panel | |
| 3 | Gold estimate, with method and caveats shown in the UI | |
| 4 | Land layers: CAPAD parks, DBCA fire history, AEMO generators, mines | |
| 5 | Wonders by published rules, plus lenses and advisors | |
| 6 | Scale to all of WA (coarser hexes at low zoom), then Australia | |

## Licence and attribution

Code: MIT (see `LICENSE`). Data keeps its own licences: elevation from Copernicus DEM via Open-Meteo (CC BY 4.0), places © OpenStreetMap contributors (ODbL). Base map tiles © OpenStreetMap contributors. Future ABS, Geoscience Australia and WA government data will carry their own CC BY terms and be credited here. Not affiliated with Karpathy or the Civilization franchise.
