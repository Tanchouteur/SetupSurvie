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
    <p id="work-queue-freshness" role="status" hidden></p>
    <div id="work-queue-groups"></div>`;
  $('main').append(page);

  const previews = [
    WorkQueuePreview.mount($('main-navigation'), {href: '#/file', refresh, toggle: () => state && command('/pause', {paused: !state.paused})}),
    WorkQueuePreview.mount(document.querySelector('.top-actions'), {href: '#/file', mobile: true, refresh})
  ];

  const {isSnapshot, waiting, failed, held, statusLabel, plural, freshness, lanes} = WorkQueuePreview;
  let state = null;
  let connection = 'loading';
  let observedAt = null;
  let lastPage = '';
  let pending = false;
  let fetching = null;
  let generation = 0;

  function message(text) {
    $('work-queue-error').hidden = !text;
    $('work-queue-error').textContent = text;
  }

  async function command(path, body, focus) {
    if (pending || connection !== 'ready') return;
    pending = true;
    draw();
    try {
      await api('/work-queue' + path, body);
      message('');
    } catch (error) {
      message(error.message);
    } finally {
      pending = false;
      draw();
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
    node.classList.toggle('work-queue-held', held(job));
    const main = element('div', undefined, 'work-queue-content');
    const title = element(job.href ? 'a' : 'strong', job.title);
    if (job.href) title.href = job.href;
    const label = element('span', job.next ? (state.paused ? 'À la reprise' : 'Ensuite') : statusLabel(job), 'work-queue-status');
    main.append(element('p', [job.type, job.model].filter(Boolean).join(' · '), 'work-queue-meta'), title);
    if (job.priority) main.append(element('span', 'Question prioritaire', 'work-queue-priority'));
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
    if (job.error && job.error !== job.stage) main.append(element('p', job.error, failed(job) ? 'work-queue-error-text' : 'work-queue-meta'));
    if (failed(job) && !job.error && !job.stage && !job.failure_count) {
      main.append(element('p', 'Le détail de cette erreur est indisponible.', 'work-queue-meta'));
    }
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
        control.disabled = connection !== 'ready' || pending || position + direction < 0 || position + direction >= movable.length;
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
      control.disabled = connection !== 'ready' || pending;
      tools.append(control);
    }
    node.dataset.workId = job.id;
    node.append(main, tools);
    return node;
  }

  function draw() {
    const admin = S.user?.role === 'admin';
    for (const preview of previews) preview.draw(state, {admin, connection, pending, current: S.view === 'work-queue'});
    if (page.hidden) return;
    const summary = $('work-queue-state');
    summary.tabIndex = -1;
    const status = $('work-queue-freshness');
    status.hidden = !state || !freshness[connection];
    status.textContent = status.hidden ? '' : freshness[connection] +
      (observedAt ? ' Dernière actualisation à ' + observedAt.toLocaleTimeString('fr-FR') + '.' : '');
    const toggle = $('work-queue-pause');
    toggle.hidden = !state || !admin;
    toggle.disabled = connection !== 'ready' || pending;
    if (!state) {
      summary.textContent = freshness[connection] || 'Chargement du suivi…';
      return;
    }
    const signature = JSON.stringify([state, admin, connection, pending]);
    if (signature === lastPage) return;
    lastPage = signature;
    const next = state.jobs.filter(waiting);
    const active = state.jobs.filter(job => job.status === 'running');
    const failures = state.jobs.filter(failed);
    const pausedJobs = state.jobs.filter(held);
    const partial = state.jobs.filter(job => !failed(job) && job.failure_count > 0);
    const counts = [
      active.length && plural(active.length, 'tâche en cours', 'tâches en cours'),
      next.length && plural(next.length, 'tâche en attente', 'tâches en attente'),
      failures.length && plural(failures.length, 'erreur', 'erreurs'),
      partial.length && plural(partial.length, 'lot avec des lignes à vérifier', 'lots avec des lignes à vérifier'),
      pausedJobs.length && plural(pausedJobs.length, 'tâche à reprendre', 'tâches à reprendre')
    ].filter(Boolean);
    const activity = counts.join(' · ') || (state.running ? 'Un travail est en cours sur l’appareil.' : 'Aucune tâche active.');
    summary.textContent = (state.paused ? 'File en pause. ' : '') + activity;
    toggle.textContent = state.paused ? 'Reprendre la file' : 'Mettre en pause';
    const host = $('work-queue-groups');
    const previous = document.activeElement?.dataset.workControl;
    const expanded = new Set(Array.from(host.querySelectorAll('li[data-work-id] > div > details[open]'), item => item.closest('li').dataset.workId));
    host.replaceChildren();
    function group(heading, jobs, container, className = 'work-queue-group') {
      if (!jobs.length) return;
      const section = element('section', undefined, className);
      const list = element('ul');
      const movable = {priority: [], standard: []};
      for (const job of jobs) {
        if (job.movable) movable[job.priority ? 'priority' : 'standard'].push(job);
      }
      for (const job of jobs) {
        const card = taskCard(job, movable[job.priority ? 'priority' : 'standard']);
        if (expanded.has(job.id)) {
          const details = card.querySelector('details');
          if (details) details.open = true;
        }
        list.append(card);
      }
      if (heading) section.append(element('h2', heading));
      section.append(list);
      container.append(section);
    }

    group('En erreur', failures, host);
    group('À reprendre', pausedJobs, host);
    const completedWithIssues = partial.filter(job => !waiting(job) && job.status !== 'running' && !held(job));
    group('Lots avec des lignes à vérifier', completedWithIssues, host);
    for (const lane of lanes(state)) {
      const section = element('section', undefined, 'work-queue-lane');
      section.dataset.lane = lane.id;
      const header = element('div', undefined, 'work-queue-lane-heading');
      const label = lane.running ? 'En cours' : state.paused ? 'En pause'
        : lane.waiting.length ? 'En attente' : 'Disponible';
      header.append(element('h2', lane.title), element('span', label, 'work-queue-meta'));
      section.append(header);
      if (lane.id === 'ai') {
        section.append(element('p', 'Les questions passent en priorité. Une tâche de fond avance après trois questions prioritaires si elle attend toujours.', 'work-queue-lane-rule'));
      }
      if (lane.running && !lane.active.length) section.append(element('p', 'Un travail utilise ce créneau.', 'work-queue-lane-rule'));
      if (!lane.running && !lane.waiting.length) section.append(element('p', 'Aucune tâche en attente.', 'work-queue-lane-rule'));
      group(null, [...lane.active, ...lane.waiting], section, 'work-queue-lane-jobs');
      host.append(section);
    }

    group('Historique récent', state.jobs.filter(job => !waiting(job) && job.status !== 'running' && !failed(job) && !held(job) && !(job.failure_count > 0)).slice(0, 30), host);
    if (previous) Array.from(host.querySelectorAll('[data-work-control]')).find(control => control.dataset.workControl === previous)?.focus({preventScroll: true});
  }

  async function refresh() {
    if (!S.user || !S.authReady || document.hidden || fetching) return;
    const epoch = generation;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    fetching = api('/work-queue', undefined, {signal: controller.signal}).then(value => {
      if (epoch !== generation) return;
      if (!isSnapshot(value)) throw Error();
      state = value;
      observedAt = new Date();
      connection = 'ready';
      draw();
    }).catch(() => {
      if (epoch !== generation) return;
      connection = state ? 'stale' : 'unavailable';
      draw();
    }).finally(() => {
      clearTimeout(timeout);
      fetching = null;
    });
    await fetching;
  }

  $('work-queue-pause').onclick = () => state && command('/pause', {paused: !state.paused});
  document.addEventListener('survie:auth', () => {
    state = null;
    connection = S.user ? 'loading' : 'anonymous';
    observedAt = null;
    message('');
    lastPage = '';
    generation++;
    $('work-queue-groups').replaceChildren();
    draw();
    if (fetching) fetching.then(refresh);
    else refresh();
  });
  document.addEventListener('survie:route', () => { draw(); refresh(); });
  document.addEventListener('visibilitychange', refresh);
  window.addEventListener('online', refresh);
  window.addEventListener('offline', () => {
    if (!S.user) return;
    connection = state ? 'stale' : 'unavailable';
    draw();
  });
  draw();
  setInterval(refresh, 3500);
})();
