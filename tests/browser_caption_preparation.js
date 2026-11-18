// Real local queue/index/API and decoded fixture clip; translation is simulated.
async page=>{
  const base='http://10.0.3.2:8769',headers={Origin:base},checks=[],calls=[],errors=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>calls.push(request.url()));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers});
  const fixture=await(await page.request.post(base+'/fixture/captions',{headers})).json();
  await page.goto(base+'/#/bibliotheque/recherche?kind=videos&source='+encodeURIComponent(fixture.video+'#t=2000'));
  const card=page.locator('#video-reader-preparation');await card.waitFor();
  check(!calls.some(url=>url.includes('/api/chat')),'Ouvrir les vidéos ne lance aucune inférence');
  const player=page.locator('#reader video');
  await player.evaluate(video=>{video.dataset.preparationFixture='open';});
  const preparation=card.locator('details').filter({hasText:'Préparer une piste française'});
  if(!await preparation.evaluate(details=>details.open))await preparation.locator('summary').click();
  check(await card.locator('select[aria-label="Piste source à traduire"]').inputValue()==='0','La piste source anglaise est choisie explicitement');
  const previous=(await(await page.request.get(base+'/api/admin/video-captions')).json()).jobs.map(job=>job.id);
  await card.getByRole('button',{name:'Traduire les sous-titres',exact:true}).click();
  let current;
  for(let i=0;i<100&&!current;i++){
    const result=await(await page.request.get(base+'/api/admin/video-captions')).json();
    current=result.jobs.find(job=>!previous.includes(job.id)&&job.video_id===fixture.video&&job.done===16&&['queued','running'].includes(job.status));
    if(!current)await page.waitForTimeout(100);
  }
  check(!!current,'La préparation courante atteint seize segments conservés');
  let job=card.locator('[data-caption-job="'+current.id+'"]');
  await job.filter({hasText:'16 / 40'}).waitFor();
  check(await job.isVisible(),'Le suivi s’affiche sous le lecteur après le lancement');
  check(calls.some(url=>url.includes('/api/admin/video-captions?video_id='+encodeURIComponent(fixture.video))),
    'Le suivi interroge les traductions de la vidéo ouverte');
  await job.getByRole('button',{name:'Mettre en pause',exact:true}).click();
  await job.filter({hasText:'En pause'}).waitFor();
  check((await job.textContent()).includes('16 / 40'),'La pause garde les seize segments déjà traduits');
  const stillEnglish=await(await page.request.get(base+'/api/source?id='+encodeURIComponent(fixture.video))).json();
  check(stillEnglish.language==='en'&&!stillEnglish.tracks.some(track=>track.language==='fr'),'Un brouillon partiel ne devient pas une piste française');
  await page.request.post(base+'/fixture/captions-release',{headers});await job.getByRole('button',{name:'Reprendre',exact:true}).click();
  await job.filter({hasText:'40 / 40'}).filter({hasText:'Piste française préparée'}).waitFor();
  let indexed=false;
  for(let i=0;i<100&&!indexed;i++){
    const response=await page.request.get(base+'/api/source?id='+encodeURIComponent(fixture.video));
    indexed=response.ok()&&(await response.json()).language==='fr';if(!indexed)await page.waitForTimeout(100);
  }
  check(indexed,'La piste complète est indexée après la traduction');
  check((await job.textContent()).includes('relecture à faire'),'La piste terminée garde sa limite de validation humaine');
  const found=await(await page.request.get(base+'/api/search?q=roulement&language=fr&domain=all')).json();
  check(found.results.some(row=>row.id.startsWith(fixture.video)),'Les paroles françaises préparées rejoignent la recherche commune');
  check(await player.getAttribute('data-preparation-fixture')==='open','La préparation conserve le lecteur déjà ouvert');
  await player.evaluate(video=>video.play());
  await page.waitForFunction(()=>{const v=document.querySelector('#reader video');return v?.videoWidth===96&&[...v.textTracks].some(track=>track.language==='fr'&&track.cues?.length===40);});
  await player.evaluate(video=>video.pause());
  check(await player.evaluate(video=>[...video.textTracks].some(track=>track.language==='fr'&&track.mode==='showing')),'Le lecteur décode le média et affiche la nouvelle piste française');
  check((await page.locator('#reader').textContent()).includes('Traduction locale automatique'),'L’origine automatique reste visible dans le lecteur');
  await page.locator('#reader select[aria-label="Sous-titres de la vidéo"]').selectOption('0');
  check(await player.evaluate(video=>video.textTracks[0].language==='en'&&video.textTracks[0].mode==='showing'),'La piste anglaise d’origine reste sélectionnable');
  for(const width of [1366,390,320]){await page.setViewportSize({width,height:844});check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Aucun débordement à '+width);}
  await page.goto(base+'/#/bibliotheque/collections');await page.waitForFunction(()=>S.authReady&&S.user);
  if(!await page.locator('#next-caption-preparation').evaluate(details=>details.open))await page.locator('#next-caption-preparation > summary').click();
  job=page.locator('#next-caption-jobs [data-caption-job="'+current.id+'"]');
  const downloading=page.waitForEvent('download');await job.getByRole('button',{name:'Télécharger le rapport',exact:true}).click();
  const download=await downloading,chunks=[];for await(const chunk of await download.createReadStream())chunks.push(chunk);const report=JSON.parse(Buffer.concat(chunks).toString());
  check(report.total===40&&report.parts.length===40&&report.human_review==='not_performed','Le rapport garde tous les segments et distingue la relecture humaine');
  check(report.parts[10].start_ms===2000&&report.parts[10].end_ms===2150,'Les horodatages sont ceux de la piste source');
  check(!calls.some(url=>url.includes('/api/chat')||url.includes('/api/admin/inference')),'Le navigateur ne commande ni démarrage moteur ni appel direct à l’IA');
  await page.request.post(base+'/fixture/captions?enabled=false',{headers});
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks,real_translation:false};
}
