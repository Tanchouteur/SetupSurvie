// Long synthetic answer, no real model or practical advice.
async page => {
  const base='http://10.0.3.2:8769',checks=[],errors=[];
  const check=(value,label)=>{if(!value)throw Error(label);checks.push(label);};
  page.on('pageerror',e=>errors.push(e.message));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.setViewportSize({width:1440,height:900});await page.goto(base+'/#/assistant');
  await page.waitForFunction(()=>S.authReady&&S.user&&!S.loadingConversation);
  await page.locator('#chat-reset').click();
  await page.waitForFunction(()=>!S.conversation&&!S.source&&!S.translation);
  await page.evaluate(()=>{
    $('chat-messages').replaceChildren();
    message('user','Question fictive pour mesurer le confort de lecture.');
    message('assistant',Array.from({length:40},(_,i)=>`### Partie ${i+1}\n\nParagraphe de démonstration : une réponse longue doit rester lisible à zoom normal, sans réduire la taille du texte.\n\n| Repère | Observation | Suite |\n| --- | --- | --- |\n| Exemple | Texte synthétique pour la recette | Consulter la source |`).join('\n\n'));
  });
  check(await page.locator('a[href^="/classique/"]').count()===0,'Aucun lien classique dans l’interface courante');
  check(!await page.locator('#feedback-button').isVisible(),'Faire un retour absent');
  check(!await page.locator('.next-history').count(),'Historique retiré de la zone de lecture');
  check(!await page.locator('#view-chat .native-help').count(),'Aide Open WebUI retirée de l’entête de conversation');
  const layouts=[];
  for(const [width,height] of [[1440,900],[1366,768],[1024,768],[900,600],[390,844],[320,568],[844,390]]){
    await page.setViewportSize({width,height});
    // Resize events and visualViewport updates are asynchronous in WebKit.
    // Measure only after the conversation has fitted the requested viewport.
    await page.waitForFunction(([width,height])=>{
      const send=document.getElementById('send-question').getBoundingClientRect();
      const workspace=document.querySelector('.workspace').getBoundingClientRect();
      const visible=document.elementFromPoint(send.left+send.width/2,send.top+send.height/2)?.closest('#send-question');
      return innerWidth===width&&Math.abs(workspace.height-height)<2&&send.bottom<=innerHeight&&send.bottom<=document.getElementById('main').getBoundingClientRect().bottom&&visible;
    },[width,height]);
    const sizes=await page.evaluate(()=>{const messages=$('chat-messages').getBoundingClientRect(),send=$('send-question').getBoundingClientRect(),composer=$('chat-form').getBoundingClientRect(),nav=$('navigation').getBoundingClientRect();return {height:messages.height,send:send.bottom,composer:composer.height,navTop:nav.top,overflow:document.documentElement.scrollWidth>innerWidth,font:parseFloat(getComputedStyle(document.querySelector('.message')).fontSize),readingWidth:document.querySelector('.message-assistant').getBoundingClientRect().width,mainBottom:$('main').getBoundingClientRect().bottom,sendVisible:!!document.elementFromPoint(send.left+send.width/2,send.top+send.height/2)?.closest('#send-question')};});
    check(sizes.send<=sizes.mainBottom&&sizes.sendVisible,'Bouton Envoyer entièrement visible et non recouvert à '+width+'×'+height);
    check(!sizes.overflow,'Pas de débordement à '+width+'×'+height);
    check(sizes.font>=16,'Texte lisible sans dézoom à '+width+'×'+height);
    check(sizes.height>=Math.min(180,height*.20),'Zone de lecture suffisante à '+width+'×'+height+' : '+sizes.height);
    if(width<=760)check(sizes.send<=sizes.navTop,'Saisie au-dessus de la navigation mobile à '+width);
    layouts.push({width,height,...sizes});
  }
  await page.setViewportSize({width:1440,height:900});
  const historyButton=page.locator('[data-assistant-zone="history"]');
  const visible=await page.locator('#assistant-history').isVisible();
  await historyButton.click();
  check(await page.locator('#assistant-history').isVisible()!==visible,'Volet des conversations repliable');
  await historyButton.click();
  check(await page.locator('#assistant-history').isVisible()===visible,'Volet retrouvé sans quitter la discussion');
  await page.screenshot({path:'/artifacts/conversation-confort-pc.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:'/artifacts/conversation-confort-mobile.png',fullPage:true});
  await page.route('**/api/search?*',r=>r.fulfill({json:{results:[],coverage:{status:'unavailable',warning:'Les encyclopédies n’ont pas pu être interrogées. La recherche est incomplète.'}}}));
  await page.evaluate(()=>search('feu'));
  await page.waitForFunction(()=>document.getElementById('search-message').textContent.includes('incomplète'));
  check((await page.locator('#search-results').textContent()).includes('ne prouve pas'),'Recherche dégradée ne signifie pas absence d’information');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,layouts};
}
