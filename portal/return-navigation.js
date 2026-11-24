/* Keep native PDF/map pages connected to the portal routes, without external redirects. */
(() => {
  const home='/';
  const map=document.querySelector('.map-header');
  const back=map?.querySelector('.back-link')||document.querySelector('header > a');
  if(back){back.href=map?home+'#/accueil':home+'#/bibliotheque/collections';back.textContent=map?'← Accueil':'← Bibliothèque';}
  const update=()=>{
    const ask=document.getElementById('pdf-ask');
    if(ask){const id=new URLSearchParams(location.search).get('id');if(id){const target=home+'?document='+encodeURIComponent(id)+'#/assistant';if(ask.getAttribute('href')!==target)ask.href=target;}}
    const save=document.getElementById('save-point');
    if(save?.getAttribute('href')){const u=new URL(save.href);if(u.origin===location.origin&&(u.pathname==='/index.html'||u.pathname==='/')){u.pathname=home;u.hash='#/appareil/reglages';if(save.href!==u.href)save.href=u.href;}}
  };
  update();
  if(map&&window.MapUI){window.MapUI.ready.then(user=>{if(!user)return;const key='survie-next-v1:'+user.id+':map-panel';let saved;try{saved=JSON.parse(localStorage.getItem(key));}catch(_){}const ids=['geo-tools','map-notebook','map-layers'];if(saved&&Date.now()-saved.at<7*86400000&&ids.includes(saved.value))window.MapUI.showPanel(saved.value,false);for(const id of ids){document.getElementById(id)?.addEventListener('toggle',e=>{if(e.target.open)try{localStorage.setItem(key,JSON.stringify({at:Date.now(),value:id}));}catch(_){} });}});}
  for(const id of ['pdf-ask','save-point']){const node=document.getElementById(id);if(node)new MutationObserver(()=>{const before=node.href;update();if(node.href===before)return;}).observe(node,{attributes:true,attributeFilter:['href']});}
})();
