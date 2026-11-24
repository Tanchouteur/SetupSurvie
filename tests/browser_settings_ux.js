async page => {
  const base='http://10.0.3.2:8769',checks=[],errors=[],commands=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  const ready=()=>page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.user);
  const reload=async()=>{await page.waitForLoadState('networkidle');await page.reload({waitUntil:'domcontentloaded'});await ready();};
  const route=async tab=>{await page.goto(base+'/#/appareil/'+tab);await ready();await page.waitForFunction(tab=>location.hash===(tab==='activite'?'#/file':'#/appareil/'+tab),tab).catch(error=>{throw Error('Route '+tab+' URL '+page.url()+' JS '+errors.join(' / ')+' '+error.message);});if(['reglages','acces','bibliotheque','assistant','tests','entretien','lieux'].includes(tab))await page.locator('#settings-'+tab).waitFor({state:'visible'});};
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(['POST','PUT','DELETE','PATCH'].includes(r.method()))commands.push(new URL(r.url()).pathname);});
  let state={online:false,paused:true,message:'Mode jeu · assistant en pause',models:[],gpus:[],memory:{},disk:{},jobs:{},control_available:true};
  await page.route('**/api/inference',r=>r.fulfill({json:state}));
  await page.route('**/api/admin/inference/*',r=>{const start=r.request().url().endsWith('/start');state={...state,online:start,paused:!start,message:start?'Assistant disponible':'Assistant arrêté'};return r.fulfill({json:{ok:true}});});
  await page.route('**/api/activity',r=>r.fulfill({json:{phase:'downloading',source:'windows',observed_at:Date.now()/1000,worker_alive:true,total_bytes:10000,verified_bytes:3000,total_count:4,verified_count:1,active:[{id:'fixture',title:'Collection simulée en cours',bytes:3000,total:10000}]}}));
  await page.setViewportSize({width:1440,height:950});await route('reglages');
  check(await page.locator('#settings-reglages .settings-destination').count()===5,'Cinq entrées par usage, avec Tests et diagnostics');
  const commandStart=commands.length;
  for(const tab of ['acces','profils','connexion','reglages','bibliotheque','telechargements','stockage','assistant','tests','entretien','lieux','ensemble','activite']){
    await route(tab);
    check(await page.locator('#view-'+({profils:'users',connexion:'connect',telechargements:'data',stockage:'storage',ensemble:'monitor',activite:'work-queue'}[tab]||'settings')).isVisible(),'Lien direct '+tab);
    check(await page.evaluate(()=>{const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);return new Set(ids).size===ids.length;}),'IDs uniques dans '+tab);
  }
  check(commands.length===commandStart,'La navigation ne lance aucune commande');
  await route('reglages');await page.locator('#settings-reglages a[href$="/bibliotheque"]').click();await page.waitForURL('**/#/appareil/bibliotheque');
  await page.locator('#settings-add-guide > summary').click();await page.locator('#upload-form [name="title"]').fill('Brouillon de guide');
  await page.locator('#settings-back').click();await page.goBack();await page.waitForURL('**/#/appareil/bibliotheque');
  check(await page.locator('#upload-form [name="title"]').inputValue()==='Brouillon de guide','Retour conserve le formulaire déplacé');
  await page.goForward();await page.waitForURL('**/#/appareil/reglages');check(page.url().endsWith('/reglages'),'Suivant retrouve le hub');
  await page.goBack();await page.waitForURL('**/#/appareil/bibliotheque');await page.locator('#settings-bibliotheque').waitFor({state:'visible'});await reload();await page.locator('#settings-bibliotheque').waitFor({state:'visible'});
  check(await page.locator('#settings-add-guide').evaluate(n=>n.open),'Rubrique dépliée conservée au rechargement');
  check(!await page.locator('#settings-index').evaluate(n=>n.open),'Options techniques repliées au premier passage');
  await page.locator('#settings-index > summary').click();await page.waitForFunction(()=>JSON.parse(localStorage.getItem('survie-next-v1:'+S.user.id+':detail:settings-index'))?.value===true);await reload();
  check(await page.locator('#settings-index').evaluate(n=>n.open),'Préparation avancée mémorisée');
  await page.locator('#navigation [data-route="assistant"]').click();await page.locator('#chat-input').fill('Brouillon conversation UX');
  await page.locator('#navigation [data-route="appareil"]').click();await route('tests');
  if(!await page.locator('#settings-test-offline').evaluate(n=>n.open))await page.locator('#settings-test-offline > summary').click();
  await page.locator('#next-usage-open').click();check(await page.locator('#next-usage-dialog').isVisible(),'Contrôle hors ligne toujours branché');
  await page.locator('#next-usage-dialog [data-close]').click();await page.waitForFunction(()=>!document.querySelector('#next-usage-dialog').open);
  await page.locator('#navigation [data-route="assistant"]').click();check(await page.locator('#chat-input').inputValue()==='Brouillon conversation UX','Brouillon conservé après paramètres et dialogue');
  await reload();check(await page.locator('#chat-input').inputValue()==='Brouillon conversation UX','Brouillon conservé après rechargement');
  await route('assistant');await page.waitForFunction(()=>document.querySelector('#engine-start').textContent.includes('Forcer'));
  const beforeGame=commands.length;
  await page.setViewportSize({width:390,height:844});
  check(await page.locator('#engine-stop').isVisible(),'Arrêt de l’assistant accessible sur téléphone');
  check(commands.length===beforeGame,'Mode jeu préservé à l’ouverture mobile');
  await page.locator('#engine-start').click();await page.waitForFunction(()=>document.querySelector('#engine-stop').disabled===false);
  await page.locator('#engine-stop').click();await page.waitForFunction(()=>document.querySelector('#engine-start').disabled===false);
  check(commands.filter(p=>p==='/api/admin/inference/start').length===1&&commands.filter(p=>p==='/api/admin/inference/stop').length===1,'Un seul événement par commande déplacée, API simulée');
  for(const width of [320,390,760,820,1440]){
    await page.setViewportSize({width,height:950});
    for(const tab of ['reglages','acces','bibliotheque','assistant','tests','entretien','lieux','activite','telechargements','stockage','connexion','profils','ensemble']){
      await route(tab);
      check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Sans débordement '+width+' / '+tab);
    }
  }
  await page.route('**/api/work-queue',r=>r.fulfill({json:{paused:false,running:true,jobs:[{
    id:'host:download',kind:'host-download',type:'Préparation de l’appareil',title:'Téléchargement de la bibliothèque',
    lane:'network',status:'running',stage:'Téléchargement',preparation:{source:'windows',total_bytes:10000,verified_bytes:3000,
      total_count:4,verified_count:1,active:[{title:'Collection simulée en cours',bytes:3000,total:10000}]}
  }]}}));
  await page.setViewportSize({width:320,height:740});await route('activite');
  await page.getByText('Détails techniques', {exact:true}).click();
  check(await page.getByText('Transfert Windows indépendant · suivi en lecture seule.', {exact:true}).isVisible(),'Suivi du travail indépendant accessible à 320 px');
  await route('bibliotheque');await page.locator('#settings-index > summary').click(); // Collapse if previously remembered open; inspect visibility via DOM below.
  check(!await page.locator('#next-index-start').isVisible(),'Préparation complexe réservée au PC');
  check(await page.locator('.next-mobile-tools a[href="/secours.html"]').isVisible(),'Secours accessible sur téléphone');
  check(await page.locator('.next-mobile-tools .native-webui').isVisible(),'Open WebUI accessible sur téléphone');
  check(!await page.locator('#feedback-button').isVisible()&&await page.locator('a[href^="/classique/"]').count()===0,'Aucun retour ni lien classique réintroduit');
  await route('assistant');await page.locator('#settings-context > summary').click();
  await page.locator('#next-context-size').focus();check(await page.locator('#next-context-size').evaluate(n=>n===document.activeElement),'Champ technique accessible au clavier');
  // Preserve the original controls and the ancestor contracts used by feature modules.
  for(const id of ['location-target','location-query','location-mode','location-label','location-lat','location-lon','clear-departure','engine-start','engine-stop','assistant-policy','refresh-feedback','next-search-check-suite','next-search-check-open','next-usage-open','next-experiment-mode','next-experiment-suite','next-experiment-budget','next-experiment-start','next-experiment-stop','next-experiment-export','next-index-prepare','next-index-start','next-index-pause','next-index-export','next-index-auto','next-index-from','next-index-until','next-index-workers','next-context-model','next-context-size','next-calibration-mode','next-calibration-limit','next-calibration-start','next-calibration-stop','next-calibration-apply','next-calibration-rollback','next-calibration-export','next-clear-memory','geo-use-location','geo-lat','geo-lon','geo-radius','geo-terrain','geo-download','routing-download','geo-refresh','geo-pause','print-connect','copy-connect'])check(await page.locator('#'+id).count()===1,'Commande conservée '+id);
  for(const name of ['title','file','language','provenance','document_date','edition','licence'])check(await page.locator('#upload-form [name="'+name+'"]').count()===1,'Champ du guide conservé '+name);
  check(await page.locator('#next-context-form').evaluate(n=>!!n.closest('article')&&!!n.closest('#view-settings')),'Ancêtres nécessaires au contrôleur conservés');
  await page.setViewportSize({width:1440,height:950});await route('profils');
  const profileName='Profil UX '+Date.now();await page.locator('#add-user-form [name="name"]').fill(profileName);
  const profileCreated=page.waitForResponse(response=>new URL(response.url()).pathname==='/api/admin/users'&&response.request().method()==='POST');
  await page.locator('#add-user-form button').click();const profileResponse=await profileCreated;
  check(profileResponse.ok(),'Création de profil HTTP '+profileResponse.status()+' : '+await profileResponse.text());
  await page.waitForFunction(()=>document.querySelector('#user-status').textContent.includes('Profil créé')).catch(async error=>{throw Error('Statut de création de profil : '+await page.locator('#user-status').textContent()+' ; '+error.message);});
  check(true,'Création de profil branchée depuis les nouveaux paramètres');
  await page.locator('#navigation [data-route="assistant"]').click();await page.locator('#chat-input').fill('Brouillon Famille UX');
  await page.locator('#account-button').click();await page.locator('#profile-list').getByRole('button',{name:profileName,exact:true}).click();
  await page.waitForFunction(name=>typeof S!=='undefined'&&S.authReady&&S.user?.name===name,profileName);
  check(await page.locator('#chat-input').inputValue()==='','Le nouveau profil ne reprend pas le brouillon Famille');
  await page.goto(base+'/#/appareil/reglages');await page.locator('#auth-dialog').waitFor({state:'visible'});
  check(await page.locator('#auth-dialog').isVisible(),'Profil lecteur invité à choisir Famille pour les réglages partagés');
  await page.locator('#profile-list').getByRole('button',{name:'Famille',exact:true}).click();await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.user?.id==='local-family');
  await page.locator('#settings-reglages').waitFor({state:'visible'});
  await page.locator('#navigation [data-route="assistant"]').click();
  await page.waitForFunction(() => document.querySelector('#chat-input').value === 'Brouillon Famille UX');
  check(await page.locator('#chat-input').inputValue()==='Brouillon Famille UX','Retour Famille conserve son brouillon');
  check(await page.locator('input[type="password"]').count()===0,'Aucun mot de passe ajouté');
  await route('entretien');await page.locator('#settings-navigation-memory > summary').click();
  page.once('dialog',dialog=>dialog.dismiss());await page.locator('#next-clear-memory').click();
  await page.locator('#navigation [data-route="assistant"]').click();
  check(await page.locator('#chat-input').inputValue()==='Brouillon Famille UX','Annuler l’effacement conserve les brouillons');
  await page.waitForLoadState('networkidle');await page.goto(base+'/?lat=43.18&lon=6.04&target=departure#settings');await ready();await page.locator('#settings-lieux').waitFor({state:'visible'});
  await page.waitForFunction(()=>document.querySelector('#location-lat').value==='43.18');
  check(await page.locator('#location-lon').inputValue()==='6.04'&&await page.locator('#location-target').inputValue()==='departure','Retour direct depuis la carte conserve le point à confirmer');
  check(errors.length===0,'Aucune erreur JS : '+errors.join(', '));
  return {checks:checks.length,results:checks};
}
