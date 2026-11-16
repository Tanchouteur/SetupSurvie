/* One set of controls, profile-owned organization and independent evidence. */
(() => {
  const chat=$('view-chat'),context=chat.querySelector('.next-chat-context');
  const tools=element('details',undefined,'assistant-tools');tools.append(element('summary','Outils'));
  const bottom=document.querySelector('.sidebar-bottom');
  tools.append($('admin-nav'),bottom.querySelector('.sidebar-tools'));bottom.prepend(tools);

  const body=element('div',undefined,'assistant-workspace');body.id='assistant-workspace';
  const left=element('aside',undefined,'assistant-history');left.id='assistant-history';left.setAttribute('aria-label','Conversations et dossiers');
  const center=element('div',undefined,'assistant-discussion');center.id='assistant-discussion';
  const right=element('aside',undefined,'assistant-documents');right.id='assistant-documents';right.setAttribute('aria-label','Documents de la discussion');
  const title=element('h2','Conversations');
  const create=button('Nouvelle discussion',()=>newConversation());left.append(title,create);
  const search=element('input');search.type='search';search.maxLength=160;search.placeholder='Rechercher une conversation';search.setAttribute('aria-label','Rechercher une conversation');
  const folders=element('div',undefined,'assistant-folders');folders.setAttribute('aria-label','Dossiers personnels');
  const add=button('Créer un dossier',()=>edit('Créer un dossier','Nom du dossier','',value=>api('/conversation-folders',{name:value})));add.id='assistant-folder-create';
  const folderState=element('p','','small muted');folderState.setAttribute('role','status');
  const list=$('conversation-list');left.append(search,folders,add,folderState,list);
  const previous=button('Conversations précédentes',()=>{offset=Math.max(0,offset-100);void histories();},'secondary');previous.hidden=true;left.append(previous);
  const more=button('Voir la suite',()=>{offset+=100;void histories();},'secondary');more.hidden=true;left.append(more);
  const banner=$('inference-banner');center.append(banner,$('chat-messages'),$('chat-form'));
  body.append(left,center,right);chat.append(body);
  const selectedTitle=element('h2','Documents choisis'),usedTitle=element('h2','Sources consultées');
  const used=element('div');used.id='assistant-consulted-sources';
  right.append(selectedTitle,context,usedTitle,used);
  const responseOptions=element('details');responseOptions.append(element('summary','Options de réponse'));
  const modelTrials=element('input');modelTrials.type='checkbox';const trialsLabel=element('label','Afficher les modèles d’essai');trialsLabel.prepend(modelTrials);responseOptions.append(trialsLabel);
  const modelSelect=$('chat-mode');
  function trialVisibility(){for(const group of modelSelect.querySelectorAll('optgroup'))if(group.label==='Autres modèles à comparer')group.hidden=!modelTrials.checked;}
  modelTrials.onchange=trialVisibility;new MutationObserver(trialVisibility).observe(modelSelect,{childList:true});
  const scope=$('chat-domain').closest('label');responseOptions.append(scope);right.append(responseOptions);

  const empty=element('p','Aucun document choisi. Vous pouvez en sélectionner dans la bibliothèque.','small muted');context.prepend(empty);
  const library=element('a','Choisir dans la bibliothèque');library.href='#/bibliotheque';library.dataset.route='bibliotheque';context.prepend(library);
  const tabs=element('div',undefined,'assistant-view-controls');tabs.setAttribute('aria-label','Zones de la discussion');
  for(const [key,label] of [['history','Conversations'],['discussion','Discussion'],['documents','Documents']]){
    const b=button(label,()=>select(key),'secondary');b.dataset.assistantZone=key;tabs.append(b);
  }
  chat.querySelector('.chat-top').after(tabs);
  $('next-history-open').hidden=true;
  let folder='all',offset=0,generation=0,folderItems=[],evidence=new Map(),timer=0;
  body.dataset.zone='discussion';body.dataset.left='open';body.dataset.right='open';
  function select(zone){
    if(innerWidth<=1000)body.dataset.zone=zone;
    else if(zone==='history')body.dataset.left=body.dataset.left==='open'?'closed':'open';
    else if(zone==='documents')body.dataset.right=body.dataset.right==='open'?'closed':'open';
    else{body.dataset.left='closed';body.dataset.right='closed';}
    refreshZones();
  }
  function refreshZones(){for(const b of tabs.children)b.setAttribute('aria-pressed',String(innerWidth<=1000?body.dataset.zone===b.dataset.assistantZone:b.dataset.assistantZone==='history'?body.dataset.left==='open':b.dataset.assistantZone==='documents'?body.dataset.right==='open':body.dataset.left==='closed'&&body.dataset.right==='closed'));}
  window.addEventListener('resize',refreshZones);refreshZones();
  const editor=element('dialog');editor.id='assistant-editor';editor.setAttribute('aria-labelledby','assistant-editor-title');
  const form=element('form'),heading=element('h2');heading.id='assistant-editor-title';
  const input=element('input');input.maxLength=80;input.required=true;
  const label=element('label');label.append(element('span'),input);
  const error=element('p');error.setAttribute('role','alert');
  const save=element('button','Enregistrer');save.type='submit';
  const cancel=button('Annuler',()=>editor.close(),'secondary');
  form.append(heading,label,error,save,cancel);editor.append(form);document.body.append(editor);document.dispatchEvent(new CustomEvent('survie:dialog',{detail:editor}));
  let commit=null,editOwner=null;
  function edit(title,caption,value,action){heading.textContent=title;label.firstChild.textContent=caption;input.value=value;error.textContent='';commit=action;editOwner=S.user?.id;editor.showModal();input.focus();}
  form.onsubmit=async event=>{event.preventDefault();if(!commit||editOwner!==S.user?.id)return;save.disabled=true;
    try{await commit(input.value.trim());editor.close();await histories();}catch(e){error.textContent=e.message;}finally{save.disabled=false;}};
  function menu(label){const d=element('details',undefined,'assistant-row-menu');const summary=element('summary','⋯');summary.setAttribute('aria-label',label);d.append(summary);return d;}
  function folderButton(value,label){const b=button(label,()=>{folder=value;offset=0;histories();},'secondary');b.setAttribute('aria-pressed',String(folder===value));return b;}
  histories=async()=>{
    if(!S.user)return;const own=++generation,owner=S.user.id;
    try{
      let data,organization,degraded=false;
      try{[data,organization]=await Promise.all([api('/conversations?'+new URLSearchParams({folder,q:search.value,offset:String(offset)})),api('/conversation-folders')]);}
      catch(_){data=await api('/conversations');organization={folders:[]};degraded=true;folder='all';offset=0;}
      if(own!==generation||S.user?.id!==owner)return;folderItems=organization.folders;
      if(folder!=='all'&&folder!=='unfiled'&&!folderItems.some(f=>f.id===folder)){folder='all';offset=0;return histories();}
      folders.replaceChildren(folderButton('all','Toutes les conversations'),folderButton('unfiled','Sans dossier'));
      for(const f of folderItems){const row=element('div',undefined,'assistant-folder-row'),m=menu('Actions du dossier '+f.name);
        m.append(button('Renommer',()=>edit('Renommer le dossier','Nom du dossier',f.name,value=>api('/conversation-folders/'+encodeURIComponent(f.id),{name:value},{method:'PATCH'})),'text-button'),button('Supprimer le dossier',async()=>{if(!confirm('Supprimer le dossier « '+f.name+' » ? Ses conversations seront conservées dans Sans dossier.'))return;try{await api('/conversation-folders/'+encodeURIComponent(f.id),undefined,{method:'DELETE'});await histories();}catch(e){toast(e.message);}},'text-button'));
        row.append(folderButton(f.id,f.name+' ('+f.count+')'),m);folders.append(row);
      }
      list.replaceChildren();
      for(const c of data.conversations){const row=element('div',undefined,'conversation-row'),open=button(c.title,async()=>{await openConversation(c.id);body.dataset.zone='discussion';refreshZones();},'conversation-link'),m=menu('Actions de '+c.title);
        open.setAttribute('aria-current',String(c.id===S.conversation));
        const move=element('select');move.setAttribute('aria-label','Dossier de '+c.title);move.append(new Option('Sans dossier',''));for(const f of folderItems)move.append(new Option(f.name,f.id));move.value=c.folder_id||'';
        move.onchange=async()=>{move.disabled=true;try{await api('/conversations/'+encodeURIComponent(c.id)+'/folder',{folder_id:move.value||null},{method:'PUT'});await histories();}catch(e){toast(e.message);move.disabled=false;}};
        m.append(button('Renommer',()=>edit('Renommer la conversation','Titre',c.title,async value=>{await api('/conversations/'+encodeURIComponent(c.id)+'/title',{title:value},{method:'PATCH'});if(S.conversation===c.id)$('chat-title').textContent=value;}),'text-button'),move,button('Supprimer',()=>deleteConversation(c),'text-button'));
        row.append(open,m);list.append(row);
      }
      if(!data.conversations.length)list.append(element('p',search.value?'Aucune conversation ne correspond à ces mots.':'Aucune conversation ici.','small muted'));
      previous.hidden=!offset;more.hidden=!data.has_more;folderState.textContent=degraded?'Classement indisponible. Vos conversations restent accessibles.':offset?'Conversations '+(offset+1)+' à '+(offset+data.conversations.length):'';
    }catch(e){if(own===generation)folderState.textContent=e.message+' Les conversations restent accessibles depuis leur adresse.';}
  };
  search.oninput=()=>{clearTimeout(timer);timer=setTimeout(()=>{offset=0;histories();},250);};
  function drawEvidence(){used.replaceChildren();for(const source of evidence.values())used.append(button(source.title,()=>readSource(source.id),'text-button'));if(!evidence.size)used.append(element('p','Les sources réellement consultées apparaîtront ici après une réponse.','small muted'));}
  function record(data){for(const s of data?.consulted_sources||[])if(typeof s.id==='string'&&typeof s.title==='string')evidence.set(s.id,s);drawEvidence();}
  document.addEventListener('survie:conversation',event=>{evidence.clear();for(const m of event.detail.messages||[])record(m.documentary);drawEvidence();body.dataset.zone='discussion';refreshZones();});
  document.addEventListener('survie:message',event=>record(event.detail.observed));
  for(const name of ['survie:translation-command','survie:summary-command'])document.addEventListener(name,()=>{if(S.view==='chat'){body.dataset.right='open';body.dataset.zone='documents';refreshZones();}});
  document.addEventListener('survie:job',()=>{for(const node of $('chat-messages').querySelectorAll('.documentary-sources button[data-source]'))evidence.set(node.dataset.source,{id:node.dataset.source,title:node.textContent});drawEvidence();});
  document.addEventListener('survie:source-choices',()=>{empty.hidden=!!selectedSourceChoices().length;});
  document.addEventListener('survie:new-conversation',()=>{evidence.clear();drawEvidence();$('chat-title').textContent='Nouvelle discussion';body.dataset.zone='discussion';refreshZones();});
  document.addEventListener('survie:auth',()=>{generation++;folder='all';offset=0;search.value='';if(editor.open)editor.close();evidence.clear();drawEvidence();histories();});
  drawEvidence();
  document.addEventListener('DOMContentLoaded',()=>{if(!S.conversation)$('chat-title').textContent='Nouvelle discussion';});
  const tasks=element('div',undefined,'assistant-tasks');
  for(const [label,action] of [
    ['Poser une question',()=>$('chat-input').focus()],
    ['Traduire un document',()=>{view('library');toast('Ouvrez le document à traduire dans la bibliothèque.');}],
    ['Faire une synthèse',()=>{if(!selectedSourceChoices().length){view('library');toast('Choisissez les documents à comparer, puis revenez à la discussion.');}else{body.dataset.right='open';body.dataset.zone='documents';refreshZones();$('summary-panel').open=true;}}],
    ['Comprendre ou apprendre',()=>{$('chat-input').value='Aide-moi à comprendre ce sujet avec une explication adaptée à mon niveau et des exercices : ';$('chat-input').focus();}]
  ])tasks.append(button(label,action,'secondary'));
  const emptyTemplate=()=>{const target=$('chat-messages').querySelector('.chat-empty');if(target&&!target.querySelector('.assistant-tasks')){target.querySelector('.question-examples')?.remove();target.querySelector('h2').textContent='Comment puis-je vous aider ?';target.append(tasks);}};
  emptyTemplate();document.addEventListener('survie:new-conversation',emptyTemplate);
})();
