// Actual private queue/index/HTTP; recognizer and translator are simulated.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],writes=[],errors=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{if(request.method()==='POST'&&request.url().includes('/api/admin/video-transcriptions'))writes.push(request.url());});
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.request.post(base+'/fixture/transcriptions?hold=true',{headers:{Origin:base}});
  await page.setViewportSize({width:1366,height:900});await page.goto(base+'/#/bibliotheque/collections');
  const card=page.locator('#next-videos-list .data-card').filter({hasText:'Paroles fictives sans piste'});await card.waitFor();
  check(writes.length===0,'Ouvrir Collections ne lance aucune reconnaissance');
  await card.getByRole('button',{name:'Voir la vidéo'}).click();
  const reader=page.locator('#video-reader-preparation');
  await reader.locator('summary').filter({hasText:'Créer les sous-titres depuis l’audio'}).click();
  check(writes.length===0,'Ouvrir la vidéo et le formulaire ne lance aucune reconnaissance');
  await reader.getByLabel('Langue parlée dans la vidéo').selectOption('en');
  await reader.getByRole('button',{name:'Créer les sous-titres',exact:true}).click();
  const job=reader.locator('[data-audio-job]');
  await job.filter({hasText:'1 segments conservés'}).waitFor();
  check(writes.length===1,'Une seule commande explicite lance la transcription');
  const id=await job.getAttribute('data-audio-job');
  await job.getByRole('button',{name:'Mettre en pause',exact:true}).click();
  await job.filter({hasText:'En pause'}).waitFor();
  let result=await(await page.request.get(base+'/api/admin/video-transcriptions/'+id+'/report')).json();
  check(result.status==='paused'&&result.units_done===1,'Pause conserve le premier passage audio');
  const video=result.video_id;let source=await(await page.request.get(base+'/api/source?id='+encodeURIComponent(video))).json();
  check(source.tracks.length===0,'Une transcription partielle ne devient pas une piste disponible');
  await page.reload();
  await job.filter({hasText:'En pause'}).waitFor();
  check(writes.filter(url=>!url.endsWith('/pause')).length===1,'Rechargement sans reprise automatique');
  await page.request.post(base+'/fixture/transcriptions-release',{headers:{Origin:base}});
  await job.getByRole('button',{name:'Reprendre',exact:true}).click();
  // The source is complete before the separate translation has been enqueued.
  // Wait for this job's recorded link, rather than any older completed card.
  const deadline=Date.now()+30000;
  do{
    result=await(await page.request.get(base+'/api/admin/video-transcriptions/'+id+'/report')).json();
    if(result.status==='completed'&&result.translation_job)break;
    await page.waitForTimeout(100);
  }while(Date.now()<deadline);
  check(result.status==='completed'&&!!result.translation_job,'Le suivi relie la traduction au travail audio courant');
  await reader.locator('[data-caption-job="'+result.translation_job+'"]').filter({hasText:'Piste française préparée'}).waitFor();
  await page.locator('#reader [aria-label="Sous-titres de la vidéo"] option').filter({hasText:'fr · traduction locale'}).waitFor({state:'attached'});
  check(await reader.locator('[data-audio-job]').count()===1&&await reader.locator('[data-caption-job]').count()===1,'Le lecteur affiche les tâches de la vidéo ouverte et sa nouvelle piste');
  check(result.units_done===2&&result.cues===2&&!!result.translation_job,'La suite traduit les deux passages conservés');
  source=await(await page.request.get(base+'/api/source?id='+encodeURIComponent(video))).json();
  check(source.language==='fr'&&source.tracks.some(track=>track.origin==='local_transcription')&&source.tracks.some(track=>track.origin==='local_translation'),'Pistes source reconnue et française présentes ensemble');
  check(source.tracks.some(track=>track.transcription_notice.includes('estimés')),'Origine automatique et estimation des horodatages explicites');
  const download=page.waitForEvent('download');await job.getByRole('button',{name:'Télécharger le rapport audio',exact:true}).click();
  const saved=await download,parts=[];for await(const chunk of await saved.createReadStream())parts.push(chunk);const report=JSON.parse(Buffer.concat(parts).toString());
  check(report.human_review==='not_performed'&&report.units.length===2&&report.units[0].cues[0].text.includes('17 mm'),'Rapport privé garde les paroles et la limite de validation humaine');
  const search=await(await page.request.get(base+'/api/search?q=roulement&domain=all')).json();
  check(search.results.some(item=>item.kind==='video'&&item.id.startsWith(video+'#t=')),'La parole française préparée rejoint la recherche commune avec horodatage');
  for(const width of [1366,390,320]){await page.setViewportSize({width,height:844});check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Préparation audio lisible à '+width);}
  await page.request.post(base+'/fixture/transcriptions?enabled=false&hold=false',{headers:{Origin:base}});
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks,real_recognition:false,real_translation:false};
}
