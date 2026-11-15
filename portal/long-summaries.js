/* Explicit, private long reading. The server owns progress and saved snapshots. */
(()=>{
  'use strict';
  const panel=element('details',undefined,'translation-panel');panel.id='summary-panel';panel.hidden=true;
  const heading=element('summary','Lire les documents et préparer une synthèse');panel.append(heading);
  const body=element('div',undefined,'translation-content');
  body.append(element('p','Pour un livre entier ou plusieurs documents, la lecture avance par étapes et peut prendre longtemps. Fermer cette page ne l’arrête pas. La synthèse et ses notes restent dans ce profil ; les images ne sont pas interprétées. Si vous avez choisi une page précise, seule cette page sera lue.','small'));
  const actions=element('div',undefined,'translation-actions');
  const start=button('Préparer une synthèse longue',()=>action('start')),
    pause=button('Mettre en pause',()=>action('pause'),'secondary'),
    resume=button('Reprendre avec le modèle choisi',()=>action('resume'),'secondary');
  start.id='summary-start';pause.id='summary-pause';resume.id='summary-resume';
  const download=element('a','Télécharger la synthèse et les notes','secondary-link');download.id='summary-export';
  actions.append(start,pause,resume,download);
  const state=element('p');state.id='summary-status';state.setAttribute('role','status');state.setAttribute('aria-live','polite');
  const progress=element('progress');progress.id='summary-progress';progress.setAttribute('aria-label','Passages examinés');
  const sources=element('div');sources.id='summary-sources';
  const notes=element('details');notes.id='summary-notes';notes.append(element('summary','Consulter les notes intermédiaires'));
  const noteBody=element('div');notes.append(noteBody);
  const pages=element('div',undefined,'translation-actions'),previous=button('Étapes précédentes',()=>load(job,Math.max(0,offset-10)),'secondary'),next=button('Étapes suivantes',()=>load(job,offset+10),'secondary');pages.append(previous,next);
  body.append(actions,state,progress,sources,notes,pages);panel.append(body);$('translation-panel').after(panel);
  let job=null,offset=0,timer=null,version=0,busy=false;
  const active=value=>['preparing','queued','running'].includes(value);
  function clear(){clearTimeout(timer);version++;job=null;offset=0;S.summaryActive=false;state.textContent='';sources.replaceChildren();noteBody.replaceChildren();heading.textContent='Lire les documents et préparer une synthèse';for(const node of [pause,resume,download,progress,notes,previous,next])node.hidden=true;start.hidden=false;panel.open=false;refreshSourceChoices();refresh();}
  function refresh(){panel.hidden=!selectedSourceChoices().length&&!job;start.disabled=busy||S.sourceChanging||S.loadingConversation||S.sending||!!S.job||!!S.summaryActive;}
  async function load(id,position=0){
    clearTimeout(timer);job=id;offset=position;const generation=++version,conversation=S.conversation,user=S.user?.id;
    try{
      const data=await api('/summaries/'+encodeURIComponent(id)+'?offset='+position);
      if(generation!==version||conversation!==S.conversation||user!==S.user?.id)return;
      S.summaryActive=active(data.status);panel.hidden=false;
      const labels={preparing:'Préparation des textes',queued:'En attente du moteur',running:data.pending?'Lecture des passages':'Regroupement et rédaction',paused:'Synthèse en pause',error:'Étape à reprendre',incomplete:'Références à vérifier',completed:'Synthèse terminée'};
      heading.textContent=(labels[data.status]||data.status)+' · '+data.read+'/'+data.total+' passages examinés';
      state.textContent=(data.error||data.notice)+(data.unreadable?' '+data.unreadable+' page(s) sans texte extractible.':'');
      progress.hidden=false;progress.max=Math.max(1,data.total);progress.value=data.read+data.unreadable;
      start.hidden=true;pause.hidden=!S.summaryActive;resume.hidden=S.summaryActive||data.status==='completed';download.hidden=false;download.href='/api/summaries/'+encodeURIComponent(id)+'/export';
      sources.replaceChildren();for(const source of data.inputs){const row=element('p',undefined,'small');row.append(button('['+source.number+'] '+source.title,()=>readSource(source.source_id),'text-button'),document.createTextNode(' — '+(source.error||({pending:'Texte à préparer',ready:'Texte conservé pour cette synthèse',unavailable:'Indisponible'}[source.status]||source.status))));sources.append(row);}
      const existing=new Map([...noteBody.children].map(node=>[node.dataset.stepId,node])),articles=[];
      for(const step of data.nodes){let article=existing.get(String(step.id));if(article){articles.push(article);continue;}article=element('article',undefined,'translation-part');article.dataset.stepId=String(step.id);articles.push(article);article.append(element('h3','Étape '+(step.id+1)+(step.level?' · regroupement':' · lecture')));
        for(const note of step.notes){article.append(element('p',note.text));if(note.quote){const quote=element('details');quote.append(element('summary','Source ['+note.source_number+'], page/section '+note.page),element('blockquote',note.quote));const source=data.inputs.find(source=>source.number===note.source_number);if(source){const base=source.source_id.split('#page=')[0],target=base.startsWith('guide:')&&base.toLowerCase().endsWith('.pdf')?base+'#page='+note.page:source.source_id;quote.append(button('Consulter ce passage dans l’original',()=>readSource(target),'text-button'));}article.append(quote);}}
        if(!step.notes.length)article.append(element('p','Aucune information retenue pour la demande dans ces passages.','small muted'));}
      if(articles.length!==noteBody.children.length||articles.some((article,index)=>noteBody.children[index]!==article))noteBody.replaceChildren(...articles);
      notes.hidden=!data.node_count;previous.hidden=position===0;next.hidden=position+data.nodes.length>=data.node_count;
      refreshSourceChoices();refresh();
      if(data.status==='completed'&&data.message_id&&!$('chat-messages').querySelector('[data-message-id="'+data.message_id+'"]')){
        const history=await api('/conversations/'+encodeURIComponent(conversation));
        if(generation!==version||conversation!==S.conversation||user!==S.user?.id)return;
        const answer=history.messages.find(item=>item.id===data.message_id);
        if(answer&&!$('chat-messages').querySelector('[data-summary-message="'+id+'"]')){const box=$('chat-messages'),bottom=box.scrollHeight-box.clientHeight-box.scrollTop<24;const row=message('assistant',answer.content,answer.sources,'Synthèse longue · '+(answer.model||'Assistant'));row.node.dataset.summaryMessage=id;row.node.dataset.messageId=String(answer.id);if(bottom)box.scrollTop=box.scrollHeight;rememberReading();}
        return;
      }
      if(S.summaryActive&&S.view==='chat')timer=setTimeout(()=>load(id,position),2500);
    }catch(error){if(generation===version){state.textContent=error.status?error.message:'Connexion interrompue. Le travail reste enregistré ; nouvelle vérification dans quelques secondes.';if(S.view==='chat'&&error.status!==404&&error.status!==401)timer=setTimeout(()=>load(id,position),5000);}}
  }
  async function action(kind){
    if(busy||S.sending||S.sourceChanging||S.loadingConversation||S.job||!needUser())return;
    const conversation=S.conversation,user=S.user.id,generation=version;busy=true;S.sending=true;refresh();
    try{
      const data=kind==='start'?await api('/summaries',{conversation_id:conversation,source_ids:selectedSourceChoices().map(source=>source.id),mode:$('chat-mode').value,question:$('chat-input').value.trim()||'Fais une synthèse des informations utiles des documents choisis.'}):await api('/summaries/'+encodeURIComponent(job)+'/'+kind,kind==='resume'?{mode:$('chat-mode').value}:{});
      if(generation!==version||conversation!==S.conversation||user!==S.user?.id)return;
      S.sending=false;
      if(kind==='start'){$('chat-input').value='';await openConversation(data.conversation_id);await histories();}
      await load(data.id);panel.open=true;
    }catch(error){toast(error.message);state.textContent=error.message;}
    finally{busy=false;S.sending=false;refreshSourceChoices();refresh();}
  }
  document.addEventListener('survie:source-choices',refresh);
  document.addEventListener('survie:source-state',refresh);
  document.addEventListener('survie:new-conversation',clear);
  document.addEventListener('survie:conversation',event=>{clear();const item=event.detail.summary_jobs?.[0];if(item)void load(item.id);});
  document.addEventListener('survie:view',()=>{clearTimeout(timer);if(S.view==='chat'&&job)void load(job,offset);});
  clear();
})();
