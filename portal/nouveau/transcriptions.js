/* Audio preparation is explicit; playback and opening Collections never start it. */
(() => {
  const area=element('details');area.id='next-audio-preparation';area.className='video-disclosure';area.innerHTML='<summary>Transcriptions audio</summary><p id="next-audio-message" class="small" role="status"></p><div id="next-audio-jobs"></div>';
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
      const article=element('article',undefined,'data-card video-job');article.dataset.audioJob=job.id;
      article.append(element('h3',target===$('next-audio-jobs')?job.title:'Transcription audio'),element('p',((window.WorkQueuePreview?.workLabel(job,states[job.status])||states[job.status]||'État inconnu'))+' · '+duration(job.progress_ms||0)+(job.duration_ms?' / environ '+duration(job.duration_ms):''),'small'));
      if(job.detected_language)article.append(element('p','Langue reconnue : '+job.detected_language+' · '+job.cues+' segments conservés','small muted'));
      if(job.error)article.append(element('p',job.error,'small catalogue-warning'));
      if(job.translation_job)article.append(element('p','Traduction française envoyée dans la file d’attente.','small'));
      if(job.status==='completed'&&job.index_status==='pending')article.append(element('p','Piste conservée ; actualisez les vidéos pour terminer sa mise en recherche.','small'));
      const actions=element('div',undefined,'actions');
      if(['queued','running'].includes(job.status))actions.append(button('Mettre en pause',()=>command(job.id,'pause'),'secondary'));
      if(['paused','error'].includes(job.status))actions.append(button('Reprendre',()=>command(job.id,'resume'),'secondary'));
      actions.append(button('Télécharger le rapport audio',()=>download(job.id),'text-button'));article.append(actions);target.append(article);
    }
    if(target===$('next-audio-jobs')&&!visibleJobs.length)target.append(element('p','Aucune transcription lancée. Choisissez une vidéo sans sous-titres.','small muted'));
  }
  function render(){
    renderJobs($('next-audio-jobs'),jobs);
  }
  async function refresh(){
    area.hidden=S.user?.role!=='admin';if(area.hidden||loading||busy||document.hidden)return;
    if(owner!==S.user.id){owner=S.user.id;jobs=[];render();}
    const reading=readerVisible()?reader:null;
    const query=reading?'?video_id='+encodeURIComponent(reading.id):'';
    loading=true;
    const current=++generation,id=S.user.id;
    try{
      const result=await api('/admin/video-transcriptions'+query);
      if(current!==generation||S.user?.id!==id||(reading&&reading!==reader))return;
      const previous=reading?reading.entries:jobs;
      const completed=result.jobs.some(job=>job.status==='completed'&&!previous.some(old=>old.id===job.id&&old.status==='completed'));
      if(JSON.stringify(previous)!==JSON.stringify(result.jobs)){
        if(reading){
          reading.entries=result.jobs;
          renderJobs(reading.jobs,reading.entries);
        }else{
          jobs=result.jobs;
          render();
        }
      }
      if(!result.available)message(result.message,reader?.form.firstElementChild?reader.id:null);
      if(completed)document.dispatchEvent(new Event('survie:videos-changed'));
    }catch(error){if(current===generation)message(error.message);}
    finally{loading=false;}
  }
  async function command(id,action,options={}){
    if(busy)return;busy=true;const profile=S.user?.id;
    const videoId=action==='create'?id:([...jobs,...(reader?.entries||[])].find(job=>job.id===id)?.video_id??null);
    message(action==='create'?'Lancement de la reconnaissance des paroles…':'Commande en cours…',videoId);let failure='';
    try{await api('/admin/video-transcriptions'+(action==='create'?'':'/'+encodeURIComponent(id)+'/'+action),action==='create'?{id,mode:$('next-caption-mode').value||'rapide',...options}:{});}
    catch(error){failure=error.message;}finally{busy=false;}
    if(S.user?.id!==profile)return;
    message(failure,videoId);
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
    details.append(label,translation,button('Créer les sous-titres',()=>command(item.id,'create',{language:language.value,translate_french:checkbox.checked}),'secondary'));
    return details;
  }
  document.addEventListener('survie:video-cards',event=>{
    area.hidden=S.user?.role!=='admin';if(area.hidden)return;
    for(const item of event.detail){
      const card=$('next-videos-list').querySelector('[data-video-id="'+CSS.escape(item.id)+'"]');
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
    reader={host,id,form:formHost,message:status,jobs:target,entries:jobs.filter(job=>job.video_id===id)};
    renderJobs(target,reader.entries);
    refresh();
  });
  document.addEventListener('survie:auth',()=>{generation++;reader=null;owner=null;jobs=[];message('');area.hidden=S.user?.role!=='admin';render();refresh();});
  area.addEventListener('toggle',()=>{if(area.open)refresh();});
  setInterval(()=>{if(readerVisible()||(!$('next-collections').hidden&&(area.open||jobs.some(job=>['queued','running'].includes(job.status)))))refresh();},2000);
})();
