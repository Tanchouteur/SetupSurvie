/* Explicit preparation, independent of reading a video. No automatic inference. */
(() => {
  const area=element('details');area.id='next-caption-preparation';area.innerHTML='<summary>Préparer les sous-titres</summary><p class="small">Traduisez une piste source depuis sa vidéo. Les temps restent ceux de l’original. Les pistes terminées deviennent utilisables sans IA ; la relecture du sens reste à faire.</p><label>Modèle pour la préparation<select id="next-caption-mode"></select></label><p id="next-caption-message" class="small" role="status"></p><div id="next-caption-jobs"></div>';
  $('next-videos').append(area);
  area.hidden=true;
  let jobs=[],owner=null,loading=false,busy=false,version=0;
  const states={queued:'En attente',running:'Traduction en cours',paused:'En pause',error:'À reprendre après vérification',completed:'Piste française préparée · relecture à faire'};
  function modes(){
    const select=$('next-caption-mode'),available=S.status?.modes||[],previous=select.value;
    if(available.length&&[...select.options].map(o=>o.value).join('|')!==available.map(o=>o.id).join('|')){
      select.replaceChildren(...available.map(mode=>new Option(mode.name,mode.id)));
      if(available.some(mode=>mode.id===previous))select.value=previous;
    }
  }
  function render(){
    const target=$('next-caption-jobs');target.replaceChildren();
    for(const job of jobs){
      const article=element('article',undefined,'data-card');article.dataset.captionJob=job.id;
      article.append(element('h3',job.title),element('p',(states[job.status]||job.status)+' · '+job.done+' / '+job.total+' segments','small'));
      if(job.error)article.append(element('p',job.error,'small catalogue-warning'));
      if(job.warnings)article.append(element('p',job.warnings+' segment(s) à vérifier dans le rapport.','small catalogue-warning'));
      if(job.status==='completed')article.append(element('p','Lisez le début, le milieu, la fin et les passages techniques en comparant à l’original. Les contrôles automatiques ne certifient pas la traduction.','small'));
      if(job.status==='completed'&&job.index_status==='pending')article.append(element('p','Piste conservée ; actualisez les vidéos pour terminer sa mise en recherche.','small'));
      const actions=element('div',undefined,'actions');
      if(['queued','running'].includes(job.status))actions.append(button('Mettre en pause',()=>command(job.id,'pause'),'secondary'));
      if(['paused','error'].includes(job.status))actions.append(button('Reprendre',()=>command(job.id,'resume'),'secondary'));
      actions.append(button('Télécharger le rapport',()=>download(job.id),'secondary'));article.append(actions);target.append(article);
    }
    if(!jobs.length)target.append(element('p','Aucune préparation lancée. Choisissez une piste à traduire sur une vidéo.','small muted'));
  }
  async function refresh(){
    modes();area.hidden=S.user?.role!=='admin';if(area.hidden||loading||busy||document.hidden)return;
    if(owner!==S.user.id){owner=S.user.id;jobs=[];render();}
    loading=true;const current=++version,id=S.user.id;
    try{
      const result=await api('/admin/video-captions');if(current!==version||S.user?.id!==id)return;
      const completed=result.jobs.some(job=>job.status==='completed'&&jobs.some(old=>old.id===job.id&&old.status!=='completed'));
      jobs=result.jobs;render();if(completed)document.dispatchEvent(new Event('survie:videos-changed'));
    }catch(error){if(current===version)$('next-caption-message').textContent=error.message;}
    finally{loading=false;}
  }
  async function command(id,action,track){
    if(busy)return;busy=true;const profile=S.user?.id;
    $('next-caption-message').textContent=action==='create'?'Lancement de la préparation…':'Commande en cours…';
    let failure='';
    try{
      await api('/admin/video-captions'+(action==='create'?'':'/'+encodeURIComponent(id)+'/'+action),action==='create'?{id,track,mode:$('next-caption-mode').value||'rapide'}:action==='resume'?{mode:$('next-caption-mode').value||'rapide'}:{});
    }catch(error){failure=error.message;}
    finally{busy=false;}
    if(S.user?.id!==profile)return;
    $('next-caption-message').textContent=failure||'Commande reçue. Les segments terminés sont conservés.';area.open=true;await refresh();
  }
  async function download(id){
    try{
      const profile=S.user?.id,result=await api('/admin/video-captions/'+encodeURIComponent(id)+'/report');if(S.user?.id!==profile)return;
      downloadReport(result,'sous-titres');
    }catch(error){$('next-caption-message').textContent=error.message;}
  }
  document.addEventListener('survie:video-cards',event=>{
    modes();area.hidden=S.user?.role!=='admin';if(area.hidden)return;
    for(const item of event.detail){
      const card=[...$('next-videos-list').children].find(card=>card.dataset.videoId===item.id);if(!card||item.available===false)continue;
      const tracks=item.tracks.filter(track=>track.status==='passed'&&track.language&&!track.language.startsWith('fr')&&track.origin!=='local_translation');
      if(!tracks.length){if(item.subtitle_status==='missing')card.append(element('p','La vidéo n’a pas encore de piste source. Utilisez « Créer les sous-titres depuis l’audio ».','small muted'));continue;}
      const details=element('details');details.append(element('summary','Préparer une piste française'));
      const label=element('label','Piste source'),select=element('select');select.setAttribute('aria-label','Piste source à traduire');
      tracks.forEach(track=>select.append(new Option(track.language+' · '+({automatic:'automatique',provided:'fournie',unknown:'origine inconnue'}[track.origin]||track.origin),String(track.id))));label.append(select);
      details.append(label,button('Traduire les sous-titres',()=>command(item.id,'create',Number(select.value)),'secondary'));card.append(details);
    }
    refresh();
  });
  document.addEventListener('survie:auth',()=>{version++;owner=null;jobs=[];area.hidden=S.user?.role!=='admin';render();refresh();});
  setInterval(()=>{if(!$('next-collections').hidden&&(area.open||jobs.some(job=>['queued','running'].includes(job.status))))refresh();},2000);
  area.addEventListener('toggle',()=>{if(area.open)refresh();});
})();
