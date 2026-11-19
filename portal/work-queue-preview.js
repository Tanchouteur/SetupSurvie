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
        return {id, title, active, waiting: jobs.filter(waiting), running: !!active.length || !!state.lanes?.[id]?.running};
      });
  }

  function aiBusy(state) {
    const lane = state?.lanes?.ai;
    return !!state && (state.paused || lane?.running || lane?.waiting ||
      state.jobs.some(job => (job.lane || 'ai') === 'ai' && (waiting(job) || job.status === 'running')));
  }

  function translationLabels(busy, start, resume, startLabel, resumeLabel) {
    const label = 'Ajouter à la file d’attente';
    start.textContent = busy ? label : startLabel;
    resume.textContent = busy ? label : resumeLabel;
  }

  function dragHandle(job, jobs, move, disabled, redraw) {
    const control = make('button', '', 'work-queue-handle');
    control.type = 'button';
    control.disabled = disabled;
    control.dataset.workControl = job.id + ':move';
    control.setAttribute('aria-label', 'Déplacer ' + job.title);
    control.setAttribute('aria-description', 'Glissez la poignée ou utilisez les flèches haut et bas du clavier.');
    control.title = 'Glisser pour déplacer · flèches haut et bas au clavier';
    control.addEventListener('keydown', event => {
      if (!['ArrowUp', 'ArrowDown'].includes(event.key)) return;
      event.preventDefault();
      const after = event.key === 'ArrowDown';
      const target = jobs[jobs.indexOf(job) + (after ? 1 : -1)];
      if (target) move(job.id, target.id, after);
    });
    let id, source, target, after, start, frame, point, lane, ghost, lifted, peers;
    const locate = () => {
      target?.classList.remove('work-queue-drop-before', 'work-queue-drop-after');
      if (lane) {
        const list = source.parentElement;
        const top = list.getBoundingClientRect().top;
        // Read layout positions so the sliding cards do not change the drop target.
        target = document.elementFromPoint(point.x, point.y)?.closest('.work-queue-preview-lane') === lane
          ? peers.find(card => card !== source && point.y >= top + card.offsetTop &&
            point.y < top + card.offsetTop + card.offsetHeight)
          : null;
        if (target) after = point.y >= top + target.offsetTop + target.offsetHeight / 2;
        const from = peers.indexOf(source);
        const to = target ? peers.indexOf(target) + Number(after) : from;
        const displacement = source.offsetHeight + (parseFloat(getComputedStyle(list).rowGap) || 0);
        peers.forEach((card, index) => {
          if (card === source) return;
          const offset = index >= to && index < from ? displacement
            : index > from && index < to ? -displacement : 0;
          card.style.setProperty('--work-queue-shift', offset + 'px');
        });
      } else {
        const card = document.elementFromPoint(point.x, point.y)?.closest('[data-work-id]');
        target = card !== source && card?.parentElement === source.parentElement &&
          jobs.some(item => item.id === card.dataset.workId) ? card : null;
        if (target) {
          const rect = target.getBoundingClientRect();
          after = point.y >= rect.top + rect.height / 2;
        }
      }
      target?.classList.add(after ? 'work-queue-drop-after' : 'work-queue-drop-before');
    };
    const scroll = () => {
      const panel = source.closest('.work-queue-preview-sections');
      const bounds = panel?.getBoundingClientRect() || {top: 0, bottom: window.innerHeight};
      if (point.x >= (bounds.left ?? 0) && point.x <= (bounds.right ?? window.innerWidth) &&
          point.y >= bounds.top && point.y <= bounds.bottom) {
        const step = point.y < bounds.top + 42 ? -12 : point.y > bounds.bottom - 42 ? 12 : 0;
        if (step) {
          (panel || window).scrollBy(0, step);
          locate();
        }
      }
      frame = requestAnimationFrame(scroll);
    };
    control.addEventListener('pointerdown', event => {
      if (!event.isPrimary || event.button !== 0 || id !== undefined) return;
      source = control.closest('[data-work-id]');
      id = event.pointerId;
      start = {x: event.clientX, y: event.clientY};
      source.classList.add('work-queue-dragging');
      control.setPointerCapture(id);
    });
    control.addEventListener('pointermove', event => {
      if (event.pointerId !== id) return;
      const x = event.clientX - start.x;
      const y = event.clientY - start.y;
      if (!frame && Math.hypot(x, y) < 5) return;
      point = {x: event.clientX, y: event.clientY};
      if (!frame) {
        lane = source.closest('.work-queue-preview-lane');
        if (lane) {
          peers = [...source.parentElement.children].filter(card => jobs.some(item => item.id === card.dataset.workId));
          lifted = source.getBoundingClientRect();
          ghost = source.cloneNode(true);
          ghost.classList.remove('work-queue-dragging');
          ghost.classList.add('work-queue-drag-ghost');
          ghost.removeAttribute('data-work-id');
          ghost.inert = true;
          ghost.style.width = lifted.width + 'px';
          document.body.append(ghost);
          lane.classList.add('work-queue-drag-lane');
        }
        frame = requestAnimationFrame(scroll);
      }
      if (ghost) {
        ghost.style.transform = `translate3d(${lifted.left + x}px, ${lifted.top + y}px, 0)`;
      }
      locate();
    });
    const finish = event => {
      if (event.pointerId !== id) return;
      if (frame && event.type === 'pointerup') {
        point = {x: event.clientX, y: event.clientY};
        locate();
      }
      const destination = event.type === 'pointerup' && target?.dataset.workId;
      cancelAnimationFrame(frame);
      frame = undefined;
      id = undefined;
      ghost?.remove();
      ghost = null;
      source.classList.remove('work-queue-dragging');
      lane?.classList.remove('work-queue-drag-lane');
      peers?.forEach(card => card.style.removeProperty('--work-queue-shift'));
      lane = null;
      peers = null;
      target?.classList.remove('work-queue-drop-before', 'work-queue-drop-after');
      target = null;
      if (destination) move(job.id, destination, after);
      redraw();
    };
    control.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || id === undefined) return;
      const pointerId = id;
      finish({pointerId});
      if (control.hasPointerCapture(pointerId)) control.releasePointerCapture(pointerId);
    });
    for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) control.addEventListener(name, finish);
    return control;
  }

  function mount(container, {href, mobile = false, refresh, toggle, move}) {
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
    const heading = make('div', '', 'work-queue-preview-heading');
    const open = make('a', 'Ouvrir la file');
    open.href = href;
    if (href.startsWith('#')) open.dataset.route = 'file';
    const controls = make('div', '', 'work-queue-preview-controls');
    const action = make('button', '', 'secondary work-queue-preview-toggle');
    action.type = 'button';
    action.hidden = true;
    controls.append(action, open);
    heading.append(make('strong', 'File d’attente'), controls);
    const list = make('div', '', 'work-queue-preview-sections');
    let signature, lastDraw;
    preview.append(heading, list);
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
      if (toggle) action.onclick = () => {
        if (action.getAttribute('aria-disabled') !== 'true') toggle();
      };
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
      action.setAttribute('aria-disabled', String(connection !== 'ready' || pending));
      if (state) {
        const label = state.paused ? 'Reprendre la file' : 'Mettre en pause';
        action.dataset.paused = String(state.paused);
        action.setAttribute('aria-label', label);
        action.title = label;
      }
      if (mobile) return;
      lastDraw = () => draw(state, {admin, current, connection, pending});
      if (preview.querySelector('.work-queue-dragging')) return;
      const renderKey = JSON.stringify([state, connection, pending]);
      if (renderKey === signature) return;
      signature = renderKey;
      const focused = document.activeElement?.dataset.workControl;
      const entries = [];
      if (freshness[connection]) entries.push(make('p', freshness[connection], 'work-queue-preview-notice'));
      if (state?.paused) entries.push(make('p', 'File en pause', 'work-queue-preview-notice'));
      function section(title, jobs, movable = [], empty = '') {
        const group = make('section', '', 'work-queue-preview-lane');
        group.append(make('h2', title));
        const cards = make('ul');
        for (const job of jobs) {
          const row = make('li', '', 'work-queue-preview-card');
          row.dataset.workId = job.id;
          row.dataset.status = job.status;
          if (job.next) row.dataset.next = '';
          const content = make('div', '', 'work-queue-preview-content');
          const label = job.next ? (state.paused ? 'À la reprise' : 'Ensuite') : statusLabel(job);
          const title = make(job.href ? 'a' : 'strong', job.title, 'work-queue-preview-task');
          if (job.href) title.href = job.href.startsWith('#') ? href.split('#')[0] + job.href : job.href;
          content.append(make('span', label + (job.type ? ' · ' + job.type : ''), 'work-queue-meta'), title);
          if (job.stage) content.append(make('span', job.stage, 'work-queue-meta'));
          if (job.total > 0 && Number.isFinite(job.done)) {
            const meter = make('progress');
            meter.max = job.total;
            meter.value = job.done;
            meter.setAttribute('aria-label', 'Avancement de ' + job.title);
            content.append(meter);
          }
          const reason = job.error || job.failures?.[0]?.message;
          if (reason) content.append(make('span', reason, 'work-queue-meta'));
          row.append(content);
          const peers = movable.filter(peer => !!peer.priority === !!job.priority);
          if (move && peers.length > 1 && peers.includes(job)) {
            row.append(dragHandle(job, peers, move, connection !== 'ready' || pending, () => lastDraw()));
          }
          cards.append(row);
        }
        if (jobs.length) group.append(cards);
        else group.append(make('p', empty, 'work-queue-meta'));
        entries.push(group);
      }
      if (state) {
        const problems = state.jobs.filter(job => failed(job) ||
          (job.failure_count > 0 && !held(job) && !waiting(job) && job.status !== 'running'));
        if (problems.length) section('À vérifier', problems);
        const pausedJobs = state.jobs.filter(held);
        if (pausedJobs.length) section('À reprendre', pausedJobs);
        const activeLanes = lanes(state).filter(lane => lane.running || lane.waiting.length);
        for (const lane of activeLanes.length ? activeLanes : lanes(state).slice(0, 1)) {
          section(lane.title, [...lane.active, ...lane.waiting], lane.waiting.filter(job => job.movable),
            lane.running ? 'En cours sur l’appareil' : 'Aucune tâche en attente');
        }
      }
      list.replaceChildren(...entries);
      if (focused) [...list.querySelectorAll('[data-work-control]')].find(node => node.dataset.workControl === focused)?.focus({preventScroll: true});
    }
    return {draw};
  }

  window.WorkQueuePreview = {mount, isSnapshot, waiting, failed, held, statusLabel, workLabel, plural, freshness, lanes, aiBusy, translationLabels, dragHandle};
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
  const preview = mount(map, {href: '/#/file', refresh: fetchQueue});
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
