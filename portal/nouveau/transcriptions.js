/* Audio preparation is explicit; playback and opening Collections never start it. */
(() => {
  const area=element('details');area.id='next-audio-preparation';area.innerHTML='<summary>Suivre la création des sous-titres depuis l’audio</summary><p class="small">Sur une vidéo sans sous-titres, choisissez « Créer les sous-titres depuis l’audio ». Le logiciel reconnaît les paroles, puis peut les traduire en français. La vidéo d’origine reste conservée. Vérifiez les mots, nombres et passages techniques.</p><p id="next-audio-message" class="small" role="status"></p><div id="next-audio-jobs"></div>';
  $('next-caption-preparation').append(area);area.hidden=true;
  let reader=null;
  const readerVisible=()=>reader?.host.isConnected&&!$('reader').hidden&&!$('view-library').hidden;
  let jobs=[],owner=null,loading=false,busy=false,generation=0;
  const states={queued:'En attente',running:'Reconnaissance des paroles en cours',paused:'En pause',error:'À reprendre après vérification',completed:'Paroles transcrites · relecture à faire'};
  const duration=ms=>Math.floor(ms/60000)+' min '+Math.floor(ms%60000/1000)+' s';
  function message(text,videoId=reader?.id){
    $('next-audio-message').textContent=text;
    if(reader?.host.isConnected&&reader.id===videoId)reader.message.textContent=text;
  }
  function renderJobs(target,visibleJobs){
    target.replaceChildren();
    for(const job of visibleJobs){
      const article=element('article',undefined,'data-card');article.dataset.audioJob=job.id;
      article.append(element('h3',job.title),element('p',(states[job.status]||job.status)+' · '+duration(job.progress_ms||0)+(job.duration_ms?' / environ '+duration(job.duration_ms):''),'small'));
      if(job.detected_language)article.append(element('p','Langue reconnue : '+job.detected_language+' · '+job.cues+' segments conservés','small muted'));
      if(job.error)article.append(element('p',job.error,'small catalogue-warning'));
      if(job.translation_job)article.append(element('p','Traduction française envoyée dans la file d’attente.','small'));
      if(job.status==='completed'&&job.index_status==='pending')article.append(element('p','Piste conservée ; actualisez les vidéos pour terminer sa mise en recherche.','small'));
      if(job.status==='completed')article.append(element('p','Les horodatages sont estimés. Comparez les passages utiles avec l’original ; la transcription ne décrit pas les gestes de la vidéo.','small'));
      const actions=element('div',undefined,'actions');
      if(['queued','running'].includes(job.status))actions.append(button('Mettre en pause',()=>command(job.id,'pause'),'secondary'));
      if(['paused','error'].includes(job.status))actions.append(button('Reprendre',()=>command(job.id,'resume'),'secondary'));
      actions.append(button('Télécharger le rapport audio',()=>download(job.id),'secondary'));article.append(actions);target.append(article);
    }
    if(target===$('next-audio-jobs')&&!visibleJobs.length)target.append(element('p','Aucune transcription lancée. Choisissez une vidéo sans sous-titres.','small muted'));
  }
  function render(){
    renderJobs($('next-audio-jobs'),jobs);
    if(reader?.host.isConnected)renderJobs(reader.jobs,jobs.filter(job=>job.video_id===reader.id));
  }
  async function refresh(){
    area.hidden=S.user?.role!=='admin';if(area.hidden||loading||busy||document.hidden)return;
    if(owner!==S.user.id){owner=S.user.id;jobs=[];render();}
    loading=true;const current=++generation,id=S.user.id;
    try{
      const result=await api('/admin/video-transcriptions');if(current!==generation||S.user?.id!==id)return;
      const completed=result.jobs.some(job=>job.status==='completed'&&!jobs.some(old=>old.id===job.id&&old.status==='completed'));
      if(JSON.stringify(jobs)!==JSON.stringify(result.jobs)){jobs=result.jobs;render();}
      if(!result.available)message(result.message,reader?.form.firstElementChild?reader.id:null);
      if(completed)document.dispatchEvent(new Event('survie:videos-changed'));
    }catch(error){if(current===generation)message(error.message);}
    finally{loading=false;}
  }
  async function command(id,action,options={}){
    if(busy)return;busy=true;const profile=S.user?.id;
    const videoId=action==='create'?id:jobs.find(job=>job.id===id)?.video_id;
    message(action==='create'?'Lancement de la reconnaissance des paroles…':'Commande en cours…',videoId);let failure='';
    try{await api('/admin/video-transcriptions'+(action==='create'?'':'/'+encodeURIComponent(id)+'/'+action),action==='create'?{id,mode:$('next-caption-mode').value||'rapide',...options}:{});}
    catch(error){failure=error.message;}finally{busy=false;}
    if(S.user?.id!==profile)return;
    message(failure||'Commande reçue. Les passages terminés sont conservés.',videoId);
    $('next-caption-preparation').open=true;area.open=true;await refresh();
  }
  async function download(id){
    try{
      const profile=S.user?.id,result=await api('/admin/video-transcriptions/'+encodeURIComponent(id)+'/report');if(S.user?.id!==profile)return;
      downloadReport(result,'transcription-audio');
    }catch(error){message(error.message);}
  }
  function preparation(item){
    if((item.archive_video&&!item.audio_transcription_supported)||item.tracks.some(track=>track.status==='passed'))return;
    const details=element('details');details.append(element('summary','Créer les sous-titres depuis l’audio'));
    const label=element('label','Langue parlée'),language=element('select');language.setAttribute('aria-label','Langue parlée dans la vidéo');
    for(const [value,text] of [['','Détection automatique'],['en','Anglais'],['fr','Français']])language.append(new Option(text,value));label.append(language);
    const translation=element('label',undefined,'video-caption-check'),checkbox=element('input');checkbox.type='checkbox';checkbox.checked=true;translation.append(checkbox,document.createTextNode('Préparer aussi la version française'));
    details.append(label,translation,element('p','La préparation peut durer longtemps. Elle garde les passages terminés et reprend à votre demande après une pause.','small'),button('Créer les sous-titres',()=>command(item.id,'create',{language:language.value,translate_french:checkbox.checked}),'secondary'));
    return details;
  }
  document.addEventListener('survie:video-cards',event=>{
    area.hidden=S.user?.role!=='admin';if(area.hidden)return;
    for(const item of event.detail){
      const card=[...$('next-videos-list').children].find(card=>card.dataset.videoId===item.id);
      if(!card||item.available===false)continue;
      const form=preparation(item);
      if(form)card.append(form);
    }
    refresh();
  });
  document.addEventListener('survie:video-reader',event=>{
    const {item,host}=event.detail;
    if(S.user?.role!=='admin')return;
    const id=item.id.split('#')[0];
    const form=preparation({...item,id});
    if(reader?.host===host){
      const previous=reader.form.firstElementChild;
      if(form&&previous)form.open=previous.open;
      reader.form.replaceChildren(...(form?[form]:[]));
      return;
    }
    const panel=element('div'),formHost=element('div'),status=element('p',undefined,'small'),target=element('div');
    status.setAttribute('role','status');
    if(form)formHost.append(form);
    panel.append(formHost,status,target);host.append(panel);
    reader={host,id,form:formHost,message:status,jobs:target};
    renderJobs(target,jobs.filter(job=>job.video_id===id));
    refresh();
  });
  document.addEventListener('survie:auth',()=>{generation++;reader=null;owner=null;jobs=[];message('');area.hidden=S.user?.role!=='admin';render();refresh();});
  area.addEventListener('toggle',()=>{if(area.open)refresh();});
  setInterval(()=>{if(readerVisible()||(!$('next-collections').hidden&&(area.open||jobs.some(job=>['queued','running'].includes(job.status)))))refresh();},2000);
})();
