// Intercepted local experiment only. No inference or document download.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],calls=[],errors=[],headers={Origin:base};
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers});
  const version=(await(await page.request.get(base+'/api/health')).json()).version;
  let state={schema:1,version,status:'not_started',cases:[]};
  await page.route('**/api/admin/search-experiment',r=>r.fulfill({json:state}));
  await page.route('**/api/admin/search-experiment/start',r=>{calls.push(r.request().postDataJSON());state={...state,id:'c'.repeat(32),status:'running',planned_cases:32,message:'Comparatif simulé en cours.'};return r.fulfill({status:202,json:state});});
  await page.route('**/api/admin/search-experiment/stop',r=>{calls.push('stop');state={...state,status:'cancelled',message:'Arrêt demandé.'};return r.fulfill({json:state});});
  await page.route('**/api/admin/search-experiment/review',r=>{
    const data=r.request().postDataJSON();calls.push(data);state.cases[0].judgments={...state.cases[0].judgments,...data.judgments};state.summary.splits.verification.reranked.fully_judged=1;return r.fulfill({json:state});
  });
  await page.setViewportSize({width:1366,height:900});await page.goto(base+'/#/appareil/tests?test=search');await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.user);
  if(!await page.locator('#next-search-experiment').evaluate(n=>n.open))await page.locator('#next-search-experiment > summary').click();await page.locator('#next-experiment-suite').waitFor({state:'visible'});await page.waitForFunction(()=>document.getElementById('next-experiment-mode').options.length>0);
  check(calls.length===0,'Ouvrir le comparatif ne lance pas de modèle');
  await page.locator('#next-experiment-suite').selectOption('all');await page.locator('#next-experiment-budget').selectOption('30');await page.locator('#next-experiment-form').evaluate(form=>form.requestSubmit());
  await page.waitForFunction(()=>document.getElementById('next-experiment-stop').hidden===false);
  check(calls[0].suite==='all'&&calls[0].latency_budget_seconds===30&&calls[0].mode==='rapide','Suite, modèle et délai transmis explicitement');
  check(await page.locator('#next-experiment-start').isDisabled(),'Double lancement désactivé pendant les mesures');
  await page.locator('#next-experiment-stop').click();await page.waitForFunction(()=>document.getElementById('next-experiment-status').textContent.includes('Arrêt demandé'));
  check(calls.includes('stop'),'Arrêt explicite transmis');
  const metric={measured:1,fully_judged:0,hit5:0,judged_results:0,unrelated_results:0,median_ms:1000,p95_ms:1200,errors:0};
  state={...state,status:'completed',message:'Mesures terminées.',planned_cases:1,cases:[{id:'verify-fire',query:'comment produire du feu',need:'Trouver une procédure utile, pas une mention.',domain:'resilience',coverage_complete:false,judgments:{},
    candidates:[{id:'guide:fixture.en.txt',title:'Fictional fire procedure',language:'en'},{id:'guide:mention',title:'Incidental mention',language:'en'}],methods:{baseline:{ids:['guide:mention'],elapsed_ms:1000},rewritten:{ids:['guide:fixture.en.txt','guide:mention'],elapsed_ms:2000},reranked:{ids:['guide:fixture.en.txt','guide:mention'],elapsed_ms:2300}}}],
    summary:{decision:'needs_review',enabled_by_default:false,splits:{verification:{baseline:{...metric},rewritten:{...metric},reranked:{...metric}}}}};
  await page.locator('#next-search-experiment > summary').click();await page.locator('#next-search-experiment > summary').click();
  await page.waitForFunction(()=>document.getElementById('next-experiment-status').textContent.includes('Mesures terminées'));
  await page.locator('.experiment-case > summary').click();
  check((await page.locator('.experiment-case').textContent()).includes('Recherche partielle'),'Couverture partielle visible avant le jugement');
  const link=page.locator('.experiment-candidates a').first();check((await link.getAttribute('href')).includes('source=guide%3Afixture.en.txt'),'Article directement accessible pour la relecture');
  check((await page.locator('.experiment-candidates li').first().textContent()).includes('Actuelle : absent des cinq premiers'),'Positions comparées sur le même document');
  await page.locator('.experiment-candidates select').first().selectOption('useful');await page.waitForFunction(()=>document.getElementById('next-experiment-summary').textContent.includes('1 cas entièrement relus'));
  check(calls.some(c=>c.case_id==='verify-fire'&&c.judgments?.['guide:fixture.en.txt']==='useful'),'Avis humain enregistré par document et demande');
  const downloading=page.waitForEvent('download');await page.locator('#next-experiment-export').click();const saved=await downloading,chunks=[];for await(const c of await saved.createReadStream())chunks.push(c);const report=JSON.parse(Buffer.concat(chunks).toString());
  check(/^setupsurvie-comparatif-ia.*-v[^/]+-\d{4}-\d{2}-\d{2}_\d{2}h\d{2}m\d{2}s\.json$/.test(saved.suggestedFilename()),'Nom du rapport lisible avec type, version et heure précise');
  check(report.version===version&&report.cases[0].judgments['guide:fixture.en.txt']==='useful','Rapport exporté avec version, méthodes et avis');
  check(report.summary.enabled_by_default===false&&!('messages' in report),'Aucune activation ni conversation dans le comparatif');
  state.cases[0].methods.rewritten.error='latency_budget';await page.locator('#next-search-experiment > summary').click();await page.locator('#next-search-experiment > summary').click();
  await page.waitForFunction(()=>document.getElementById('next-experiment-cases').textContent.includes('Délai choisi atteint'));
  if(!await page.locator('.experiment-case').evaluate(e=>e.open))await page.locator('.experiment-case > summary').click();
  check((await page.locator('.experiment-case').textContent()).includes('Résultats précédents conservés'),'Délai choisi atteint expliqué sans perdre les résultats');
  for(const width of [1366,390,320]){await page.setViewportSize({width,height:844});check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Comparatif sans débordement à '+width);}
  await page.setViewportSize({width:1366,height:900});await page.reload();await page.waitForFunction(()=>S.authReady&&S.user);if(!await page.locator('#next-search-experiment').evaluate(e=>e.open))await page.locator('#next-search-experiment > summary').click();await page.waitForFunction(()=>document.querySelector('.experiment-case'));
  await page.locator('.experiment-case > summary').click();check(await page.locator('.experiment-candidates select').first().inputValue()==='useful','Avis conservé après rechargement');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks};
}
