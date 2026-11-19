/* All data and actions use the local server. No external assets or browser-stored tokens. */
const $=id=>document.getElementById(id);
const S={view:'home',user:null,conversation:null,source:null,sources:[],sourceChanging:false,sending:false,job:null,poll:null,status:null,searchAbort:null,translation:null,translationOffset:0};
const EMPTY=$('chat-messages').innerHTML;
let contentTimer=null,contentState=null,contentInitialized=false,contentCommandBusy=false;
const labels={home:'Votre espace',library:'Bibliothèque',chat:'Assistant',data:'Données locales',settings:'Paramètres',connect:'Connecter un appareil',monitor:'État de l’appareil',users:'Profils locaux'};
function element(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function reportFilename(kind,report={}){
  const safe=value=>String(value).replace(/[^a-zA-Z0-9._-]+/g,'-').slice(0,80);
  const raw=report.created??report.started??report.updated;
  let date=new Date(typeof raw==='number'?raw*1000:raw);
  if(!Number.isFinite(date.getTime()))date=new Date();
  const pad=value=>String(value).padStart(2,'0');
  const stamp=date.getFullYear()+'-'+pad(date.getMonth()+1)+'-'+pad(date.getDate())+'_'+pad(date.getHours())+'h'+pad(date.getMinutes())+'m'+pad(date.getSeconds())+'s';
  return 'setupsurvie-'+safe(kind)+'-v'+safe(report.version||S.status?.version||'inconnue')+'-'+stamp+'.json';
}
function downloadReport(report,kind){
  const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})),link=element('a');
  link.href=url;link.download=reportFilename(kind,report);link.hidden=true;
  // Content outside showModal() is inert. Keep Safari's download action in
  // the same active dialog as the export button, including after a reload.
  const host=document.activeElement?.closest('dialog[open]')||[...document.querySelectorAll('dialog[open]')].at(-1)||document.body;
  host.append(link);link.click();
  // Keep the attached link and Blob alive while Safari starts its download.
  setTimeout(()=>{link.remove();URL.revokeObjectURL(url);},30000);
}
const mobileNav=matchMedia('(max-width:760px)');
function fitChatViewport(){
  const height=window.visualViewport?.height||window.innerHeight;
  document.documentElement.style.setProperty('--chat-viewport-height',height+'px');
}
window.visualViewport?.addEventListener('resize',fitChatViewport,{passive:true});
window.addEventListener('resize',fitChatViewport,{passive:true});fitChatViewport();
function setMenu(open,restore=true){open=!!open&&mobileNav.matches;document.body.classList.toggle('nav-open',open);document.querySelector('.workspace').inert=open;$('menu-toggle').setAttribute('aria-expanded',String(open));$('nav-overlay').hidden=!open;$('main-navigation').inert=mobileNav.matches&&!open;if(open)$('menu-close').focus();else if(restore&&mobileNav.matches)$('menu-toggle').focus();}
// Only conversation identifiers and reading positions are stored on this browser, per account.
function readingState(){try{return JSON.parse(localStorage.getItem('survie-reading:'+S.user.id))||{};}catch(_){return {};}}
function writeReading(state){if(S.user)try{localStorage.setItem('survie-reading:'+S.user.id,JSON.stringify(state));}catch(_){}}
function rememberReading(){
  if(!S.user||!S.conversation||S.view!=='chat'||S.loadingConversation)return;
  const state=readingState(),box=$('chat-messages');state.selected=S.conversation;state.positions=state.positions||{};
  state.positions[S.conversation]={top:box.scrollTop,page:window.scrollY,bottom:box.scrollHeight-box.clientHeight-box.scrollTop<24};
  const ids=Object.keys(state.positions);for(const id of ids.slice(0,Math.max(0,ids.length-100)))delete state.positions[id];writeReading(state);
}
function selectReading(id){const state=readingState();state.selected=id;writeReading(state);}
function restoreReading(id){
  const position=readingState().positions?.[id],box=$('chat-messages');
  const legacyPage=mobileNav.matches&&(position?.page||0)>0;
  box.scrollTop=legacyPage?position.page:position?(position.bottom?box.scrollHeight:position.top):box.scrollHeight;
  if(mobileNav.matches)window.scrollTo({top:0,behavior:'instant'});
}
function resumeConversation(){if(S.user&&S.view==='chat'&&!S.conversation&&!S.loadingConversation&&!new URLSearchParams(location.search).has('document')){const id=readingState().selected;if(id)openConversation(id);}}
$('chat-messages').addEventListener('scroll',rememberReading,{passive:true});
window.addEventListener('scroll',()=>{if(mobileNav.matches)rememberReading();},{passive:true});
window.addEventListener('pagehide',rememberReading);
document.addEventListener('visibilitychange',()=>{if(document.hidden)rememberReading();});
function reloadProfile(){if(S.profileReloading)return;S.profileReloading=true;location.reload();}
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,6500);}
const PAGE_REQUESTS=new Set();
let PAGE_CLOSING=false;
function closePageRequests(){PAGE_CLOSING=true;for(const controller of PAGE_REQUESTS)controller.abort();}
window.addEventListener('beforeunload',closePageRequests);
window.addEventListener('pagehide',closePageRequests);
window.addEventListener('pageshow',()=>{PAGE_CLOSING=false;});
async function api(path,body,options={}){
  if(PAGE_CLOSING)throw new DOMException('La page est en cours de fermeture.','AbortError');
  const {onResult,...requestOptions}=options,controller=new AbortController(),external=requestOptions.signal,relay=()=>controller.abort();
  if(external?.aborted)relay();else external?.addEventListener('abort',relay,{once:true});
  PAGE_REQUESTS.add(controller);
  try{
  const config={credentials:'same-origin',...requestOptions,signal:controller.signal};if(S.user)config.headers={...config.headers,'X-Survie-Profile':S.user.id};
  if(body!==undefined){config.method=options.method||'POST';config.body=body instanceof FormData?body:JSON.stringify(body);if(!(body instanceof FormData))config.headers={...config.headers,'Content-Type':'application/json'};}
  const r=await fetch('/api'+path,config);let data;
  if(r.ok&&onResult&&r.headers.get('Content-Type')?.includes('text/event-stream')){
    const reader=r.body.getReader(),decoder=new TextDecoder();let buffer='',final=null;
    try{
      while(true){const part=await reader.read();buffer+=decoder.decode(part.value||new Uint8Array(),{stream:!part.done});if(buffer.length>2_000_000)throw Error('Réponse documentaire trop volumineuse.');
        let newline;while((newline=buffer.indexOf('\n'))>=0){const line=buffer.slice(0,newline).trimEnd();buffer=buffer.slice(newline+1);if(!line.startsWith('data: '))continue;
          const value=JSON.parse(line.slice(6));if(value.state==='error')throw Error(value.message||'La recherche a été interrompue.');
          if(Array.isArray(value.results)){onResult(value);if(value.state==='done')final=value;}
        }
        if(part.done)break;
      }
      if(!final)throw Error('La recherche a été interrompue. Les résultats reçus sont conservés.');return final;
    }finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
  }
  try{data=await r.json();}catch(_){throw new Error('Le service ne répond pas. Réessayez dans quelques instants.');}
  if(!r.ok){if(r.headers.get('X-Survie-Profile-Changed')){reloadProfile();throw Error('Le profil a changé dans un autre onglet. Actualisation…');}if(r.status===401){S.user=null;accountUI();}const error=new Error(typeof data.detail==='string'?data.detail:'Vérifiez les informations saisies.');error.status=r.status;throw error;}
  if(r.status===202 || config.method==='POST' && path.startsWith('/admin/library/index/')) {
    document.dispatchEvent(new Event('survie:work-accepted'));
  }
  return data;
  }catch(error){if(controller.signal.aborted)throw new DOMException('La requête a été annulée.','AbortError');throw error;}
  finally{PAGE_REQUESTS.delete(controller);external?.removeEventListener('abort',relay);}
}
function button(text,action,cls='secondary'){const b=element('button',text,cls);b.type='button';b.addEventListener('click',action);return b;}
function view(name){
  if(name==='admin')name='settings';
  if(!(name in labels))name='home';
  if(['settings','users'].includes(name)&&S.user?.role!=='admin'){if(S.user){toast('Choisissez le profil Famille pour ouvrir les réglages.');auth();return;}S.requestedView=name;auth();return;}
  rememberReading();
  setMenu(false,false);
  S.view=name;document.dispatchEvent(new CustomEvent('survie:view'));if(name!=='data')clearTimeout(contentTimer);if(name!=='chat')clearTimeout(translationTimer);else if(S.translation)loadTranslation(S.translation);
  document.body.classList.toggle('chat-open',name==='chat');
  for(const section of document.querySelectorAll('.view'))section.hidden=section.id!=='view-'+name;
  document.querySelectorAll('.nav-item').forEach(b=>{b.classList.toggle('active',b.dataset.view===name);if(b.dataset.view===name)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
  $('breadcrumb').textContent=labels[name];
  // The portal route adapter (interface/navigation.js) owns the URL and history state.
  if(name==='library')loadLearning();if(name==='monitor')refreshInference();if(name==='connect')loadNetwork();if(name==='settings'){loadAdmin();loadSettings();}if(name==='users')loadAdmin();if(name==='data')loadData();
  if(name!=='chat')window.scrollTo({top:0,behavior:'instant'});
  else{resumeConversation();if(S.conversation&&!S.loadingConversation)restoreReading(S.conversation);}
}
function accountUI(){
  const label=$('account-label');label.replaceChildren();
  label.append(document.createTextNode(S.user?.name||'Choisir un profil'),element('small',S.user?'Changer de profil · sans mot de passe':'Conversations et favoris'));
  $('content-manager').hidden=S.user?.role!=='admin';if(S.view==='data'&&S.user){loadContentManager();loadGeography();}
  $('mobile-account').textContent=S.user?.name||'Choisir un profil';$('engine-controls').hidden=S.user?.role!=='admin';$('admin-nav').hidden=S.user?.role!=='admin';$('geo-download-form').hidden=S.user?.role!=='admin';
  document.dispatchEvent(new CustomEvent('survie:auth'));
}
async function auth(){
  setMenu(false,false);
  const dialog=$('auth-dialog');if(!dialog.open)dialog.showModal();$('profile-error').textContent='';$('profile-list').replaceChildren();
  try{const data=await api('/profiles');for(const profile of data.profiles){const b=button(profile.name+(profile.id===S.user?.id?' · utilisé ici':''),()=>switchProfile(profile.id),'profile-choice secondary');b.setAttribute('aria-pressed',String(profile.id===S.user?.id));$('profile-list').append(b);}}
  catch(error){$('profile-error').textContent=error.message;}
}
async function switchProfile(identifier){
  try{await api('/profiles/select',{id:identifier});localStorage.setItem('survie.profile.changed',String(Date.now()));reloadProfile();}catch(error){$('profile-error').textContent=error.message;}
}

function needUser(){if(S.user)return true;auth();return false;}
async function histories(){
  const list=$('conversation-list'),picker=$('conversation-picker');list.replaceChildren();picker.replaceChildren(element('option','Retrouver une conversation'));picker.firstChild.value='';
  if(!S.user){list.append(element('p','Choisissez un profil pour retrouver vos échanges.','muted small'));picker.hidden=true;return;}
  try{const data=await api('/conversations');for(const c of data.conversations){const row=element('div',undefined,'conversation-row'),remove=button('×',()=>deleteConversation(c),'conversation-delete');remove.setAttribute('aria-label','Supprimer la conversation : '+c.title);remove.title='Supprimer cette conversation';row.append(button(c.title,()=>openConversation(c.id),'conversation-link'),remove);list.append(row);const o=element('option',c.title);o.value=c.id;picker.append(o);}picker.hidden=!data.conversations.length;if(!data.conversations.length)list.append(element('p','Vos premières conversations apparaîtront ici.','muted small'));}catch(e){toast(e.message);}
}
async function deleteConversation(c){
  if(!confirm('Supprimer la conversation « '+c.title+' » et tous ses messages ? Les traductions publiées restent dans la bibliothèque. Les traductions non publiées seront supprimées.'))return;
  try{await api('/conversations/'+encodeURIComponent(c.id),undefined,{method:'DELETE'});if(S.conversation===c.id)newConversation();await histories();toast('Conversation supprimée.');}catch(e){toast(e.message);}
}
function renderText(target,text,sources=[]){
  const html=marked.parse(String(text),{gfm:true,breaks:true});
  const fragment=DOMPurify.sanitize(html,{
    RETURN_DOM_FRAGMENT:true,
    ALLOWED_TAGS:['p','br','strong','b','em','i','s','del','h1','h2','h3','h4','h5','h6','ul','ol','li','blockquote','pre','code','hr','table','thead','tbody','tr','th','td','a','sub','sup','details','summary'],
    ALLOWED_ATTR:['href','title','start','colspan','rowspan'],
    ALLOW_DATA_ATTR:false,ALLOW_ARIA_ATTR:false
  });
  for(const link of fragment.querySelectorAll('a')){
    const href=link.getAttribute('href')||'';
    if(!/^(https?:|mailto:|\/|#)/i.test(href)||href.startsWith('//'))link.removeAttribute('href');
    else if(/^https?:/i.test(href)){link.target='_blank';link.rel='noopener noreferrer';}
  }
  // Citations stay clickable, except inside literal code and existing links.
  const walker=document.createTreeWalker(fragment,NodeFilter.SHOW_TEXT),texts=[];
  while(walker.nextNode())if(!walker.currentNode.parentElement?.closest('code,pre,a'))texts.push(walker.currentNode);
  const citation=/\[(\d{1,3}(?:\s*[,;]\s*\d{1,3})*)(?:\s*,\s*p(?:age)?s?\.?\s*(\d{1,4}))?\]/gi;
  for(const node of texts){
    const text=node.textContent,replacement=document.createDocumentFragment();let last=0;
    for(const match of text.matchAll(citation)){
      if(match.index&&/[\p{L}\p{N}_\\]/u.test(text[match.index-1]))continue;
      replacement.append(document.createTextNode(text.slice(last,match.index)));
      const numbers=match[1].split(/\s*[,;]\s*/).map(Number),known=numbers.map(number=>sources.find(source=>source.number===number));
      if(known.every(Boolean))for(const source of known){
        const page=Number(match[2]),base=source.id.split('#page=')[0],readPage=source.id.endsWith('#page='+page)||source.pages?.includes(page);
        const target=page&&readPage&&base.startsWith('guide:')&&base.toLowerCase().endsWith('.pdf')?base+'#page='+page:source.id;
        replacement.append(button('['+source.number+(page?', p. '+page:'')+']',()=>readSource(target),'citation'));
      }else replacement.append(document.createTextNode(match[0]));
      last=match.index+match[0].length;
    }
    if(last){replacement.append(document.createTextNode(text.slice(last)));node.replaceWith(replacement);}
  }
  for(const table of fragment.querySelectorAll('table')){const wrap=element('div',undefined,'message-table');wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Tableau défilant horizontalement');table.replaceWith(wrap);wrap.append(table);wrap.before(element('p','Faites glisser le tableau pour lire les autres colonnes →','table-scroll-hint'));}
  target.replaceChildren(fragment);
}

function sourceDates(source){
  const parts=[source.document_date?'Document : '+source.document_date:'Date du document inconnue'];
  if(source.edition)parts.push('Édition : '+source.edition);
  if(source.archive_date)parts.push('Archive (catalogue) : '+source.archive_date);
  if(source.collected_at)parts.push('Collecte locale : '+source.collected_at);
  return parts.join(' · ');
}
function sourceChips(sources){
  const refs=element('div',undefined,'source-chips');
  for(const source of sources){
    refs.append(button(`[${source.number}] ${source.title} · ${sourceDates(source)}`,()=>readSource(source.id)));
    if(source.id?.startsWith('guide:')&&source.id.split('#page=')[0].toLowerCase().endsWith('.pdf')&&Array.isArray(source.pages))for(const page of source.pages.slice(0,12).filter(n=>Number.isInteger(n)&&n>0&&n<=1200))refs.append(button('['+source.number+'] Page '+page,()=>readSource(source.id.split('#page=')[0]+'#page='+page)));
  }
  return refs;
}

function documentaryStatus(target,data){
  const statuses={complete:'Recherche effectuée',partial:'Recherche limitée',unavailable:'Recherche indisponible',unknown:'Couverture non mesurée',not_run:'Document consulté'};
  const counts=['searches','results','sources_read','failed_reads','partial_reads'];
  const valid=data?.schema===1&&Object.prototype.hasOwnProperty.call(statuses,data.status)&&counts.every(key=>Number.isInteger(data[key])&&data[key]>=0&&data[key]<=10000);
  target.hidden=!valid||data.status==='not_run'&&!data.sources_read&&!data.failed_reads;
  if(target.hidden)return;
  const label=!data.searches&&data.failed_reads?'Lecture limitée':data.status==='complete'&&!data.results?'Aucun résultat pour ces recherches':statuses[data.status];
  target.querySelector('summary').textContent=label+' · '+(data.sources_read?data.sources_read+' source(s) consultée(s)':'aucune source consultée');
  const scope={library:'Bibliothèque',targeted:'Périmètre ciblé',favorites:'Favoris',mixed:'Plusieurs périmètres',document:'Document indiqué'}[data.scope]||'Périmètre non mesuré';
  target.querySelector('.documentary-counts').textContent=scope+' · '+data.searches+' recherche(s) · '+data.results+' résultat(s) proposé(s).';
  const reading=target.querySelector('.documentary-reading');reading.hidden=!data.failed_reads&&!data.partial_reads;
  reading.textContent=(data.failed_reads?data.failed_reads+' source(s) n’ont pas pu être lues. ':'')+(data.partial_reads?data.partial_reads+' source(s) ont été consultées par passages.':'');
  const limit=target.querySelector('.documentary-limits');limit.hidden=data.status==='not_run'||data.status==='complete'&&data.results>0;
  limit.textContent=data.status==='complete'?'Aucun résultat pour ces recherches ; cela ne prouve pas que le sujet est absent de la bibliothèque.':'Le suivi est incomplet. Il ne permet pas de conclure que le sujet est absent de la bibliothèque.';
  const sources=Array.isArray(data.consulted_sources)?data.consulted_sources.filter(source=>source&&typeof source.id==='string'&&/^(guide|zim|video):/.test(source.id)&&typeof source.title==='string').slice(0,12):[];
  const list=target.querySelector('.documentary-sources'),heading=target.querySelector('.documentary-source-heading');heading.hidden=!sources.length;list.hidden=!sources.length;
  heading.textContent='Documents consultés · '+sources.length+' lien(s) affiché(s) sur '+data.sources_read;
  const previous=new Map([...list.querySelectorAll('button')].map(node=>[node.dataset.source,node]));
  for(const source of sources){let node=previous.get(source.id);if(!node){node=button(source.title,()=>readSource(source.id),'secondary');node.dataset.source=source.id;list.append(node);}else{node.textContent=source.title;previous.delete(source.id);}}
  for(const node of previous.values())node.remove();
}
function message(role,text,sources=[],profile='',observed=null){
  const node=element('article',undefined,'message message-'+role);node.append(element('div',role==='user'?'Vous':(profile||'Assistant'),'message-label'));
  const body=element('div');renderText(body,text,sources);node.append(body);
  const tracking=element('details',undefined,'documentary-status');tracking.hidden=true;
  tracking.setAttribute('aria-label','Suivi documentaire de cette réponse');tracking.append(element('summary'));
  for(const name of ['counts','reading','limits'])tracking.append(element('p',undefined,'small muted documentary-'+name));
  tracking.append(element('p',undefined,'small muted documentary-source-heading'),element('div',undefined,'documentary-sources'));
  node.append(tracking);if(role==='assistant')documentaryStatus(tracking,observed);
  if(sources.length)node.append(sourceChips(sources));
  node.sourceReferences=sources;$('chat-messages').append(node);document.dispatchEvent(new CustomEvent('survie:message',{detail:{node,sources,observed}}));return {node,body,tracking};
}
function resetChatMessages(empty=false){
  const messages=$('chat-messages');
  messages.replaceChildren(...(translationThread?[translationThread]:[]));
  if(empty)messages.insertAdjacentHTML('beforeend',EMPTY);
}
function newConversation(){
  if(S.sourceChanging||S.sending){toast('Attendez la fin du choix des documents ou de l’envoi de la question.');return;}
  if(S.job){toast('Attendez la réponse ou annulez la demande avant d’ouvrir une autre conversation.');view('chat');return;}
  rememberReading();selectReading(null);S.conversationLoad=(S.conversationLoad||0)+1;S.loadingConversation=false;S.conversation=null;S.source=null;S.sources=[];clearTranslation();showAssociatedSource();$('chat-title').textContent='Une question ? Prenons le temps de comprendre.';resetChatMessages(true);bindExamples();view('chat');document.dispatchEvent(new CustomEvent('survie:new-conversation'));
}
async function openConversation(id,{silent=false}={}){
  if(S.sending){toast('La question est en cours d’envoi.');return;}
  if(S.job){toast('Une demande est en cours. Vous pouvez l’annuler pour changer de conversation.');return;}
  rememberReading();S.loadingConversation=true;refreshSourceChoices();const load=S.conversationLoad=(S.conversationLoad||0)+1;
  try{
    const data=await api('/conversations/'+encodeURIComponent(id));
    if(load!==S.conversationLoad)return;
    S.conversation=id;
    S.sources=data.selected_sources||(data.source?[data.source]:[]);
    S.source=S.sources[0]||null;
    clearTranslation();
    showAssociatedSource();
    $('chat-title').textContent=data.title;
    resetChatMessages();
    for(const m of data.messages){
      const profile=m.model?(({rapide:'Réponse rapide',moyenne:'Réponse moyenne',approfondie:'Réponse approfondie'}[m.mode]||'Comparaison')+' · '+m.model):'';
      message(m.role,m.content,m.sources,profile,m.documentary).node.dataset.messageId=String(m.id);
    }
    if(!silent)view('chat');
    selectReading(id);
    if(data.jobs.length)watch(data.jobs[0].id);
    const match=data.translation_items?.find(t=>t.source_id.split('#page=')[0]===S.source?.id.split('#page=')[0]);
    const translation=match?.id||(translationThread?data.translation_items?.[0]?.id:null)||(!data.translation_items?data.translations?.[0]:null);
    if(translation)loadTranslation(translation);
    document.dispatchEvent(new CustomEvent('survie:conversation',{detail:data}));
    if(!silent)restoreReading(id);
  }catch(e){
    if(e.status===404)selectReading(null);
    toast(e.message);
  }finally{
    if(load===S.conversationLoad){S.loadingConversation=false;refreshSourceChoices();}
  }
}
function bindExamples(){document.querySelectorAll('[data-question]').forEach(b=>b.onclick=()=>{$('chat-input').value=b.dataset.question;$('chat-input').focus();});}
async function status(){
  try{
    S.status=await api('/status');
    $('software-version').textContent='Version d’essai '+S.status.version;
    for(const version of document.querySelectorAll('.ds-nav-version'))version.textContent=S.status.version;
    const modes=$('chat-mode'),selected=modes.value;modes.replaceChildren();for(const category of ['recommended','comparison']){const group=element('optgroup');group.label=category==='recommended'?'Choix conseillés pour les essais':'Autres modèles à comparer';for(const profile of S.status.modes.filter(x=>x.category===category)){const option=element('option',profile.name);option.value=profile.id;group.append(option);}modes.append(group);}if([...modes.options].some(o=>o.value===selected))modes.value=selected;$('library-count').textContent=`${S.status.books.length} collections · ${S.status.guides} guides`;
    const grid=$('collections');grid.replaceChildren();for(const book of S.status.books){const b=button('',()=>{view('data');},'collection');b.append(element('span','▤','book-icon'));const copy=element('span');copy.append(element('strong',book.title),element('small',book.language==='fra'?'Français · disponible hors ligne':'Anglais · disponible hors ligne'));b.append(copy);grid.append(b);}
  }catch(e){$('service-status').textContent='Service momentanément indisponible';toast(e.message);}
}
function search(query){document.dispatchEvent(new CustomEvent('survie:scope-reset'));$('library-query').value=query;view('library');runSearch();}
async function runSearch(event){
  event?.preventDefault();const q=$('library-query').value.trim(),kind=$('search-kind')?.value||'all';if(!q&&kind!=='videos')return;
  S.searchAbort?.abort();const controller=new AbortController();S.searchAbort=controller;$('search-message').textContent='Recherche en cours — aucun résultat pour le moment. Les collections sont en cours d’examen.';$('search-message').classList.remove('search-warning');$('search-results').setAttribute('aria-busy','true');$('reader').hidden=true;document.querySelector('.reading-layout').classList.remove('reading');$('search-results').replaceChildren();
  function display(data){
    if(controller.signal.aborted||S.searchAbort!==controller)return;
    const selectedCollection=[...($('search-collection')?.options||[])].find(o=>o.value===data.coverage?.collection)?.textContent||({wikipedia:'Wikipédia',appropedia:'Appropedia',wikibooks:'Wikilivres',wikihow:'wikiHow'}[data.coverage?.collection])||data.coverage?.collection;
    const ongoing=data.state==='results',partial=!!data.coverage?.status&&data.coverage.status!=='complete';
    $('search-results').setAttribute('aria-busy',String(ongoing));
    $('search-message').classList.toggle('search-warning',!ongoing&&partial);
    const noun={videos:'vidéo(s) trouvée(s)',documents:'document(s) trouvé(s)'}[kind]||'résultat(s) trouvé(s)',count=`${data.results.length} ${noun}`+(q?` pour « ${q} »`:' parmi les vidéos répertoriées');
    const label=ongoing?(data.results.length?'Recherche en cours — '+count+'. D’autres résultats peuvent encore arriver.':'Recherche en cours — aucun résultat pour le moment.'):
      (partial?'Recherche terminée, mais incomplète — ':'Recherche terminée — ')+(data.results.length?count:partial?'aucun résultat dans la partie interrogée.':q?'aucun résultat trouvé pour « '+q+' ».':'aucune vidéo répertoriée.');
    $('search-message').textContent=label+(ongoing&&Number.isFinite(data.coverage?.collections_selected)?' · '+((data.coverage.searched||0)+(data.coverage.locally_indexed||0))+' / '+data.coverage.collections_selected+' collections examinées':'')+(data.coverage?.collection?' · Collection : '+selectedCollection:'')+(data.coverage?.warning?' · '+data.coverage.warning:'');
    const signature=JSON.stringify(data.results);if($('search-results').dataset.signature!==signature){
      const cards=[...$('search-results').querySelectorAll('.result')],opened=new Set(cards.filter(card=>card.querySelector('details[open]')).map(card=>card.dataset.source));
      const active=document.activeElement,focused=active?.closest('#search-results .result'),controls='a,button,summary,input,select',position=focused?[...focused.querySelectorAll(controls)].indexOf(active):-1,source=focused?.dataset.source;
      $('search-results').dataset.signature=signature;$('search-results').replaceChildren();renderLibraryResults(data.results);
      for(const card of $('search-results').querySelectorAll('.result')){if(opened.has(card.dataset.source)&&card.querySelector('details'))card.querySelector('details').open=true;if(source===card.dataset.source&&position>=0)card.querySelectorAll(controls)[position]?.focus({preventScroll:true});}
    }
    $('search-results').querySelectorAll('.search-extra').forEach(node=>node.remove());
    if(data.coverage?.domain&&data.coverage.domain!=='all'){const wider=button('Élargir à toute la bibliothèque',()=>{$('search-domain').value='all';$('search-domain').dispatchEvent(new Event('change'));},'secondary search-extra');$('search-results').append(wider);}
    if(!data.results.length&&kind==='videos'&&!ongoing)$('search-results').append(element('div',q?'Aucune vidéo ne correspond à ces mots. Effacez la recherche pour voir toutes les vidéos répertoriées, ou essayez un mot plus court.':'Aucune vidéo répertoriée pour le moment. Ajoutez des vidéos dans le dossier library/video, puis patientez : le répertoire s’actualise automatiquement.','empty-panel search-extra'));
    else if(!data.results.length)$('search-results').append(element('div',ongoing?'Aucun résultat pour le moment. La recherche continue ; les premiers documents apparaîtront ici.':partial?'Aucun résultat dans la partie interrogée. La recherche est incomplète ; cela ne prouve pas l’absence d’information.':'Aucun résultat trouvé. La recherche est terminée. Essayez un autre mot, une formulation plus courte ou une autre langue.','empty-panel search-extra'));
  }
  $('search-results').dataset.signature='';
  function interrupted(message){$('search-message').textContent=message;$('search-message').classList.add('search-warning');$('search-results').setAttribute('aria-busy','false');const empty=$('search-results').querySelector('.empty-panel.search-extra');if(empty)empty.textContent='Aucun résultat reçu avant l’interruption. La recherche est incomplète ; vous pouvez la relancer.';}
  $('search-stop')?.remove();const stop=button('Arrêter la recherche',()=>{controller.abort();if(S.searchAbort===controller){interrupted('Recherche arrêtée. Les résultats reçus sont conservés ; la recherche peut être incomplète.');stop.remove();}},'secondary');stop.id='search-stop';$('search-message').after(stop);
  try{const data=await api('/search?q='+encodeURIComponent(q)+'&stream=true&kind='+encodeURIComponent(kind)+'&language='+encodeURIComponent($('search-language').value)+'&domain='+encodeURIComponent($('search-domain')?.value||'all')+'&collection='+encodeURIComponent($('search-collection')?.value||$('search-collection')?.dataset.requested||''),undefined,{signal:controller.signal,onResult:display});display(data);
  }catch(e){if(e.name!=='AbortError'&&S.searchAbort===controller)interrupted(e.message);}
  finally{stop.remove();}
}
function videoTimestamp(ms){const seconds=Math.floor((Number(ms)||0)/1000);return String(Math.floor(seconds/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0');}
function renderLibraryResults(results){
  for(const result of results){const node=element('article',undefined,'result');node.dataset.source=result.id;node.append(element('div',`${result.kind==='guide'?'Guide':result.kind==='video'?'Vidéo':'Article'} · ${{fra:'Français',fr:'Français',eng:'Anglais',en:'Anglais'}[result.language]||'Autre langue'}${result.collection?' · '+result.collection:''}`,'result-meta'),element('h3',result.title),element('p',sourceDates(result),'muted small'),element('p',result.excerpt),button(result.kind==='video'?'Voir la vidéo →':'Lire le document →',()=>readSource(result.id)),sourceChoiceButton(result));
    if(result.kind==='video')node.append(element('p',result.match==='subtitle'?'Passage à '+videoTimestamp(result.position_ms)+' · sous-titres '+(result.language||'de langue inconnue'):'Titre et description seulement ; paroles non recherchées dans ce résultat.','small muted'));
    if(result.match_quality&&result.match_quality!=='subject')node.append(element('p',result.match_quality==='mention'?'Mention du sujet dans le texte ; vérifiez que ce passage répond au besoin.':'Correspondance à vérifier en ouvrant le document.','small muted'));
    if(result.other_matches?.length){const details=element('details',undefined,'other-matches');details.append(element('summary',result.other_matches.length+' autre(s) passage(s) dans ce document'));for(const match of result.other_matches){
      const passage=button(match.kind==='video'?'À '+videoTimestamp(match.position_ms)+' · '+(match.language||'langue inconnue')+' · '+match.title:match.title,()=>readSource(match.id),'text-button');
      passage.dataset.resultPassage=match.id;
      details.append(passage);
    }node.append(details);}
    $('search-results').append(node);
  }
  refreshSourceChoices();document.dispatchEvent(new CustomEvent('survie:results',{detail:results}));
}

let learningState=null;
function learningSelection(){
  const domain=learningState?.domains.find(d=>d.id===$('learning-domain').value);
  return {domain,subject:domain?.subjects[Number($('learning-subject').value)]};
}
function updateLearningSubject(){
  const domain=learningSelection().domain;$('learning-subject').replaceChildren();
  for(const [i,subject] of (domain?.subjects||[]).entries()){const option=element('option',subject.label);option.value=i;$('learning-subject').append(option);}
  $('learning-summary').textContent=domain?.summary||'';
}
async function loadLearning(){
  if(learningState)return;
  try{
    const data=await api('/library/learning');if(!Array.isArray(data.domains)||!Array.isArray(data.steps))throw Error('Catalogue de parcours incomplet');learningState=data;
    $('learning-domain').replaceChildren();for(const domain of data.domains){const option=element('option',domain.label);option.value=domain.id;$('learning-domain').append(option);}
    $('learning-level').replaceChildren();for(const level of data.levels||[]){const option=element('option',level.label);option.value=level.id;$('learning-level').append(option);}
    $('learning-notice').textContent=data.notice;$('learning-steps').replaceChildren();
    for(const step of data.steps){const item=element('li');item.append(element('strong',step.label+' : '),document.createTextNode(step.description));$('learning-steps').append(item);}
    updateLearningSubject();for(const id of ['learning-domain','learning-subject','learning-search','learning-ask'])$(id).disabled=!data.domains.length;
  }catch(e){$('learning-notice').textContent='Les parcours ne sont pas disponibles. Vous pouvez utiliser la recherche ci-dessous.';}
}
$('learning-domain').onchange=updateLearningSubject;
$('learning-search').onclick=()=>{const {subject}=learningSelection();if(!subject)return;$('library-query').value=subject.query;$('library-search').requestSubmit();};
$('learning-ask').onclick=()=>{
  if(S.job){toast('Attendez la réponse en cours ou annulez-la.');return;}
  if(!needUser())return;
  const {domain,subject}=learningSelection();if(!subject)return;const level=learningState.levels?.find(l=>l.id===$('learning-level').value);
  newConversation();$('chat-input').value=`Je souhaite apprendre : ${subject.label} (${domain.label}). Niveau demandé : ${level?.label||'Comprendre le principe'} — ${level?.description||''}. Adapte le parcours à mon âge et mon niveau ; demande les informations manquantes et les ressources disponibles. Recherche puis lis les documents locaux. Explique les principes, propose des exercices et des corrections, puis les étapes : comprendre, mesurer, réaliser, contrôler, entretenir, transmettre, lorsque cela s’applique. Précise les matériaux, outils, instruments, compétences, limites et contrôles documentés. Cite les sources et leurs dates ; signale les informations absentes. Pour un acte à risque, distingue l’étude de la réalisation pratique.`;
  $('chat-title').textContent='Apprendre : '+subject.label;$('chat-input').focus();
};

function documentText(source){let text=String(source.text||'');if(/^guide:(?:WIKI-FR-|BOOK-EN-)/.test(source.id)&&text.startsWith('Identifiant de source : ')){const end=text.indexOf('\n\n');if(end>=0)text=text.slice(end+2);}const lines=text.split('\n'),norm=x=>x.trim().replace(/[’‘]/g,"'").toLocaleLowerCase();while(lines.length&&(!lines[0].trim()||norm(lines[0])===norm(source.title)))lines.shift();return lines.join('\n');}
function renderDocument(target,source){const text=documentText(source);if(source.id?.split('#')[0].endsWith('.md')){renderText(target,text);return;}if(!text.trim()){target.textContent='Cet aperçu ne contient pas de texte lisible. Ouvrez le document d’origine pour le consulter.';return;}for(const line of text.split('\n')){if(!line.trim())continue;const paragraph=element('p',line);target.append(paragraph);}}
function originalSourceURL(id){
  const archive=id.startsWith('zim:'),guide=id.startsWith('guide:');if(!archive&&!guide)return null;
  let path=id.slice(archive?4:6).replace(/#page=\d+$/,'');
  try{for(let count=0;count<3;count++){const decoded=decodeURIComponent(path);if(decoded===path)break;path=decoded;}}catch(_){return null;}
  if(!path||path.startsWith('/')||path.includes('\\')||path.includes('\0')||/%[a-f0-9]{2}/i.test(path)||path.split('/').some(part=>part==='.'||part==='..'))return null;
  const encoded=path.split('/').map(encodeURIComponent).join('/');
  if(archive)return localServiceURL('/content/'+encoded,'kiwix');
  return path.toLowerCase().endsWith('.pdf')?'/pdf.html?id='+encodeURIComponent(id):'/guides/'+encoded;
}
async function readSource(id){
  view('library');document.querySelectorAll('.result').forEach(node=>node.classList.toggle('selected',node.dataset.source===id));S.reader=id;const reader=$('reader');reader.hidden=false;reader.replaceChildren(element('p','Ouverture du document…','muted'));
  document.querySelector('.reading-layout').classList.add('reading');
  try{const source=await api('/source?id='+encodeURIComponent(id));if(S.reader!==id)return;reader.replaceChildren();
    const actions=element('div',undefined,'reader-actions');actions.append(button('← Résultats',()=>{reader.hidden=true;document.querySelector('.reading-layout').classList.remove('reading');},'secondary'),button('Poser une question sur ce document',()=>askSource(source)));
    actions.append(sourceChoiceButton(source));if(S.conversation)actions.append(button('Revenir à la conversation',()=>view('chat'),'text-button'));
    reader.append(actions,element('div',source.id.startsWith('guide:WIKI-FR-')?'EXTRAIT DE WIKIPÉDIA':source.id.startsWith('guide:BOOK-EN-')?'EXTRAIT DE WIKILIVRES':source.kind==='guide'?'GUIDE LOCAL':source.kind==='video'?'VIDÉO LOCALE':'ARTICLE DE LA BIBLIOTHÈQUE','eyebrow'),element('h2',source.title));
    reader.append(element('p',sourceDates(source),'source-dates muted small'));
    if(source.images?.length){const images=element('div',undefined,'reader-images');for(const img of source.images.slice(0,4)){const e=element('img');e.src='/api/media?id='+encodeURIComponent(img.id);e.alt=img.alt;e.loading='lazy';images.append(e);}reader.append(images);}
    if(source.kind!=='video'&&/^(en|eng)$/.test(source.language||'')){const translate=button('Traduire en français',()=>{askSource(source);if(S.source?.id===source.id){$('translation-panel').open=true;$('translation-panel').scrollIntoView({block:'nearest'});}},'secondary');translate.dataset.documentAction='translate';actions.append(translate);}
    if(source.provenance||source.licence){const details=element('details',undefined,'source-details');details.append(element('summary','Origine et licence du document'));if(source.provenance)details.append(element('p',source.provenance));if(source.licence)details.append(element('p',source.licence));reader.append(details);}const body=element('div',undefined,'reader-body');renderDocument(body,source);reader.append(body);
    if(source.preview)reader.append(element('p',source.kind==='video'?'Aperçu des sous-titres à partir du passage choisi ; la lecture complète du média reste disponible dans le lecteur.':'Aperçu du début du livre. La recherche retrouve aussi les pages suivantes dont le texte est lisible. Ouvrez le PDF pour consulter l’ensemble des pages et illustrations.','muted small'));
    const original=element('a',source.id.includes('.pdf')?'Lire le PDF illustré →':'Ouvrir le document d’origine →','secondary-link');
    const archiveLink=/^guide:(?:WIKI-FR-|BOOK-EN-)/.test(source.id)?source.text.match(/Original illustré local : (https?:\/\/[^\s]+)/):null;if(archiveLink){try{const path=new URL(archiveLink[1]).pathname;if(path.startsWith('/content/')){original.href=localServiceURL(path,'kiwix');original.textContent='Voir la page illustrée d’origine →';}}catch(_){}}if(!original.hasAttribute('href')&&(source.id.startsWith('guide:')||source.kind==='video'))original.href=source.url;else if(!original.hasAttribute('href')){original.href=localServiceURL(source.url,'kiwix');}original.target='_blank';original.rel='noopener';actions.append(original);document.dispatchEvent(new CustomEvent('survie:source',{detail:source}));
  }catch(e){
    if(S.reader!==id)return;
    const message=element('p','L’aperçu de ce document n’a pas pu être ouvert.','error'),actions=element('div',undefined,'reader-actions');
    actions.append(button('← Résultats',()=>{reader.hidden=true;document.querySelector('.reading-layout').classList.remove('reading');},'secondary'),button('Réessayer',()=>readSource(id),'secondary'));
    const direct=originalSourceURL(id);
    if(direct){const link=element('a','Ouvrir le document d’origine →','secondary-link');link.href=direct;link.target='_blank';link.rel='noopener';actions.append(link);}
    reader.replaceChildren(actions,message,element('p',e.message,'small muted'),element('p','Un résultat de recherche ne garantit pas que sa page soit encore lisible. L’original peut fonctionner même lorsque cet aperçu échoue.','small muted'));
  }
}
function askSource(source){
  if(S.sourceChanging||S.sending){toast('Attendez la fin du choix des documents ou de l’envoi de la question.');return;}
  if(S.job){toast('Attendez la réponse en cours ou annulez-la.');return;}
  newConversation();S.source=source;S.sources=[source];showAssociatedSource();view('chat');$('chat-input').focus();
}
let translationTimer=null,translationVersion=0,translationBusy=false;
function clearTranslation(){clearTimeout(translationTimer);translationVersion++;S.translation=null;S.translationSource=null;S.translationOffset=0;$('translation-panel').open=false;$('translation-parts').replaceChildren();$('translation-status').textContent='';$('translation-summary').textContent='Traduire le document en français';$('translation-progress').hidden=true;$('translation-progress').value=0;$('translation-progress').max=1;document.dispatchEvent(new CustomEvent('survie:translation-clear'));for(const id of ['translation-pause','translation-resume','translation-export','translation-previous','translation-next'])$(id).hidden=true;$('translation-start').hidden=false;$('translation-first').value='1';$('translation-last').value='';}
function selectedSourceChoices(){return S.sources?.length?S.sources:S.source?[S.source]:[];}
function sourceChoiceButton(source){
  const b=button('',()=>toggleSourceChoice(source),'secondary source-choice-action');b.dataset.choiceId=source.id;const chosen=selectedSourceChoices().some(item=>item.id===source.id);b.textContent=chosen?'Choisi pour l’assistant':'Choisir pour l’assistant';b.setAttribute('aria-pressed',String(chosen));b.disabled=!!(S.sourceChanging||S.sending||S.job||S.summaryActive||S.loadingConversation);return b;
}
function refreshSourceChoices(){
  const ids=new Set(selectedSourceChoices().map(source=>source.id));
  if($('translation-target'))$('translation-target').disabled=!!(S.sourceChanging||S.sending||translationBusy);
  for(const b of document.querySelectorAll('.source-choice-action')){
    b.disabled=!!(S.sourceChanging||S.sending||S.job||S.summaryActive||S.loadingConversation);
    if(b.dataset.choiceId){const chosen=ids.has(b.dataset.choiceId);b.setAttribute('aria-pressed',String(chosen));b.textContent=chosen?'Choisi pour l’assistant':'Choisir pour l’assistant';}
  }
  document.dispatchEvent(new CustomEvent('survie:source-state'));
}
async function changeSourceChoices(choices){
  if(!needUser())return false;
  if(S.job||S.summaryActive||S.sourceChanging||S.sending||S.loadingConversation){toast('Attendez la fin du travail en cours avant de modifier les documents.');return false;}
  const conversation=S.conversation,user=S.user.id,primary=S.source?.id;S.sourceChanging=true;refreshSourceChoices();
  try{
    const data=conversation?await api('/conversations/'+encodeURIComponent(conversation)+'/sources',{source_ids:choices.map(source=>source.id)},{method:'PUT'}):choices.length?await api('/conversations',{source_ids:choices.map(source=>source.id)}):{source:null,selected_sources:[]};
    if(S.user?.id!==user||S.conversation!==conversation)return false;
    S.sources=data.selected_sources||[];S.source=S.sources.find(source=>source.id===primary)||S.sources[0]||null;
    if(data.conversation_id){S.conversation=data.conversation_id;selectReading(S.conversation);$('chat-title').textContent='Documents : '+(S.sources[0]?.title||'Nouvelle conversation');await histories();}
    showAssociatedSource();return true;
  }catch(error){toast(error.message);return false;}
  finally{S.sourceChanging=false;refreshSourceChoices();$('translation-start').disabled=!S.source||translationBusy;}
}
async function toggleSourceChoice(source){
  const current=selectedSourceChoices(),chosen=current.some(item=>item.id===source.id);
  if(!chosen&&current.length>=12){toast('Vous avez choisi douze documents. Retirez-en un avant d’en ajouter un autre.');return;}
  if(await changeSourceChoices(chosen?current.filter(item=>item.id!==source.id):[...current,source]))toast(chosen?'Document retiré de la sélection.':'Document ajouté. Vous pouvez en choisir d’autres avant de poser votre question.');
}
function showAssociatedSource(){
  const choices=selectedSourceChoices(),node=$('chat-source'),wasOpen=node.querySelector('details')?.open;node.replaceChildren();node.hidden=!choices.length;
  const remove=source=>{const b=button('Retirer',()=>changeSourceChoices(selectedSourceChoices().filter(item=>item.id!==source.id)),'text-button source-choice-action');b.setAttribute('aria-label','Retirer '+source.title);return b;};
  if(choices.length===1){const source=choices[0];node.append(button('Document associé : '+source.title,()=>readSource(source.id),'text-button'),remove(source));}
  else if(choices.length){
    const detail=element('details',undefined,'chosen-documents');detail.open=!!wasOpen;detail.append(element('summary',choices.length+' documents choisis pour cette conversation'));
    const list=element('div',undefined,'chosen-documents-list');
    for(const source of choices){const row=element('div',undefined,'chosen-document');row.append(button(source.title,()=>readSource(source.id),'text-button'),remove(source));list.append(row);}
    detail.append(list,element('p','L’assistant lit des passages adaptés à votre question. Le suivi précise les documents réellement consultés.','small muted'));node.append(detail);
  }
  let tray=$('library-chosen-documents');if(!tray){tray=element('div',undefined,'library-chosen-documents');tray.id='library-chosen-documents';document.querySelector('.reading-layout').before(tray);}
  tray.replaceChildren();tray.hidden=!choices.length;
  if(choices.length){tray.append(element('span',choices.length+' document(s) choisi(s) pour l’assistant'),button('Poser une question',()=>{view('chat');$('chat-input').focus();},'secondary'));}
  let target=$('translation-target');if(!target){
    const label=element('label','Document à traduire');label.id='translation-target-label';target=element('select');target.id='translation-target';label.append(target);$('translation-range').before(label);
    target.onchange=()=>{S.source=selectedSourceChoices().find(source=>source.id===target.value)||null;clearTranslation();showAssociatedSource();};
  }
  target.replaceChildren();for(const source of choices){const option=element('option',source.title);option.value=source.id;target.append(option);}target.value=S.source?.id||'';target.disabled=!!(S.sourceChanging||S.sending||translationBusy);
  $('translation-target-label').hidden=choices.length<2;
  $('translation-panel').hidden=!S.source&&!S.translation;
  $('translation-start').disabled=!S.source||S.source.id.startsWith('video:')||translationBusy||S.sourceChanging;$('translation-range').hidden=!S.source?.id.toLowerCase().split('#page=')[0].endsWith('.pdf')||!!S.translation;
  refreshSourceChoices();document.dispatchEvent(new CustomEvent('survie:source-choices'));
}
async function attachToConversation(source){
  if(await changeSourceChoices([...selectedSourceChoices().filter(item=>item.id!==source.id),source]))view('chat');
}
function translationReadingState(id){
  try{const saved=JSON.parse(localStorage.getItem('survie-translation-reading:'+S.user.id))?.[id];return {offset:Number.isInteger(saved?.offset)?Math.max(0,Math.min(100000,saved.offset)):0,open:saved?.open===true};}catch(_){return {offset:0,open:false};}
}
function translationReading(id,offset,open){
  if(!S.user)return 0;
  const key='survie-translation-reading:'+S.user.id;
  try{
    const saved=JSON.parse(localStorage.getItem(key))||{};
    if(offset===undefined&&open===undefined)return translationReadingState(id).offset;
    saved[id]={offset:offset??translationReadingState(id).offset,open:typeof open==='boolean'?open:saved[id]?.open===true,updated:Date.now()};
    const ids=Object.keys(saved).sort((a,b)=>(saved[b].updated||0)-(saved[a].updated||0));
    for(const old of ids.slice(100))delete saved[old];localStorage.setItem(key,JSON.stringify(saved));
  }catch(_){}return 0;
}
function renderTranslationParts(data,parts){
  const parent=$('translation-parts'),key=S.user.id+':'+data.id+':'+data.offset;
  if(parent.dataset.reading!==key){parent.replaceChildren();parent.dataset.reading=key;}
  const existing=new Map([...parent.children].map(node=>[Number(node.dataset.position),node]));
  let next=parent.firstElementChild;
  for(const part of parts){
    const previous=existing.get(part.position),snapshot=JSON.stringify(part);
    existing.delete(part.position);
    if(previous?._translationSnapshot===snapshot){next=previous.nextElementSibling;continue;}
    const article=element('article',undefined,'translation-part');article.append(element('h3','Page/section '+part.page+' · passage '+(part.position+1)));
    if(part.model||part.quality?.model)article.append(element('p',part.model||part.quality.model,'small muted'));
    if(part.status==='done'){
      const text=element('div',undefined,'translation-text');
      if(window.SurvieTranslationText)window.SurvieTranslationText.render(text,part.translated);else text.textContent=part.translated;
      article.append(text);
    }else if(!translationThread||part.status==='unreadable'||part.status==='deferred')article.append(element('p',part.status==='unreadable'?'Aucun texte extractible : page illustrée ou reconnaissance de caractères nécessaire.':part.status==='deferred'?'Ce passage reste à traduire après vérification.':'Ce passage reste à traduire.'));
    if(part.quality&&(!translationThread||part.status!=='unreadable'||part.quality.status!=='unchecked')){
      const labels={checked:'Contrôles limités : aucune anomalie repérée. Le sens reste à vérifier.',warning:'À relire : anomalie possible.',blocked:'Passage refusé par les contrôles.',unchecked:'Pas de contrôle automatique enregistré pour ce passage.'};
      article.append(element('p',labels[part.quality.status]||'Contrôle indisponible.',part.quality.status==='checked'?'small muted':'translation-label small'));
      for(const issue of part.quality.issues||[])article.append(element('p',issue.message,'translation-label small'));
    }
    if(part.source_text){const details=element('details',undefined,'translation-comparison');details.append(element('summary','Comparer avec le texte original'),element('pre',part.source_text));article.append(details);}
    if(part.candidate){const details=element('details');details.append(element('summary','Voir la proposition refusée · ne pas utiliser'),element('p',part.candidate));article.append(details);}
    const original=data.source_id.toLowerCase().endsWith('.pdf')?data.source_id+'#page='+part.page:data.source_id;article.append(button('Consulter l’original',()=>readSource(original),'text-button'));
    article.dataset.position=part.position;article._translationSnapshot=snapshot;
    if(previous){const opened=[...previous.querySelectorAll('details')].map(node=>node.open);article.querySelectorAll('details').forEach((node,i)=>node.open=!!opened[i]);previous.replaceWith(article);}
    else parent.insertBefore(article,next);
    next=article.nextElementSibling;
  }
  for(const node of existing.values())node.remove();
}
const translationStop=button('Arrêter la traduction',()=>translationAction('stop'),'secondary');translationStop.id='translation-stop';translationStop.hidden=true;
const translationDelete=button('Supprimer la traduction',()=>translationAction('delete'),'secondary');translationDelete.id='translation-delete';translationDelete.hidden=true;
$('translation-pause').after(translationStop);$('translation-export').after(translationDelete);
const translationReadingStatus=element('p',undefined,'small');translationReadingStatus.id='translation-reading-status';translationReadingStatus.setAttribute('role','status');
$('translation-progress').after(translationReadingStatus);
const translationReadingActions=element('div',undefined,'translation-actions');translationReadingActions.id='translation-reading-actions';translationReadingActions.hidden=true;
const translationBeginning=button('Lire depuis le début',()=>loadTranslation(S.translation,0),'secondary');translationBeginning.id='translation-reading-first';
const translationLatest=button('Lire les derniers passages traduits',()=>loadTranslation(S.translation,Math.floor((S.translationLastDone||0)/10)*10),'secondary');translationLatest.id='translation-reading-latest';
translationReadingActions.append(translationBeginning,translationLatest);translationReadingStatus.after(translationReadingActions);
const translationReader=element('dialog',undefined,'translation-reading-dialog');translationReader.id='translation-reading-dialog';translationReader.setAttribute('aria-labelledby','translation-reading-title');
translationReader.innerHTML='<header><h2 id="translation-reading-title">Lire le texte français</h2><button id="translation-reading-close" class="secondary">Fermer la lecture</button></header><p id="translation-reading-notice" class="small muted"></p><div id="translation-reading-content"></div>';
document.body.append(translationReader);
const translationReadOpen=button('Lire le texte français',()=>openTranslationReader(),'secondary');translationReadOpen.id='translation-reading-open';translationReadOpen.hidden=true;$('translation-summary').after(translationReadOpen);
const translationControls=$('translation-pause').parentElement;
const translationDownload=$('translation-export');
const translationNavigation=$('translation-previous').parentElement;
let translationMore=null,translationMoreActions=null;
const translationThread=element('section',undefined,'translation-thread');
if(translationThread){
  translationThread.id='translation-thread';
  translationThread.setAttribute('aria-label','Passages de la traduction');
  translationThread.hidden=true;
  $('chat-messages').append(translationThread);
  translationThread.append(translationReadingStatus,translationReadingActions,$('translation-parts'),translationNavigation);

  const toolbar=element('div',undefined,'translation-toolbar');
  toolbar.append(translationControls,translationReadOpen);
  translationMore=element('details',undefined,'translation-more');
  translationMore.id='translation-more';
  translationMore.hidden=true;
  translationMoreActions=element('div',undefined,'translation-actions');
  translationMoreActions.append(translationStop,translationDownload,translationDelete);
  translationMore.append(element('summary','Plus d’actions'),translationMoreActions);
  const content=$('translation-panel').querySelector('.translation-content');
  content.prepend(toolbar,$('translation-progress'),translationMore,$('translation-status'));
  const help=element('details',undefined,'translation-help');
  help.append(element('summary','À propos de la traduction'),content.querySelector('p.small'));
  content.append(help);
}
const readingNodes=[translationControls,translationMoreActions,translationReadingStatus,translationReadingActions,$('translation-parts'),translationNavigation].filter(Boolean);
const readingMarkers=readingNodes.map(node=>{const marker=document.createComment('translation-reading-home');node.before(marker);return marker;});
function moveTranslationReader(open){
  if(open){for(const node of readingNodes)$('translation-reading-content').append(node);}
  else readingNodes.forEach((node,index)=>readingMarkers[index].after(node));
}
function openTranslationReader(restoring=false){
  if(!S.translation||!S.user)return;
  if(restoring&&document.readyState==='loading'){
    const id=S.translation,owner=S.user.id;document.addEventListener('DOMContentLoaded',()=>setTimeout(()=>{if(S.translation===id&&S.user?.id===owner)openTranslationReader(true);},0),{once:true});return;
  }
  translationReader.dataset.translationId=S.translation;translationReader.dataset.profileId=S.user.id;
  if(restoring)history.replaceState({...history.state,dialog:translationReader.id},'',location.href);
  translationReading(S.translation,S.translationOffset,true);moveTranslationReader(true);translationReader.showModal();
}
function rememberTranslationReaderClosed(){const id=translationReader.dataset.translationId;if(id&&S.user?.id===translationReader.dataset.profileId)translationReading(id,undefined,false);}
translationReader.addEventListener('close',()=>{if(!translationReader.open)rememberTranslationReaderClosed();});
translationReader.addEventListener('cancel',rememberTranslationReaderClosed);
$('translation-reading-close').onclick=()=>{rememberTranslationReaderClosed();translationReader.close();};
new MutationObserver(()=>{if(!translationReader.open)rememberTranslationReaderClosed();else if(S.translation&&S.user)translationReading(S.translation,S.translationOffset,true);moveTranslationReader(translationReader.open);}).observe(translationReader,{attributes:true,attributeFilter:['open']});
let translationReaderRestoredFor=null;
document.addEventListener('survie:translation',event=>{
  const data=event.detail;translationReadOpen.hidden=false;translationReadOpen.disabled=!data.done;
  const key=S.user?.id+':'+data.id;
  if(key!==translationReaderRestoredFor){translationReaderRestoredFor=key;if(data.done&&S.view==='chat'&&!translationReader.open&&translationReadingState(data.id).open)openTranslationReader(true);}
  $('translation-reading-title').textContent=data.title;
  $('translation-reading-notice').textContent=({running:'La suite continue à se traduire pendant votre lecture. ',queued:'La suite attend le moteur. ',paused:'Traduction en pause ; les passages terminés restent lisibles. ',stopped:'Traduction arrêtée ; les passages terminés restent lisibles et une reprise volontaire est possible. ',error:'La suite reste à reprendre depuis le panneau de traduction. ',completed:data.done<data.total?'Traduction incomplète. L’original reste consultable. ':'Traitement terminé. '}[data.status]||'')+(data.notice||'');
});
document.addEventListener('survie:view',()=>{if(S.view!=='chat'&&translationReader.open)translationReader.close();});
document.addEventListener('survie:translation-clear',()=>{if(translationReader.open){rememberTranslationReaderClosed();translationReader.close();}translationReaderRestoredFor=null;if(translationThread){translationThread.hidden=true;translationMore.hidden=true;translationMore.open=false;}translationReadOpen.hidden=true;translationStop.hidden=true;translationDelete.hidden=true;translationReadingActions.hidden=true;translationReadingStatus.textContent='';S.translationLastDone=null;});
document.addEventListener('survie:work-queue', ({detail}) => {
  const queue = window.WorkQueuePreview;
  queue.translationLabels(queue.aiBusy(detail), $('translation-start'), $('translation-resume'),
    'Traduire en français', $('translation-resume').dataset.deferred==='true'?'Reprendre les passages à vérifier':'Reprendre avec le modèle choisi');
});
async function loadTranslation(id,offset){
  if(offset===undefined)offset=id===S.translation?S.translationOffset:translationReading(id);
  clearTimeout(translationTimer);S.translation=id;S.translationOffset=offset;const version=++translationVersion,conversation=S.conversation,owner=S.user?.id;
  try{const data=await api('/translations/'+encodeURIComponent(id)+'?offset='+offset);
    if(version!==translationVersion||conversation!==S.conversation||!S.user||S.user.id!==owner)return;
    if(offset>=data.total&&offset>0)return loadTranslation(id,Math.max(0,Math.floor((data.total-1)/10)*10));
    translationReading(id,offset);
    S.translationSource=data.source_id;$('translation-panel').hidden=false;const active=['queued','running'].includes(data.status),finished=data.status==='completed';
    const labels={queued:'En attente',running:'Traduction en cours',paused:'En pause',stopped:'Arrêtée',error:'Passage à reprendre',completed:data.done<data.total?'Traduction incomplète':'Traitement terminé'};
    const label=(window.WorkQueuePreview?.workLabel(data,labels[data.status])||labels[data.status]||'État inconnu')+' · '+data.done+'/'+data.total+' passages traduits';
    $('translation-summary').textContent=translationThread&&data.status!=='running'?'Traduction · '+label:label;
    const status=$('translation-status');
    const automaticNotice=translationThread?'Traduction automatique à vérifier avec l’original.':data.notice;
    const notice=data.title+' — '+(data.deferred?'Traduction incomplète : '+data.deferred+' passage(s) à reprendre. L’original reste consultable. ':'')+(data.error||automaticNotice||'')+(data.unreadable?' '+data.unreadable+' passage(s) sans texte extractible : pages illustrées ou reconnaissance de caractères nécessaire.':'')+(data.quality?.warnings?' '+data.quality.warnings+' passage(s) à relire après les contrôles automatiques.':'');
    if(status.textContent!==notice)status.textContent=notice;
    const parts=translationThread?data.parts.filter(part=>part.status!=='pending'||part.quality?.status==='blocked'):data.parts;
    if(translationThread){
      translationMore.hidden=false;
      // Open the tools on arrival in this conversation. Polling respects manual collapse.
      if(translationThread.hidden){
        $('translation-panel').open=true;
        $('chat-messages').append(translationThread);
        translationThread.hidden=false;
      }
    }
    $('translation-start').hidden=true;$('translation-range').hidden=true;$('translation-pause').hidden=!active;$('translation-resume').hidden=active||(finished&&!data.deferred);$('translation-resume').dataset.deferred=String(finished&&!!data.deferred);$('translation-resume').textContent=finished&&data.deferred?'Reprendre les passages à vérifier':'Reprendre avec le modèle choisi';
    translationStop.hidden=finished||data.status==='stopped';translationDelete.hidden=false;
    const meter=$('translation-progress');meter.hidden=false;meter.max=Math.max(1,data.total);meter.value=data.done;meter.setAttribute('aria-label','Passages réellement traduits');
    const pageStatus=(Number.isInteger(data.pages_done)?data.pages_done+' / '+data.pages+' pages ou sections entièrement traduites. ':'')+(data.pages_partial?data.pages_partial+' page(s) commencée(s). ':'')+(active&&data.current_page?'Page ou section en cours : '+data.current_page+'. ':'');
    const textStatus=data.done?'':active?'Le premier passage n’est pas encore prêt. ':'Aucun passage français n’est enregistré. L’original reste consultable. ';
    const groupStatus=parts.length?'Passages '+(parts[0].position+1)+' à '+(parts.at(-1).position+1)+'.':data.done?'Aucun passage prêt dans ce groupe.':'';
    const readingStatus=pageStatus+textStatus+groupStatus;
    if(translationReadingStatus.textContent!==readingStatus)translationReadingStatus.textContent=readingStatus;
    S.translationLastDone=data.last_done_position;
    translationBeginning.disabled=offset===0;
    translationLatest.disabled=!Number.isInteger(data.last_done_position)||Math.floor(data.last_done_position/10)*10===offset;
    if(translationThread){
      translationBeginning.hidden=translationBeginning.disabled;
      translationLatest.hidden=translationLatest.disabled;
    }
    translationReadingActions.hidden=!data.done||(translationThread&&translationBeginning.disabled&&translationLatest.disabled);
    translationDownload.hidden=false;translationDownload.href='/api/translations/'+encodeURIComponent(id)+'/export';
    renderTranslationParts(data,parts);
    $('translation-previous').hidden=offset===0;$('translation-next').hidden=offset+data.parts.length>=data.total;
    document.dispatchEvent(new CustomEvent('survie:translation',{detail:data}));
    if(active&&S.view==='chat')translationTimer=setTimeout(()=>loadTranslation(id,offset),2000);
  }catch(e){if(version===translationVersion&&S.user?.id===owner){$('translation-status').textContent=e.message;if(S.view==='chat'&&e.status!==401&&e.status!==404)translationTimer=setTimeout(()=>loadTranslation(id,offset),5000);}}
}
async function translationAction(action){
  if(translationBusy||S.sourceChanging||!needUser())return;
  if(action==='delete'&&(!S.translation||!confirm('Supprimer ce travail de traduction, ses passages privés et son suivi ? Cette action est définitive. Le document original, la conversation et toute version déjà partagée dans la bibliothèque sont conservés.')))return;
  translationBusy=true;$('translation-start').disabled=true;$('translation-resume').disabled=true;$('translation-pause').disabled=true;
  translationStop.disabled=translationDelete.disabled=true;
  const conversation=S.conversation,owner=S.user.id,identifier=S.translation;const version=translationVersion;
  try{let data;
    if(action==='start'){
      if(!S.source)return;
      const pdf=S.source.id.toLowerCase().split('#page=')[0].endsWith('.pdf');
      const first=pdf?Number($('translation-first').value):1,last=pdf&&$('translation-last').value?Number($('translation-last').value):null;
      if(!Number.isInteger(first)||first<1||first>1200||(last!==null&&(!Number.isInteger(last)||last<first||last>1200)))throw new Error('Vérifiez les numéros des pages à traduire.');
      data=await api('/translations',{source_id:S.source.id,conversation_id:S.conversation,mode:$('chat-mode').value,first_page:first,last_page:last});
      if(version!==translationVersion||conversation!==S.conversation||!S.user)return;
      S.conversation=data.conversation_id;selectReading(S.conversation);$('chat-title').textContent='Traduction : '+data.title;S.source={id:data.source_id,title:data.title};S.sources=[S.source,...selectedSourceChoices().filter(source=>source.id!==S.source.id)];showAssociatedSource();await histories();
    }else if(action==='delete'){
      const result=await api('/translations/'+encodeURIComponent(identifier),undefined,{method:'DELETE'});
      if(S.conversation!==conversation||S.user?.id!==owner||S.translation!==identifier)return;
      clearTranslation();translationReader.dataset.translationId='';
      try{const key='survie-translation-reading:'+owner,saved=JSON.parse(localStorage.getItem(key))||{};delete saved[identifier];localStorage.setItem(key,JSON.stringify(saved));}catch(_){}
      showAssociatedSource();$('translation-panel').open=true;document.dispatchEvent(new CustomEvent('survie:translation-deleted',{detail:{id:identifier,conversation_id:conversation}}));toast(result.notice);return true;
    }else{
      if(!S.translation)return;
      data=await api('/translations/'+encodeURIComponent(S.translation)+'/'+action,action==='resume'?{mode:$('chat-mode').value}:{});
      if(version!==translationVersion||conversation!==S.conversation||!S.user)return;
    }
    if(['start','resume'].includes(action)&&window.WorkQueuePreview?.aiBusy(window.WorkQueuePreview.current?.()))toast('Traduction ajoutée à la file d’attente.');
    await loadTranslation(data.id,action==='start'?0:undefined);$('translation-panel').open=true;document.dispatchEvent(new CustomEvent('survie:translation-command',{detail:{action,id:data.id}}));return true;
  }catch(e){toast(e.message);$('translation-status').textContent=e.message;}
  finally{translationBusy=false;$('translation-start').disabled=!S.source;$('translation-resume').disabled=false;$('translation-pause').disabled=false;translationStop.disabled=translationDelete.disabled=false;refreshSourceChoices();}
}
$('translation-start').onclick=()=>translationAction('start');$('translation-pause').onclick=()=>translationAction('pause');$('translation-resume').onclick=()=>translationAction('resume');
$('translation-previous').onclick=()=>loadTranslation(S.translation,Math.max(0,S.translationOffset-10));$('translation-next').onclick=()=>loadTranslation(S.translation,S.translationOffset+10);

function wholeDocumentTranslation(text){
  const normalized=text.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  return /^(?:(?:peux[- ]tu|peut tu|pourrais[- ]tu)\s+)?(?:me\s+)?tradui(?:s|t|re|sez)\s+(?:moi\s+)?(?:(?:ce|le|tout le)\s+)?(?:document|guide|livre|manuel)(?:\s+(?:entierement|en francais|entier|complet|stp|ici))*[.!?]?$/.test(normalized);
}
async function send(event){
  event.preventDefault();if(!needUser()||S.job||S.sourceChanging||S.sending)return;
  const text=$('chat-input').value.trim();if(!text)return;
  if(S.summaryActive){toast('La synthèse longue est en cours. Mettez-la en pause pour poser une question dans cette conversation.');return;}
  if(S.source&&wholeDocumentTranslation(text)){$('translation-panel').open=true;if(S.translation&&S.translationSource?.split('#page=')[0]===S.source.id.split('#page=')[0]){$('translation-status').textContent='Une traduction existe déjà pour cette conversation. Consultez-la ou reprenez-la ci-dessus.';return;}$('translation-first').value='1';$('translation-last').value='';if(await translationAction('start'))$('chat-input').value='';return;}
  S.sending=true;$('send-question').disabled=true;refreshSourceChoices();
  $('chat-status').textContent='Envoi de la question…';
  try{const data=await api('/questions',{message:text,mode:$('chat-mode').value,domain:$('chat-domain')?.value||'all',conversation_id:S.conversation,source_ids:selectedSourceChoices().map(source=>source.id)});
    if(!S.conversation||!$('chat-messages').querySelector('.message')){
      const messages=$('chat-messages');
      if(translationThread&&!translationThread.hidden)messages.querySelector('.chat-empty')?.remove();
      else{resetChatMessages();$('chat-title').textContent=text.slice(0,80);}
    }S.conversation=data.conversation_id;selectReading(S.conversation);message('user',text);$('chat-messages').scrollTop=$('chat-messages').scrollHeight;rememberReading();$('chat-input').value='';await histories();watch(data.id);
  }catch(e){
    const problem=e.status?e.message:'Impossible de confirmer l’envoi. Votre texte reste dans la zone de saisie.';
    $('chat-status').textContent=problem;toast(problem);$('send-question').disabled=false;
  }
  finally{S.sending=false;refreshSourceChoices();}
}
function watch(id){
  clearTimeout(S.poll);S.job=id;const owner=S.user?.id;refreshSourceChoices();$('cancel-job').hidden=false;$('send-question').disabled=true;const pending=message('assistant','Préparation de la réponse…');
  async function poll(){
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),8000);
    try{const job=await api('/jobs/'+encodeURIComponent(id),undefined,{signal:controller.signal});
      if(S.job!==id||S.user?.id!==owner)return;
      const seconds=Math.round((Date.now()/1000)-job.created);pending.node.querySelector('.message-label').textContent=S.status?.modes.find(p=>p.id===job.mode)?.name||'Assistant';
      document.dispatchEvent(new CustomEvent('survie:job',{detail:{...job,id}}));
      const phase={searching:'Recherche dans la bibliothèque',reading:'Lecture des documents trouvés',illustrating:'Sélection des illustrations originales',referencing:'Ajout des références aux documents consultés',switching:'Changement de modèle en cours, votre question est conservée',loading:'Chargement du modèle',retrying:'Reprise automatique, votre question est conservée',preparing:'Préparation de la réponse par le modèle',writing:'Rédaction de la réponse'}[job.progress?.stage]||'Réponse en cours';
      const read=Number(job.progress?.sources_read||0),found=Number(job.progress?.sources_found||0);const detail=read?` · ${read} source(s) consultée(s)`:found?` · ${found} résultat(s) à examiner`:'';
      const waiting={paused:'Question en attente. La file est en pause.',next:'Question suivante dans le créneau IA.',waiting:'Question en attente de son tour dans le créneau IA.'}[job.queue_state]||'Question en attente dans la file.';
      $('chat-status').textContent=job.status==='queued'?waiting:`${phase}${detail} · ${seconds} s. Vous pouvez continuer à consulter la bibliothèque.`;
      renderText(pending.body,job.answer||(job.status==='queued'?waiting:phase+'…'),job.sources);
      documentaryStatus(pending.tracking,job.documentary);
      if(['done','failed','cancelled','interrupted','incomplete'].includes(job.status)){
        S.job=null;refreshSourceChoices();$('cancel-job').hidden=true;$('send-question').disabled=false;
        $('chat-status').textContent=job.error||(job.status==='incomplete'?'Réponse incomplète : essayez une question plus ciblée.':'Réponse terminée. Vous pouvez ouvrir les sources ou poursuivre.');
        if(!job.answer)renderText(pending.body,job.error||'Aucune réponse finale.',[]);
        if(job.sources.length)pending.node.append(sourceChips(job.sources));await histories();return;
      }
      S.poll=setTimeout(poll,1000);
    }catch(e){
      if(S.job!==id||S.user?.id!==owner||PAGE_CLOSING)return;
      if(!e.status||e.status>=500){
        $('chat-status').textContent='Suivi de la réponse indisponible. Nouvelle tentative automatique.';
        S.poll=setTimeout(poll,3000);
        return;
      }
      S.job=null;refreshSourceChoices();$('cancel-job').hidden=true;$('send-question').disabled=false;$('chat-status').textContent=e.message;
    }finally{clearTimeout(timeout);}
  }poll();
}
function localServiceURL(path,service){const u=new URL(location.href);u.port=service==='webui'?(u.protocol==='https:'?'8444':'3000'):(u.protocol==='https:'?'8445':'8081');u.pathname=path;u.search='';u.hash='';return u.href;}
function memoryBytes(value){return (value/1024**3).toLocaleString('fr-FR',{maximumFractionDigits:1})+' Gio';}
function bytes(value){if(value===null||value===undefined)return 'Taille non renseignée';return value>=1e9?(value/1e9).toFixed(1)+' Go':value>=1e6?(value/1e6).toFixed(1)+' Mo':Math.round(value/1e3)+' Ko';}

let inferenceTimer=null;
async function refreshInference(){
  clearTimeout(inferenceTimer);
  try{
    const data=await api('/inference');S.inference=data;document.dispatchEvent(new CustomEvent('survie:inference',{detail:data}));
    const models=Array.isArray(data.models)?data.models:[],modelsKnown=data.models_available!==false&&data.control_available!==false;
    const banner=$('inference-banner');banner.hidden=!!data.online&&!data.operation;
    banner.replaceChildren(document.createTextNode(data.message+'. '),button('Voir l’état de l’appareil',()=>view('monitor'),'text-button'));
    $('engine-state').textContent=data.message;
    $('engine-detail').textContent=models.length?'Modèle'+(models.length>1?'s':'')+' chargé'+(models.length>1?'s':'')+' : '+models.map(model=>model.name).join(', ')+'.':
      !modelsKnown?'Le modèle réellement chargé n’a pas pu être vérifié.':data.online?'Aucun modèle signalé par le moteur. Le prochain se chargera à votre demande.':'La recherche et la lecture des documents restent accessibles.';
    $('engine-dot').style.background=data.online?'#50855a':'#ad8241';$('engine-controls').hidden=S.user?.role!=='admin';
    $('engine-start').textContent=data.paused?'Forcer le démarrage de l’IA':'Démarrer l’assistant';
    $('engine-start').disabled=!!data.operation||data.online||!data.control_available;
    $('engine-stop').disabled=!!data.operation||!data.online||!data.control_available;
    $('engine-caution').textContent=data.paused?'Forcer la reprise réactive l’IA même en mode jeu et peut ralentir le jeu. Le modèle se chargera à la prochaine question.':'Arrêter le moteur interrompt les réponses en cours et libère sa mémoire.';
    $('engine-error').textContent=data.error||(!data.control_available?'Le service de commande ne répond pas. Les mesures du PC ne sont pas disponibles.':'');
    const grid=$('monitor-stats');grid.replaceChildren();
    function stat(title,value,detail,ratio){
      const card=element('article',undefined,'monitor-stat');card.append(element('span',title,'muted small'),element('strong',value),element('p',detail,'muted small'));
      if(Number.isFinite(ratio)){const meter=element('progress');meter.max=100;meter.value=Math.max(0,Math.min(100,ratio));meter.setAttribute('aria-label',title);card.append(meter);}grid.append(card);
    }
    const ram=data.memory||{};
    if(ram.total)stat('RAM du PC',memoryBytes(ram.used)+' / '+memoryBytes(ram.total),memoryBytes(ram.available)+' disponibles · tous les programmes du PC',100*ram.used/ram.total);
    else stat('RAM du PC','Mesure indisponible','La mémoire du serveur n’a pas pu être relevée.');
    const gpus=Array.isArray(data.gpus)?data.gpus:[];
    for(const gpu of gpus){
      stat('VRAM de la carte graphique',memoryBytes(gpu.used)+' / '+memoryBytes(gpu.total),gpu.name+' · '+memoryBytes(Math.max(0,gpu.total-gpu.used))+' disponibles · tous les usages du PC',100*gpu.used/gpu.total);
      stat('Activité de la carte graphique',Number.isFinite(gpu.utilization)?gpu.utilization+' %':'Mesure indisponible',gpu.name+(Number.isFinite(gpu.temperature)?' · '+gpu.temperature+' °C':''),gpu.utilization);
    }
    if(!gpus.length)stat('VRAM de la carte graphique','Mesure indisponible','Aucune mesure reçue ; cela ne signifie pas que la carte est absente ou inutilisée.');
    stat('Questions en cours',String(data.jobs?.running||0),String(data.jobs?.queued||0)+' en attente');
    const list=$('monitor-models');list.replaceChildren();
    for(const model of models){
      const row=element('div',undefined,'model-monitor-row');
      const detail=[Number.isFinite(model.size_vram)?memoryBytes(model.size_vram)+' en VRAM':null,Number.isFinite(model.size)?memoryBytes(model.size)+' alloués au modèle (RAM et VRAM)':null,Number.isFinite(model.context_length)?'contexte '+model.context_length.toLocaleString('fr-FR')+' tokens':null].filter(Boolean).join(' · ');
      row.append(element('strong',model.name),element('span',detail||'Détails mémoire non communiqués','muted small'));list.append(row);
    }
    if(!models.length)list.append(element('p',modelsKnown?'Aucun modèle signalé par le moteur.':'Impossible de vérifier le modèle chargé. Les mesures sont indisponibles.','muted'));
    $('monitor-updated').textContent='Actualisé à '+new Date().toLocaleTimeString('fr-FR')+' · les mesures du contrôleur peuvent avoir quelques secondes de décalage.';
  }catch(e){document.dispatchEvent(new CustomEvent('survie:inference',{detail:{observation_error:true}}));$('engine-state').textContent='Les mesures sont momentanément indisponibles.';$('monitor-updated').textContent='Actualisation impossible. Les dernières valeurs affichées ne sont plus confirmées.';}
  finally{inferenceTimer=setTimeout(refreshInference,S.view==='monitor'?3000:15000);}
}
async function engineCommand(action){$('engine-start').disabled=true;$('engine-stop').disabled=true;try{await api('/admin/inference/'+action,action==='start'?{force:!!S.inference?.paused}:{});toast(action==='start'?'Démarrage demandé. Le chargement du modèle attendra votre prochaine question.':'Arrêt demandé.');}catch(e){toast(e.message);}await refreshInference();}

async function loadNetwork(){try{const data=await api('/network');const warning=$('connect-warning');warning.hidden=!data.warning;warning.textContent=data.warning||'';if(!data.lan_enabled){warning.hidden=false;warning.textContent='L’accès depuis les autres appareils est désactivé. La personne qui prépare ce PC peut l’activer dans les réglages réseau.';}$('connect-qr').src='/api/network/qr.svg?kind=direct&v='+Date.now();$('connect-address').textContent=data.http_url;$('connect-address').href=data.http_url;$('connect-secure').textContent=data.https_url;$('connect-secure').href=data.https_url;}catch(e){$('connect-warning').hidden=false;$('connect-warning').textContent=e.message;}}
async function loadData(){
  if(S.user?.role==='admin')loadContentManager();
  if(S.user)loadGeography();
  try{const data=await api('/inventory');$('data-summary').replaceChildren();for(const [title,text] of [['Collections',String(data.books.length)],['Guides',String(data.guides.length)],['Modèles locaux',String(data.models.length)]]){const card=element('div',undefined,'data-stat');card.append(element('strong',text),element('span',title));$('data-summary').append(card);}
    for(const [kind,id] of [['books','data-books'],['guides','data-guides'],['models','data-models']]){
      const grid=$(id);grid.replaceChildren();
      for(const item of data[kind]){const card=element('article',undefined,'data-card');card.dataset.collectionId=item.id||'';card.dataset.catalogSearch=[item.id,item.name,item.title,item.description,item.language,item.version,item.family,item.variant].filter(Boolean).join(' ');card.dataset.inventoryReady=String(!!item.ready);card.dataset.family=item.family||item.title||item.name||'';card.dataset.variant=item.variant||'';card.dataset.archiveName=item.archive_name||'';card.append(element('span',item.ready?'Disponible sur cet appareil':'Préparation à vérifier',item.ready?'ready-label':'muted small'),element('h3',item.title||item.name),element('p',[item.language,item.version,bytes(item.bytes)].filter(Boolean).join(' · '),'muted small'));
        if(item.description)card.append(element('p',item.description,'small'));
        if(item.ready&&kind==='books'){const link=element('a','Ouvrir cette collection →','text-button');link.href=localServiceURL(item.url,'kiwix');link.target='_blank';link.rel='noopener';card.append(link);}
        if(item.ready&&kind==='guides')card.append(button('Lire le guide →',()=>readSource(item.id),'text-button'));
        grid.append(card);
      }
      if(!data[kind].length)grid.append(element('div','Aucun élément de ce type n’est encore préparé.','empty-panel'));
    }
    $('data-preparation').textContent=data.note;document.dispatchEvent(new CustomEvent('survie:inventory',{detail:data}));
  }catch(e){$('data-summary').textContent=e.message;}
}
function contentOptions(){return {themes:[...$('content-themes').querySelectorAll('input:checked')].map(e=>e.value),languages:$('content-languages').value.split(','),max_add_gb:Number($('content-budget').value),include_supplements:$('content-supplements').checked};}
function sameContentOptions(a,b){return !!a&&JSON.stringify([...a.themes].sort())===JSON.stringify([...b.themes].sort())&&JSON.stringify([...a.languages].sort())===JSON.stringify([...b.languages].sort())&&a.max_add_gb===b.max_add_gb&&!!a.include_supplements===!!b.include_supplements;}
function renderContentState(){
  if(!contentState)return;
  const data=contentState,busy=['starting','planning','downloading','refreshing'].includes(data.phase),plan=data.plan;
  $('content-fields').disabled=busy||contentCommandBusy;$('content-plan').disabled=busy||contentCommandBusy;
  $('content-message').textContent=data.message||'Choisissez les thèmes, puis cherchez les collections disponibles.';
  const meter=$('content-progress'),progress=data.progress;meter.hidden=data.phase!=='downloading';
  if(progress?.total&&['downloading','paused'].includes(data.phase)){meter.value=100*progress.bytes/progress.total;$('content-message').textContent+=' '+bytes(progress.bytes)+' / '+bytes(progress.total)+'.';}else meter.removeAttribute('value');
  $('content-pause').hidden=!['starting','planning','downloading'].includes(data.phase);$('content-pause').disabled=contentCommandBusy||!!data.pause_requested;
  $('content-download').hidden=!plan||!['planned','paused','error'].includes(data.phase);
  $('content-download').disabled=contentCommandBusy||!plan?.count||!sameContentOptions(data.options,contentOptions());
  $('content-download').textContent=(data.phase==='paused'?'Reprendre le téléchargement':'Télécharger la sélection')+(plan?.count?' · '+bytes(plan.remaining_download_bytes):'');
  $('content-plan-summary').textContent=plan?(data.phase==='completed'?plan.count+' collection(s) téléchargée(s) et vérifiée(s).':plan.count+' nouvelle(s) collection(s) sélectionnée(s) · '+bytes(plan.remaining_download_bytes)+' à transférer lors de la préparation du plan.') : '';
  const names=new Map((data.themes||[]).map(t=>[t.id,t.label]));
  $('content-gaps').textContent=plan?.missing_themes?.length?'Aucune référence repérée dans les catalogues consultés pour : '+plan.missing_themes.map(t=>names.get(t)||t).join(', ')+'.':'';
  const coverage=plan?.learning_coverage||[];$('content-learning').hidden=!coverage.length;$('content-learning-list').replaceChildren();
  for(const area of coverage){const item=element('li');item.append(element('strong',area.label+' : '),document.createTextNode(`${area.references} référence(s) repérée(s), ${area.local_references??'présence inconnue'} présente(s). Sujets à examiner : ${area.skills_to_review.join(', ')}.`));$('content-learning-list').append(item);}
  if(plan?.legacy_selection)$('content-plan-summary').append(document.createTextNode(' Ancien plan : les nouveaux filtres de pertinence ne lui sont pas appliqués. Pour les utiliser, mettez le transfert en pause puis préparez une nouvelle sélection.'));
  $('content-results').hidden=!plan;
  if(plan){
    const labels={selected:data.phase==='completed'?'Téléchargée et vérifiée':'À télécharger',already_local:'Déjà présent',covered_by_full_collection:'Collection complète présente ou sélectionnée',budget_excluded:'Dépasse le plafond choisi',optional_excluded:'Complément non demandé',out_of_scope:'Hors du fonds pratique',metadata_unavailable:'Informations de téléchargement indisponibles',existing_conflict:'Fichier existant conservé',partial_conflict:'Fichier partiel à vérifier'};
    $('content-candidates').replaceChildren();
    for(const item of plan.candidates){const row=element('li');row.append(element('strong',item.title),element('span',labels[item.status]||item.status,'small'),element('span',[item.themes.map(t=>names.get(t)||t).join(', '),bytes(item.bytes||item.estimated_bytes),item.fulltext_index?'':'Consultation directe dans Kiwix'].filter(Boolean).join(' · '),'small muted'));$('content-candidates').append(row);}
  }
}
async function loadContentManager(){
  clearTimeout(contentTimer);if(S.user?.role!=='admin'||S.view!=='data')return;
  try{
    const data=await api('/admin/library');if(S.user?.role!=='admin'||S.view!=='data')return;
    if(!contentInitialized){
      $('content-themes').replaceChildren();const defaults=data.options?.themes||data.themes.map(t=>t.id);
      for(const theme of data.themes){const label=element('label'),input=element('input');input.type='checkbox';input.name='theme';input.value=theme.id;input.checked=defaults.includes(theme.id);label.append(input,element('span',theme.label));$('content-themes').append(label);}
      if(data.options?.themes){$('content-languages').value=data.options.languages.join(',');const budget=$('content-budget');if(![...budget.options].some(o=>Number(o.value)===data.options.max_add_gb)){const option=element('option',data.options.max_add_gb+' Go');option.value=data.options.max_add_gb;budget.append(option);}budget.value=data.options.max_add_gb;}
      $('content-supplements').checked=!!data.options?.include_supplements;contentInitialized=true;
    }
    const previous=contentState?.phase;contentState=data;renderContentState();renderGeoJob(data);
    if(previous&&previous!=='completed'&&data.phase==='completed'){status();loadData();}
    if(['starting','planning','downloading','refreshing'].includes(data.phase))contentTimer=setTimeout(loadContentManager,2000);
  }catch(e){$('content-message').textContent=e.message;$('content-plan').disabled=!contentInitialized;}
}
async function contentAction(action,body){
  if(contentCommandBusy)return;
  contentCommandBusy=true;renderContentState();
  try{await api('/admin/library/'+action,body||{});await loadContentManager();}
  catch(e){$('content-message').textContent=e.message;}
  finally{contentCommandBusy=false;if(contentState)renderGeoJob(contentState);if(contentState){const message=$('content-message').textContent;renderContentState();$('content-message').textContent=message;}}
}
$('content-form').onsubmit=e=>{e.preventDefault();const options=contentOptions();if(!options.themes.length){$('content-message').textContent='Choisissez au moins un thème.';return;}contentAction('plan',options);};
$('content-form').onchange=renderContentState;
$('content-download').onclick=()=>contentAction('download',{id:contentState.id});
$('content-pause').onclick=()=>contentAction('pause');
$('content-refresh').onclick=loadContentManager;

async function loadAdmin(){
  if(S.user?.role!=='admin')return;
  try{const data=await api('/admin/users');$('users-list').replaceChildren();for(const u of data.users){const row=element('div',undefined,'user-entry');const copy=element('span',u.name);copy.append(element('small',u.role==='admin'?'Accès aux réglages':'Profil personnel'));row.append(copy);$('users-list').append(row);}const context=await api('/assistant-context');$('assistant-policy').textContent=context.system;await feedbacks();}catch(e){toast(e.message);}
}

async function feedbacks(){try{const data=await api('/admin/feedback');$('feedback-list').replaceChildren();for(const f of data.feedback){const item=element('article',undefined,'feedback-entry');item.append(element('small',new Date(f.created*1000).toLocaleString('fr-FR')+' · '+f.view,'muted'),element('p',f.content));$('feedback-list').append(item);}if(!data.feedback.length)$('feedback-list').append(element('p','Les premiers retours apparaîtront ici.','muted small'));}catch(e){toast(e.message);}}

document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view));
document.querySelectorAll('[data-search]').forEach(b=>b.onclick=()=>search(b.dataset.search));
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>$(b.dataset.close).close());
window.addEventListener('hashchange',()=>view(location.hash.slice(1)));
$('home-search').onsubmit=e=>{e.preventDefault();search($('home-query').value);};$('library-search').onsubmit=runSearch;
$('menu-toggle').onclick=()=>setMenu(!document.body.classList.contains('nav-open'));$('menu-close').onclick=()=>setMenu(false);$('nav-overlay').onclick=()=>setMenu(false);mobileNav.addEventListener('change',()=>setMenu(false,false));document.addEventListener('keydown',e=>{if(e.key==='Escape')setMenu(false);if(e.key==='Tab'&&document.body.classList.contains('nav-open')){const items=[...$('main-navigation').querySelectorAll('button:not([hidden]),a[href],input,select')].filter(x=>x.offsetParent!==null),first=items[0],last=items.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}});setMenu(false,false);
$('account-button').onclick=auth;$('mobile-account').onclick=auth;$('new-chat').onclick=newConversation;$('chat-reset').onclick=newConversation;
$('engine-start').onclick=()=>engineCommand('start');$('engine-stop').onclick=()=>engineCommand('stop');
$('print-connect').onclick=()=>window.print();$('copy-connect').onclick=async()=>{const text=$('connect-address').href;try{if(navigator.clipboard)await navigator.clipboard.writeText(text);else{const input=element('textarea');input.value=text;document.body.append(input);input.select();const done=document.execCommand('copy');input.remove();if(!done)throw new Error();}toast('Adresse copiée.');}catch(_){toast('Vous pouvez sélectionner et copier l’adresse affichée.');}};
$('conversation-picker').onchange=e=>{if(e.target.value)openConversation(e.target.value);};
$('chat-form').onsubmit=send;$('cancel-job').onclick=async()=>{if(S.job)try{await api('/jobs/'+encodeURIComponent(S.job)+'/cancel',{});}catch(e){toast(e.message);}};
window.addEventListener('storage',event=>{if(event.key==='survie.profile.changed')reloadProfile();});
async function refreshProfileOnReturn(){
  if(PAGE_CLOSING||!S.user||document.hidden||S.profileChecking||S.profileReloading)return;
  S.profileChecking=true;const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),4000);
  PAGE_REQUESTS.add(controller);
  try{
    const response=await fetch('/api/profiles/current',{credentials:'same-origin',signal:controller.signal});
    if(response.ok){
      const profile=await response.json();
      if(!PAGE_CLOSING&&!controller.signal.aborted&&profile.id!==S.user?.id)reloadProfile();
    }
  }catch(_){/* Offline reading remains available. */}
  finally{clearTimeout(timeout);PAGE_REQUESTS.delete(controller);S.profileChecking=false;}
}
window.addEventListener('focus',refreshProfileOnReturn);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshProfileOnReturn();});
setInterval(refreshProfileOnReturn,10000);
$('profile-create-form').onsubmit=async event=>{event.preventDefault();const b=event.submitter;b.disabled=true;try{await api('/profiles',{name:new FormData(event.target).get('name')});localStorage.setItem('survie.profile.changed',String(Date.now()));reloadProfile();}catch(error){$('profile-error').textContent=error.message;}finally{b.disabled=false;}};
$('add-user-form').onsubmit=async event=>{event.preventDefault();const b=event.submitter;b.disabled=true;try{await api('/admin/users',Object.fromEntries(new FormData(event.target)));event.target.reset();$('user-status').textContent='Profil créé. Il est disponible dans le choix de profil.';await loadAdmin();}catch(error){$('user-status').textContent=error.message;}finally{b.disabled=false;}};
$('upload-form').onsubmit=async e=>{e.preventDefault();const b=e.submitter||e.target.querySelector('button[type=submit]');b.disabled=true;$('upload-status').textContent='Ajout et préparation de la recherche…';try{const data=await api('/admin/guides',new FormData(e.target));$('upload-status').textContent='Guide ajouté. Il est disponible dans la recherche et pour l’assistant.';e.target.reset();status();}catch(error){$('upload-status').textContent=error.message;}finally{b.disabled=false;}};
$('feedback-button').onclick=()=>{if(needUser())$('feedback-dialog').showModal();};$('feedback-form').onsubmit=async e=>{e.preventDefault();try{await api('/feedback',{content:new FormData(e.target).get('content'),view:S.view+(S.view==='chat'?' · '+$('chat-mode').selectedOptions[0].textContent:'')});e.target.reset();$('feedback-dialog').close();toast('Merci, votre retour a été enregistré sur cet appareil.');}catch(error){$('feedback-status').textContent=error.message;}};$('refresh-feedback').onclick=feedbacks;
document.querySelectorAll('.native-webui').forEach(a=>a.href=localServiceURL('/','webui'));
window.addEventListener('DOMContentLoaded',()=>{
bindExamples();view(location.hash.slice(1)||'home');status();refreshInference();
api('/profiles/current').then(u=>{S.user=u;S.authReady=true;accountUI();histories();resumeConversation();if(S.view==='library'&&!S.loadingConversation&&!S.conversation&&!new URLSearchParams(location.search).has('document')){const saved=readingState().selected;if(saved)openConversation(saved,{silent:true});}if(S.requestedView){const target=S.requestedView;S.requestedView=null;if($('auth-dialog').open)$('auth-dialog').close();view(target);}}).catch(()=>{S.user=null;S.authReady=true;accountUI();});

});
