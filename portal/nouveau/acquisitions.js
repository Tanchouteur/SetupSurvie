/* Only an explicit command contacts YouTube; retained tracks work offline. */
(() => {
  const area=element('details');area.id='next-acquisition-preparation';area.className='video-disclosure';area.innerHTML='<summary>Récupérations YouTube</summary><p id="next-acquisition-message" class="small" role="status"></p><div id="next-acquisition-jobs"></div>';
  $('next-caption-preparation').append(area);area.hidden=true;
  let jobs=[],owner=null,loading=false,busy=false,generation=0;
  const states={queued:'En attente',running:'Récupération sur YouTube en cours',paused:'En pause',error:'Récupération non aboutie',completed:'Sous-titres récupérés · relecture à faire'};
  function render(){
    const target=$('next-acquisition-jobs');target.replaceChildren();
    for(const job of jobs){
      const article=element('article',undefined,'data-card video-job');article.dataset.acquisitionJob=job.id;
      article.append(element('h3',job.title),element('p',(window.WorkQueuePreview?.workLabel(job,states[job.status])||states[job.status]||'État inconnu'),'small'));
      if(job.language)article.append(element('p',job.language+' · '+(job.origin==='automatic'?'piste déclarée automatique':'piste déclarée fournie')+' · '+job.cues+' segments','small'));
      if(job.error)article.append(element('p',job.error,'small catalogue-warning'));
      if(job.status==='completed')article.append(element('p',job.notice,'small catalogue-warning'));
      if(job.translation_job)article.append(element('p','La traduction française est dans les préparations de pistes ci-dessus.','small'));
      if(job.status==='completed'&&job.index_status==='pending')article.append(element('p','Piste conservée ; actualisez les vidéos pour terminer sa mise en recherche.','small'));
      const actions=element('div',undefined,'actions');
      if(['queued','running'].includes(job.status))actions.append(button('Mettre en pause',()=>command(job.id,'pause'),'secondary'));
      if(['paused','error'].includes(job.status))actions.append(button('Reprendre avec Internet',()=>command(job.id,'resume'),'secondary'));
      actions.append(button('Télécharger le rapport de récupération',()=>download(job.id),'text-button'));article.append(actions);target.append(article);
    }
    if(!jobs.length)target.append(element('p','Aucune récupération lancée. Choisissez « Récupérer sur YouTube » sur une vidéo.','small muted'));
  }
  async function refresh(){
    area.hidden=S.user?.role!=='admin';if(area.hidden||loading||busy||document.hidden)return;
    if(owner!==S.user.id){owner=S.user.id;jobs=[];render();}
    loading=true;const current=++generation,id=S.user.id;
    try{
      const result=await api('/admin/video-acquisitions');if(current!==generation||S.user?.id!==id)return;
      const changed=result.jobs.some(job=>job.status==='completed'&&(!jobs.some(old=>old.id===job.id&&old.status==='completed')||jobs.some(old=>old.id===job.id&&old.translation_job!==job.translation_job)));
      jobs=result.jobs;render();if(changed)document.dispatchEvent(new Event('survie:videos-changed'));
    }catch(error){if(current===generation)$('next-acquisition-message').textContent=error.message;}
    finally{loading=false;}
  }
  async function command(id,action,options={}){
    if(busy)return;busy=true;const profile=S.user?.id;
    $('next-acquisition-message').textContent=action==='create'?'Récupération demandée avec Internet…':'Commande en cours…';let failure='';
    try{await api('/admin/video-acquisitions'+(action==='create'?'':'/'+encodeURIComponent(id)+'/'+action),action==='create'?{id,mode:$('next-caption-mode').value||'rapide',...options}:{});}
    catch(error){failure=error.message;}finally{busy=false;}
    if(S.user?.id!==profile)return;
    $('next-acquisition-message').textContent=failure||'Commande reçue. Les pistes déjà disponibles restent conservées.';
    $('next-caption-preparation').open=true;area.open=true;await refresh();
  }
  async function download(id){
    try{const profile=S.user?.id,result=await api('/admin/video-acquisitions/'+encodeURIComponent(id)+'/report');if(S.user?.id!==profile)return;downloadReport(result,'recuperation-sous-titres');}
    catch(error){$('next-acquisition-message').textContent=error.message;}
  }
  document.addEventListener('survie:video-cards',event=>{
    area.hidden=S.user?.role!=='admin';if(area.hidden)return;
    for(const item of event.detail){
      if(item.available===false)continue;
      const card=$('next-videos-list').querySelector('[data-video-id="'+CSS.escape(item.id)+'"]');if(!card)continue;
      const details=element('details');details.append(element('summary','Récupérer sur YouTube'));
      const referenceLabel=element('label','Adresse YouTube (si elle n’est pas déjà associée)'),reference=element('input');reference.type='text';reference.maxLength=2000;reference.placeholder='https://www.youtube.com/watch?v=…';referenceLabel.append(reference);
      const languageLabel=element('label','Piste à récupérer'),language=element('select');
      for(const [value,text] of [['','Choix automatique · français en priorité'],['fr','Français'],['en','Anglais']])language.append(new Option(text,value));languageLabel.append(language);
      const translation=element('label',undefined,'video-caption-check'),checkbox=element('input');checkbox.type='checkbox';checkbox.checked=true;translation.append(checkbox,document.createTextNode('Traduire ensuite en français si nécessaire'));
      details.append(referenceLabel,languageLabel,translation,element('p','Nécessite Internet. La référence doit correspondre à cette vidéo ; le logiciel ne la devine pas depuis son titre. Aucun média n’est téléchargé.','small'),button('Récupérer les sous-titres',()=>command(item.id,'create',{reference:reference.value.trim(),language:language.value,translate_french:checkbox.checked}),'secondary'));card.append(details);
    }
    refresh();
  });
  document.addEventListener('survie:auth',()=>{generation++;owner=null;jobs=[];area.hidden=S.user?.role!=='admin';render();refresh();});
  area.addEventListener('toggle',()=>{if(area.open)refresh();});
  setInterval(()=>{if(!$('next-collections').hidden&&(area.open||jobs.some(job=>['queued','running'].includes(job.status))))refresh();},2000);
})();
