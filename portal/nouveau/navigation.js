/* Functional UX adapter. Existing shared controls keep their API and data contracts. */
(() => {
  const sections={home:'accueil',library:'bibliotheque',chat:'assistant',maps:'cartes',monitor:'appareil',activity:'appareil',data:'appareil',storage:'appareil',settings:'appareil',users:'appareil',connect:'appareil'};
  const routes={accueil:['home',''],assistant:['chat',''],cartes:['maps',''],bibliotheque:['library','collections'],appareil:['monitor','ensemble']};
  const machine={ensemble:'monitor',activite:'activity',telechargements:'data',stockage:'storage',reglages:'settings',profils:'users',connexion:'connect'};
  const libraryTabs=['collections','recherche','parcours','favoris','traductions'];
  const namespace='survie-next-v1:',ttl=7*86400000;
  let current=null,applying=false,popping=false,scopeCommand=false,activityTimer=null,inventoryAt=0,historyReady=false,openingSource=false,skipSearch=false,lastActivity=null,activityRequest=null,pendingRestore=null;
  let profileId=null,draftKey=null,lastDraft='';
  const initialHash=location.hash,initialDocument=new URLSearchParams(location.search).get('document');
  const get=(name,fallback)=>{try{const record=JSON.parse(localStorage.getItem(namespace+S.user?.id+':'+name));if(record&&Date.now()-record.at<ttl)return record.value;}catch(_){}return fallback;};
  const put=(name,value)=>{if(!S.user)return;try{localStorage.setItem(namespace+S.user.id+':'+name,JSON.stringify({at:Date.now(),value}));}catch(_){}};
  const urlFor=(section,tab='',params=new URLSearchParams())=>'#/'+section+(tab?'/'+tab:'')+(params.size?'?'+params:'');
  function parse(hash){
    const [path,query='']=hash.replace(/^#\/?/,'').split('?'),[section,requested]=path.split('/');
    if(!Object.hasOwn(routes,section))return null;
    let [name,tab]=routes[section];
    if(section==='appareil'){tab=requested||get('machine-tab','ensemble');if(!Object.hasOwn(machine,tab))tab='ensemble';name=machine[tab];}
    if(section==='bibliotheque'){tab=requested||get('library-tab','collections');if(!libraryTabs.includes(tab))tab='collections';}
    return {section,name,tab,params:new URLSearchParams(query)};
  }
  function fromLegacy(name){
    if(name==='admin')name='settings';
    if(name==='library')return {section:'bibliotheque',name,tab:current?.section==='bibliotheque'&&!['collections','parcours'].includes(current.tab)?current.tab:'recherche',params:current?.section==='bibliotheque'?new URLSearchParams(current.params):new URLSearchParams()};
    if(name==='chat')return {section:'assistant',name,tab:'',params:new URLSearchParams(S.conversation?{conversation:S.conversation}:{})};
    const tab=Object.keys(machine).find(k=>machine[k]===name);
    return tab?{section:'appareil',name,tab,params:new URLSearchParams()}:parse('#/'+(sections[name]||'accueil'));
  }
  function remember(){
    if(!historyReady||!current)return;
    const state={...history.state,scroll:window.scrollY,focus:document.activeElement?.id||null};
    history.replaceState(state,'',location.href);
    put('last',urlFor(current.section,current.tab,current.params));
  }
  function saveDraft(){
    if(!S.user||profileId!==S.user.id||!draftKey)return;
    lastDraft=$('chat-input').value.slice(0,20000);put(draftKey,lastDraft);
  }
  function restoreDraft(){
    if(!S.user||S.loadingConversation)return;
    const target='draft:'+(S.conversation||'new');
    if(draftKey===target&&profileId===S.user.id)return;
    saveDraft();profileId=S.user.id;draftKey=target;
    const saved=get(draftKey,'');lastDraft=typeof saved==='string'?saved:'';$('chat-input').value=lastDraft;
  }
  function restorePosition(state){requestAnimationFrame(()=>{const target=state?.focus&&document.getElementById(state.focus);(target||$('main')).focus({preventScroll:true});window.scrollTo({top:state?.scroll||0,behavior:'instant'});});}
  const baseView=view,baseRead=readSource,baseOpen=openConversation,baseStatus=status,baseData=loadData,baseSearch=search,baseResume=resumeConversation;
  labels.maps='Cartes';labels.storage='Stockage';labels.activity='Activité';labels.data='Téléchargements';labels.monitor='Vue d’ensemble';labels.settings='Réglages';
  setMenu=()=>{document.body.classList.remove('nav-open');$('main-navigation').inert=false;document.querySelector('.workspace').inert=false;$('nav-overlay').hidden=true;$('menu-toggle').setAttribute('aria-expanded','false');};
  function fitNextChat(){if(current?.name!=='chat')return;const viewport=window.visualViewport;const height=viewport?.height||innerHeight;const top=$('view-chat').getBoundingClientRect().top-(viewport?.offsetTop||0);const nav=mobileNav.matches?$('main-navigation').getBoundingClientRect().height:0;document.documentElement.style.setProperty('--next-chat-height',Math.max(160,height-top-nav)+'px');}
  window.addEventListener('resize',fitNextChat,{passive:true});window.visualViewport?.addEventListener('resize',fitNextChat,{passive:true});
  function activate(route,restoring=false){
    if(!route)return;
    if(route.name==='maps'){saveDraft();remember();location.replace('/cartes.html?interface=nouveau');return;}
    if(['settings','users'].includes(route.name)&&S.user?.role!=='admin'){
      if(S.authReady){toast('Choisissez le profil Famille pour ouvrir ces réglages.');auth();}else S.requestedView=route.name;
      return;
    }
    const saved=history.state;
    if(restoring&&route.name==='library')pendingRestore={hash:urlFor(route.section,route.tab,route.params),state:saved};
    applying=true;current=route;
    baseView(route.name);
    history.replaceState(saved,'',urlFor(route.section,route.tab,route.params));
    applying=false;setMenu();
    document.title=(labels[route.name]||'SetupSurvie')+' · SetupSurvie';
    $('breadcrumb').textContent=route.section==='appareil'?'Mon appareil':labels[route.name];
    document.querySelectorAll('#navigation [data-route]').forEach(a=>{const active=a.dataset.route===route.section;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
    for(const a of document.querySelectorAll('.next-tabs [data-route]')){
      const active=a.dataset.route===route.section+'/'+route.tab||route.section==='appareil'&&['profils','connexion'].includes(route.tab)&&a.dataset.route==='appareil/reglages';
      if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');
    }
    if(route.section==='appareil'){
      document.querySelector('#view-'+route.name+' .page-heading').after($('next-machine-tabs'));put('machine-tab',route.tab);
      if(route.name==='storage')loadData();
    }
    if(route.name==='library'){
      put('library-tab',route.tab);
      $('next-collections').hidden=route.tab!=='collections';$('next-learning').hidden=route.tab!=='parcours';$('next-search').hidden=['collections','parcours'].includes(route.tab);
      if(route.tab==='collections'){const query=route.params.get('resource')??get('collection-query','');window.CollectionsFilter?.setQuery(query);if(query)route.params.set('resource',query);history.replaceState(saved,'',urlFor(route.section,route.tab,route.params));if(Date.now()-inventoryAt>60000)loadData();}
      if(!['collections','parcours'].includes(route.tab)){
        $('library-query').value=route.params.get('q')||'';$('search-language').value=route.params.get('lang')||'';
        const scope=route.tab==='favoris'?'favorites':route.tab==='traductions'?'translations':'all';
        scopeCommand=true;
        const control=document.querySelector(`[data-library-scope="${scope}"]`);
        if(!skipSearch&&control&&(scope!=='all'||route.params.has('q')))control.click();
        else document.dispatchEvent(new CustomEvent('survie:scope-reset'));
        scopeCommand=false;
        const source=route.params.get('source');
        if(source&&!openingSource&&S.reader!==source){openingSource=true;baseRead(source).finally(()=>{openingSource=false;if(restoring)restorePosition(saved);});}
        if(!source){$('reader').hidden=true;document.querySelector('.reading-layout').classList.remove('reading');}
      }
    }
    if(route.name==='chat'){
      restoreDraft();
      const id=route.params.get('conversation');
      if(S.user&&id&&S.conversation!==id&&!S.loadingConversation)openConversation(id);
    }
    for(const detail of document.querySelectorAll('#view-'+route.name+' details[id]')){const open=get('detail:'+detail.id,null);if(typeof open==='boolean')detail.open=open;}
    if(restoring)restorePosition(saved);
    else if(route.name!=='chat'){$('main').focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});}
    put('last',urlFor(route.section,route.tab,route.params));
    fitNextChat();pollActivity();
  }
  function navigate(route,replace=false){
    if(!route)return;
    if(!applying){saveDraft();remember();}
    const hash=urlFor(route.section,route.tab,route.params);
    if(!replace&&hash!==location.hash)history.pushState({scroll:0},'',hash);
    else if(replace)history.replaceState({...history.state},'',hash);
    activate(route,popping);
  }
  view=name=>{
    if(applying)return baseView(name);
    if(name.startsWith('/'))return activate(parse('#'+name)||parse('#/accueil'),true);
    navigate(fromLegacy(name));
  };
  search=q=>{
    const params=new URLSearchParams({q,lang:$('search-language').value});navigate({section:'bibliotheque',name:'library',tab:'recherche',params});
    // activate already executes the search through the shared scoped form.
  };
  readSource=async id=>{
    if(openingSource)return baseRead(id);
    const route=fromLegacy('library');route.params.set('q',$('library-query').value);route.params.set('lang',$('search-language').value);route.params.set('source',id);
    openingSource=true;navigate(route);
    try{await baseRead(id);}finally{openingSource=false;}
  };
  openConversation=async id=>{
    if(S.job&&S.conversation!==id){toast('Attendez la réponse ou annulez la demande avant de changer de conversation.');return;}
    saveDraft();
    const route=fromLegacy('chat');route.params.set('conversation',id);
    // Reserve the destination without recursively reopening it in activate.
    $('chat-input').readOnly=true;
    S.loadingConversation=true;navigate(route);S.loadingConversation=false;
    try{await baseOpen(id);restoreDraft();}finally{$('chat-input').readOnly=false;}
  };
  resumeConversation=()=>{
    const target=current?.name==='chat'&&current.params.get('conversation');
    if(target){if(S.user&&!S.loadingConversation&&S.conversation!==target)openConversation(target);return;}
    baseResume();
  };
  status=async()=>{await baseStatus();const grid=$('collections');if(!S.status?.books)return;grid.replaceChildren();for(const book of S.status.books){const a=element('a',undefined,'collection');a.href=localServiceURL('/content/'+encodeURIComponent(book.book)+'/','kiwix');a.target='_blank';a.rel='noopener';a.append(element('span','▤','book-icon'));const text=element('span');text.append(element('strong',book.title),element('small','Ouvrir cette collection →'));a.append(text);grid.append(a);}};
  loadData=async()=>{const user=S.user?.id;$('next-inventory-notice').textContent='Lecture des contenus installés…';await baseData();if(user!==S.user?.id)return;inventoryAt=Date.now();$('next-inventory-notice').textContent=$('data-summary').querySelector('.data-stat')?'Les collections marquées disponibles peuvent être ouvertes directement.':$('data-summary').textContent;};
  // Do not poll GPU/process state in an invisible browser tab.
  const baseInference=refreshInference;
  refreshInference=async()=>{if(document.hidden){clearTimeout(inferenceTimer);return;}await baseInference();};
  const phaseLabels={idle:'Aucune préparation suivie',starting:'Démarrage de la préparation',planning:'Recherche des collections',downloading:'Téléchargement en cours',verifying:'Vérification du fichier reçu',checking:'Vérification ou passage au fichier suivant',waiting_retry:'En attente d’une nouvelle tentative',pausing:'Pause demandée',paused:'Préparation en pause',interrupted:'Préparation interrompue',refreshing:'Mise à disposition des contenus',verified:'Tous les éléments du plan ont un reçu de vérification',completed:'Préparation terminée',planned:'Sélection prête',error:'Préparation à vérifier',unknown:'Suivi momentanément indisponible'};
  function renderActivity(data){
    const unknown=data.phase==='unknown';
    for(const block of document.querySelectorAll('.next-activity')){
      block.querySelector('.next-transfer-title').textContent=phaseLabels[data.phase]||'État de la préparation à vérifier';
      block.querySelector('.next-transfer-message').textContent=data.total_bytes?`${bytes(data.verified_bytes)} / ${bytes(data.total_bytes)} vérifiés d’après les reçus · ${data.verified_count} / ${data.total_count} éléments.`:unknown?'Le suivi ne répond pas. Cela ne signifie pas que le transfert est arrêté.':data.kind==='geography'?'Préparation des adresses, lieux et relief.':data.kind==='routing'?'Préparation des itinéraires.':'La consultation des documents ne lance aucune préparation.';
      const meter=block.querySelector('progress');meter.hidden=!data.total_bytes||unknown;if(data.total_bytes){meter.max=data.total_bytes;meter.value=data.verified_bytes;}
      const files=block.querySelector('.next-transfer-files');files.replaceChildren();
      for(const file of data.active||[]){const row=element('div',undefined,'next-file');row.append(element('strong',file.title),element('span',bytes(file.bytes)+' / '+bytes(file.total)+' · '+(file.phase==='verifying'?'Vérification':'Transfert'),'small muted'));files.append(row);}
      const stamp=data.observed_at?new Date(data.observed_at*1000).toLocaleTimeString('fr-FR'):'';
      block.querySelector('.next-transfer-time').textContent=(stamp?'Dernière observation : '+stamp+'. ':'')+(data.stale?'Progression ancienne ou non confirmée. ':'')+(data.pending_errors?data.pending_errors+' contenu(s) en attente. ':'')+(data.source==='windows'?'Transfert Windows indépendant · suivi en lecture seule.':'');
    }
  }
  async function pollActivity(){
    clearTimeout(activityTimer);
    if(document.hidden||!current||current.section!=='appareil')return;
    const profile=S.user?.id;
    try{if(!activityRequest)activityRequest=api('/activity').finally(()=>{activityRequest=null;});const data=await activityRequest;if(profile===S.user?.id){lastActivity=data;renderActivity(data);}}catch(_){renderActivity({phase:'unknown',stale:true});}
    if(current?.name==='monitor'){
      try{const health=await api('/health');$('next-service-health').textContent=health.degraded_features?.length?'Portail disponible ; certaines fonctions demandent une vérification : '+health.degraded_features.join(', ')+'.':'Le portail et ses fonctions déclarées répondent. L’état de la lecture des collections est indiqué dans la bibliothèque.';}
      catch(_){$('next-service-health').textContent='Le service du portail ne répond pas. Les liens de lecture et de secours restent accessibles selon les services disponibles.';}
    }
    clearTimeout(activityTimer);activityTimer=setTimeout(pollActivity,5000);
  }
  function decorateLinks(){
    document.querySelectorAll('a[href^="/pdf.html"]').forEach(a=>{const u=new URL(a.href);u.searchParams.set('interface','nouveau');a.href=u.href;});
    document.querySelectorAll('a[href^="/cartes.html"]').forEach(a=>{const u=new URL(a.href);u.searchParams.set('interface','nouveau');a.href=u.href;});
  }
  document.addEventListener('toggle',event=>{const node=event.target;if(node.tagName==='DETAILS'&&node.id&&!applying&&S.user)put('detail:'+node.id,node.open);},true);
  let frame=0;window.addEventListener('scroll',()=>{if(!frame)frame=requestAnimationFrame(()=>{frame=0;remember();});},{passive:true});
  $('chat-input').addEventListener('input',saveDraft);
  document.addEventListener('survie:collection-filter',event=>{const query=event.detail;put('collection-query',query);if(current?.tab==='collections'){if(query)current.params.set('resource',query);else current.params.delete('resource');history.replaceState(history.state,'',urlFor(current.section,current.tab,current.params));put('last',location.hash);}});
  // Capture the validated search before the shared handler clears/updates results.
  $('library-search').addEventListener('submit',()=>{if(applying||scopeCommand)return;const route=fromLegacy('library');route.params.delete('source');route.params.set('q',$('library-query').value);route.params.set('lang',$('search-language').value);skipSearch=true;navigate(route);skipSearch=false;},true);
  document.addEventListener('click',event=>{
    if(lastActivity?.source==='windows'&&lastActivity.worker_alive===true&&event.target.closest('#content-download,#routing-download')){event.preventDefault();event.stopImmediatePropagation();toast('Un transfert Windows est déjà actif. Ce suivi reste en lecture seule.');return;}
    if(event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
    if(event.target.closest('a.skip')){event.preventDefault();$('main').focus();return;}
    const routeLink=event.target.closest('[data-route]');
    if(routeLink){event.preventDefault();event.stopImmediatePropagation();navigate(parse('#/'+routeLink.dataset.route));return;}
    const scope=event.target.closest('[data-library-scope]');
    if(scope&&!scopeCommand){event.preventDefault();event.stopImmediatePropagation();const tab={all:'recherche',favorites:'favoris',translations:'traductions'}[scope.dataset.libraryScope];navigate(parse('#/bibliotheque/'+tab));}
  },true);
  document.addEventListener('submit',event=>{if(lastActivity?.source==='windows'&&lastActivity.worker_alive===true&&['content-form','geo-download-form'].includes(event.target.id)){event.preventDefault();event.stopImmediatePropagation();toast('Un transfert Windows est déjà actif. Attendez sa fin ou utilisez sa procédure de pause avant une autre préparation.');}},true);
  window.addEventListener('hashchange',event=>{event.stopImmediatePropagation();if(current&&location.hash===urlFor(current.section,current.tab,current.params))return;popping=true;activate(parse(location.hash)||fromLegacy(location.hash.slice(1)),true);popping=false;},true);
  window.addEventListener('popstate',()=>{
    saveDraft();popping=true;
    if(history.state?.dialog){const dialog=$(history.state.dialog);if(dialog&&!dialog.open)dialog.showModal();}
    else{for(const dialog of document.querySelectorAll('dialog[open]'))dialog.close();activate(parse(location.hash)||fromLegacy(location.hash.slice(1)),true);}
    popping=false;
  });
  // Dialog closure participates in Back/Forward, without recording typed values.
  for(const dialog of document.querySelectorAll('dialog')){
    new MutationObserver(()=>{
      if(popping)return;
      if(dialog.open&&history.state?.dialog!==dialog.id){remember();history.pushState({...history.state,dialog:dialog.id},'',location.href);}
      else if(!dialog.open&&history.state?.dialog===dialog.id)history.back();
    }).observe(dialog,{attributes:true,attributeFilter:['open']});
  }
  document.addEventListener('survie:source',()=>{decorateLinks();const back=$('reader').querySelector('.reader-actions button');if(back)back.onclick=()=>{const route=fromLegacy('library');route.params.delete('source');navigate(route);};});
  document.addEventListener('survie:results',()=>{decorateLinks();if(pendingRestore&&pendingRestore.hash===location.hash){restorePosition(pendingRestore.state);pendingRestore=null;}});
  document.addEventListener('survie:conversation',()=>{restoreDraft();if(current?.name==='chat'){const route=fromLegacy('chat');history.replaceState(history.state,'',urlFor(route.section,route.tab,route.params));current=route;}});
  document.addEventListener('survie:auth',()=>{
    if(!S.user)return;
    profileId=S.user.id;draftKey=null;
    const saved=!initialHash?get('last',''):'';
    const target=saved&&parse(saved)||current||parse('#/accueil');
    navigate(target,true);restoreDraft();
  });
  const baseNew=newConversation;
  newConversation=()=>{saveDraft();baseNew();restoreDraft();};
  $('new-chat').onclick=newConversation;$('chat-reset').onclick=newConversation;
  const baseSend=send;
  send=async event=>{const old='draft:'+(S.conversation||'new');saveDraft();await baseSend(event);if(!$('chat-input').value){put(old,'');draftKey='draft:'+(S.conversation||'new');put(draftKey,'');if(current?.name==='chat'){const route=fromLegacy('chat');history.replaceState(history.state,'',urlFor(route.section,route.tab,route.params));current=route;}}};
  $('chat-form').onsubmit=send;
  $('next-clear-memory').onclick=()=>{try{for(const k of Object.keys(localStorage))if(k.startsWith(namespace))localStorage.removeItem(k);}catch(_){}lastDraft='';draftKey=null;$('chat-input').value='';toast('Mémoire de navigation effacée. Les données du serveur sont conservées.');};
  window.addEventListener('pagehide',()=>{saveDraft();remember();});
  document.addEventListener('visibilitychange',()=>{if(document.hidden){saveDraft();remember();clearTimeout(activityTimer);clearTimeout(inferenceTimer);}else{refreshInference();pollActivity();}});
  history.scrollRestoration='manual';
  window.addEventListener('DOMContentLoaded',()=>{
    const requested=parse(initialHash)||fromLegacy(initialHash.slice(1)||'home');
    if(initialDocument){const chatIntent=initialHash==='#chat'||initialHash.startsWith('#/assistant');requested.name=chatIntent?'chat':'library';requested.section=chatIntent?'assistant':'bibliotheque';requested.tab=requested.name==='library'?'recherche':'';}
    historyReady=true;history.replaceState({...history.state,scroll:history.state?.scroll||0},'',urlFor(requested.section,requested.tab,requested.params));activate(requested,true);decorateLinks();
  });
  document.documentElement.style.setProperty('--next-banner-height','0px');
})();
