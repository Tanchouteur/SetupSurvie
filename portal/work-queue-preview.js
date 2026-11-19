/* Queue entry shared by the portal header and the separate map page. */
(() => {
  const make = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const isSnapshot = state => Array.isArray(state?.jobs);
  const waiting = job => ['queued', 'preparing'].includes(job.status);
  const failed = job => ['error', 'failed'].includes(job.status);
  const held = job => ['paused', 'stopped', 'interrupted', 'incomplete'].includes(job.status);
  const statusLabel = job => ({
    queued: 'En attente', preparing: 'Préparation', running: 'En cours', paused: 'En pause',
    completed: 'Terminé', done: 'Terminé', error: 'En erreur', failed: 'En erreur',
    incomplete: 'Incomplet', interrupted: 'Interrompu', stopped: 'Arrêté', cancelled: 'Annulé'
  })[job.status] || 'État inconnu';
  const workLabel = (job, fallback) => ({
    paused:'En attente · file en pause', next:'Ensuite dans la file', waiting:'En attente de son tour'
  })[job.queue_state] || fallback;
  const plural = (count, singular, multiple) => count + ' ' + (count === 1 ? singular : multiple);
  const freshness = {
    loading: 'Chargement du suivi…',
    unavailable: 'Suivi indisponible. Nouvelle tentative automatique.',
    stale: 'Suivi indisponible. Dernier état connu.',
    anonymous: 'Choisissez un profil pour voir la file.'
  };

  function lanes(state) {
    return [['ai', 'Assistant et traductions'], ['network', 'Téléchargements'], ['local', 'Préparation locale']]
      .map(([id, title]) => {
        const jobs = state.jobs.filter(job => (job.lane || 'ai') === id);
        const active = jobs.filter(job => job.status === 'running');
        return {id, title, active, waiting: jobs.filter(waiting), running: state.lanes?.[id]?.running ?? !!active.length};
      });
  }

  function mount(container, {href, mobile = false, refresh, toggle}) {
    const host = make('div', '', 'work-queue-nav' + (mobile ? ' work-queue-mobile' : ''));
    const link = make('a', '', 'work-queue-link');
    link.href = href;
    if (href.startsWith('#')) link.dataset.route = 'file';
    link.setAttribute('aria-label', 'File d’attente');
    const count = make('span', '', 'work-queue-count');
    count.setAttribute('aria-hidden', 'true');
    const icon = make('span', '☷', 'work-queue-icon');
    icon.setAttribute('aria-hidden', 'true');
    const signal = make('span', '', 'work-queue-signal');
    signal.setAttribute('aria-hidden', 'true');
    signal.hidden = true;
    link.append(icon, count, signal);
    host.append(link);

    const preview = make('div', '', 'work-queue-preview');
    const list = make('ul');
    const action = make('button', 'Mettre en pause', 'secondary');
    action.type = 'button';
    action.hidden = true;
    preview.append(make('strong', 'File d’attente'), list, action);
    if (!mobile) {
      host.append(preview);
      host.addEventListener('pointerenter', () => {
        host.classList.remove('work-queue-dismissed');
        refresh();
      });
      host.addEventListener('focusin', event => {
        if (event.target === link) {
          host.classList.remove('work-queue-dismissed');
          refresh();
        }
      });
      host.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
          link.focus();
          host.classList.add('work-queue-dismissed');
        }
      });
      if (toggle) action.onclick = toggle;
    }
    container.append(host);

    function draw(state, {admin = false, current = false, connection = 'ready', pending = false} = {}) {
      const queued = state?.jobs.filter(waiting).length || 0;
      const active = state?.jobs.filter(job => job.status === 'running').length || 0;
      const errors = state?.jobs.filter(failed).length || 0;
      const partial = state?.jobs.filter(job => !failed(job) && job.failure_count > 0).length || 0;
      const suspended = state?.jobs.filter(held).length || 0;
      host.dataset.state = errors ? 'attention' : state?.paused || partial || suspended ? 'paused' : '';
      host.dataset.connection = connection;
      count.textContent = state ? queued + active : '';
      const unknown = connection === 'stale' || connection === 'unavailable';
      signal.textContent = errors || partial ? '!' : unknown ? '?' : state?.paused || suspended ? 'Ⅱ' : '';
      signal.hidden = !signal.textContent;
      signal.dataset.level = errors ? 'error' : unknown ? 'unknown' : 'warning';
      link.setAttribute('aria-label', ['File d’attente',
        state && plural(active, 'tâche en cours', 'tâches en cours'),
        state && plural(queued, 'tâche en attente', 'tâches en attente'),
        errors && plural(errors, 'erreur', 'erreurs'),
        partial && plural(partial, 'lot avec des lignes à vérifier', 'lots avec des lignes à vérifier'),
        suspended && plural(suspended, 'tâche à reprendre', 'tâches à reprendre'),
        state?.paused && 'file en pause', freshness[connection]
      ].filter(Boolean).join(' · '));
      if (current) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
      action.hidden = !state || !admin || !toggle;
      action.disabled = connection !== 'ready' || pending;
      if (state) action.textContent = state.paused ? 'Reprendre la file' : 'Mettre en pause';
      if (mobile) return;
      const entries = [];
      if (freshness[connection]) entries.push(make('li', freshness[connection], 'work-queue-preview-notice'));
      if (state?.paused) entries.push(make('li', 'File en pause', 'work-queue-preview-notice'));
      if (state) {
        const problems = [...state.jobs.filter(failed), ...state.jobs.filter(job => !failed(job) && job.failure_count > 0)];
        const pausedJobs = state.jobs.filter(held);
        for (const [items, title, style] of [
          [problems, errors ? plural(errors, 'erreur', 'erreurs') : 'Lignes à vérifier', errors ? 'work-queue-error-text' : 'work-queue-preview-notice'],
          [pausedJobs, plural(suspended, 'tâche à reprendre', 'tâches à reprendre'), 'work-queue-preview-notice']
        ]) {
          if (!items.length) continue;
          const row = make('li', '', style);
          row.append(make('strong', title));
          for (const job of items.slice(0, 2)) {
            const detail = failed(job) || held(job) ? statusLabel(job) : 'Lignes à vérifier';
            row.append(make('span', detail + ' · ' + job.title, 'work-queue-preview-task'));
            const reason = job.error || job.failures?.[0]?.message;
            if (reason) {
              const note = make('span', reason, 'work-queue-preview-task');
              note.title = reason;
              row.append(note);
            }
          }
          if (items.length > 2) row.append(make('span', plural(items.length - 2, 'autre tâche dans la file', 'autres tâches dans la file'), 'work-queue-meta'));
          entries.push(row);
        }
        for (const lane of lanes(state).filter(lane => lane.id === 'ai' || lane.running || lane.waiting.length)) {
          const row = make('li', '', 'work-queue-preview-lane');
          row.append(make('strong', lane.title));
          for (const job of lane.active) row.append(make('span', 'En cours · ' + job.title, 'work-queue-preview-task'));
          if (!lane.active.length && lane.running) row.append(make('span', 'En cours sur l’appareil', 'work-queue-meta'));
          const next = lane.waiting.find(job => job.next);
          if (next) row.append(make('span', (state.paused ? 'À la reprise · ' : 'Ensuite · ') + next.title, 'work-queue-preview-task'));
          if (lane.waiting.length > (next ? 1 : 0)) {
            row.append(make('span', plural(lane.waiting.length, 'tâche en attente', 'tâches en attente'), 'work-queue-meta'));
          } else if (!lane.running && !lane.waiting.length && !state.paused) {
            row.append(make('span', 'Aucune tâche en attente', 'work-queue-meta'));
          }
          entries.push(row);
        }
      }
      list.replaceChildren(...entries);
    }
    return {draw};
  }

  window.WorkQueuePreview = {mount, isSnapshot, waiting, failed, held, statusLabel, workLabel, plural, freshness, lanes};
  const map = document.querySelector('.map-site-nav');
  if (!map) return;
  let snapshot = null, fetching = false, generation = 0;
  const fetchQueue = async () => {
    if (document.hidden || fetching) return;
    fetching = true;
    const epoch = generation;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
      const response = await fetch('/api/work-queue', {credentials: 'same-origin', signal: controller.signal});
      if (epoch !== generation) return;
      if (response.status === 401 || response.status === 403) {
        snapshot = null;
        preview.draw(null, {connection: 'anonymous'});
        return;
      }
      if (!response.ok) throw Error();
      const result = await response.json();
      if (epoch !== generation) return;
      if (!isSnapshot(result)) throw Error();
      snapshot = result;
      preview.draw(snapshot);
    } catch {
      if (epoch === generation) preview.draw(snapshot, {connection: snapshot ? 'stale' : 'unavailable'});
    } finally {
      clearTimeout(timeout);
      fetching = false;
      if (epoch !== generation) fetchQueue();
    }
  };
  const preview = mount(map, {href: '/nouveau/#/file', refresh: fetchQueue});
  preview.draw(null, {connection: 'loading'});
  document.addEventListener('survie:auth', () => {
    generation++;
    snapshot = null;
    preview.draw(null, {connection: 'loading'});
    fetchQueue();
  });
  document.addEventListener('visibilitychange', fetchQueue);
  fetchQueue();
  setInterval(fetchQueue, 7000);
})();
