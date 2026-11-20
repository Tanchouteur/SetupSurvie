(() => {
  const area=element('details');
  area.id='collection-sort';
  area.className='next-collection-group';
  area.innerHTML=`
    <summary>Tri des collections</summary>
    <div class="sort-actions" id="collection-sort-actions">
      <label>Filtrer les collections<input type="search" id="collection-sort-filter" maxlength="160"></label>
      <button type="button" class="secondary" id="collection-sort-select">Sélectionner les résultats</button>
      <button type="button" class="secondary" id="collection-sort-clear">Vider la sélection</button>
      <button type="button" class="secondary" data-state="main">Mettre dans Fonds principal</button>
      <button type="button" class="secondary" data-state="other">Mettre dans Autre</button>
      <button type="button" class="secondary" id="collection-sort-delete">Supprimer et exclure…</button>
      <a class="secondary" href="/api/admin/library/collection-sort/export" id="collection-sort-export" download="SetupSurvie-tri.json">Exporter le tri</a>
    </div>
    <p id="collection-sort-total" class="small"></p>
    <p id="collection-sort-status" role="status"></p>
    <ul id="collection-sort-list"></ul>
    <dialog id="collection-delete-dialog" aria-labelledby="collection-delete-title">
      <h2 id="collection-delete-title">Supprimer et exclure ces collections</h2>
      <p id="collection-delete-total"></p>
      <ul id="collection-delete-list"></ul>
      <div class="sort-actions">
        <form method="dialog"><button class="secondary">Annuler</button></form>
        <button type="button" id="collection-delete-confirm">Confirmer la suppression</button>
      </div>
      <p id="collection-delete-status" role="status"></p>
    </dialog>`;
  $('collection-filter-form').after(area);
  const category=element('details',undefined,'next-collection-group');
  category.id='category-index';
  category.innerHTML='<summary>Index par catégorie de Wikipédia en français</summary>'+
    '<p id="category-index-status" role="status"></p><progress id="category-index-progress" max="100" hidden></progress>'+
    '<div class="sort-actions"><button type="button" id="category-index-start" hidden>Préparer les index</button>'+
    '<button type="button" class="secondary" id="category-index-pause" hidden>Mettre en pause</button></div>';
  area.after(category);
  let categoryPoll;
  const categoryStart=$('category-index-start'),categoryPause=$('category-index-pause');
  const categoryLabels={
    not_prepared:'La recherche utilise encore l’archive Wikipédia complète.',
    running:'Préparation en arrière-plan. La recherche utilise encore l’archive Wikipédia complète.',
    completed:'Index Autonomie et résilience et Savoirs et culture prêts.',
    outdated:'Une correction ou une nouvelle édition doit être intégrée. La recherche utilise l’archive complète.',
    paused:'Préparation en pause. Elle reprend à partir du dernier point enregistré.',
    interrupted:'Préparation interrompue. Elle reprend à partir du dernier point enregistré.',
    error:'La préparation a rencontré un problème. La recherche habituelle reste disponible.',
    unavailable:'Aucune archive Wikipédia en français disponible.'
  };
  async function showCategory(){
    clearTimeout(categoryPoll);
    if(!category.open)return;
    const message=$('category-index-status'),progress=$('category-index-progress');
    try{
      const report=await api('/library/category-index',undefined,{cache:'no-store'});
      const job=admin()?await api('/admin/library').catch(()=>null):null;
      const active=job?.action==='category-index'&&['starting','downloading'].includes(job.phase);
      const phase=active?'running':job?.action==='category-index'&&job.phase==='error'?'error':report.phase==='running'&&job?'interrupted':report.phase;
      message.textContent=categoryLabels[phase]||categoryLabels.not_prepared;
      if(report.bytes&&phase==='completed')message.textContent+=' '+bytes(report.bytes)+' sur le disque · '+Math.round(report.elapsed_seconds)+' s pour la dernière préparation.';
      progress.hidden=phase!=='running';
      if(report.total)progress.value=100*(report.done||0)/report.total;
      else progress.removeAttribute('value');
      categoryStart.hidden=!admin()||['running','completed','unavailable'].includes(phase);
      categoryStart.disabled=Boolean(job&&['starting','planning','downloading','refreshing'].includes(job.phase));
      categoryStart.textContent=phase==='paused'||phase==='interrupted'?'Reprendre la préparation':'Préparer les index';
      categoryPause.hidden=!active;
      categoryPause.disabled=Boolean(job?.pause_requested);
    }catch(error){message.textContent=error.message;}
    if(category.open)categoryPoll=setTimeout(showCategory,3500);
  }
  async function categoryCommand(action,button){
    button.disabled=true;
    try{await api('/admin/library/'+action,{});await showCategory();}
    catch(error){$('category-index-status').textContent=error.message;button.disabled=false;}
  }
  categoryStart.onclick=()=>categoryCommand('category-index',categoryStart);
  categoryPause.onclick=()=>categoryCommand('pause',categoryPause);
  category.addEventListener('toggle',showCategory);
  const selected=new Set(), labels={main:'Fonds principal',other:'Autre',excluded:'Exclue'};
  const actions=[...area.querySelectorAll('[data-state]')],dialog=$('collection-delete-dialog');
  const normalize=value=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  let rows=[],visible=[],busy=false,confirmation=null,poll;
  function admin(){return S.user?.role==='admin';}
  function selection(){
    const checked=rows.filter(row=>selected.has(row.key));
    $('collection-sort-total').textContent=admin()?`${checked.length} collection(s) sélectionnée(s) · ${bytes(checked.reduce((sum,row)=>sum+row.bytes,0))}`:'';
    for(const action of actions)action.disabled=busy||!checked.length||checked.some(row=>row.state==='excluded');
    $('collection-sort-delete').disabled=busy||!checked.length;
    $('collection-sort-clear').disabled=busy||!checked.length;
    $('collection-sort-select').disabled=busy||!visible.length;
  }
  function render(){
    const query=normalize($('collection-sort-filter').value).trim().split(/\s+/);
    visible=rows.filter(row=>query.every(word=>normalize([row.title,labels[row.state],...row.files].join(' ')).includes(word)));
    const list=$('collection-sort-list'),fragment=document.createDocumentFragment();
    for(const row of visible){
      const item=element('li'),label=element('label'),body=element('span');
      if(admin()){
        const input=element('input');
        input.type='checkbox';input.checked=selected.has(row.key);input.disabled=busy;
        input.onchange=()=>{if(input.checked)selected.add(row.key);else selected.delete(row.key);selection();};
        label.append(input);
      }
      body.append(element('strong',row.title),element('span',` · ${bytes(row.bytes)} · ${labels[row.state]}`));
      if(row.files.length)body.append(element('code',row.files.join(' · '),'small muted'));
      label.append(body);item.append(label);fragment.append(item);
    }
    list.replaceChildren(fragment);
    for(const action of actions)action.hidden=!admin();
    for(const id of ['collection-sort-delete','collection-sort-clear','collection-sort-select','collection-sort-export'])$(id).hidden=!admin();
    selection();
  }
  async function refresh(){
    try{
      rows=await api('/library/collection-sort',undefined,{cache:'no-store'});
      for(const key of selected)if(!rows.some(row=>row.key===key))selected.delete(key);
      render();
    }catch(error){$('collection-sort-status').textContent=error.message;}
  }
  async function command(action,body){
    return api('/admin/library/collection-sort/'+action,body);
  }
  $('collection-sort-filter').oninput=render;
  $('collection-sort-select').onclick=()=>{for(const row of visible)selected.add(row.key);render();};
  $('collection-sort-clear').onclick=()=>{selected.clear();render();};
  for(const action of actions)action.onclick=async()=>{
    busy=true;render();
    try{
      await command('move',{keys:[...selected],state:action.dataset.state});
      selected.clear();
      $('collection-sort-status').textContent='Classement enregistré.';
      await refresh();
    }catch(error){$('collection-sort-status').textContent=error.message;}
    finally{busy=false;render();}
  };
  $('collection-sort-delete').onclick=async()=>{
    busy=true;render();
    try{
      const keys=[...selected],preview=await command('preview',{keys});
      if(!preview.files.length)throw Error('Aucun fichier présent à supprimer.');
      confirmation={keys,token:preview.token};
      $('collection-delete-total').textContent=`${preview.files.length} fichier(s) · ${bytes(preview.bytes)} récupérables. Ces collections seront écartées des prochains téléchargements.`;
      $('collection-delete-list').replaceChildren(...preview.files.map(file=>element('li',file.name+' · '+bytes(file.bytes))));
      $('collection-delete-status').textContent='';
      dialog.showModal();
    }catch(error){$('collection-sort-status').textContent=error.message;}
    finally{busy=false;render();}
  };
  async function follow(attempt=0){
    clearTimeout(poll);
    try{
      const job=await api('/admin/library');
      if(job.action==='collection-exclude'){
        $('collection-sort-status').textContent=job.message;
        if(['starting','refreshing'].includes(job.phase)){poll=setTimeout(follow,1800);return;}
        await refresh();
        if(job.phase==='completed')loadData();
      }
    }catch(error){
      if(attempt<8){poll=setTimeout(()=>follow(attempt+1),1800);return;}
      $('collection-sort-status').textContent=error.message;
    }
    busy=false;render();
  }
  $('collection-delete-confirm').onclick=async()=>{
    if(!confirmation)return;
    const button=$('collection-delete-confirm');
    button.disabled=true;
    try{
      await command('exclude',confirmation);
      selected.clear();confirmation=null;dialog.close();
      busy=true;render();
      await follow();
    }catch(error){$('collection-delete-status').textContent=error.message;}
    finally{button.disabled=false;}
  };
  area.addEventListener('toggle',()=>{if(area.open)refresh();});
  document.addEventListener('survie:inventory',()=>{if(area.open&&!busy)refresh();});
})();
