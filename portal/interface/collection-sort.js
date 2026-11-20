/* Organise the collections once: main stock, « Autre » or deletion.
   - Mon appareil › Bibliothèque › Organiser les collections: the page itself (placed by settings-layout.js).
   - Collections tab: one summary line, a shortcut and an « Autre » tag on the cards.
   - Mon appareil › Bibliothèque › search preparation: the French Wikipedia classification. */
(() => {
  const ROUTE='appareil/collections';
  const admin=()=>S.user?.role==='admin';
  const normalize=value=>String(value||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();
  const plural=(count,one,many)=>count.toLocaleString('fr-FR')+' '+(count>1?many:one);
  const friendly=error=>error instanceof TypeError||/NetworkError|Failed to fetch|Load failed/i.test(error?.message||'')
    ?'Le PC serveur ne répond pas pour le moment. Vérifiez qu’il est allumé, puis réessayez dans quelques secondes.'
    :error?.message||'Une erreur inattendue est survenue.';

  /* ---------- Collections tab: summary and shortcut ---------- */
  const strip=element('div',undefined,'collection-organize');
  strip.id='collection-organize';
  strip.hidden=true;
  strip.innerHTML='<p id="collection-organize-text"></p><a class="secondary-link" id="collection-organize-open"></a>';
  const shortcut=strip.querySelector('a');
  shortcut.href='#/'+ROUTE;shortcut.dataset.route=ROUTE;shortcut.textContent='Organiser les collections →';
  $('collection-filter-form').after(strip);

  /* ---------- The page ---------- */
  const page=element('article',undefined,'panel organizer');
  page.id='collection-organizer';
  page.innerHTML=`
    <div class="organizer-legend">
      <div data-state="main"><strong><span class="organizer-dot" aria-hidden="true"></span>Fonds principal</strong>
        <span>Consulté en premier par la recherche et l’assistant. Pour ce qui sert vraiment au quotidien.</span></div>
      <div data-state="other"><strong><span class="organizer-dot" aria-hidden="true"></span>Autre</strong>
        <span>Gardé sur l’appareil et lisible normalement. La recherche ne le consulte que si l’on choisit « Autre » ou « Toute la bibliothèque ».</span></div>
      <div data-state="delete"><strong><span class="organizer-dot" aria-hidden="true"></span>Supprimer</strong>
        <span>Efface les fichiers du PC serveur. La collection ne sera plus proposée aux prochains téléchargements.</span></div>
    </div>
    <div id="organizer-browse">
      <div class="organizer-toolbar">
        <label class="organizer-search"><span class="sr-only">Chercher une collection</span>
          <input type="search" id="organizer-filter" maxlength="160" placeholder="Chercher une collection : Wikipédia, cuisine, vidéos…" autocomplete="off"></label>
        <div class="organizer-chips" role="group" aria-label="Afficher">
          <button type="button" data-view="all"></button>
          <button type="button" data-view="main"></button>
          <button type="button" data-view="other"></button>
        </div>
      </div>
      <p id="organizer-status" class="organizer-status" role="status" aria-live="polite"></p>
      <div id="organizer-groups" class="organizer-groups"></div>
      <p class="organizer-empty" id="organizer-empty" hidden></p>
      <div class="organizer-bar" id="organizer-bar" hidden>
        <p id="organizer-selection"></p>
        <div class="organizer-actions">
          <button type="button" class="secondary" data-bulk="main">Fonds principal</button>
          <button type="button" class="secondary" data-bulk="other">Autre</button>
          <button type="button" class="organizer-danger" id="organizer-delete">Supprimer…</button>
          <button type="button" class="quiet" id="organizer-clear">Tout décocher</button>
        </div>
      </div>
      <p class="organizer-foot small muted"><a href="/api/admin/library/collection-sort/export" download="SetupSurvie-tri.json">Exporter ce classement</a>
        pour le réutiliser lors d’une autre installation (champ « Fichier de tri » des téléchargements).</p>
    </div>
    <section id="organizer-confirm" class="organizer-confirm" hidden aria-labelledby="organizer-confirm-title">
      <h3 id="organizer-confirm-title"></h3>
      <ul id="organizer-confirm-names" class="organizer-confirm-names"></ul>
      <p id="organizer-confirm-text"></p>
      <p class="organizer-warning">Les fichiers seront effacés définitivement et ces collections ne seront plus téléchargées.
        Pour les garder sans qu’elles encombrent la recherche, choisissez plutôt « Autre ».</p>
      <details><summary id="organizer-confirm-files"></summary><ul id="organizer-file-list"></ul></details>
      <div class="organizer-actions">
        <button type="button" class="secondary" id="organizer-back">Annuler</button>
        <button type="button" class="organizer-danger is-strong" id="organizer-confirm-delete">Supprimer définitivement</button>
      </div>
    </section>`;
  // settings-layout.js moves this article into its own page.
  document.getElementById('view-settings').append(page);

  let rows=[],view='all',selected=new Set(),busy=false,pending=new Set(),confirmation=null,poll,loaded=false;
  const status=$('organizer-status');
  const say=text=>{status.textContent=text||'';};

  function cardTags(){
    const state=new Map(rows.map(row=>[row.key,row.state]));
    for(const card of document.querySelectorAll('#data-books .data-card')){
      card.querySelector('.collection-tag')?.remove();
      if(state.get(card.dataset.sortKey)!=='other')continue;
      const tag=element('span','Rangée dans Autre','collection-tag');
      tag.title='Lisible normalement ; la recherche ne la consulte que si vous choisissez « Autre » ou « Toute la bibliothèque ».';
      card.querySelector('h3')?.after(tag);
    }
  }
  function summary(){
    const other=rows.filter(row=>row.state==='other').length,main=rows.filter(row=>row.state==='main').length;
    strip.hidden=!rows.length||!admin()&&!other;
    shortcut.hidden=!admin();
    $('collection-organize-text').textContent=other
      ?`Fonds principal : ${plural(main,'collection','collections')} · Autre : ${plural(other,'collection gardée','collections gardées')} de côté, cherchée${other>1?'s':''} seulement à la demande.`
      :`Les ${plural(main,'collection est','collections sont')} dans le fonds principal, consulté par la recherche.`;
  }
  function filtered(){
    const words=normalize($('organizer-filter').value).trim().split(/\s+/).filter(Boolean);
    return rows.filter(row=>row.state!=='excluded'&&(view==='all'||row.state===view)&&
      words.every(word=>normalize([row.title,row.description,...row.files].join(' ')).includes(word)));
  }
  function toggle(row){
    const group=element('div',undefined,'organizer-toggle');
    group.setAttribute('role','group');
    group.setAttribute('aria-label','Classement de '+row.title);
    for(const [state,label] of [['main','Principal'],['other','Autre']]){
      const choice=element('button',label);
      choice.type='button';
      choice.dataset.choice=state;
      choice.setAttribute('aria-pressed',String(row.state===state));
      choice.disabled=busy||pending.has(row.key);
      choice.onclick=()=>{if(row.state!==state)move([row.key],state);};
      group.append(choice);
    }
    return group;
  }
  function rowNode(row){
    const item=element('li',undefined,'organizer-row');
    item.dataset.state=row.state;
    const check=element('input');
    check.type='checkbox';check.checked=selected.has(row.key);check.disabled=busy;
    check.setAttribute('aria-label','Cocher '+row.title);
    check.onchange=()=>{check.checked?selected.add(row.key):selected.delete(row.key);render();};
    const body=element('div',undefined,'organizer-name');
    body.append(element('strong',row.kind==='video'?row.title:row.variant||row.title));
    const meta=[row.kind==='video'?(row.count?plural(row.count,'vidéo','vidéos'):'Vidéos'):'Collection Kiwix',bytes(row.bytes)];
    const line=element('span',meta.join(' · '),'organizer-meta');
    if(row.url){
      const open=element('a','Aperçu ↗');
      open.href=localServiceURL(row.url,'kiwix');open.target='_blank';open.rel='noopener';
      open.title='Ouvrir cette collection dans un nouvel onglet pour voir son contenu';
      line.append(' · ',open);
    }
    body.append(line);
    if(row.description)body.append(element('span',row.description,'organizer-description'));
    const file=element('span',row.files.join(' · '),'organizer-file');
    body.append(file);
    item.append(check,body,toggle(row));
    return item;
  }
  function render(){
    const counts={all:0,main:0,other:0};
    for(const row of rows)if(row.state!=='excluded'){counts.all++;counts[row.state]++;}
    for(const chip of page.querySelectorAll('[data-view]')){
      chip.textContent={all:'Toutes',main:'Fonds principal',other:'Autre'}[chip.dataset.view]+' · '+counts[chip.dataset.view];
      chip.setAttribute('aria-pressed',String(chip.dataset.view===view));
    }
    const shown=filtered(),families=new Map();
    for(const row of shown){
      const family=row.kind==='video'?'Vidéos téléchargées':row.family||row.title;
      if(!families.has(family))families.set(family,[]);
      families.get(family).push(row);
    }
    const ordered=[...families].sort((a,b)=>b[1].reduce((s,r)=>s+r.bytes,0)-a[1].reduce((s,r)=>s+r.bytes,0));
    const fragment=document.createDocumentFragment();
    for(const [family,members] of ordered){
      const section=element('section',undefined,'organizer-group');
      const head=element('div',undefined,'organizer-group-head');
      const all=element('input');
      all.type='checkbox';all.disabled=busy;
      all.checked=members.every(row=>selected.has(row.key));
      all.indeterminate=!all.checked&&members.some(row=>selected.has(row.key));
      all.setAttribute('aria-label','Cocher toute la famille '+family);
      all.onchange=()=>{for(const row of members)all.checked?selected.add(row.key):selected.delete(row.key);render();};
      const title=element('h3',family);
      const size=members.reduce((sum,row)=>sum+row.bytes,0);
      const other=members.filter(row=>row.state==='other').length;
      head.append(all,title,element('span',[plural(members.length,'élément','éléments'),bytes(size),other?other+' dans Autre':''].filter(Boolean).join(' · '),'organizer-meta'));
      const list=element('ul');
      for(const row of members)list.append(rowNode(row));
      section.append(head,list);
      fragment.append(section);
    }
    $('organizer-groups').replaceChildren(fragment);
    const empty=$('organizer-empty');
    empty.hidden=!!shown.length||!loaded;
    empty.textContent=$('organizer-filter').value.trim()?'Aucune collection ne correspond à ces mots.'
      :view==='other'?'Rien n’est rangé dans Autre pour l’instant. Choisissez « Autre » sur les collections à garder de côté.'
      :'Aucune collection sur cet appareil.';
    const chosen=rows.filter(row=>selected.has(row.key));
    $('organizer-bar').hidden=!chosen.length;
    $('organizer-selection').textContent=chosen.length
      ?`${plural(chosen.length,'collection cochée','collections cochées')} · ${bytes(chosen.reduce((sum,row)=>sum+row.bytes,0))}`:'';
    for(const button of page.querySelectorAll('[data-bulk],#organizer-delete,#organizer-clear'))button.disabled=busy||!chosen.length;
  }
  async function refresh(){
    try{
      rows=await api('/library/collection-sort',undefined,{cache:'no-store'});
      loaded=true;
      for(const key of [...selected])if(!rows.some(row=>row.key===key&&row.state!=='excluded'))selected.delete(key);
      summary();cardTags();render();
      if(status.dataset.error){say('');delete status.dataset.error;}
    }catch(error){say(friendly(error));status.dataset.error='1';}
  }
  async function move(keys,state){
    for(const key of keys)pending.add(key);
    const before=new Map(rows.map(row=>[row.key,row.state]));
    for(const row of rows)if(keys.includes(row.key))row.state=state;  // show the choice at once
    render();
    try{
      await api('/admin/library/collection-sort/move',{keys,state});
      say(`${plural(keys.length,'collection placée','collections placées')} dans ${state==='other'?'Autre':'le fonds principal'}.`);
      for(const key of keys)selected.delete(key);
    }catch(error){
      for(const row of rows)if(before.has(row.key))row.state=before.get(row.key);
      say('Classement non enregistré. '+friendly(error));
    }finally{
      for(const key of keys)pending.delete(key);
      await refresh();
    }
  }
  function step(confirming){
    $('organizer-browse').hidden=confirming;
    $('organizer-confirm').hidden=!confirming;
    page.querySelector('.organizer-legend').hidden=confirming;
  }
  async function askDelete(){
    busy=true;render();say('');
    try{
      const chosen=rows.filter(row=>selected.has(row.key)),keys=chosen.map(row=>row.key);
      const preview=await api('/admin/library/collection-sort/preview',{keys});
      if(!preview.files.length)throw Error('Aucun fichier présent à supprimer pour cette sélection.');
      confirmation={keys,token:preview.token};
      $('organizer-confirm-title').textContent=`Supprimer ${plural(keys.length,'collection','collections')} du disque ?`;
      $('organizer-confirm-names').replaceChildren(...chosen.slice(0,12).map(row=>element('li',row.title+' · '+bytes(row.bytes))),
        ...(chosen.length>12?[element('li','… et '+plural(chosen.length-12,'autre','autres'))]:[]));
      $('organizer-confirm-text').textContent=`${bytes(preview.bytes)} seront libérés sur le PC serveur.`;
      $('organizer-confirm-files').textContent=preview.files.length>1?'Voir les '+plural(preview.files.length,'fichier concerné','fichiers concernés'):'Voir le fichier concerné';
      $('organizer-file-list').replaceChildren(...preview.files.map(file=>element('li',file.name.split('/').pop()+' · '+bytes(file.bytes))));
      step(true);
      page.scrollIntoView({block:'start'});
      $('organizer-back').focus();
    }catch(error){say(friendly(error));}
    finally{busy=false;render();}
  }
  async function follow(attempt=0){
    clearTimeout(poll);
    try{
      const job=await api('/admin/library');
      if(job.action==='collection-exclude'&&['starting','refreshing'].includes(job.phase)){
        say('Suppression en cours… Vous pouvez quitter cette page : le suivi reste dans la file d’attente.');
        poll=setTimeout(follow,1800);return;
      }
      await refresh();
      if(job.action==='collection-exclude')say(job.phase==='completed'?(job.message||'Suppression terminée.'):friendly({message:job.message}));
      if(job.phase==='completed')loadData();
    }catch(error){
      if(attempt<10){poll=setTimeout(()=>follow(attempt+1),2000);return;}
      say(friendly(error));
    }
    busy=false;render();
  }
  async function confirmDelete(){
    if(!confirmation)return;
    const button=$('organizer-confirm-delete');
    button.disabled=true;
    try{
      await api('/admin/library/collection-sort/exclude',confirmation);
      selected.clear();confirmation=null;step(false);
      busy=true;render();
      say('Suppression en cours…');
      await follow();
    }catch(error){say(friendly(error));step(false);}
    finally{button.disabled=false;}
  }

  for(const chip of page.querySelectorAll('[data-view]'))chip.onclick=()=>{view=chip.dataset.view;render();};
  for(const button of page.querySelectorAll('[data-bulk]'))button.onclick=()=>move([...selected],button.dataset.bulk);
  $('organizer-filter').oninput=render;
  $('organizer-delete').onclick=askDelete;
  $('organizer-clear').onclick=()=>{selected.clear();render();};
  $('organizer-back').onclick=()=>{confirmation=null;step(false);$('organizer-delete').focus();};
  $('organizer-confirm-delete').onclick=confirmDelete;
  document.addEventListener('survie:inventory',()=>{if(!busy)refresh();});
  // Refresh when the page or the collections tab is opened.
  document.addEventListener('survie:route',event=>{
    const route=event.detail||{};
    summary();  // the profile may have changed since the last load
    if(route.section==='bibliotheque'&&route.tab==='collections'&&!busy)refresh();
    if(route.section==='appareil'&&route.tab==='collections'&&!busy){step(false);refresh();}
    if(route.section==='appareil'&&route.tab==='bibliotheque')showCategory();
  });

  /* ---------- French Wikipedia classification, in the search preparation panel ---------- */
  const category=element('section',undefined,'category-index');
  category.id='category-index';
  category.innerHTML=`
    <h3>Classement de Wikipédia par espace</h3>
    <p class="small">Range chaque article de Wikipédia en français dans <strong>Autonomie et résilience</strong>
      ou <strong>Savoirs et culture</strong>, pour qu’une recherche limitée à un espace soit plus rapide et plus pertinente.
      Il se fait sur le PC serveur, sans Internet ni IA, et se relance seul quand Wikipédia change.
      En attendant, la recherche utilise l’archive complète. Le suivi apparaît aussi dans la file d’attente.</p>
    <p id="category-index-status" role="status"></p>
    <div class="category-progress" id="category-index-meter" hidden><progress id="category-index-progress" max="100"></progress><span id="category-index-percent"></span></div>
    <p id="category-index-counts" class="small muted"></p>
    <div class="actions"><button type="button" class="secondary" id="category-index-start" hidden>Lancer le classement</button>
      <button type="button" class="secondary" id="category-index-pause" hidden>Mettre en pause</button></div>`;
  $('next-index-status').closest('article').append(category);
  const categoryLabels={
    not_prepared:'Pas encore préparé.',
    running:'Classement en cours.',
    completed:'Prêt : la recherche par espace utilise ce classement.',
    outdated:'Wikipédia a changé : le classement doit être refait. Il se relancera automatiquement.',
    paused:'En pause. La reprise repart du dernier point enregistré.',
    interrupted:'Interrompu. La reprise repart du dernier point enregistré.',
    error:'Arrêté sur un problème. La recherche habituelle reste disponible ; vous pouvez reprendre.',
    unavailable:'Aucune archive Wikipédia en français sur cet appareil : rien à classer.'
  };
  const number=value=>Number(value||0).toLocaleString('fr-FR');
  let categoryPoll,categoryFailures=0;
  async function showCategory(){
    clearTimeout(categoryPoll);
    if(document.hidden||category.closest('[hidden]')||!admin()){categoryPoll=setTimeout(showCategory,5000);return;}
    const start=$('category-index-start'),pause=$('category-index-pause');
    let phase='not_prepared';
    try{
      const report=await api('/library/category-index',undefined,{cache:'no-store'});
      const job=await api('/admin/library').catch(()=>null);
      categoryFailures=0;
      const mine=job?.action==='category-index';
      const active=mine&&['starting','downloading'].includes(job.phase);
      phase=active?'running':mine&&job.phase==='error'?'error':mine&&job.phase==='paused'?'paused':report.phase==='running'?'interrupted':report.phase;
      let text=categoryLabels[phase]||categoryLabels.not_prepared;
      if(phase==='completed'&&report.bytes)text+=` ${bytes(report.bytes)} sur le disque · ${Math.max(1,Math.round((report.elapsed_seconds||0)/60))} min pour la dernière préparation.`;
      $('category-index-status').textContent=text;
      const showMeter=['running','paused','interrupted','error'].includes(phase)&&report.total>0;
      $('category-index-meter').hidden=!showMeter;
      if(showMeter){
        const percent=Math.min(100,100*(report.done||0)/report.total);
        $('category-index-progress').value=percent;
        $('category-index-percent').textContent=`${percent.toFixed(percent<10?1:0)} % des articles examinés`;
      }
      const found=report.counts||{};
      $('category-index-counts').textContent=(found.resilience||found.culture)
        ?`${number(found.resilience)} article(s) en Autonomie et résilience · ${number(found.culture)} en Savoirs et culture.`:'';
      const otherJob=job&&!mine&&['starting','planning','downloading','refreshing'].includes(job.phase);
      start.hidden=['running','completed','unavailable'].includes(phase);
      start.disabled=!!otherJob;
      start.title=otherJob?'Une autre préparation est en cours ; réessayez après elle.':'';
      start.textContent=['paused','interrupted','error'].includes(phase)?'Reprendre le classement':phase==='outdated'?'Refaire le classement maintenant':'Lancer le classement';
      pause.hidden=!active;
      pause.disabled=Boolean(job?.pause_requested);
    }catch(error){
      // A single failed poll keeps the last known state; only a lasting failure is shown.
      if(++categoryFailures>=3)$('category-index-status').textContent=friendly(error);
    }
    categoryPoll=setTimeout(showCategory,phase==='running'?3000:10000);
  }
  async function categoryCommand(action,button){
    button.disabled=true;
    try{await api('/admin/library/'+action,{});}
    catch(error){$('category-index-status').textContent=friendly(error);}
    await showCategory();
  }
  $('category-index-start').onclick=()=>categoryCommand('category-index',$('category-index-start'));
  $('category-index-pause').onclick=()=>categoryCommand('pause',$('category-index-pause'));
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)showCategory();});
  showCategory();
})();
