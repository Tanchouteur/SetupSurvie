/* This small independent script keeps native access usable if PDF.js fails. */
(() => {
  const id=new URLSearchParams(location.search).get('id')||'',base=id.split('#page=')[0];
  if(!base.startsWith('guide:')||!base.toLowerCase().endsWith('.pdf')){
    document.getElementById('pdf-status').textContent='Référence PDF non valide. Revenez à la bibliothèque.';return;
  }
  const original='/api/original?id='+encodeURIComponent(base);
  const path=base.slice(6);if(path.includes('\\')||path.split('/').some(p=>!p||p==='..'||p==='.'))return;
  const file='/guides/'+path.split('/').map(encodeURIComponent).join('/');
  document.getElementById('pdf-original').href=original;
  document.getElementById('pdf-emergency').href=file;
  document.getElementById('pdf-download').href=file;
  document.getElementById('pdf-download').download=path.split('/').pop();
  document.getElementById('pdf-ask').href='/index.html?document='+encodeURIComponent(id)+'#chat';
  const favorite=document.getElementById('pdf-favorite');let active=false,logged=false;
  const render=()=>{favorite.textContent=active?'★ Retirer des favoris':'☆ Ajouter aux favoris';favorite.setAttribute('aria-pressed',String(active));};
  async function refresh(){
    try{const response=await fetch('/api/favorites');logged=response.ok;if(!logged)return;const data=await response.json();active=data.results.some(r=>r.id===base);render();}catch(_){/* PDF reading never depends on favorites. */}
  }
  favorite.onclick=async()=>{
    if(!logged){document.getElementById('pdf-status').textContent='Connectez-vous dans le portail pour utiliser vos favoris. Le PDF reste consultable.';return;}
    favorite.disabled=true;
    try{
      const response=await fetch('/api/favorites'+(active?'?source_id='+encodeURIComponent(base):''),{method:active?'DELETE':'PUT',headers:{'Content-Type':'application/json'},body:active?undefined:JSON.stringify({source_id:base})});
      if(!response.ok)throw Error('Favoris momentanément indisponibles. Le PDF reste consultable.');active=!active;render();
    }catch(error){document.getElementById('pdf-status').textContent=error.message;}finally{favorite.disabled=false;}
  };
  refresh();
})();
