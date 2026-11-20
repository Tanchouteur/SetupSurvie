async page => {
  const base='http://10.0.3.2:8769';const checks=[];const errors=[];const commands=[];
  const assert=(value,label)=>{if(!value)throw Error(label);checks.push(label);};
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.method()==='POST')commands.push(new URL(r.url()).pathname);});
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.goto('about:blank');await page.context().clearCookies();
  await page.route('**/api/activity',r=>r.fulfill({json:{phase:'downloading',source:'windows',observed_at:Date.now()/1000,worker_alive:true,total_bytes:10000000000,verified_bytes:3000000000,total_count:4,verified_count:1,active:[{id:'book',title:'Collection fixture',bytes:1000000000,total:2000000000,phase:'downloading'}]}}));
  await page.setViewportSize({width:1440,height:950});await page.goto(base+'/#/accueil');await page.waitForFunction(()=>S.authReady&&S.user&&!S.loadingConversation);
  assert(await page.locator('#navigation').isVisible(),'Nouvelle interface par défaut');
  assert(await page.locator('#view-home #collections, #view-home #library-count').count()===0,'Accueil sans liste de collections');
  assert(!await page.locator('#feedback-button').isVisible(),'Bouton de retour retiré');
  assert(await page.locator('a[href^="/classique/"]').count()===0,'Liens classiques retirés des menus');
  await page.locator('#navigation [data-route="bibliotheque"]').click();
  await page.locator('.next-tabs [data-route="bibliotheque/collections"]').click();
  await page.locator('#collection-filter').fill('');
  const guides=page.locator('#collection-section-guides');
  if(!await guides.evaluate(section=>section.open))await guides.locator(':scope > summary').click();
  const directGuide=guides.locator('#data-guides > .data-card button').first();
  await directGuide.waitFor();
  assert(await page.locator('#next-collections').isVisible(),'Bibliothèque réelle et guides');
  // Existing reader and enriched PDF/favorite functions retain the same controls.
  await directGuide.click();await page.waitForSelector('#reader .reader-actions');
  assert(page.url().includes('source='),'Document adressable');
  assert(await page.locator('#reader').isVisible(),'Lecture du vrai document fixture');
  await page.goBack();await page.waitForFunction(()=>document.querySelector('#next-collections').hidden===false);
  assert(await page.locator('#next-collections').isVisible(),'Retour à la collection');
  await page.locator('.next-tabs [data-route="bibliotheque/recherche"]').click();await page.locator('#library-query').fill('Shelter');
  await page.locator('#library-search').evaluate(f=>f.requestSubmit());await page.waitForSelector('#search-results .result');
  assert(page.url().includes('q=Shelter'),'Recherche et filtres adressables');
  await page.locator('#search-results .result button').first().click();await page.waitForSelector('#reader h2');
  await page.goBack();await page.waitForSelector('#search-results .result');
  assert(await page.locator('#library-query').inputValue()==='Shelter','Retour conserve la requête');
  await page.locator('#navigation [data-route="assistant"]').click();
  await page.locator('#chat-input').fill('Brouillon conservé');
  await page.locator('#navigation [data-route="appareil"]').click();
  await page.waitForFunction(()=>document.querySelector('.next-activity .next-transfer-title').textContent==='Téléchargement en cours');
  assert((await page.locator('#view-monitor .next-transfer-message').textContent()).includes('3.0 Go'),'Vrais volumes API, pas de mesures fictives codées en dur');
  await page.goto(base+'/#/appareil/telechargements');
  await page.locator('#content-manager').evaluate(d=>d.open=true);
  assert(await page.locator('#content-form').isVisible(),'Préparation documentaire conservée sur ordinateur');
  await page.locator('#content-plan').click();
  assert(!commands.includes('/api/admin/library/plan'),'Pas de préparation concurrente pendant le transfert indépendant');
  await page.locator('#next-machine-tabs [data-route="appareil/reglages"]').click();
  assert(await page.locator('#upload-form').count()===1,'Ajout de guide et réglages conservés');
  await page.locator('#navigation [data-route="assistant"]').click();
  assert(await page.locator('#chat-input').inputValue()==='Brouillon conservé','Brouillon après navigation');
  await page.reload();await page.waitForFunction(()=>S.authReady&&S.user&&!S.loadingConversation);
  assert(await page.locator('#chat-input').inputValue()==='Brouillon conservé','Brouillon après rechargement');
  await page.locator('#chat-input').fill('Question simulée de recette');await page.locator('#chat-form').evaluate(f=>f.requestSubmit());
  await page.waitForURL(/conversation=/);await page.waitForFunction(()=>!!S.conversation&&!S.job);
  assert(page.url().includes('conversation='),'Conversation réelle adressable');
  assert((await page.locator('#chat-messages').textContent()).includes('Réponse simulée'),'Envoi fonctionne sur API simulée sans modèle');
  const conversation=await page.evaluate(()=>S.conversation);
  // Former bookmarks of the retired interfaces land on the same portal, route and profile.
  for(const legacy of ['/classique/#chat','/nouveau/#/assistant']){
    const old=await page.context().newPage();await old.goto(base+legacy);await old.waitForURL(url=>new URL(url).pathname==='/');
    await old.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.user);
    assert(await old.locator('#view-chat').isVisible(),'Ancienne adresse '+legacy+' redirigée vers l’assistant');await old.close();
  }
  await page.setViewportSize({width:390,height:844});await page.locator('#navigation [data-route="appareil"]').click();
  await page.goto(base+'/#/appareil/telechargements');
  assert(!await page.locator('#geo-download-form').isVisible(),'Préparation complexe retirée sur mobile');
  assert(await page.locator('#view-data .next-activity').isVisible(),'Suivi accessible sur mobile');
  const [queueResponse] = await Promise.all([
    page.waitForResponse(response => response.url() === base+'/api/work-queue' &&
      response.request().frame().url().startsWith(base+'/cartes.html')),
    page.locator('#navigation').getByRole('link',{name:'Cartes',exact:true}).click(),
  ]);
  await page.waitForURL('**/cartes.html');
  await page.waitForFunction(()=>window.SurvieMap);
  assert(await page.locator('#map').isVisible(),'L’onglet Cartes ouvre directement la carte sur mobile');
  for(const width of [320,390,760,820,1440]){await page.setViewportSize({width,height:950});assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Pas de débordement à '+width);}
  // Let the maps header finish its initial local request before leaving the page.
  assert(queueResponse.ok() && await queueResponse.finished() === null, 'Suivi de la file disponible depuis les cartes');
  await page.goto(base+'/pdf.html?id=guide%3Ashelter.en.pdf');
  await page.waitForFunction(()=>document.querySelector('#pdf-ask').getAttribute('href')?.startsWith('/?document='));
  await page.getByRole('link',{name:'Questionner ce document'}).click();
  await page.waitForFunction(()=>typeof S!=='undefined'&&S.source?.id==='guide:shelter.en.pdf');
  assert(await page.locator('#view-chat').isVisible(),'Le lecteur PDF ouvre le bon assistant avec son document associé');
  assert(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  assert(!commands.some(p=>/inference|geography\/download|routing\/download|library\/download/.test(p)),'Aucun démarrage moteur ni téléchargement réel');
  return {checks:checks.length,results:checks,conversation};
}
