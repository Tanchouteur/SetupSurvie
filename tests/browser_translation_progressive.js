// Partial ordinary translation, staged API progress; never a real LLM.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],errors=[],commands=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  let stage='initialisation';try{
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
  let done=2,reads=0,paused=false,scan=false;
  await page.route('**/api/translations/'+id+'?*',route=>{
    reads++;const offset=Number(new URL(route.request().url()).searchParams.get('offset')||0);
    const parts=Array.from({length:30},(_,position)=>({position,page:position+1,source_text:scan?'':'Source fictive '+position,translated:position<done?'Passage français fictif '+position:'',status:scan?'unreadable':position<done?'done':'pending',quality:{status:scan?'unchecked':'checked',issues:[]},model:position<done?'fixture-model':''}));
    return route.fulfill({json:{id,source_id:'guide:shelter.en.txt',title:'Livre fictif',status:scan?'completed':paused?'paused':'running',notice:'Traduction automatique fictive, non vérifiée.',total:30,done,unreadable:scan?30:0,pages:30,pages_done:done,pages_partial:0,pages_unreadable:scan?30:0,current_page:scan?null:done+1,last_done_position:done?done-1:null,offset,parts:parts.slice(offset,offset+10),quality:{warnings:0},publication:{automatic:false}}});
  });
  await page.evaluate(id=>loadTranslation(id),id);
  stage='lire dans la discussion';
  const inline=page.locator('#chat-messages #translation-parts');
  check(await page.locator('#assistant-discussion > #translation-panel').isVisible(),'Commandes dans le bandeau au-dessus de la discussion');
  check(await page.locator('#assistant-documents #translation-panel').count()===0,'Commandes indépendantes du volet Documents');
  check(await inline.locator('article').count()===2,'Seuls les deux passages disponibles sont affichés dans le fil');
  await page.locator('#translation-summary').click();
  done=3;
  await inline.getByText('Passage français fictif 2',{exact:true}).waitFor();
  check(await page.locator('#translation-panel').evaluate(node=>!node.open),'Les passages arrivent dans le fil avec le bandeau replié');
  await page.locator('#translation-summary').click();
  stage='ouvrir la lecture';await page.locator('#translation-reading-open').click();await page.locator('#translation-reading-dialog').waitFor({state:'visible'});
  check(await page.locator('#translation-reading-dialog #translation-parts').isVisible(),'Une fenêtre de lecture libère la place occupée par la conversation');
  check((await page.locator('#translation-reading-status').textContent()).includes('3 / 30'),'Pages terminées et volume total visibles pendant le travail');
  check((await page.locator('#translation-reading-status').textContent()).includes('déjà lire'),'Lecture possible avant la fin annoncée clairement');
  check((await page.locator('#translation-parts').textContent()).includes('Passage français fictif 0'),'Le premier texte terminé est lisible sans attendre le livre');
  await page.locator('#translation-parts article').first().locator('details').evaluate(node=>node.open=true);
  await page.evaluate(()=>{window.readingNode=document.querySelector('#translation-parts article');const text=readingNode.querySelectorAll('p')[1];if(text){const range=document.createRange();range.selectNodeContents(text);getSelection().removeAllRanges();getSelection().addRange(range);window.readingSelection=getSelection().toString();}});
  const before=reads;done=4;
  stage='attendre le quatrième passage';await page.waitForFunction(()=>document.getElementById('translation-progress').value===4,null,{timeout:10000});
  check(reads>before,'L’avancement reçu se met à jour pendant la lecture');
  check(await page.evaluate(()=>readingNode===document.querySelector('#translation-parts article')),'Un passage terminé garde son élément pendant les actualisations');
  check(await page.locator('#translation-parts article').first().locator('details').evaluate(node=>node.open),'La comparaison ouverte ne se referme pas à chaque actualisation');
  check(await page.evaluate(()=>getSelection().toString()===readingSelection),'La sélection de texte du lecteur reste conservée');
  stage='attendre quatorze passages';done=14;await page.waitForFunction(()=>document.getElementById('translation-progress').value===14,null,{timeout:10000});
  check(await page.evaluate(()=>S.translationOffset===0),'L’avancement ne déplace pas automatiquement la lecture');
  stage='lire les derniers passages';await page.locator('#translation-reading-latest').click();await page.waitForFunction(()=>S.translationOffset===10&&document.querySelector('#translation-parts article')?.dataset.position==='10');
  check((await page.locator('#translation-parts').textContent()).includes('Passage français fictif 13'),'Accès volontaire aux derniers passages prêts');
  stage='fermer avant la pause';await page.locator('#translation-reading-close').click();await page.waitForFunction(()=>!document.getElementById('translation-reading-dialog').open&&!history.state?.dialog);
  await page.route('**/api/translations/'+id+'/pause',route=>{paused=true;return route.fulfill({json:{id,status:'paused'}});});
  stage='mettre en pause';await page.locator('#translation-pause').click();await page.locator('#translation-resume').waitFor({state:'visible'});
  check(await page.evaluate(()=>S.translationOffset===10),'La mise en pause conserve la page de lecture');
  check(await page.evaluate(id=>{const data=JSON.parse(localStorage.getItem('survie-translation-reading:'+S.user.id));return data[id].offset===10&&Object.keys(data[id]).every(key=>['offset','open','updated'].includes(key));},id),'La mémoire de lecture garde seulement le groupe lu et sa date');
  stage='ouvrir la lecture';await page.locator('#translation-reading-open').click();await page.locator('#translation-reading-dialog').waitFor({state:'visible'});
  const historyLength=await page.evaluate(()=>history.length);
  stage='retrouver la lecture après rechargement';const sent=commands.length;await page.reload();await page.waitForFunction(()=>S.translationOffset===10&&document.querySelector('#translation-parts article')?.dataset.position==='10');
  await page.locator('#translation-panel').evaluate(node=>node.open=true);
  await page.locator('#translation-reading-dialog').waitFor({state:'visible'});
  check(true,'La fenêtre de lecture est retrouvée après rechargement');
  check(await page.evaluate(()=>history.length)===historyLength,'Restaurer la lecture ne rajoute pas une étape à l’historique');
  check(commands.length===sent,'Recharger la lecture ne relance aucune traduction');
  check(await page.evaluate(()=>S.translationOffset===10),'Le groupe de passages lu est retrouvé après rechargement');
  stage='revenir au début';await page.locator('#translation-reading-first').click();await page.waitForFunction(()=>document.querySelector('#translation-parts article')?.dataset.position==='0');
  check(await page.evaluate(()=>S.translationOffset===0),'Retour explicite au début du texte disponible');
  for(const width of [1366,390,320]){await page.setViewportSize({width,height:900});check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Suivi et lecture adaptés à '+width);}
  stage='fermer avec le retour navigateur';await page.goBack();await page.locator('#translation-reading-dialog').waitFor({state:'hidden'});
  check(await inline.isVisible(),'Retour navigateur ferme la lecture et retrouve les passages dans le fil');
  await page.goForward();await page.locator('#translation-reading-dialog').waitFor({state:'visible'});
  check(await page.evaluate(()=>translationReadingState(S.translation).open),'Avancer dans le navigateur retrouve la lecture ouverte et son repère');
  await page.keyboard.press('Escape');await page.locator('#translation-reading-dialog').waitFor({state:'hidden'});
  check(await page.evaluate(()=>!translationReadingState(S.translation).open),'Échap ferme la lecture et conserve ce choix');
  stage='signaler un document sans texte traduit';scan=true;done=0;await page.evaluate(id=>loadTranslation(id,0),id);
  check((await page.locator('#translation-reading-status').textContent()).includes('Aucun passage français')&&!(await page.locator('#translation-reading-status').textContent()).includes('pas encore prêt'),'Un document sans texte extractible ne promet pas une arrivée de traduction');
  check(await page.locator('#translation-reading-open').isDisabled()&&await page.locator('#translation-progress').evaluate(node=>node.value===0),'Les pages illisibles ne deviennent ni lecture disponible ni passages traduits');
  stage='poser une question dans la conversation de traduction';
  await page.setViewportSize({width:1366,height:900});
  await page.locator('#chat-input').fill('Quel est le sujet du document fictif ?');
  await page.locator('#send-question').click();
  await page.locator('#chat-messages .message-user').waitFor();
  check(await inline.isVisible(),'La première question conserve le résultat de traduction dans le fil');
  await page.waitForFunction(()=>!S.job&&!S.sending);
  await page.locator('#chat-reset').click();
  check(await inline.isHidden(),'Une nouvelle discussion masque les passages de la précédente');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks,real_inference:false};
  }catch(error){const state=await page.evaluate(()=>({dialog:document.getElementById('translation-reading-dialog')?.open,history:history.state,offset:S.translationOffset,translation:S.translation,reading:JSON.parse(localStorage.getItem('survie-translation-reading:'+S.user?.id)),status:document.getElementById('translation-status')?.textContent,hash:location.hash}));throw Error(stage+' : '+error.message+' '+JSON.stringify(state));}
}
