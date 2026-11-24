'use strict';

(() => {
  const storage = window.SurvieMapStorage;
  const $ = id => document.getElementById(id);
  const dialog = $('offline-map-dialog'), select = $('offline-area'), status = $('offline-map-status');
  const download = $('download-offline-map'), open = $('open-offline-maps'), cancel = $('cancel-offline-map');
  let available = [], saved = [], controller, canStore = false;

  function update() {
    const item = available.find(area => area.id === select.value);
    const copy = saved.find(area => area.id === item?.id);
    download.disabled = !canStore || !item || !!controller || copy?.sha256 === item?.sha256;
    select.disabled = !!controller || !available.length || !canStore;
    download.textContent = copy ? 'Mettre à jour' : 'Télécharger cette zone';
    if (copy?.sha256 === item?.sha256 && copy) download.textContent = 'Zone déjà téléchargée';
    $('offline-area-size').textContent = item ? storage.formatBytes(item.bytes) : '';
    cancel.hidden = !controller;
    open.hidden = !saved.length;
    open.href = storage.VIEWER + (copy ? '?zone=' + encodeURIComponent(copy.id) : '');
  }

  async function ensureViewer() {
    const registration = await navigator.serviceWorker.register(storage.VIEWER + 'sw.js', {updateViaCache: 'none'});
    const worker = registration.installing || registration.waiting || registration.active;
    if (!worker) throw new Error('Le lecteur hors ligne est indisponible.');
    if (worker.state !== 'activated') await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => finish(new Error('La préparation du lecteur a pris trop de temps. Réessayez.')), 30000);
      function finish(error) {
        clearTimeout(timeout);
        worker.removeEventListener('statechange', check);
        if (error) reject(error);
        else resolve();
      }
      function check() {
        if (worker.state === 'activated') finish();
        if (worker.state === 'redundant') finish(new Error('Le lecteur hors ligne n’a pas pu être préparé.'));
      }
      worker.addEventListener('statechange', check);
      check();
    });
    await new Promise((resolve, reject) => {
      const channel = new MessageChannel();
      const timeout = setTimeout(() => finish(false), 30000);
      function finish(ready) {
        clearTimeout(timeout);
        channel.port1.close();
        if (ready) resolve();
        else reject(new Error('Le lecteur hors ligne n’a pas été conservé. Réessayez depuis le réseau de la maison.'));
      }
      channel.port1.onmessage = event => finish(event.data);
      worker.postMessage('prepare-map-viewer', [channel.port2]);
    });
  }

  async function refreshSaved() {
    saved = await storage.areas();
    if (saved.length) await ensureViewer();
  }

  window.MapDownloads = {
    setAreas(items) {
      available = items.filter(item => Number.isSafeInteger(item.bytes) && item.bytes >= 127 && /^[a-f0-9]{64}$/.test(item.sha256));
      select.replaceChildren(...available.map(item => new Option(item.title, item.id)));
      update();
    }
  };

  $('offline-map').onclick = async () => {
    dialog.showModal();
    canStore = storage.supported();
    const active = $('area').value;
    if (available.some(item => item.id === active)) select.value = active;
    status.textContent = '';
    $('offline-https-help').hidden = window.isSecureContext;
    $('offline-https-link').href = 'https://' + location.hostname + ':8443/cartes.html';
    $('offline-map-unavailable').hidden = canStore || !window.isSecureContext;
    $('offline-map-fields').hidden = !canStore;
    update();
    if (!canStore) return;
    try {
      await refreshSaved();
      if (!available.length) status.textContent = 'Aucun fond de carte prêt à télécharger sur le serveur.';
    } catch (_) {
      status.textContent = 'Le navigateur ne peut pas ouvrir le stockage des cartes.';
      canStore = false;
    }
    update();
  };

  select.onchange = () => { status.textContent = ''; update(); };
  $('close-offline-map').onclick = () => dialog.close();
  cancel.onclick = () => controller?.abort();

  download.onclick = async () => {
    const item = available.find(area => area.id === select.value);
    if (!item || controller) return;
    controller = new AbortController();
    const {signal} = controller;
    const progress = $('offline-map-progress');
    progress.hidden = false;
    progress.removeAttribute('value');
    update();
    status.textContent = 'Préparation du lecteur hors ligne…';
    try {
      await ensureViewer();
      signal.throwIfAborted();
      status.textContent = 'Téléchargement en cours. Gardez cet onglet ouvert.';
      await storage.download(item, signal, received => { progress.value = received / item.bytes; });
      saved = await storage.areas();
      status.textContent = 'Carte prête. Ouvrez « Mes cartes téléchargées » et ajoutez la page à vos favoris.';
    } catch (error) {
      status.textContent = signal.aborted ? 'Téléchargement annulé.'
        : error.name === 'QuotaExceededError' ? 'Espace insuffisant dans ce navigateur. Choisissez une zone plus petite.'
        : error instanceof TypeError ? 'Téléchargement interrompu. Vérifiez le réseau de la maison puis réessayez.'
        : error.message || 'La carte n’a pas pu être téléchargée.';
    } finally {
      controller = null;
      progress.hidden = true;
      update();
    }
  };
})();
