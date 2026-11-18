/* Filter the existing inventory cards; never fetch, remove or rebuild their actions. */
(() => {
  const input=document.getElementById('collection-filter');
  const normal=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('fr').replace(/[’'_-]/g,' ').replace(/\s+/g,' ').trim();
  const groups=[['livres','data-books'],['guides','data-guides']];
  const categoryLinks=[...document.querySelectorAll('[data-collection-type]')];
  const collections=document.getElementById('next-collections');
  const topbar=document.querySelector('.topbar');
  new ResizeObserver(()=>collections.style.setProperty('--collection-mobile-top',topbar.offsetHeight+'px')).observe(topbar);
  let category='',readOpen=(_,fallback)=>fallback;
  const disclosureSelector='.next-collection-section, .next-collection-group';
  const groupId=value=>{let hash=2166136261;for(const char of value)hash=Math.imul(hash^char.charCodeAt(0),16777619);return 'collection-group-'+(hash>>>0).toString(16);};
  function arrangeCollections(){
    for(const [type,id] of groups)groupCards(document.getElementById(id),type);
  }
  function groupCards(grid,type){
    const guides=type==='guides',families=new Map();
    for(const card of grid.querySelectorAll(':scope > .data-card')){
      const heading=card.querySelector('h3');
      const parts=guides?heading.textContent.match(/^(.+?)\s+[—–]\s+(.+)$/):null;
      if(guides&&!parts)continue;
      const family=guides?parts[1]:card.dataset.family||heading.textContent;
      if(!families.has(family))families.set(family,[]);
      families.get(family).push({card,heading,variant:guides?parts[2]:card.dataset.variant});
    }
    for(const [family,cards] of families){
      if(cards.length<2)continue;
      const group=document.createElement('details');group.className='next-collection-group';group.id=groupId(guides?'guide:'+family:family);
      group.open=readOpen(group.id,false);
      const summary=document.createElement('summary');summary.textContent=family+' · '+cards.length+(guides?' documents':' collections');group.append(summary);
      const children=document.createElement('div');children.className='data-grid';group.append(children);cards[0].card.before(group);
      for(const {card,heading,variant} of cards){
        if(variant)heading.textContent=variant;
        if(!guides&&card.dataset.archiveName){const info=document.createElement('details'),label=document.createElement('summary'),name=document.createElement('p');label.textContent='Référence de cette collection';name.textContent=card.dataset.archiveName;info.append(label,name);card.append(info);}
        children.append(card);
      }
    }
  }
  function collectionOptions(data){
    const select=document.getElementById('search-collection');if(!select)return;
    const selected=select.value||select.dataset.requested||'',families=new Map();
    for(const item of data.books||[]){if(!item.ready)continue;const family=item.family||item.title||item.id,key=normal(item.family||item.id).replace(/[^a-z0-9]/g,'');if(!key)continue;const prior=families.get(key);families.set(key,{label:family,edited:!!prior?.edited||item.labels_status==='corrected'});}
    select.replaceChildren(new Option('Toutes les collections',''));
    for(const [key,value] of families)select.append(new Option(value.label,(value.edited?'group:':'')+key));
    if(selected&&![...select.options].some(option=>option.value===selected))select.append(new Option(selected+' · à vérifier',selected));
    select.value=selected;
  }
  document.addEventListener('survie:inventory',event=>{arrangeCollections();collectionOptions(event.detail);apply();});
  function revealMatches(group,filtering,visible){
    if(filtering){
      if(!group.dataset.filtering)group.dataset.previousOpen=String(group.open);
      group.dataset.filtering='true';group.open=visible;
    }else if(group.dataset.filtering){
      group.open=group.dataset.previousOpen==='true';delete group.dataset.filtering;delete group.dataset.previousOpen;
    }
  }
  function apply(){
    const query=input.value.slice(0,160),words=normal(query).split(' ').filter(Boolean);
    for(const link of categoryLinks){
      const type=link.dataset.collectionType,params=new URLSearchParams();
      if(type)params.set('rubrique',type);
      if(query)params.set('resource',query);
      const route='bibliotheque/collections'+(params.size?'?'+params:'');
      link.href='#/'+route;link.dataset.route=route;
      if(type===category)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');
    }
    let total=0,matching=0,ready=0,loaded=true;
    for(const [type,id] of groups){
      const grid=document.getElementById(id),section=grid.parentElement;
      const selected=!category||category===type;
      let visible=0;loaded=loaded&&grid.children.length>0;
      for(const card of grid.querySelectorAll('.data-card')){
        const text=normal(card.dataset.catalogSearch||card.textContent);
        const match=words.every(word=>text.includes(word));
        card.hidden=!match;
        if(match)visible++;
        if(selected){total++;if(match){matching++;if(card.dataset.inventoryReady==='true')ready++;}}
      }
      for(const group of grid.querySelectorAll('.next-collection-group')){
        const visible=[...group.querySelectorAll('.data-card')].some(card=>!card.hidden);group.hidden=!visible;
        revealMatches(group,!!words.length,visible);
      }
      for(const placeholder of grid.querySelectorAll('.empty-panel'))placeholder.hidden=!!words.length;
      section.hidden=!selected||!!words.length&&!visible;
      revealMatches(section,!!words.length,!!visible);
    }
    const videosOnly=category==='videos',videoSection=document.querySelector('[data-collection-section="videos"]');
    videoSection.hidden=!!category&&!videosOnly;
    revealMatches(videoSection,!!words.length,true);
    document.getElementById('collection-filter-count').textContent=videosOnly?'':total?`${matching} / ${total} ressource(s) affichée(s) · ${ready} disponible(s) à la lecture.`:loaded?'Aucune ressource recensée dans cet inventaire.':'';
    document.getElementById('collection-filter-empty').hidden=videosOnly||!words.length||matching>0||!loaded;
    const link=document.getElementById('collection-search-inside');
    const search=new URLSearchParams();
    if(query||videosOnly)search.set('q',query);
    if(videosOnly)search.set('kind','videos');
    link.dataset.route='bibliotheque/recherche'+(search.size?'?'+search:'');
    link.href='#/'+link.dataset.route;
    link.textContent=videosOnly?'Rechercher aussi dans les sous-titres →':'Chercher aussi à l’intérieur des documents →';
    document.getElementById('collection-filter-clear').disabled=!input.value;
  }
  const changed=()=>{apply();document.dispatchEvent(new CustomEvent('survie:collection-filter',{detail:input.value.slice(0,160)}));};
  input.addEventListener('input',changed);
  document.getElementById('collection-filter-form').addEventListener('submit',event=>{event.preventDefault();changed();});
  document.getElementById('collection-filter-clear').onclick=()=>{input.value='';changed();input.focus();};
  const observer=new MutationObserver(apply);
  for(const [,id] of groups)observer.observe(document.getElementById(id),{childList:true});
  window.CollectionsFilter={setView(value,type,read){
    readOpen=read;
    category=categoryLinks.some(link=>link.dataset.collectionType===type)?type:'';
    const previous=input.value;
    input.value=String(value||'').slice(0,160);
    for(const detail of document.querySelectorAll(disclosureSelector)){
      const open=readOpen(detail.id,detail.matches('.next-collection-section'));
      if(detail.dataset.filtering)detail.dataset.previousOpen=String(open);
      else detail.open=open;
    }
    apply();
    if(previous!==input.value)document.dispatchEvent(new Event('survie:collection-query-restored'));
  }};
  apply();
})();
