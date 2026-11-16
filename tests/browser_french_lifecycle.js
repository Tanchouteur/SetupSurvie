// Deferred optional French lookup; no inference, reload or outage on a real PC.
async page=>{
 const base='http://10.0.3.2:8769',checks=[],errors=[];
 const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
 page.on('pageerror',error=>errors.push(error.message));
 await page.addInitScript(()=>{const original=fetch;window.frenchRequests=0;window.frenchAborts=0;window.fetch=(input,options)=>{if(new URL(input,location.href).pathname==='/api/library/french-reading'){window.frenchRequests++;options?.signal?.addEventListener('abort',()=>window.frenchAborts++,{once:true});}return original(input,options);};});
 let release,hold=true;const gate=new Promise(resolve=>release=resolve);
 await page.route('**/api/library/french-reading?*',async route=>{if(hold)await gate;try{await route.fulfill({json:{translations:[]}});}catch(_){} });
 try{
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.goto(base+'/#/bibliotheque/recherche');await page.waitForFunction(()=>S.user&&S.authReady);
  const pending=page.waitForRequest(request=>new URL(request.url()).pathname==='/api/library/french-reading');
  await page.evaluate(()=>readSource('guide:shelter.en.pdf#page=2'));await pending;
  await page.evaluate(()=>window.dispatchEvent(new Event('beforeunload')));
  check(await page.evaluate(()=>frenchRequests===1&&frenchAborts===1),'La navigation annule la requête française avant la désactivation du document');
  await page.evaluate(()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:false})));
  hold=false;release();
  check(await page.locator('#reader').isVisible(),'L’original ne dépend pas de cette option');
  await page.evaluate(()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true})));
  await page.waitForFunction(()=>frenchRequests>=2);
  check(await page.evaluate(()=>frenchRequests>=2),'Un retour depuis le cache du navigateur permet une nouvelle vérification');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks,real_model:false};
 }finally{hold=false;release();}
}
