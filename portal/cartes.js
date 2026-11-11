'use strict';
(async () => {
  const status = document.getElementById('status');
  const select = document.getElementById('area');
  const home = document.getElementById('home');
  document.getElementById('print').addEventListener('click', () => window.print());
  try {
    const response = await fetch('/api/maps');
    if (!response.ok) throw new Error('Le service des cartes ne répond pas.');
    const {maps} = await response.json();
    if (!maps.length) throw new Error('Aucune carte terminée sur cet appareil. Le téléchargement doit être préparé par un administrateur.');
    const protocol = new pmtiles.Protocol();
    maplibregl.addProtocol('pmtiles', protocol.tile);
    select.replaceChildren(...maps.map(item => new Option(item.title, item.id)));
    let current = maps.find(m => m.id === 'sollies') || maps[0];
    select.value = current.id;
    const style = item => ({
      version: 8,
      glyphs: location.origin + '/vendor/maps/fonts/{fontstack}/{range}.pbf',
      sources: {local: {type: 'vector', url: 'pmtiles://' + location.origin + item.url, attribution: item.attribution}},
      layers: [
        {id: 'background', type: 'background', paint: {'background-color': '#f1efdf'}},
        {id: 'earth', type: 'fill', source: 'local', 'source-layer': 'earth', paint: {'fill-color': '#f1efdf'}},
        {id: 'landcover', type: 'fill', source: 'local', 'source-layer': 'landcover', paint: {'fill-color': '#d2dfbd', 'fill-opacity': 0.6}},
        {id: 'landuse', type: 'fill', source: 'local', 'source-layer': 'landuse', paint: {'fill-color': '#c4d5b0', 'fill-opacity': 0.55}},
        {id: 'water', type: 'fill', source: 'local', 'source-layer': 'water', filter: ['==', ['geometry-type'], 'Polygon'], paint: {'fill-color': '#a6cdda'}},
        {id: 'rivers', type: 'line', source: 'local', 'source-layer': 'water', filter: ['==', ['geometry-type'], 'LineString'], paint: {'line-color': '#76afc6', 'line-width': 1}},
        {id: 'boundaries', type: 'line', source: 'local', 'source-layer': 'boundaries', paint: {'line-color': '#9c9690', 'line-width': 1, 'line-dasharray': [3, 3]}},
        {id: 'buildings', type: 'fill', source: 'local', 'source-layer': 'buildings', minzoom: 12, paint: {'fill-color': '#c8b9a9'}},
        {id: 'roads-outline', type: 'line', source: 'local', 'source-layer': 'roads', paint: {'line-color': '#c2b7a1', 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.8, 15, 5]}},
        {id: 'roads', type: 'line', source: 'local', 'source-layer': 'roads', paint: {'line-color': ['match', ['get', 'kind'], 'highway', '#edc578', 'major_road', '#f2db9c', 'path', '#b7a27b', '#ffffff'], 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.4, 15, 3]}},
        {id: 'road-names', type: 'symbol', source: 'local', 'source-layer': 'roads', minzoom: 12, layout: {'symbol-placement': 'line', 'text-field': ['coalesce', ['get', 'name:fr'], ['get', 'name'], ''], 'text-font': ['Noto Sans Regular'], 'text-size': 11}, paint: {'text-color': '#64574b', 'text-halo-color': '#fff', 'text-halo-width': 1}},
        {id: 'places', type: 'symbol', source: 'local', 'source-layer': 'places', layout: {'text-field': ['coalesce', ['get', 'name:fr'], ['get', 'name'], ''], 'text-font': ['Noto Sans Regular'], 'text-size': ['interpolate', ['linear'], ['zoom'], 5, 11, 13, 15]}, paint: {'text-color': '#29463e', 'text-halo-color': '#fff', 'text-halo-width': 1.5}}
      ]
    });
    const map = new maplibregl.Map({container: 'map', style: style(current), center: current.center, zoom: 12, maxZoom: 18, preserveDrawingBuffer: true});
    map.setMaxBounds([[current.bbox[0], current.bbox[1]], [current.bbox[2], current.bbox[3]]]);
    map.on('idle', () => {document.getElementById('map').dataset.ready = 'true';});
    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(new maplibregl.ScaleControl({unit: 'metric'}));
    const showStatus = () => { status.textContent = current.title + ' · données du ' + current.edition + ' · détail jusqu’au zoom ' + current.maxzoom + '. Fonctionne sans Internet.'; };
    map.on('load', showStatus);
    map.on('error', event => {status.textContent = 'Certaines données de la carte ne sont pas disponibles à cet endroit. Revenez dans la zone sélectionnée.'; console.warn(event.error);});
    select.addEventListener('change', () => {
      current = maps.find(m => m.id === select.value);
      map.setStyle(style(current));
      map.setMaxBounds([[current.bbox[0], current.bbox[1]], [current.bbox[2], current.bbox[3]]]);
      map.fitBounds([[current.bbox[0], current.bbox[1]], [current.bbox[2], current.bbox[3]]], {padding: 24});
      showStatus();
    });
    home.addEventListener('click', () => {
      current = maps.find(m => m.id === 'sollies') || maps[0]; select.value = current.id;
      map.setStyle(style(current));
      map.setMaxBounds([[current.bbox[0], current.bbox[1]], [current.bbox[2], current.bbox[3]]]);
      map.jumpTo({center: current.center, zoom: 13}); showStatus();
    });
    select.disabled = false; home.disabled = false;
  } catch (error) {status.textContent = error.message || 'Impossible d’ouvrir les cartes. Revenez à la bibliothèque et réessayez.';}
})();
