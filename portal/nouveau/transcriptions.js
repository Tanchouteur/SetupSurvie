/* Audio preparation is explicit; playback and opening Collections never start it. */
(() => {
  const area=element('details');area.id='next-audio-preparation';area.innerHTML='<summary>Suivre la création des sous-titres depuis l’audio</summary><p class="small">Sur une vidéo sans sous-titres, choisissez « Créer les sous-titres depuis l’audio ». Le logiciel reconnaît les paroles, puis peut les traduire en français. La vidéo d’origine reste conservée. Vérifiez les mots, nombres et passages techniques.</p><p id="next-audio-message" class="small" role="status"></p><div id="next-audio-jobs"></div>';
  $('next-caption-preparation').append(area);area.hidden=true;
  let jobs=[],owner=null,loading=false,busy=false,generation=0;
  const states={queued:'En attente',running:'Reconnaissance des paroles en cours',paused:'En pause',error:'À reprendre après vérification',completed:'Paroles transcrites · relecture à faire'};
  const duration=ms=>Math.floor(ms/60000)+' min '+Math.floor(ms%60000/1000)+' s';
  function render(){
    const target=$('next-audio-jobs');target.replaceChildren();
    for(const job of jobs){
      const article=element('article',undefined,'data-card');article.dataset.audioJob=job.id;
      article.append(element('h3',job.title),element('p',(states[job.status]||job.status)+' · '+duration(job.progress_ms||0)+(job.duration_ms?' / environ '+duration(job.duration_ms):''),'small'));
      if(job.detected_language)article.append(element('p','Langue reconnue : '+job.detected_language+' · '+job.cues+' segments conservés','small muted'));
      if(job.error)article.append(element('p',job.error,'small catalogue-warning'));
      if(job.translation_job)article.append(element('p','Traduction française lancée : son suivi est dans les préparations de pistes ci-dessus.','small'));
      if(job.status==='completed'&&job.index_status==='pending')article.append(element('p','Piste conservée ; actualisez les vidéos pour terminer sa mise en recherche.','small'));
      if(job.status==='completed')article.append(element('p','Les horodatages sont estimés. Comparez les passages utiles avec l’original ; la transcription ne décrit pas les gestes de la vidéo.','small'));
      const actions=element('div',undefined,'actions');
      if(['queued','running'].includes(job.status))actions.append(button('Mettre en pause',()=>command(job.id,'pause'),'secondary'));
      if(['paused','error'].includes(job.status))actions.append(button('Reprendre',()=>command(job.id,'resume'),'secondary'));
      actions.append(button('Télécharger le rapport audio',()=>download(job.id),'secondary'));article.append(actions);target.append(article);
    }
    if(!jobs.length)target.append(element('p','Aucune transcription lancée. Choisissez une vidéo sans sous-titres.','small muted'));
  }
  async function refresh(){
    area.hidden=S.user?.role!=='admin';if(area.hidden||loading||busy||document.hidden)return;
    if(owner!==S.user.id){owner=S.user.id;jobs=[];render();}
    loading=true;const current=++generation,id=S.user.id;
    try{
      const result=await api('/admin/video-transcriptions');if(current!==generation||S.user?.id!==id)return;
      const completed=result.jobs.some(job=>job.status==='completed'&&jobs.some(old=>old.id===job.id&&old.status!=='completed'));
      jobs=result.jobs;render();if(!result.available)$('next-audio-message').textContent=result.message;
      if(completed)document.dispatchEvent(new Event('survie:videos-changed'));
    }catch(error){if(current===generation)$('next-audio-message').textContent=error.message;}
    finally{loading=false;}
  }
  async function command(id,action,options={}){
    if(busy)return;busy=true;const profile=S.user?.id;
    $('next-audio-message').textContent=action==='create'?'Lancement de la reconnaissance des paroles…':'Commande en cours…';let failure='';
    try{await api('/admin/video-transcriptions'+(action==='create'?'':'/'+encodeURIComponent(id)+'/'+action),action==='create'?{id,mode:$('next-caption-mode').value||'rapide',...options}:{});}
    catch(error){failure=error.message;}finally{busy=false;}
    if(S.user?.id!==profile)return;
    $('next-audio-message').textContent=failure||'Commande reçue. Les passages terminés sont conservés.';
    $('next-caption-preparation').open=true;area.open=true;await refresh();
  }
  async function download(id){
    try{
      const profile=S.user?.id,result=await api('/admin/video-transcriptions/'+encodeURIComponent(id)+'/report');if(S.user?.id!==profile)return;
      const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'})),link=element('a');link.href=url;link.download='setupsurvie-audio-'+id+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    }catch(error){$('next-audio-message').textContent=error.message;}
  }
  document.addEventListener('survie:video-cards',event=>{
    area.hidden=S.user?.role!=='admin';if(area.hidden)return;
    for(const item of event.detail){
      if(item.available===false||item.tracks.some(track=>track.status==='passed'))continue;
      const card=[...$('next-videos-list').children].find(node=>node.dataset.videoId===item.id);if(!card)continue;
      const details=element('details');details.append(element('summary','Créer les sous-titres depuis l’audio'));
      const label=element('label','Langue parlée'),language=element('select');language.setAttribute('aria-label','Langue parlée dans la vidéo');
      for(const [value,text] of [['','Détection automatique'],['en','Anglais'],['fr','Français']])language.append(new Option(text,value));label.append(language);
      const translation=element('label'),checkbox=element('input');translation.style.flexDirection='row';translation.style.alignItems='center';translation.style.gap='8px';checkbox.type='checkbox';checkbox.checked=true;checkbox.style.width='auto';checkbox.style.flex='0 0 auto';translation.append(checkbox,document.createTextNode('Préparer aussi la version française'));
      details.append(label,translation,element('p','La préparation peut durer longtemps. Elle garde les passages terminés et reprend à votre demande après une pause.','small'),button('Créer les sous-titres',()=>command(item.id,'create',{language:language.value,translate_french:checkbox.checked}),'secondary'));card.append(details);
    }
    refresh();
  });
  document.addEventListener('survie:auth',()=>{generation++;owner=null;jobs=[];area.hidden=S.user?.role!=='admin';render();refresh();});
  area.addEventListener('toggle',()=>{if(area.open)refresh();});
  setInterval(()=>{if(!$('next-collections').hidden&&(area.open||jobs.some(job=>['queued','running'].includes(job.status))))refresh();},2000);
})();
