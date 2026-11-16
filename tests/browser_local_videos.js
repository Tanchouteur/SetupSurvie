// A generated 1.2 KB green clip, local captions and real HTTP player; no model.
async page=>{
  const base='http://10.0.3.2:8769',headers={Origin:base},checks=[],calls=[],errors=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>calls.push({url:request.url(),method:request.method()}));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers});
  check((await page.request.post(base+'/fixture/videos',{headers})).ok(),'Petits médias synthétiques préparés sans téléchargement');
  await page.goto(base+'/#/bibliotheque/collections');await page.waitForFunction(()=>S.authReady&&S.user);
  await page.locator('#next-videos-index').click();await page.waitForFunction(()=>document.getElementById('next-videos-status').textContent.includes('Inventaire terminé'));
  check(await page.locator('#next-videos-list .data-card').count()===2,'Vidéos locales inventoriées depuis Collections');
  check((await page.locator('#next-videos-list').textContent()).includes('Sous-titres à préparer'),'Vidéo sans piste signalée séparément');
  const found=await(await page.request.get(base+'/api/search?q=rotor&domain=all')).json();const hit=found.results.find(row=>row.kind==='video'&&row.id.includes('#t=8000'));
  check(!!hit,'Le moteur commun retrouve le passage horodaté des sous-titres');
  const before=calls.length;await page.evaluate(id=>readSource(id),hit.id);
  const player=page.locator('#reader video');await player.waitFor();
  await player.evaluate(v=>v.play());
  await page.waitForFunction(()=>{const v=document.querySelector('#reader video');return v&&v.readyState>=2&&v.videoWidth===96&&v.currentTime>=7.9;});
  await player.evaluate(v=>v.pause());
  check(Math.abs(await player.evaluate(v=>v.duration)-12)<.2,'Le vrai navigateur décode le petit fichier local de douze secondes');
  check(await player.evaluate(v=>v.currentTime>=7.9),'La vidéo s’ouvre sur le passage trouvé');
  check((await page.locator('#reader').textContent()).includes('non vérifiés'),'Limites de fidélité et de synchronisation conservées');
  await page.waitForFunction(()=>[...document.querySelector('#reader video').textTracks].some(t=>t.language==='fr'&&t.cues?.length===2));
  check(await player.evaluate(v=>[...v.textTracks].find(t=>t.language==='fr').mode==='showing'),'Piste française locale proposée par défaut');
  await page.locator('#reader select[aria-label="Sous-titres de la vidéo"]').selectOption('off');
  check(await player.evaluate(v=>[...v.textTracks].every(t=>t.mode==='disabled')),'Sous-titres désactivables');
  await page.locator('#reader select[aria-label="Sous-titres de la vidéo"]').selectOption('0');
  await page.waitForFunction(()=>{const v=document.querySelector('#reader video');return v.textTracks[0].cues?.length>0;});
  check(await player.evaluate(v=>v.textTracks[0].mode==='showing'),'Piste anglaise sélectionnable sans traduction');
  await player.evaluate(v=>{v.currentTime=9;v.dispatchEvent(new Event('pause'));});
  await page.evaluate(id=>readSource(id.split('#t=')[0]),hit.id);
  await page.waitForFunction(()=>document.querySelector('#reader video')?.currentTime>=8.9);
  check(true,'Position retrouvée pour la même vidéo et la même révision');
  check(calls.slice(before).every(row=>!row.url.includes('/api/chat')&&!row.url.includes('/api/translations')&&!row.url.includes('/api/admin/inference')),'Lire une vidéo ou une piste ne lance ni modèle ni traduction');
  for(const width of [1366,390,320]){await page.setViewportSize({width,height:844});await page.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth);check(await player.evaluate(v=>v.getBoundingClientRect().width<=innerWidth),'Lecteur vidéo adapté à '+width);}
  await page.locator('#navigation [data-route="assistant"]').click();check(await player.evaluate(v=>v.paused),'Quitter le lecteur met le média en pause');
  await page.goto(base+'/#/bibliotheque/collections');await page.waitForFunction(()=>S.authReady&&S.user);
  const downloading=page.waitForEvent('download');await page.locator('#next-videos-report').click();const download=await downloading,chunks=[];for await(const chunk of await download.createReadStream())chunks.push(chunk);const report=JSON.parse(Buffer.concat(chunks).toString());
  check(report.per_video.length===2&&report.per_video.every(v=>v.validation.human_review==='not_performed'),'Rapport par vidéo, sans inventer une validation humaine');
  check(report.per_video.some(v=>v.subtitle_status==='missing'),'Les pistes manquantes restent dans le rapport exporté');
  await page.locator('#collection-filter').fill('rotor');await page.locator('#collection-filter').dispatchEvent('input');
  await page.waitForFunction(()=>document.querySelectorAll('#next-videos-list .data-card').length===1);
  check((await page.locator('#next-videos-list').textContent()).includes('rotor'),'Le filtre des collections inclut les titres vidéo');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks};
}
