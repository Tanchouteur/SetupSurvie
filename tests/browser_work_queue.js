async page => {
  const base = 'http://127.0.0.1:8769';
  const verify = (value, message) => { if (!value) throw Error(message); };
  const tasks = [
    {id: 'active', kind: 'speech', type: 'Transcription audio', title: 'Audio en cours', model: 'Whisper small · CPU', status: 'running', done: 60000, total: 120000},
    {id: 'document', kind: 'translation', type: 'Traduction de document', title: 'Manuel en anglais', model: 'gemma', status: 'queued', done: 3, total: 8, movable: true},
    {id: 'question', kind: 'chat', type: 'Question à l’assistant', title: 'Comment réparer ce mécanisme ?', model: 'gemma', status: 'queued', movable: true},
    {id: 'video', kind: 'youtube', type: 'Téléchargement YouTube', title: 'Liste de vidéos', model: 'yt-dlp', status: 'error',
      error: 'Une vidéo est privée.', retry: true, failure_count: 1, failures: [{line: 2, message: 'vidéo privée'}]}
  ];
  let paused = false;
  await page.route('**/api/work-queue**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path.endsWith('/pause')) paused = request.postDataJSON().paused;
    if (path.endsWith('/question/move') && request.postDataJSON().direction === -1) {
      [tasks[1], tasks[2]] = [tasks[2], tasks[1]];
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
  await page.waitForFunction(() => document.querySelector('#main-navigation .work-queue-count').textContent === '3');
  const preview = page.locator('#main-navigation .work-queue-preview');
  await shortcut.hover();
  await preview.getByText('Audio en cours').waitFor();
  await preview.getByRole('button', {name: 'Mettre en pause'}).click();
  await preview.getByRole('button', {name: 'Reprendre la file'}).waitFor();
  await shortcut.focus();
  await page.keyboard.press('Escape');
  await preview.waitFor({state: 'hidden'});
  await shortcut.press('Enter');
  await page.getByRole('heading', {name: 'File d’attente', exact: true}).waitFor();
  const view = page.locator('#view-work-queue');
  await view.getByText('50 %').waitFor();
  await view.getByText('Une vidéo est privée.').waitFor();
  await view.getByRole('button', {name: 'Avancer Comment réparer ce mécanisme ?'}).click();
  await page.waitForFunction(() => document.querySelector('.work-queue-group:nth-child(2) .work-queue-card').dataset.workId === 'question');
  await view.getByRole('button', {name: 'Reprendre la file'}).click();
  await view.getByRole('button', {name: 'Mettre en pause'}).waitFor();
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
  verify(!errors.length, errors.join('\n'));
  return {passed: ['aperçu survol et clavier', 'pause et reprise', 'ordre des tâches', 'avancement', 'erreur et relance', 'navigation tactile', 'import et envoi du TXT Windows entier']};
}
