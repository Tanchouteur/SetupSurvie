async page => {
  const base = 'http://10.0.3.2:8769', checks = [];
  const check = (condition, description) => {
    if (!condition) throw Error(description);
    checks.push(description);
  };
  const models = [
    {model: 'gpt-oss:20b', name: 'GPT-OSS 20B', category: 'recommended', installed: true, size: 13793441566},
    {model: 'gemma4:e4b', name: 'Gemma4 E4B', category: 'recommended', installed: false, size: 6583656505},
    {model: 'qwen3.5:27b-q4_K_M', name: 'Qwen3.5 27B', category: 'comparison', installed: false, size: 17478556591},
  ];
  const id = 'a'.repeat(32);
  let available = true, download = null, starts = 0, cancels = 0;
  await page.route('**/api/admin/models', route => route.fulfill({
    json: {available, models: models.map(model => ({...model, installed: available ? model.installed : null})), download},
  }));
  await page.route('**/api/admin/models/download', route => {
    starts++;
    const {model} = route.request().postDataJSON();
    download = {id, model, state: 'downloading', completed: 1800000000, total: 6583656505, message: ''};
    return route.fulfill({status: 202, json: download});
  });
  await page.route('**/api/admin/models/cancel', route => {
    check(route.request().postDataJSON().id === id, 'L’annulation vise le téléchargement affiché');
    cancels++;
    download = {...download, state: 'cancelled', message: 'Vous pouvez le relancer.'};
    return route.fulfill({json: download});
  });
  const card = page.locator('#model-downloads');
  const start = card.getByRole('button', {name: 'Télécharger Gemma4 E4B'});
  await page.setViewportSize({width: 1440, height: 950});
  await page.goto(base + '/#/appareil/assistant');
  await start.waitFor();
  check(await card.locator('.model-installed:visible').count() === 1, 'Indication du modèle déjà installé');
  check(await card.getByText('Environ 6,6 Go').isVisible(), 'Taille visible avant téléchargement');
  const comparisons = card.locator('details');
  check(!(await comparisons.evaluate(node => node.open)), 'Comparaisons repliées');
  await comparisons.locator('summary').click();
  check(await card.getByRole('button', {name: 'Télécharger Qwen3.5 27B'}).isVisible(), 'Comparaisons accessibles');
  await comparisons.locator('summary').click();
  await card.screenshot({path:'/artifacts/modeles-ordinateur.png'});

  await start.focus();
  await page.keyboard.press('Enter');
  await card.getByText('1,8 Go sur 6,6 Go').waitFor();
  check(await start.isDisabled(), 'Un seul téléchargement à la fois');
  await page.locator('#navigation [data-route="assistant"]').click();
  await page.locator('#chat-input').waitFor();
  check(await page.locator('#dictate').count() === 0, 'Saisie dans le portail sans microphone');
  await page.goto(base + '/#/appareil/assistant');
  await card.getByText('1,8 Go sur 6,6 Go').waitFor();
  check(starts === 1, 'Retour au téléchargement existant');

  await page.setViewportSize({width: 320, height: 760});
  check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Réglages sans débordement à 320 px');
  await card.screenshot({path:'/artifacts/modeles-mobile.png'});
  await card.getByRole('button', {name: 'Annuler', exact: true}).click();
  await card.getByText('Téléchargement annulé · Gemma4 E4B').waitFor();
  check(cancels === 1, 'Annulation et état final visibles');
  await start.click();
  await card.getByText('1,8 Go sur 6,6 Go').waitFor();
  models[1].installed = true;
  download = {...download, state: 'complete', completed: download.total, message: 'Modèle prêt à utiliser.'};
  await card.getByText('Modèle prêt · Gemma4 E4B').waitFor();
  check(await card.locator('.model-installed:visible').count() === 2 && await start.count() === 0, 'Le modèle terminé rejoint les modèles installés');

  available = false;
  await card.getByText('Démarrez le moteur IA', {exact: false}).waitFor();
  check(await start.isDisabled(), 'Moteur arrêté et téléchargements désactivés');
  await page.goto(base + '/classique/#settings');
  await card.getByText('Démarrez le moteur IA', {exact: false}).waitFor();
  check(await page.locator('#dictate').count() === 0, 'Interface classique sans bouton de dictée');
  return {checks};
}
