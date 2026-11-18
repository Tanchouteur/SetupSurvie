// Real portal/API/private index; provider and translator are simulated.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],writes=[],errors=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{if(request.method()==='POST'&&request.url().includes('/api/admin/video-acquisitions'))writes.push(request.url());});
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.request.post(base+'/fixture/acquisitions?hold=true&reset=true',{headers:{Origin:base}});
  await page.setViewportSize({width:1366,height:900});await page.goto(base+'/#/bibliotheque/collections');
  const card=page.locator('#next-videos-list .data-card').filter({hasText:'Récupération source fictive'});await card.waitFor();
  check(writes.length===0,'Ouvrir Collections ne contacte pas le fournisseur');
  await card.getByText('Options de sous-titrage',{exact:true}).click();
  const form=card.locator('.video-card-tools > details').filter({hasText:'Récupérer sur YouTube'});
  await form.locator('summary').click();
  await form.getByLabel('Adresse YouTube').fill('https://example.org/not-youtube');
  await form.getByRole('button',{name:'Récupérer les sous-titres',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#next-acquisition-message')?.textContent.includes('HTTPS YouTube'));
  check(await page.locator('#next-acquisition-jobs [data-acquisition-job]').count()===0,'Une référence invalide reste une erreur compréhensible, sans travail vide');
  await form.getByLabel('Adresse YouTube').fill('');await form.getByRole('button',{name:'Récupérer les sous-titres',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#next-acquisition-jobs')?.textContent.includes('Récupération sur YouTube en cours'));
  const job=page.locator('#next-acquisition-jobs [data-acquisition-job]').first(),id=await job.getAttribute('data-acquisition-job');
  await job.getByRole('button',{name:'Mettre en pause',exact:true}).click();
  await page.waitForFunction(id=>document.querySelector('[data-acquisition-job="'+id+'"]')?.textContent.includes('En pause'),id);
  let result=await(await page.request.get(base+'/api/admin/video-acquisitions/'+id+'/report')).json();const video=result.video_id;
  check(result.status==='paused','La pause conserve le travail et attend une reprise explicite');
  let source=await(await page.request.get(base+'/api/source?id='+encodeURIComponent(video))).json();check(source.tracks.length===0,'Aucune piste partielle proposée');
  const before=writes.length;await page.reload();await page.locator('#next-acquisition-preparation').waitFor({state:'attached'});
  await page.locator('#next-caption-preparation').evaluate(node=>node.open=true);await page.locator('#next-acquisition-preparation').evaluate(node=>node.open=true);
  await page.waitForFunction(id=>document.querySelector('[data-acquisition-job="'+id+'"]')?.textContent.includes('En pause'),id);
  check(writes.length===before,'Recharger ne reprend aucune récupération');
  await page.request.post(base+'/fixture/acquisitions?hold=false&blocked=true',{headers:{Origin:base}});
  await page.locator('[data-acquisition-job="'+id+'"]').getByRole('button',{name:'Reprendre avec Internet',exact:true}).click();
  await page.waitForFunction(id=>document.querySelector('[data-acquisition-job="'+id+'"]')?.textContent.includes('YouTube refuse'),id);
  check(await page.locator('[data-acquisition-job="'+id+'"]').getByRole('button',{name:'Reprendre avec Internet',exact:true}).isVisible(),'Un blocage fournisseur propose une reprise et la reconnaissance locale');
  await page.request.post(base+'/fixture/acquisitions-release',{headers:{Origin:base}});
  await page.locator('[data-acquisition-job="'+id+'"]').getByRole('button',{name:'Reprendre avec Internet',exact:true}).click();
  const deadline=Date.now()+30000;
  do{
    result=await(await page.request.get(base+'/api/admin/video-acquisitions/'+id+'/report')).json();
    if(result.status==='completed'&&result.translation_job)break;
    await page.waitForTimeout(100);
  }while(Date.now()<deadline);
  check(result.status==='completed'&&!!result.translation_job,'La piste récupérée rejoint ensuite la traduction française');
  await page.waitForFunction(id=>document.querySelector('[data-caption-job="'+id+'"]')?.textContent.includes('Piste française préparée'),result.translation_job);
  source=await(await page.request.get(base+'/api/source?id='+encodeURIComponent(video))).json();
  check(source.language==='fr'&&source.tracks.some(track=>track.origin==='provided')&&source.tracks.some(track=>track.origin==='local_translation'),'Piste source et piste française restent disponibles ensemble');
  check(source.tracks.some(track=>track.acquisition_notice.includes('vérifiez l’alignement')),'Le lecteur reçoit l’origine et la limite de l’alignement');
  const search=await(await page.request.get(base+'/api/search?q=roulement&domain=all')).json();
  check(search.results.some(item=>item.kind==='video'&&item.id.startsWith(video+'#t=')),'La traduction rejoint la recherche avec accès au passage');
  await page.waitForFunction(()=>document.querySelector('#next-acquisition-jobs')?.textContent.includes('Sous-titres récupérés'));
  const download=page.waitForEvent('download');await page.locator('[data-acquisition-job="'+id+'"]').getByRole('button',{name:'Télécharger le rapport de récupération',exact:true}).click();
  const saved=await download,chunks=[];for await(const chunk of await saved.createReadStream())chunks.push(chunk);const report=JSON.parse(Buffer.concat(chunks).toString());
  check(saved.suggestedFilename().includes('-v'+report.version+'-')&&!saved.suggestedFilename().includes(id),'Nom du rapport avec version et heure, sans identifiant aléatoire');
  check(report.provider_result.raw_provider_cues[0].text.includes('17 mm')&&report.human_review==='not_performed','Rapport privé conserve les paroles source et la validation humaine restante');
  for(const width of [1366,390,320]){await page.setViewportSize({width,height:844});check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Récupération lisible à '+width);}
  await page.request.post(base+'/fixture/acquisitions?enabled=false&hold=false',{headers:{Origin:base}});
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks,real_provider:false,real_translation:false};
}
