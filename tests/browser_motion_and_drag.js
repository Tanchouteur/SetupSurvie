// Real browser drag events and persisted fixture API moves. No real inference.
async page => {
  const base = 'http://10.0.3.2:8769', checks = [], errors = [], moves = [];
  const check = (ok, label) => { if (!ok) throw Error(label); checks.push(label); };
  page.on('pageerror', e => errors.push(e.message));
  page.on('request', r => { if (r.method() === 'PUT' && r.url().endsWith('/folder')) moves.push(r); });
  await page.request.post(base+'/api/profiles/select', {data:{id:'local-family'},headers:{Origin:base}});
  await page.setViewportSize({width:1440,height:950});
  await page.goto(base+'/#/assistant');
  await page.waitForFunction(()=>typeof S!=='undefined' && S.authReady && S.user);
  await page.locator('#chat-reset').click();
  await page.locator('#chat-input').fill('Conversation fictive pour le glisser-déposer '+Date.now());
  await page.locator('#chat-form').evaluate(n=>n.requestSubmit());
  await page.waitForFunction(()=>!!S.conversation&&!S.job);
  const id = await page.evaluate(()=>S.conversation), name = 'Dossier de recette '+Date.now();
  await page.locator('#assistant-folder-create').click();
  await page.locator('#assistant-editor input').fill(name);
  await page.locator('#assistant-editor button[type=submit]').click();
  await page.locator('#assistant-editor').waitFor({state:'hidden'});
  await page.waitForFunction(()=>!history.state?.dialog);
  const folder = (await (await page.request.get(base+'/api/conversation-folders',{maxRetries:1})).json()).folders.find(f=>f.name===name).id;
  const row = () => page.locator('.conversation-row').filter({has:page.locator('[data-conversation-id="'+id+'"]')});
  const target = page.locator('[data-folder-id="'+folder+'"]');
  await page.locator('#chat-input').fill('Brouillon à conserver');
  await row().dragTo(target);
  await page.waitForFunction(folder=>document.querySelector('[data-folder-id="'+folder+'"]')?.textContent.includes('(1)'),folder);
  check((await (await page.request.get(base+'/api/conversations?folder='+folder,{maxRetries:1})).json()).conversations.some(c=>c.id===id),'Glisser-déposer range réellement la conversation dans le dossier');
  check(moves.length===1,'Un seul déplacement transmis pour un dépôt');
  check((await page.locator('.toast').textContent()).includes(name),'Confirmation nommant le dossier de destination');
  check(await page.evaluate(id=>S.conversation===id,id) && await page.locator('#chat-input').inputValue()==='Brouillon à conserver','Déplacer garde la discussion ouverte et le brouillon');
  await row().dragTo(target);
  await page.waitForFunction(()=>document.querySelector('.toast').textContent.includes('déjà dans ce dossier'));
  check(moves.length===1,'Dépôt dans le dossier courant expliqué sans déplacement supplémentaire');
  await page.reload();await page.waitForFunction(()=>typeof S!=='undefined' && S.authReady && S.user&&!S.loadingConversation);
  check((await (await page.request.get(base+'/api/conversations?folder='+folder,{maxRetries:1})).json()).conversations.some(c=>c.id===id),'Classement retrouvé après rechargement');
  await row().dragTo(page.locator('[data-folder-id=""]'));
  await page.waitForFunction(folder=>document.querySelector('[data-folder-id="'+folder+'"]')?.textContent.includes('(0)'),folder);
  check((await (await page.request.get(base+'/api/conversations?folder=unfiled',{maxRetries:1})).json()).conversations.some(c=>c.id===id),'Dépôt sur Sans dossier retire le classement sans supprimer la conversation');
  const before = moves.length;
  await target.evaluate((node,id)=>{const dt=new DataTransfer();dt.setData('application/x-setupsurvie-conversation',id);node.dispatchEvent(new DragEvent('drop',{bubbles:true,dataTransfer:dt}));},id);
  check(moves.length===before,'Un dépôt externe sans glissement local ne déclenche aucun déplacement');
  await row().dragTo(page.locator('#assistant-discussion'));
  check(moves.length===before && !await page.locator('.assistant-dragging,.is-drop-target,.is-dragging').count(),'Dépôt hors dossier annulé proprement');
  await page.route('**/api/conversations/'+id+'/folder',route=>route.fulfill({status:503,json:{detail:'Classement temporairement indisponible.'}}));
  await row().dragTo(target);
  await page.waitForFunction(()=>document.querySelector('.toast').textContent.includes('Classement temporairement indisponible'));
  check((await (await page.request.get(base+'/api/conversations?folder=unfiled',{maxRetries:1})).json()).conversations.some(c=>c.id===id),'Échec du déplacement annoncé sans perdre ni déplacer la conversation');
  await page.unroute('**/api/conversations/'+id+'/folder');
  await row().locator('summary').click();
  await row().locator('select').selectOption(folder);
  await page.waitForFunction(folder=>document.querySelector('[data-folder-id="'+folder+'"]')?.textContent.includes('(1)'),folder);
  check(true,'Le menu de classement reste fonctionnel après un glissement refusé');
  const panel = page.locator('#assistant-documents'), opener = page.locator('[data-assistant-zone=documents]');
  const closing = await page.evaluate(async()=>{
    document.querySelector('[data-close-panel=documents]').click();
    await new Promise(requestAnimationFrame);await new Promise(requestAnimationFrame);
    return {inert:document.getElementById('assistant-documents').inert,
      expanded:document.querySelector('[data-assistant-zone=documents]').getAttribute('aria-expanded'),
      moving:document.getElementById('assistant-workspace').getAnimations().some(a=>a.transitionProperty==='grid-template-columns')};
  });
  check(closing.inert&&closing.expanded==='false','Volet fermé immédiatement retiré des commandes accessibles');
  check(closing.moving,'La largeur des volets évolue pendant la fermeture');
  await panel.waitFor({state:'hidden'});
  check(await opener.evaluate(n=>n.getBoundingClientRect().right>innerWidth-45&&n.getBoundingClientRect().left>innerWidth/2),'Commande Documents placée près du bord droit');
  check(await opener.evaluate(n=>n===document.activeElement),'Focus rendu au bouton de réouverture');
  await opener.press('Enter');await panel.waitFor({state:'visible'});
  check(await panel.evaluate(n=>!n.inert)&&await opener.getAttribute('aria-expanded')==='true','Réouverture au clavier avec état accessible cohérent');
  const routeAnimation = await page.evaluate(()=>{
    document.querySelector('#navigation [data-route=accueil]').click();
    return document.querySelector('.view:not([hidden])').getAnimations().some(a=>a.id==='survie-reveal');
  });
  check(routeAnimation,'Le changement de page possède une transition visible');
  const rapid = await page.evaluate(()=>{
    for(const route of ['bibliotheque','appareil','assistant'])document.querySelector('#navigation [data-route='+route+']').click();
    return {count:document.getAnimations().filter(a=>a.id==='survie-reveal').length,view:S.view};
  });
  check(rapid.count<=1&&rapid.view==='chat','Clics rapides : seule la dernière page conserve sa transition');
  check(await page.locator('#chat-input').inputValue()==='Brouillon à conserver','Transitions et navigation conservent le brouillon');
  for(const width of [1440,1024,390,320]){
    await page.setViewportSize({width,height:844});
    if(width<=1000){await opener.click();await page.locator('[data-close-panel=documents]').click();}
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Commandes et volets sans débordement à '+width);
    check(await page.locator('#chat-input').isVisible(),'Saisie retrouvée après les changements de volet à '+width);
  }
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.waitForFunction(()=>matchMedia('(prefers-reduced-motion: reduce)').matches);
  const reduced = await page.evaluate(()=>{
    document.querySelector('#navigation [data-route=accueil]').click();
    return document.getAnimations().filter(a=>a.id==='survie-reveal').length;
  });
  check(reduced===0,'La préférence de réduction des animations supprime les mouvements JavaScript');
  await page.setViewportSize({width:1440,height:950});
  await page.locator('#navigation [data-route=assistant]').click();
  check(await page.locator('#assistant-workspace').evaluate(n=>getComputedStyle(n).transitionDuration==='0s'),'La préférence de réduction supprime aussi les transitions CSS');
  await page.locator('[data-close-panel=documents]').click();await panel.waitFor({state:'hidden'});await opener.press('Enter');await panel.waitFor({state:'visible'});
  check(await page.locator('#chat-input').inputValue()==='Brouillon à conserver','Volets utilisables sans animation');
  for(const path of ['/pdf.html?id=guide%3Ashelter.en.pdf&interface=nouveau','/cartes.html?interface=nouveau']){
    await page.goto(base+path);await page.waitForFunction(()=>!!window.SurvieMotion);
    check(await page.locator('body').evaluate(n=>n.classList.contains('ux-motion')),'Retour visuel commun chargé dans '+path.split('?')[0]);
    check(await page.locator('button').first().evaluate(n=>getComputedStyle(n).transitionDuration==='0s'),'Réduction des animations respectée dans '+path.split('?')[0]);
  }
  check(!errors.length,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks,real_inference:false};
}
