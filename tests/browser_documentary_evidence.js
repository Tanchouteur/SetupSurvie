// Actual fixture API/storage and DOM. Model prose and observations are synthetic.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],errors=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.goto(base+'/#/assistant');await page.waitForFunction(()=>S.authReady&&S.user);
  async function fixture(options){
    const response=await page.request.post(base+'/fixture/documentary?'+new URLSearchParams(options),{headers:{Origin:base}});
    if(!response.ok())throw Error('Documentary fixture unavailable');return await response.json();
  }
  const live=await fixture({state:'partial',running:'true'});
  await page.evaluate(id=>openConversation(id),live.conversation);
  let receipt=page.locator('.message-assistant .documentary-status').last();await receipt.waitFor({state:'visible'});
  check((await receipt.locator('summary').textContent()).includes('Recherche limitée'),'Limite observée visible indépendamment du texte du modèle');
  check((await page.locator('.message-assistant').last().textContent()).includes('affirmation fictive volontairement erronée'),'Texte du modèle conservé sans transformer le suivi en correction automatique');
  check(!(await receipt.evaluate(node=>node.open)),'Suivi documentaire replié pour laisser la réponse lisible');
  await receipt.locator('summary').click();
  check((await receipt.locator('.documentary-counts').textContent()).includes('1 résultat(s) proposé(s)'),'Document trouvé distinct de la lecture');
  check((await receipt.locator('summary').textContent()).includes('1 source(s) consultée(s)'),'Source réellement consultée comptée');
  check((await receipt.locator('.documentary-reading').textContent()).includes('par passages'),'Lecture par passages annoncée sans prétendre à une lecture intégrale');
  check((await receipt.locator('.documentary-limits').textContent()).includes('ne permet pas de conclure'),'Recherche limitée distincte de l’absence dans la bibliothèque');
  check(await receipt.locator('.documentary-sources button').count()===1,'Document consulté accessible même sans citation du modèle');
  await receipt.locator('.documentary-sources button').focus();
  await page.waitForResponse(response=>response.url().includes('/api/jobs/'+live.job));
  check(await receipt.evaluate(node=>node.open),'Détails ouverts conservés pendant les mises à jour');
  check(await receipt.locator('.documentary-sources button').evaluate(node=>node===document.activeElement),'Focus clavier conservé pendant le suivi');
  const finished=await page.request.post(base+'/fixture/documentary-finish?'+new URLSearchParams({job:live.job}),{headers:{Origin:base}});check(finished.ok(),'Fin de la réponse fictive enregistrée');
  await page.waitForFunction(()=>S.job===null);await page.reload();await page.waitForFunction(()=>S.authReady&&S.conversation);
  receipt=page.locator('.message-assistant .documentary-status').last();await receipt.waitFor({state:'visible'});
  check((await receipt.locator('summary').textContent()).includes('Recherche limitée'),'Suivi conservé avec la réponse après rechargement');
  if(!await receipt.evaluate(node=>node.open))await receipt.locator('summary').click();
  for(const width of [1366,390,320]){
    await page.setViewportSize({width,height:844});check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Suivi et liens sans débordement à '+width);
  }
  await page.screenshot({path:'/artifacts/suivi-documentaire-mobile.png',fullPage:true});
  await receipt.locator('.documentary-sources button').click();
  await page.waitForFunction(()=>!document.getElementById('reader').hidden&&document.getElementById('reader').textContent.includes('Shelter'));
  check(await page.locator('#reader').isVisible(),'Document consulté ouvert depuis le suivi indépendant');
  const unread=await fixture({state:'partial',read_source:'false'});await page.evaluate(id=>openConversation(id),unread.conversation);
  receipt=page.locator('.message-assistant .documentary-status').last();await receipt.waitFor({state:'visible'});
  check((await receipt.locator('summary').textContent()).includes('aucune source consultée'),'Résultat proposé ne devient pas une source lue');
  check(await receipt.locator('.documentary-sources button').count()===0,'Aucun faux lien de source consultée');
  const empty=await fixture({state:'empty'});await page.evaluate(id=>openConversation(id),empty.conversation);
  receipt=page.locator('.message-assistant .documentary-status').last();await receipt.waitFor({state:'visible'});await receipt.locator('summary').click();
  check((await receipt.locator('summary').textContent()).includes('Aucun résultat pour ces recherches'),'Zéro résultat limité aux demandes réellement exécutées');
  check((await receipt.locator('.documentary-limits').textContent()).includes('ne prouve pas'),'Zéro résultat ne certifie pas une absence générale');
  const legacy=await fixture({state:'legacy'});await page.evaluate(id=>openConversation(id),legacy.conversation);
  check(await page.locator('.message-assistant .documentary-status').isHidden(),'Ancienne réponse sans suivi gardée inconnue');
  check((await page.locator('.message-assistant').last().textContent()).includes('affirmation fictive'),'Ancienne réponse conservée');
  await page.evaluate(()=>{
    const target=document.querySelector('.message-assistant .documentary-status');
    documentaryStatus(target,{schema:1,status:'complete',scope:'library',searches:1,results:1,sources_read:1,failed_reads:0,partial_reads:0,consulted_sources:[{id:'guide:shelter.en.txt',title:'<img src=x onerror="window.unsafeDocumentary=true">'}]});
  });
  check(!await page.evaluate(()=>window.unsafeDocumentary),'Titre documentaire affiché comme texte, sans exécution HTML');
  check((await page.locator('.documentary-sources button').textContent()).includes('<img'),'Titre non interprété comme une instruction d’interface');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks,real_model:false,real_corpus:false};
}
