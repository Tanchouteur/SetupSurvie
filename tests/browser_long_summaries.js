// Full fixture API/store, simulated inference; real browser comfort and recovery.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],errors=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',e=>errors.push(e.message));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.setViewportSize({width:390,height:844});
  await page.goto(base+'/#/assistant');await page.waitForFunction(()=>S.user&&!S.loadingConversation);
  await page.locator('#chat-reset').click();
  await page.evaluate(async()=>{await attachToConversation({id:'guide:shelter.en.pdf',title:'PDF fictif complet'});});
  check(await page.locator('#summary-panel').isVisible(),'Synthèse longue proposée après le choix des documents');
  check(!await page.locator('#summary-panel').evaluate(n=>n.open),'Le suivi reste replié au départ');
  await page.locator('#summary-panel').evaluate(n=>n.open=true);
  await page.locator('#chat-input').fill('Compare les informations fictives du PDF entier.');
  await page.waitForFunction(()=>!S.loadingConversation&&!S.sourceChanging&&!S.sending);
  await page.locator('#summary-start').click();
  await page.waitForFunction(()=>S.summaryActive&&!S.sending);
  const conv=await page.evaluate(()=>S.conversation);
  const data=await(await page.request.get(base+'/api/conversations/'+conv)).json(),id=data.summary_jobs[0].id;
  await page.waitForFunction(()=>document.getElementById('summary-status').textContent.length>0);
  check(await page.locator('#chat-source .source-choice-action').evaluateAll(nodes=>nodes.every(n=>n.disabled)),'Choix figés pendant la lecture longue');
  await page.locator('#summary-panel').evaluate(n=>n.open=true);
  await page.waitForFunction(()=>document.querySelector('#summary-notes article details'));
  await page.locator('#summary-notes').evaluate(node=>node.open=true);
  await page.locator('#summary-notes article details').first().evaluate(node=>node.open=true);
  await page.locator('#summary-pause').click();
  await page.waitForFunction(()=>!S.summaryActive&&document.getElementById('summary-status').textContent.includes('pause'));
  check(await page.locator('#summary-notes article details').first().evaluate(node=>node.open),'Les extraits ouverts restent ouverts pendant le suivi et la pause');
  const paused=await(await page.request.get(base+'/api/summaries/'+id)).json();
  check(paused.status==='paused','Pause conservée côté serveur');
  await page.reload();await page.waitForFunction(()=>S.conversation&&!S.loadingConversation&&document.getElementById('summary-export').getAttribute('href'));
  check(await page.evaluate(()=>S.conversation)===conv,'Travail retrouvé après rechargement');
  check(!await page.evaluate(()=>S.summaryActive),'Le rechargement ne relance pas la synthèse');
  await page.locator('#summary-panel').evaluate(n=>n.open=true);
  for(const [width,height] of [[1366,900],[390,844],[320,568]]){
    await page.setViewportSize({width,height});await page.waitForFunction(()=>document.getElementById('send-question').getBoundingClientRect().bottom<=innerHeight);
    check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Lecture et composition accessibles à '+width);
  }
  await page.setViewportSize({width:1366,height:900});await page.locator('#summary-panel').evaluate(n=>n.open=true);
  let lostFinalRead=false;await page.route('**/api/conversations/'+conv,async route=>{if(!lostFinalRead){lostFinalRead=true;await route.abort();}else await route.continue();});
  await page.locator('#summary-resume').click();
  await page.waitForFunction(()=>document.querySelector('.message-assistant')?.textContent.includes('Synthèse fictive'),{timeout:30000});
  check(lostFinalRead,'Une lecture finale interrompue est réessayée sans renvoyer la question');
  check(await page.locator('#summary-panel').evaluate(node=>node.open),'La rédaction terminée ne referme pas le suivi ouvert');
  const completed=await(await page.request.get(base+'/api/summaries/'+id)).json();
  check(completed.status==='completed'&&completed.pending===0,'Lecture et rédaction menées à leur terme');
  check(completed.read===completed.total&&completed.total>6,'PDF entier lu au-delà de son aperçu');
  await page.locator('#summary-panel').evaluate(n=>n.open=true);
  const exportPath=await page.locator('#summary-export').getAttribute('href');
  const exported=await page.request.get(base+exportPath);const text=await exported.text();
  check(text.includes('page/section 6')&&text.includes('empreinte'),'Export des notes avec dernière page et provenance');
  check(await page.locator('.source-chips button').filter({hasText:'Page 6'}).count()>0,'Pages lues accessibles depuis les références de la synthèse');
  const pageResponse=page.waitForResponse(response=>response.url().includes('/api/source?id=')&&decodeURIComponent(response.url()).endsWith('guide:shelter.en.pdf#page=6'));
  await page.locator('.source-chips button').filter({hasText:'Page 6'}).first().click();
  check((await (await pageResponse).json()).id==='guide:shelter.en.pdf#page=6','Le lien ouvre réellement la dernière page du PDF');
  await page.evaluate(()=>view('chat'));await page.reload();await page.waitForFunction(()=>S.conversation&&!S.loadingConversation);
  check(await page.locator('.message-assistant').count()===1,'Résultat enregistré une seule fois');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks,real_inference:false};
}
