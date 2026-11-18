// Staged measurements and translation progress, no real GPU, model or documents.
async page=>{
 let stage='mémoire';
 try{
 const base='http://10.0.3.2:8769',checks=[],errors=[];
 const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
 page.on('pageerror',error=>errors.push(error.message));
 await page.request.post(base+'/api/profiles/select',{data:{id:'local-family'},headers:{Origin:base}});
 let inference={online:true,paused:false,message:'Assistant actif',models_available:true,control_available:true,
 models:[{name:'modele-charge-fixture',size:6*1024**3,size_vram:4*1024**3,context_length:16384}],
 memory:{used:18*1024**3,total:32*1024**3,available:14*1024**3},gpus:[{name:'Carte fictive',used:5*1024**3,total:8*1024**3,utilization:12,temperature:46}],jobs:{}};
 await page.route('**/api/inference',route=>route.fulfill({json:inference}));
 await page.setViewportSize({width:1440,height:1000});await page.goto(base+'/#/appareil/assistant');await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.user);
 await page.locator('#settings-assistant').getByRole('link',{name:/Voir la RAM/}).click();
 await page.waitForFunction(()=>location.hash==='#/appareil/ensemble');await page.waitForFunction(()=>document.getElementById('monitor-models').textContent.includes('modele-charge-fixture'));
 await page.locator('.resource-status').filter({hasText:'modele-charge-fixture'}).waitFor();
 const status=page.locator('.resource-status');
 const values=status.locator('.resource-status-value');
 check((await status.getAttribute('aria-label')).includes('RAM 18/32 Go · VRAM 5/8 Go')&&(await values.allTextContents()).join(',')==='56%,63%','Les jauges reprennent les mesures réelles avec les volumes accessibles');
 await page.evaluate(()=>{document.querySelector('#account-label').textContent='Profil familial avec un nom volontairement très long';});
 for(const width of [1001,1024,1181,1281,1400,1401,1440,1561,1920]){
   await page.setViewportSize({width,height:900});
   const metrics=()=> {
     const link=document.querySelector('.resource-status');
     const box=node=>{const {left,right,top,bottom,height}=node.getBoundingClientRect();return {left,right,top,bottom,height};};
     return {bar:box(link.parentElement),badge:box(link),account:box(document.querySelector('#account-button')),
       navigation:box(document.querySelector('#navigation')),width:innerWidth};
   };
   const {bar,badge,account,navigation,width:viewport}=await page.evaluate(metrics);
   const fits=Math.abs(bar.height-68)<0.5&&badge.height>0&&badge.right<=viewport&&badge.top>=bar.top&&badge.bottom<=bar.bottom&&
     navigation.right<=account.left&&account.right<=badge.left;
   check(fits,'Bloc mémoire sur la ligne de navigation à '+width+(fits?'':' '+JSON.stringify({bar,badge,account,viewport})));
 }
 check(await page.locator('#monitor-models').isVisible()&&await page.locator('#monitor-stats').isVisible(),'Modèle et mesures visibles sans déplier des détails');
 check(await page.locator('#settings-server-metrics').evaluate(n=>n.tagName==='SECTION'&&n.getBoundingClientRect().top<500),'Les mesures arrivent avant les cartes de suivi du stockage');
 check((await page.locator('#monitor-stats').innerText()).includes('RAM du PC')&&(await page.locator('#monitor-stats').innerText()).includes('VRAM de la carte graphique'),'RAM et VRAM distinguées du disque');
 await page.goBack();await page.waitForFunction(()=>location.hash==='#/appareil/assistant');await page.goForward();await page.waitForFunction(()=>location.hash==='#/appareil/ensemble');await page.reload();await page.locator('#monitor-models').getByText('modele-charge-fixture',{exact:true}).waitFor();
 check(await page.locator('#monitor-stats').isVisible(),'Retour, suivant et rechargement gardent les mesures accessibles');
 inference={...inference,models:[],models_available:false,control_available:false,memory:{},gpus:[]};await page.evaluate(()=>refreshInference());
 check((await page.locator('#monitor-models').innerText()).includes('Impossible de vérifier'),'Une observation indisponible ne devient pas aucun modèle chargé');
 check((await page.locator('#monitor-stats').innerText()).includes('Mesure indisponible'),'RAM ou VRAM absentes restent explicitement indisponibles');
 check((await values.allTextContents()).join(',')==='—,—','Une jauge indisponible affiche un tiret');
 inference={...inference,models_available:true,control_available:true,models:[],paused:true,memory:{used:0,total:1}};
 await page.evaluate(()=>refreshInference());
 check((await values.allTextContents()).join(',')==='0%,—'&&(await status.innerText()).includes('Moteur en pause'),'La mesure de zéro reste distincte de l’absence de mesure');
 stage='mise en forme';
 const formatting=await page.evaluate(()=>{const target=document.createElement('div');document.body.append(target);window.SurvieTranslationText.render(target,'## Titre du passage\n\nUne phrase\ncoupée par le PDF.\n\n- Premier élément\n- Deuxième élément\n\n| Nom | Valeur |\n| --- | --- |\n| Essai | 17 mm |\n\n```math\n\\frac{19}{7}\n```\n\n<img src="/interdit" onerror="window.translationInjected=true">\n\n[lien](javascript:alert(1))');target.classList.add('translation-text');const out={head:!!target.querySelector('h2'),list:target.querySelectorAll('li').length,table:!!target.querySelector('table'),formula:target.querySelector('pre code')?.textContent.includes('\\frac{19}{7}'),whiteSpace:getComputedStyle(target.querySelector('p')).whiteSpace,unsafe:!!target.querySelector('img,script,[onerror],a[href^="javascript:"]')};target.remove();return out;});
 check(formatting.head&&formatting.list===2&&formatting.table&&formatting.formula,'Titres, listes, tableaux et formules conservent leur structure');
 check(formatting.whiteSpace==='normal'&&!formatting.unsafe,'Retours PDF réunis dans la prose et contenu actif écarté');
 stage='lien vers les mesures';
 await page.goto(base+'/#/accueil');
 await status.click();
 await page.waitForURL('**/#/appareil/ensemble');
 await page.locator('#view-monitor').waitFor();
 check(true,'Le bloc entier ouvre les mesures depuis une autre rubrique');
 stage='profil traduction';
 const profile=await page.request.post(base+'/api/profiles',{data:{name:'Recette confort traduction '+Date.now()},headers:{Origin:base}});check(profile.ok(),'Profil de traduction isolé');
 const profileId=(await profile.json()).id;
 await page.goto(base+'/nouveau/#/bibliotheque/recherche?q=Shelter');
 await page.waitForFunction(id=>typeof S!=='undefined'&&S.authReady&&S.user?.id===id,profileId);
 await page.waitForSelector('#search-results .result button');await page.evaluate(()=>readSource('guide:shelter.en.txt'));
 stage='création traduction';
 const job=await page.evaluate(async()=>{const item=await api('/translations',{source_id:'guide:shelter.en.txt',mode:'rapide'});await api('/translations/'+item.id+'/pause',{});return item;});
 let done=3,reads=0;
 await page.route('**/api/translations/'+job.id+'?*',route=>{reads++;const offset=Number(new URL(route.request().url()).searchParams.get('offset')||0);return route.fulfill({json:{...job,status:'running',mode:'rapide',created:1,notice:'Traduction fictive',total:24,done,pages:24,pages_done:done,pages_partial:0,current_page:done+1,last_done_position:done-1,offset,quality:{warnings:0},publication:{},parts:Array.from({length:10},(_,i)=>{const position=offset+i;return {position,page:position+1,status:position<done?'done':'pending',translated:position<done?'## Titre conservé\n\nPhrase du PDF\nréunie pour la lecture.\n\n- Premier\n- Second':'',source_text:'Source fictive',model:position<done?'modele-fixture':'',quality:{status:'checked',issues:[]}};})}});});
 stage='ouverture lecteur';
 await page.evaluate(()=>readSource('guide:shelter.en.txt'));
 await page.locator('#reader [data-document-action=translate]').click();await page.waitForFunction(()=>document.querySelector('#reader-work-parts h2'));
 await page.evaluate(()=>{window.firstReadingNode=document.querySelector('#reader-work-parts article');window.pauseReadingButton=[...document.querySelectorAll('#reader-work button')].find(n=>n.textContent==='Mettre en pause');window.hiddenChanges=0;window.readingObserver=new MutationObserver(rows=>{hiddenChanges+=rows.filter(r=>r.attributeName==='hidden').length;});readingObserver.observe(pauseReadingButton,{attributes:true,attributeFilter:['hidden']});});
 stage='progression';
 const before=reads;done=4;await page.waitForFunction(()=>document.querySelector('#reader-work progress').value===4);
 check(reads>before&&await page.evaluate(()=>firstReadingNode===document.querySelector('#reader-work-parts article')),'Progression reçue sans remplacer les passages déjà lus');
 check(await page.evaluate(()=>hiddenChanges===0),'Les commandes ne disparaissent pas pendant le rafraîchissement');
 check((await page.locator('#reader-work-status').innerText()).includes('4/24'),'Avancement visible depuis la bibliothèque');
 stage='derniers passages';
 done=14;await page.waitForFunction(()=>document.querySelector('#reader-work progress').value===14);await page.locator('#reader-work').getByRole('button',{name:'Lire les derniers passages traduits',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#reader-work-parts article')?.dataset.position==='10');
 check(true,'Les derniers passages sont accessibles volontairement sans changer la lecture pendant le calcul');
 stage='dialogue lecture';
 await page.goto(base+'/#/assistant?conversation='+job.conversation_id);await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.user&&!S.loadingConversation);await page.evaluate(async id=>{await loadTranslation(id,0);document.getElementById('translation-panel').open=true;},job.id);await page.locator('#translation-reading-open').click();await page.locator('#translation-reading-dialog').waitFor({state:'visible'});
 check(await page.locator('#translation-reading-dialog').evaluate(n=>n.getBoundingClientRect().width>850),'Fenêtre de lecture PC réellement large');
 for(const width of [1440,1024,390,320]){await page.setViewportSize({width,height:900});check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Lecture sans débordement '+width);}
 await page.keyboard.press('Escape');
 stage='navigation cartes';
 inference={...inference,models_available:true,control_available:true,models:[{name:'modele-charge-fixture'}]};
 await page.route('**/vendor/maps/maplibre-gl.js',route=>route.fulfill({contentType:'text/javascript',body:'window.maplibregl={addProtocol(){},Map:class{constructor(){throw Error("fixture driver unavailable");}}};'}));
 await page.setViewportSize({width:1440,height:900});await page.goto(base+'/cartes.html?interface=nouveau');
 await page.locator('.map-site-nav [aria-current=page]').waitFor();await page.locator('.map-site-nav .resource-status').filter({hasText:'modele-charge-fixture'}).waitFor();
 check(await page.locator('.map-site-nav nav a').count()===5,'La navigation principale reste dans les cartes');
 check(await page.locator('#map-sidebar').isVisible(),'Les outils cartographiques sont conservés');
 for(const width of [1440,1024,390,320]){
   await page.setViewportSize({width,height:900});
   const layout=await page.locator('.map-site-nav nav').evaluate(nav=>{
     const links=[...nav.children].map(link=>link.getBoundingClientRect());
     return {
       fits:document.documentElement.scrollWidth<=innerWidth&&nav.scrollWidth<=nav.clientWidth&&
         links.every(link=>link.right<=innerWidth),
       minHeight:Math.min(...links.map(link=>link.height)),
     };
   });
   check(layout.fits,'Navigation des cartes entièrement visible à '+width);
   if(width<=760)check(layout.minHeight>=44,`Cibles tactiles des cartes à ${width} px : ${layout.minHeight} px, minimum 44 px`);
 }
 await page.locator('.map-site-nav').getByRole('link',{name:'Bibliothèque',exact:true}).click();await page.waitForFunction(()=>typeof S!=='undefined'&&S.view==='library');
 check(true,'Retour direct des cartes vers la bibliothèque');
 check(!errors.length,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks};
 }catch(error){throw Error(stage+' : '+error.message);}
}
