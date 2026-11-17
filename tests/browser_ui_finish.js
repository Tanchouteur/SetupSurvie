// Reported visual regressions, with populated views and real hit targets; no model.
async (page) => {
  const base = 'http://10.0.3.2:8769', checks = [], errors = [];
  const check = (value, name) => { if (!value) throw Error(name); checks.push(name); };
  const fit = () => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
  page.on('pageerror', e => errors.push(e.message));
  await page.request.post(base + '/api/profiles/select', {data:{id:'browser'}, headers:{Origin:base}});
  await page.setViewportSize({width:1920, height:1080});
  await page.goto(base + '/#/assistant'); await page.waitForFunction(() => typeof S!=='undefined' && S.authReady && S.user);
  await page.locator('#chat-reset').click();
  await page.evaluate(() => {
    $('chat-title').textContent = 'Une question longue, avec plusieurs documents et des explications à retrouver dans la conversation';
    $('chat-messages').replaceChildren();
    message('user', 'Question fictive pour une revue de mise en page.');
    message('assistant', Array.from({length:18}, (_, i) => '### Partie '+i+'\n\nUne réponse longue doit laisser les commandes accessibles.\n\n| Source | Observation |\n| --- | --- |\n| Document fictif | À relire |').join('\n\n'));
  });
  check(await page.locator('#navigation .nav-item').evaluateAll(ns => ns.every(n => {
    const a=n.getBoundingClientRect(),b=n.lastElementChild.getBoundingClientRect();
    return b.left>=a.left && b.right<=a.right+1;
  })), 'Les libellés de navigation restent dans leur cible, sans se chevaucher');
  check(await page.getByRole('button', {name:'Discussion', exact:true}).count() === 0, 'Aucun bouton Discussion sans fonction propre');
  check(await page.locator('#chat-form .ux-help').count() === 0, 'La saisie ne contient plus de gros bouton d’aide');
  check(await page.locator('#chat-reset').count() === 1, 'Une seule commande Nouvelle discussion');
  check(await page.locator('#assistant-history').evaluate(n => n.getBoundingClientRect().left < 40), 'Le poste PC utilise la largeur disponible');
  await page.locator('#assistant-documents details').last().evaluate(n => n.open = true);
  const aligned = await page.locator('#assistant-model-trials').evaluate(n => {
    const a=n.getBoundingClientRect(), b=n.nextElementSibling.getBoundingClientRect();
    return b.left >= a.right && b.left-a.right < 20 && Math.abs(a.top+a.height/2-b.top-b.height/2) < 2;
  });
  check(aligned, 'Case et libellé sur la même ligne, sans ambiguïté');
  await page.getByLabel('Afficher les modèles d’essai', {exact:true}).check();
  check(await page.getByLabel('Afficher les modèles d’essai', {exact:true}).isChecked(), 'Libellé de case utilisable à la souris');
  await page.locator('[data-close-panel=history]').click();
  check(await page.locator('#assistant-history').isHidden(), 'Fermeture depuis le volet Conversations');
  check(await page.locator('#chat-reset').isVisible(), 'Nouvelle discussion disponible avec le volet fermé');
  await page.locator('[data-assistant-zone=history]').click();
  check(await page.locator('#assistant-history').isVisible(), 'Réouverture du volet depuis l’en-tête');
  await page.locator('[data-close-panel=documents]').click();
  await page.locator('[data-assistant-zone=documents]').click();
  check(await page.locator('#assistant-documents').isVisible(), 'Fermeture et réouverture indépendantes des documents');
  for (const width of [1920,1440,1024,390,320]) {
    await page.setViewportSize({width, height:844});
    if (width<=1000) {
      if (await page.locator('#assistant-documents').isVisible()) await page.locator('[data-close-panel=documents]').click();
      await page.locator('[data-assistant-zone=history]').click();
      await page.locator('[data-close-panel=history]').click();
      check(await page.locator('#chat-input').isVisible(), 'Retour à la saisie sans bouton intermédiaire à '+width);
      await page.locator('#chat-input').focus();check(await page.locator('[data-assistant-zone=documents]').isVisible(),'Volets accessibles pendant la saisie à '+width);
    }
    check(await fit(), 'Conversation peuplée sans débordement à '+width);
    check(await page.locator('#chat-reset').isVisible(), 'Nouvelle discussion accessible à '+width);
  }
  await page.request.post(base + '/api/profiles/select', {data:{id:'local-family'},headers:{Origin:base}});
  await page.goto('about:blank');
  for (const width of [1440,1024,390,320]) {
    await page.setViewportSize({width, height:950});
    for (const route of ['reglages','acces','bibliotheque','assistant','entretien']) {
      await page.goto(base + '/#/appareil/'+route); await page.waitForFunction(() => typeof S!=='undefined' && S.authReady && S.user);await page.locator('#settings-'+route).waitFor({state:'visible'});
      const cards=await page.locator('.settings-pane:not([hidden]) .settings-destination').evaluateAll(ns => ns.filter(n=>n.getClientRects().length).map(n=>({
        height:n.getBoundingClientRect().height,
        valid:!!n.querySelector('strong')?.textContent && !!n.querySelector('span.muted')?.textContent && !!n.querySelector('.settings-arrow')?.textContent,
        radius:getComputedStyle(n).borderRadius,
      })));
      check(cards.length>0 && cards.every(c=>c.valid), 'Titre, description et action sur chaque carte '+route+' à '+width);
      check(Math.max(...cards.map(c=>c.height))-Math.min(...cards.map(c=>c.height))<2, 'Cartes de même hauteur '+route+' à '+width);
      check(new Set(cards.map(c=>c.radius)).size===1 && await fit(), 'Cartes cohérentes et sans débordement '+route+' à '+width);
    }
    for (const route of ['bibliotheque','assistant','entretien','tests']) {
      await page.goto(base + '/#/appareil/'+route);await page.locator('#settings-'+route).waitFor({state:'visible'});
      const headers=await page.locator('#settings-'+route+' .settings-card-summary').evaluateAll(ns=>ns.filter(n=>n.getClientRects().length).map(n=>({
        title:n.querySelector('.settings-card-title')?.textContent,
        description:n.querySelector('.settings-card-description')?.textContent,
        font:getComputedStyle(n.querySelector('.settings-card-title')).fontSize,
      })));
      check(headers.length>0 && headers.every(h=>h.title&&h.description)&&new Set(headers.map(h=>h.font)).size===1,'Titres et descriptions cohérents sur les cartes dépliables '+route+' à '+width);
      check(await fit(),'Cartes dépliables sans débordement '+route+' à '+width);
    }
    await page.goto(base + '/#/bibliotheque/recherche?q=Shelter'); await page.waitForSelector('#search-results .result');
    check(await fit(), 'Recherche et libellés masqués sans débordement à '+width);
    await page.goto(base + '/#/bibliotheque/collections'); await page.waitForFunction(()=>typeof S!=='undefined' && S.authReady);
    const help=page.getByRole('button',{name:'Comprendre le filtre des collections',exact:true});
    await help.click();
    check(await help.getAttribute('aria-expanded')==='true', 'Aide facultative disponible à '+width);
    await page.keyboard.press('Escape');
  }
  check(!errors.length, 'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length, results:checks};
}
