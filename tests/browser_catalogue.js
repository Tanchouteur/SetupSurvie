// Human edits persist on the fixture API. Archive navigation itself is simulated.
async page => {
  const base='http://10.0.3.2:8769',checks=[],errors=[],dossierReads=[],headers={Origin:base};
  const check=(value,label)=>{if(!value)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{if(request.url().includes('/api/library/dossiers'))dossierReads.push(request.url());});
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers});
  const guide='guide:craft.en.txt',books=['fixture-channel_en_energy_2026-01','fixture-channel_en_food_2026-01'];
  for(const id of [guide,...books.map(id=>'collection:'+id)])await page.request.delete(base+'/api/admin/library/metadata?'+new URLSearchParams({source_id:id}),{headers});
  await page.route('**/api/profiles/current',async route=>{const response=await route.fetch();await new Promise(resolve=>setTimeout(resolve,200));return route.fulfill({response});});
  await page.route('**/api/inventory',async route=>{
    const data=await(await route.fetch()).json();data.books=data.books.map(item=>({...item,ready:true}));return route.fulfill({json:data});
  });
  await page.setViewportSize({width:1366,height:900});await page.goto(base+'/#/bibliotheque/recherche?q=sewing&domain=all');
  await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.user);
  await page.locator('#search-results .result').filter({hasText:'craft'}).getByRole('button',{name:'Lire le document →',exact:true}).click();
  const editor=page.locator('#reader .catalogue-editor');await editor.locator('summary').click();
  check(dossierReads.length===0,'Lire et classer un document ne charge pas les dossiers repliés');
  await editor.locator('[name="domain"][value="resilience"]').uncheck();await editor.locator('[name="domain"][value="culture"]').check();
  await editor.locator('[name="document_type"]').selectOption('manual');await editor.getByLabel('J’ai examiné le contenu pour ce classement.').check();
  await editor.getByRole('button',{name:'Enregistrer le classement',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#reader > .small')?.textContent.includes('classement examiné'));
  check((await page.locator('#reader').textContent()).includes('Notice technique · classement examiné'),'Type et classement humain visibles après enregistrement');
  await page.reload();await page.waitForSelector('#reader .catalogue-editor');
  check((await page.locator('#reader').textContent()).includes('Notice technique · classement examiné'),'Correction conservée au rechargement et dans l’adresse du document');
  let result=await(await page.request.get(base+'/api/search?'+new URLSearchParams({q:'sewing',domain:'resilience'}))).json();
  check(!result.results.some(row=>row.id===guide),'Correction utilisée par le filtre pratique');
  result=await(await page.request.get(base+'/api/search?'+new URLSearchParams({q:'sewing',domain:'culture'}))).json();
  check(result.results.some(row=>row.id===guide),'Même document retrouvé dans l’espace corrigé');
  result=await(await page.request.get(base+'/api/search?q=sewing&domain=all')).json();check(result.results.some(row=>row.id===guide),'Toute la bibliothèque conserve le document');
  await editor.locator('summary').click();
  for(const width of [1366,390,320]){await page.setViewportSize({width,height:844});check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Classement lisible sans débordement à '+width);}
  await page.setViewportSize({width:1366,height:900});
  await editor.getByRole('button',{name:'Revenir au classement automatique',exact:true}).click();
  await page.waitForFunction(()=>!document.getElementById('reader').textContent.includes('classement examiné'));
  check(!(await page.locator('#reader').textContent()).includes('classement examiné'),'Retour au classement automatique explicite');

  await page.locator('#navigation [data-route="bibliotheque"]').click();await page.locator('.next-tabs [data-route="bibliotheque/collections"]').click();
  await page.locator('#collection-filter').fill('');
  await page.waitForSelector('#data-books [data-collection-id]',{state:'attached'});
  await page.locator('#data-books .next-collection-group').evaluateAll(nodes=>nodes.forEach(node=>node.open=true));
  const original=await page.locator('[data-collection-id="'+books[0]+'"]').getByRole('link',{name:'Ouvrir cette collection →',exact:true}).getAttribute('href');
  for(const [index,id] of books.entries()){
    const card=page.locator('[data-collection-id="'+id+'"]');const parent=card.locator('xpath=ancestor::details[contains(@class,"next-collection-group")]');if(await parent.count())await parent.evaluate(e=>e.open=true);
    await card.getByRole('button',{name:'Modifier les noms',exact:true}).click();
    const dialog=page.locator('#catalogue-collection-dialog');
    if(index===0){await page.goBack();await dialog.waitFor({state:'hidden'});await page.goForward();await dialog.waitFor({state:'visible'});check(await dialog.isVisible(),'Précédent et Suivant ferment et rouvrent le dialogue de noms');}
    await dialog.locator('[name="family"]').fill('Groupe de recette');await dialog.locator('[name="variant"]').fill(index?'Alimentation pratique':'Énergie pratique');
    await dialog.getByRole('button',{name:'Enregistrer les noms',exact:true}).click();await dialog.waitFor({state:'hidden'});
    await page.waitForFunction(id=>[...document.querySelectorAll('#data-books .data-card')].find(n=>n.dataset.collectionId===id)?.dataset.family==='Groupe de recette',id);
  }
  const group=page.locator('.next-collection-group').filter({hasText:'Groupe de recette'});await group.evaluate(e=>e.open=true);await page.waitForTimeout(80);
  check(await group.count()===1&&await group.locator('.data-card').count()===2,'Collections renommées réunies sous le même groupe');
  check(await page.locator('[data-collection-id="'+books[0]+'"]').getByRole('link',{name:'Ouvrir cette collection →',exact:true}).getAttribute('href')===original,'Lien d’ouverture inchangé après renommage');
  await page.reload();await group.waitFor();await page.waitForFunction(()=>[...document.querySelectorAll('.next-collection-group')].find(e=>e.textContent.includes('Groupe de recette'))?.open);
  check(await group.evaluate(e=>e.open),'Groupe renommé ouvert mémorisé après rechargement');
  await page.locator('#collection-filter').fill('énergie pratique');check(await page.locator('#data-books .data-card:visible').count()===1,'Recherche de collection utilise le nouveau libellé');
  await page.locator('.next-tabs [data-route="bibliotheque/recherche"]').click();await page.locator('#search-collection').selectOption('group:groupederecette');await page.locator('#library-query').fill('sewing');
  const request=page.waitForRequest(r=>r.url().includes('/api/search?')&&new URL(r.url()).searchParams.get('collection')==='group:groupederecette');await page.locator('#library-search').evaluate(form=>form.requestSubmit());await request;
  check(page.url().includes('group%3Agroupederecette'),'Filtre du groupe corrigé enregistré dans l’adresse');
  await page.goBack();await page.waitForURL(/bibliotheque\/recherche$/);
  await page.goBack();await page.waitForSelector('#collection-filter:visible');check(await page.locator('#collection-filter').inputValue()==='énergie pratique','Retour navigateur conserve le filtre de collections renommées');
  await page.locator('#navigation [data-route="appareil"]').click();await page.locator('#next-machine-tabs [data-route="appareil/reglages"]').click();await page.locator('#settings-reglages a[href="#/appareil/entretien"]').click();
  if(!await page.locator('#settings-exports').evaluate(node=>node.open))await page.locator('#settings-exports > summary').click();const downloading=page.waitForEvent('download');await page.getByRole('button',{name:'Exporter les métadonnées',exact:true}).click();const download=await downloading,chunks=[];for await(const chunk of await download.createReadStream())chunks.push(chunk);const report=JSON.parse(Buffer.concat(chunks).toString());
  check(report.kind==='SetupSurvie documentary metadata'&&report.records.filter(row=>row.id.startsWith('collection:fixture-channel')).length===2,'Métadonnées corrigées exportées');
  check(!('conversations' in report)&&report.records.every(row=>!('text' in row)&&!('user_id' in row)),'Export sans texte des documents ni données de profil');
  for(const id of books)await page.request.delete(base+'/api/admin/library/metadata?'+new URLSearchParams({source_id:'collection:'+id}),{headers});
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks};
}
