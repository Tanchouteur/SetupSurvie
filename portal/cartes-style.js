'use strict';
window.survieMapStyle = (item, archiveUrl) => ({
  version: 8,
  glyphs: location.origin + '/vendor/maps/fonts/{fontstack}/{range}.pbf',
  sources: {local: {type: 'vector', url: 'pmtiles://' + archiveUrl, attribution: item.attribution}},
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
