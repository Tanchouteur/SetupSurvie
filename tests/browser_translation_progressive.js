// Partial ordinary translation, staged API progress; never a real LLM.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],errors=[],commands=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{if(request.method()==='POST'&&request.url().includes('/api/translations'))commands.push(request.url());});
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.setViewportSize({width:1366,height:900});await page.goto(base+'/#/assistant');await page.waitForFunction(()=>S.authReady&&S.user&&!S.loadingConversation);
  await page.locator('#chat-reset').click();
  const id=await page.evaluate(async()=>{
    await attachToConversation({id:'guide:shelter.en.txt',title:'Document fictif'});
    const item=await api('/translations',{source_id:S.source.id,conversation_id:S.conversation,mode:'rapide'});
    await api('/translations/'+item.id+'/pause',{});return item.id;
  });
  let done=2,reads=0,paused=false;
  await page.route('**/api/translations/'+id+'?*',route=>{
    reads++;const offset=Number(new URL(route.request().url()).searchParams.get('offset')||0);
    const parts=Array.from({length:30},(_,position)=>({position,page:position+1,source_text:'Source fictive '+position,translated:position<done?'Passage français fictif '+position:'',status:position<done?'done':'pending',quality:{status:'checked',issues:[]},model:position<done?'fixture-model':''}));
    return route.fulfill({json:{id,source_id:'guide:shelter.en.txt',title:'Livre fictif',status:paused?'paused':'running',notice:'Traduction automatique fictive, non vérifiée.',total:30,done,unreadable:0,pages:30,pages_done:done,pages_partial:0,pages_unreadable:0,current_page:done+1,last_done_position:done-1,offset,parts:parts.slice(offset,offset+10),quality:{warnings:0},publication:{automatic:false}}});
  });
  await page.evaluate(async id=>{await loadTranslation(id);document.getElementById('translation-panel').open=true;},id);
  check((await page.locator('#translation-reading-status').textContent()).includes('2 / 30'),'Pages terminées et volume total visibles pendant le travail');
  check((await page.locator('#translation-reading-status').textContent()).includes('déjà lire'),'Lecture possible avant la fin annoncée clairement');
  check((await page.locator('#translation-parts').textContent()).includes('Passage français fictif 0'),'Le premier texte terminé est lisible sans attendre le livre');
  await page.locator('#translation-parts article').first().locator('details').evaluate(node=>node.open=true);
  await page.evaluate(()=>{window.readingNode=document.querySelector('#translation-parts article');const text=readingNode.querySelectorAll('p')[1];if(text){const range=document.createRange();range.selectNodeContents(text);getSelection().removeAllRanges();getSelection().addRange(range);window.readingSelection=getSelection().toString();}});
  const before=reads;done=3;
  await page.waitForFunction(()=>document.getElementById('translation-progress').value===3,null,{timeout:10000});
  check(reads>before,'L’avancement reçu se met à jour pendant la lecture');
  check(await page.evaluate(()=>readingNode===document.querySelector('#translation-parts article')),'Un passage terminé garde son élément pendant les actualisations');
  check(await page.locator('#translation-parts article').first().locator('details').evaluate(node=>node.open),'La comparaison ouverte ne se referme pas à chaque actualisation');
  check(await page.evaluate(()=>getSelection().toString()===readingSelection),'La sélection de texte du lecteur reste conservée');
  done=14;await page.waitForFunction(()=>document.getElementById('translation-progress').value===14,null,{timeout:10000});
  check(await page.evaluate(()=>S.translationOffset===0),'L’avancement ne déplace pas automatiquement la lecture');
  await page.locator('#translation-reading-latest').click();await page.waitForFunction(()=>S.translationOffset===10&&document.querySelector('#translation-parts article')?.dataset.position==='10');
  check((await page.locator('#translation-parts').textContent()).includes('Passage français fictif 13'),'Accès volontaire aux derniers passages prêts');
  await page.route('**/api/translations/'+id+'/pause',route=>{paused=true;return route.fulfill({json:{id,status:'paused'}});});
  await page.locator('#translation-pause').click();await page.locator('#translation-resume').waitFor({state:'visible'});
  check(await page.evaluate(()=>S.translationOffset===10),'La mise en pause conserve la page de lecture');
  const sent=commands.length;await page.reload();await page.waitForFunction(()=>S.translationOffset===10&&document.querySelector('#translation-parts article')?.dataset.position==='10');
  await page.locator('#translation-panel').evaluate(node=>node.open=true);
  check(commands.length===sent,'Recharger la lecture ne relance aucune traduction');
  check(await page.evaluate(()=>S.translationOffset===10),'Le groupe de passages lu est retrouvé après rechargement');
  await page.locator('#translation-reading-first').click();await page.waitForFunction(()=>document.querySelector('#translation-parts article')?.dataset.position==='0');
  check(await page.evaluate(()=>S.translationOffset===0),'Retour explicite au début du texte disponible');
  for(const width of [1366,390,320]){await page.setViewportSize({width,height:900});check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Suivi et lecture adaptés à '+width);}
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks,real_inference:false};
}
