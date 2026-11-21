/* Updates and complete copies in the portal.

   - Status: /catalog/maintenance.json, served by Caddy or, while every container is
     stopped, by scripts/maintenance_site.py. The home page shows the tracking.
   - While the site is unavailable, open tabs switch to a maintenance mode: only the
     home page stays reachable; the previous page is remembered for afterwards.
   - Famille profile: the version number shows the last update check on hover and
     becomes a « Mettre à jour » button only when a newer version exists. */
(() => {
  const tracker = window.SurvieMaintenance;
  if (!tracker) return;
  const RETURN = 'survie-maintenance-return', LAUNCHED = 'survie-update-launched', ACK = 'survie-maintenance-ack';
  const RESULT_TTL = 24 * 3600;
  const session = {
    get: key => { try { return sessionStorage.getItem(key); } catch (_) { return null; } },
    set: (key, value) => { try { sessionStorage.setItem(key, value); } catch (_) {} },
    drop: key => { try { sessionStorage.removeItem(key); } catch (_) {} },
  };
  const acknowledged = () => { try { return localStorage.getItem(ACK); } catch (_) { return null; } };
  const acknowledge = id => { try { localStorage.setItem(ACK, id); } catch (_) {} };
  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  };

  /* ---- Tracking on the home page ------------------------------------------------ */
  const panel = make('section', 'maintenance-home');
  panel.id = 'maintenance-home';
  panel.setAttribute('aria-live', 'polite');
  panel.hidden = true;
  $('view-home').prepend(panel);

  const banner = make('div', 'maintenance-banner');
  banner.id = 'maintenance-banner';
  banner.setAttribute('role', 'status');
  banner.hidden = true;
  const bannerText = make('span'), bannerLink = make('a', '', 'Voir le suivi');
  bannerLink.href = '#/accueil';
  banner.append(bannerText, bannerLink);
  $('main').before(banner);

  let last = null, connection = 'ready', timer = null, failures = 0, mode = false;

  function fresh(status) {
    return Date.now() / 1000 - (Number(status.updated) || 0) < RESULT_TTL;
  }

  function enterMode() {
    if (mode) return;
    mode = true;
    document.body.classList.add('maintenance-mode');
    const hash = location.hash;
    if (hash && !/^#\/?(accueil|home)?$/.test(hash)) session.set(RETURN, hash);
    if (S.view !== 'home') window.view('home');
  }

  function leaveMode() {
    if (!mode) return;
    mode = false;
    document.body.classList.remove('maintenance-mode');
  }

  document.addEventListener('survie:route', event => {
    if (!mode || event.detail?.section === 'accueil') return;
    setTimeout(() => {
      window.view('home');
      toast('Maintenance en cours : le suivi reste affiché sur l’accueil.');
    });
  });

  function resultActions(status) {
    const actions = panel.maintenanceParts.actions;
    actions.replaceChildren();
    if (status.state === 'running' && !tracker.stale(status)) return;
    const back = session.get(RETURN);
    if (back) {
      const resume = make('button', '', 'Revenir à la page précédente');
      resume.type = 'button';
      resume.onclick = () => { session.drop(RETURN); close(status); location.hash = back; };
      actions.append(resume);
    }
    const dismiss = make('button', back ? 'secondary' : '', 'Fermer ce message');
    dismiss.type = 'button';
    dismiss.onclick = () => { session.drop(RETURN); close(status); };
    actions.append(dismiss);
  }

  function close(status) {
    acknowledge(status.id || '');
    panel.hidden = true;
  }

  function show(status) {
    // A status left « running » by a power cut must never lock the portal.
    const running = status.state === 'running' && !tracker.stale(status);
    const launchedHere = session.get(LAUNCHED) === status.id;
    // Results, and a stale « running » left by a power cut, stay until closed (24 h at most).
    const dismissed = acknowledged() === status.id;
    const visible = running || (fresh(status) && !dismissed && (status.state !== 'current' || launchedHere));
    panel.hidden = !visible;
    if (visible) {
      tracker.render(panel, status, {connection});
      resultActions(status);
    }
    const unavailable = running && status.unavailable;
    if (unavailable || (running && connection === 'lost' && last?.unavailable)) enterMode();
    else leaveMode();
    banner.hidden = !running || S.view === 'home';
    bannerText.textContent = `${tracker.kinds[status.kind] || 'Maintenance'} en cours · ${status.title || ''} `;
    if (!running && launchedHere) session.drop(LAUNCHED);
    reloadAfterUpdate(status);
  }

  /* The open tab still runs the old scripts after an update: load the new ones once. */
  function reloadAfterUpdate(status) {
    if (status.state !== 'completed' || status.kind === 'transfer' || !status.available) return;
    const loaded = S.status?.version;
    const key = 'survie-maintenance-reloaded:' + status.id;
    if (!loaded || loaded === status.available || session.get(key) || !fresh(status)) return;
    session.set(key, '1');
    location.reload();
  }

  async function poll() {
    clearTimeout(timer);
    try {
      const {status} = await tracker.fetchStatus();
      failures = 0;
      connection = 'ready';
      if (status) {
        last = status;
        show(status);
      } else {
        last = null;
        panel.hidden = true;
        banner.hidden = true;
        leaveMode();
      }
    } catch (_) {
      failures += 1;
      if (last?.state === 'running') {
        connection = failures > 1 ? 'lost' : 'ready';
        show(last);
      }
    }
    const busy = (last?.state === 'running' && !tracker.stale(last)) || session.get(LAUNCHED);
    timer = setTimeout(poll, busy ? 2000 : 15000);
  }
  document.addEventListener('survie:view', () => { if (last) banner.hidden = last.state !== 'running' || S.view === 'home'; });
  document.addEventListener('visibilitychange', () => { if (!document.hidden) poll(); });

  /* ---- Navigation entry and confirmation (Famille profile, Windows) ------------- */
  let update = null, updateTimer = null, checkingSince = 0;
  const entries = [];
  const dateFormat = new Intl.DateTimeFormat('fr-FR', {dateStyle: 'medium', timeStyle: 'short'});

  function checkedText(value) {
    if (!value?.checked_at) return 'Aucune vérification enregistrée.';
    const minutes = Math.round((Date.now() / 1000 - value.checked_at) / 60);
    const ago = minutes < 1 ? 'à l’instant' : minutes < 60 ? `il y a ${minutes} min` : `il y a ${Math.round(minutes / 60)} h`;
    const label = value.error ? 'Dernière tentative' : 'Dernière vérification';
    return `${label} : ${dateFormat.format(new Date(value.checked_at * 1000))} (${ago}).`;
  }

  function headline(value) {
    if (value.running) return 'Mise à jour en cours : suivez-la sur l’accueil.';
    if (value.error) return value.update_available
      ? `Dernière version repérée : ${value.available}. La vérification a échoué.`
      : `Version ${value.installed} installée. La vérification a échoué.`;
    if (value.update_available) return `Nouvelle version ${value.available} disponible.`;
    return value.checked_at
      ? `Version ${value.installed} installée, à jour selon la dernière vérification.`
      : `Version ${value.installed} installée. Les mises à jour restent à vérifier.`;
  }

  /* The version number (top left, and in the phone top bar) is the entry point:
     hovering it shows the last check; it becomes a button only when a newer
     version exists (Louis, 20 November 2026). */
  function mountEntry(version, mobile) {
    if (!version) return;
    const host = make('div', 'update-nav ' + (mobile ? 'update-nav-mobile' : 'update-nav-desktop'));
    host.hidden = true;
    const button = make('button', 'update-nav-button');
    button.type = 'button';
    button.setAttribute('aria-haspopup', 'dialog');
    const current = make('span', 'update-nav-version');
    const icon = make('span', 'update-nav-icon', '↻');
    icon.setAttribute('aria-hidden', 'true');
    const label = make('span', 'update-nav-label', 'Mettre à jour');
    const dot = make('span', 'update-nav-dot');
    dot.setAttribute('aria-hidden', 'true');
    button.append(current, icon, label, dot);
    button.onclick = openDialog;
    host.append(button);
    const preview = make('div', 'update-nav-preview');
    const title = make('strong', '', 'Mises à jour de SetupSurvie');
    const state = make('p', 'update-nav-state'), checked = make('p', 'update-nav-checked'), error = make('p', 'update-nav-error');
    const actions = make('div', 'update-nav-actions');
    const refresh = make('button', 'secondary', 'Vérifier maintenant');
    refresh.type = 'button';
    refresh.onclick = check;
    const install = make('button', '', 'Mettre à jour…');
    install.type = 'button';
    install.onclick = openDialog;
    actions.append(refresh, install);
    preview.append(title, state, checked, error, actions);
    if (!mobile) host.append(preview);
    // The brand is a link: the entry sits beside it, never inside it.
    (version.closest('.brand') || version).after(host);
    entries.push({host, version, button, current, dot, state, checked, error, refresh, install});
  }
  mountEntry(document.querySelector('.brand .ds-nav-version'), false);
  mountEntry($('breadcrumb').parentElement.querySelector('.ds-nav-version'), true);

  function drawEntries() {
    const visible = !!update?.supported && S.user?.role === 'admin';
    for (const entry of entries) {
      entry.host.hidden = !visible;
      entry.version.classList.toggle('update-nav-replaced', visible);
      if (!visible) continue;
      const available = !!update.update_available;
      entry.host.classList.toggle('update-available', available);
      entry.current.textContent = update.installed || S.status?.version || '';
      entry.dot.hidden = !available;
      entry.button.setAttribute('aria-label', available
        ? `Mettre à jour : version ${update.available} disponible`
        : `Version ${entry.current.textContent} · état des mises à jour`);
      entry.state.textContent = headline(update);
      entry.checked.textContent = update.checking ? 'Vérification en cours…' : checkedText(update);
      entry.error.textContent = update.error || '';
      entry.error.hidden = !update.error;
      entry.refresh.disabled = !!update.checking;
      entry.install.hidden = !available || update.running;
    }
    drawDialog();
  }

  async function loadUpdate() {
    clearTimeout(updateTimer);
    if (S.user?.role !== 'admin') {
      update = null;
      drawEntries();
      return;
    }
    try {
      update = await api('/maintenance/update');
    } catch (_) {
      update = update && {...update, error: 'État des mises à jour momentanément indisponible.'};
    }
    drawEntries();
    const checking = update?.checking && Date.now() - checkingSince < 300000;
    updateTimer = setTimeout(loadUpdate, checking ? 3000 : 600000);
  }

  async function check() {
    try {
      checkingSince = Date.now();
      const result = await api('/maintenance/update/check', {});
      if (!result.accepted && update) toast('Une vérification vient d’être faite. Réessayez dans une minute.');
      if (update) update = {...update, checking: !!result.accepted};
      drawEntries();
      setTimeout(loadUpdate, 1500);
    } catch (error) {
      toast(error.message);
    }
  }

  /* Confirmation dialog: what changes, what stops, and the launch itself. */
  const dialog = make('dialog', 'update-dialog');
  dialog.id = 'update-dialog';
  dialog.setAttribute('aria-labelledby', 'update-dialog-title');
  const closeButton = make('button', 'dialog-close', '×');
  closeButton.type = 'button';
  closeButton.setAttribute('aria-label', 'Fermer');
  closeButton.onclick = () => dialog.close();
  const eyebrow = make('div', 'eyebrow', 'MISE À JOUR');
  const heading = make('h2', '', 'Mettre à jour SetupSurvie');
  heading.id = 'update-dialog-title';
  const dialogState = make('p', 'update-dialog-state'), dialogChecked = make('p', 'muted small');
  const dialogError = make('p', 'error');
  dialogError.setAttribute('role', 'alert');
  const changesTitle = make('h3', '', 'Changements prévus');
  const changes = make('ul', 'update-dialog-changes');
  const warning = make('p', 'update-dialog-warning',
    'Pendant la sauvegarde et le redémarrage, SetupSurvie sera indisponible quelques minutes sur tous les appareils. ' +
    'Une réponse de l’assistant en cours sera interrompue. Vos conversations, documents et réglages sont sauvegardés avant le remplacement ; ' +
    'en cas de problème, l’ancienne version est remise en service. Le suivi s’affiche sur l’accueil.');
  const queueNotice = make('p', 'update-dialog-queue');
  queueNotice.hidden = true;
  const dialogActions = make('div', 'update-dialog-actions');
  const launch = make('button', '', 'Lancer la mise à jour');
  launch.type = 'button';
  const recheck = make('button', 'secondary', 'Vérifier maintenant');
  recheck.type = 'button';
  recheck.onclick = check;
  const later = make('button', 'quiet', 'Plus tard');
  later.type = 'button';
  later.onclick = () => dialog.close();
  dialogActions.append(launch, recheck, later);
  dialog.append(closeButton, eyebrow, heading, dialogState, dialogChecked, dialogError, changesTitle, changes,
    warning, queueNotice, dialogActions);
  document.body.append(dialog);
  let queueBusy = false, launching = false;

  function drawDialog() {
    if (!update) return;
    dialogState.textContent = update.update_available && !update.running
      ? `Version installée ${update.installed} → ${update.error ? 'dernière version repérée' : 'nouvelle version'} ${update.available}.`
      : headline(update);
    dialogChecked.textContent = update.checking ? 'Vérification en cours…' : checkedText(update);
    const transferNotice = update.transfer_in_progress
      ? 'Un transfert est en cours. La mise à jour attendra sa fin.' : '';
    dialogError.textContent = [update.error, transferNotice].filter(Boolean).join(' ');
    dialogError.hidden = !dialogError.textContent;
    const items = update.update_available ? update.changes || [] : [];
    changes.replaceChildren(...items.map(text => make('li', '', text)));
    changesTitle.hidden = changes.hidden = !items.length;
    const ready = update.update_available && !update.running && !update.transfer_in_progress;
    warning.hidden = !ready;
    launch.hidden = !ready;
    launch.disabled = launching;
    recheck.disabled = !!update.checking;
  }

  async function openDialog() {
    drawDialog();
    if (!dialog.open) dialog.showModal();
    queueBusy = false;
    queueNotice.hidden = true;
    try {
      const queue = await api('/work-queue');
      const active = (queue.jobs || []).filter(job => ['running', 'preparing'].includes(job.status));
      queueBusy = !!(queue.running || active.length);
      if (queueBusy) {
        queueNotice.textContent = queue.paused
          ? 'La file d’attente est en pause. La mise à jour attendra l’arrêt des travaux déjà commencés (cinq minutes au plus).'
          : 'Des travaux sont en cours : la file d’attente sera mise en pause et la mise à jour attendra leur arrêt (cinq minutes au plus). Reprenez la file ensuite.';
        queueNotice.hidden = false;
      }
    } catch (_) {
      // The updater checks the queue again by itself before stopping anything.
    }
  }

  launch.onclick = async () => {
    if (launching) return;
    launching = true;
    drawDialog();
    try {
      const result = await api('/maintenance/update/start', {confirmed: true, pause_queue: queueBusy});
      if (result.id) session.set(LAUNCHED, result.id);
      dialog.close();
      window.view('home');
      poll();
      loadUpdate();
    } catch (error) {
      dialogError.textContent = error.message;
      dialogError.hidden = false;
    } finally {
      launching = false;
      drawDialog();
    }
  };

  document.addEventListener('survie:auth', loadUpdate);
  setTimeout(loadUpdate, 1500);
  poll();
})();
