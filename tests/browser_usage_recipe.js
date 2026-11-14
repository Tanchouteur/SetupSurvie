// Guided acceptance on tiny fixture documents, without a model or real outage.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],calls=[],errors=[],headers={Origin:base};
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  const deferred=[];let blockSearch=false,blockHealth=false,healthVersion=null,healthCalls=0,changeAtEnd=false,degraded=false;
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>calls.push({url:request.url(),method:request.method()}));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers});
  const version=(await(await page.request.get(base+'/api/health')).json()).version;
  const answer=async(route,value,status=200)=>{try{await route.fulfill({status,json:value});}catch(_){} };
  await page.route('**/api/health',async route=>{
    healthCalls++;const current=healthCalls;
    if(blockHealth){blockHealth=false;await new Promise(resolve=>deferred.push(resolve));}
    await answer(route,{ok:true,version:healthVersion||(changeAtEnd&&current%2===0?version+'-changed':version)});
  });
  await page.route('**/api/inference',route=>answer(route,{control_available:!degraded,online:false,paused:true}));
  await page.route('**/api/library/search-diagnostic',route=>answer(route,{kiwix:{state:degraded?'unavailable':'reachable'},catalog:{state:degraded?'stale':'live',collections:2},guides:{indexed:1},archive_index:{phase:'completed',results:[{private:'MANIFEST_SENTINEL'}]}}));
  await page.route('**/api/search?*',async route=>{
    if(blockSearch)await new Promise(resolve=>deferred.push(resolve));
    await answer(route,{results:[{id:'guide:shelter.en.txt',title:'Tiny fictional fixture',language:'en',kind:'guide',excerpt:'EXCERPT_SENTINEL'},{id:'zim:fixture_fr/A/Feu',title:'Second fictional fixture',language:'fr',kind:'article'},{id:'guide:third.txt',title:'Not read automatically'},{id:'zim:../../unsafe',title:'Rejected path'}],coverage:{status:degraded?'partial':'complete'}});
  });
  await page.route('**/api/source?*',route=>{
    const id=new URL(route.request().url()).searchParams.get('id');
    return degraded&&id.startsWith('zim:')?answer(route,{detail:'Fixture inaccessible'},404):answer(route,{id,text:'SOURCE_SENTINEL',preview:true});
  });
  const download=async()=>{const pending=page.waitForEvent('download');await page.locator('#next-usage-export').click();const file=await pending,parts=[];for await(const chunk of await file.createReadStream())parts.push(chunk);return JSON.parse(Buffer.concat(parts).toString());};
  const ready=()=>page.waitForFunction(()=>S.authReady&&S.user&&S.status);
  const open=()=>page.locator('#next-usage-open').click();
  const measured=()=>page.waitForFunction(()=>document.querySelector('#next-usage-status').textContent.includes('Contrôles terminés'));
  await page.setViewportSize({width:1366,height:900});await page.goto(base+'/#/appareil/reglages');await ready();
  const initial=calls.length;await open();
  check(calls.slice(initial).every(call=>!call.url.includes('/api/search?')&&!call.url.includes('/api/source?')),'Ouvrir le contrôle ne lance pas ses recherches');
  check(await page.locator('[data-usage-step]').count()===14&&await page.locator('[data-usage-step]').evaluateAll(nodes=>nodes.every(node=>node.value==='unperformed')),'Toutes les observations humaines commencent à Non effectué');
  await page.locator('#next-usage-network').selectOption('disconnected');await page.locator('#next-usage-device').selectOption('windows');
  await page.locator('#next-usage-note').fill('Observation fictive à conserver');
  await page.locator('#next-usage-dialog summary').getByText('Étapes vérifiées par vous',{exact:true}).click();
  await page.locator('[data-usage-step="original"]').selectOption('passed');await page.locator('[data-usage-step="pdf"]').selectOption('failed');
  await page.locator('#next-usage-dialog summary').getByText('Après une maintenance prévue ou sur une copie d’essai',{exact:true}).click();
  await page.locator('[data-usage-step="faults"]').selectOption('not_applicable');
  check(await page.locator('#next-usage-network').isDisabled(),'Les conditions restent associées aux observations déjà faites');
  const before=calls.length;await page.locator('#next-usage-run').click();await measured();let report=await download();
  check(report.version===version&&report.kind==='usage_recipe'&&report.status==='measured'&&report.measurements.length===10,'Rapport daté de la version réelle avec dix mesures distinctes');
  const own=calls.slice(before);
  check(own.filter(call=>call.url.includes('/api/search?')).length===2&&own.filter(call=>call.url.includes('/api/source?')).length===2,'Deux recherches et deux aperçus au maximum');
  check(own.every(call=>call.method==='GET'&&call.url.startsWith(base+'/')),'Les contrôles font seulement des lectures locales, sans commande IA ni téléchargement');
  check(report.measurements.filter(row=>row.id.startsWith('engine_')).every(row=>row.state==='passed'&&row.online===false),'Arrêt du moteur vérifié séparément avant et après');
  check(report.context.internet_evidence==='operator_declaration'&&report.context.network==='disconnected'&&(await page.locator('#next-usage-status').textContent()).includes('pas une détection automatique'),'La coupure Internet reste une déclaration humaine');
  check(report.summary.human_reviewed===2&&report.summary.human_failed===1&&report.summary.human_not_applicable===1&&report.summary.human_unperformed===11,'Essai réussi, échec, non applicable et non effectué restent distincts');
  check(!/SOURCE_SENTINEL|EXCERPT_SENTINEL|MANIFEST_SENTINEL/.test(JSON.stringify(report))&&!('user_id' in report),'Export sans texte de document, manifeste détaillé ni identité du profil');
  check((await page.locator('[data-usage-measure="source"] a').first().getAttribute('href')).includes('source=guide%3Ashelter.en.txt'),'La relecture humaine garde un accès au document');
  await page.locator('[data-close="next-usage-dialog"]').click();await open();
  check(await page.locator('[data-usage-measure]').count()===10,'Fermer et rouvrir conserve les mesures de la page');
  await page.reload();await ready();await open();report=await download();
  check(report.measurements.length===0&&report.status==='draft'&&report.manual.find(row=>row.id==='original').state==='passed'&&report.note==='Observation fictive à conserver','Rechargement retrouve les observations, sans recycler les anciennes mesures');
  await page.locator('[data-close="next-usage-dialog"]').click();
  await page.request.post(base+'/api/profiles/select',{data:{id:'local-family'},headers});await page.reload();await ready();await open();
  check(await page.locator('[data-usage-step]').evaluateAll(nodes=>nodes.every(node=>node.value==='unperformed'))&&await page.locator('#next-usage-note').inputValue()==='','Les observations d’un autre profil restent séparées');
  await page.locator('[data-close="next-usage-dialog"]').click();
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers});await page.reload();await ready();await open();
  check(await page.locator('[data-usage-step="original"]').inputValue()==='passed','Retour au premier profil retrouve son essai');
  degraded=true;await page.locator('#next-usage-run').click();await measured();report=await download();
  check(report.measurements.find(row=>row.id==='resilience').coverage==='partial'&&report.measurements.find(row=>row.id==='diagnostic').state==='unverified','Recherche partielle et catalogue dégradé restent signalés');
  check(report.measurements.filter(row=>row.id.startsWith('engine_')).every(row=>row.state==='unverified'),'Contrôleur absent ne prouve pas que l’IA est arrêtée');
  check(report.measurements.filter(row=>row.id==='source').some(row=>row.state==='failed')&&report.measurements.some(row=>row.id==='health_after'),'Un aperçu indisponible conserve les autres contrôles');
  degraded=false;blockSearch=true;const waiting=page.waitForRequest(request=>request.url().includes('/api/search?'));await page.locator('#next-usage-run').click();await waiting;
  check(await page.locator('#next-usage-run').isDisabled(),'Un contrôle en cours empêche le double lancement');
  await page.locator('#next-usage-cancel').click();await page.waitForFunction(()=>document.querySelector('#next-usage-cancel').hidden);
  blockSearch=false;while(deferred.length)deferred.shift()();report=await download();
  check(report.status==='cancelled'&&report.measurements.length>0&&report.measurements.length<10,'Arrêt conserve et exporte seulement les mesures reçues');
  await page.locator('#next-usage-new').click();await page.locator('#next-usage-run').click();await measured();report=await download();
  check(report.status==='measured'&&report.measurements.length===10&&report.context.network==='unknown'&&report.summary.human_reviewed===0,'Nouvel essai repart sans les résultats ni conditions du précédent');
  check((await page.locator('#next-usage-status').textContent()).includes('ne démontre pas un usage sans Internet'),'Une connexion non précisée ne devient pas une preuve hors ligne');
  blockSearch=true;const profileWaiting=page.waitForRequest(request=>request.url().includes('/api/search?'));await page.locator('#next-usage-run').click();await profileWaiting;blockSearch=false;
  await page.request.post(base+'/api/profiles/select',{data:{id:'local-family'},headers});
  const profileClosed=await page.evaluate(()=>{S.user={id:'local-family',role:'admin',name:'Famille'};accountUI();const closed=!document.getElementById('next-usage-dialog').open;document.getElementById('next-usage-open').click();document.getElementById('next-usage-run').click();return closed;});
  await measured();while(deferred.length)deferred.shift()();report=await download();
  check(profileClosed&&report.measurements.length===10&&report.summary.human_reviewed===0,'Changement de profil annule l’ancien contrôle sans interrompre le nouveau');
  await page.locator('[data-close="next-usage-dialog"]').click();await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers});await page.reload();await ready();await open();
  await page.evaluate(()=>{const save=Storage.prototype.setItem;window.restoreUsageStorage=()=>{Storage.prototype.setItem=save;};Storage.prototype.setItem=function(key,value){if(key.startsWith('survie-usage-v1:'))throw new DOMException('Fixture full','QuotaExceededError');return save.call(this,key,value);};});
  await page.locator('#next-usage-note').fill('Observation gardée malgré mémoire indisponible');report=await download();
  check((await page.locator('#next-usage-status').textContent()).includes('mémoire de ce navigateur est indisponible')&&report.note==='Observation gardée malgré mémoire indisponible','Mémoire du navigateur indisponible expliquée sans perdre l’export');await page.evaluate(()=>window.restoreUsageStorage());
  healthVersion=version+'-changed';const beforeVersion=calls.filter(call=>call.url.includes('/api/search?')).length;
  await page.locator('#next-usage-run').click();await page.waitForFunction(()=>document.querySelector('#next-usage-status').textContent.includes('version du serveur a changé'));report=await download();
  check(report.status==='version_changed'&&report.version===version&&report.measurements[0].observed_version===healthVersion&&calls.filter(call=>call.url.includes('/api/search?')).length===beforeVersion,'Changement de version arrête le contrôle avant de mélanger ses résultats');
  healthVersion=null;healthCalls=0;changeAtEnd=true;await page.locator('#next-usage-run').click();await page.waitForFunction(()=>document.querySelector('#next-usage-status').textContent.includes('version du serveur a changé'));report=await download();
  check(report.status==='version_changed'&&report.measurements.at(-1).id==='health_after','La version est aussi contrôlée à la fin');changeAtEnd=false;
  for(const width of [1366,390,320]){
    await page.setViewportSize({width,height:844});
    check(!await page.locator('#next-usage-dialog').evaluate(node=>node.scrollWidth>node.clientWidth+1)&&!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Contrôle lisible sans débordement à '+width);
  }
  await page.screenshot({path:'/artifacts/usage-recipe-mobile.png',fullPage:false});await page.setViewportSize({width:1366,height:900});
  await page.clock.install();blockHealth=true;const timeoutRequest=page.waitForRequest(request=>request.url().endsWith('/api/health'));await page.locator('#next-usage-run').click();await timeoutRequest;await page.clock.fastForward(15001);await measured();report=await download();
  check(report.measurements[0].state==='failed'&&report.measurements[0].error==='timeout','Une lecture dépassant quinze secondes est bornée et les suivantes continuent');while(deferred.length)deferred.shift()();
  blockHealth=true;const deadlineRequest=page.waitForRequest(request=>request.url().endsWith('/api/health'));await page.locator('#next-usage-run').click();await deadlineRequest;await page.clock.fastForward(90001);
  await page.waitForFunction(()=>document.querySelector('#next-usage-status').textContent.includes('90 secondes atteinte'));report=await download();
  check(report.status==='timed_out','Le plafond de quatre-vingt-dix secondes arrête aussi une requête bloquée');while(deferred.length)deferred.shift()();
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks,real_inference:false,real_disconnection:false,physical_phone:false};
}
