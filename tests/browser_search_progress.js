// Real streamed HTTP from the tiny fixture API; its documents/delays are fictional.
async page=>{
  const base='http://10.0.3.2:8772',checks=[],errors=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  const gate=async(query,hold)=>{const reply=await page.request.post(base+'/fixture/search-gate?'+new URLSearchParams({query,hold:String(hold)}),{headers:{Origin:base}});if(!reply.ok())throw Error('Fixture gate unavailable');};
  page.on('pageerror',error=>errors.push(error.message));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.setViewportSize({width:1366,height:900});
  await gate('fixture-progress-one',true);await page.goto(base+'/#/bibliotheque/recherche?q=fixture-progress-one&domain=all');
  await page.waitForFunction(()=>document.querySelectorAll('#search-results .result').length===1&&document.getElementById('search-stop'));
  check((await page.locator('#search-message').textContent()).includes('Recherche en cours'),'Premier résultat visible pendant que les autres collections restent en cours');
  check(await page.locator('#search-results .result h3').first().textContent()==='Premier document fictif','Premier document reçu sans attendre la réponse finale');
  await page.locator('#search-results .other-matches summary').click();
  await page.locator('#search-results .other-matches button').focus();
  await gate('fixture-progress-one',false);
  await page.waitForFunction(()=>document.querySelectorAll('#search-results .result').length===2&&!document.getElementById('search-stop'));
  check(await page.locator('#search-results .other-matches').evaluate(node=>node.open),'Les passages ouverts restent dépliés quand arrivent les autres documents');
  check(await page.locator('#search-results .other-matches button').evaluate(node=>node===document.activeElement),'La navigation au clavier est conservée pendant les résultats progressifs');
  check(!(await page.locator('#search-message').textContent()).includes('Recherche en cours'),'Fin de recherche distincte des premiers résultats');
  check((await page.locator('#search-message').textContent()).includes('2 document(s)'),'Dernière réponse complète les résultats');
  const request=async query=>{if(!await page.locator('#library-query').isVisible())await page.locator('#reader').getByRole('button',{name:'← Résultats',exact:true}).click();await page.locator('#library-query').fill(query);await page.locator('#library-search').evaluate(form=>form.requestSubmit());};
  for(const suffix of ['complete','partial','stop','error']){
    const query='fixture-progress-empty-'+suffix;await gate(query,true);await request(query);
    await page.waitForFunction(()=>document.querySelector('#search-message').textContent.includes('Recherche en cours — aucun résultat pour le moment')&&document.querySelector('#search-stop'));
    check(!(await page.locator('#search-message').textContent()).includes('0 document(s) trouvé(s)'),'Aucun résultat provisoire annoncé comme un total final : '+suffix);
    check((await page.locator('#search-results .empty-panel').textContent()).includes('La recherche continue'),'Attente expliquée aussi dans la liste vide : '+suffix);
    if(suffix==='stop')await page.locator('#search-stop').click();
    await gate(query,false);await page.waitForFunction(()=>!document.getElementById('search-stop'));
    const message=await page.locator('#search-message').textContent(),empty=await page.locator('#search-results .empty-panel').textContent();
    check(!message.includes('Recherche en cours')&&!empty.includes('La recherche continue'),'Aucun faux suivi actif après la fin ou interruption : '+suffix);
    check(await page.locator('#search-results').getAttribute('aria-busy')==='false','Fin de traitement accessible aux lecteurs d’écran : '+suffix);
    check(suffix==='complete'?message.includes('Recherche terminée — aucun résultat trouvé'):suffix==='partial'?message.includes('Recherche terminée, mais incomplète'):message.includes(suffix==='stop'?'arrêtée':'interrompue'),'Fin complète, partielle, arrêt et erreur distingués : '+suffix);
  }
  await gate('fixture-progress-stop',true);await request('fixture-progress-stop');await page.waitForFunction(()=>document.querySelectorAll('#search-results .result').length===1&&document.getElementById('search-stop'));
  await page.locator('#search-stop').click();
  check((await page.locator('#search-message').textContent()).includes('résultats reçus sont conservés'),'Arrêt annoncé comme incomplet avec résultats conservés');
  await gate('fixture-progress-stop',false);
  await page.waitForTimeout(900);check(await page.locator('#search-results .result').count()===1,'La réponse finale tardive ne remplit pas une recherche arrêtée');
  await gate('fixture-progress-error',true);await request('fixture-progress-error');await page.waitForFunction(()=>document.querySelectorAll('#search-results .result').length===1&&document.getElementById('search-stop'));
  await gate('fixture-progress-error',false);
  await page.waitForFunction(()=>document.getElementById('search-message').textContent.includes('interrompue'));
  check(await page.locator('#search-results .result').count()===1,'Erreur du flux conserve les résultats déjà reçus');
  check(!(await page.locator('#search-message').textContent()).includes('PRIVATE'),'Erreur technique exportée sous un message public');
  await gate('fixture-progress-read',true);await request('fixture-progress-read');await page.waitForFunction(()=>document.querySelectorAll('#search-results .result').length===1&&document.getElementById('search-stop'));
  await page.locator('#search-results .result button').first().click();
  await page.waitForFunction(()=>!document.getElementById('reader').hidden&&document.getElementById('reader').textContent.includes('Shelter'));
  const readingDuringSearch=await page.locator('#reader').isVisible()&&await page.locator('#search-stop').count()===1;
  await gate('fixture-progress-read',false);
  await page.waitForFunction(()=>!document.getElementById('search-stop'));
  check(readingDuringSearch&&await page.locator('#reader').isVisible(),'Lire un document reste possible pendant la recherche');
  await page.reload();await page.waitForFunction(()=>S.authReady&&document.getElementById('library-query').value==='fixture-progress-read');
  await page.waitForFunction(()=>!document.getElementById('search-stop')&&document.querySelectorAll('#search-results .result').length===2);
  check((await page.locator('#library-query').inputValue())==='fixture-progress-read','Rechargement conserve la demande avec le flux progressif');
  for(const width of [1366,390,320]){
    const query='fixture-progress-layout'+width;await gate(query,true);await page.setViewportSize({width,height:844});await request(query);
    await page.waitForFunction(()=>document.querySelectorAll('#search-results .result').length===1&&document.getElementById('search-stop'));
    check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Résultats et arrêt accessibles sans débordement à '+width);
    await gate(query,false);await page.waitForFunction(()=>!document.getElementById('search-stop'));
  }
  await page.route('**/api/search?*',route=>{const url=new URL(route.request().url());url.searchParams.set('q','fixture-progress-report');return route.continue({url:url.toString()});});
  await page.goto(base+'/#/appareil/tests?test=search');await page.locator('#next-search-check-open').click();
  await page.waitForFunction(()=>document.getElementById('next-search-check-progress').value===10);
  const downloading=page.waitForEvent('download');await page.locator('#next-search-check-export').click();const download=await downloading,chunks=[];
  for await(const chunk of await download.createReadStream())chunks.push(chunk);const report=JSON.parse(Buffer.concat(chunks).toString());
  const times=report.cases.map(row=>({first:row.first_results_ms,total:row.elapsed_ms,updates:row.updates_received,error:row.error}));
  const coherent=times.every(row=>Number.isFinite(row.first)&&row.first>=0&&row.first<=row.total);
  check(coherent,'Rapport distingue première réception et durée totale, même si les paquets arrivent ensemble'+(coherent?'':JSON.stringify(times)));
  check(report.cases.every(row=>row.updates_received>0&&!row.error),'Rapport conserve le nombre de mises à jour progressives reçues');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks,real_model:false,real_corpus:false};
}
