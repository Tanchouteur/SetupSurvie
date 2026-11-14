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
  await page.waitForFunction(()=>document.getElementById('search-message').textContent.includes('indisponible')&&document.querySelector('#search-results .result'));
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
  await page.route('**/api/source?id=*',r=>r.fulfill({status:404,json:{detail:'Document indisponible.'}}));
  await page.evaluate(()=>readSource('zim:wikipedia_fr/Alias'));
  check((await page.locator('#reader').textContent()).includes('L’aperçu de ce document'),'Échec de l’aperçu distinct d’une absence de document');
  const fallback=page.locator('#reader').getByRole('link',{name:'Ouvrir le document d’origine →'});
  check(await fallback.getAttribute('href').then(value=>new URL(value).pathname==='/content/wikipedia_fr/Alias'),'Accès direct conservé après échec de l’aperçu');
  check(await page.locator('#reader').getByRole('button',{name:'Réessayer',exact:true}).count()===1,'Nouvel essai disponible dans le lecteur');
  check(await page.evaluate(()=>originalSourceURL('zim:book/%2e%2e/private')===null&&originalSourceURL('zim:book/../../api')===null),'Repli de lecture refuse les chemins hors archive');
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
  await page.locator('#next-search-check-suite').selectOption('extended');
  await page.locator('#next-search-check-open').click();
  await page.waitForFunction(()=>document.getElementById('next-search-check-progress').value===32);
  check(await page.locator('#next-search-check-results .search-check-case').count()===32,'Contrôle complet des 32 demandes disponible');
  check(writes.length===postsBefore,'Contrôle complet sans appel de calcul ni téléchargement');
  const feedback=page.locator('#next-search-check-results .search-check-review select');
  await feedback.nth(0).selectOption('0');await feedback.nth(1).selectOption('no_useful');await feedback.nth(2).selectOption('uncertain');
  const extendedDownload=page.waitForEvent('download');await page.locator('#next-search-check-export').click();const extended=await extendedDownload,extendedChunks=[];for await(const chunk of await extended.createReadStream())extendedChunks.push(chunk);
  const complete=JSON.parse(Buffer.concat(extendedChunks).toString());
  check(complete.schema===2&&complete.suite==='extended'&&complete.reference.version==='2026-11-14.1'&&complete.cases.length===32,'Rapport complet avec référence versionnée');
  check(complete.review_summary.reviewed===3&&complete.review_summary.useful===1&&complete.cases[0].review.rank===1&&complete.cases[1].review.state==='no_useful'&&complete.cases[2].review.state==='uncertain','Avis humains conservés sans validation automatique');
  check(complete.cases.slice(3).every(row=>row.review.state==='unreviewed'),'Mesure terminée distincte des résultats encore à lire');
  check(await page.locator('#next-search-check-results .search-check-case a').first().getAttribute('href').then(value=>value.includes('domain=resilience')),'Lecture du résultat conserve le périmètre de test');
  for(const width of [1366,390,320]){
    await page.setViewportSize({width,height:768});check(!await page.locator('#next-search-check-dialog').evaluate(e=>e.scrollWidth>e.clientWidth),'Contrôle complet sans débordement à '+width);
  }
  await page.setViewportSize({width:1366,height:768});
  await page.locator('[data-close="next-search-check-dialog"]').click();
  await page.route('**/nouveau/search-reference.json?*',r=>r.fulfill({json:{schema:99,cases:[]}}));
  await page.locator('#next-search-check-open').click();
  await page.waitForFunction(()=>document.getElementById('next-search-check-status').textContent.includes('doit être mise à jour'));
  check(!await page.locator('#next-search-check-open').isDisabled(),'Liste de tests invalide expliquée et relance possible');
  await page.locator('[data-close="next-search-check-dialog"]').click();
  await page.unroute('**/nouveau/search-reference.json?*');await page.locator('#next-search-check-suite').selectOption('short');
  await page.route('**/api/search?*',async r=>{await new Promise(resolve=>setTimeout(resolve,250));await r.fulfill({json:{results:[],coverage:{status:'complete'}}}).catch(()=>{});});
  const requested=page.waitForRequest(r=>r.url().includes('/api/search?'));await page.locator('#next-search-check-open').click();await requested;await page.locator('#next-search-check-cancel').click();
  await page.waitForFunction(()=>document.getElementById('next-search-check-status').textContent.includes('Vérification arrêtée'));
  check(await page.locator('#next-search-check-progress').evaluate(e=>e.value<10),'Arrêt des vérifications encore en cours');
  const partialDownload=page.waitForEvent('download');await page.locator('#next-search-check-export').click();const partial=await partialDownload,partialChunks=[];for await(const chunk of await partial.createReadStream())partialChunks.push(chunk);
  check(JSON.parse(Buffer.concat(partialChunks).toString()).status==='cancelled','Rapport partiel explicitement marqué après arrêt');
  await page.locator('[data-close="next-search-check-dialog"]').click();
  await page.evaluate(async()=>{
    const original=api;
    try{
      api=(path,...args)=>path.startsWith('/search?')?new Promise(resolve=>{const query=new URLSearchParams(path.split('?')[1]).get('q');setTimeout(()=>resolve({results:[{id:'guide:'+query,title:query,language:'fr',kind:'guide',excerpt:'Fixture de concurrence'}],coverage:{status:'complete'}}),query==='ancienne-demande'?150:5);}):original(path,...args);
      $('library-query').value='ancienne-demande';const first=runSearch();$('library-query').value='nouvelle-demande';const last=runSearch();await Promise.all([first,last]);
    }finally{api=original;}
  });
  check((await page.locator('#search-message').textContent()).includes('nouvelle-demande'),'La réponse tardive ne remplace pas la dernière requête');
  check(await page.locator('#search-results .result').first().getAttribute('data-source')==='guide:nouvelle-demande','Les résultats correspondent à la requête actuelle');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks};
}
