// Genuine tiny archive and playable WebM; ASR/translation/host/HTTP are simulated.
async page=>{
  const base='http://10.0.3.2:8769',headers={Origin:base},checks=[],errors=[],calls=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>calls.push(request.url()));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers});
  await page.request.post(base+'/fixture/transcriptions?hold=true',{headers});
  check((await page.request.post(base+'/fixture/archive-videos?wait=false&without_tracks=true',{headers})).ok(),'Archive native sans piste préparée pour la recette');
  try{
    await page.request.post(base+'/api/admin/zim-videos/start',{headers,data:{}});let ready=false;
    for(let n=0;n<200;n++){if((await(await page.request.get(base+'/api/zim-videos')).json()).reader_ready){ready=true;break;}await new Promise(r=>setTimeout(r,100));}
    check(ready,'Le lecteur prend en compte le nouveau média sans paroles indexées');
    await page.goto(base+'/#/bibliotheque/collections');await page.waitForFunction(()=>S.authReady&&S.user);
    const card=page.locator('#next-videos-list .data-card').filter({hasText:'Fictional video course'});await card.waitFor();
    check((await card.textContent()).includes('Sous-titres à préparer'),'L’absence de piste reste explicite');
    await card.getByText('Créer les sous-titres depuis l’audio',{exact:true}).click();
    await card.getByLabel('Langue parlée dans la vidéo').selectOption('en');
    const request=page.waitForResponse(response=>response.url().endsWith('/api/admin/video-transcriptions')&&response.request().method()==='POST');
    await card.getByRole('button',{name:'Créer les sous-titres',exact:true}).click();const job=await(await request).json();
    check(!!job.id,'La commande existante accepte aussi l’identifiant de vidéo d’archive');
    await page.waitForFunction(id=>document.querySelector('[data-audio-job="'+id+'"]')?.textContent.includes('1 segments conservés'),job.id);
    const entry=page.locator('[data-audio-job="'+job.id+'"]');await entry.getByRole('button',{name:'Mettre en pause',exact:true}).click();
    await page.waitForFunction(id=>document.querySelector('[data-audio-job="'+id+'"]')?.textContent.includes('En pause'),job.id);
    const paused=await(await page.request.get(base+'/api/admin/video-transcriptions/'+job.id+'/report')).json();
    check(paused.units_done===1&&paused.progress_ms===2000,'La pause conserve la première unité audio terminée');
    const before=await(await page.request.get(base+'/api/source?id='+encodeURIComponent(job.video_id))).json();
    check(!before.transcription_available,'Le brouillon ne devient pas une piste complète dans le lecteur');
    await page.request.post(base+'/fixture/transcriptions-release',{headers});await entry.getByRole('button',{name:'Reprendre',exact:true}).click();
    await page.waitForFunction(id=>document.querySelector('[data-audio-job="'+id+'"]')?.textContent.includes('Paroles transcrites'),job.id);
    let result;
    for(let n=0;n<100;n++){result=await(await page.request.get(base+'/api/admin/video-transcriptions/'+job.id+'/report')).json();if(result.translation_job)break;await new Promise(r=>setTimeout(r,100));}
    check(result.units_done===2&&!!result.translation_job,'La reprise termine l’audio et lance la préparation française choisie');
    await page.waitForFunction(id=>document.querySelector('[data-caption-job="'+id+'"]')?.textContent.includes('Piste française préparée'),result.translation_job);
    const found=await(await page.request.get(base+'/api/search?q=roulement&language=fr&domain=all')).json();const hit=found.results.find(row=>row.id.startsWith(job.video_id));
    check(!!hit,'Les nouvelles paroles françaises sont retrouvées dans le moteur commun');
    await page.evaluate(id=>readSource(id),hit.id);const player=page.locator('#reader video');await player.waitFor();await player.evaluate(v=>v.play());
    await page.waitForFunction(()=>{const video=document.querySelector('#reader video');return video?.videoWidth===96&&[...video.textTracks].some(track=>track.language==='fr'&&track.mode==='showing'&&track.cues?.length===2);});await player.evaluate(v=>v.pause());
    check((await page.locator('#reader').textContent()).includes('Transcription locale'),'L’origine de reconnaissance reste visible avec le français');
    for(const width of [1366,390,320]){await page.setViewportSize({width,height:844});check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Aucun débordement de lecture à '+width);}
    await page.goto(base+'/#/bibliotheque/collections');await page.waitForFunction(()=>S.authReady&&S.user);
    if(!await page.locator('#next-caption-preparation').evaluate(d=>d.open))await page.locator('#next-caption-preparation > summary').click();
    if(!await page.locator('#next-audio-preparation').evaluate(d=>d.open))await page.locator('#next-audio-preparation > summary').click();
    const downloading=page.waitForEvent('download');await page.locator('[data-audio-job="'+job.id+'"]').getByRole('button',{name:'Télécharger le rapport audio'}).click();
    const download=await downloading,chunks=[];for await(const chunk of await download.createReadStream())chunks.push(chunk);const report=JSON.parse(Buffer.concat(chunks).toString());
    check(report.units_done===2&&report.units.every(unit=>unit.media_io.source==='kiwix_byte_ranges'),'Le rapport conserve les unités et les mesures de lecture simulées');
    check(report.human_review==='not_performed','Aucune validation humaine inventée');
    check(!calls.some(url=>url.includes('/api/admin/inference')||url.includes('/api/chat')),'Le navigateur ne démarre aucun moteur lui-même');
    check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
    return {checks:checks.length,results:checks,real_asr:false,real_translation:false,real_corpus:false};
  }finally{
    await page.request.post(base+'/fixture/transcriptions?enabled=false',{headers});
    await page.request.post(base+'/fixture/archive-videos?active=false',{headers});
  }
}
