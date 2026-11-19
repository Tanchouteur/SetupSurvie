/* Queue entry shared by the portal header and the separate map page. */
(() => {
  const make = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const waiting = job => ['queued', 'preparing'].includes(job.status);
  const failed = job => ['error', 'failed', 'interrupted', 'incomplete', 'paused', 'stopped'].includes(job.status);

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
    link.append(icon, count);
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

    function draw(state, {admin = false, current = false} = {}) {
      host.dataset.state = '';
      count.textContent = '';
      action.hidden = true;
      list.replaceChildren();
      link.setAttribute('aria-label', 'File d’attente');
      if (current) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
      if (!state) return;
      const queued = state.jobs.filter(waiting);
      const active = state.jobs.filter(job => job.status === 'running');
      const errors = state.jobs.filter(failed).length;
      host.dataset.state = state.paused ? 'paused' : errors ? 'attention' : '';
      count.textContent = queued.length + active.length;
      link.setAttribute('aria-label', 'File d’attente · ' + queued.length + ' en attente' +
        (state.paused ? ' · en pause' : '') + (errors ? ' · ' + errors + ' à vérifier' : ''));
      if (mobile) return;
      const entries = lanes(state).filter(lane => lane.id === 'ai' || lane.running || lane.waiting.length).map(lane => {
        const row = make('li', '', 'work-queue-preview-lane');
        row.append(make('strong', lane.title, 'work-queue-lane-title'));
        if (lane.active.length) row.append(make('span', 'En cours · ' + lane.active[0].title, 'work-queue-preview-task'));
        else if (lane.running) row.append(make('span', 'En cours sur l’appareil', 'work-queue-meta'));
        else if (lane.id === 'ai' && !state.paused) row.append(make('span', 'Créneau IA libre', 'work-queue-meta'));
        const next = lane.waiting.find(job => job.next);
        if (next) row.append(make('span', 'Ensuite · ' + next.title, 'work-queue-preview-task'));
        if (lane.waiting.length > (next ? 1 : 0)) {
          row.append(make('span', lane.waiting.length + ' en attente', 'work-queue-meta'));
        }
        return row;
      });
      if (errors) entries.push(make('li', errors + (errors === 1 ? ' tâche à vérifier.' : ' tâches à vérifier.'), 'work-queue-error-text'));
      list.append(...entries);
      action.hidden = !admin || !toggle;
      action.textContent = state.paused ? 'Reprendre la file' : 'Mettre en pause';
    }
    return {draw};
  }

  window.WorkQueuePreview = {mount, waiting, failed, lanes};
  const map = document.querySelector('.map-site-nav');
  if (!map) return;
  const fetchQueue = async () => {
    if (document.hidden) return;
    try {
      const response = await fetch('/api/work-queue', {credentials: 'same-origin'});
      preview.draw(response.ok ? await response.json() : null);
    } catch {
      preview.draw(null);
    }
  };
  const preview = mount(map, {href: '/nouveau/#/file', refresh: fetchQueue});
  document.addEventListener('survie:auth', fetchQueue);
  document.addEventListener('visibilitychange', fetchQueue);
  fetchQueue();
  setInterval(fetchQueue, 7000);
})();
