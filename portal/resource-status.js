/* Portal: consume the existing refresh. Map: read-only refresh when visible on desktop. */
(() => {
  const mapHeader = document.querySelector('.map-site-nav');
  const container = mapHeader || document.getElementById('main-navigation');
  if (!container) return;
  const link = document.createElement('a'); link.className = 'resource-status';
  link.href = (mapHeader ? '/nouveau/' : '') + '#/appareil/ensemble';
  if (!mapHeader) link.dataset.route = 'appareil/ensemble';
  container.append(link);
  function show(text, stale = false) {
    link.textContent = text; link.title = text; link.dataset.stale = String(stale);
  }
  const validMemory = item => item && Number.isFinite(item.used) && item.used >= 0 && Number.isFinite(item.total) && item.total > 0 && item.used <= item.total;
  const size = bytes => (bytes / 1024 ** 3).toLocaleString('fr-FR', {maximumFractionDigits:1});
  const memory = item => validMemory(item) ? size(item.used) + '/' + size(item.total) + ' Go' : '–';
  function display(data) {
    if (!data || data.observation_error) { show('Mesures non actualisées', true); return; }
    let model = 'état indisponible';
    if (data.control_available && data.models_available !== false && Array.isArray(data.models)) {
      const names = data.models.map(m => m && m.name).filter(name => typeof name === 'string' && name.trim());
      model = data.models.length === 0 ? 'aucun modèle signalé' : names.length === data.models.length ? names.join(', ') : 'état indisponible';
    }
    const gpus = data.gpus;
    const gpu = Array.isArray(gpus) && gpus.length && gpus.every(validMemory)
      ? {used:gpus.reduce((sum,g) => sum + g.used,0),total:gpus.reduce((sum,g) => sum + g.total,0)} : null;
    show('IA : ' + model + ' · RAM ' + memory(data.memory) + ' · VRAM ' + memory(gpu));
  }
  show('Mesures non actualisées', true);
  if (!mapHeader) {
    document.addEventListener('survie:inference', event => display(event.detail));
    if (typeof S !== 'undefined' && S.inference) display(S.inference);
    return;
  }
  const desktop = matchMedia('(min-width: 1001px) and (min-height: 501px)');
  let timer = null, controller = null, generation = 0;
  async function refresh() {
    if (!desktop.matches || document.hidden || controller) return;
    const current = ++generation; controller = new AbortController();
    const timeout=setTimeout(()=>controller?.abort(),6000);
    try {
      const response = await fetch('/api/inference', {credentials:'same-origin', signal:controller.signal});
      if (!response.ok) throw new Error('inference unavailable');
      const data = await response.json();
      if (current === generation && desktop.matches && !document.hidden) display(data);
    } catch (_) { if (current === generation) show('Mesures non actualisées', true); }
    finally {
      clearTimeout(timeout);
      if (current === generation) { controller = null; if (desktop.matches && !document.hidden) timer = setTimeout(refresh, 15000); }
    }
  }
  function visibility() {
    clearTimeout(timer); generation++; if (controller) controller.abort(); controller = null;
    if (desktop.matches && !document.hidden) refresh();
  }
  desktop.addEventListener('change', visibility); document.addEventListener('visibilitychange', visibility); visibility();
})();
