'use strict';

(async () => {
  const storage = window.SurvieMapStorage;
  const $ = id => document.getElementById(id);
  const select = $('saved-area'), status = $('status'), remove = $('remove-area');
  let db, map, saved = [], request = 0;

  async function loadAreas(preferred) {
    saved = await storage.areas();
    select.replaceChildren(...saved.map(area => new Option(area.title, area.id)));
    if (saved.some(area => area.id === preferred)) select.value = preferred;
    $('controls').hidden = !saved.length;
    await showArea();
  }

  async function showArea() {
    const ticket = ++request;
    const area = saved.find(item => item.id === select.value);
    map?.remove();
    map = null;
    $('map').hidden = true;
    delete $('map').dataset.ready;
    if (!area) {
      status.textContent = 'Aucune carte dans ce navigateur. Reconnectez-vous au serveur pour télécharger une zone.';
      return;
    }
    status.textContent = 'Ouverture du fond de carte…';
    try {
      const protocol = new pmtiles.Protocol();
      maplibregl.addProtocol('pmtiles', protocol.tile);
      const source = storage.source(db, area);
      const archive = new pmtiles.PMTiles(source);
      protocol.add(archive);
      await archive.getHeader();
      if (ticket !== request) return;
      const size = storage.formatBytes(area.bytes);
      $('map').hidden = false;
      map = new maplibregl.Map({
        container: 'map', style: window.survieMapStyle(area, source.getKey()),
        center: area.center, bounds: area.bbox, fitBoundsOptions: {padding: 24, maxZoom: 15},
        maxZoom: 18, maxTileCacheSize: 48
      });
      map.addControl(new maplibregl.NavigationControl(), 'top-right');
      map.addControl(new maplibregl.ScaleControl({unit: 'metric'}));
      map.once('idle', () => { $('map').dataset.ready = 'true'; });
      map.on('error', () => {
        status.textContent = 'Certaines données de la carte sont illisibles. Réessayez ou téléchargez à nouveau cette zone.';
      });
      status.textContent = 'Disponible sans le serveur · ' + size + (area.edition ? ' · données du ' + area.edition : '');
    } catch (_) {
      if (ticket !== request) return;
      status.textContent = 'Cette carte ne peut pas s’afficher dans ce navigateur. Essayez de rouvrir la page ou de télécharger à nouveau la zone.';
    }
  }

  try {
    db = await storage.openDatabase();
    select.onchange = showArea;
    remove.onclick = async () => {
      const area = saved.find(item => item.id === select.value);
      if (!area || !confirm('Supprimer « ' + area.title + ' » de ce navigateur ?')) return;
      remove.disabled = true;
      select.disabled = true;
      try {
        await storage.remove(area);
        await loadAreas();
      } catch (error) {
        status.textContent = error.message || 'La carte n’a pas pu être supprimée.';
      } finally {
        remove.disabled = false;
        select.disabled = false;
      }
    };
    await loadAreas(new URLSearchParams(location.search).get('zone'));
  } catch (_) {
    status.textContent = 'Le navigateur ne peut pas lire le stockage des cartes.';
  }
})();
