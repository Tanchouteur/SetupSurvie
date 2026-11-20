/* Shared view of an update or a complete copy.
   Used by the portal home page and by the temporary maintenance page served while
   every container is stopped (scripts/maintenance_site.py). Status text is always
   inserted with textContent; nothing from the status is interpreted as HTML. */
(() => {
  const STATUS_URL = '/catalog/maintenance.json';
  const KINDS = {
    update: 'Mise à jour de SetupSurvie',
    recover: 'Récupération d’une mise à jour',
    rollback: 'Retour à une version précédente',
    transfer: 'Copie complète de SetupSurvie',
  };
  const number = new Intl.NumberFormat('fr-FR', {maximumFractionDigits: 1});
  // Same limit as scripts/update_watch.py: every running phase reports far more often.
  const STALE_SECONDS = 1200;
  const stale = (status, now = Date.now() / 1000) =>
    status?.state === 'running' && now - (Number(status.updated) || 0) > STALE_SECONDS;

  function make(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function duration(seconds) {
    const total = Math.max(0, Math.round(seconds));
    const hours = Math.floor(total / 3600), minutes = Math.floor(total % 3600 / 60), rest = total % 60;
    if (hours) return `${hours} h ${String(minutes).padStart(2, '0')} min`;
    if (minutes) return `${minutes} min ${String(rest).padStart(2, '0')} s`;
    return `${rest} s`;
  }

  /* Plain words for the person in front of the screen, from the raw status. */
  function summary(status) {
    const kind = status.kind || 'update';
    const versions = status.installed && status.available ? `${status.installed} → ${status.available}` : status.installed || '';
    if (status.state === 'completed') {
      if (kind === 'transfer') return {tone: 'ok', title: 'Copie vérifiée',
        text: 'Terminez l’activation depuis « Transférer SetupSurvie » sur le PC serveur.'};
      return {tone: 'ok', title: kind === 'update' ? 'Mise à jour terminée' : 'Opération terminée',
        text: status.available ? `La version ${status.available} est installée. Vos données sont conservées.` : 'Vos données sont conservées.'};
    }
    if (status.state === 'current') return {tone: 'ok', title: 'SetupSurvie est déjà à jour', text: versions ? `Version ${status.installed}.` : ''};
    if (status.state === 'failed') {
      if (kind === 'transfer') return {tone: 'danger', title: 'Copie interrompue',
        text: status.detail || 'Reprenez la copie depuis « Transférer SetupSurvie » sur le PC serveur.'};
      if (status.rolled_back) return {tone: 'warn', title: 'Mise à jour annulée',
        text: 'L’ancienne version a été remise en service et vos données sont conservées. ' + (status.detail || '')};
      return {tone: 'danger', title: 'La mise à jour s’est arrêtée',
        text: (status.detail || '') + ' Sur le PC serveur, le raccourci « Mettre à jour SetupSurvie » affiche le journal.'};
    }
    if (stale(status)) return {tone: 'warn', title: 'Suivi interrompu', text: kind === 'transfer'
      ? 'Aucune nouvelle information depuis longtemps. La copie a peut-être été interrompue : rouvrez « Transférer SetupSurvie » sur le PC serveur pour la reprendre.'
      : 'Aucune nouvelle information depuis longtemps. L’opération a peut-être été interrompue (coupure, redémarrage) : sur le PC serveur, ouvrez « Mettre à jour SetupSurvie », qui reprend ou récupère la mise à jour.'};
    return {tone: 'running', title: status.title || 'Opération en cours', text: status.detail || ''};
  }

  function build(host) {
    host.replaceChildren();
    host.classList.add('mv-panel');
    const parts = {
      kind: make('p', 'mv-kind'), versions: make('p', 'mv-versions'), title: make('h2', 'mv-title'),
      text: make('p', 'mv-text'), meter: make('div', 'mv-meter'), bar: make('progress', 'mv-progress'),
      amount: make('p', 'mv-amount'), file: make('p', 'mv-file'), availability: make('p', 'mv-availability'),
      connection: make('p', 'mv-connection'), times: make('p', 'mv-times'), steps: make('ol', 'mv-steps'),
      details: make('details', 'mv-details'), lines: make('pre', 'mv-lines'), actions: make('div', 'mv-actions'),
    };
    parts.title.setAttribute('tabindex', '-1');
    parts.text.setAttribute('role', 'status');
    parts.connection.setAttribute('role', 'alert');
    parts.bar.max = 100;
    parts.bar.setAttribute('aria-label', 'Avancement de l’étape');
    parts.meter.append(parts.bar, parts.amount, parts.file);
    parts.details.append(make('summary', '', 'Détails techniques'), parts.lines);
    host.append(parts.kind, parts.versions, parts.title, parts.text, parts.meter, parts.availability,
      parts.connection, parts.times, parts.steps, parts.details, parts.actions);
    host.maintenanceParts = parts;
    return parts;
  }

  function render(host, status, {connection = 'ready', now = Date.now() / 1000} = {}) {
    const parts = host.maintenanceParts || build(host);
    const view = summary(status);
    host.dataset.state = status.state || 'running';
    host.dataset.tone = view.tone;
    parts.kind.textContent = KINDS[status.kind] || 'Maintenance de SetupSurvie';
    parts.versions.textContent = status.installed && status.available
      ? `Version installée ${status.installed} · nouvelle version ${status.available}`
      : status.destination ? `Destination : ${status.destination}` : '';
    parts.versions.hidden = !parts.versions.textContent;
    parts.title.textContent = view.title;
    parts.text.textContent = view.text.trim();
    parts.text.hidden = !parts.text.textContent;

    const running = status.state === 'running' && !stale(status, now);
    const total = Number(status.total) || 0, current = Number(status.current) || 0;
    parts.meter.hidden = !running;
    if (total > 0) {
      parts.bar.value = Math.min(100, 100 * current / total);
      const percent = Math.floor(100 * current / total);
      parts.amount.textContent = status.unit === 'bytes'
        ? `${number.format(current / 1e9)} Go sur ${number.format(total / 1e9)} Go vérifiés (${percent} %)`
        : `${current.toLocaleString('fr-FR')} sur ${total.toLocaleString('fr-FR')} (${percent} %)`;
    } else {
      parts.bar.removeAttribute('value');
      parts.amount.textContent = '';
    }
    const fileTotal = Number(status.file_total) || 0;
    parts.file.textContent = running && fileTotal > 100e6
      ? `Fichier en cours : ${number.format((Number(status.file_bytes) || 0) / 1e9)} Go sur ${number.format(fileTotal / 1e9)} Go` : '';
    parts.file.hidden = !parts.file.textContent;

    parts.availability.hidden = !running;
    parts.availability.textContent = status.unavailable
      ? 'Le site est indisponible pendant cette étape, sur tous les appareils. Cette page se met à jour toute seule.'
      : 'Vous pouvez continuer à utiliser SetupSurvie. Le site sera indisponible quelques minutes pendant l’installation.';
    if (status.kind === 'transfer' && running) parts.availability.textContent =
      'SetupSurvie est arrêté pendant la copie. Les documents seront de nouveau accessibles après l’activation ou le retour à la source.';

    parts.connection.hidden = connection === 'ready';
    parts.connection.textContent = connection === 'lost'
      ? 'Connexion au serveur momentanément perdue : dernier état connu affiché. Nouvelle tentative automatique.'
      : '';

    const times = [];
    if (status.started) times.push((running ? 'Commencé il y a ' : 'Durée : ') +
      duration((running ? now : Number(status.updated) || now) - status.started));
    if (running && status.updated && now - status.updated > 120) times.push(`dernière information il y a ${duration(now - status.updated)}`);
    parts.times.textContent = times.join(' · ');
    parts.times.hidden = !times.length;

    const steps = Array.isArray(status.steps) ? status.steps : [];
    parts.steps.replaceChildren(...steps.map((step, index) => {
      const last = index === steps.length - 1;
      const item = make('li', last && running ? 'mv-step-current' : 'mv-step-done', step.title || '');
      if (last && running) item.setAttribute('aria-current', 'step');
      return item;
    }));
    parts.steps.hidden = !steps.length;
    const lines = Array.isArray(status.lines) ? status.lines.map(String) : [];
    parts.lines.textContent = lines.join('\n');
    parts.details.hidden = !lines.length;
    return parts;
  }

  async function fetchStatus(signal) {
    const response = await fetch(STATUS_URL, {cache: 'no-store', credentials: 'same-origin', signal});
    if (response.status === 404) return {status: null, maintenancePage: false};
    if (!response.ok) throw new Error('status');
    const status = await response.json();
    return {
      status: status && typeof status === 'object' ? status : null,
      maintenancePage: response.headers.get('X-SetupSurvie-Maintenance') === '1',
    };
  }

  window.SurvieMaintenance = {render, summary, fetchStatus, stale, kinds: KINDS};

  /* Standalone page: poll until the real portal answers again, then reload. */
  const standalone = document.getElementById('maintenance-standalone');
  if (!standalone) return;
  let last = null, failures = 0;
  async function poll() {
    try {
      const {status, maintenancePage} = await fetchStatus();
      failures = 0;
      if (!maintenancePage) {
        location.reload();
        return;
      }
      if (status) last = status;
      if (last) render(standalone, last);
    } catch (_) {
      failures += 1;
      if (last) render(standalone, last, {connection: failures > 1 ? 'lost' : 'ready'});
    }
    setTimeout(poll, 2000);
  }
  poll();
})();
