/* Household settings and preparation; online calls happen only on explicit submission. */
async function loadSettings(){
  try{const data=await api('/settings');$('location-summary').textContent='Domicile : '+(data.home?.label||'non défini')+' · Point de départ : '+(data.departure?.label||data.home?.label||'non défini');$('clear-departure').disabled=!data.departure;
    const params=new URLSearchParams(location.search);if(params.has('lat')&&params.has('lon')){$('location-target').value=params.get('target')==='home'?'home':'departure';$('location-lat').value=params.get('lat');$('location-lon').value=params.get('lon');$('location-coordinates').closest('details').open=true;history.replaceState(null,'',location.pathname+'#settings');}
  }catch(e){$('location-summary').textContent=e.message;}
}
async function saveLocation(body){
  try{await api('/admin/settings/'+$('location-target').value,body);$('location-message').textContent='Lieu enregistré pour cet appareil. Disponible hors ligne.';$('location-results').replaceChildren();await loadSettings();}
  catch(e){$('location-message').textContent=e.message;}
}
$('location-search-form').onsubmit=async e=>{
  e.preventDefault();const submit=e.submitter;submit.disabled=true;$('location-results').replaceChildren();$('location-message').textContent='Recherche de l’adresse…';
  try{const data=await api('/geography/addresses?q='+encodeURIComponent($('location-query').value.trim())+'&online='+($('location-mode').value==='online'));$('location-message').textContent=data.results.length?data.note:'Aucune adresse trouvée dans cette recherche. Essayez une autre formulation ou choisissez un point sur la carte.';
    const target=$('location-target').value,query=$('location-query').value,mode=$('location-mode').value;
    for(const item of data.results){const row=element('article',undefined,'location-result');row.append(element('strong',item.label),element('p',item.source+(item.precision?' · précision : '+item.precision:''),'small muted'));
      const link=element('a','Vérifier sur la carte →');link.href='/cartes.html?lat='+item.lat+'&lon='+item.lon;link.target='_blank';link.rel='noopener';row.append(link,button('Confirmer ce lieu',()=>{if(target!==$('location-target').value||query!==$('location-query').value||mode!==$('location-mode').value){$('location-message').textContent='Les choix ont changé. Relancez la recherche.';return;}saveLocation({candidate:item.id});}));$('location-results').append(row);}
  }catch(error){$('location-message').textContent=error.message;}finally{submit.disabled=false;}
};
for(const id of ['location-target','location-query','location-mode'])$(id).addEventListener('input',()=>{$('location-results').replaceChildren();$('location-message').textContent='';});
$('location-coordinates').onsubmit=e=>{e.preventDefault();saveLocation({lat:Number($('location-lat').value),lon:Number($('location-lon').value),label:$('location-label').value});};
$('clear-departure').onclick=async()=>{try{await api('/admin/settings/departure',undefined,{method:'DELETE'});await loadSettings();$('location-message').textContent='Le domicile sert à nouveau de point de départ.';}catch(e){$('location-message').textContent=e.message;}};
async function loadGeography(){
  try{const data=await api('/geography/status'),box=$('geo-datasets');box.replaceChildren();for(const item of data.datasets){box.append(element('p',item.radius_km+' km autour de '+item.center[1].toFixed(4)+', '+item.center[0].toFixed(4)+' · '+item.addresses+' adresses/lieux nommés · '+item.places+' lieux utiles · '+(item.terrain?'relief inclus':'sans relief')+' · '+item.created));}if(!data.datasets.length)box.textContent='Aucune zone d’adresses et de relief préparée. Les fonds de carte existants restent accessibles.';}catch(e){$('geo-datasets').textContent=e.message;}
}
function renderGeoJob(data){const geo=!!data.options&&'radius_km' in data.options,busy=['starting','planning','downloading','refreshing'].includes(data.phase);$('geo-download').disabled=busy||contentCommandBusy;$('routing-download').disabled=busy||contentCommandBusy;$('geo-pause').hidden=!geo||!['starting','downloading'].includes(data.phase);if(geo){$('geo-message').textContent=data.message||'';if(data.phase==='completed')loadGeography();}}
$('geo-use-location').onclick=async()=>{try{const data=await api('/settings'),point=data.departure||data.home;if(!point)throw new Error('Définissez d’abord un lieu dans Paramètres.');$('geo-lat').value=point.lat;$('geo-lon').value=point.lon;}catch(e){$('geo-message').textContent=e.message;}};
$('geo-download-form').onsubmit=async e=>{e.preventDefault();await contentAction('geography',{lat:Number($('geo-lat').value),lon:Number($('geo-lon').value),radius_km:Number($('geo-radius').value),terrain:$('geo-terrain').checked});$('geo-message').textContent=$('content-message').textContent;};
$('geo-refresh').onclick=()=>{loadGeography();if(S.user?.role==='admin')loadContentManager();};
$('geo-pause').onclick=()=>contentAction('pause');

$('routing-download').onclick=async()=>{if(!$('geo-lat').reportValidity()||!$('geo-lon').reportValidity())return;await contentAction('routing',{lat:Number($('geo-lat').value),lon:Number($('geo-lon').value),radius_km:Number($('geo-radius').value),terrain:false});$('routing-download-status').textContent=$('content-message').textContent;};
