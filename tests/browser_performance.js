// Intercepted campaign state, no host stress or inference.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],calls=[],errors=[],headers={Origin:base};
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers});
  let state={schema:1,id:'a'.repeat(32),version:'fixture',status:'not_started',sample_count:0,steps:[],message:'Aucun essai lancé.'};
  await page.route('**/api/admin/performance',route=>route.fulfill({json:state}));
  await page.route('**/api/admin/performance/start',route=>{
    calls.push({start:route.request().postDataJSON()});state={...state,status:'running',current_phase:'reading',message:'Mesures en cours…',sample_count:4,host_sample_count:4,steps:[{id:'search-1',kind:'classical',query:'faire du feu',repeat:1,status:'completed',elapsed_ms:1200}]};return route.fulfill({status:202,json:state});
  });
  await page.route('**/api/admin/performance/stop',route=>{calls.push('stop');state={...state,status:'cancelled',message:'Essai arrêté à votre demande.'};return route.fulfill({json:state});});
  await page.route('**/api/admin/performance/report',route=>route.fulfill({json:{...state,samples:[{source:'host_controller',available:true,elapsed_ms:3000,cpu:{percent:75,max_core_percent:99},disks:[{id:'0 D:',data_disk:true,busy_percent:80}],memory:{available:8*1024**3},gpus:[{used:7*1024**3,total:8*1024**3}]}]}}));
  await page.goto(base+'/#/appareil/entretien');await page.waitForFunction(()=>S.authReady&&document.getElementById('next-performance-mode').options.length>0);
  const panel=page.locator('#next-performance');await panel.waitFor({state:'visible'});
  check(calls.length===0,'Ouvrir Entretien ne lance aucun essai');
  check(await panel.locator('#next-performance-export').isDisabled(),'Pas de faux rapport avant le premier essai');
  await page.locator('#next-performance-start').click();await page.locator('#next-performance-stop').waitFor({state:'visible'});
  check(calls.length===1&&calls[0].start.mode==='rapide','Une seule commande lance la campagne avec le mode choisi');
  check(await page.locator('#next-performance-start').isDisabled(),'Le double lancement est désactivé');
  check((await page.locator('#next-performance-status').textContent()).includes('Lecture'),'Étape de travail affichée pendant les mesures');
  await page.goto(base+'/#/bibliotheque');await page.goto(base+'/#/appareil/entretien');await page.locator('#next-performance-stop').waitFor({state:'visible'});
  check(calls.length===1,'Naviguer et recharger retrouve le test sans le relancer');
  await page.locator('#next-performance-stop').click();await page.waitForFunction(()=>document.getElementById('next-performance-status').textContent.includes('arrêté'));
  check(calls.includes('stop'),'Le bouton d’arrêt conserve le rapport partiel');
  state={...state,status:'completed',message:'Mesures terminées.',steps:[...state.steps,{id:'generation-1',kind:'generation',repeat:1,status:'completed',elapsed_ms:30000},{id:'documentary-1',kind:'documentary',repeat:1,status:'failed',reason:'memory_error',elapsed_ms:15000}]};
  await page.waitForFunction(()=>document.getElementById('next-performance-results').textContent.includes('mémoire insuffisante'));
  check((await page.locator('#next-performance-results').textContent()).includes('Rédaction sans documents'),'Rédaction seule distincte de la réponse documentaire');
  const downloading=page.waitForEvent('download');await page.locator('#next-performance-export').click();const saved=await downloading,chunks=[];
  for await(const chunk of await saved.createReadStream())chunks.push(chunk);
  const report=JSON.parse(Buffer.concat(chunks).toString());
  check(report.samples[0].source==='host_controller'&&report.steps.length===3,'Export des étapes et des ressources du serveur dans un fichier');
  check(report.samples[0].disks[0].data_disk&&report.samples[0].cpu.max_core_percent===99,'Compteurs disque et CPU par cœur présents dans le rapport');
  check(!('answer' in report)&&!('messages' in report),'Rapport numérique sans conversation ni réponse');
  for(const width of [1366,390,320]){await page.setViewportSize({width,height:844});await page.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth);check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Diagnostic lisible à '+width);}
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks};
}
