// Real original PDF/SVG rendering and fixture store, simulated model selection.
async page=>{
 const base='http://10.0.3.2:8769',checks=[],errors=[];
 const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
 page.on('pageerror',error=>errors.push(error.message));
 await page.request.post(base+'/fixture/figures?enabled=true',{headers:{Origin:base}});
 try{
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.setViewportSize({width:390,height:844});await page.goto(base+'/?figures-check='+Date.now()+'#/assistant');await page.waitForFunction(()=>S.user&&!S.loadingConversation);await page.locator('#chat-reset').click();
  await page.locator('#chat-input').fill('Montre les schémas fixture du montage et leurs pages originales.');await page.locator('#send-question').click();
  await page.waitForFunction(()=>!S.job&&document.querySelectorAll('.source-figure').length===2);
  check(await page.locator('.source-figure').count()===2,'Deux visuels originaux et aucun logo ajouté');
  for(const figure of await page.locator('.source-figure').all()){await figure.scrollIntoViewIfNeeded();await page.waitForFunction(()=>[...document.querySelectorAll('.source-figure')].some(f=>f.querySelector('img').naturalWidth>0));await figure.locator('img').evaluate(img=>new Promise((resolve,reject)=>{if(img.naturalWidth)return resolve();img.addEventListener('load',resolve,{once:true});img.addEventListener('error',()=>reject(Error('Original image unavailable')),{once:true});}));}
  check(await page.locator('.source-figure img').evaluateAll(nodes=>nodes.every(n=>n.naturalWidth>0)),'Page PDF entière et SVG original réellement rendus');
  check((await page.locator('.source-figures').textContent()).includes('17 mm, garder la protection'),'Légende, unité et avertissement originaux conservés');
  check((await page.locator('.source-figures').textContent()).includes('ne sont pas interprétées'),'Sélection par légende distincte de la compréhension des pixels');
  check(await page.locator('.message-assistant .citation').filter({hasText:'p. 6'}).count()===1,'Référence composée avec page rendue cliquable');
  const conversation=await page.evaluate(()=>S.conversation);const stored=await(await page.request.get(base+'/api/conversations/'+conversation)).json();
  check(stored.messages.at(-1).sources.reduce((n,s)=>n+(s.figures?.length||0),0)===2,'Sélection enregistrée avec ses vraies sources');
  for(const [width,height] of [[1366,900],[390,844],[320,568]]){
   await page.setViewportSize({width,height});await page.waitForFunction(()=>document.getElementById('send-question').getBoundingClientRect().bottom<=innerHeight);
   check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Visuels sans débordement à '+width);
  }
  await page.setViewportSize({width:1366,height:900});await page.locator('.source-figures').scrollIntoViewIfNeeded();await page.screenshot({path:'/artifacts/setupsurvie-0190-figures-desktop.png'});
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:'/artifacts/setupsurvie-0190-figures-mobile.png'});
  const opened=page.waitForResponse(response=>response.url().includes('/api/source?id=')&&decodeURIComponent(response.url()).endsWith('#page=6'));
  await page.locator('.message-assistant .citation').filter({hasText:'p. 6'}).click();check((await(await opened).json()).id==='guide:shelter.en.pdf#page=6','La référence ouvre la page réellement consultée');
  await page.evaluate(()=>view('chat'));await page.reload();await page.waitForFunction(()=>S.conversation&&!S.loadingConversation&&document.querySelectorAll('.source-figure').length===2);
  check(await page.locator('.source-figure').count()===2,'Visuels retrouvés après rechargement sans modèle');
  const changed=await page.request.post(base+'/fixture/figures-change',{headers:{Origin:base}});check(changed.ok(),'Le document de test est réellement modifié');await page.reload();await page.waitForFunction(()=>document.querySelectorAll('.source-figure').length===2);
  await page.locator('.source-figures').scrollIntoViewIfNeeded();await page.waitForFunction(()=>document.querySelector('.source-figure').textContent.includes('a changé'));
  check(await page.locator('.source-figure img').first().isHidden(),'Un PDF modifié ne remplace pas silencieusement l’original sélectionné');
  check((await page.locator('.message-assistant').textContent()).includes('Montage fictif'),'Une erreur de visuel conserve la réponse textuelle');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks,real_model:false};
 }finally{await page.request.post(base+'/fixture/figures?enabled=false',{headers:{Origin:base}});}
}
