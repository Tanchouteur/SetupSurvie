// Native tiny ZIM + real browser decoding, simulated host/Kiwix HTTP and model.
async page=>{
  const base='http://10.0.3.2:8769',headers={Origin:base},checks=[],errors=[],calls=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>calls.push(request.url()));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers});
  check((await page.request.post(base+'/fixture/archive-videos',{headers})).ok(),'Petite archive native et média synthétique préparés');
  await page.request.post(base+'/fixture/videos',{headers});
  await page.request.post(base+'/fixture/acquisitions',{headers});
  try{
    await page.goto(base+'/#/bibliotheque/collections');await page.waitForFunction(()=>S.authReady&&S.user);
    await page.getByText('Gestion de la vidéothèque',{exact:true}).click();
    const section=page.locator('#next-archive-videos');if(!await section.evaluate(d=>d.open))await section.locator('summary').click();
    await page.locator('#next-archive-videos-start').click();await page.waitForFunction(()=>document.querySelector('#next-archive-videos-status').textContent.includes('Examen en cours'));
    check(await page.locator('#next-archive-videos-start').isDisabled(),'Un second examen ne démarre pas en parallèle');
    await page.locator('#next-archive-videos-pause').click();await page.waitForFunction(()=>document.querySelector('#next-archive-videos-status').textContent.includes('Examen en pause'));
    check(true,'Pause explicite disponible depuis le site');
    const started=page.waitForResponse(response=>response.url().endsWith('/api/admin/zim-videos/start')&&response.request().method()==='POST');
    await page.locator('#next-archive-videos-start').click();check((await started).ok(),'Reprise acceptée avant de libérer le lecteur de test');
    await page.request.post(base+'/fixture/archive-videos-release',{headers});
    let ready=false;
    for(let n=0;n<200;n++){if((await(await page.request.get(base+'/api/zim-videos')).json()).reader_ready){ready=true;break;}await new Promise(resolve=>setTimeout(resolve,100));}
    check(ready,'Le nouvel inventaire est réellement repris dans le lecteur');
    const collection=page.locator('#next-videos-list .video-collection-group').filter({hasText:'Fictional video inventory'});
    const collectionHeader=collection.locator(':scope > summary');
    await collectionHeader.waitFor();
    check((await collectionHeader.textContent()).includes('2 vidéos')&&!await collection.evaluate(d=>d.open),
      'Les vidéos de la même collection sont comptées sur une carte repliée');
    const origin=page.getByRole('combobox',{name:'Origine des vidéos'});
    await origin.selectOption('local');
    const youtubeVideo=page.locator('#next-videos-list .data-card').filter({hasText:'Récupération source fictive'});
    const localVideo=page.getByRole('heading',{name:'sans-piste',exact:true});
    await localVideo.waitFor();
    await youtubeVideo.waitFor();
    check(await collection.count()===0,'Nos vidéos ajoutées retire les vidéos des archives Kiwix');
    check(await localVideo.isVisible(),'Nos vidéos ajoutées garde les fichiers du dossier vidéo, YouTube compris');
    await page.locator('#collection-filter').fill('terme-sans-résultat');
    await page.getByText('Aucune vidéo ne correspond à ces filtres.').waitFor();
    check(await youtubeVideo.count()===0,'Le filtre par mots se combine avec l’origine');
    await page.locator('#collection-filter').fill('');
    await origin.selectOption('all');
    await youtubeVideo.waitFor();
    await collectionHeader.waitFor();
    check(await collectionHeader.isVisible(),'Toutes les vidéos réunit les archives et nos vidéos');
    await collectionHeader.click();
    await page.waitForFunction(()=>[...document.querySelectorAll('#next-videos-list .data-card')].some(card=>card.textContent.includes('Fictional video course')));
    const card=page.locator('#next-videos-list .data-card').filter({hasText:'Fictional video course'});
    check(await card.getByRole('link',{name:'Ouvrir l’article d’origine'}).count()===1,'Origine documentaire conservée sur la vidéo');
    const sectionHeader=page.locator('[data-collection-section="videos"] > summary');
    await sectionHeader.click();
    check(!await page.locator('#next-videos-origin').isVisible(),'Le filtre est masqué lorsque le volet vidéo est replié');
    await sectionHeader.click();
    await origin.waitFor();
    check(await card.getByText('Créer les sous-titres depuis l’audio',{exact:true}).count()===0,'Une piste présente évite de proposer inutilement une reconnaissance audio');
    const found=await(await page.request.get(base+'/api/search?q=Fictional&domain=all')).json();const hit=found.results.find(row=>row.archive_video&&row.id.includes('#t=1000'));
    check(!!hit,'La recherche commune retrouve les paroles internes et leur horodatage');
    await page.evaluate(id=>readSource(id),hit.id);const player=page.locator('#reader video');await player.waitFor();await player.evaluate(v=>v.play());
    await page.waitForFunction(()=>{const v=document.querySelector('#reader video');return v?.videoWidth===96&&v.currentTime>=1&&[...v.textTracks].some(t=>t.language==='en'&&t.cues?.length===1);});
    await player.evaluate(v=>v.pause());check(Math.abs(await player.evaluate(v=>v.duration)-12)<.2,'Le navigateur lit le WebM servi depuis l’archive');
    check(await player.evaluate(v=>[...v.textTracks].some(t=>t.cues?.[0]?.startTime===1)),'La piste interne garde son temps original');
    await page.goto(base+'/#/bibliotheque/collections');await page.waitForFunction(()=>S.authReady&&S.user);
    const refreshed=page.locator('#next-videos-list .data-card').filter({hasText:'Fictional video course'});await refreshed.waitFor();
    await refreshed.getByText('Options de sous-titrage',{exact:true}).click();
    await refreshed.getByText('Préparer une piste française',{exact:true}).click();
    const preparing=page.waitForResponse(response=>response.url().endsWith('/api/admin/video-captions')&&response.request().method()==='POST');
    await refreshed.getByRole('button',{name:'Traduire les sous-titres'}).click();const job=await(await preparing).json();
    await page.waitForFunction(id=>document.querySelector('[data-caption-job="'+id+'"]')?.textContent.includes('Piste française préparée'),job.id);
    // Publication and search indexing finish independently.
    let translated;
    for(let n=0;n<100&&!translated;n++){
      const french=await(await page.request.get(base+'/api/search?q=roulement&language=fr&domain=all')).json();
      translated=french.results.find(row=>row.archive_video&&row.id.split('&track=')[0]===hit.id.split('&track=')[0]);
      if(!translated)await new Promise(resolve=>setTimeout(resolve,100));
    }
    check(!!translated,'La piste française préparée rejoint le même moteur de recherche');
    await page.evaluate(id=>readSource(id),translated.id);await player.waitFor();await player.evaluate(v=>v.play());
    await page.waitForFunction(()=>{const v=document.querySelector('#reader video');return [...v.textTracks].some(t=>t.language==='fr'&&t.mode==='showing'&&t.cues?.length===1);});await player.evaluate(v=>v.pause());
    check((await page.locator('#reader').textContent()).includes('Traduction locale automatique'),'La traduction reste signalée comme automatique');
    for(const width of [1366,390,320]){await page.setViewportSize({width,height:844});check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Lecture sans débordement à '+width);}
    check(!calls.some(url=>url.includes('/api/chat')||url.includes('/api/admin/inference')),'Lecture et examen ne commandent aucun démarrage moteur');
    check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
    return {checks:checks.length,results:checks,real_corpus:false,real_model:false,simulated_reader_http:true};
  }finally{
    await page.request.post(base+'/fixture/acquisitions?enabled=false',{headers});
    await page.request.post(base+'/fixture/archive-videos?active=false',{headers});
  }
}
