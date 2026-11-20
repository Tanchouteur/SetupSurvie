(() => {
  const page = element('section', undefined, 'view work-queue-page');
  page.id = 'view-work-queue';
  page.hidden = true;
  page.innerHTML = `
    <div class="page-heading work-queue-heading">
      <h1>File d’attente</h1>
      <details class="queue-help">
        <summary aria-label="Comment fonctionne la file d’attente ?">?</summary>
        <p>Chaque carte indique où en est un travail. Utilisez ses boutons pour mettre une préparation en pause ou la reprendre. Ouvrez son titre pour retrouver les réglages et le rapport.</p>
        <p>La pause générale concerne les tâches programmées par la file. Pour arrêter une préparation du PC serveur, utilisez le bouton de sa carte.</p>
      </details>
    </div>
    <div class="work-queue-toolbar">
      <div><strong id="work-queue-overview">Suivi des tâches</strong>
      <p id="work-queue-state" role="status">Chargement de la file…</p></div>
      <button id="work-queue-pause" type="button" class="secondary" hidden>Mettre en pause</button>
    </div>
    <p id="work-queue-error" role="alert" hidden></p>
    <p id="work-queue-freshness" role="status" hidden></p>
    <p id="work-queue-help" class="work-queue-meta" hidden>Glissez la poignée d’une tâche en attente pour la déplacer dans son groupe. Au clavier, utilisez les flèches haut et bas sur la poignée.</p>
    <p id="work-queue-host-notice" class="work-queue-meta" hidden>Le suivi des préparations de l’appareil est indisponible. Les autres tâches restent visibles.</p>
    <div class="work-queue-filters" role="group" aria-label="Travaux affichés" hidden>
      <button type="button" data-queue-filter="current" aria-pressed="true">À suivre</button>
      <button type="button" data-queue-filter="history" aria-pressed="false">Historique récent</button>
    </div>
    <div id="work-queue-groups"></div>`;
  $('main').append(page);

  const previews = [
    WorkQueuePreview.mount($('main-navigation'), {href: '#/file', refresh, move, toggle: () => state && command('/pause', {paused: !state.paused})}),
    WorkQueuePreview.mount(document.querySelector('.top-actions'), {href: '#/file', mobile: true, refresh})
  ];

  const {isSnapshot, waiting, failed, held, statusLabel, plural, freshness, lanes, dragHandle} = WorkQueuePreview;
  let state = null;
  let connection = 'loading';
  let observedAt = null;
  let lastPage = '';
  let pending = false;
  let fetching = null;
  let generation = 0;
  let filter = 'current';
  const filters = page.querySelector('.work-queue-filters');
  const laneHelp = {
    ai: 'Les questions passent en priorité. Si un travail de fond attend toujours après trois questions prioritaires, il avance à son tour.',
    network: 'Ces tâches récupèrent des fichiers ou des pistes. Elles peuvent avancer pendant une réponse de l’assistant.',
    local: 'L’appareil examine ou transforme des fichiers déjà présents, par exemple pour les retrouver dans la recherche ou transcrire une vidéo.'
  };
  function help(label, explanation) {
    const details = element('details', undefined, 'queue-help');
    const summary = element('summary', '?');
    summary.setAttribute('aria-label', label);
    details.append(summary, element('p', explanation));
    return details;
  }
  filters.addEventListener('click', event => {
    const control = event.target.closest('[data-queue-filter]');
    if (!control) return;
    filter = control.dataset.queueFilter;
    draw();
  });

  function preparationDetails(job) {
    const data = job.preparation;
    const details = element('details', undefined, 'work-queue-failures');
    details.dataset.queueDetails = JSON.stringify([job.id, 'preparation']);
    details.append(element('summary', 'Détails techniques'));
    const stamp = data.observed_at && new Date(data.observed_at * 1000).toLocaleTimeString('fr-FR');
    if (stamp) details.append(element('p', 'Dernière observation à ' + stamp + '.'));
    if (data.stale) details.append(element('p', 'Progression ancienne ou non confirmée.'));
    if (data.source === 'windows') details.append(element('p', 'Transfert Windows indépendant · suivi en lecture seule.'));
    if (data.total_bytes > 0) {
      details.append(element('p', bytes(data.verified_bytes) + ' / ' + bytes(data.total_bytes) +
        ' vérifiés · ' + data.verified_count + ' / ' + data.total_count + ' éléments.'));
      details.append(element('p', 'Les fichiers partiels sont vérifiés après réception. Un fichier vérifié peut encore attendre sa mise à disposition.'));
    }
    if (data.active?.length) {
      const list = element('ul');
      for (const file of data.active) {
        const phase = file.phase === 'verifying' ? 'Vérification' : 'Transfert';
        list.append(element('li', file.title + ' · ' + bytes(file.bytes) + ' / ' + bytes(file.total) + ' · ' + phase));
      }
      details.append(list);
    }
    if (data.pending_errors) details.append(element('p', data.pending_errors + ' contenu(s) à vérifier.'));
    const progress = data.index_progress;
    if (progress?.archives > 0) details.append(element('p', progress.completed + ' / ' + progress.archives +
      ' archives examinées' + (Number.isFinite(progress.articles) ? ' · ' + progress.articles + ' articles indexés' : '') + '.'));
    if (progress?.videos > 0) details.append(element('p', progress.downloaded + ' / ' + progress.videos +
      ' vidéos ajoutées · ' + progress.skipped + ' déjà présentes · ' + progress.errors + ' en erreur.'));
    return details;
  }


  function message(text) {
    $('work-queue-error').hidden = !text;
    $('work-queue-error').textContent = text;
    if (text && page.hidden) toast(text);
  }

  async function command(path, body, focus) {
    if (pending || connection !== 'ready') return;
    const epoch = generation;
    const preview = document.activeElement?.closest('.work-queue-nav');
    pending = true;
    draw();
    try {
      await api('/work-queue' + path, body);
      if (epoch === generation) message('');
    } catch (error) {
      if (epoch === generation) message(error.message);
    } finally {
      if (fetching) await fetching;
      await refresh();
      pending = false;
      draw();
    }
    if (focus && epoch === generation) {
      const within = preview || page;
      if (!preview && page.hidden) return;
      const button = [...within.querySelectorAll('button[data-work-control]')]
        .find(control => control.dataset.workControl === focus && !control.disabled);
      if (preview) preview.querySelector('.work-queue-link').focus({preventScroll: true});
      (button || (!preview && $('work-queue-state')))?.focus?.({preventScroll: true});
    }
  }

  function move(id, target, after) {
    return command('/' + encodeURIComponent(id) + '/move', {target, after}, id + ':move');
  }

  function reveal(id) {
    const target = document.getElementById(id);
    if (!target) return;
    for (let node = target; node; node = node.parentElement?.closest('details')) if (node.tagName === 'DETAILS') node.open = true;
    target.scrollIntoView({block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
  }

  // People using the portal may know nothing about computers: say plainly what to do next.
  function nextStep(job) {
    const box = element('div', undefined, 'work-queue-next-step');
    box.append(element('strong', 'Que faire ?'));
    const fallback = job.retry
      ? 'Cliquez sur « ' + (job.retry_label || 'Réessayer') + ' ». Si l’erreur revient, notez le message en rouge et demandez de l’aide à la personne qui s’occupe de l’appareil.'
      : job.href
        ? 'Cliquez sur le titre de la tâche pour ouvrir sa page et la relancer. Si l’erreur revient, notez le message en rouge et demandez de l’aide à la personne qui s’occupe de l’appareil.'
        : 'Notez le message en rouge et demandez de l’aide à la personne qui s’occupe de l’appareil.';
    box.append(element('p', job.help || fallback));
    return box;
  }

  function taskCard(job, movable) {
    const node = element('li', undefined, 'work-queue-card');
    node.dataset.status = job.status;
    if (job.next) node.dataset.next = '';
    node.classList.toggle('work-queue-problem', failed(job));
    node.classList.toggle('work-queue-held', held(job));
    const main = element('div', undefined, 'work-queue-content');
    const title = element(job.href ? 'a' : 'strong', job.title);
    if (job.href) {
      title.href = job.href;
      title.className = 'work-queue-open';
      title.title = 'Ouvrir la page de cette tâche';
      // Commands often sit in a folded panel: unfold it and bring it into view.
      if (job.focus) title.addEventListener('click', () => setTimeout(() => reveal(job.focus), 250));
    }
    const label = element('span', job.next ? (state.paused ? 'À la reprise' : 'Ensuite') : statusLabel(job), 'work-queue-status');
    main.append(title, element('p', [job.type, job.model].filter(Boolean).join(' · '), 'work-queue-meta'));
    if (job.priority) main.append(element('span', 'Question prioritaire', 'work-queue-priority'));
    // A failed card already shows « En erreur » and the real message: skip the generic stage.
    if (job.stage && !(failed(job) && job.error)) main.append(element('p', job.stage, 'work-queue-meta'));
    const hostBytes = job.preparation?.total_bytes > 0;
    const total = hostBytes ? job.preparation.total_bytes : job.total;
    const done = hostBytes ? job.preparation.verified_bytes : job.done;
    if (total > 0 && Number.isFinite(done)) {
      const percent = Math.round(100 * Math.min(total, done) / total);
      const progress = element('progress');
      progress.max = total;
      progress.value = done;
      progress.setAttribute('aria-label', 'Avancement de ' + job.title);
      const row = element('div', undefined, 'work-queue-progress');
      const amount = hostBytes ? percent + ' % vérifiés'
        : job.kind === 'speech' || job.unit === 'percent' ? percent + ' %' : done + ' / ' + total;
      row.append(progress, element('span', amount));
      main.append(row);
    }
    if (job.error && job.error !== job.stage) main.append(element('p', job.error, failed(job) ? 'work-queue-error-text' : 'work-queue-meta'));
    if (failed(job) && !job.error && !job.stage && !job.failure_count) {
      main.append(element('p', 'Le détail de cette erreur est indisponible.', 'work-queue-meta'));
    }
    if (failed(job) || job.status === 'interrupted') main.append(nextStep(job));
    if (job.preparation) main.append(preparationDetails(job));
    if (job.failure_count) {
      const details = element('details', undefined, 'work-queue-failures');
      details.dataset.queueDetails = JSON.stringify([job.id, 'failures']);
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
    if (movable.length > 1 && movable.includes(job)) {
      tools.append(dragHandle(job, movable, move, connection !== 'ready' || pending, draw));
    }
    if (job.pausable) {
      const id = job.id + ':pause';
      const control = button('Mettre en pause', () => command('/' + encodeURIComponent(job.id) + '/pause', {operation_id: job.operation_id}, id));
      control.setAttribute('aria-label', 'Mettre en pause ' + job.title);
      control.dataset.workControl = id;
      control.disabled = connection !== 'ready' || pending;
      tools.append(control);
    }
    if (job.retry) {
      const id = job.id + ':retry';
      const control = button(job.retry_label || (held(job) ? 'Reprendre' : 'Réessayer'), () => command('/' + encodeURIComponent(job.id) + '/retry', {}, id));
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
    if (page.hidden || page.querySelector('.work-queue-dragging')) return;
    const summary = $('work-queue-state');
    summary.tabIndex = -1;
    const status = $('work-queue-freshness');
    status.hidden = !state || !freshness[connection];
    status.textContent = status.hidden ? '' : freshness[connection] +
      (observedAt ? ' Dernière actualisation à ' + observedAt.toLocaleTimeString('fr-FR') + '.' : '');
    $('work-queue-host-notice').hidden = state?.preparations_available !== false;
    filters.hidden = !state;
    const toggle = $('work-queue-pause');
    toggle.hidden = !state || !admin;
    toggle.disabled = connection !== 'ready' || pending;
    if (!state) {
      $('work-queue-help').hidden = true;
      summary.textContent = freshness[connection] || 'Chargement du suivi…';
      return;
    }
    const signature = JSON.stringify([state, admin, connection, pending, filter]);
    if (signature === lastPage) return;
    lastPage = signature;
    const next = state.jobs.filter(waiting);
    const active = state.jobs.filter(job => job.status === 'running');
    const failures = state.jobs.filter(failed);
    const unknown = state.jobs.filter(job => job.status === 'unknown');
    const pausedJobs = state.jobs.filter(held);
    const partial = state.jobs.filter(job => !failed(job) && job.failure_count > 0);
    const counts = [
      active.length && plural(active.length, 'tâche en cours', 'tâches en cours'),
      next.length && plural(next.length, 'tâche en attente', 'tâches en attente'),
      failures.length && plural(failures.length, 'erreur', 'erreurs'),
      partial.length && plural(partial.length, 'lot avec des lignes à vérifier', 'lots avec des lignes à vérifier'),
      unknown.length && plural(unknown.length, 'état à vérifier', 'états à vérifier'),
      pausedJobs.length && plural(pausedJobs.length, 'tâche à reprendre', 'tâches à reprendre')
    ].filter(Boolean);
    const activity = counts.join(' · ') || (state.running ? 'Un travail est en cours sur l’appareil.' : 'Aucune tâche active.');
    summary.textContent = (state.paused ? 'File en pause. ' : '') + activity;
    toggle.textContent = state.paused ? 'Reprendre la file' : 'Mettre en pause';
    const host = $('work-queue-groups');
    const previous = document.activeElement?.dataset.workControl;
    const focusedDetails = document.activeElement?.matches('details[data-queue-details] > summary')
      ? document.activeElement.parentElement.dataset.queueDetails : null;
    const expanded = new Set(Array.from(host.querySelectorAll('details[data-queue-details][open]'), item => item.dataset.queueDetails));
    const openHelp = new Set(Array.from(host.querySelectorAll('[data-lane] .queue-help[open]'), item => item.closest('[data-lane]').dataset.lane));
    const focusedLane = document.activeElement?.closest('.queue-help')?.closest('[data-lane]')?.dataset.lane;
    const history = state.jobs.filter(job => !waiting(job) && !['running', 'unknown'].includes(job.status) &&
      !failed(job) && !held(job) && !job.failure_count)
      .sort((a, b) => (b.updated || 0) - (a.updated || 0)).slice(0, 30);
    for (const control of filters.querySelectorAll('button')) {
      control.setAttribute('aria-pressed', String(control.dataset.queueFilter === filter));
    }
    host.replaceChildren();
    let reorderable = false;
    let focusedSummary;
    function group(heading, jobs, container, className = 'work-queue-group') {
      if (!jobs.length) return;
      const section = element('section', undefined, className);
      const list = element('ul');
      const movable = {priority: [], standard: []};
      for (const job of jobs) {
        if (job.movable) movable[job.priority ? 'priority' : 'standard'].push(job);
      }
      reorderable ||= movable.priority.length > 1 || movable.standard.length > 1;
      for (const job of jobs) {
        const card = taskCard(job, movable[job.priority ? 'priority' : 'standard']);
        for (const details of card.querySelectorAll('details[data-queue-details]')) {
          details.open = expanded.has(details.dataset.queueDetails);
          if (details.dataset.queueDetails === focusedDetails) focusedSummary = details.querySelector('summary');
        }
        list.append(card);
      }
      if (heading) section.append(element('h2', heading));
      section.append(list);
      container.append(section);
    }

    if (filter === 'history') {
      group('Historique récent', history, host);
      if (!history.length) host.append(element('p', 'Aucun travail récent dans l’historique.', 'work-queue-empty'));
      $('work-queue-help').hidden = true;
      focusedSummary?.focus({preventScroll: true});
      return;
    }
    group('En erreur', failures, host);
    group('À vérifier', unknown, host);
    group('À reprendre', pausedJobs, host);
    group('Inventaires terminés', state.jobs.filter(job => job.status === 'partial'), host);
    const completedWithIssues = partial.filter(job => !waiting(job) && job.status !== 'running' && !held(job));
    group('Lots avec des lignes à vérifier', completedWithIssues, host);
    const laneList = lanes(state);
    const idle = !failures.length && !unknown.length && !pausedJobs.length && !completedWithIssues.length &&
      !state.jobs.some(job => job.status === 'partial') &&
      laneList.every(lane => !lane.running && !lane.active.length && !lane.waiting.length);
    if (idle) {
      /* Un seul état vide plutôt qu'un encadré vide par créneau. */
      const empty = element('div', undefined, 'work-queue-idle');
      empty.append(element('strong', 'Rien en cours'),
        element('p', 'Les téléchargements, les préparations et les réponses de l’assistant apparaîtront ici pendant leur traitement. Vous pouvez utiliser SetupSurvie normalement.'));
      host.append(empty);
      $('work-queue-help').hidden = true;
      focusedSummary?.focus({preventScroll: true});
      return;
    }
    for (const lane of laneList) {
      const section = element('section', undefined, 'work-queue-lane');
      section.dataset.lane = lane.id;
      const header = element('div', undefined, 'work-queue-lane-heading');
      const heading = element('div', undefined, 'work-queue-lane-title');
      const hint = help('Que signifie « ' + lane.title + ' » ?', laneHelp[lane.id]);
      hint.open = openHelp.has(lane.id);
      heading.append(element('h2', lane.title), hint);
      header.append(heading);
      section.append(header);
      if (lane.running && !lane.active.length) section.append(element('p', 'Un travail utilise ce créneau.', 'work-queue-lane-rule'));
      if (!lane.running && !lane.active.length && !lane.waiting.length) section.append(element('p', 'Aucun travail en cours ou en attente.', 'work-queue-lane-rule'));
      group(null, [...lane.active, ...lane.waiting], section, 'work-queue-lane-jobs');
      host.append(section);
    }

    $('work-queue-help').hidden = !reorderable;
    focusedSummary?.focus({preventScroll: true});
    if (focusedLane) host.querySelector('[data-lane="' + focusedLane + '"] .queue-help summary')?.focus({preventScroll: true});
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
      document.dispatchEvent(new CustomEvent('survie:work-queue', {detail: state}));
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
    document.dispatchEvent(new CustomEvent('survie:work-queue', {detail: null}));
    message('');
    lastPage = '';
    filter = 'current';
    generation++;
    $('work-queue-groups').replaceChildren();
    draw();
    if (fetching) fetching.then(refresh);
    else refresh();
  });
  document.addEventListener('survie:route', () => { draw(); refresh(); });
  document.addEventListener('survie:translation-command', refresh);
  document.addEventListener('survie:work-accepted', async () => {
    if (fetching) await fetching;
    refresh();
  });
  document.addEventListener('visibilitychange', refresh);
  window.addEventListener('online', refresh);
  window.addEventListener('offline', () => {
    if (!S.user) return;
    connection = state ? 'stale' : 'unavailable';
    draw();
  });
  WorkQueuePreview.current = () => state;
  draw();
  setInterval(refresh, 3500);
})();
