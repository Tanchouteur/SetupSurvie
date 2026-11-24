/* Shared by the classic and new settings. */
(() => {
  const area = document.getElementById('model-downloads');
  area.innerHTML = `
    <h2 id="model-downloads-heading">Modèles de l’assistant</h2>
    <p>Le téléchargement demande Internet sur le PC serveur. Vous pourrez ensuite utiliser le modèle hors ligne.</p>
    <p class="model-notice small" role="status">Vérification des modèles…</p>
    <div class="model-progress" hidden>
      <strong class="model-progress-title" role="status"></strong>
      <progress aria-label="Progression du téléchargement"></progress>
      <div class="model-progress-footer">
        <span class="model-progress-detail small"></span>
        <button type="button" class="secondary model-cancel">Annuler</button>
      </div>
    </div>
    <div class="model-catalogue" hidden>
      <h3>Modèles conseillés</h3>
      <ul class="model-list model-recommended"></ul>
      <details class="model-comparison">
        <summary>Modèles de comparaison</summary>
        <ul class="model-list"></ul>
      </details>
    </div>`;

  const get = selector => area.querySelector(selector);
  const notice = get('.model-notice');
  const catalogue = get('.model-catalogue');
  const recommended = get('.model-recommended');
  const comparisons = get('.model-comparison .model-list');
  const downloadPanel = get('.model-progress');
  const progressTitle = get('.model-progress-title');
  const progressBar = get('progress');
  const progressDetail = get('.model-progress-detail');
  const cancel = get('.model-cancel');
  const rows = new Map();
  const labels = {
    downloading: 'Téléchargement en cours',
    complete: 'Modèle prêt',
    error: 'Échec du téléchargement',
    cancelled: 'Téléchargement annulé',
  };
  const format = new Intl.NumberFormat('fr-FR', {maximumFractionDigits: 1});
  const size = value => {
    if (value >= 1e9) return format.format(value / 1e9) + ' Go';
    if (value >= 1e6) return format.format(value / 1e6) + ' Mo';
    return format.format(value / 1e3) + ' Ko';
  };
  function updateText(node, text) {
    if (node.textContent !== text) node.textContent = text;
  }

  let latest = null, busy = false, loading = false, generation = 0, commandError = '';
  function controls() {
    const running = latest?.download?.state === 'downloading';
    for (const row of rows.values()) {
      row.button.disabled = busy || !latest?.available || running;
    }
    cancel.disabled = busy || !running;
  }

  function createRow(model) {
    const node = document.createElement('li');
    const info = document.createElement('div');
    const title = document.createElement('strong');
    title.textContent = model.name || model.model;
    const detail = document.createElement('p');
    detail.className = 'small muted';
    const installed = document.createElement('span');
    installed.className = 'model-installed';
    installed.textContent = '✓ Installé';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'secondary';
    button.textContent = 'Télécharger';
    button.setAttribute('aria-label', 'Télécharger ' + title.textContent);
    button.addEventListener('click', () => command('/admin/models/download', {model: model.model}));
    info.append(title, detail);
    node.append(info, installed, button);
    (model.category === 'recommended' ? recommended : comparisons).append(node);
    return {detail, installed, button};
  }

  function render(value) {
    latest = value;
    catalogue.hidden = false;
    updateText(notice, commandError || (value.available ? '' : 'Démarrez le moteur IA pour vérifier les modèles installés et en télécharger.'));
    for (const model of value.models) {
      if (!rows.has(model.model)) rows.set(model.model, createRow(model));
      const row = rows.get(model.model);
      const showSize = Number.isFinite(model.size);
      row.installed.hidden = model.installed !== true;
      row.button.hidden = model.installed === true;
      row.detail.textContent = showSize ? (model.installed === true ? '' : 'Environ ') + size(model.size) : 'Taille inconnue';
    }

    const download = value.download;
    downloadPanel.hidden = !download;
    if (download) {
      const name = value.models.find(model => model.model === download.model)?.name || download.model;
      const running = download.state === 'downloading';
      downloadPanel.dataset.state = download.state;
      updateText(progressTitle, labels[download.state] + ' · ' + name);
      progressBar.hidden = !running;
      cancel.hidden = !running;
      if (running && Number.isFinite(download.completed) && download.total > 0) {
        progressBar.max = download.total;
        progressBar.value = Math.min(download.completed, download.total);
      } else {
        progressBar.removeAttribute('value');
      }
      const count = running && progressBar.hasAttribute('value')
        ? size(progressBar.value) + ' sur ' + size(download.total) : '';
      updateText(progressDetail, [count, download.message].filter(Boolean).join(' · '));
    }
    controls();
  }

  const visible = () => !document.hidden && area.getClientRects().length > 0;
  async function refresh() {
    if (loading || busy || S.user?.role !== 'admin' || !visible()) return;
    loading = true;
    const ticket = generation;
    try {
      const result = await api('/admin/models');
      if (ticket === generation) render(result);
    } catch (error) {
      if (ticket === generation) {
        updateText(notice, 'Impossible de vérifier les modèles. ' + error.message);
        latest = null;
        controls();
      }
    } finally {
      loading = false;
    }
  }

  async function command(path, body) {
    if (busy) return;
    busy = true;
    generation++;
    commandError = '';
    controls();
    try {
      const result = await api(path, body);
      if (latest) render({...latest, download: result});
    } catch (error) {
      commandError = error.message;
      updateText(notice, commandError);
    } finally {
      busy = false;
      controls();
      refresh();
    }
  }

  cancel.addEventListener('click', () => command('/admin/models/cancel', {id: latest.download.id}));
  document.addEventListener('survie:auth', () => {
    generation++;
    latest = null;
    commandError = '';
    controls();
    refresh();
  });
  const settings = document.getElementById('view-settings');
  const observer = new MutationObserver(changes => {
    if (changes.some(change => change.target === settings || change.target.classList.contains('settings-pane'))) refresh();
  });
  observer.observe(settings, {attributes: true, subtree: true, attributeFilter: ['hidden']});
  document.addEventListener('visibilitychange', refresh);
  setInterval(refresh, 2500);
})();
