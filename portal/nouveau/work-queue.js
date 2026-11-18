(() => {
  const page = element('section', undefined, 'view work-queue-page');
  page.id = 'view-work-queue';
  page.hidden = true;
  page.innerHTML = `
    <div class="page-heading"><h1>File d’attente</h1></div>
    <div class="work-queue-toolbar">
      <p id="work-queue-state" role="status">Chargement de la file…</p>
      <button id="work-queue-pause" type="button" class="secondary" hidden>Mettre en pause</button>
    </div>
    <p id="work-queue-error" role="alert" hidden></p>
    <div id="work-queue-groups"></div>`;
  $('main').append(page);

  const previews = [
    WorkQueuePreview.mount($('main-navigation'), {href: '#/file', refresh, toggle: () => state && command('/pause', {paused: !state.paused})}),
    WorkQueuePreview.mount(document.querySelector('.top-actions'), {href: '#/file', mobile: true, refresh})
  ];

  const labels = {
    queued: 'En attente', preparing: 'Préparation', running: 'En cours',
    paused: 'En pause', completed: 'Terminé', done: 'Terminé', error: 'En erreur',
    failed: 'En erreur', incomplete: 'Incomplet', interrupted: 'Interrompu',
    stopped: 'Arrêté', cancelled: 'Annulé'
  };
  const {waiting, failed} = WorkQueuePreview;
  let state = null;
  let lastPage = '';
  let pending = false;
  let fetching = null;
  let generation = 0;

  function message(text) {
    $('work-queue-error').hidden = !text;
    $('work-queue-error').textContent = text;
  }

  async function command(path, body, focus) {
    if (pending) return;
    pending = true;
    try {
      await api('/work-queue' + path, body);
      message('');
    } catch (error) {
      message(error.message);
    } finally {
      pending = false;
    }
    if (fetching) await fetching;
    await refresh();
    if (focus) {
      const buttons = Array.from(page.querySelectorAll('button[data-work-control]'));
      const button = buttons.find(control => control.dataset.workControl === focus && !control.disabled);
      const fallback = buttons.find(control => control.dataset.workControl.split(':')[0] === focus.split(':')[0] && !control.disabled);
      (button || fallback || $('work-queue-state')).focus({preventScroll: true});
    }
  }

  function taskCard(job, movable) {
    const node = element('li', undefined, 'work-queue-card');
    node.classList.toggle('work-queue-problem', failed(job));
    const main = element('div', undefined, 'work-queue-content');
    const title = element(job.href ? 'a' : 'strong', job.title);
    if (job.href) title.href = job.href;
    const label = element('span', labels[job.status] || 'À vérifier', 'work-queue-status');
    main.append(element('p', [job.type, job.model].filter(Boolean).join(' · '), 'work-queue-meta'), title);
    if (job.stage) main.append(element('p', job.stage, 'work-queue-meta'));
    if (job.total > 0 && Number.isFinite(job.done)) {
      const percent = Math.round(100 * Math.min(job.total, job.done) / job.total);
      const progress = element('progress');
      progress.max = job.total;
      progress.value = job.done;
      progress.setAttribute('aria-label', 'Avancement de ' + job.title);
      const row = element('div', undefined, 'work-queue-progress');
      const amount = job.kind === 'speech' ? percent + ' %' : job.done + ' / ' + job.total;
      row.append(progress, element('span', amount));
      main.append(row);
    }
    if (job.error && job.error !== job.stage) main.append(element('p', job.error, 'work-queue-error-text'));
    if (job.failure_count) {
      const details = element('details', undefined, 'work-queue-failures');
      const list = element('ul');
      for (const failure of job.failures) {
        list.append(element('li', 'Ligne ' + failure.line + ' · ' + failure.message));
      }
      details.append(element('summary', job.failure_count + ' ligne(s) à vérifier'), list);
      if (job.failure_count > job.failures.length) details.append(element('p', 'Le rapport YouTube contient les autres lignes.'));
      main.append(details);
    }
    const tools = element('div', undefined, 'work-queue-controls');
    tools.append(label);
    const position = movable.indexOf(job);
    if (position >= 0) {
      const order = element('div', undefined, 'work-queue-order');
      for (const [direction, symbol, name] of [[-1, '↑', 'Avancer'], [1, '↓', 'Reculer']]) {
        const id = job.id + ':' + direction;
        const control = button(symbol, () => command('/' + encodeURIComponent(job.id) + '/move', {direction}, id));
        control.dataset.workControl = id;
        control.disabled = position + direction < 0 || position + direction >= movable.length;
        control.setAttribute('aria-label', name + ' ' + job.title);
        control.title = name;
        order.append(control);
      }
      tools.append(order);
    }
    if (job.retry) {
      const id = job.id + ':retry';
      const control = button(job.status === 'paused' ? 'Reprendre' : 'Réessayer', () => command('/' + encodeURIComponent(job.id) + '/retry', {}, id));
      control.dataset.workControl = id;
      tools.append(control);
    }
    node.dataset.workId = job.id;
    node.append(main, tools);
    return node;
  }

  function draw() {
    if (!state) return;
    const next = state.jobs.filter(waiting);
    const active = state.jobs.filter(job => job.status === 'running');
    const failures = state.jobs.filter(failed);
    for (const preview of previews) preview.draw(state, {admin: S.user?.role === 'admin', current: S.view === 'work-queue'});
    if (page.hidden) return;
    const signature = JSON.stringify([state, S.user?.role]);
    if (signature === lastPage) return;
    lastPage = signature;
    const summary = $('work-queue-state');
    summary.tabIndex = -1;
    summary.textContent = state.paused ? (state.running ? 'File en pause. Le traitement en cours termine son étape.' : 'File en pause.')
      : state.running && !active.length ? 'Un autre travail utilise l’appareil.' : next.length ? next.length + ' travail(aux) en attente.' : 'Aucun travail en attente.';
    const toggle = $('work-queue-pause');
    toggle.hidden = S.user?.role !== 'admin';
    toggle.textContent = state.paused ? 'Reprendre la file' : 'Mettre en pause';
    const host = $('work-queue-groups');
    const previous = document.activeElement?.dataset.workControl;
    const expanded = new Set(Array.from(host.querySelectorAll('li[data-work-id] > div > details[open]'), item => item.closest('li').dataset.workId));
    host.replaceChildren();
    const movable = next.filter(job => job.movable);
    for (const [heading, jobs] of [
      ['En cours', active], ['En attente', next], ['À vérifier', failures],
      ['Historique récent', state.jobs.filter(job => !waiting(job) && job.status !== 'running' && !failed(job)).slice(0, 30)]
    ]) {
      if (!jobs.length) continue;
      const section = element('section', undefined, 'work-queue-group');
      const list = element('ul');
      for (const job of jobs) {
        const card = taskCard(job, movable);
        if (expanded.has(job.id)) {
          const details = card.querySelector('details');
          if (details) details.open = true;
        }
        list.append(card);
      }
      section.append(element('h2', heading), list);
      host.append(section);
    }
    if (previous) Array.from(host.querySelectorAll('[data-work-control]')).find(control => control.dataset.workControl === previous)?.focus({preventScroll: true});
  }

  async function refresh() {
    if (!S.user || !S.authReady || document.hidden || fetching) return;
    const epoch = generation;
    fetching = api('/work-queue').then(value => {
      if (epoch !== generation) return;
      state = value;
      draw();
    }).catch(() => {
      if (epoch === generation && !state && !page.hidden) $('work-queue-state').textContent = 'Le suivi de la file est indisponible. Nouvelle tentative dans quelques secondes.';
    }).finally(() => { fetching = null; });
    await fetching;
  }

  $('work-queue-pause').onclick = () => state && command('/pause', {paused: !state.paused});
  document.addEventListener('survie:auth', () => {
    state = null;
    lastPage = '';
    generation++;
    $('work-queue-groups').replaceChildren();
    for (const preview of previews) preview.draw(null);
    if (fetching) fetching.then(refresh);
    else refresh();
  });
  document.addEventListener('survie:route', () => { draw(); refresh(); });
  document.addEventListener('visibilitychange', refresh);
  setInterval(refresh, 3500);
})();
