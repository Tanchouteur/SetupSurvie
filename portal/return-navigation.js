/* Keep native PDF/map pages usable from either portal, without external redirects. */
(() => {
  const mode=new URLSearchParams(location.search).get('interface');
  if(!['nouveau','classique'].includes(mode))return;
  const modern=mode==='nouveau';
  const home=modern?'/nouveau/':'/classique/';
  const map=document.querySelector('.map-header');
  const back=map?.querySelector('.back-link')||document.querySelector('header > a');
  if(back){back.href=modern?(map?home+'#/cartes':home+'#/bibliotheque/collections'):home+'#library';back.textContent=map?'← Cartes et bibliothèque':'← Bibliothèque';}
  const update=()=>{
    const ask=document.getElementById('pdf-ask');
    if(ask){const id=new URLSearchParams(location.search).get('id');if(id){const target=home+'?document='+encodeURIComponent(id)+(modern?'#/assistant':'#chat');if(ask.getAttribute('href')!==target)ask.href=target;}}
    const save=document.getElementById('save-point');
    if(save?.getAttribute('href')){const u=new URL(save.href);if(u.origin===location.origin&&(u.pathname==='/index.html'||u.pathname==='/')){u.pathname=home;u.hash=modern?'#/appareil/reglages':'#settings';if(save.href!==u.href)save.href=u.href;}}
  };
  update();
  if(map&&modern&&window.MapUI){window.MapUI.ready.then(user=>{if(!user)return;const key='survie-next-v1:'+user.id+':map-panel';let saved;try{saved=JSON.parse(localStorage.getItem(key));}catch(_){}const ids=['geo-tools','map-notebook','map-layers'];if(saved&&Date.now()-saved.at<7*86400000&&ids.includes(saved.value))window.MapUI.showPanel(saved.value,false);for(const id of ids){document.getElementById(id)?.addEventListener('toggle',e=>{if(e.target.open)try{localStorage.setItem(key,JSON.stringify({at:Date.now(),value:id}));}catch(_){} });}});}
  for(const id of ['pdf-ask','save-point']){const node=document.getElementById(id);if(node)new MutationObserver(()=>{const before=node.href;update();if(node.href===before)return;}).observe(node,{attributes:true,attributeFilter:['href']});}
})();
