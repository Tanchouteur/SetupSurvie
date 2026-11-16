// Fake question/measurements and intercepted calibration; never real inference.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],calls=[],errors=[],headers={Origin:base};
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers});
  const version=(await(await page.request.get(base+'/api/health')).json()).version;
  await page.route('**/api/jobs/*/measurements',async route=>{
    const report=await(await route.fetch()).json();
    report.phases_ms.model_loading=1000;report.phases_ms.model_preparation=3100;
    report.model_preparations=[{status:'ready',duration_ms:1000}];report.model_retries=[{stage:'chat',reason:'empty_response'}];
    report.phases_ms.procedure_review=1200;report.procedure_review={status:'selected',candidates:3,selected:1,rejected:0};report.continued_sources=2;report.tool_protocol_retries=1;
    report.selected_sources=5;report.prepared_sources=5;report.citation_linking={applied:5,rejected:0};report.phases_ms.source_linking=200;
    await route.fulfill({json:report});
  });
  await page.setViewportSize({width:1366,height:900});await page.goto(base+'/#/assistant');await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.user);
  await page.locator('#chat-input').fill('Question de recette privée à ne pas exporter');await page.locator('#chat-form').evaluate(form=>form.requestSubmit());
  await page.waitForFunction(()=>S.conversation&&!S.job&&document.querySelector('#next-response-measures-open')?.hidden===false);
  const conversation=await page.evaluate(()=>S.conversation);
  await page.locator('#next-response-measures-open').click();await page.waitForFunction(()=>document.getElementById('next-response-measures-export').disabled===false);
  const body=page.locator('#next-response-measures-body');check((await body.textContent()).includes('Recherche documentaire')&&(await body.textContent()).includes('Lecture des sources'),'Recherche et lecture distinctes dans les durées');
  check((await body.textContent()).includes('Changement ou reprise du modèle')&&(await body.textContent()).includes('Reprises automatiques'),'Changement et reprise visibles dans les mesures');
  check((await body.textContent()).includes('Documents préparés')&&(await body.textContent()).includes('Liaisons ajoutées aux sources'),'Dossier documentaire et références visibles dans les mesures');
  check((await body.textContent()).includes('Relecture des conditions de départ')&&(await body.textContent()).includes('Documents repris de la réponse précédente'),'Relances et relecture des conditions visibles dans les mesures');
  const downloading=page.waitForEvent('download');await page.locator('#next-response-measures-export').click();const saved=await downloading,chunks=[];for await(const chunk of await saved.createReadStream())chunks.push(chunk);const report=JSON.parse(Buffer.concat(chunks).toString());
  check(report.version===version&&report.total_ms===6500,'Mesures exportées avec version et temps total');
  check(report.model_retries.length===1&&report.model_preparations[0].status==='ready'&&report.phases_ms.model_loading===1000,'Préparation et reprise présentes dans l’export numérique');
  check(report.selected_sources===5&&report.prepared_sources===5&&report.citation_linking.applied===5&&report.phases_ms.source_linking===200,'Sources préparées et ajout des références exportés sans texte');
  check(report.procedure_review.selected===1&&report.continued_sources===2&&report.tool_protocol_retries===1,'Conditions et reprises exportées sans extraits de documents');
  check(!JSON.stringify(report).includes('Question de recette privée')&&!JSON.stringify(report).includes('Réponse simulée')&&!('sources' in report),'Export sans question, réponse ni source privée');
  for(const width of [1366,390,320]){await page.setViewportSize({width,height:844});check(!await page.locator('#next-response-measures-dialog').evaluate(e=>e.scrollWidth>e.clientWidth),'Rapport des durées sans débordement à '+width);}
  await page.setViewportSize({width:1366,height:900});await page.locator('[data-close="next-response-measures-dialog"]').click();
  await page.reload();await page.waitForFunction(()=>S.conversation&&!S.loadingConversation&&document.getElementById('next-response-measures-open')?.hidden===false);
  check(await page.evaluate(()=>S.conversation)===conversation,'Mesures retrouvées après rechargement de la conversation');
  let state={schema:1,status:'not_started',trials:[],recommendation:null};
  await page.route('**/api/admin/assistant/calibration',r=>r.fulfill({json:{version,...state}}));
  await page.route('**/api/admin/assistant/calibration/start',r=>{calls.push(r.request().postDataJSON());state={schema:1,id:'a'.repeat(32),status:'running',model:'gpt-oss:20b',mode:'rapide',trials:[],recommendation:null,message:'Essai simulé en cours.'};return r.fulfill({status:202,json:state});});
  await page.route('**/api/admin/assistant/calibration/stop',r=>{calls.push('stop');state={...state,status:'cancelled',message:'Essai arrêté à votre demande.'};return r.fulfill({json:state});});
  await page.route('**/api/admin/assistant/calibration/apply',r=>{calls.push({apply:r.request().postDataJSON()});state={...state,configured_context:32768,can_rollback:true};return r.fulfill({json:{model:state.model,tokens:32768,previous:16384}});});
  await page.route('**/api/admin/assistant/context/rollback',r=>{calls.push('rollback');state={...state,configured_context:16384,can_rollback:false};return r.fulfill({json:{model:state.model,tokens:16384}});});
  await page.locator('#navigation [data-route="appareil"]').click();await page.locator('#next-machine-tabs [data-route="appareil/reglages"]').click();await page.locator('#settings-reglages a[href="#/appareil/tests"]').click();
  if(!await page.locator('#settings-test-memory').evaluate(node=>node.open))await page.locator('#settings-test-memory > summary').click();await page.waitForFunction(()=>document.getElementById('next-calibration-mode').options.length>0);
  check(calls.length===0,'Ouvrir les réglages ne lance pas d’essai');
  await page.locator('#next-calibration-limit').selectOption('65536');await page.locator('#next-calibration-form').evaluate(form=>form.requestSubmit());
  await page.waitForFunction(()=>document.getElementById('next-calibration-stop').hidden===false);
  check(calls.some(row=>row.mode==='rapide'&&row.max_context===65536),'Essai explicitement demandé avec plafond choisi');
  check(await page.locator('#next-calibration-start').isDisabled(),'Pas de double lancement pendant les mesures');
  await page.locator('#next-calibration-stop').click();await page.waitForFunction(()=>document.getElementById('next-calibration-status').textContent.includes('arrêté'));
  check(calls.includes('stop'),'Arrêt explicite transmis');
  state={...state,status:'completed',message:'Mesures synthétiques terminées.',recommendation:32768,configured_context:16384,can_rollback:false,
    trials:[{context:16384,temperature:'cold',status:'passed',duration_ms:5000,first_text_ms:4400,minimum_free:{ram_available:10*1024**3}},{context:32768,temperature:'warm',status:'passed',duration_ms:4000,first_text_ms:3500,minimum_free:{ram_available:7*1024**3}}]};
  await page.waitForFunction(()=>document.getElementById('next-calibration-apply').hidden===false);
  check(!calls.some(row=>row.apply),'Le résultat ne change pas automatiquement le réglage');
  await page.locator('#next-calibration-apply').click();await page.waitForFunction(()=>document.getElementById('next-calibration-rollback').hidden===false);
  check(calls.some(row=>row.apply?.id==='a'.repeat(32)),'Application volontaire du contexte mesuré');
  const calibrationDownload=page.waitForEvent('download');await page.locator('#next-calibration-export').click();const calibrationSaved=await calibrationDownload,parts=[];for await(const chunk of await calibrationSaved.createReadStream())parts.push(chunk);const calibrationReport=JSON.parse(Buffer.concat(parts).toString());
  check(calibrationReport.recommendation===32768&&!('messages' in calibrationReport),'Rapport mémoire exportable sans messages');
  await page.locator('#next-calibration-rollback').click();await page.waitForFunction(()=>document.getElementById('next-calibration-results').textContent.includes('Réglage courant : 16k'));
  check(calls.includes('rollback'),'Retour au réglage précédent disponible');
  for(const width of [1366,390,320]){
    await page.setViewportSize({width,height:844});
    // Let responsive layout settle, then inspect native select overflow too:
    // WebKit can propagate option text beyond a bounded select's border box.
    await page.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth,null,{timeout:5000}).catch(()=>{});
    const layout=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,
      overflowing:[...document.querySelectorAll('body *')].filter(node=>{const r=node.getBoundingClientRect();return r.width&&r.right>innerWidth+.5;}).map(node=>({tag:node.tagName,id:node.id,
        class:typeof node.className==='string'?node.className:'',right:node.getBoundingClientRect().right,width:node.getBoundingClientRect().width,
        parent:node.closest('[id]')?.id,text:node.textContent.slice(0,90)})).slice(-20),
      internal:[...document.querySelectorAll('body *')].filter(node=>node.clientWidth&&node.scrollWidth>node.clientWidth+1).map(node=>({tag:node.tagName,id:node.id,
        client:node.clientWidth,scroll:node.scrollWidth,overflow:getComputedStyle(node).overflowX,text:node.textContent.slice(0,90)})).slice(-20),
      textOverflow:(()=>{const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),rows=[];let node;while(node=walker.nextNode()){
        const range=document.createRange();range.selectNodeContents(node);const r=range.getBoundingClientRect();if(r.width&&r.right>innerWidth+.5)rows.push({parent:node.parentElement?.tagName,id:node.parentElement?.closest('[id]')?.id,right:r.right,text:node.textContent.slice(0,90)});
      }return rows.slice(-20);})()}));
    check(layout.scroll<=layout.width,'Essai mémoire sans débordement à '+width+(layout.scroll>layout.width?' '+JSON.stringify(layout):''));
  }
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks};
}
