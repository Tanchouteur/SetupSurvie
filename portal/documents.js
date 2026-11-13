/* Optional document features. A failure here must leave the core portal usable. */
(() => {
  const D={scope:'all',favorites:new Set(),entries:[],conversation:null,timer:null,intent:false};
  const base=id=>String(id||'').startsWith('guide:')?id.split('#page=')[0]:id;
  const pdf=source=>base(source.id).toLowerCase().endsWith('.pdf');
  const pdfURL=source=>'/pdf.html?id='+encodeURIComponent(source.id);
  const notice=message=>{const node=$('document-feature-status');if(node)node.textContent=message;};
  const guard=fn=>async event=>{try{await fn(event);}catch(error){notice(error.message||'Fonction documentaire indisponible ; la recherche habituelle reste accessible.');}};
  async function request(path,body,options={}){
    const controller=new AbortController();let timedOut=false;
    const cancel=()=>controller.abort();options.signal?.addEventListener('abort',cancel,{once:true});if(options.signal?.aborted)cancel();
    const timer=setTimeout(()=>{timedOut=true;controller.abort();},15000);
    try{return await api(path,body,{...options,signal:controller.signal});}
    catch(error){if(timedOut)throw Error('Cette fonction ne répond pas assez vite. Vous pouvez réessayer ; les autres fonctions restent disponibles.');throw error;}
    finally{clearTimeout(timer);options.signal?.removeEventListener('abort',cancel);}
  }
  function link(text,href){const a=element('a',text,'secondary-link');a.href=href;a.target='_blank';a.rel='noopener';return a;}
  function updateStars(){
    for(const star of document.querySelectorAll('[data-favorite-id]')){
      const active=D.favorites.has(star.dataset.favoriteId);
      star.textContent=active?'★ Retirer des favoris':'☆ Ajouter aux favoris';star.setAttribute('aria-pressed',String(active));
    }
  }
  async function refreshFavorites(){
    D.favorites.clear();
    if(S.user){const user=S.user.id;const data=await request('/favorites');if(S.user?.id!==user)return;D.favorites=new Set(data.results.map(r=>base(r.id)));}
    updateStars();
  }
  function favoriteButton(source){
    const star=button('',guard(async()=>{
      if(!needUser())return;
      star.disabled=true;
      try{
        const id=base(source.id),active=D.favorites.has(id),user=S.user.id;
        if(active){await request('/favorites?source_id='+encodeURIComponent(id),undefined,{method:'DELETE'});if(S.user?.id!==user)return;D.favorites.delete(id);}
        else{await request('/favorites',{source_id:id},{method:'PUT'});if(S.user?.id!==user)return;D.favorites.add(id);}
        updateStars();if(D.scope==='favorites')await scopedSearch();
      }finally{star.disabled=false;}
    }),'favorite-toggle secondary');
    star.dataset.favoriteId=base(source.id);return star;
  }
  function decorateResults(event){
    const records=new Map(event.detail.map(r=>[r.id,r]));
    for(const card of document.querySelectorAll('.result')){
      if(card.dataset.documentEnhanced)continue;
      const source=records.get(card.dataset.source);if(!source)continue;
      card.dataset.documentEnhanced='true';
      if(pdf(source)){
        const old=card.querySelector('button');
        if(old){old.textContent='Texte et assistant';old.className='text-button';old.before(link('Lire le PDF →',pdfURL(source)));}
      }
      if(source.is_ai_translation)card.append(element('p','Traduction IA non vérifiée · consulter aussi l’original.','translation-label small'));
      card.append(favoriteButton(source));
    }
    updateStars();
  }
  function decorateSource(event){
    const source=event.detail,reader=$('reader'),actions=reader.querySelector('.reader-actions');if(!actions)return;
    actions.append(favoriteButton(source));updateStars();
    const original=actions.querySelector('a');
    if(pdf(source)&&original){
      original.textContent='Lire le PDF en pleine page →';original.href=pdfURL(source);
      actions.append(link('Ouvrir directement l’original','/api/original?id='+encodeURIComponent(base(source.id))));
    }
    if(source.is_ai_translation){
      reader.prepend(element('p',source.translation_notice||'Traduction IA non vérifiée.','translation-label'));
      if(source.original_id)actions.append(button('Consulter l’original',()=>readSource(source.original_id),'secondary'));
      if(original)original.textContent='Lire la traduction mise en page →';
    }
  }
  function setScope(scope){
    D.scope=scope;$('library-query').required=scope==='all';
    for(const node of document.querySelectorAll('[data-library-scope]'))node.setAttribute('aria-pressed',String(node.dataset.libraryScope===scope));
  }
  async function scopedSearch(event){
    event?.preventDefault();
    if(D.scope==='all'){await runSearch();return;}
    if(D.scope==='favorites'&&!needUser())return;
    const q=$('library-query').value.trim(),language=$('search-language').value;
    S.searchAbort?.abort();const controller=new AbortController();S.searchAbort=controller;
    $('reader').hidden=true;document.querySelector('.reading-layout').classList.remove('reading');
    $('search-message').textContent='Recherche dans '+(D.scope==='favorites'?'vos favoris…':'les traductions partagées…');
    const path=q?'/search?q='+encodeURIComponent(q)+'&language='+encodeURIComponent(language)+(D.scope==='favorites'?'&favorites_only=true':'&translations_only=true'):
      D.scope==='favorites'?'/favorites?language='+encodeURIComponent(language):'/library/translations';
    try{
      const data=await request(path,undefined,{signal:controller.signal});if(controller.signal.aborted)return;
      const results=data.results.filter(r=>!language||r.language===language||r.language===({fr:'fra',en:'eng'}[language]));
      $('search-results').replaceChildren();renderLibraryResults(results);
      $('search-message').textContent=results.length+' résultat(s)'+(q?' pour « '+q+' »':'')+(D.scope==='translations'&&!q?' · traductions récentes ; recherchez un mot pour trouver les autres.':'.');
      if(!results.length)$('search-results').append(element('p',D.scope==='favorites'?'Aucun favori trouvé. Ajoutez une étoile à un document, ou essayez un autre mot.':'Aucune traduction partagée trouvée. Les nouvelles traductions terminées apparaîtront ici.','empty-panel'));
    }catch(error){if(error.name!=='AbortError'){$('search-message').textContent=error.message;throw error;}}
  }
  function translationChoices(){
    let label=$('translation-choice-label');
    if(!label){label=element('label','Traductions de cette conversation');label.id='translation-choice-label';const select=element('select');select.id='translation-choice';label.append(select);$('translation-publication').before(label);
      select.onchange=guard(async()=>{if(select.value){await loadTranslation(select.value,0);$('translation-panel').open=true;}else{clearTranslation();showAssociatedSource();$('translation-panel').open=true;}});}
    const select=$('translation-choice');select.replaceChildren();const fresh=element('option','Nouvelle traduction du document associé');fresh.value='';select.append(fresh);
    for(const item of D.entries){const option=element('option',item.title+' · '+item.status+' · '+item.mode);option.value=item.id;select.append(option);}
    select.value=S.translation||'';label.hidden=D.entries.length===0;
  }
  async function publicationStatus(event){
    const data=event.detail,node=$('translation-publication');if(!node)return;
    clearTimeout(D.timer);node.replaceChildren();
    if(D.conversation!==S.conversation){D.entries=[];D.conversation=S.conversation;}
    const previous=D.entries.find(t=>t.id===data.id);if(previous)Object.assign(previous,data);else D.entries.unshift(data);
    translationChoices();
    const publication=data.publication||{};
    if(publication.source_id){
      node.append(element('p','Cette traduction est dans les documents locaux, accessible à tout le monde.'),button('Lire le document partagé',()=>readSource(publication.source_id),'secondary'),favoriteButton({id:publication.source_id}));updateStars();
    }else if(data.status==='completed'){
      const publishing=publication.automatic&&!publication.error;
      node.append(element('p',publication.error||(publishing?'Traduction terminée. Ajout aux documents locaux en cours…':'Cette ancienne traduction reste privée tant que vous ne l’ajoutez pas aux documents locaux.')));
      if(!publishing){node.append(button('Ajouter aux documents locaux · visible par tous',guard(async event=>{const b=event.target,conversation=S.conversation,user=S.user?.id;b.disabled=true;try{await request('/translations/'+encodeURIComponent(data.id)+'/publish',{});if(S.conversation===conversation&&S.user?.id===user&&S.translation===data.id)await loadTranslation(data.id,0);}finally{b.disabled=false;}}),'secondary'));}
      else if(S.view==='chat')D.timer=setTimeout(()=>{if(S.translation===data.id&&S.view==='chat')loadTranslation(data.id,S.translationOffset);},1500);
    }
  }
  async function intent(){
    if(D.intent)return;const id=new URLSearchParams(location.search).get('document');if(!id)return;
    const chat=location.hash==='#chat'||location.hash.startsWith('#/assistant');if(chat&&!S.user){if(S.authReady)auth();return;}
    D.intent=true;
    try{
      if(chat){const source=await request('/source?id='+encodeURIComponent(id));askSource(source);history.replaceState(null,'',location.pathname+(location.pathname.startsWith('/nouveau/')?'#/assistant':'#chat'));}
      else await readSource(id);
    }catch(error){D.intent=false;throw error;}
  }
  try{
    for(const node of document.querySelectorAll('[data-library-scope]'))node.onclick=guard(async()=>{if(node.dataset.libraryScope==='favorites'&&!needUser())return;setScope(node.dataset.libraryScope);await scopedSearch();});
    $('library-search').onsubmit=guard(scopedSearch);
    document.addEventListener('survie:scope-reset',()=>setScope('all'));
    document.addEventListener('survie:results',guard(decorateResults));
    document.addEventListener('survie:source',guard(decorateSource));
    document.addEventListener('survie:auth',guard(refreshFavorites));
    document.addEventListener('survie:auth',()=>setTimeout(guard(intent),0));
    document.addEventListener('survie:conversation',guard(event=>{D.entries=event.detail.translation_items||[];D.conversation=S.conversation;translationChoices();}));
    document.addEventListener('survie:translation',guard(publicationStatus));
    document.addEventListener('survie:translation-clear',()=>{clearTimeout(D.timer);$('translation-publication')?.replaceChildren();if(!S.conversation||S.conversation!==D.conversation){D.entries=[];D.conversation=S.conversation;}translationChoices();});
    window.addEventListener('DOMContentLoaded',guard(intent));
    $('document-filters').hidden=false;
  }catch(error){notice('Favoris et lecteur enrichi indisponibles. La recherche habituelle reste disponible.');}
})();
