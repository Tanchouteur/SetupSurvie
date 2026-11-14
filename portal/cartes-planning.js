'use strict';
(() => {
  const $=id=>document.getElementById(id);
  const mobile=matchMedia('(max-width:760px)');
  let pickingPoint=false;
  let book={lists:[],points:[],routes:[]},user=null,map=null,listId='',editingPoint=null,editingList=null,stops=['',''],draft=null,activeRoute=null,request=0;
  const kinds={water:'Eau',food:'Alimentation',health:'Santé',shelter:'Abri',meeting:'Rendez-vous',repair:'Réparation',communication:'Communications',other:'Repère'};
  function node(tag,text){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;return el;}
  function button(label,action,cls=''){const el=node('button',label);el.type='button';el.className=cls;el.onclick=action;return el;}
  function km(meters){return (meters/1000).toLocaleString('fr-FR',{maximumFractionDigits:2})+' km';}
  function duration(seconds){const mins=Math.max(0,Math.ceil(seconds/60));return mins>=60?Math.floor(mins/60)+' h '+String(mins%60).padStart(2,'0'):mins+' min';}
  async function api(path,body,method){const options={credentials:'same-origin'};if(body!==undefined){options.method=method||'POST';options.headers={'Content-Type':'application/json'};options.body=JSON.stringify(body);}else if(method)options.method=method;if(window.MapUI.user)options.headers={...options.headers,'X-Survie-Profile':window.MapUI.user.id};const response=await fetch('/api'+path,options);const data=await response.json();if(!response.ok)throw Object.assign(new Error(response.status===401?'Choisissez un profil pour retrouver les points et trajets.':typeof data.detail==='string'?data.detail:data.detail?.message||'Vérifiez les informations saisies.'),{code:data.code||data.detail?.code});return data;}
  function selectedPoints(){return book.points.filter(p=>p.list_id===listId);}
  function clearRoute(){cancelAccess();accessChoices.clear();accessQueries.clear();$('map-route-chip').hidden=true;request++;draft=null;activeRoute=null;$('route-save-form').hidden=true;$('selected-route').hidden=true;map?.route(null);}
  function listOptions(select,value){select.replaceChildren();for(const list of book.lists){const option=node('option',list.title);option.value=list.id;select.append(option);}if(book.lists.some(l=>l.id===value))select.value=value;}
  function updateMap(){map?.points(selectedPoints());}
  function displayRoute(route){if(mobile.matches)document.body.classList.remove('map-panel-open');activeRoute=route;$('selected-point-card').hidden=true;$('map-route-chip').hidden=false;$('map-route-chip').textContent=km(route.distance_m)+' · '+duration(route.duration_s)+' · Voir le trajet';$('selected-route').hidden=false;$('selected-route-title').textContent=route.title||'Trajet calculé';$('selected-route-distance').textContent=km(route.distance_m)+' par les voies';$('selected-route-duration').textContent=duration(route.duration_s)+' estimées · '+route.speed_kmh+' km/h · '+({foot:'à pied',motorcycle:'moto',car:'petite voiture'}[route.mode]);$('selected-route-note').textContent=route.note;$('selected-route-stops').replaceChildren();for(const point of route.points||[]){$('selected-route-stops').append(node('li',point.title+(point.offset_m>5?' · liaison à vérifier : '+Math.round(point.offset_m)+' m à vol d’oiseau':'')));}const segments=$('selected-route-segments');segments.replaceChildren();for(const step of (route.segments||[]).slice(0,50)){segments.append(node('p',step.name+' · '+km(step.distance_m)));}if((route.segments||[]).length>50)segments.append(node('p','Les 50 premiers segments sont affichés. Le fichier GPX conserve le tracé complet.'));$('selected-route-export').hidden=!route.id;if(route.id)$('selected-route-export').href='/api/map-notebook/routes/'+route.id+'/gpx';map?.route(route.geometry,route.connectors||[]);}
  async function openRoute(id){clearRoute();const ticket=request;try{const route=await api('/map-notebook/routes/'+id);if(ticket!==request)return;displayRoute(route);$('planning-message').textContent='';}catch(e){$('notebook-message').textContent=e.message;}}
  function render(){
    listOptions($('notebook-list'),listId);listOptions($('point-list'),listId);
    $('notebook-export').hidden=!listId;if(listId)$('notebook-export').href='/api/map-notebook/lists/'+listId+'/gpx';
    const points=$('notebook-points'),routes=$('notebook-routes');points.replaceChildren();routes.replaceChildren();
    for(const point of selectedPoints()){
      const row=node('article');row.className='notebook-card';row.append(button(point.title,()=>map?.selectPoint(point),'point-open'),node('small',kinds[point.kind]||'Repère'));
      if(point.notes){const details=node('details');details.append(node('summary','Notes'),node('p',point.notes));row.append(details);}
      if(user?.role==='admin'){const actions=node('div');actions.className='editor-only card-actions';actions.append(button('Modifier',()=>editPoint(point)),button('Supprimer',()=>removePoint(point)));row.append(actions);}points.append(row);
    }
    for(const route of book.routes.filter(r=>r.list_id===listId)){
      const row=node('article');row.className='notebook-card';row.append(button(route.title,()=>openRoute(route.id),'route-open'),node('small',km(route.distance_m)+' · '+duration(route.duration_s)+' · '+({foot:'à pied',motorcycle:'moto',car:'petite voiture'}[route.mode])));
      if(user?.role==='admin'){const remove=button('Supprimer',()=>removeRoute(route));remove.className='editor-only';row.append(remove);}routes.append(row);
    }
    if(!points.children.length)points.append(node('p',user?.role==='admin'?'Votre liste est vide. Cliquez sur « Ajouter un point », puis choisissez son emplacement sur la carte.':'Aucun point enregistré dans cette liste.'));
    if(!routes.children.length)routes.append(node('p','Aucun trajet enregistré dans cette liste.'));
    $('notebook-message').textContent=book.lists.length?'Choisissez un point ou un trajet pour l’afficher. Consultation sans GPS.':user?.role==='admin'?'Commencez par « Ajouter un point ». Vous pourrez créer sa liste dans le même formulaire.':'Aucune liste préparée. Un administrateur peut préparer les repères sur ordinateur.';
    for(const id of ['rename-map-list','delete-map-list'])$(id).disabled=!listId;
    $('new-map-point').disabled=false;
    $('route-calculate').disabled=book.points.length<2;
    renderStops();updateMap();
  }
  async function load(){try{const profile=await window.MapUI.ready;if(!profile){$('notebook-message').textContent='Choisissez un profil avec le bouton en haut de la page pour retrouver vos repères.';return;}const data=await api('/map-notebook');book=data;user=profile;if(!book.lists.some(l=>l.id===listId))listId=book.lists[0]?.id||'';$('planning-panel').hidden=user.role!=='admin';render();const status=await api('/routing');$('routing-availability').textContent=status.note+(status.coverage?' · zone du '+status.coverage.created:'');}catch(e){$('notebook-message').textContent=e.message;}}
  function editList(list=null){editingList=list?.id||null;$('map-list-dialog-title').textContent=list?'Renommer la liste':'Nouvelle liste';$('map-list-title').value=list?.title||'';$('list-form-message').textContent='';$('map-list-dialog').showModal();$('map-list-title').focus();}
  $('new-map-list').onclick=()=>editList();$('rename-map-list').onclick=()=>editList(book.lists.find(l=>l.id===listId));$('cancel-list').onclick=()=>$('map-list-dialog').close();
  $('map-list-form').onsubmit=async event=>{event.preventDefault();const submit=event.submitter;submit.disabled=true;try{const result=await api('/admin/map-notebook/lists'+(editingList?'/'+editingList:''),{title:$('map-list-title').value.trim()});listId=result.id;$('map-list-dialog').close();clearRoute();await load();}catch(e){$('list-form-message').textContent=e.message;}finally{submit.disabled=false;}};
  $('delete-map-list').onclick=async()=>{if(!listId||!confirm('Supprimer cette liste vide ? Les listes contenant des points ou trajets sont conservées.'))return;try{await api('/admin/map-notebook/lists/'+listId,undefined,'DELETE');clearRoute();await load();}catch(e){$('planning-message').textContent=e.message;}};
  function editPoint(point=null){
    if(!window.MapUI.requireUser())return;const chosen=point||map?.point();if(!chosen){$('planning-message').textContent='Choisissez d’abord un point sur la carte.';return;}
    editingPoint=point?.id||null;listOptions($('point-list'),point?.list_id||listId);const create=node('option','＋ Créer une nouvelle liste');create.value='__new__';$('point-list').append(create);if(!listId)$('point-list').value='__new__';$('point-new-list-field').hidden=$('point-list').value!=='__new__';$('point-new-list-title').required=$('point-list').value==='__new__';$('map-point-dialog-title').textContent=point?'Modifier le point':'Enregistrer le point choisi';$('point-title').value=point?.title||'';$('point-lat').value=chosen.lat;$('point-lon').value=chosen.lon;$('point-kind').value=point?.kind||'other';$('point-notes').value=point?.notes||'';$('point-form-message').textContent='';$('map-point-dialog').showModal();$('point-title').focus();
  }
  function beginPoint(){if(!window.MapUI.requireUser())return;if(user?.role!=='admin'){window.MapUI.notify('Choisissez le profil Famille ou un profil avec accès aux réglages pour ajouter un point.');return;}pickingPoint=true;map?.pickPoint();if(mobile.matches)document.body.classList.remove('map-panel-open');}
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&pickingPoint){pickingPoint=false;map?.finishPick();window.MapUI.notify('Ajout du point annulé.');}});
  $('new-map-point').onclick=beginPoint;
  $('begin-map-point').onclick=beginPoint;
  $('save-selected-point').onclick=()=>{if(window.MapUI.requireUser())editPoint();};
  $('point-list').onchange=()=>{const create=$('point-list').value==='__new__';$('point-new-list-field').hidden=!create;$('point-new-list-title').required=create;};
  window.addEventListener('survie-map-picked',()=>{if(pickingPoint){pickingPoint=false;map?.finishPick();window.MapUI.notify('');editPoint();}});$('cancel-point').onclick=()=>{pickingPoint=false;map?.finishPick();$('map-point-dialog').close();};
  $('map-point-form').onsubmit=async event=>{event.preventDefault();const submit=event.submitter;submit.disabled=true;try{if($('point-list').value==='__new__'){const created=await api('/admin/map-notebook/lists',{title:$('point-new-list-title').value.trim()});book.lists.push(created);listId=created.id;listOptions($('point-list'),created.id);$('point-new-list-field').hidden=true;$('point-new-list-title').required=false;}await api('/admin/map-notebook/points'+(editingPoint?'/'+editingPoint:''),{list_id:$('point-list').value,title:$('point-title').value.trim(),lat:Number($('point-lat').value),lon:Number($('point-lon').value),kind:$('point-kind').value,notes:$('point-notes').value});listId=$('point-list').value;$('map-point-dialog').close();window.MapUI.showPanel('map-notebook');window.MapUI.notify('Point enregistré dans votre liste.');clearRoute();await load();}catch(e){$('point-form-message').textContent=e.message;}finally{submit.disabled=false;}};
  async function removePoint(point){if(!confirm('Supprimer le point « '+point.title+' » ? Les trajets déjà enregistrés restent conservés.'))return;try{await api('/admin/map-notebook/points/'+point.id,undefined,'DELETE');clearRoute();await load();}catch(e){$('planning-message').textContent=e.message;}}
  async function removeRoute(route){if(!confirm('Supprimer le trajet « '+route.title+' » ?'))return;try{await api('/admin/map-notebook/routes/'+route.id,undefined,'DELETE');if(activeRoute?.id===route.id)clearRoute();await load();}catch(e){$('planning-message').textContent=e.message;}}
  function renderStops(){const target=$('route-stops');target.replaceChildren();stops=stops.map(id=>book.points.some(p=>p.id===id)?id:'');for(let i=0;i<stops.length;i++){
    const row=node('div');row.className='route-stop';const label=node('label',i===0?'Départ':i===stops.length-1?'Arrivée':'Étape '+i),select=node('select');select.required=true;select.setAttribute('aria-label',label.textContent);select.append(node('option','Choisir un point enregistré'));select.firstChild.value='';for(const p of book.points){const option=node('option',p.title+' · '+(book.lists.find(l=>l.id===p.list_id)?.title||''));option.value=p.id;select.append(option);}select.value=stops[i];select.onchange=()=>{stops[i]=select.value;clearRoute();};label.append(select);row.append(label);if(i>0&&i<stops.length-1)row.append(button('Retirer',()=>{stops.splice(i,1);clearRoute();renderStops();}));target.append(row);
    }$('route-add-stop').disabled=stops.length>=8;}
  $('route-add-stop').onclick=()=>{if(stops.length<8){stops.splice(stops.length-1,0,'');clearRoute();renderStops();}};
  $('route-mode').onchange=()=>{const foot=$('route-mode').value==='foot';$('route-speed').value=foot?4:40;$('route-speed').min=foot?0.5:5;$('route-speed').max=foot?12:130;$('route-avoid-motorways').disabled=foot;clearRoute();};
  $('route-speed').oninput=clearRoute;$('route-avoid-motorways').onchange=clearRoute;$('route-avoid-motorways').disabled=true;
  const accessChoices=new Map(),accessQueries=new Map();
  let accessOrigin=null,candidates=[],candidateIndex=-1,accessVersion=0,calculating=false;
  function cancelAccess(){
    accessVersion++;accessOrigin=null;candidates=[];candidateIndex=-1;
    $('route-access').hidden=true;$('route-form').hidden=false;$('route-review-access').hidden=true;$('route-data-action').hidden=true;
    map?.accesses([],null);map?.pickAccess(null);
  }
  function routePoints(){return stops.map(id=>book.points.find(p=>p.id===id));}
  function selectAccess(index){
    if(!candidates[index])return;candidateIndex=index;map?.pickAccess(null);
    [...$('access-candidates').children].forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));
    $('access-confirm').disabled=false;map?.accesses(candidates,accessOrigin,index);
  }
  window.addEventListener('survie-access-selected',event=>selectAccess(event.detail));
  async function chooseAccess(index,near=null,prepared=null){
    const points=routePoints(),origin=points[index];if(!origin)return;
    const ticket=++accessVersion;accessOrigin=origin;candidateIndex=-1;
    $('route-form').hidden=true;$('route-access').hidden=false;$('route-review-access').hidden=true;
    $('access-title').textContent='Choisir un accès pour '+origin.title;
    $('access-status').textContent='Recherche des accès proches…';$('access-candidates').replaceChildren();
    $('access-confirm').disabled=true;$('access-manual').hidden=false;map?.accesses([],origin);map?.pickAccess(null);
    try{
      const result=prepared||await api('/admin/map-notebook/accesses',{lat:origin.lat,lon:origin.lon,mode:$('route-mode').value,avoid_motorways:$('route-avoid-motorways').checked,near:near?[near.lat,near.lon]:null});
      if(ticket!==accessVersion)return;if(!near)accessQueries.set(index,result);candidates=result.candidates;
      $('access-status').textContent=candidates.length?'Choisissez une voie. La liaison depuis le point reste à vérifier sur place.':'Aucun accès trouvé ici à moins de 1 km. Choisissez un autre emplacement ou préparez une zone plus large.';
      for(const [i,c] of candidates.entries()){
        const b=button((i+1)+'. '+c.label+' · '+Math.round(c.distance_m)+' m à vol d’oiseau',()=>selectAccess(i));
        b.setAttribute('aria-pressed','false');b.onfocus=()=>map?.accesses(candidates,origin,i);b.onmouseenter=()=>map?.accesses(candidates,origin,i);b.onmouseleave=()=>map?.accesses(candidates,origin,candidateIndex);$('access-candidates').append(b);
      }
      map?.accesses(candidates,origin,-1,true);
      $('access-confirm').onclick=()=>{if(candidateIndex<0)return;accessChoices.set(index,candidates[candidateIndex].token);cancelAccess();calculateRoute();};
      $('access-manual').onclick=()=>{const manualTicket=accessVersion;$('access-status').textContent='Cliquez près de la voie à utiliser, à moins de 1 km du point.';map?.pickAccess(p=>{if(manualTicket===accessVersion)chooseAccess(index,p);});};
    }catch(e){if(ticket===accessVersion)$('access-status').textContent=e.message;}
  }
  $('access-cancel').onclick=()=>{cancelAccess();$('route-save-form').hidden=!draft;$('route-review-access').hidden=!(draft||activeRoute);$('planning-message').textContent='Préparation conservée. Vous pouvez modifier les étapes ou réessayer.';};
  $('route-review-access').onclick=()=>{
    cancelAccess();$('route-review-access').hidden=true;
    $('route-save-form').hidden=true;$('route-access').hidden=false;$('route-form').hidden=true;$('access-title').textContent='Quel point souhaitez-vous raccorder autrement ?';
    $('access-status').textContent='Choisissez le départ, l’arrivée ou une étape.';$('access-candidates').replaceChildren();$('access-confirm').disabled=true;
    $('access-manual').hidden=true;
    routePoints().forEach((p,i)=>$('access-candidates').append(button(p.title,()=>{$('access-manual').hidden=false;chooseAccess(i);})));
  };
  async function calculateRoute(){
    if(calculating||!listId)return;const points=routePoints();
    if(points.some(p=>!p)){$('planning-message').textContent='Choisissez chaque étape.';return;}
    if(points.every(p=>p.id===points[0].id)){$('planning-message').textContent='Choisissez au moins deux points différents.';return;}
    draft=null;activeRoute=null;$('route-save-form').hidden=true;$('selected-route').hidden=true;$('map-route-chip').hidden=true;map?.route(null);
    const ticket=++request;calculating=true;$('route-calculate').disabled=true;$('route-form').setAttribute('aria-busy','true');$('planning-message').textContent='Calcul dans le réseau local…';$('route-review-access').hidden=true;$('route-data-action').hidden=true;
    try{
      const data=await api('/admin/map-notebook/calculate',{points:points.map((p,i)=>({lat:p.lat,lon:p.lon,title:p.title,access_token:accessChoices.get(i)||null})),mode:$('route-mode').value,speed_kmh:Number($('route-speed').value),avoid_motorways:$('route-avoid-motorways').checked});
      if(ticket!==request)return;draft=data;displayRoute(data);$('route-title').value=points[0].title+' → '+points.at(-1).title;$('route-save-form').hidden=false;$('route-review-access').hidden=false;
      $('planning-message').textContent='Vérifiez le tracé et les liaisons en pointillés, puis enregistrez le trajet.';
    }catch(e){
      if(ticket!==request)return;$('planning-message').textContent=e.message;
      if(e.code==='no_access'){
        // Locate the first point that lacks an ordinary 100 m attachment.
        for(let i=0;i<points.length;i++){
          if(accessChoices.has(i))continue;
          try{const r=accessQueries.get(i)||await api('/admin/map-notebook/accesses',{lat:points[i].lat,lon:points[i].lon,mode:$('route-mode').value,avoid_motorways:$('route-avoid-motorways').checked});
            if(ticket!==request)return;accessQueries.set(i,r);if(!r.candidates.length||r.candidates[0].distance_m>100){await chooseAccess(i,null,r);break;}
          }catch(error){if(ticket===request)$('planning-message').textContent=error.message;break;}
        }
        if(ticket===request&&$('route-access').hidden)$('route-review-access').hidden=false;
      }else if(['no_route','access_expired'].includes(e.code)){if(e.code==='access_expired'){accessChoices.clear();accessQueries.clear();}$('route-review-access').hidden=false;}
      const engineProblem=['engine_unavailable','engine_timeout','stale_graph','invalid_response'].includes(e.code);
      $('route-data-action').hidden=!engineProblem&&!['outside_coverage','not_prepared'].includes(e.code);
      $('route-data-action').href=engineProblem?'/#/appareil':'/#data';
      $('route-data-action').textContent=engineProblem?'Vérifier l’état de l’appareil →':'Préparer les routes et chemins de cette zone →';
    }finally{calculating=false;$('route-calculate').disabled=book.points.length<2;$('route-form').removeAttribute('aria-busy');}
  }
  $('route-form').onsubmit=event=>{event.preventDefault();calculateRoute();};

  $('route-save-form').onsubmit=async event=>{event.preventDefault();if(!draft)return;const data=draft,submit=event.submitter;submit.disabled=true;try{const saved=await api('/admin/map-notebook/routes',{draft_id:data.draft_id,list_id:listId,title:$('route-title').value.trim()});draft=null;$('route-save-form').hidden=true;await load();await openRoute(saved.id);$('planning-message').textContent='Trajet enregistré. Il reste consultable sans moteur de calcul ni GPS.';}catch(e){$('planning-message').textContent=e.message;}finally{submit.disabled=false;}};
  $('map-route-chip').onclick=()=>{window.MapUI.showPanel('map-notebook');$('selected-route').scrollIntoView({block:'nearest'});};
  $('notebook-list').onchange=()=>{listId=$('notebook-list').value;clearRoute();render();};$('notebook-refresh').onclick=load;$('clear-map-route').onclick=clearRoute;
  $('planning-panel').addEventListener('toggle',()=>{if(!$('planning-panel').open&&!$('route-access').hidden){cancelAccess();$('route-save-form').hidden=!draft;$('route-review-access').hidden=!(draft||activeRoute);}});
  for(const id of ['map-notebook','planning-panel','geo-tools'])$(id).addEventListener('toggle',()=>{requestAnimationFrame(()=>map?.resize());});
  window.addEventListener('survie-map-ready',()=>{map=window.SurvieMap;updateMap();if(activeRoute)map.route(activeRoute.geometry,activeRoute.connectors||[]);});
  if(window.SurvieMap)map=window.SurvieMap;
  let printSheetOpen=false;
  window.addEventListener('beforeprint',()=>{printSheetOpen=$('route-sheet').open;if(activeRoute)$('route-sheet').open=true;map?.resize();});
  window.addEventListener('afterprint',()=>{$('route-sheet').open=printSheetOpen;map?.resize();});
  load();
})();
