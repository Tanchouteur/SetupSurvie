/* Functional UX adapter. Existing shared controls keep their API and data contracts. */
(() => {
  const sections={'work-queue':'file',home:'accueil',library:'bibliotheque',chat:'assistant',maps:'cartes',monitor:'appareil',data:'appareil',storage:'appareil',settings:'appareil',users:'appareil',connect:'appareil'};
  const routes={file:['work-queue',''],accueil:['home',''],assistant:['chat',''],cartes:['maps',''],bibliotheque:['library','collections'],appareil:['monitor','ensemble']};
  const machine={ensemble:'monitor',telechargements:'data',stockage:'storage',reglages:'settings',profils:'users',connexion:'connect',acces:'settings',bibliotheque:'settings',assistant:'settings',entretien:'settings',tests:'settings',lieux:'settings',collections:'settings'};
  const libraryTabs=['collections','recherche','parcours','favoris','traductions'];
  const namespace='survie-next-v1:',ttl=7*86400000;
  let current=null,applying=false,popping=false,scopeCommand=false,activityTimer=null,inventoryAt=0,historyReady=false,openingSource=false,skipSearch=false,lastActivity=null,activityRequest=null,pendingRestore=null;
  let profileId=null,draftKey=null,lastDraft='',pendingAdminRoute=null;
  // Results live only in this tab's memory. Keep their actual nodes so buttons,
  // expanded passages and keyboard state survive navigation without a new request.
  const searches=new Map();let searchKey=null,searchProfile=null,searchActive=false;
  function keyFor(route){
    if(route.name!=='library'||['collections','parcours'].includes(route.tab))return null;
    const p=route.params;
    return JSON.stringify([S.user?.id||null,route.tab,p.get('q')||'',p.get('lang')||'',p.get('kind')||'all',p.get('domain')||get('domain','resilience'),p.get('collection')||'']);
  }
  function saveSearch(){
    if(searchKey===null||!searchActive)return;
    const results=$('search-results'),message=$('search-message');
    if(results.getAttribute('aria-busy')==='true'){$('search-stop')?.remove();message.textContent='Recherche interrompue lors du changement de recherche. Les résultats reçus sont conservés ; vous pouvez la relancer.';message.classList.add('search-warning');results.setAttribute('aria-busy','false');}
    S.searchAbort?.abort();
    searches.set(searchKey,{nodes:[...results.childNodes],message:message.textContent,warning:message.classList.contains('search-warning'),signature:results.dataset.signature||'',busy:results.getAttribute('aria-busy')||'false'});
    if(searches.size>10)searches.delete(searches.keys().next().value);
  }
  function switchSearch(key){
    if(key===searchKey)return searchActive;
    saveSearch();searchKey=key;
    const results=$('search-results'),message=$('search-message'),saved=searches.get(key);searchActive=!!saved;
    results.replaceChildren(...(saved?.nodes||[]));results.dataset.signature=saved?.signature||'';results.setAttribute('aria-busy',saved?.busy||'false');
    message.textContent=saved?.message||'';message.classList.toggle('search-warning',!!saved?.warning);
    if(saved)document.dispatchEvent(new CustomEvent('survie:favorites-refresh'));
    return !!saved;
  }
  const initialHash=location.hash,initialDocument=new URLSearchParams(location.search).get('document');
  const get=(name,fallback,maxAge=ttl)=>{try{const record=JSON.parse(localStorage.getItem(namespace+S.user?.id+':'+name));if(record&&Date.now()-record.at<maxAge)return record.value;}catch(_){}return fallback;};
  const put=(name,value)=>{if(!S.user)return;try{localStorage.setItem(namespace+S.user.id+':'+name,JSON.stringify({at:Date.now(),value}));}catch(_){}};
  const collectionDisclosure='.next-collection-section, .next-collection-group';
  const urlFor=(section,tab='',params=new URLSearchParams())=>'#/'+section+(tab?'/'+tab:'')+(params.size?'?'+params:'');
  function parse(hash){
    const [path,query='']=hash.replace(/^#\/?/,'').split('?'),[section,requested]=path.split('/');
    if(!Object.hasOwn(routes,section))return null;
    if (section === 'appareil' && requested === 'activite') {
      return {section:'file', name:'work-queue', tab:'', params:new URLSearchParams(query)};
    }
    let [name,tab]=routes[section];
    if(section==='appareil'){tab=requested||get('machine-tab','ensemble');if(!Object.hasOwn(machine,tab))tab='ensemble';name=machine[tab];}
    if(section==='bibliotheque'){tab=requested||get('library-tab','collections');if(!libraryTabs.includes(tab))tab='collections';}
    return {section,name,tab,params:new URLSearchParams(query)};
  }
  function fromLegacy(name){
    if(name==='admin')name='settings';
    if(name==='library')return {section:'bibliotheque',name,tab:current?.section==='bibliotheque'&&!['collections','parcours'].includes(current.tab)?current.tab:'recherche',params:current?.section==='bibliotheque'?new URLSearchParams(current.params):new URLSearchParams()};
    if(name==='chat')return {section:'assistant',name,tab:'',params:new URLSearchParams(S.conversation?{conversation:S.conversation}:{})};
    const tab=name==='settings'&&new URLSearchParams(location.search).has('lat')?'lieux':Object.keys(machine).find(k=>machine[k]===name);
    return tab?{section:'appareil',name,tab,params:new URLSearchParams()}:parse('#/'+(sections[name]||'accueil'));
  }
  // Per-tab memory for this browser tab: the first click on another tab returns
  // to its last screen; a click on the tab already shown resets it to its root.
  const tabMemory=new Map();let readerOrigin=null;
  const groupOf=route=>route.section==='file'?'appareil':route.section;
  const tabOf=route=>route.section==='bibliotheque'?'bibliotheque/'+route.tab:route.section==='file'?'file':route.section==='appareil'?(route.tab==='ensemble'?'appareil/ensemble':'appareil/reglages'):null;
  const copyRoute=route=>({...route,params:new URLSearchParams(route.params)});
  function memorize(){
    if(!current||current.name==='maps')return;
    const entry={route:copyRoute(current),scroll:window.scrollY,query:current.name==='library'?$('library-query').value:null};
    tabMemory.set(groupOf(current),entry);
    // A document opened from Collections, the home page or the assistant uses the
    // search route; it must not replace what the Rechercher tab shows.
    if(current.name==='library'&&current.params.has('source')&&readerOrigin!==current.tab)return;
    const tab=tabOf(current);if(tab)tabMemory.set(tab,entry);
  }
  function forget(key){
    // A main section forgets its sub-tabs too, so the whole section starts afresh.
    const section=Object.hasOwn(routes,key)&&key!=='file';
    for(const name of [...tabMemory.keys()])if(name===key||section&&(name.startsWith(key+'/')||key==='appareil'&&name==='file'))tabMemory.delete(name);
  }
  function resetTarget(key){
    if(key==='bibliotheque'||key==='bibliotheque/collections'){put('collection-query','');return parse('#/bibliotheque/collections');}
    if(key==='appareil')return parse('#/appareil/ensemble');
    // The assistant keeps its conversation: “Nouvelle conversation” stays explicit.
    if(key==='assistant')return fromLegacy('chat');
    return parse('#/'+key);
  }
  // Reset: forget after navigate(), which memorizes the screen being left.
  function openTab(link){
    const key=link.dataset.route,main=!!link.closest('#navigation');
    const active=current&&(main?groupOf(current)===key:tabOf(current)===key);
    if(active){navigate(resetTarget(key));forget(key);return;}
    const saved=tabMemory.get(key);
    if(!saved){navigate(parse('#/'+key));return;}
    const route=copyRoute(saved.route),hash=urlFor(route.section,route.tab,route.params),state={scroll:saved.scroll,focus:null};
    saveDraft();remember();
    if(hash!==location.hash)history.pushState(state,'',hash);else history.replaceState(state,'',hash);
    activate(route,true);
    if(saved.query!==null&&route.name==='library'&&current===route)$('library-query').value=saved.query;
  }
  function remember(){
    if(!historyReady||!current)return;
    memorize();
    const state={...history.state,scroll:window.scrollY,focus:document.activeElement?.id||null};
    if(history.state?.scroll!==state.scroll||history.state?.focus!==state.focus)history.replaceState(state,'',location.href);
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
  const baseView=view,baseRead=readSource,baseOpen=openConversation,baseData=loadData,baseSearch=search,baseResume=resumeConversation;
  labels['work-queue']='File d’attente';labels.maps='Cartes';labels.storage='Stockage';labels.data='Téléchargements';labels.monitor='Vue d’ensemble';labels.settings='Paramètres';
  setMenu=()=>{document.body.classList.remove('nav-open');$('main-navigation').inert=false;document.querySelector('.workspace').inert=false;$('nav-overlay').hidden=true;$('menu-toggle').setAttribute('aria-expanded','false');};
  function fitNextChat(){if(current?.name!=='chat')return;const viewport=window.visualViewport;const height=viewport?.height||innerHeight;const top=$('view-chat').getBoundingClientRect().top-(viewport?.offsetTop||0);const nav=mobileNav.matches?$('main-navigation').getBoundingClientRect().height:0;document.documentElement.style.setProperty('--next-chat-height',Math.max(160,height-top-nav)+'px');}
  window.addEventListener('resize',fitNextChat,{passive:true});window.visualViewport?.addEventListener('resize',fitNextChat,{passive:true});
  // WebKit may publish resize before the media-query change. Refit when the
  // mobile navigation actually changes so it cannot cover the composer.
  mobileNav.addEventListener('change',fitNextChat);new ResizeObserver(fitNextChat).observe($('main-navigation'));
  function activate(route,restoring=false){
    if(!route)return;
    if(route.name==='maps'){saveDraft();remember();location.replace('/cartes.html');return;}
    if(['settings','users'].includes(route.name)&&S.user?.role!=='admin'){
      if(S.authReady){toast('Choisissez le profil Famille pour ouvrir ces réglages.');if(!$('auth-dialog').open)auth();}else{pendingAdminRoute=route;S.requestedView=route.name;}
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
      const active=a.dataset.route===route.section+'/'+route.tab||a.dataset.route==='file'&&route.name==='work-queue'||route.section==='appareil'&&route.tab!=='ensemble'&&a.dataset.route==='appareil/reglages';
      if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');
    }
    if(route.name==='work-queue') document.querySelector('#view-work-queue .page-heading').after($('next-machine-tabs'));
    if(route.section==='appareil'){
      if(route.name==='settings')window.SettingsLayout.show(route.tab,route.params.get('test'));
      document.querySelector('#view-'+route.name+' .page-heading').after($('next-machine-tabs'));put('machine-tab',route.tab);
      if(route.name==='storage')loadData();
    }
    if(route.name==='library'){
      put('library-tab',route.tab);$('next-domain-controls').hidden=route.tab!=='recherche';$('next-domain-help').hidden=route.tab!=='recherche';
      $('next-collections').hidden=route.tab!=='collections';$('next-learning').hidden=route.tab!=='parcours';$('next-search').hidden=['collections','parcours'].includes(route.tab);
      if(route.tab==='collections'){const query=route.params.get('resource')??get('collection-query','');window.CollectionsFilter?.setView(query,route.params.get('rubrique'),(id,fallback)=>get('detail:'+id,fallback,Infinity));if(query)route.params.set('resource',query);history.replaceState(saved,'',urlFor(route.section,route.tab,route.params));if(Date.now()-inventoryAt>60000)loadData();}
      if(!['collections','parcours'].includes(route.tab)){
        if($('search-collection')?.options.length===1)loadData();
        if($('search-domain'))$('search-domain').value=route.params.get('domain')||get('domain','resilience');$('library-query').value=route.params.get('q')||'';$('search-language').value=route.params.get('lang')||'';if($('search-kind')){$('search-kind').value=['videos','documents'].includes(route.params.get('kind'))?route.params.get('kind'):'all';$('search-kind').fitKind?.();}if($('search-collection')){$('search-collection').dataset.requested=route.params.get('collection')||'';$('search-collection').value=route.params.get('collection')||'';}
        const scope=route.tab==='favoris'?'favorites':route.tab==='traductions'?'translations':'all';
        const cached=switchSearch(keyFor(route));
        document.dispatchEvent(new CustomEvent('survie:scope-set',{detail:scope}));
        scopeCommand=true;
        const control=document.querySelector(`[data-library-scope="${scope}"]`);
        // Both startup listeners activate the route before the profile response;
        // the auth event restores it once more. Search only after that response,
        // including its anonymous fallback, rather than sending three requests.
        if(S.authReady&&!skipSearch&&!cached&&control&&(scope!=='all'||route.params.has('q'))){if(!openingSource||!route.params.has('source')){searchActive=true;control.click();}}
        scopeCommand=false;
        const source=route.params.get('source');
        if(source&&S.authReady&&!openingSource&&(S.reader!==source||$('reader').hidden)){openingSource=true;baseRead(source).finally(()=>{openingSource=false;if(restoring)restorePosition(saved);});}
        if(!source){$('reader').hidden=true;document.querySelector('.reading-layout').classList.remove('reading');}
      }
    }
    if(route.name==='chat'){
      restoreDraft();
      const id=route.params.get('conversation');
      if(S.user&&id&&S.conversation!==id&&!S.loadingConversation)openConversation(id);
    }
    for(const detail of document.querySelectorAll('#view-'+route.name+' details[id]')){if(detail.matches(collectionDisclosure)||detail.dataset.filtering)continue;const open=get('detail:'+detail.id,null);if(typeof open==='boolean')detail.open=open;}
    if(route.section==='appareil'&&route.tab==='tests'&&['performance','search','memory','translation','offline'].includes(route.params.get('test')))document.getElementById('settings-test-'+route.params.get('test')).open=true;
    if(restoring)restorePosition(saved);
    else if(route.name!=='chat'){$('main').focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});}
    put('last',urlFor(route.section,route.tab,route.params));
    fitNextChat();pollActivity();
    document.dispatchEvent(new CustomEvent('survie:route',{detail:{section:route.section,tab:route.tab,params:Object.fromEntries(route.params)}}));
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
    readerOrigin=current?.name==='library'?current.tab:null;
    const route=fromLegacy('library');route.params.set('q',$('library-query').value);route.params.set('lang',$('search-language').value);route.params.set('kind',$('search-kind')?.value||'all');route.params.set('domain',$('search-domain')?.value||'resilience');if($('search-collection')?.value)route.params.set('collection',$('search-collection').value);else route.params.delete('collection');route.params.set('source',id);
    openingSource=true;navigate(route);
    try{await baseRead(id);}finally{openingSource=false;}
  };
  openConversation=async (id,options)=>{
    if(options?.silent)return baseOpen(id,options);
    if(S.sending){toast('La question est en cours d’envoi.');return;}
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
  loadData=async()=>{const user=S.user?.id;$('next-inventory-notice').textContent='Lecture des contenus installés…';await baseData();if(user!==S.user?.id)return;inventoryAt=Date.now();$('next-inventory-notice').textContent=$('data-summary').querySelector('.data-stat')?'Les collections marquées disponibles peuvent être ouvertes directement.':$('data-summary').textContent;};
  // Do not poll GPU/process state in an invisible browser tab.
  const baseInference=refreshInference;
  refreshInference=async()=>{if(document.hidden){clearTimeout(inferenceTimer);return;}await baseInference();};
  const phaseLabels={indexing:'Indexation des documents',index_preparation:'Préparation de l’outil de recherche',idle:'Aucune préparation suivie',starting:'Démarrage de la préparation',planning:'Recherche des collections',downloading:'Téléchargement en cours',verifying:'Vérification du fichier reçu',checking:'Vérification ou passage au fichier suivant',waiting_retry:'En attente d’une nouvelle tentative',pausing:'Pause demandée',paused:'Préparation en pause',interrupted:'Préparation interrompue',refreshing:'Mise à disposition des contenus',verified:'Tous les éléments du plan ont un reçu de vérification',completed:'Préparation terminée',planned:'Sélection prête',error:'Préparation à vérifier',unknown:'Suivi momentanément indisponible'};
  function renderActivity(data){
    const unknown=data.phase==='unknown';
    for(const block of document.querySelectorAll('.next-activity')){
      block.querySelector('.next-transfer-title').textContent=phaseLabels[data.phase]||'État de la préparation à vérifier';
      block.querySelector('.next-transfer-message').textContent=data.total_bytes?`${bytes(data.verified_bytes)} / ${bytes(data.total_bytes)} vérifiés d’après les reçus · ${data.verified_count} / ${data.total_count} éléments.`:unknown?'Le suivi ne répond pas. Cela ne signifie pas que le transfert est arrêté.':data.kind==='index'?`${data.index_progress?.completed||0} / ${data.index_progress?.archives||0} archives examinées · ${data.index_progress?.articles||0} articles indexés.`:data.kind==='youtube-download'?`${data.index_progress?.downloaded||0} ajoutée(s), ${data.index_progress?.skipped||0} déjà présente(s), ${data.index_progress?.errors||0} en erreur sur ${data.index_progress?.videos||0} vidéo(s) YouTube.`:data.kind==='video-inventory'?'Examen des vidéos contenues dans les collections, sans IA.':data.kind==='index-prepare'?'Préparation de l’outil, sans modèle IA.':data.kind==='geography'?'Préparation des adresses, lieux et relief.':data.kind==='routing'?'Préparation des itinéraires.':'La consultation des documents ne lance aucune préparation.';
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
  document.addEventListener('survie:favorites-changed',()=>{for(const key of searches.keys())if(JSON.parse(key)[1]==='favoris')searches.delete(key);});
  document.addEventListener('toggle',event=>{const node=event.target;if(node.tagName==='DETAILS'&&node.id&&!node.matches(collectionDisclosure)&&!applying&&S.user&&!node.dataset.filtering)put('detail:'+node.id,node.open);},true);
  $('next-collections').addEventListener('click',event=>{
    const summary=event.target.closest('summary'),detail=summary?.parentElement;
    if(event.defaultPrevented||!detail?.matches(collectionDisclosure))return;
    const open=!detail.open;
    if(detail.dataset.filtering)detail.dataset.previousOpen=String(open);
    put('detail:'+detail.id,open);
  });
  let scrollTimer=0;window.addEventListener('scroll',()=>{if(!scrollTimer)scrollTimer=setTimeout(()=>{scrollTimer=0;remember();},250);},{passive:true});
  $('chat-input').addEventListener('input',saveDraft);
  document.addEventListener('survie:collection-filter',event=>{const query=event.detail;put('collection-query',query);if(current?.tab==='collections'){if(query)current.params.set('resource',query);else current.params.delete('resource');history.replaceState(history.state,'',urlFor(current.section,current.tab,current.params));put('last',location.hash);}});
  // Capture the validated search before the shared handler clears/updates results.
  $('chat-domain').addEventListener('change',()=>put('chat-domain',$('chat-domain').value));
  $('search-domain').addEventListener('change',()=>{put('domain',$('search-domain').value);const route=fromLegacy('library');route.params.set('domain',$('search-domain').value);if($('library-query').value)route.params.set('q',$('library-query').value);navigate(route);});
  $('search-kind')?.addEventListener('change',()=>{const route=fromLegacy('library');route.params.delete('source');route.params.set('kind',$('search-kind').value);route.params.set('q',$('library-query').value);if(!$('library-query').value&&$('search-kind').value!=='videos')route.params.delete('q');navigate(route);});
  $('library-search').addEventListener('submit',()=>{if(applying||scopeCommand)return;const route=fromLegacy('library');route.params.delete('source');route.params.set('q',$('library-query').value);route.params.set('lang',$('search-language').value);route.params.set('kind',$('search-kind')?.value||'all');route.params.set('domain',$('search-domain')?.value||'resilience');if($('search-collection')?.value)route.params.set('collection',$('search-collection').value);else route.params.delete('collection');skipSearch=true;navigate(route);skipSearch=false;searchActive=true;},true);
  document.addEventListener('click',event=>{
    if(lastActivity?.source==='windows'&&lastActivity.worker_alive===true&&event.target.closest('#organizer-reference-apply,.organizer-reference-row button,#routing-download')){event.preventDefault();event.stopImmediatePropagation();toast('Un transfert Windows est déjà actif. Ce suivi reste en lecture seule.');return;}
    if(event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
    if(event.target.closest('a.skip')){event.preventDefault();$('main').focus();return;}
    const routeLink=event.target.closest('[data-route]');
    if(routeLink){
      event.preventDefault();event.stopImmediatePropagation();
      const type=routeLink.dataset.collectionType;
      if(type){
        const detail=$('collection-section-'+type);
        detail.open=true;put('detail:'+detail.id,true);
      }
      if(!type&&routeLink.closest('#navigation, .next-tabs')){openTab(routeLink);return;}
      navigate(parse('#/'+routeLink.dataset.route));return;
    }
    const scope=event.target.closest('[data-library-scope]');
    if(scope&&!scopeCommand){event.preventDefault();event.stopImmediatePropagation();const tab={all:'recherche',favorites:'favoris',translations:'traductions'}[scope.dataset.libraryScope];navigate(parse('#/bibliotheque/'+tab));}
  },true);
  document.addEventListener('submit',event=>{if(lastActivity?.source==='windows'&&lastActivity.worker_alive===true&&event.target.id==='geo-download-form'){event.preventDefault();event.stopImmediatePropagation();toast('Un transfert Windows est déjà actif. Attendez sa fin ou utilisez sa procédure de pause avant une autre préparation.');}},true);
  window.addEventListener('hashchange',event=>{event.stopImmediatePropagation();if(current&&location.hash===urlFor(current.section,current.tab,current.params))return;popping=true;activate(parse(location.hash)||fromLegacy(location.hash.slice(1)),true);popping=false;},true);
  window.addEventListener('popstate',()=>{
    saveDraft();popping=true;
    if(history.state?.dialog){const dialog=$(history.state.dialog);if(dialog&&!dialog.open)dialog.showModal();}
    else{for(const dialog of document.querySelectorAll('dialog[open]'))dialog.close();activate(parse(location.hash)||fromLegacy(location.hash.slice(1)),true);}
    popping=false;
  });
  // Dialog closure participates in Back/Forward, without recording typed values.
  const observedDialogs=new WeakSet();
  function observeDialog(dialog){
    if(observedDialogs.has(dialog))return;observedDialogs.add(dialog);
    new MutationObserver(()=>{
      if(popping)return;
      if(dialog.open&&history.state?.dialog!==dialog.id){remember();history.pushState({...history.state,dialog:dialog.id},'',location.href);}
      else if(!dialog.open&&history.state?.dialog===dialog.id)history.back();
    }).observe(dialog,{attributes:true,attributeFilter:['open']});
  }
  for(const dialog of document.querySelectorAll('dialog'))observeDialog(dialog);
  document.addEventListener('survie:dialog',event=>{if(event.detail instanceof HTMLDialogElement)observeDialog(event.detail);});
  document.addEventListener('survie:source',()=>{const back=$('reader').querySelector('.reader-actions button');if(back)back.onclick=()=>{const route=fromLegacy('library');route.params.delete('source');navigate(route);};});
  document.addEventListener('survie:results',()=>{if(pendingRestore&&pendingRestore.hash===location.hash){restorePosition(pendingRestore.state);pendingRestore=null;}});
  document.addEventListener('survie:conversation',()=>{restoreDraft();if(current?.name==='chat'){const route=fromLegacy('chat');history.replaceState(history.state,'',urlFor(route.section,route.tab,route.params));current=route;}});
  document.addEventListener('survie:auth',()=>{
    const nextProfile=S.user?.id||null;
    if(searchProfile!==nextProfile){tabMemory.clear();S.searchAbort?.abort();$('search-stop')?.remove();searches.clear();searchKey=null;searchActive=false;searchProfile=nextProfile;$('search-results').replaceChildren();$('search-results').dataset.signature='';$('search-message').textContent='';S.reader=null;$('reader').hidden=true;$('reader').replaceChildren();document.querySelector('.reading-layout').classList.remove('reading');}
    if(!S.user){if(S.authReady&&current?.name==='library')activate(current,true);return;}
    profileId=S.user.id;draftKey=null;$('chat-domain').value=get('chat-domain','resilience');
    const saved=!initialHash?get('last',''):'';
    const target=pendingAdminRoute||saved&&parse(saved)||current||parse('#/accueil');
    if(pendingAdminRoute){pendingAdminRoute=null;S.requestedView=null;if(S.user.role==='admin'&&$('auth-dialog').open)$('auth-dialog').close();}
    navigate(target,true);restoreDraft();
  });
  const baseNew=newConversation;
  newConversation=()=>{saveDraft();baseNew();restoreDraft();};
  $('new-chat').onclick=newConversation;$('chat-reset').onclick=newConversation;
  const baseSend=send;
  send=async event=>{const old='draft:'+(S.conversation||'new');saveDraft();await baseSend(event);if(!$('chat-input').value){put(old,'');draftKey='draft:'+(S.conversation||'new');put(draftKey,'');if(current?.name==='chat'){const route=fromLegacy('chat');history.replaceState(history.state,'',urlFor(route.section,route.tab,route.params));current=route;}}};
  $('chat-form').onsubmit=send;
  $('next-clear-memory').onclick=()=>{if(!confirm('Effacer les rubriques, filtres et brouillons de ce navigateur ? Les conversations et favoris du serveur seront conservés.'))return;try{for(const k of Object.keys(localStorage))if(k.startsWith(namespace))localStorage.removeItem(k);}catch(_){}lastDraft='';draftKey=null;$('chat-input').value='';toast('Mémoire de navigation effacée. Les données du serveur sont conservées.');};
  window.addEventListener('pagehide',()=>{saveDraft();remember();});
  document.addEventListener('visibilitychange',()=>{if(document.hidden){saveDraft();remember();clearTimeout(activityTimer);clearTimeout(inferenceTimer);}else{refreshInference();pollActivity();}});
  history.scrollRestoration='manual';
  window.addEventListener('DOMContentLoaded',()=>{
    const requested=parse(initialHash)||fromLegacy(initialHash.slice(1)||'home');
    if(initialDocument){const chatIntent=initialHash==='#chat'||initialHash.startsWith('#/assistant');requested.name=chatIntent?'chat':'library';requested.section=chatIntent?'assistant':'bibliotheque';requested.tab=requested.name==='library'?'recherche':'';}
    // A modal is not restored by a document reload. Do not keep its stale history marker.
    const {dialog:previousDialog,...initialState}=history.state||{};
    historyReady=true;history.replaceState({...initialState,scroll:initialState.scroll||0},'',urlFor(requested.section,requested.tab,requested.params));activate(requested,true);
  });
  document.documentElement.style.setProperty('--next-banner-height','0px');
})();
