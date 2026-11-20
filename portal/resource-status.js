/* Portal: consume the existing refresh. Map: read-only refresh when visible on desktop. */
(() => {
  const mapHeader = document.querySelector('.map-site-nav');
  const container = mapHeader || document.getElementById('main-navigation');
  if (!container) return;
  const link = document.createElement('a');
  link.className = 'resource-status';
  link.href = (mapHeader ? '/' : '') + '#/appareil/ensemble';
  if (!mapHeader) link.dataset.route = 'appareil/ensemble';
  link.innerHTML = `
    <span class="resource-status-model" aria-hidden="true">
      <span class="resource-status-caption">Modèle chargé</span>
      <span class="resource-status-name"></span>
    </span>
    <span class="resource-status-meters" aria-hidden="true"></span>
    <span class="resource-status-chevron" aria-hidden="true">›</span>`;
  /* Téléphone : pastille compacte dans l'en-tête (modèle + deux jauges),
   * pour garder la surveillance visible sans place pour la jauge complète. */
  const chips = mapHeader ? [] : [document.querySelector('.topbar .top-actions'), container].filter(Boolean).map(host => {
    const chip = document.createElement('a');
    chip.className = 'resource-chip';
    chip.href = '#/appareil/ensemble';
    chip.dataset.route = 'appareil/ensemble';
    chip.innerHTML = '<span class="resource-chip-dot" aria-hidden="true"></span><span class="resource-chip-bars" aria-hidden="true"><i data-meter="ram"></i><i data-meter="vram"></i></span>';
    if (host === container) host.append(chip); else host.prepend(chip);
    return chip;
  });
  const caption = link.querySelector('.resource-status-caption');
  const modelName = link.querySelector('.resource-status-name');
  const meters = link.querySelector('.resource-status-meters');
  container.append(link);

  function createMeter(label) {
    const element = document.createElement('span');
    element.className = 'resource-status-meter';
    element.innerHTML = `
      <span class="resource-status-meter-label">
        <span></span><span class="resource-status-value"></span>
      </span>
      <span class="resource-status-track"><span class="resource-status-fill"></span></span>`;
    element.querySelector('.resource-status-meter-label > span').textContent = label;
    meters.append(element);
    return {element, value: element.querySelector('.resource-status-value'), label};
  }

  const ram = createMeter('RAM');
  const vram = createMeter('VRAM');
  const validMemory = item => item && Number.isFinite(item.used) && item.used >= 0 &&
    Number.isFinite(item.total) && item.total > 0 && item.used <= item.total;
  const formatter = new Intl.NumberFormat('fr-FR', {maximumFractionDigits: 1});
  const size = bytes => formatter.format(bytes / 1024 ** 3);

  function updateMeter(meter, item) {
    const usage = validMemory(item) ? item.used / item.total : null;
    meter.element.dataset.level = usage === null ? 'unavailable' : usage >= 0.9 ? 'high' : 'normal';
    meter.element.style.setProperty('--resource-usage', usage ?? 0);
    meter.value.textContent = usage === null ? '—' : Math.round(usage * 100) + '%';
    return usage === null ? meter.label + ' indisponible' : meter.label + ' ' + size(item.used) + '/' + size(item.total) + ' Go';
  }

  function show(model, modelCaption, memory, gpu, spokenModel = modelCaption + ' : ' + model, modelState = 'unknown') {
    caption.textContent = modelCaption;
    modelName.textContent = model;
    const summary = [spokenModel, updateMeter(ram, memory), updateMeter(vram, gpu)].join(' · ');
    link.title = summary;
    link.dataset.model = modelState;
    link.setAttribute('aria-label', 'Voir les mesures de l’appareil. ' + summary);
    for (const chip of chips) {
      chip.dataset.model = modelState;
      for (const meter of [ram, vram]) {
        const bar = chip.querySelector(`[data-meter="${meter.label.toLowerCase()}"]`);
        bar.style.setProperty('--resource-usage', meter.element.style.getPropertyValue('--resource-usage') || 0);
        bar.dataset.level = meter.element.dataset.level;
      }
      chip.title = summary;
      chip.setAttribute('aria-label', 'État de l’appareil. ' + summary);
    }
  }

  function unavailable() {
    show('Mesures indisponibles', 'État de l’appareil', null, null, 'Mesures non actualisées');
  }

  function display(data) {
    if (!data || data.observation_error) {
      unavailable();
      return;
    }

    /* Sans service de commande, le modèle chargé ne peut pas être vérifié :
     * on le dit tel quel, sans laisser croire que l'assistant est en panne. */
    let model = 'Non vérifié';
    let modelCaption = 'Modèle chargé';
    let spokenModel = 'Modèle chargé non vérifié : le service de mesure ne répond pas. L’assistant peut tout de même répondre.';
    if (data.control_available && data.models_available !== false && Array.isArray(data.models)) {
      const names = data.models.map(item => typeof item?.name === 'string' ? item.name.trim() : '').filter(Boolean);
      if (!data.models.length) {
        modelCaption = 'Assistant';
        if (data.operation === 'start') model = 'Démarrage…';
        else if (data.operation === 'stop') model = 'Arrêt en cours…';
        else model = data.paused ? 'Moteur en pause' : 'Aucun modèle';
        spokenModel = model === 'Aucun modèle' ? 'Aucun modèle chargé' : model + ' · Aucun modèle chargé';
      } else if (names.length === data.models.length) {
        model = names[0] + (names.length > 1 ? ' +' + (names.length - 1) : '');
        spokenModel = (names.length > 1 ? 'Modèles chargés : ' : 'Modèle chargé : ') + names.join(', ');
      }
    }
    const gpus = data.gpus;
    const gpu = Array.isArray(gpus) && gpus.length && gpus.every(validMemory)
      ? {used: gpus.reduce((sum, item) => sum + item.used, 0),
         total: gpus.reduce((sum, item) => sum + item.total, 0)} : null;
    const modelState = model === 'Non vérifié' ? 'unknown' : modelCaption === 'Assistant'
      ? (data.operation ? 'busy' : data.paused ? 'paused' : 'idle') : 'loaded';
    show(model, modelCaption, data.memory, gpu, spokenModel, modelState);
  }

  unavailable();
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
    } catch (_) { if (current === generation) unavailable(); }
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
