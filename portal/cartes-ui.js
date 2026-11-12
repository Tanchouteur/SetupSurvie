'use strict';
(() => {
  const $=id=>document.getElementById(id),mobile=matchMedia('(max-width:760px)'),panels=['geo-tools','map-notebook','planning-panel','map-layers'];
  function resize(){requestAnimationFrame(()=>window.SurvieMap?.resize());}
  function showPanel(id,expand=true){
    $('map-notice').hidden=true;
    for(const name of panels){const el=$(name);el.open=name===id;}
    document.querySelectorAll('[data-panel]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.panel===id)));
    if(expand)document.body.classList.add('map-panel-open');
    resize();
  }
  function notify(text){$('map-notice').textContent=text;$('map-notice').hidden=!text;}
  function login(){if(!$('map-login-dialog').open)$('map-login-dialog').showModal();}
  const UI=window.MapUI={user:null,showPanel,notify,login,requireUser(){if(this.user)return true;notify('Connectez-vous pour utiliser cet outil. La carte reste ouverte.');login();return false;}};
  document.querySelectorAll('[data-panel]').forEach(b=>b.onclick=()=>showPanel(b.dataset.panel));
  document.querySelectorAll('[data-map-login]').forEach(b=>b.onclick=login);
  $('map-account').onclick=()=>{if(!UI.user)login();else notify('Connecté : '+UI.user.name+' · '+(UI.user.role==='admin'?'administrateur':'lecteur'));};
  $('open-map-panel').onclick=()=>{document.body.classList.add('map-panel-open');resize();};
  $('close-map-panel').onclick=()=>{document.body.classList.remove('map-panel-open');resize();};
  for(const id of panels)$(id).addEventListener('toggle',()=>{if($(id).open){document.querySelectorAll('[data-panel]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.panel===id)));resize();}});
  mobile.addEventListener('change',()=>{document.body.classList.remove('map-panel-open');resize();});
  $('map-login-close').onclick=()=>$('map-login-dialog').close();
  $('map-login-form').onsubmit=async event=>{
    event.preventDefault();const submit=event.submitter;submit.disabled=true;$('map-login-error').textContent='Connexion…';
    try{const response=await fetch('/api/auth/login',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(event.target)))});const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Connexion impossible. Vérifiez votre identifiant.');event.target.reset();location.reload();}
    catch(e){$('map-login-error').textContent=e.message;}finally{submit.disabled=false;}
  };
  UI.ready=(async()=>{try{const response=await fetch('/api/auth/me',{credentials:'same-origin'});if(response.ok){UI.user=await response.json();$('map-account').textContent=UI.user.name||'Mon compte';$('map-auth-state').hidden=true;}else if(response.status===401){$('map-auth-state').hidden=false;}else{notify('Le service de connexion est indisponible. Vous pouvez toujours consulter la carte.');}}
  catch(_){notify('Le service de connexion ne répond pas. La carte reste accessible.');}
  document.body.dataset.mapRole=UI.user?.role||'guest';return UI.user;})();
  showPanel('geo-tools',false);
})();
