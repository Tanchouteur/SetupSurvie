/* Filter the existing inventory cards; never fetch, remove or rebuild their actions. */
(() => {
  const input=document.getElementById('collection-filter');
  const normal=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('fr').replace(/[’'_-]/g,' ').replace(/\s+/g,' ').trim();
  const groups=[['data-books','collection-books-title'],['data-guides','collection-guides-title']];
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
