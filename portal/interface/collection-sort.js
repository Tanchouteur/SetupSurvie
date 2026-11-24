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
    <p id="organizer-delete-status" class="organizer-status" role="status" aria-live="polite"></p>
    <a id="organizer-delete-queue" class="secondary-link" href="#/file" data-route="file" hidden>Voir la file d’attente →</a>
    <div id="organizer-browse">
      <details id="organizer-reference" class="organizer-group">
        <summary class="organizer-group-head">Comparer avec la bibliothèque de référence</summary>
        <div class="organizer-reference-content">
          <p id="organizer-reference-status" class="organizer-status" role="status"></p>
          <ul id="organizer-reference-rows"></ul>
          <div class="organizer-actions">
            <button type="button" class="secondary" id="organizer-reference-refresh">Actualiser</button>
            <button type="button" class="secondary" id="organizer-reference-restore">Choisir les changements à appliquer…</button>
          </div>
          <section id="organizer-reference-confirm" class="organizer-confirm" hidden aria-labelledby="organizer-reference-confirm-title">
            <h3 id="organizer-reference-confirm-title">Choisir les changements à appliquer</h3>
            <p>Cochez seulement ce que vous voulez. Les lignes non cochées restent telles quelles. Le classement s’applique tout de suite, sans attendre les téléchargements.</p>
            <div id="organizer-reference-confirm-changes"></div>
            <p id="organizer-reference-confirm-space" role="status"></p>
            <div class="organizer-actions">
              <button type="button" class="secondary" id="organizer-reference-cancel">Fermer</button>
              <button type="button" class="organizer-danger is-strong" id="organizer-reference-apply">Appliquer les changements cochés</button>
            </div>
          </section>
        </div>
      </details>
      <div class="organizer-toolbar">
        <label class="organizer-search"><span class="sr-only">Chercher une collection</span>
          <input type="search" id="organizer-filter" maxlength="160" placeholder="Chercher une collection : Wikipédia, cuisine, vidéos…" autocomplete="off"></label>
        <div class="organizer-chips" role="group" aria-label="Afficher">
          <button type="button" data-view="all"></button>
          <button type="button" data-view="main"></button>
          <button type="button" data-view="other"></button>
        </div>
      </div>
      <div class="organizer-subbar"><p id="organizer-status" class="organizer-status" role="status" aria-live="polite"></p>
        <button type="button" class="text-button" id="organizer-expand" hidden>Tout déplier</button></div>
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
  const openGroups=new Set();  // families are folded until opened
  const status=$('organizer-status');
  const say=text=>{status.textContent=text||'';};
  const reference=$('organizer-reference');
  const referenceRefresh=$('organizer-reference-refresh');
  const referenceStatus=$('organizer-reference-status');
  const referenceJobs=new Set();
  const restore=$('organizer-reference-restore');
  const restorePanel=$('organizer-reference-confirm');
  const restoreApply=$('organizer-reference-apply');
  let restorationPlan=null;
  const referenceLabels={
    missing:'À télécharger', size_mismatch:'Taille différente', hash_mismatch:'Empreinte différente',
    other_edition:'Autre édition', extra:'Hors référence',
    main:'Fonds principal', other:'Autre', excluded:'Exclue'
  };

  async function refreshReference(){
    if(referenceRefresh.disabled||!admin())return;
    referenceRefresh.disabled=true;
    referenceStatus.textContent='Comparaison en cours…';
    try{
      const report=await api('/admin/library/reference',undefined,{cache:'no-store'});
      const differences=report.archives.filter(row=>!['size_matches','ok'].includes(row.status)||row.state!==row.expected_state);
      const titles=new Map(report.archives.filter(row=>row.title).map(row=>[row.archive,row.title]));
      $('organizer-reference-rows').replaceChildren(...differences.map(row=>{
        const entry=element('li',undefined,'organizer-reference-row');
        entry.dataset.status=row.status;
        const name=element('div',undefined,'organizer-name');
        name.append(element('strong',row.title||titles.get(row.expected)||row.archive));
        if((row.title||row.expected)&&row.archive)name.append(element('span',row.archive,'organizer-file'));
        const note=[referenceLabels[row.status]];
        if(row.state!==row.expected_state&&row.expected_state)note.push(`${referenceLabels[row.state]} → ${referenceLabels[row.expected_state]}`);
        if(row.remaining_bytes)note.push(bytes(row.remaining_bytes)+' à télécharger');
        entry.append(name,element('span',note.filter(Boolean).join(' · '),'organizer-meta'));
        if(row.status==='missing'&&row.state!=='excluded'){
          const download=element('button',referenceJobs.has(row.archive)?'Dans la File d’attente':'Télécharger','secondary');
          download.type='button';
          download.disabled=referenceJobs.has(row.archive);
          download.setAttribute('aria-label','Télécharger '+(row.title||row.archive));
          download.onclick=async()=>{
            download.disabled=true;
            try{
              await api('/admin/library/reference/download',{archive:row.archive});
              referenceJobs.add(row.archive);
              download.textContent='Dans la File d’attente';
              const queue=element('a','Voir la file d’attente →','secondary-link');
              queue.href='#/file';queue.dataset.route='file';
              referenceStatus.replaceChildren('Téléchargement demandé. ',queue);
            }catch(error){
              download.disabled=false;
              referenceStatus.textContent='Téléchargement non lancé. '+friendly(error);
            }
          };
          entry.append(download);
        }
        return entry;
      }));
      const comparison=differences.length?plural(differences.length,'écart','écarts')+' avec la référence.':'Aucun écart de fichier ou de classement.';
      const transfer=report.download_bytes?` ${bytes(report.download_bytes)} à télécharger. ${bytes(report.available_bytes)} disponibles.`:'';
      referenceStatus.textContent=comparison+transfer+' Contrôle rapide par taille et empreintes déjà enregistrées.';
    }catch(error){
      referenceStatus.textContent='Comparaison indisponible. '+friendly(error);
    }finally{
      referenceRefresh.disabled=false;
    }
  }
  reference.addEventListener('toggle',()=>{if(reference.open)refreshReference();});
  referenceRefresh.onclick=()=>{referenceJobs.clear();refreshReference();};
  $('organizer-reference-cancel').onclick=()=>{
    restorePanel.hidden=true;
    restorationPlan=null;
    restore.focus();
  };
  // Each line of the comparison is a separate choice: nothing forces the whole reference.
  const groupChoices=new Map();
  function chosen(){
    const selection={downloads:[],removals:[],moves:[]};
    for(const [field,boxes] of groupChoices)for(const box of boxes)if(box.checked)selection[field].push(box.value);
    return selection;
  }
  function updateChoice(){
    if(!restorationPlan)return;
    const selection=chosen();
    const count=selection.downloads.length+selection.removals.length+selection.moves.length;
    const picked=new Set(selection.downloads);
    const download=restorationPlan.downloads.filter(row=>picked.has(row.archive)).reduce((sum,row)=>sum+(row.remaining_bytes||0),0);
    const enough=!download||restorationPlan.available_bytes>=download+(restorationPlan.storage_reserve||0);
    const parts=[count?plural(count,'changement coché','changements cochés'):'Aucun changement coché'];
    if(download)parts.push(bytes(download)+' à télécharger');
    parts.push(bytes(restorationPlan.available_bytes)+' disponibles');
    $('organizer-reference-confirm-space').textContent=parts.join(' · ')+'.'+(enough?'':' L’espace libre est insuffisant pour ces téléchargements.');
    restoreApply.disabled=!count||!enough;
    restoreApply.textContent=count?'Appliquer '+plural(count,'changement','changements'):'Appliquer les changements cochés';
    for(const [field,boxes] of groupChoices){
      const all=$('organizer-reference-all-'+field);
      if(!all)continue;
      const ticked=boxes.filter(box=>box.checked).length;
      all.checked=ticked===boxes.length;
      all.indeterminate=ticked>0&&ticked<boxes.length;
    }
  }
  restore.onclick=async()=>{
    restore.disabled=true;
    try{
      const plan=await api('/admin/library/reference/restoration',undefined,{cache:'no-store'});
      restorationPlan=plan;
      groupChoices.clear();
      const removalNote=row=>row.expected?(plan.downloads.some(item=>item.archive===row.expected)?' · remplacée par '+row.expected:' · ancienne édition'):' · hors référence';
      // Ranking is ticked by default; downloads and deletions are chosen one by one.
      const groups=[
        ['moves','key','Collections à reclasser',plan.moves,row=>`${row.title} · ${referenceLabels[row.state]} → ${referenceLabels[row.expected_state]}`,true],
        ['downloads','archive','À télécharger ou remplacer',plan.downloads,row=>`${row.title} · ${row.archive}`+(row.remaining_bytes?` · ${bytes(row.remaining_bytes)}`:''),false],
        ['removals','archive','Fichiers à supprimer',plan.removals,row=>row.archive+removalNote(row),false],
      ];
      $('organizer-reference-confirm-changes').replaceChildren(...groups.filter(([,,,rows])=>rows.length).map(([field,identifier,label,rows,display,checked])=>{
        const details=element('details');
        details.open=true;
        const summaryLine=element('summary',`${label} (${rows.length})`);
        const allLabel=element('label',undefined,'organizer-reference-choice organizer-reference-all');
        const all=element('input');
        all.type='checkbox';all.id='organizer-reference-all-'+field;all.checked=checked;
        allLabel.append(all,element('span','Tout cocher ou décocher'));
        const list=element('ul',undefined,'organizer-confirm-names organizer-reference-choices');
        const boxes=rows.map(row=>{
          const item=element('li');
          const choice=element('label',undefined,'organizer-reference-choice');
          const box=element('input');
          box.type='checkbox';box.value=row[identifier];box.checked=checked;
          box.onchange=updateChoice;
          choice.append(box,element('span',display(row)));
          item.append(choice);
          list.append(item);
          return box;
        });
        all.onchange=()=>{for(const box of boxes)box.checked=all.checked;updateChoice();};
        groupChoices.set(field,boxes);
        details.append(summaryLine,allLabel,list);
        return details;
      }));
      if(!groups.some(([,,,rows])=>rows.length)){
        $('organizer-reference-confirm-space').textContent='La bibliothèque correspond déjà à la référence.';
        restoreApply.disabled=true;
      }else updateChoice();
      restorePanel.hidden=false;
      $('organizer-reference-cancel').focus();
    }catch(error){referenceStatus.textContent='Comparaison indisponible. '+friendly(error);}
    finally{restore.disabled=false;}
  };
  restoreApply.onclick=async()=>{
    if(!restorationPlan)return;
    const selection=chosen();
    if(selection.removals.length&&!confirm('Supprimer définitivement '+plural(selection.removals.length,'fichier coché','fichiers cochés')+' du PC serveur ?'))return;
    restoreApply.disabled=true;
    try{
      const result=await api('/admin/library/reference/restoration',{confirmation_token:restorationPlan.confirmation_token,selection});
      restorePanel.hidden=true;
      restorationPlan=null;
      if(result?.queued===false){
        await refresh();
        referenceJobs.clear();
        await refreshReference();
        referenceStatus.textContent='Classement appliqué. '+referenceStatus.textContent;
        restore.focus();
        return;
      }
      const queue=element('a','Voir la file d’attente →','secondary-link');
      queue.href='#/file';queue.dataset.route='file';
      referenceStatus.replaceChildren((selection.moves.length?'Classement appliqué. ':'')+'Changements demandés : téléchargements et suppressions suivent dans la file d’attente. ',queue);
      if(selection.moves.length)refresh();
      queue.focus();
    }catch(error){
      referenceStatus.textContent='Changements non appliqués. '+friendly(error);
      restoreApply.disabled=false;
    }
  };

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
  function stateToggle(row,choose,waiting){
    const group=element('div',undefined,'organizer-toggle');
    group.setAttribute('role','group');
    group.setAttribute('aria-label','Classement de '+row.title);
    for(const [state,label] of [['main','Principal'],['other','Autre']]){
      const choice=element('button',label);
      choice.type='button';
      choice.dataset.choice=state;
      choice.setAttribute('aria-pressed',String(row.state===state));
      choice.disabled=busy||waiting;
      choice.onclick=()=>{if(row.state!==state)choose(state);};
      group.append(choice);
    }
    return group;
  }
  function toggle(row){return stateToggle(row,state=>move([row.key],state),pending.has(row.key));}
  const groupId=family=>'organizer-family-'+[...family].reduce((hash,char)=>Math.imul(hash^char.charCodeAt(0),16777619)>>>0,2166136261).toString(16);
  // Several archives of a family often share one generic name (« Project Gutenberg Library »);
  // their catalogue description (« Fine arts », « Science »…) is what tells them apart.
  function rowName(row,duplicate){
    const name=row.kind==='video'?row.title:row.variant||row.title;
    return duplicate&&row.description?row.description:name;
  }
  function rowNode(row,duplicate,heading){
    const item=element('li',undefined,'organizer-row');
    item.dataset.state=row.state;
    const check=element('input');
    check.type='checkbox';check.checked=selected.has(row.key);check.disabled=busy;
    check.setAttribute('aria-label','Cocher '+row.title);
    check.onchange=()=>{check.checked?selected.add(row.key):selected.delete(row.key);render();};
    const body=element('div',undefined,'organizer-name');
    const name=rowName(row,duplicate);
    if(heading){
      body.append(element('strong',heading));
      if(normalize(name)!==normalize(heading))body.append(element('span',name,'organizer-variant'));
    }else body.append(element('strong',name));
    const meta=[row.kind==='video'?(row.count?plural(row.count,'vidéo','vidéos'):'Vidéos'):'Collection Kiwix',bytes(row.bytes)];
    const line=element('span',meta.join(' · '),'organizer-meta');
    if(row.url){
      const open=element('a','Aperçu ↗');
      open.href=localServiceURL(row.url,'kiwix');open.target='_blank';open.rel='noopener';
      open.title='Ouvrir cette collection dans un nouvel onglet pour voir son contenu';
      line.append(' · ',open);
    }
    body.append(line);
    if(row.description&&!duplicate)body.append(element('span',row.description,'organizer-description'));
    else if(duplicate&&row.description)body.append(element('span',row.kind==='video'?row.title:row.variant||row.title,'organizer-description'));
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
    const labels=new Map();
    for(const row of shown){
      const name=row.kind==='video'?'Vidéos téléchargées':row.family||row.title;
      // « wiktionary » and « Wiktionary » are one family; keep the capitalised spelling.
      const family=normalize(name).trim();
      const best=labels.get(family);
      if(!best||best===best.toLowerCase()&&name!==name.toLowerCase())labels.set(family,name);
      if(!families.has(family))families.set(family,[]);
      families.get(family).push(row);
    }
    const display=family=>{const name=labels.get(family)||family;return name.charAt(0).toLocaleUpperCase('fr')+name.slice(1);};
    const ordered=[...families].sort((a,b)=>b[1].reduce((s,r)=>s+r.bytes,0)-a[1].reduce((s,r)=>s+r.bytes,0));
    const fragment=document.createDocumentFragment();
    const filtering=!!$('organizer-filter').value.trim(),single=ordered.length===1;
    const foldable=ordered.filter(([,members])=>members.length>1);
    const expandAll=$('organizer-expand');
    expandAll.hidden=filtering||single||!foldable.length;
    const allOpen=foldable.length&&foldable.every(([family])=>openGroups.has(family));
    expandAll.textContent=allOpen?'Tout replier':'Tout déplier';
    expandAll.onclick=()=>{for(const [family] of foldable)allOpen?openGroups.delete(family):openGroups.add(family);render();};
    const baseName=row=>row.kind==='video'?row.title:row.variant||row.title;
    for(const [key,members] of ordered){
      const family=display(key);
      const names=new Map();
      for(const row of members)names.set(baseName(row),(names.get(baseName(row))||0)+1);
      const duplicate=row=>names.get(baseName(row))>1;
      if(members.length===1){
        // A single collection needs no folding: show it directly, under its family name.
        const section=element('section',undefined,'organizer-group is-single');
        const list=element('ul');
        list.append(rowNode(members[0],duplicate(members[0]),family));
        section.append(list);fragment.append(section);
        continue;
      }
      const open=filtering||single||openGroups.has(key);
      const section=element('section',undefined,'organizer-group');
      section.classList.toggle('is-open',open);
      const head=element('div',undefined,'organizer-group-head');
      const all=element('input');
      all.type='checkbox';all.disabled=busy;
      all.checked=members.every(row=>selected.has(row.key));
      all.indeterminate=!all.checked&&members.some(row=>selected.has(row.key));
      all.setAttribute('aria-label','Cocher toute la famille '+family);
      all.onchange=()=>{for(const row of members)all.checked?selected.add(row.key):selected.delete(row.key);render();};
      const size=members.reduce((sum,row)=>sum+row.bytes,0);
      const other=members.filter(row=>row.state==='other').length;
      const listId=groupId(family);
      const toggle=element('button',undefined,'organizer-group-toggle');
      toggle.type='button';
      toggle.setAttribute('aria-expanded',String(open));
      toggle.setAttribute('aria-controls',listId);
      toggle.disabled=filtering||single;
      const chevron=element('span',undefined,'organizer-chevron');chevron.setAttribute('aria-hidden','true');
      const titles=[...new Set(members.map(row=>rowName(row,duplicate(row))))];
      const preview=titles.slice(0,5).join(' · ')+(titles.length>5?` · et ${titles.length-5} autre${titles.length>6?'s':''}`:'');
      const text=element('span',undefined,'organizer-group-text');
      text.append(element('span',undefined,'organizer-group-line'),element('span',preview,'organizer-group-preview'));
      text.firstChild.append(element('h3',family),element('span',[plural(members.length,'collection','collections'),bytes(size),
        other===members.length?'tout dans Autre':other?other+' dans Autre':'tout dans le fonds principal'].join(' · '),'organizer-meta'));
      toggle.append(chevron,text);
      toggle.onclick=()=>{openGroups.has(key)?openGroups.delete(key):openGroups.add(key);render();};
      head.append(all,toggle);
      if(members.length>1){
        // Move the whole family at once: pressed only when every member is already there.
        const familyRow={key:'family:'+family,title:'toute la famille '+family,
          state:members.every(row=>row.state==='main')?'main':members.every(row=>row.state==='other')?'other':'mixed'};
        const switcher=stateToggle(familyRow,state=>move(members.filter(row=>row.state!==state).map(row=>row.key),state),
          members.some(row=>pending.has(row.key)));
        switcher.classList.add('organizer-family-toggle');
        switcher.title='Ranger toute la famille';
        head.append(switcher);
      }
      section.append(head);
      if(open){
        const list=element('ul');list.id=listId;
        for(const row of members)list.append(rowNode(row,duplicate(row)));
        section.append(list);
      }
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
      if(reference.open)refreshReference();
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
  let deletionId;
  function deletionStatus(message,tracked=true){
    $('organizer-delete-status').textContent=message;
    $('organizer-delete-queue').hidden=!tracked;
  }
  async function follow(attempt=0,checking=false){
    clearTimeout(poll);
    try{
      const job=await api('/admin/library',undefined,{cache:'no-store'});
      if(checking&&busy)return;
      if(job.action==='collection-exclude'&&(!deletionId||job.id===deletionId)){
        deletionId=job.id;
        if(['starting','refreshing'].includes(job.phase)){
          busy=true;render();
          deletionStatus(job.phase==='starting'?'Démarrage de la suppression…':job.message||'Suppression en cours…');
          poll=setTimeout(follow,1800);return;
        }
        deletionStatus(job.phase==='completed'?(job.message||'Suppression terminée.')
          :'Suppression à vérifier. '+(job.message||'Consultez la file d’attente.'));
        await refresh();
        if(job.phase==='completed')loadData();
      }else if(!checking){
        deletionStatus('Le résultat de cette suppression n’est plus disponible ici. Vérifiez les collections restantes.');
        await refresh();
      }
    }catch(error){
      if(!checking){
        deletionStatus('Le suivi est momentanément indisponible. Vérification du résultat…');
        if(attempt<25){poll=setTimeout(()=>follow(attempt+1),2400);return;}
        deletionStatus('Le résultat de la suppression reste à vérifier. Consultez la file d’attente ou rouvrez cette page.');
      }
    }
    if(!checking){busy=false;render();}
  }
  async function confirmDelete(){
    if(!confirmation||busy)return;
    const button=$('organizer-confirm-delete'),back=$('organizer-back');
    busy=true;render();button.disabled=back.disabled=true;
    deletionId=undefined;
    deletionStatus('Envoi de la demande de suppression…',false);
    $('organizer-delete-status').scrollIntoView({block:'nearest'});
    try{
      const job=await api('/admin/library/collection-sort/exclude',confirmation);
      deletionId=job.id;
      selected.clear();confirmation=null;step(false);
      deletionStatus('Demande acceptée. Suppression en cours…');
      await follow();
    }catch(error){
      deletionStatus(error.status&&error.status<500
        ?'Suppression refusée. '+friendly(error)
        :'Le serveur n’a pas confirmé la demande. Vérifiez la file d’attente avant de réessayer.',!(error.status&&error.status<500));
      confirmation=null;step(false);busy=false;render();
    }finally{button.disabled=back.disabled=false;}
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
    if(route.section==='appareil'&&route.tab==='collections'&&!busy){
      step(false);refresh();
      if(admin())follow(0,true);
    }
    if(route.section==='appareil'&&route.tab==='bibliotheque')showCategory();
  });

  /* ---------- French Wikipedia classification, in the search preparation panel ---------- */
  const category=element('section',undefined,'category-index');
  category.id='category-index';
  category.innerHTML=`
    <h3>Classement du fonds principal par espace</h3>
    <p class="small">Prépare la recherche dans <strong>Autonomie et résilience</strong> et <strong>Savoirs et culture</strong>.
      Les archives du fonds principal sont classées en arrière-plan. La recherche reste disponible pendant la préparation.</p>
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
    outdated:'Une partie du fonds principal reste à classer.',
    paused:'En pause. La reprise repart du dernier point enregistré.',
    interrupted:'Interrompu. La reprise repart du dernier point enregistré.',
    error:'Arrêté sur un problème. La recherche habituelle reste disponible ; vous pouvez reprendre.',
    unavailable:'Le fonds principal ne contient aucune archive.'
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
      if(report.archives)text+=` ${number(report.completed)} / ${number(report.archives)} archives prêtes.`;
      if(phase==='running'&&report.archive)text+=` Archive en cours : ${report.archive}.`;
      $('category-index-status').textContent=text;
      const showMeter=['running','paused','interrupted','error'].includes(phase)&&report.total>0;
      $('category-index-meter').hidden=!showMeter;
      if(showMeter){
        const percent=Math.min(100,100*(report.done||0)/report.total);
        $('category-index-progress').value=percent;
        $('category-index-percent').textContent=`${percent.toFixed(percent<10?1:0)} % de l’archive en cours`;
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
