// UI contract on tiny simulated data. Actual Kiwix protocol is tested separately.
async page => {
  const base='http://10.0.3.2:8769',checks=[],errors=[],searches=[],writes=[];
  const check=(value,label)=>{if(!value)throw Error(label);checks.push(label);};
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.method()==='POST')writes.push(new URL(r.url()).pathname);});
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.route('**/api/inventory',async r=>{
    const data=await(await r.fetch()).json();data.books=[
      {id:'canadian-prepper_en_preppingfood_2026-01',title:'Canadian Prepper',family:'Canadian Prepper',variant:'Alimentation',archive_name:'canadian-prepper_en_preppingfood_2026-01.zim',language:'Anglais',version:'2026-01',ready:true,url:'/content/food/',description:'Collection vidéo fictive'},
      {id:'canadian-prepper_en_preppinggear_2026-01',title:'Canadian Prepper',family:'Canadian Prepper',variant:'Équipement',archive_name:'canadian-prepper_en_preppinggear_2026-01.zim',language:'Anglais',version:'2026-01',ready:true,url:'/content/gear/',description:'Collection vidéo fictive'},
      {id:'wikipedia_fr_2026-01',title:'Wikipédia',family:'Wikipédia',variant:'Collection complète',language:'Français',version:'2026-01',ready:true,url:'/content/wiki/',description:'Encyclopédie fictive'}
    ];return r.fulfill({json:data});
  });
  await page.route('**/api/search?*',r=>{const params=new URL(r.request().url()).searchParams;searches.push(Object.fromEntries(params));return r.fulfill({json:{results:[{id:'guide:shelter.en.pdf#page=2',kind:'guide',title:'Document de recette — page 2',language:'en',excerpt:'Extrait fictif pour vérifier la présentation.',other_matches:[{id:'guide:shelter.en.pdf#page=3',title:'Même document — page 3',url:'/guides/shelter.en.pdf#page=3'}]}],coverage:{status:'partial',collection:params.get('collection'),warning:'Une collection de démonstration reste indisponible.'}}});});
  await page.setViewportSize({width:1440,height:900});await page.goto(base+'/#/bibliotheque/collections');
  await page.waitForFunction(()=>S.authReady&&S.user&&!S.loadingConversation);
  const group=page.locator('.next-collection-group').filter({hasText:'Canadian Prepper'});
  await group.waitFor();check(await group.count()===1,'Une seule famille Canadian Prepper');
  if(!await group.evaluate(e=>e.open))await group.locator(':scope > summary').click();
  check(await group.locator('h3').allTextContents().then(v=>v.includes('Alimentation')&&v.includes('Équipement')),'Sous-collections nommées distinctement');
  check(await group.locator('a').evaluateAll(nodes=>nodes.every(a=>a.href.includes('/content/'))),'Ouverture directe de chaque archive conservée');
  await page.screenshot({path:'/artifacts/collections-regroupees.png',fullPage:true});
  await page.locator('#collection-filter').fill('alimentation');
  check(await page.locator('#data-books .data-card:visible').count()===1,'Filtre français dans les sous-collections regroupées');
  await page.locator('#collection-filter-clear').click();
  await group.evaluate(e=>e.open=true);await page.waitForTimeout(80);
  await page.reload();await group.waitFor();await page.waitForFunction(()=>document.querySelector('.next-collection-group')?.open);
  check(await group.evaluate(e=>e.open),'Groupe ouvert mémorisé au rechargement');
  await page.locator('.next-tabs [data-route="bibliotheque/recherche"]').click();
  await page.locator('#search-collection').selectOption('wikipedia');await page.locator('#library-query').fill('faire du feu');
  await page.locator('#library-search').evaluate(f=>f.requestSubmit());await page.waitForSelector('#search-results .result');
  check(searches.at(-1).collection==='wikipedia','Filtre de collection transmis au moteur commun');
  check(page.url().includes('collection=wikipedia'),'Filtre de collection dans l’adresse');
  await page.reload();await page.waitForSelector('#search-results .result');
  check(searches.at(-1).collection==='wikipedia','Filtre conservé au rechargement avant chargement de l’inventaire');
  check((await page.locator('#search-message').textContent()).includes('indisponible'),'Recherche partielle expliquée');
  await page.screenshot({path:'/artifacts/recherche-pertinence.png',fullPage:true});
  check(await page.locator('.other-matches').count()===1,'Autres pages regroupées sous le document');
  await page.locator('.other-matches summary').click();await page.locator('.other-matches button').click();
  await page.waitForSelector('#reader .reader-actions');check(page.url().includes(encodeURIComponent('#page=3')),'Bonne page après ouverture d’un passage regroupé');
  await page.locator('#reader .reader-actions').getByRole('button',{name:'Traduire en français',exact:true}).click();
  check(await page.locator('#translation-panel').evaluate(e=>e.open),'Traduction accessible depuis le haut du lecteur');
  check(!writes.includes('/api/translations'),'Ouvrir la traduction ne lance pas de calcul automatiquement');
  await page.route('**/api/source?id=*',r=>r.fulfill({json:{id:'guide:template.fr.md',title:'Modèle fictif',language:'fr',kind:'guide',url:'/guides/template.fr.md',text:'# Équipements\n\n| Objet | Notice |\n| --- | --- |\n| Exemple | À joindre |\n\n<script>window.unsafeFixture=true</script>'}}));
  await page.evaluate(()=>readSource('guide:template.fr.md'));await page.waitForSelector('#reader .reader-body table');
  check(await page.locator('#reader .reader-body h1').textContent()==='Équipements','Titres Markdown lisibles');
  check(!await page.evaluate(()=>window.unsafeFixture),'Document Markdown assaini');
  let stage='searching';
  await page.route('**/api/jobs/phase-fixture',r=>r.fulfill({json:{id:'phase-fixture',created:Date.now()/1000-5,mode:'rapide',status:stage==='done'?'done':'running',answer:stage==='done'?'Réponse fictive terminée.':'',sources:[],progress:{stage,sources_found:2,sources_read:stage==='reading'?1:0}}}));
  await page.evaluate(()=>{newConversation();watch('phase-fixture');});
  await page.waitForFunction(()=>document.getElementById('chat-status').textContent.includes('Recherche dans la bibliothèque'));
  check((await page.locator('#chat-status').textContent()).includes('2 résultat(s)'),'Recherche et nombre de résultats visibles pendant l’attente');
  stage='reading';await page.waitForFunction(()=>document.getElementById('chat-status').textContent.includes('1 source(s) consultée(s)'));
  check((await page.locator('#chat-status').textContent()).includes('Lecture des documents'),'Lecture distincte de la rédaction');
  stage='done';await page.waitForFunction(()=>S.job===null);
  for(const [width,height] of [[1366,768],[390,844],[320,568]]){
    await page.setViewportSize({width,height});check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Pas de débordement à '+width);
  }
  check((await page.locator('[data-route="bibliotheque/parcours"]').textContent()).includes('Apprendre par thème'),'Parcours renommé par son usage');
  await page.setViewportSize({width:1366,height:768});
  await page.locator('#navigation [data-route="appareil"]').click();await page.locator('#next-machine-tabs [data-route="appareil/reglages"]').click();
  const postsBefore=writes.length;await page.locator('#next-search-check-open').click();
  await page.waitForFunction(()=>document.getElementById('next-search-check-progress').value===10);
  check(await page.locator('#next-search-check-results .search-check-case').count()===10,'Recette des dix recherches disponible depuis le site');
  check(writes.length===postsBefore,'Recette de recherche sans appel de calcul ni téléchargement');
  const downloading=page.waitForEvent('download');await page.locator('#next-search-check-export').click();const saved=await downloading;
  const chunks=[];for await(const chunk of await saved.createReadStream())chunks.push(chunk);const report=JSON.parse(Buffer.concat(chunks).toString());
  check(report.status==='measured'&&report.cases.length===10,'Rapport exporté sans confondre mesure et validation');
  check(report.version===await page.evaluate(()=>S.status.version),'Version réelle du serveur dans le rapport');
  check(!('conversations' in report)&&!('user' in report),'Rapport limité aux recherches de test');
  await page.screenshot({path:'/artifacts/controle-recherche.png',fullPage:true});
  await page.locator('[data-close="next-search-check-dialog"]').click();
  await page.route('**/api/search?*',async r=>{await new Promise(resolve=>setTimeout(resolve,250));await r.fulfill({json:{results:[],coverage:{status:'complete'}}}).catch(()=>{});});
  const requested=page.waitForRequest(r=>r.url().includes('/api/search?'));await page.locator('#next-search-check-open').click();await requested;await page.locator('#next-search-check-cancel').click();
  await page.waitForFunction(()=>document.getElementById('next-search-check-status').textContent.includes('Vérification arrêtée'));
  check(await page.locator('#next-search-check-progress').evaluate(e=>e.value<10),'Arrêt des vérifications encore en cours');
  const partialDownload=page.waitForEvent('download');await page.locator('#next-search-check-export').click();const partial=await partialDownload,partialChunks=[];for await(const chunk of await partial.createReadStream())partialChunks.push(chunk);
  check(JSON.parse(Buffer.concat(partialChunks).toString()).status==='cancelled','Rapport partiel explicitement marqué après arrêt');
  await page.locator('[data-close="next-search-check-dialog"]').click();
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks};
}
