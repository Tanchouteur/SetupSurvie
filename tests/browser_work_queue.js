async page => {
  const base = 'http://127.0.0.1:8769';
  const verify = (value, message) => { if (!value) throw Error(message); };
  const tasks = [
    {id: 'active', lane: 'local', kind: 'speech', type: 'Transcription audio', title: 'Audio en cours', model: 'Whisper small · CPU', status: 'running', done: 60000, total: 120000},
    {id: 'question', lane: 'ai', kind: 'chat', type: 'Question à l’assistant', title: 'Comment réparer ce mécanisme ?', model: 'gemma', status: 'queued', priority: true, next: true, movable: true},
    {id: 'document', lane: 'ai', kind: 'translation', type: 'Traduction de document', title: 'Manuel en anglais', model: 'gemma', status: 'queued', done: 3, total: 8, movable: true},
    {id: 'video', lane: 'network', kind: 'youtube', type: 'Téléchargement YouTube', title: 'Liste de vidéos', model: 'yt-dlp', status: 'error',
      error: 'Une vidéo est privée.', retry: true, failure_count: 1, failures: [{line: 2, message: 'vidéo privée'}]},
    {id: 'second', lane: 'ai', kind: 'translation', type: 'Traduction de document', title: 'Notice de montage', model: 'gemma', status: 'queued', movable: true},
    {id: 'download', lane: 'network', kind: 'youtube', type: 'Téléchargement YouTube', title: 'Vidéos du jardin', status: 'running'}
  ];
  tasks.push({id:'held',lane:'local',kind:'speech',type:'Transcription audio',title:'Audio suspendu',status:'paused',retry:true});
  let paused = false, unavailable = false;
  await page.route('**/api/work-queue**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (unavailable && request.method() === 'GET') {
      return unavailable === 'invalid' ? route.fulfill({json: {ok: true}})
        : route.fulfill({status: 503, json: {detail: 'Indisponible'}});
    }
    if (path.endsWith('/pause')) paused = request.postDataJSON().paused;
    if (path.endsWith('/second/move') && request.postDataJSON().direction === -1) {
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
  await page.request.post(base + '/api/profiles/select', {headers: {Origin: base}, data: {id: 'famille'}});
  await page.setViewportSize({width: 1440, height: 900});
  await page.goto(base + '/nouveau/#/accueil');
  const shortcut = page.locator('#main-navigation .work-queue-link');
  await page.waitForFunction(() => document.querySelector('#main-navigation .work-queue-count').textContent === '5');
  const preview = page.locator('#main-navigation .work-queue-preview');
  await shortcut.hover();
  await preview.getByText('Audio en cours').waitFor();
  await preview.getByText('En erreur · Liste de vidéos', {exact:true}).waitFor();
  await preview.getByText('Une vidéo est privée.', {exact:true}).waitFor();
  verify((await shortcut.getAttribute('aria-label')).includes('1 erreur'), 'L’erreur doit être annoncée dans la barre.');
  await shortcut.locator('.work-queue-signal[data-level=error]').waitFor();
  await preview.getByText('En cours · Vidéos du jardin').waitFor();
  await preview.getByText('Ensuite · Comment réparer ce mécanisme ?').waitFor();
  await preview.getByRole('button', {name: 'Mettre en pause'}).click();
  await preview.getByRole('button', {name: 'Reprendre la file'}).waitFor();
  await preview.getByText('File en pause', {exact:true}).waitFor();
  await preview.getByText('À la reprise · Comment réparer ce mécanisme ?').waitFor();
  verify((await shortcut.getAttribute('aria-label')).includes('1 erreur'), 'La pause doit laisser l’erreur visible.');
  await shortcut.focus();
  await page.keyboard.press('Escape');
  await preview.waitFor({state: 'hidden'});
  await shortcut.press('Enter');
  await page.getByRole('heading', {name: 'File d’attente', exact: true}).waitFor();
  const view = page.locator('#view-work-queue');
  await view.getByText('50 %').waitFor();
  await view.getByText('Une vidéo est privée.').waitFor();
  verify(await view.locator('#work-queue-groups > section').first().locator('h2').textContent() === 'En erreur',
    'Les erreurs doivent être visibles avant les créneaux.');
  await view.getByRole('heading', {name:'À reprendre', exact:true}).waitFor();
  const ai = view.locator('[data-lane=ai]');
  await ai.getByText('Question prioritaire').waitFor();
  verify(await ai.getByRole('button', {name: 'Reculer Comment réparer ce mécanisme ?'}).isDisabled(),
    'Une question prioritaire ne peut pas être déplacée dans les tâches de fond.');
  await ai.getByRole('button', {name: 'Avancer Notice de montage'}).click();
  await page.waitForFunction(() => document.querySelectorAll('[data-lane=ai] .work-queue-card')[1]?.dataset.workId === 'second');
  await view.getByRole('button', {name: 'Reprendre la file'}).click();
  await view.getByRole('button', {name: 'Mettre en pause'}).waitFor();
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
  verify(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'La file déborde sur ordinateur.');

  await page.setViewportSize({width: 390, height: 844});
  await page.goto(base + '/nouveau/#/accueil');
  const mobile = page.locator('.top-actions .work-queue-link');
  if (await page.evaluate(() => navigator.maxTouchPoints)) await mobile.tap();
  else await mobile.click();
  await view.getByRole('heading', {name: 'File d’attente', exact: true}).waitFor();
  await view.getByText('Manuel en anglais').waitFor();
  verify(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'La file déborde sur téléphone.');
  // Exercise the actual file input and list-validation API, without pasting.
  await page.goto(base + '/nouveau/#/appareil/bibliotheque');
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
  await page.goto(base + '/nouveau/#/assistant');
  await page.waitForFunction(() => typeof S !== 'undefined' && S.authReady && S.user);
  let failSend;
  const pendingSend = new Promise(resolve => {failSend = resolve;});
  await page.route('**/api/questions', async route => {
    await pendingSend;
    await route.abort('failed');
  });
  const draft = page.locator('#chat-input');
  await draft.fill('Question à conserver');
  await page.locator('#chat-form').evaluate(form => form.requestSubmit());
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
  verify(!errors.length, errors.join('\n'));
  return {passed: ['aperçu des créneaux parallèles au survol et au clavier', 'question prioritaire', 'pause et reprise', 'ordre des tâches', 'avancement', 'erreur visible pendant la pause', 'distinction pause et erreur', 'perte et retour du suivi', 'erreur et relance', 'navigation tactile', 'envoi et brouillon visibles', 'suivi de la réponse après reconnexion', 'import et envoi du TXT Windows entier']};
}
