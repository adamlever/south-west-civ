// Minimal viewer: loads data/grid.geojson (built by `make build`) and draws it with Leaflet.
const TERRAIN = {
  sea: '#a8cde8', plains: '#b9d98b', hills: '#d9c27a', highlands: '#a9825a', unknown: '#cccccc',
};
const ELEV_STOPS = [[0, '#d7ecb0'], [50, '#a8d18d'], [100, '#e3d58a'], [200, '#c9965b'], [300, '#8c5a3a']];

function elevColour(e) {
  if (e === null || e === undefined) return TERRAIN.unknown;
  let c = ELEV_STOPS[0][1];
  for (const [limit, colour] of ELEV_STOPS) if (e >= limit) c = colour;
  return c;
}

const map = L.map('map');
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 17,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);

let layerMode = 'terrain';
let gridLayer, placeLayer;

const style = (f) => ({
  weight: 0.6, color: '#fff', fillOpacity: 0.62,
  fillColor: layerMode === 'terrain'
    ? TERRAIN[f.properties.terrain]
    : (f.properties.terrain === 'sea' ? TERRAIN.sea : elevColour(f.properties.elev_m)),
});

function legend() {
  const items = layerMode === 'terrain'
    ? Object.entries(TERRAIN).filter(([k]) => k !== 'unknown')
    : [['sea', TERRAIN.sea], ...ELEV_STOPS.map(([m, c]) => [`${m}+ m`, c])];
  document.getElementById('legend').innerHTML = items
    .map(([k, c]) => `<div><span class="swatch" style="background:${c}"></span>${k}</div>`).join('');
}

fetch('data/grid.geojson').then((r) => r.json()).then((fc) => {
  const m = fc.metadata;
  document.getElementById('meta').textContent =
    `${fc.features.length} hexes, ${m.hex_spacing_km} km spacing. Data: ${m.sources.join('; ')}.`;
  gridLayer = L.geoJSON(fc, {
    style,
    onEachFeature: (f, layer) => {
      const p = f.properties;
      layer.bindTooltip(
        `<b>${p.place || 'Hex ' + p.id}</b>${p.place ? ' (' + p.place_type + ')' : ''}<br>` +
        `${p.terrain}, mean land elevation ${p.elev_m} m, ${Math.round(p.land_frac * 100)}% land`);
    },
  }).addTo(map);
  placeLayer = L.layerGroup(fc.features.filter((f) => f.properties.place).map((f) => {
    return L.marker([f.properties.lat, f.properties.lon], { interactive: false, icon: L.divIcon({
      className: 'place-label', html: f.properties.place, iconSize: [0, 0] }) });
  })).addTo(map);
  map.fitBounds(gridLayer.getBounds());
  legend();
});

document.querySelectorAll('input[name=layer]').forEach((el) => el.addEventListener('change', (e) => {
  layerMode = e.target.value;
  if (gridLayer) gridLayer.setStyle(style);
  legend();
}));
document.getElementById('places').addEventListener('change', (e) => {
  if (!placeLayer) return;
  e.target.checked ? placeLayer.addTo(map) : map.removeLayer(placeLayer);
});
