async page => {
  const base = 'http://127.0.0.1:8769';
  const verify = (value, message) => { if (!value) throw Error(message); };
  const tasks = [
    {id: 'active', lane: 'local', kind: 'speech', type: 'Transcription audio', title: 'Audio en cours', model: 'Whisper small · CPU', status: 'running', done: 60000, total: 120000},
    {id: 'question', lane: 'ai', kind: 'chat', type: 'Question à l’assistant', title: 'Comment réparer ce mécanisme ?', model: 'gemma', status: 'queued', priority: true, next: true, movable: true},
    {id: 'document', lane: 'ai', kind: 'translation', type: 'Traduction de document', title: 'Manuel en anglais', model: 'gemma', status: 'queued', done: 3, total: 8, movable: true},
    {id: 'video', lane: 'network', kind: 'youtube', type: 'Téléchargement YouTube', title: 'Liste de vidéos', model: 'yt-dlp', status: 'error',
      error: 'Une vidéo est privée.', preparation: {source: 'host'}, retry: true, failure_count: 1, failures: [{line: 2, message: 'vidéo privée'}]},
    {id: 'second', lane: 'ai', kind: 'translation', type: 'Traduction de document', title: 'Notice de montage', model: 'gemma', status: 'queued', movable: true},
    {id: 'download', lane: 'network', kind: 'youtube', type: 'Téléchargement YouTube', title: 'Vidéos du jardin', status: 'running'}
  ];
  tasks.push({id:'held',lane:'local',kind:'speech',type:'Transcription audio',title:'Audio suspendu',status:'paused',retry:true});
  tasks.push(
    {id:'video-index', lane:'local', kind:'video-index', type:'Indexation vidéo', title:'Inventaire des vidéos et sous-titres', status:'running', stage:'19 vidéos traitées'},
    {id:'archive-video-index', lane:'local', kind:'archive-video-index', type:'Examen des collections', title:'Inventaire des vidéos dans les collections', status:'running', done:2, total:5, pausable:true, operation_id:'a'.repeat(32)}
  );
  let paused = false, unavailable = false, moveRequests = 0;
  await page.route('**/api/work-queue**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (unavailable && request.method() === 'GET') {
      return unavailable === 'invalid' ? route.fulfill({json: {ok: true}})
        : route.fulfill({status: 503, json: {detail: 'Indisponible'}});
    }
    if (path.endsWith('/move')) moveRequests++;
    if (path === '/api/work-queue/pause') paused = request.postDataJSON().paused;
    if (path.endsWith('/archive-video-index/pause') && request.postDataJSON().operation_id === 'a'.repeat(32)) {
      Object.assign(tasks.find(task => task.id === 'archive-video-index'), {status:'paused', pausable:false, retry:true});
    }
    if (path.endsWith('/second/move') && request.postDataJSON().target === 'document' && !request.postDataJSON().after ||
        path.endsWith('/document/move') && request.postDataJSON().target === 'second') {
      [tasks[2], tasks[4]] = [tasks[4], tasks[2]];
    }
    if (path.endsWith('/video/retry')) {
      tasks[3].status = 'queued';
      tasks[3].retry = false;
      tasks[3].error = null;
      tasks[3].failure_count = 0;
    }
    await route.fulfill({json: {paused, running: true, jobs: tasks}});
  });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const profile = await page.request.post(base + '/api/profiles/select', {headers: {Origin: base}, data: {id: 'local-family'}});
  verify(profile.ok(), 'Le profil Famille doit pouvoir piloter la file.');
  await page.setViewportSize({width: 1440, height: 900});
  await page.goto(base + '/#/accueil');
  await page.goto(base + '/#/appareil/ensemble');
  await page.locator('#next-machine-tabs').getByText('File d’attente').click();
  await page.locator('#view-work-queue:visible').waitFor();
  verify(await page.locator('#next-machine-tabs [aria-current=page]').textContent() === 'File d’attente', 'La file doit être l’onglet actif.');
  await page.goto(base + '/#/appareil/activite');
  await page.waitForURL('**/#/file');
  const queuePage = page.locator('#view-work-queue');
  await queuePage.getByLabel('Comment fonctionne la file d’attente ?').press('Enter');
  await queuePage.getByText(/Chaque carte indique/).waitFor();
  await queuePage.getByLabel('Comment fonctionne la file d’attente ?').press('Enter');
  await queuePage.getByRole('button', {name:'Historique récent'}).click();
  await queuePage.getByText('Aucun travail récent dans l’historique.').waitFor();
  const completed = {
    id: 'host:index', lane: 'local', kind: 'index', title: 'Indexation terminée',
    status: 'completed', preparation: {total_bytes: 100, verified_bytes: 100, verified_count: 1, total_count: 1}
  };
  tasks.push(completed);
  const historyCard = queuePage.locator('[data-work-id="host:index"]');
  const historySummary = historyCard.locator('summary');
  await historySummary.press('Enter');
  completed.stage = 'Rapport d’index disponible';
  await historyCard.getByText(completed.stage).waitFor();
  verify(await historySummary.evaluate(node => node.parentElement.open && node === document.activeElement),
    'Le volet technique ouvert doit garder le focus dans l’historique.');
  await queuePage.getByRole('button', {name:'À suivre'}).click();
  const videoCard = queuePage.locator('[data-work-id=video]');
  const technicalDetails = videoCard.locator('details').filter({hasText: 'Détails techniques'});
  const failures = videoCard.locator('details').filter({hasText: 'ligne(s) à vérifier'});
  await failures.locator('summary').press('Enter');
  tasks[3].preparation.pending_errors = 2;
  await page.waitForFunction(() => document.querySelector('[data-work-id=video] details')?.textContent.includes('2 contenu(s) à vérifier.'));
  verify(await failures.evaluate(node => node.open), 'Les erreurs ouvertes doivent rester visibles après actualisation.');
  verify(await technicalDetails.evaluate(node => !node.open), 'Les détails techniques doivent rester repliés.');
  verify(await failures.locator('summary').evaluate(node => node === document.activeElement), 'Le focus doit rester sur les erreurs.');
  await page.goto(base + '/#/accueil');
  const shortcut = page.locator('#main-navigation .work-queue-link');
  await page.waitForFunction(() => document.querySelector('#main-navigation .work-queue-count').textContent === '7');
  const preview = page.locator('#main-navigation .work-queue-preview');
  await shortcut.hover();
  await preview.getByText('Audio en cours').waitFor();
  // The pointer must reach the preview without crossing an empty gap that closes it.
  const icon = await shortcut.boundingBox(), panel = await preview.boundingBox();
  await page.mouse.move(icon.x + icon.width / 2, icon.y + icon.height / 2);
  await page.mouse.move(icon.x + icon.width / 2, panel.y + 40, {steps: 12});
  verify(await preview.isVisible(), 'L’aperçu doit rester ouvert quand la souris descend de l’icône vers lui.');
  await preview.getByText('Inventaire des vidéos et sous-titres', {exact:true}).waitFor();
  await preview.getByText('Inventaire des vidéos dans les collections', {exact:true}).waitFor();
  await preview.getByText('Liste de vidéos', {exact:true}).waitFor();
  await preview.getByText('Une vidéo est privée.', {exact:true}).waitFor();
  verify((await shortcut.getAttribute('aria-label')).includes('1 erreur'), 'L’erreur doit être annoncée dans la barre.');
  await shortcut.locator('.work-queue-signal[data-level=error]').waitFor();
  await preview.getByText('Vidéos du jardin', {exact:true}).waitFor();
  await preview.getByText('Ensuite · Question à l’assistant', {exact:true}).waitFor();
  verify((await preview.boundingBox()).height > 620, 'L’aperçu doit montrer davantage de cartes sur un écran haut.');
  await shortcut.focus();
  await page.setViewportSize({width: 900, height: 480});
  await preview.waitFor();
  const compact = await preview.boundingBox();
  verify(compact.x >= 0 && compact.y + compact.height <= 480, 'L’aperçu doit tenir dans un écran court.');
  await page.setViewportSize({width: 1440, height: 900});
  await shortcut.hover();
  const previewHandle = preview.getByRole('button', {name: 'Déplacer Notice de montage'});
  await previewHandle.scrollIntoViewIfNeeded();
  const from = await previewHandle.boundingBox();
  const sourceCard = await preview.locator('[data-work-id=second]').boundingBox();
  const to = await preview.getByText('Manuel en anglais', {exact:true}).locator('..').boundingBox();
  await page.mouse.move(from.x + from.width / 2, from.y + from.height / 2);
  await page.mouse.down();
  await page.mouse.move(to.x + to.width / 2, to.y + 2, {steps: 8});
  await preview.locator('[data-work-id=document].work-queue-drop-before').waitFor();
  const ghost = page.locator('.work-queue-drag-ghost');
  const ghostBox = await ghost.boundingBox();
  const pointerOffset = from.y + from.height / 2 - sourceCard.y;
  verify(Math.abs(ghostBox.y - (to.y + 2 - pointerOffset)) < 2,
    'La carte soulevée doit suivre le pointeur.');
  const highlighted = preview.locator('.work-queue-drag-lane');
  verify(await highlighted.locator('h2').textContent() === 'Assistant et traductions', 'Seule la section autorisée doit ressortir.');
  verify(await preview.locator('[data-work-id=document]').evaluate(node => parseFloat(node.style.getPropertyValue('--work-queue-shift'))) > 0,
    'La carte voisine doit laisser la place au dépôt.');
  const otherLane = await preview.getByText('Téléchargements', {exact: true}).boundingBox();
  await page.mouse.move(otherLane.x + 16, otherLane.y + otherLane.height / 2);
  await page.mouse.up();
  await ghost.waitFor({state: 'detached'});
  verify(moveRequests === 0 && await highlighted.count() === 0, 'Un dépôt dans une autre section doit être annulé.');
  await page.mouse.move(from.x + from.width / 2, from.y + from.height / 2);
  await page.mouse.down();
  await page.mouse.move(to.x + to.width / 2, to.y + 2, {steps: 8});
  await page.mouse.up();
  await page.waitForFunction(() => document.querySelectorAll('#main-navigation .work-queue-preview [data-work-id="second"]')[0]?.nextElementSibling?.dataset.workId === 'document');
  const pause = preview.locator('.work-queue-preview-heading').getByRole('button', {name: 'Mettre en pause'});
  verify(await pause.getAttribute('data-paused') === 'false' && await pause.textContent() === '', 'L’en-tête doit afficher le pictogramme pause.');
  await pause.press('Enter');
  const play = preview.locator('.work-queue-preview-heading').getByRole('button', {name: 'Reprendre la file'});
  await play.waitFor();
  verify(await play.getAttribute('data-paused') === 'true', 'L’icône doit passer à la lecture.');
  verify(await play.evaluate(node => node === document.activeElement), 'Le bouton pause/reprise doit garder le focus.');

  await preview.getByText('File en pause', {exact:true}).waitFor();
  await preview.getByText('À la reprise · Question à l’assistant', {exact:true}).waitFor();
  verify((await shortcut.getAttribute('aria-label')).includes('1 erreur'), 'La pause doit laisser l’erreur visible.');
  await shortcut.focus();
  await page.keyboard.press('Escape');
  await preview.waitFor({state: 'hidden'});
  await shortcut.press('Enter');
  await page.getByRole('heading', {name: 'File d’attente', exact: true}).waitFor();
  const view = page.locator('#view-work-queue');
  await view.getByText('50 %').waitFor();
  await view.locator('[data-work-id=archive-video-index]').getByText('2 / 5', {exact:true}).waitFor();
  await view.getByText('Une vidéo est privée.').waitFor();
  const failedCard = view.locator('[data-work-id=video]');
  await failedCard.getByText('Que faire ?', {exact: true}).waitFor();
  verify((await failedCard.locator('.work-queue-next-step').textContent()).includes('Réessayer'),
    'Une erreur doit dire simplement quoi faire.');
  verify(await view.locator('#work-queue-groups > section').first().locator('h2').textContent() === 'En erreur',
    'Les erreurs doivent être visibles avant les créneaux.');
  await view.getByRole('heading', {name:'À reprendre', exact:true}).waitFor();
  const ai = view.locator('[data-lane=ai]');
  await ai.getByText('Question prioritaire').waitFor();
  verify(!await ai.getByRole('button', {name: 'Déplacer Comment réparer ce mécanisme ?'}).count(),
    'Une question prioritaire ne peut pas être déplacée dans les tâches de fond.');
  const handle = ai.getByRole('button', {name: 'Déplacer Manuel en anglais'});
  await handle.press('ArrowUp');
  await page.waitForFunction(() => document.querySelectorAll('#view-work-queue [data-lane=ai] .work-queue-card')[1]?.dataset.workId === 'document');
  verify(await handle.evaluate(node => node === document.activeElement), 'Le focus reste sur la tâche déplacée.');

  await view.getByRole('button', {name: 'Reprendre la file'}).click();
  await view.getByRole('button', {name: 'Mettre en pause', exact:true}).waitFor();
  unavailable = true;
  await view.getByText(/Suivi indisponible. Dernier état connu/).waitFor();
  await view.getByText('Une vidéo est privée.').waitFor();
  verify(await view.getByRole('button', {name: 'Réessayer'}).isDisabled(), 'État ancien : commande désactivée.');
  unavailable = 'invalid';
  const badResponse = page.waitForResponse(response => response.url().endsWith('/api/work-queue') && response.ok());
  await badResponse;
  await view.getByText(/Suivi indisponible. Dernier état connu/).waitFor();
  unavailable = false;
  await view.getByText(/Suivi indisponible. Dernier état connu/).waitFor({state:'hidden'});
  await view.getByRole('button', {name: 'Réessayer'}).click();
  await view.getByText('Une vidéo est privée.').waitFor({state: 'hidden'});
  const archiveTask = view.locator('[data-work-id="archive-video-index"]');
  await archiveTask.getByRole('button', {name: 'Mettre en pause Inventaire des vidéos dans les collections'}).click();
  await archiveTask.getByRole('button', {name: 'Reprendre', exact:true}).waitFor();
  verify(await view.locator('#work-queue-pause').textContent() === 'Mettre en pause', 'La pause de l’inventaire ne doit pas bloquer la file.');
  verify(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'La file déborde sur ordinateur.');

  await page.setViewportSize({width: 390, height: 844});
  await page.goto(base + '/#/accueil');
  const mobile = page.locator('.top-actions .work-queue-link');
  if (await page.evaluate(() => navigator.maxTouchPoints)) await mobile.tap();
  else await mobile.click();
  await view.getByRole('heading', {name: 'File d’attente', exact: true}).waitFor();
  await view.getByText('Manuel en anglais').waitFor();
  verify(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'La file déborde sur téléphone.');
  if (page.context().browser().browserType().name() === 'chromium') {
    const session = await page.context().newCDPSession(page);
    await session.send('Emulation.setTouchEmulationEnabled', {enabled:true});
    try {
      const handle = view.getByRole('button', {name:'Déplacer Notice de montage'});
      await handle.scrollIntoViewIfNeeded();
      const source = await handle.boundingBox();
      const target = await view.locator('[data-work-id=document]').boundingBox();
      const send = (type, touchPoints) => session.send('Input.dispatchTouchEvent', {type, touchPoints});
      await send('touchStart', [{x:source.x + source.width / 2, y:source.y + source.height / 2}]);
      await send('touchMove', [{x:target.x + target.width / 2, y:target.y + target.height / 4}]);
      await view.locator('[data-work-id=document].work-queue-drop-before').waitFor();
      await send('touchEnd', []);
      await page.waitForFunction(() => document.querySelectorAll('#view-work-queue [data-lane=ai] .work-queue-card')[1]?.dataset.workId === 'second');
    } finally {
      await session.send('Emulation.setTouchEmulationEnabled', {enabled:false});
      await session.detach();
    }
  }
  // Exercise the actual file input and list-validation API, without pasting.
  await page.goto(base + '/#/appareil/bibliotheque');
  const youtube = page.locator('#next-youtube');
  const input = youtube.locator('input[type=file]');
  if (!await input.isVisible()) await youtube.locator('summary').click();
  const list = '[Énergie]\r\nhttps://youtu.be/aaaaaaaaaaa\r\nhttps://youtu.be/bbbbbbbbbbb\r\nhttps://youtu.be/ccccccccccc';
  await input.setInputFiles({name: 'liste.txt', mimeType: 'text/plain', buffer: Buffer.from('\uFEFF' + list, 'utf16le')});
  await youtube.getByText('3 vidéo(s) prête(s) à télécharger.', {exact: true}).waitFor();
  let submitted;
  await page.route('**/api/admin/youtube-downloads', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    submitted = route.request().postDataJSON();
    await route.fulfill({json: {accepted: true}});
  });
  await youtube.getByRole('button', {name: 'Télécharger les vidéos'}).click();
  await youtube.getByText('Liste ajoutée à la file.', {exact: false}).waitFor();
  verify(submitted.text.split(/\r?\n/).length === 4 && submitted.text.includes('ccccccccccc'),
    'Le formulaire doit envoyer les trois adresses, dans leur ordre.');
  // A temporary polling failure must leave the question tracked in the assistant.
  await page.goto(base + '/#/assistant');
  await page.waitForFunction(() => typeof S !== 'undefined' && S.authReady && S.user &&
    S.view === 'chat' && !S.loadingConversation && !S.job && !S.sending);
  await page.locator('#chat-reset').click();
  await page.waitForFunction(() => !S.conversation && !S.loadingConversation && !S.summaryActive);
  let failSend;
  const pendingSend = new Promise(resolve => {failSend = resolve;});
  await page.route('**/api/questions', async route => {
    await pendingSend;
    await route.abort('failed');
  });
  const draft = page.locator('#chat-input');
  await draft.fill('Question à conserver');
  await page.locator('#send-question').click();
  await page.locator('#chat-status').getByText('Envoi de la question…', {exact:true}).waitFor();
  failSend();
  await page.locator('#chat-status').getByText(/Impossible de confirmer l’envoi/).waitFor();
  verify(await draft.inputValue() === 'Question à conserver', 'Le texte reste disponible si l’envoi n’est pas confirmé.');
  let answer = 'unavailable';
  await page.route('**/api/jobs/queue-fixture', route => answer === 'unavailable'
    ? route.fulfill({status:503,json:{detail:'Indisponible'}})
    : route.fulfill({json:{status:answer, queue_state:'paused', error:answer === 'failed' ? 'Le moteur a arrêté la réponse.' : null,
                          mode:'rapide',sources:[],created:Date.now()/1000}}));
  await page.evaluate(() => watch('queue-fixture'));
  await page.locator('#chat-status').getByText(/Suivi de la réponse indisponible/).waitFor();
  verify(await page.evaluate(() => S.job === 'queue-fixture'), 'La réponse reste suivie pendant la coupure.');
  answer = 'queued';
  await page.locator('#chat-status').getByText(/La file est en pause/).waitFor();
  answer = 'failed';
  await page.locator('#chat-status').getByText('Le moteur a arrêté la réponse.', {exact:true}).waitFor();
  // The real API accepts starts and resumes from separate conversations of the same profile.
  await page.unroute('**/api/work-queue**');
  const post = async (path, data) => {
    const response = await page.request.post(base + '/api' + path, {headers:{Origin:base}, data});
    verify(response.ok(), path + ' : ' + await response.text());
    return response.json();
  };
  const startData = {source_id:'guide:shelter.en.txt', mode:'rapide'};
  const jobs = [];
  await post('/work-queue/pause', {paused:true});
  try {
    const first = await post('/translations', startData);
    jobs.push(first.id);
    await post('/translations/' + first.id + '/stop', {});
    const other = await post('/translations', startData);
    jobs.push(other.id);
    await page.setViewportSize({width:1440,height:900});
    await page.goto(base + '/#/assistant?conversation=' + first.conversation_id);
    const panel = page.locator('#translation-panel');
    await page.waitForFunction(id => S.translation === id, first.id);
    await panel.evaluate(node => node.open = true);
    const resume = panel.getByRole('button', {name:'Ajouter à la file d’attente', exact:true});
    await resume.waitFor();
    await resume.click();
    await panel.getByText(/En attente · file en pause/).waitFor();
    await page.locator('#chat-reset').click();
    await page.evaluate(() => attachToConversation({id:'guide:shelter.en.txt', title:'Guide fictif'}));
    await panel.evaluate(node => node.open = true);
    const response = page.waitForResponse(item => item.url().endsWith('/api/translations') && item.request().method() === 'POST');
    await panel.getByRole('button', {name:'Ajouter à la file d’attente', exact:true}).click();
    const created = await response;
    verify(created.ok(), await created.text());
    jobs.push((await created.json()).id);
    await panel.getByText(/En attente · file en pause/).waitFor();
  } finally {
    for (const id of jobs) await post('/translations/' + id + '/stop', {});
    await post('/work-queue/pause', {paused:false});
  }
  verify(!errors.length, errors.join('\n'));
  return {passed: ['aperçu des créneaux parallèles au survol et au clavier', 'question prioritaire', 'pause et reprise', 'glisser-déposer et clavier', 'ajout et reprise dans plusieurs conversations', 'avancement', 'erreur visible pendant la pause', 'distinction pause et erreur', 'perte et retour du suivi', 'erreur et relance', 'navigation tactile', 'envoi et brouillon visibles', 'suivi de la réponse après reconnexion', 'import et envoi du TXT Windows entier']};
}
