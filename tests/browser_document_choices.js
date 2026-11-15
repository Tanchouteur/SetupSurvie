// Real fixture API and store, simulated answers/translations. No model inference.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],errors=[],requests=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{if(request.method()==='POST'&&request.url().endsWith('/api/questions'))requests.push(request.postDataJSON());});
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.goto(base+'/#/assistant');await page.waitForFunction(()=>S.authReady&&S.user&&!S.loadingConversation);
  await page.locator('#chat-reset').click();
  await page.evaluate(()=>view('library'));
  const documents=[{id:'guide:craft.en.txt',title:'Sewing fiction'},{id:'guide:shelter.en.txt',title:'Shelter fiction'},{id:'guide:shelter.en.pdf',title:'PDF fiction'}];
  await page.evaluate(rows=>{document.getElementById('search-results').replaceChildren();renderLibraryResults(rows.map(row=>({...row,kind:'guide',language:'en',excerpt:'Document fictif.'})));},documents);
  for(const source of documents){await page.locator('.result').filter({has:page.locator('[data-choice-id="'+source.id+'"]')}).locator('.source-choice-action').click();await page.waitForFunction(id=>!S.sourceChanging&&S.sources.some(source=>source.id===id),source.id);}
  const conversation=await page.evaluate(()=>S.conversation);
  check(!!conversation&&requests.length===0,'Choisir plusieurs documents crée une conversation sans lancer l’IA');
  check((await page.locator('#library-chosen-documents').textContent()).includes('3 document(s)'),'Sélection visible dans la bibliothèque');
  await page.reload();await page.waitForFunction(id=>S.authReady&&S.conversation===id&&!S.loadingConversation,conversation);
  check(await page.evaluate(()=>S.view==='library'&&S.sources.length===3),'Sélection retrouvée au rechargement sans quitter la bibliothèque');
  await page.locator('#library-chosen-documents button').click();await page.locator('#chat-source summary').waitFor({state:'visible'});
  check(!await page.locator('#chat-source details').evaluate(node=>node.open),'Liste repliée pour préserver la place de lecture');
  for(const [width,height] of [[1366,900],[390,844],[320,568]]){
    await page.setViewportSize({width,height});await page.waitForFunction(()=>document.getElementById('send-question').getBoundingClientRect().bottom<=innerHeight);
    check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Sélection et envoi sans débordement à '+width);
  }
  await page.setViewportSize({width:1366,height:900});
  const fresh=await page.context().newPage();await fresh.goto(base+'/#/assistant?conversation='+conversation);await fresh.waitForFunction(id=>S.conversation===id&&!S.loadingConversation,conversation);
  check(await fresh.evaluate(()=>S.sources.length===3),'Sélection enregistrée côté serveur retrouvée dans un autre onglet');await fresh.close();
  await page.locator('#chat-input').fill('Compare les documents fictifs choisis et cite leurs différences.');await page.locator('#send-question').click();
  await page.waitForFunction(()=>!S.job&&document.querySelector('.message-assistant'));
  check(requests.length===1&&requests[0].source_ids.length===3&&!('source_id' in requests[0]),'Une seule question transmet tous les documents choisis');
  await page.reload();await page.waitForFunction(id=>S.conversation===id&&!S.loadingConversation,conversation);
  check(await page.evaluate(()=>S.sources.length===3),'Question et sélection multiple conservées ensemble');
  await page.locator('#chat-source summary').click();
  const count=await page.locator('#chat-source .chosen-document').count();check(count===3,'Chaque document peut être ouvert ou retiré');
  await page.locator('#chat-source .chosen-document').filter({hasText:'craft'}).getByRole('button',{name:/Retirer/}).click();
  await page.waitForFunction(()=>!S.sourceChanging&&S.sources.length===2);
  check(await page.locator('.message-assistant').count()===1,'Retirer un document conserve les messages');
  await page.locator('#translation-panel').evaluate(node=>node.open=true);await page.locator('#translation-target').selectOption('guide:shelter.en.pdf');
  await page.locator('#translation-panel').evaluate(node=>node.open=true);
  await page.locator('#translation-first').fill('6');await page.locator('#translation-last').fill('6');await page.locator('#translation-start').click();
  await page.waitForFunction(()=>S.translation!==null);
  const translation=await page.evaluate(()=>S.translation);const report=await(await page.request.get(base+'/api/translations/'+translation)).json();
  check(report.source_id==='guide:shelter.en.pdf'&&report.pages===1,'Traduction explicitement limitée au PDF choisi et à sa page');
  const saved=await(await page.request.get(base+'/api/conversations/'+conversation)).json();
  check(saved.selected_sources.length===2&&saved.selected_sources.some(source=>source.id==='guide:shelter.en.txt'),'Traduire un document conserve les autres choix');
  await page.reload();await page.waitForFunction(()=>S.conversation&&!S.loadingConversation);
  check(await page.evaluate(()=>S.sources.length===2),'Choix conservés après traduction et rechargement');
  let release;const gate=new Promise(resolve=>release=resolve);
  await page.route('**/api/conversations/'+conversation,async route=>{const response=await route.fetch();await gate;await route.fulfill({response});});
  const loading=page.waitForRequest(request=>request.url().endsWith('/api/conversations/'+conversation));
  await page.evaluate(id=>{void openConversation(id);},conversation);await loading;
  await page.locator('#chat-reset').click();const finished=page.waitForResponse(response=>response.url().endsWith('/api/conversations/'+conversation));release();await finished;
  await page.waitForFunction(()=>!S.loadingConversation);
  check(await page.evaluate(()=>S.conversation===null&&S.sources.length===0),'Une ancienne ouverture retardée ne remplace pas la nouvelle conversation');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks,real_inference:false};
}
