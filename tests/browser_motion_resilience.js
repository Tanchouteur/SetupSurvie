// Audit edge cases without creating conversations, moving data or starting a model.
async page => {
  const base = 'http://10.0.3.2:8769', checks = [], errors = [], commands = [];
  const check = (ok, label) => { if (!ok) throw Error(label); checks.push(label); };
  await page.request.post(base+'/api/profiles/select', {data:{id:'local-family'},headers:{Origin:base}});
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    if (new URL(request.url()).pathname.startsWith('/api/') && !['GET','HEAD','OPTIONS'].includes(request.method())) commands.push(request.method()+' '+new URL(request.url()).pathname);
  });
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.setViewportSize({width:1440,height:950});
  await page.goto(base+'/#/accueil');
  await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.user);
  const immediate = await page.evaluate(()=>{
    document.querySelector('#navigation [data-route=bibliotheque]').click();
    const animation=document.querySelector('.view:not([hidden])').getAnimations().find(a=>a.id==='survie-reveal');
    return {view:S.view,hash:location.hash,duration:animation?.effect.getTiming().duration};
  });
  check(immediate.view==='library'&&immediate.hash.startsWith('#/bibliotheque'),'La navigation s’applique immédiatement sans attendre sa transition');
  check(immediate.duration>0&&immediate.duration<=250,'La transition de page reste courte');
  // Pause an actual app animation so a slow browser cannot pass by natural expiry.
  const held = await page.evaluate(async()=>{
    const view=document.querySelector('.view:not([hidden])');SurvieMotion.reveal(view);
    const animation=view.getAnimations().find(a=>a.id==='survie-reveal');animation.pause();await animation.ready;
    return animation.playState;
  });
  check(held==='paused','Une animation de l’application est retenue pour vérifier son interruption');
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.waitForFunction(()=>matchMedia('(prefers-reduced-motion: reduce)').matches&&!document.getAnimations().some(a=>a.id==='survie-reveal'));
  check(true,'Activer la réduction du mouvement annule l’animation existante sans autre navigation');
  check(await page.locator('#assistant-workspace').evaluate(n=>getComputedStyle(n).transitionDuration==='0s'),'Les transitions CSS sont aussi coupées lors du changement de préférence');
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.waitForFunction(()=>!matchMedia('(prefers-reduced-motion: reduce)').matches);
  await page.waitForFunction(()=>{const view=document.querySelector('.view:not([hidden])');SurvieMotion.reveal(view);return view.getAnimations().some(a=>a.id==='survie-reveal');},null,{timeout:3000});
  check(true,'Les transitions sont de nouveau disponibles sans recharger la page après propagation du réglage');
  await page.locator('#navigation [data-route=assistant]').focus();
  await page.keyboard.press('Enter');await page.locator('#chat-input').waitFor({state:'visible'});
  await page.locator('#chat-input').fill('Brouillon conservé pendant l’audit des transitions');
  await page.locator('#navigation [data-route=bibliotheque]').focus();await page.keyboard.press('Enter');
  await page.locator('#next-collections').waitFor({state:'visible'});
  const length = await page.evaluate(()=>history.length);
  await page.goBack();await page.locator('#chat-input').waitFor({state:'visible'});
  check(await page.locator('#chat-input').inputValue()==='Brouillon conservé pendant l’audit des transitions','Précédent retrouve le brouillon après une navigation au clavier');
  await page.goForward();await page.locator('#next-collections').waitFor({state:'visible'});
  // The router restores history focus in requestAnimationFrame. The visible
  // view can precede that callback in WebKit: wait for this actual UI work
  // before moving focus to the help button, otherwise restoration steals Enter.
  await page.evaluate(()=>new Promise(requestAnimationFrame));
  check(await page.evaluate(length=>S.view==='library'&&history.length===length,length),'Suivant retrouve la rubrique sans étape d’historique créée par les animations');
  check(await page.evaluate(()=>{const n=document.activeElement;return !!n&&n.getClientRects().length>0&&!n.closest('[hidden],[inert]');}),'Le focus restauré reste dans une zone visible et utilisable');
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const help=page.getByRole('button',{name:'Comprendre le filtre des collections',exact:true});
  await help.focus();await page.keyboard.press('Enter');
  check(await help.getAttribute('aria-expanded')==='true','Une aide animée reste ouvrable au clavier');
  await page.keyboard.press('Escape');
  check(await help.getAttribute('aria-expanded')==='false'&&await help.evaluate(n=>n===document.activeElement),'Échap ferme l’aide sans perdre le focus');
  const fallback = await page.evaluate(()=>{
    const animate=Element.prototype.animate;
    try{
      Element.prototype.animate=undefined;
      for(const route of ['appareil','bibliotheque','accueil']) document.querySelector('#navigation [data-route='+route+']').click();
      return {view:S.view,visible:!document.getElementById('view-home').hidden};
    }finally{Element.prototype.animate=animate;}
  });
  check(fallback.view==='home'&&fallback.visible,'La navigation reste fonctionnelle sans l’API d’animation');
  await page.setViewportSize({width:390,height:844});
  const placement = await page.evaluate(async()=>{
    document.querySelector('#navigation [data-route=assistant]').click();
    document.querySelector('#navigation [data-route=bibliotheque]').click();
    const help=document.querySelector('#next-collections .ux-help-trigger');help.focus();
    const content=document.getElementById(help.getAttribute('aria-controls'));
    const before=content.getBoundingClientRect().toJSON();
    await Promise.allSettled(document.querySelector('.view:not([hidden])').getAnimations().map(a=>a.finished));
    return {before,after:content.getBoundingClientRect().toJSON(),width:innerWidth,height:innerHeight,nav:document.getElementById('main-navigation').getBoundingClientRect().top};
  });
  check(placement.before.top>=0&&placement.before.bottom<=placement.nav&&placement.before.left>=0&&placement.before.right<=placement.width,'Une aide ouverte pendant la transition mobile reste entièrement visible au-dessus de la navigation');
  check(Math.abs(placement.before.top-placement.after.top)<1&&Math.abs(placement.before.left-placement.after.left)<1,'La fin de la transition ne fait pas sauter l’aide mobile');
  await page.evaluate(()=>new Promise(requestAnimationFrame));
  check(!commands.length,'Les transitions et la consultation seules ne déclenchent aucune commande serveur');
  check(!errors.length,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks,real_inference:false};
}
