PY ?= python3

.PHONY: build test fetch serve all
all: test build

build:   ## cached raw data -> site/data/grid.geojson (offline)
	$(PY) -m swciv.build

test:    ## stdlib unittest, no dependencies
	$(PY) -m unittest discover -s tests -v

fetch:   ## refresh data/raw from the live APIs (slow; needs internet)
	$(PY) -m swciv.fetch

serve:   ## viewer at http://localhost:8000
	$(PY) -m http.server 8000 --directory site
