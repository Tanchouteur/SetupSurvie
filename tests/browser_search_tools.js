// New scopes and preparation commands on simulated server data, never real jobs.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],calls=[],queries=[];
  const check=(ok,text)=>{if(!ok)throw Error(text);checks.push(text);};
  await page.goto('about:blank');
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.route('**/api/admin/library',r=>r.fulfill({json:{phase:'idle',index_reader_ready:true,index_queue:{pending:2,completed:1,hold:'',settings:{enabled:true,start_hour:22,end_hour:6,workers:0}},search_index:{archives:3,completed:2,articles:123},message:'Fixture d’indexation'}}));
  await page.route('**/api/admin/library/index-settings',r=>{calls.push(r.request().postDataJSON());return r.fulfill({json:{accepted:true}});});
  await page.route('**/api/admin/library/index/*',r=>{calls.push(new URL(r.request().url()).pathname);return r.fulfill({json:{accepted:true}});});
  let contexts=[{model:'gpt-oss:20b',tokens:16384},{model:'gemma4:e4b',tokens:8192}];
  await page.route('**/api/admin/context',async r=>{
    if(r.request().method()==='POST'){const data=r.request().postDataJSON();calls.push(data);contexts=contexts.map(row=>row.model===data.model?data:row);return r.fulfill({json:data});}
    return r.fulfill({json:{models:contexts}});
  });
  await page.route('**/api/search?*',r=>{const params=new URL(r.request().url()).searchParams;queries.push(Object.fromEntries(params));return r.fulfill({json:{results:[],coverage:{status:'partial',domain:params.get('domain')}}});});
  await page.setViewportSize({width:1366,height:900});await page.goto(base+'/#/bibliotheque/recherche?q=feu&domain=resilience');
  await page.waitForFunction(()=>S.authReady&&S.user&&!S.loadingConversation);
  await page.getByRole('button',{name:'Élargir à toute la bibliothèque'}).waitFor();
  check(queries.at(-1).domain==='resilience','Périmètre résilience transmis au moteur');
  await page.getByRole('button',{name:'Élargir à toute la bibliothèque'}).click();
  await page.waitForFunction(()=>document.querySelector('#search-domain').value==='all'&&location.hash.includes('domain=all'));
  check(queries.at(-1).domain==='all','Élargissement global visible et transmis');
  await page.reload();await page.waitForFunction(()=>document.querySelector('#search-domain')?.value==='all');
  check(queries.at(-1).domain==='all','Périmètre conservé au rechargement');
  await page.locator('#search-domain').selectOption('culture');await page.waitForFunction(()=>location.hash.includes('domain=culture'));
  await page.goBack();await page.waitForFunction(()=>document.querySelector('#search-domain').value==='all');check(true,'Retour navigateur restaure le périmètre');
  await page.locator('#navigation [data-route="appareil"]').click();await page.locator('[data-route="appareil/reglages"]').click();
  await page.waitForFunction(()=>document.querySelector('#next-index-status').textContent.includes('123'));
  check((await page.locator('#next-index-prepare').textContent()).includes('réparer'),'Outil déjà préparé reconnu et réparable');
  const indexStarted=page.waitForResponse(response=>new URL(response.url()).pathname==='/api/admin/library/index/start'&&response.request().method()==='POST');
  await page.locator('#next-index-start').click();await indexStarted;check(calls.includes('/api/admin/library/index/start'),'Indexation lancée par la commande dédiée');
  await page.locator('#next-index-settings').locator('..').locator('summary').click();
  await page.locator('#next-index-from').selectOption('23');await page.locator('#next-index-settings').evaluate(f=>f.requestSubmit());
  await page.waitForFunction(()=>document.getElementById('next-index-settings-status').textContent.includes('enregistrée'));
  check(calls.some(row=>row.enabled===true&&row.start_hour===23&&row.end_hour===6),'Plage nocturne transmise au serveur');
  const downloading=page.waitForEvent('download');await page.locator('#next-index-export').click();const download=await downloading,parts=[];for await(const chunk of await download.createReadStream())parts.push(chunk);const report=JSON.parse(Buffer.concat(parts).toString());
  check(report.index_queue.pending===2&&!('conversations' in report),'Rapport d’indexation exporté sans conversations');
  await page.locator('#next-context-size').selectOption('32768');await page.locator('#next-context-form').evaluate(f=>f.requestSubmit());
  await page.waitForFunction(()=>document.querySelector('#next-context-status').textContent.includes('enregistré'));
  check(calls.some(row=>row.model==='gpt-oss:20b'&&row.tokens===32768),'Contexte sauvegardé par modèle');
  await page.locator('#next-context-model').selectOption('gemma4:e4b');check(await page.locator('#next-context-size').inputValue()==='8192','Autre modèle conserve son réglage');
  check(await page.locator('#chat-domain').count()===1,'Choix du périmètre dans l’assistant');
  for(const width of [1366,390,320]){await page.setViewportSize({width,height:850});check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Réglages sans débordement à '+width);}
  return {checks:checks.length,results:checks};
}
