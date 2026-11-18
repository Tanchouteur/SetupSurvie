async page => {
  // Veillée design: position cues, quick access and local fonts, on the real portal.
  const base='http://10.0.3.2:8769';const errors=[];const external=[];
  const check=(value,label)=>{if(!value)throw Error(label);};
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(!r.url().startsWith(base)&&!r.url().startsWith('data:'))external.push(r.url());});
  await page.setViewportSize({width:1440,height:900});
  await page.goto(base+'/#/accueil');await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady);
  await page.evaluate(()=>document.fonts.ready);
  check(await page.evaluate(()=>document.fonts.check('16px "Atkinson Next"')&&document.fonts.check('32px Fraunces')),'Polices locales chargées');
  check(await page.locator('footer #software-version').isVisible(),'Version visible en pied de page');
  check(!await page.locator('.topbar').isVisible(),'Bandeau retiré sur PC');
  const version=(await (await page.request.get(base+'/api/status')).json()).version;
  const desktopVersion=page.locator('.brand .ds-nav-version');
  await page.waitForFunction(value=>document.querySelector('.brand .ds-nav-version')?.textContent===value,version);
  check(await desktopVersion.isVisible()&&await desktopVersion.textContent()===version,'La barre PC affiche le numéro fourni par le service');
  check(await desktopVersion.evaluate(node=>getComputedStyle(node).fontWeight==='400'&&
    getComputedStyle(node).color!==getComputedStyle(node.closest('.brand')).color),'Numéro en graisse normale et en couleur atténuée');
  await page.setViewportSize({width:800,height:900});
  check(await desktopVersion.isVisible(),'Numéro visible dans la barre PC compacte');
  await page.setViewportSize({width:1440,height:900});
  const aligned=()=>page.evaluate(()=>{const m=document.querySelector('.ds-nav-indicator').getBoundingClientRect(),a=document.querySelector('#navigation .nav-item.active').getBoundingClientRect();return Math.abs(m.left-a.left)<2&&Math.abs(m.width-a.width)<2;});
  await page.locator('#navigation [data-route="bibliotheque"]').click();
  await page.waitForFunction(()=>{const m=document.querySelector('.ds-nav-indicator').getBoundingClientRect(),a=document.querySelector('#navigation .nav-item.active').getBoundingClientRect();return Math.abs(m.left-a.left)<2;});
  check(await aligned(),'La pastille rejoint la page active');
  // Keyboard quick access: search, question preparation, closing.
  await page.keyboard.press('Control+k');await page.locator('dialog.ds-palette[open]').waitFor();
  await page.keyboard.type('compost');await page.keyboard.press('Enter');
  await page.waitForFunction(()=>location.hash.includes('q=compost'));
  check(await page.locator('#library-query').inputValue()==='compost','Accès rapide : recherche transmise');
  await page.locator('h1:visible').first().click();await page.keyboard.press('/');await page.locator('dialog.ds-palette[open]').waitFor();
  await page.keyboard.type('Pourquoi filtrer ?');await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');
  await page.waitForFunction(()=>document.getElementById('chat-input')?.value==='Pourquoi filtrer ?');
  check(await page.locator('#chat-messages .message').count()===0,'Question préparée sans envoi');
  await page.keyboard.press('Control+k');await page.locator('dialog.ds-palette[open]').waitFor();await page.keyboard.press('Escape');
  check(await page.locator('dialog.ds-palette[open]').count()===0,'Échap ferme l’accès rapide');
  await page.locator('#chat-input').press('/');
  const typed=await page.locator('#chat-input').inputValue();
  check(await page.locator('dialog.ds-palette[open]').count()===0&&typed.endsWith('/'),'La barre oblique reste saisissable dans un champ : '+typed);
  // Phone: same quick access, no sideways scrolling.
  await page.setViewportSize({width:320,height:640});await page.goto(base+'/#/accueil');await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady);
  check(await page.locator('.top-actions .ds-search-trigger').isVisible(),'Accès rapide sur téléphone');
  const mobileVersion=page.locator('.topbar .ds-nav-version');
  check(await mobileVersion.isVisible()&&await mobileVersion.textContent()===version,'La barre mobile affiche le même numéro');
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Pas de défilement horizontal à 320 px');
  check(!external.length,'Aucune ressource distante : '+external[0]);check(!errors.length,'Aucune erreur JavaScript : '+errors[0]);
}
