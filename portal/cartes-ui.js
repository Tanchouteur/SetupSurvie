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
  async function login(){
    if(!$('map-login-dialog').open)$('map-login-dialog').showModal();$('map-login-error').textContent='';$('map-profile-list').replaceChildren();
    try{const r=await fetch('/api/profiles'),data=await r.json();if(!r.ok)throw Error('Liste des profils indisponible.');for(const profile of data.profiles){const b=document.createElement('button');b.type='button';b.textContent=profile.name;b.onclick=async()=>{b.disabled=true;try{const r=await fetch('/api/profiles/select',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:profile.id})});if(!r.ok)throw Error('Impossible de choisir ce profil.');localStorage.setItem('survie.profile.changed',String(Date.now()));location.reload();}catch(error){$('map-login-error').textContent=error.message;b.disabled=false;}};$('map-profile-list').append(b);}}
    catch(error){$('map-login-error').textContent=error.message;}
  }
  const UI=window.MapUI={user:null,showPanel,notify,login,requireUser(){if(this.user)return true;notify('Choisissez un profil pour utiliser cet outil. La carte reste ouverte.');login();return false;}};
  document.querySelectorAll('[data-panel]').forEach(b=>b.onclick=()=>showPanel(b.dataset.panel));
  document.querySelectorAll('[data-map-login]').forEach(b=>b.onclick=login);
  $('map-account').onclick=login;
  $('open-map-panel').onclick=()=>{document.body.classList.add('map-panel-open');resize();};
  $('close-map-panel').onclick=()=>{document.body.classList.remove('map-panel-open');resize();};
  for(const id of panels)$(id).addEventListener('toggle',()=>{if($(id).open){document.querySelectorAll('[data-panel]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.panel===id)));resize();}});
  mobile.addEventListener('change',()=>{document.body.classList.remove('map-panel-open');resize();});
  $('map-login-close').onclick=()=>$('map-login-dialog').close();
  window.addEventListener('storage',event=>{if(event.key==='survie.profile.changed')location.reload();});
  async function refreshProfile(){if(!UI.user||document.hidden)return;try{const response=await fetch('/api/profiles/current');if(response.ok&&(await response.json()).id!==UI.user?.id)location.reload();}catch(_){}}
  window.addEventListener('focus',refreshProfile);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshProfile();});
  UI.ready=(async()=>{try{const response=await fetch('/api/profiles/current',{credentials:'same-origin'});if(response.ok){UI.user=await response.json();$('map-account').textContent=UI.user.name||'Choisir un profil';$('map-auth-state').hidden=true;}else if(response.status===401){$('map-auth-state').hidden=false;}else{notify('Le choix de profil est indisponible. Vous pouvez toujours consulter la carte.');}}
  catch(_){notify('Le choix de profil ne répond pas. La carte reste accessible.');}
  document.body.dataset.mapRole=UI.user?.role||'guest';return UI.user;})();
  showPanel('geo-tools',false);
})();
