/* All data and actions use the local server. No external assets or browser-stored tokens. */
const $=id=>document.getElementById(id);
const S={view:'home',user:null,conversation:null,source:null,job:null,poll:null,status:null,searchAbort:null};
const EMPTY=$('chat-messages').innerHTML;
const labels={home:'Votre espace',library:'Bibliothèque',chat:'Assistant',data:'Données locales',admin:'Gestion de l’appareil',connect:'Connecter un appareil',monitor:'État de l’appareil',users:'Comptes et accès'};
function element(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
const mobileNav=matchMedia('(max-width:760px)');
function setMenu(open,restore=true){open=!!open&&mobileNav.matches;document.body.classList.toggle('nav-open',open);document.querySelector('.workspace').inert=open;$('menu-toggle').setAttribute('aria-expanded',String(open));$('nav-overlay').hidden=!open;$('main-navigation').inert=mobileNav.matches&&!open;if(open)$('menu-close').focus();else if(restore&&mobileNav.matches)$('menu-toggle').focus();}
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,6500);}
async function api(path,body,options={}){
  const config={credentials:'same-origin',...options};
  if(body!==undefined){config.method='POST';config.body=body instanceof FormData?body:JSON.stringify(body);if(!(body instanceof FormData))config.headers={...config.headers,'Content-Type':'application/json'};}
  const r=await fetch('/api'+path,config);let data;
  try{data=await r.json();}catch(_){throw new Error('Le service ne répond pas. Réessayez dans quelques instants.');}
  if(!r.ok){if(r.status===401&&path!=='/auth/login'){S.user=null;accountUI();}const error=new Error(typeof data.detail==='string'?data.detail:'Vérifiez les informations saisies.');error.status=r.status;throw error;}
  return data;
}
function button(text,action,cls='secondary'){const b=element('button',text,cls);b.type='button';b.addEventListener('click',action);return b;}
function view(name){
  if(!(name in labels))name='home';
  if(['admin','users'].includes(name)&&S.user?.role!=='admin'){if(S.user){toast('Cette page est réservée à l’administrateur.');return;}S.requestedView=name;auth();return;}
  setMenu(false,false);
  S.view=name;
  for(const section of document.querySelectorAll('.view'))section.hidden=section.id!=='view-'+name;
  document.querySelectorAll('.nav-item').forEach(b=>{b.classList.toggle('active',b.dataset.view===name);if(b.dataset.view===name)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
  $('breadcrumb').textContent=labels[name];
  if(location.hash!=='#'+name)history.replaceState(null,'','#'+name);
  if(name==='monitor')refreshInference();if(name==='connect')loadNetwork();if(name==='admin'||name==='users')loadAdmin();if(name==='data')loadData();
  if(name!=='chat')window.scrollTo({top:0,behavior:'instant'});
}
function accountUI(){
  const label=$('account-label');label.replaceChildren();
  label.append(document.createTextNode(S.user?.name||'Se connecter'),element('small',S.user?'Votre compte local':'Retrouver mes conversations'));
  $('mobile-account').textContent=S.user?.name||'Se connecter';$('engine-controls').hidden=S.user?.role!=='admin';$('admin-nav').hidden=S.user?.role!=='admin';$('users-nav').hidden=S.user?.role!=='admin';
  if(S.user&&!S.user.recovery_ready)toast('Pensez à préparer votre code de secours dans « Mon compte ».');
}
function auth(){
  setMenu(false,false);
  if(S.user){$('profile-name').textContent=S.user.name;$('profile-email').textContent=S.user.email;$('recovery-code').hidden=true;$('code-value').textContent='';$('account-dialog').showModal();}
  else{$('login-form').hidden=false;$('recovery-form').hidden=true;$('auth-title').textContent='Heureux de vous retrouver.';$('auth-dialog').showModal();}
}
function needUser(){if(S.user)return true;auth();return false;}
async function histories(){
  const list=$('conversation-list'),picker=$('conversation-picker');list.replaceChildren();picker.replaceChildren(element('option','Retrouver une conversation'));picker.firstChild.value='';
  if(!S.user){list.append(element('p','Connectez-vous pour retrouver vos échanges.','muted small'));picker.hidden=true;return;}
  try{const data=await api('/conversations');for(const c of data.conversations){const row=element('div',undefined,'conversation-row'),remove=button('×',()=>deleteConversation(c),'conversation-delete');remove.setAttribute('aria-label','Supprimer la conversation : '+c.title);remove.title='Supprimer cette conversation';row.append(button(c.title,()=>openConversation(c.id),'conversation-link'),remove);list.append(row);const o=element('option',c.title);o.value=c.id;picker.append(o);}picker.hidden=!data.conversations.length;if(!data.conversations.length)list.append(element('p','Vos premières conversations apparaîtront ici.','muted small'));}catch(e){toast(e.message);}
}
async function deleteConversation(c){
  if(!confirm('Supprimer la conversation « '+c.title+' » et tous ses messages ?'))return;
  try{await api('/conversations/'+encodeURIComponent(c.id),undefined,{method:'DELETE'});if(S.conversation===c.id)newConversation();await histories();toast('Conversation supprimée.');}catch(e){toast(e.message);}
}
function renderText(target,text,sources=[]){
  target.replaceChildren();const lines=String(text).split('\n');let code=null,table=null;
  function inline(parent,line){
    const parts=line.split(/(\[\d+\]|\*\*[^*]+\*\*|`[^`]+`)/g);
    for(const part of parts){
      if(/^\[\d+\]$/.test(part)){const source=sources.find(s=>s.number===Number(part.slice(1,-1)));if(source){parent.append(button(part,()=>readSource(source.id),'citation'));continue;}}
      if(part.startsWith('**')&&part.endsWith('**'))parent.append(element('strong',part.slice(2,-2)));
      else if(part.startsWith('`')&&part.endsWith('`'))parent.append(element('code',part.slice(1,-1)));
      else parent.append(document.createTextNode(part));
    }
  }
  for(const line of lines){
    if(line.startsWith('```')){if(code)code=null;else{code=element('pre');target.append(code);}continue;}
    if(code){code.append(document.createTextNode(line+'\n'));continue;}
    if(/^\s*\|?\s*:?-{2,}/.test(line))continue;
    if(line.trim().startsWith('|')&&line.trim().endsWith('|')){if(!table){const wrap=element('div');wrap.style.overflowX='auto';table=element('table');wrap.append(table);target.append(wrap);}const row=element('tr');line.trim().slice(1,-1).split('|').forEach(t=>{const cell=element('td');inline(cell,t.trim());row.append(cell);});table.append(row);continue;}
    table=null;if(!line.trim())continue;
    const node=element(/^#{1,3} /.test(line)?'h3':'p');inline(node,line.replace(/^#{1,3} /,''));target.append(node);
  }
}
function message(role,text,sources=[],profile=''){
  const node=element('article',undefined,'message message-'+role);node.append(element('div',role==='user'?'Vous':(profile||'Assistant'),'message-label'));
  const body=element('div');renderText(body,text,sources);node.append(body);
  if(sources.length){const refs=element('div',undefined,'source-chips');for(const source of sources)refs.append(button(`[${source.number}] ${source.title}`,()=>readSource(source.id)));node.append(refs);}
  $('chat-messages').append(node);return {node,body};
}
function newConversation(){
  if(S.job){toast('Attendez la réponse ou annulez la demande avant d’ouvrir une autre conversation.');view('chat');return;}
  S.conversation=null;S.source=null;$('chat-source').hidden=true;$('chat-title').textContent='Une question ? Prenons le temps de comprendre.';$('chat-messages').innerHTML=EMPTY;bindExamples();view('chat');
}
async function openConversation(id){
  if(S.job){toast('Une demande est en cours. Vous pouvez l’annuler pour changer de conversation.');return;}
  try{const data=await api('/conversations/'+encodeURIComponent(id));S.conversation=id;S.source=null;$('chat-source').hidden=true;$('chat-title').textContent=data.title;$('chat-messages').replaceChildren();for(const m of data.messages)message(m.role,m.content,m.sources,m.model?(({rapide:'Réponse rapide',moyenne:'Réponse moyenne',approfondie:'Réponse approfondie'}[m.mode]||'Comparaison')+' · '+m.model):'');view('chat');if(data.jobs.length)watch(data.jobs[0].id);}catch(e){toast(e.message);}
}
function bindExamples(){document.querySelectorAll('[data-question]').forEach(b=>b.onclick=()=>{$('chat-input').value=b.dataset.question;$('chat-input').focus();});}
async function status(){
  try{S.status=await api('/status');const modes=$('chat-mode'),selected=modes.value;modes.replaceChildren();for(const category of ['recommended','comparison']){const group=element('optgroup');group.label=category==='recommended'?'Choix conseillés pour les essais':'Autres modèles à comparer';for(const profile of S.status.modes.filter(x=>x.category===category)){const option=element('option',profile.name);option.value=profile.id;group.append(option);}modes.append(group);}if([...modes.options].some(o=>o.value===selected))modes.value=selected;$('library-count').textContent=`${S.status.books.length} collections · ${S.status.guides} guides`;
    const grid=$('collections');grid.replaceChildren();for(const book of S.status.books){const b=button('',()=>{view('data');},'collection');b.append(element('span','▤','book-icon'));const copy=element('span');copy.append(element('strong',book.title),element('small',book.language==='fra'?'Français · disponible hors ligne':'Anglais · disponible hors ligne'));b.append(copy);grid.append(b);}
  }catch(e){$('service-status').textContent='Service momentanément indisponible';toast(e.message);}
}
function search(query){$('library-query').value=query;view('library');runSearch();}
async function runSearch(event){
  event?.preventDefault();const q=$('library-query').value.trim();if(!q)return;
  S.searchAbort?.abort();S.searchAbort=new AbortController();$('search-message').textContent='Recherche dans vos documents…';$('reader').hidden=true;document.querySelector('.reading-layout').classList.remove('reading');$('search-results').replaceChildren();
  try{const data=await api('/search?q='+encodeURIComponent(q)+'&language='+encodeURIComponent($('search-language').value),undefined,{signal:S.searchAbort.signal});
    $('search-message').textContent=`${data.results.length} résultat(s) pour « ${q} »`;
    for(const result of data.results){const node=element('article',undefined,'result');node.dataset.source=result.id;node.append(element('div',`${result.kind} · ${{fra:'Français',fr:'Français',eng:'Anglais',en:'Anglais'}[result.language]||'Autre langue'}`,'result-meta'),element('h3',result.title),element('p',result.excerpt),button('Lire le document →',()=>readSource(result.id)));$('search-results').append(node);}
    if(!data.results.length)$('search-results').append(element('div','Aucun résultat. Essayez un autre mot, une formulation plus courte ou une autre langue.','empty-panel'));
  }catch(e){if(e.name!=='AbortError')$('search-message').textContent=e.message;}
}
function documentText(source){let text=String(source.text||'');if(/^guide:(?:WIKI-FR-|BOOK-EN-)/.test(source.id)&&text.startsWith('Identifiant de source : ')){const end=text.indexOf('\n\n');if(end>=0)text=text.slice(end+2);}const lines=text.split('\n'),norm=x=>x.trim().replace(/[’‘]/g,"'").toLocaleLowerCase();while(lines.length&&(!lines[0].trim()||norm(lines[0])===norm(source.title)))lines.shift();return lines.join('\n');}
function renderDocument(target,source){const text=documentText(source);if(!text.trim()){target.textContent='Cet aperçu ne contient pas de texte lisible. Ouvrez le document d’origine pour le consulter.';return;}for(const line of text.split('\n')){if(!line.trim())continue;const paragraph=element('p',line);target.append(paragraph);}}
async function readSource(id){
  view('library');document.querySelectorAll('.result').forEach(node=>node.classList.toggle('selected',node.dataset.source===id));S.reader=id;const reader=$('reader');reader.hidden=false;reader.replaceChildren(element('p','Ouverture du document…','muted'));
  document.querySelector('.reading-layout').classList.add('reading');
  try{const source=await api('/source?id='+encodeURIComponent(id));if(S.reader!==id)return;reader.replaceChildren();
    const actions=element('div',undefined,'reader-actions');actions.append(button('← Résultats',()=>{reader.hidden=true;document.querySelector('.reading-layout').classList.remove('reading');},'secondary'),button('Poser une question sur ce document',()=>askSource(source)));
    if(S.conversation)actions.append(button('Revenir à la conversation',()=>view('chat'),'text-button'));
    reader.append(actions,element('div',source.id.startsWith('guide:WIKI-FR-')?'EXTRAIT DE WIKIPÉDIA':source.id.startsWith('guide:BOOK-EN-')?'EXTRAIT DE WIKILIVRES':source.kind==='guide'?'GUIDE LOCAL':'ARTICLE DE LA BIBLIOTHÈQUE','eyebrow'),element('h2',source.title));
    if(source.images?.length){const images=element('div',undefined,'reader-images');for(const img of source.images.slice(0,4)){const e=element('img');e.src='/api/media?id='+encodeURIComponent(img.id);e.alt=img.alt;e.loading='lazy';images.append(e);}reader.append(images);}
    if(source.provenance||source.licence){const details=element('details',undefined,'source-details');details.append(element('summary','Origine et licence du document'));if(source.provenance)details.append(element('p',source.provenance));if(source.licence)details.append(element('p',source.licence));reader.append(details);}const body=element('div',undefined,'reader-body');renderDocument(body,source);reader.append(body);
    if(source.preview)reader.append(element('p','Aperçu du début du livre. La recherche retrouve aussi les pages suivantes dont le texte est lisible. Ouvrez le PDF pour consulter l’ensemble des pages et illustrations.','muted small'));
    const original=element('a',source.id.includes('.pdf')?'Lire le PDF illustré →':'Ouvrir le document d’origine →','secondary-link');
    const archiveLink=/^guide:(?:WIKI-FR-|BOOK-EN-)/.test(source.id)?source.text.match(/Original illustré local : (https?:\/\/[^\s]+)/):null;if(archiveLink){try{const path=new URL(archiveLink[1]).pathname;if(path.startsWith('/content/')){original.href=localServiceURL(path,'kiwix');original.textContent='Voir la page illustrée d’origine →';}}catch(_){}}if(!original.hasAttribute('href')&&source.id.startsWith('guide:'))original.href=source.url;else if(!original.hasAttribute('href')){original.href=localServiceURL(source.url,'kiwix');}original.target='_blank';original.rel='noopener';actions.append(original);
  }catch(e){reader.replaceChildren(element('p',e.message,'error'));}
}
function askSource(source){
  if(S.job){toast('Attendez la réponse en cours ou annulez-la.');return;}
  newConversation();S.source=source;const node=$('chat-source');node.replaceChildren(element('span','Document associé : '+source.title),button('Retirer',()=>{S.source=null;node.hidden=true;}));node.hidden=false;view('chat');$('chat-input').focus();
}
async function send(event){
  event.preventDefault();if(!needUser()||S.job)return;
  const text=$('chat-input').value.trim();if(!text)return;
  $('send-question').disabled=true;
  try{const data=await api('/questions',{message:text,mode:$('chat-mode').value,conversation_id:S.conversation,source_id:S.source?.id||null});
    if(!S.conversation){$('chat-messages').replaceChildren();$('chat-title').textContent=text.slice(0,80);}S.conversation=data.conversation_id;message('user',text);$('chat-input').value='';await histories();watch(data.id);
  }catch(e){toast(e.message);$('send-question').disabled=false;}
}
function watch(id){
  clearTimeout(S.poll);S.job=id;$('cancel-job').hidden=false;$('send-question').disabled=true;const pending=message('assistant','Préparation de la réponse…');
  async function poll(){
    try{const job=await api('/jobs/'+encodeURIComponent(id));const seconds=Math.round((Date.now()/1000)-job.created);pending.node.querySelector('.message-label').textContent=S.status?.modes.find(p=>p.id===job.mode)?.name||'Assistant';
      $('chat-status').textContent=job.status==='queued'?'Une autre demande est en cours. La vôtre est dans la file.':`Réponse en cours · ${seconds} s. Vous pouvez continuer à consulter la bibliothèque.`;
      renderText(pending.body,job.answer||(job.status==='queued'?'En attente de son tour…':'L’assistant réfléchit ou consulte les documents…'),job.sources);
      if(['done','failed','cancelled','interrupted','incomplete'].includes(job.status)){
        S.job=null;$('cancel-job').hidden=true;$('send-question').disabled=false;
        $('chat-status').textContent=job.error||(job.status==='incomplete'?'Réponse incomplète : essayez une question plus ciblée.':'Réponse terminée. Vous pouvez ouvrir les sources ou poursuivre.');
        if(!job.answer)renderText(pending.body,job.error||'Aucune réponse finale.',[]);
        if(job.sources.length){const chips=element('div',undefined,'source-chips');for(const s of job.sources)chips.append(button(`[${s.number}] ${s.title}`,()=>readSource(s.id)));pending.node.append(chips);}await histories();return;
      }
      S.poll=setTimeout(poll,1000);
    }catch(e){S.job=null;$('cancel-job').hidden=true;$('send-question').disabled=false;$('chat-status').textContent=e.message;}
  }poll();
}
function localServiceURL(path,service){const u=new URL(location.href);u.port=service==='webui'?(u.protocol==='https:'?'8444':'3000'):(u.protocol==='https:'?'8445':'8081');u.pathname=path;u.search='';u.hash='';return u.href;}
function memoryBytes(value){return (value/1024**3).toLocaleString('fr-FR',{maximumFractionDigits:1})+' Gio';}
function bytes(value){if(value===null||value===undefined)return 'Taille non renseignée';return value>=1e9?(value/1e9).toFixed(1)+' Go':value>=1e6?(value/1e6).toFixed(1)+' Mo':Math.round(value/1e3)+' Ko';}

let inferenceTimer=null;
async function refreshInference(){clearTimeout(inferenceTimer);try{const data=await api('/inference');S.inference=data;const banner=$('inference-banner');banner.hidden=!!data.online&&!data.operation;banner.replaceChildren(document.createTextNode(data.message+'. '),button('Voir l’état de l’appareil',()=>view('monitor'),'text-button'));$('engine-state').textContent=data.message;$('engine-detail').textContent=data.online?(data.models.length?'Le modèle reste chargé entre les questions pour répondre plus vite.':'Aucun modèle chargé. Le premier démarrera lorsque vous poserez une question.'):'La recherche et la lecture des documents fonctionnent toujours.';$('engine-dot').style.background=data.online?'#50855a':'#ad8241';$('engine-controls').hidden=S.user?.role!=='admin';$('engine-start').textContent=data.paused?'Forcer le démarrage de l’IA':'Démarrer l’assistant';$('engine-start').disabled=!!data.operation||data.online||!data.control_available;$('engine-stop').disabled=!!data.operation||!data.online||!data.control_available;$('engine-caution').textContent=data.paused?'Forcer la reprise réactive l’IA même en mode jeu et peut ralentir le jeu. Le modèle se chargera à la prochaine question.':'Arrêter le moteur interrompt les réponses en cours et libère sa mémoire.';$('engine-error').textContent=data.error||(!data.control_available?'Le service de commande ne répond pas. Utilisez le lanceur sur le PC serveur.':'');const grid=$('monitor-stats');grid.replaceChildren();function stat(title,value,detail,ratio){const card=element('article',undefined,'monitor-stat');card.append(element('span',title,'muted small'),element('strong',value),element('p',detail,'muted small'));if(Number.isFinite(ratio)){const meter=element('progress');meter.max=100;meter.value=Math.max(0,Math.min(100,ratio));meter.setAttribute('aria-label',title);card.append(meter);}grid.append(card);}for(const gpu of data.gpus){stat('Mémoire vidéo',memoryBytes(gpu.used)+' / '+memoryBytes(gpu.total),gpu.name,100*gpu.used/gpu.total);stat('Activité de la carte graphique',gpu.utilization+' %',gpu.temperature+' °C',gpu.utilization);}if(data.memory.total)stat('Mémoire du PC',memoryBytes(data.memory.used)+' / '+memoryBytes(data.memory.total),'RAM utilisée par tous les programmes',100*data.memory.used/data.memory.total);if(data.disk.total)stat('Espace libre du volume',bytes(data.disk.free),'Capacité du volume : '+bytes(data.disk.total),100*data.disk.used/data.disk.total);stat('Questions en cours',String(data.jobs.running||0),String(data.jobs.queued||0)+' en attente');const models=$('monitor-models');models.replaceChildren();for(const model of data.models){const row=element('div',undefined,'model-monitor-row');row.append(element('strong',model.name),element('span',bytes(model.size_vram)+' en mémoire vidéo · contexte '+model.context_length+' tokens','muted small'));models.append(row);}if(!data.models.length)models.append(element('p','Aucun modèle chargé.','muted'));$('monitor-updated').textContent='Dernière mesure : '+new Date().toLocaleTimeString('fr-FR');}catch(e){$('engine-state').textContent='Les mesures sont momentanément indisponibles.';}finally{inferenceTimer=setTimeout(refreshInference,S.view==='monitor'?3000:15000);}}
async function engineCommand(action){$('engine-start').disabled=true;$('engine-stop').disabled=true;try{await api('/admin/inference/'+action,action==='start'?{force:!!S.inference?.paused}:{});toast(action==='start'?'Démarrage demandé. Le chargement du modèle attendra votre prochaine question.':'Arrêt demandé.');}catch(e){toast(e.message);}await refreshInference();}

async function loadNetwork(){try{const data=await api('/network');const warning=$('connect-warning');warning.hidden=!data.warning;warning.textContent=data.warning||'';if(!data.lan_enabled){warning.hidden=false;warning.textContent='L’accès depuis les autres appareils est désactivé. La personne qui prépare ce PC peut l’activer dans les réglages réseau.';}$('connect-qr').src='/api/network/qr.svg?kind=direct&v='+Date.now();$('connect-address').textContent=data.http_url;$('connect-address').href=data.http_url;$('connect-secure').textContent=data.https_url;$('connect-secure').href=data.https_url;}catch(e){$('connect-warning').hidden=false;$('connect-warning').textContent=e.message;}}
async function loadData(){
  try{const data=await api('/inventory');$('data-summary').replaceChildren();for(const [title,text] of [['Collections',String(data.books.length)],['Guides',String(data.guides.length)],['Modèles locaux',String(data.models.length)]]){const card=element('div',undefined,'data-stat');card.append(element('strong',text),element('span',title));$('data-summary').append(card);}
    for(const [kind,id] of [['books','data-books'],['guides','data-guides'],['models','data-models']]){
      const grid=$(id);grid.replaceChildren();
      for(const item of data[kind]){const card=element('article',undefined,'data-card');card.append(element('span',item.ready?'Disponible sur cet appareil':'Préparation à vérifier',item.ready?'ready-label':'muted small'),element('h3',item.title||item.name),element('p',[item.language,item.version,bytes(item.bytes)].filter(Boolean).join(' · '),'muted small'));
        if(item.description)card.append(element('p',item.description,'small'));
        if(item.ready&&kind==='books'){const link=element('a','Ouvrir cette collection →','text-button');link.href=localServiceURL(item.url,'kiwix');link.target='_blank';link.rel='noopener';card.append(link);}
        if(item.ready&&kind==='guides')card.append(button('Lire le guide →',()=>readSource(item.id),'text-button'));
        grid.append(card);
      }
      if(!data[kind].length)grid.append(element('div','Aucun élément de ce type n’est encore préparé.','empty-panel'));
    }
    $('data-preparation').textContent=data.note;
  }catch(e){$('data-summary').textContent=e.message;}
}
function passwordDialog(name){return new Promise(resolve=>{const dialog=element('dialog'),form=element('form'),input=element('input'),label=element('label','Nouveau mot de passe (8 caractères minimum)');input.type='password';input.autocomplete='new-password';input.required=true;input.minLength=8;label.append(input);const save=element('button','Changer le mot de passe');save.type='submit';form.append(element('h2','Compte de '+name),label,save,button('Annuler',()=>dialog.close(),'secondary'));form.onsubmit=e=>{e.preventDefault();resolve(input.value);dialog.close();};dialog.addEventListener('close',()=>{dialog.remove();resolve(null);},{once:true});dialog.append(form);document.body.append(dialog);dialog.showModal();});}
async function loadAdmin(){
  if(S.user?.role!=='admin')return;
  try{const data=await api('/admin/users');$('users-list').replaceChildren();for(const u of data.users){const row=element('div',undefined,'user-entry');const copy=element('span',u.name);copy.append(element('small',u.email+' · '+(u.role==='admin'?'administrateur':'lecteur')));row.append(copy,button('Changer le mot de passe',async()=>{const pass=await passwordDialog(u.name);if(!pass)return;try{await api('/admin/users/'+encodeURIComponent(u.id)+'/password',{password:pass});toast('Mot de passe changé. Les anciennes sessions ont été fermées.');if(u.id===S.user.id){S.user=null;accountUI();auth();}}catch(e){toast(e.message);}},'secondary'));$('users-list').append(row);}const context=await api('/assistant-context');$('assistant-policy').textContent=context.system;await feedbacks();}catch(e){toast(e.message);}
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
$('forgot').onclick=()=>{$('login-form').hidden=true;$('recovery-form').hidden=false;$('auth-title').textContent='Récupérer mon compte.';};$('back-login').onclick=()=>{$('login-form').hidden=false;$('recovery-form').hidden=true;$('auth-title').textContent='Heureux de vous retrouver.';};
$('login-form').onsubmit=async e=>{e.preventDefault();const b=e.submitter||e.target.querySelector('button[type="submit"]');b.disabled=true;$('login-error').textContent='';try{S.user=await api('/auth/login',Object.fromEntries(new FormData(e.target)));$('auth-dialog').close();e.target.reset();accountUI();await histories();if(S.requestedView){const target=S.requestedView;S.requestedView=null;view(target);}toast('Vous êtes connecté.');}catch(error){$('login-error').textContent=error.message;}finally{b.disabled=false;}};
$('recovery-form').onsubmit=async e=>{e.preventDefault();const b=e.submitter||e.target.querySelector('button[type=submit]');b.disabled=true;try{const data=await api('/auth/recover',Object.fromEntries(new FormData(e.target)));S.user=data.user;$('auth-dialog').close();accountUI();await histories();auth();$('code-value').textContent=data.code;$('recovery-code').hidden=false;e.target.reset();toast('Mot de passe changé. Conservez votre nouveau code de secours.');}catch(error){$('recovery-error').textContent=error.message;}finally{b.disabled=false;}};
$('logout').onclick=async()=>{try{await api('/auth/logout',{});}catch(_){}S.user=null;S.conversation=null;clearTimeout(S.poll);S.job=null;$('account-dialog').close();accountUI();histories();newConversation();view('home');};
$('make-code').onclick=async()=>{if(S.user.recovery_ready&&!confirm('Le code précédent ne fonctionnera plus. Créer un nouveau code ?'))return;try{const data=await api('/auth/recovery-code',{});$('code-value').textContent=data.code;$('recovery-code').hidden=false;S.user.recovery_ready=true;}catch(e){$('account-error').textContent=e.message;}};
$('print-code').onclick=()=>{const w=window.open('','_blank','width=700,height=600');if(!w){toast('Autorisez l’ouverture de la fiche pour l’imprimer.');return;}const d=w.document;d.title='Fiche de secours SetupSurvie';d.body.append(element('h1','SetupSurvie — fiche de secours'),element('p','Identifiant : '+S.user.email),element('h2',$('code-value').textContent),element('p','Pour récupérer le compte : ouvrez l’accueil, choisissez Se connecter puis Mot de passe oublié. Le code fonctionne sans Internet et une seule fois. Conservez cette fiche séparément de l’appareil.'),element('p','Adresse locale actuelle : '+location.origin));w.print();};
$('upload-form').onsubmit=async e=>{e.preventDefault();const b=e.submitter||e.target.querySelector('button[type=submit]');b.disabled=true;$('upload-status').textContent='Ajout et préparation de la recherche…';try{const data=await api('/admin/guides',new FormData(e.target));$('upload-status').textContent='Guide ajouté. Il est disponible dans la recherche et pour l’assistant.';e.target.reset();status();}catch(error){$('upload-status').textContent=error.message;}finally{b.disabled=false;}};
$('add-user-form').onsubmit=async e=>{e.preventDefault();try{await api('/admin/users',Object.fromEntries(new FormData(e.target)));$('user-status').textContent='Compte lecteur créé.';e.target.reset();loadAdmin();}catch(error){$('user-status').textContent=error.message;}};
$('feedback-button').onclick=()=>{if(needUser())$('feedback-dialog').showModal();};$('feedback-form').onsubmit=async e=>{e.preventDefault();try{await api('/feedback',{content:new FormData(e.target).get('content'),view:S.view+(S.view==='chat'?' · '+$('chat-mode').selectedOptions[0].textContent:'')});e.target.reset();$('feedback-dialog').close();toast('Merci, votre retour a été enregistré sur cet appareil.');}catch(error){$('feedback-status').textContent=error.message;}};$('refresh-feedback').onclick=feedbacks;
let recorder=null,tracks=[],chunks=[];
$('dictate').onclick=async()=>{
  if(!needUser())return;
  if(recorder?.state==='recording'){recorder.stop();return;}
  if(!window.isSecureContext||!navigator.mediaDevices?.getUserMedia){toast('Le micro nécessite l’adresse HTTPS de l’appareil. Vous pouvez aussi écrire votre question.');return;}
  try{const stream=await navigator.mediaDevices.getUserMedia({audio:true});tracks=stream.getTracks();chunks=[];
    const mime=['audio/webm','audio/mp4'].find(t=>MediaRecorder.isTypeSupported(t));recorder=new MediaRecorder(stream,mime?{mimeType:mime}:{});
    recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};recorder.onstop=async()=>{tracks.forEach(t=>t.stop());$('dictate').textContent='● Dicter';if(!chunks.length)return;$('chat-status').textContent='Transcription de votre dictée…';const type=recorder.mimeType;const data=new FormData();data.append('file',new Blob(chunks,{type}),'dictee.'+(type.includes('mp4')?'mp4':'webm'));try{const result=await api('/transcribe',data);$('chat-input').value+=($('chat-input').value?' ':'')+result.text;$('chat-status').textContent=result.text?'Relisez la dictée, puis envoyez votre question.':'Aucune parole reconnue. Essayez de nouveau ou écrivez votre question.';}catch(e){$('chat-status').textContent=e.message;}};
    recorder.start();$('dictate').textContent='■ Terminer la dictée';setTimeout(()=>{if(recorder?.state==='recording')recorder.stop();},120000);
  }catch(e){tracks.forEach(t=>t.stop());toast('Le micro n’est pas accessible. Vérifiez son autorisation ou écrivez votre question.');}
};
window.addEventListener('pagehide',()=>tracks.forEach(t=>t.stop()));
document.querySelectorAll('.native-webui').forEach(a=>a.href=localServiceURL('/','webui'));
bindExamples();view(location.hash.slice(1)||'home');status();refreshInference();
api('/auth/me').then(u=>{S.user=u;accountUI();histories();if(S.requestedView){const target=S.requestedView;S.requestedView=null;if($('auth-dialog').open)$('auth-dialog').close();view(target);}}).catch(()=>{S.user=null;accountUI();});
