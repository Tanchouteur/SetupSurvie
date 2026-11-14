/* Filter the existing inventory cards; never fetch, remove or rebuild their actions. */
(() => {
  const input=document.getElementById('collection-filter');
  const normal=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('fr').replace(/[’'_-]/g,' ').replace(/\s+/g,' ').trim();
  const groups=[['data-books','collection-books-title'],['data-guides','collection-guides-title']];
  const groupId=value=>{let hash=2166136261;for(const char of value)hash=Math.imul(hash^char.charCodeAt(0),16777619);return 'collection-group-'+(hash>>>0).toString(16);};
  function arrangeCollections(){
    const grid=document.getElementById('data-books'),families=new Map();
    for(const card of grid.querySelectorAll(':scope > .data-card')){const key=card.dataset.family||card.querySelector('h3').textContent;if(!families.has(key))families.set(key,[]);families.get(key).push(card);}
    for(const [family,cards] of families){
      if(cards.length<2)continue;
      const group=document.createElement('details');group.className='next-collection-group';group.id=groupId(family);
      const summary=document.createElement('summary');summary.textContent=family+' · '+cards.length+' collections';group.append(summary);
      const children=document.createElement('div');children.className='data-grid';group.append(children);cards[0].before(group);
      for(const card of cards){
        const heading=card.querySelector('h3');if(card.dataset.variant)heading.textContent=card.dataset.variant;
        if(card.dataset.archiveName){const info=document.createElement('details'),label=document.createElement('summary'),name=document.createElement('p');label.textContent='Référence de cette collection';name.textContent=card.dataset.archiveName;info.append(label,name);card.append(info);}
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
  function apply(){
    const query=input.value.slice(0,160),words=normal(query).split(' ').filter(Boolean);
    let total=0,matching=0,ready=0,loaded=true;
    for(const [id,title] of groups){
      const grid=document.getElementById(id);let visible=0;loaded=loaded&&grid.children.length>0;
      for(const card of grid.querySelectorAll('.data-card')){
        const text=normal(card.dataset.catalogSearch||card.textContent);
        const match=words.every(word=>text.includes(word));
        card.hidden=!match;total++;if(match){visible++;matching++;if(card.dataset.inventoryReady==='true')ready++;}
      }
      for(const group of grid.querySelectorAll('.next-collection-group')){
        const visible=[...group.querySelectorAll('.data-card')].some(card=>!card.hidden);group.hidden=!visible;
        if(words.length){if(!group.dataset.filtering)group.dataset.previousOpen=String(group.open);group.dataset.filtering='true';group.open=visible;}
        else if(group.dataset.filtering){group.open=group.dataset.previousOpen==='true';delete group.dataset.filtering;delete group.dataset.previousOpen;}
      }
      for(const placeholder of grid.querySelectorAll('.empty-panel'))placeholder.hidden=!!words.length;
      document.getElementById(title).hidden=!!words.length&&!visible;
    }
    document.getElementById('collection-filter-count').textContent=total?`${matching} / ${total} ressource(s) affichée(s) · ${ready} disponible(s) à la lecture.`:loaded?'Aucune ressource recensée dans cet inventaire.':'';
    document.getElementById('collection-filter-empty').hidden=!words.length||matching>0||!loaded;
    const link=document.getElementById('collection-search-inside');
    link.href='#/bibliotheque/recherche'+(query?'?q='+encodeURIComponent(query):'');
    link.dataset.route='bibliotheque/recherche'+(query?'?q='+encodeURIComponent(query):'');
    document.getElementById('collection-filter-clear').disabled=!input.value;
  }
  const changed=()=>{apply();document.dispatchEvent(new CustomEvent('survie:collection-filter',{detail:input.value.slice(0,160)}));};
  input.addEventListener('input',changed);
  document.getElementById('collection-filter-form').addEventListener('submit',event=>{event.preventDefault();changed();});
  document.getElementById('collection-filter-clear').onclick=()=>{input.value='';changed();input.focus();};
  const observer=new MutationObserver(apply);
  for(const [id] of groups)observer.observe(document.getElementById(id),{childList:true});
  window.CollectionsFilter={setQuery(value){input.value=String(value||'').slice(0,160);apply();}};
  apply();
})();
