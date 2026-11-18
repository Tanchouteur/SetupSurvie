'use strict';

importScripts('storage.js');

// Change this version when changing the offline reader and its assets.
const VERSION = '1';
const VIEWER = '/cartes-hors-ligne/';
const ASSETS = [
  VIEWER,
  VIEWER + 'viewer.css',
  VIEWER + 'viewer.js',
  VIEWER + 'storage.js',
  '/cartes-style.js?v=0.50.0',
  '/vendor/maps/maplibre-gl.css',
  '/vendor/maps/maplibre-gl.js',
  '/vendor/maps/pmtiles.js',
  '/vendor/maps/fonts/Noto%20Sans%20Regular/0-255.pbf',
  '/vendor/maps/fonts/Noto%20Sans%20Regular/256-511.pbf',
  '/vendor/maps/fonts/Noto%20Sans%20Regular/8192-8447.pbf'
];

self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));

self.addEventListener('message', event => {
  const channel = event.ports[0];
  if (event.data !== 'prepare-map-viewer' || !channel) return;
  event.waitUntil((async () => {
    try {
      await SurvieMapStorage.saveViewer(VERSION, ASSETS);
      channel.postMessage(true);
    } catch (_) {
      channel.postMessage(false);
    }
  })());
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  const asset = event.request.mode === 'navigate' && [VIEWER, VIEWER + 'index.html'].includes(url.pathname)
    ? VIEWER : url.pathname + url.search;
  if (!ASSETS.includes(asset)) return;
  event.respondWith((async () => {
    try {
      const blob = await SurvieMapStorage.viewerAsset(VERSION, asset);
      if (blob) return new Response(blob);
    } catch (_) {}
    return fetch(event.request);
  })());
});
