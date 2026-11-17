// Only our fixture requests: page departure must release pending HTTP/streams.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],errors=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.goto(base+'/#/bibliotheque/collections');await page.waitForFunction(()=>S.authReady&&S.user);
  const pending=[];
  await page.route('**/api/fixture-delayed*',async route=>{
    await new Promise(resolve=>pending.push(resolve));
    await route.fulfill({json:{late:true}}).catch(()=>{});
  });
  await page.evaluate(()=>{window.departureRequest=api('/fixture-delayed-departure').then(()=>({late:true}),error=>({error:error.name}));});
  for(let i=0;i<50&&!pending.length;i++)await page.waitForTimeout(20);
  check(pending.length===1,'Une requête retardée de recette est réellement en attente');
  await page.evaluate(()=>{setTimeout(()=>{window.lateDepartureRequest=api('/fixture-delayed-late-departure').then(()=>({late:true}),error=>({error:error.name}));},100);});
  await page.evaluate(()=>window.dispatchEvent(new PageTransitionEvent('pagehide')));
  const result=await page.evaluate(()=>window.departureRequest);
  check(result.error==='AbortError'&&!result.late,'Le départ de la page annule la requête au lieu de recevoir une réponse tardive');
  await page.waitForTimeout(180);
  check(pending.length===1,'Un minuteur tardif ne relance pas de requête pendant la fermeture');
  check((await page.evaluate(()=>window.lateDepartureRequest)).error==='AbortError','L’appel tardif reçoit une annulation locale explicite');
  await page.evaluate(()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true})));
  await page.evaluate(()=>{window.externalController=new AbortController();window.externalRequest=api('/fixture-delayed-external',undefined,{signal:window.externalController.signal}).then(()=>({late:true}),error=>({error:error.name}));});
  for(let i=0;i<50&&pending.length<2;i++)await page.waitForTimeout(20);
  await page.evaluate(()=>window.externalController.abort());
  check((await page.evaluate(()=>window.externalRequest)).error==='AbortError','L’annulation explicite du client reste transmise');
  pending.forEach(resolve=>resolve());await page.waitForTimeout(50);
  const health=await page.evaluate(()=>api('/health'));
  check(!!health.version,'Une nouvelle requête fonctionne après la restauration de la page');
  check(await page.evaluate(()=>[...PAGE_REQUESTS].every(controller=>!controller.signal.aborted)),'Les requêtes annulées sont retirées du suivi');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks};
}
