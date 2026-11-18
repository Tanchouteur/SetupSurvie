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
      const entries = [...active, ...queued].slice(0, 4).map(job => {
        const row = make('li');
        row.append(make('span', job.status === 'running' ? 'En cours' : 'En attente', 'work-queue-meta'),
          make('strong', job.title));
        return row;
      });
      if (!entries.length) entries.push(make('li', 'Aucun travail en attente.'));
      if (errors) entries.push(make('li', errors + (errors === 1 ? ' tâche à vérifier.' : ' tâches à vérifier.'), 'work-queue-error-text'));
      list.append(...entries);
      action.hidden = !admin || !toggle;
      action.textContent = state.paused ? 'Reprendre la file' : 'Mettre en pause';
    }
    return {draw};
  }

  window.WorkQueuePreview = {mount, waiting, failed};
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
