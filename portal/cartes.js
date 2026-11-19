'use strict';
(async () => {
  const status = document.getElementById('status');
  const select = document.getElementById('area');
  const home = document.getElementById('home');
  const printButton=document.getElementById('print');printButton.disabled=true;
  try {
    const user=await window.MapUI.ready;
    const response = await fetch('/api/maps');
    if (!response.ok) throw new Error('Le service des cartes ne répond pas.');
    const {maps} = await response.json();
    window.MapDownloads?.setAreas(maps);
    const hasBasemap=maps.length>0;
    if(!hasBasemap)maps.push({id:'empty',title:'Aucun fond de carte préparé',center:[2.3,46.5],bbox:[-180,-80,180,80],maxzoom:0});
    document.getElementById('no-basemap').hidden=hasBasemap;
    let geoData=null,reference=null;if(user)try{const [g,r]=await Promise.all([fetch('/api/geography/status'),fetch('/api/settings')]);if(g.ok)geoData=await g.json();if(r.ok){const settings=await r.json();reference=settings.departure||settings.home;}}catch(_){}
    const hasTerrain=!!geoData?.datasets?.some(d=>d.terrain);let showRelief=hasTerrain;
    const reliefButton=document.getElementById('relief');
    reliefButton.disabled=false;reliefButton.dataset.unavailable=String(!hasTerrain);
    reliefButton.setAttribute('aria-pressed',String(showRelief));
    reliefButton.textContent=hasTerrain?'Masquer le relief':'Pourquoi le relief est indisponible ?';
    document.getElementById('relief-help').textContent=!user?'Choisissez un profil pour vérifier les altitudes disponibles.':geoData===null?'Le service des altitudes est momentanément indisponible. Réessayez en actualisant la page.':!hasTerrain?'Aucune altitude n’a été téléchargée. Le fond de carte seul ne contient pas de relief.':'Relief affiché par défaut dans les zones dont les altitudes sont disponibles. Vous pouvez le masquer.';
    document.getElementById('relief-prepare').hidden=!user||hasTerrain||geoData===null;
    const protocol = new pmtiles.Protocol();
    maplibregl.addProtocol('pmtiles', protocol.tile);
    select.replaceChildren(...maps.map(item => new Option(item.title, item.id)));
    let current = maps.find(m => m.id === 'sollies') || maps[0];
    select.value = current.id;
    const style=item=>{const s=window.survieMapStyle(item,location.origin+item.url);if(item.id==='empty'){s.sources={};s.layers=s.layers.filter(l=>l.id==='background');}if(showRelief){s.sources.terrain={type:'raster',tiles:[location.origin+'/api/geography/shade/{z}/{x}/{y}.png'],tileSize:256,minzoom:8,maxzoom:14,attribution:'Mapzen · Copernicus EU-DEM · USGS · NOAA'};s.layers.splice(Math.min(4,s.layers.length),0,{id:'terrain-shade',type:'raster',source:'terrain',paint:{'raster-opacity':0.8,'raster-fade-duration':0}});}return s;};
    let map;
    try {
      map = new maplibregl.Map({container: 'map', style: style(current), center: current.center, zoom: 12, maxZoom: 18, maxTileCacheSize: 96, trackResize: false});
    } catch (_) {
      // A renderer failure is not a missing download or lost notebook.
      const message = 'Le navigateur ne peut pas utiliser l’affichage graphique nécessaire à la carte. Essayez un autre navigateur ou vérifiez son accélération graphique. Les lieux et trajets enregistrés sont conservés.';
      status.textContent = message;
      const notice = document.createElement('section');
      notice.className = 'map-renderer-fallback';
      notice.setAttribute('role', 'alert');
      const title = document.createElement('h2');
      title.textContent = 'La carte ne peut pas s’afficher';
      const explanation = document.createElement('p');
      explanation.textContent = message;
      const back = document.createElement('a');
      back.href = '/#/bibliotheque';
      back.textContent = 'Revenir à la bibliothèque';
      notice.append(title, explanation, back);
      document.querySelector('.map-stage').append(notice);
      document.getElementById('no-basemap').hidden = true;
      for (const control of document.querySelectorAll('.map-workspace button, .map-workspace input, .map-workspace select')) control.disabled = true;
      return;
    }
    // Capture a fresh frame only for printing; normal rendering keeps the
    // default non-preserved drawing buffer (MapLibre 5 canvas attributes).
    const printImage=document.createElement('img');printImage.className='map-print-image';printImage.alt='Carte du trajet préparé';
    document.querySelector('.map-stage').append(printImage);
    function preparePrint(){map.resize();map.redraw();printImage.src=map.getCanvas().toDataURL('image/png');}
    printButton.onclick=async()=>{try{preparePrint();await printImage.decode();window.print();}catch(_){window.MapUI.notify('La carte ne peut pas être imprimée pour le moment. Réessayez après son chargement.');}};
    window.addEventListener('beforeprint',preparePrint);
    window.addEventListener('afterprint',()=>{printImage.removeAttribute('src');resizeMap();});
    printButton.disabled=false;
    // Free navigation also permits choosing a departure outside the downloaded basemap.
    map.on('idle', () => {document.getElementById('map').dataset.ready = 'true';});
    let resizeFrame=0;
    function resizeMap(){if(!resizeFrame)resizeFrame=requestAnimationFrame(()=>{resizeFrame=0;map.resize();});}
    new ResizeObserver(resizeMap).observe(document.getElementById('map'));
    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(new maplibregl.ScaleControl({unit: 'metric'}));
    const showStatus = () => { status.textContent = current.id==='empty'?'Aucun fond de carte téléchargé. Préparez une carte pour voir les routes et bâtiments.':current.title + ' · données du ' + current.edition + ' · détail jusqu’au zoom ' + current.maxzoom + '. Fonctionne sans Internet sur le réseau de la maison.'; };
    map.on('load', showStatus);
    map.on('error', event => {status.textContent = 'Certaines données ne sont pas téléchargées dans cette zone. Les outils restent disponibles pour les données présentes.'; console.warn(event.error);});
    select.addEventListener('change', () => {
      current = maps.find(m => m.id === select.value);
      map.setStyle(style(current));
      // Free navigation also permits choosing a departure outside the downloaded basemap.
      map.fitBounds([[current.bbox[0], current.bbox[1]], [current.bbox[2], current.bbox[3]]], {padding: 24});
      showStatus();
    });
    home.addEventListener('click', () => {
      select.value = current.id;
      if(!map.getSource('local')&&current.id!=='empty')map.setStyle(style(current));
      // Recenter without rebuilding the current basemap.
      map.jumpTo({center: reference?[reference.lon,reference.lat]:current.center, zoom: 13}); if(reference)selectPoint(reference.lat,reference.lon);else window.MapUI.notify('Aucun point de départ enregistré. Cliquez sur la carte pour choisir un point.');showStatus();
    });

    const toolStatus=document.getElementById('geo-tool-status'),results=document.getElementById('map-results');
    let point=reference?{lat:reference.lat,lon:reference.lon}:null,marker=null,measureStart=null,measuring=false,pointRequest=0,nearbyRequest=0;
    async function api(path){const response=await fetch('/api'+path,{headers:window.MapUI.user?{'X-Survie-Profile':window.MapUI.user.id}:{}});const data=await response.json();if(!response.ok){if(response.status===401){window.MapUI.user=null;document.body.dataset.mapRole='guest';document.getElementById('map-auth-state').hidden=false;window.MapUI.notify('Choisissez un profil pour continuer.');window.MapUI.login();}throw new Error(response.status===401?'Profil nécessaire pour cet outil.':typeof data.detail==='string'?data.detail:'Outil indisponible.');}return data;}
    function node(tag,text){const n=document.createElement(tag);n.textContent=text;return n;}
    async function selectPoint(lat,lon){
      const request=++pointRequest;point={lat,lon};if(marker)marker.remove();marker=new maplibregl.Marker().setLngLat([lon,lat]).addTo(map);
      document.getElementById('selected-point-card').hidden=false;document.getElementById('selected-point-title').textContent='Point sélectionné';
      window.dispatchEvent(new CustomEvent('survie-map-picked',{detail:{lat,lon}}));
      document.getElementById('map-point').textContent='Coordonnées : '+lat.toFixed(5)+', '+lon.toFixed(5)+'.';
      const link=document.getElementById('save-point');link.hidden=false;link.href='/?lat='+lat+'&lon='+lon+'&target=departure#settings';
      if(!user)return;
      try{const data=await api('/geography/elevation?lat='+lat+'&lon='+lon);if(request===pointRequest)document.getElementById('map-point').textContent+=' Altitude : '+(data.elevation_m===null?'non téléchargée':data.elevation_m+' m environ')+'.';}catch(e){if(request===pointRequest)document.getElementById('map-point').textContent+=' Altitude indisponible.';}
    }
    function locateResult(item){selectPoint(item.lat,item.lon);map.flyTo({center:[item.lon,item.lat],zoom:14});}
    let resultMarkers=[];
    function clearResults(){results.replaceChildren();for(const marker of resultMarkers)marker.remove();resultMarkers=[];}
    function renderResults(items){clearResults();for(const item of items){const row=node('div',''),button=node('button',item.label);button.type='button';button.onclick=()=>{locateResult(item);document.getElementById('selected-point-title').textContent=item.label;if(matchMedia('(max-width:760px)').matches)document.body.classList.remove('map-panel-open');};row.append(button);if(item.distance_m!==undefined){row.append(node('small',item.distance_m>=1000?(item.distance_m/1000).toLocaleString('fr-FR',{maximumFractionDigits:1})+' km à vol d’oiseau':Math.round(item.distance_m)+' m à vol d’oiseau'));resultMarkers.push(new maplibregl.Marker({color:'#b37540'}).setLngLat([item.lon,item.lat]).setPopup(new maplibregl.Popup().setText(item.label)).addTo(map));}results.append(row);}}
    function help(text){document.getElementById('search-help').hidden=!text;document.getElementById('search-help-text').textContent=text||'';}
    let searchVersion=0;
    async function search(event,nearby){
      event.preventDefault();if(!window.MapUI.requireUser())return;
      const form=event.target,submit=form.querySelector('button'),original=submit.textContent,ticket=++searchVersion;
      clearResults();help('');submit.disabled=true;submit.textContent='Recherche…';form.setAttribute('aria-busy','true');toolStatus.textContent='Recherche dans les données de cette zone…';
      window.MapUI.showPanel('geo-tools');
      try{
        if(nearby&&geoData&&geoData.datasets.length===0){toolStatus.textContent='Les lieux de cette zone ne sont pas encore téléchargés.';help('Le fond de carte est distinct des adresses et lieux utiles. Préparez une zone dans Données locales pour chercher les points d’eau, commerces et services.');return;}
        let path='/geography/addresses?q='+encodeURIComponent(document.getElementById('map-query').value);
        if(nearby){const center=map.getCenter(),origin=point||{lat:center.lat,lon:center.lng};path='/geography/nearby?lat='+origin.lat+'&lon='+origin.lon+'&category='+document.getElementById('map-category').value+'&radius_km='+document.getElementById('map-radius').value;toolStatus.textContent='Recherche '+(point?'autour du point sélectionné':'autour du centre de la carte')+'…';}
        const data=await api(path);if(ticket!==searchVersion)return;renderResults(data.results);
        toolStatus.textContent=data.results.length?data.results.length+' lieu(x) trouvé(s). Sélectionnez un résultat pour le voir sur la carte.':'Aucun lieu trouvé dans les données locales pour cette recherche.';
        if(data.note)results.append(node('p',data.note));
        if(nearby&&data.coverage?.length===0)help('Aucun lieu préparé. Téléchargez les adresses et lieux utiles de cette zone.');
        else if(!data.results.length)help('Essayez un autre mot, déplacez le point de recherche ou préparez une zone plus large. Un résultat vide ne prouve pas l’absence de lieu sur le terrain.');
      }catch(e){if(ticket===searchVersion){toolStatus.textContent=e.message;window.MapUI.notify(e.message);}}
      finally{submit.disabled=false;submit.textContent=original;form.removeAttribute('aria-busy');}
    }
    document.getElementById('map-search').onsubmit=event=>search(event,false);
    document.getElementById('map-nearby').onsubmit=event=>search(event,true);
    document.getElementById('measure').onclick=()=>{if(!window.MapUI.requireUser())return;measuring=true;window.MapUI.notify('Mesure : cliquez sur le premier point, puis sur le second.');measureStart=null;document.getElementById('terrain-profile').replaceChildren();toolStatus.textContent='Touchez le premier point, puis le second. Mesure en ligne droite.';};
    let accessPick=null;
    map.on('click',async event=>{
      if(accessPick){const pick=accessPick;accessPick=null;map.getCanvas().style.cursor='';pick({lat:event.lngLat.lat,lon:event.lngLat.lng});return;}
      if(map.getLayer('accesses')&&map.queryRenderedFeatures(event.point,{layers:['accesses']}).length)return;
      if(map.getLayer('notebook-points')&&map.queryRenderedFeatures(event.point,{layers:['notebook-points']}).length)return;
      const {lat,lng:lon}=event.lngLat.wrap();if(lat<-85||lat>85)return;selectPoint(lat,lon);
      window.MapUI.notify('');
      if(!measuring)return;if(!measureStart){measureStart={lat,lon};toolStatus.textContent='Touchez le second point.';return;}
      const a=measureStart;measuring=false;window.MapUI.showPanel('map-layers');
      try{const data=await api('/geography/profile?lat1='+a.lat+'&lon1='+a.lon+'&lat2='+lat+'&lon2='+lon);toolStatus.textContent=Math.round(data.distance_m)+' m à vol d’oiseau. '+data.note;
        const panel=document.getElementById('terrain-profile');panel.replaceChildren();const heights=data.points.filter(p=>p.elevation_m!==null).map(p=>p.elevation_m);
        if(heights.length!==data.points.length){panel.textContent='Profil incomplet : il manque des altitudes sur ce segment.';return;}
        const low=Math.min(...heights),high=Math.max(...heights),ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg'),line=document.createElementNS(ns,'polyline');svg.setAttribute('viewBox','0 0 400 100');svg.setAttribute('role','img');svg.setAttribute('aria-label','Profil du terrain de '+low+' à '+high+' mètres');line.setAttribute('points',heights.map((h,i)=>(i*400/40)+','+(95-90*(h-low)/Math.max(1,high-low))).join(' '));line.setAttribute('fill','none');line.setAttribute('stroke','#245b43');line.setAttribute('stroke-width','2');svg.append(line);panel.append(node('p','Altitude min. '+low+' m · max. '+high+' m'),svg);
      }catch(e){toolStatus.textContent=e.message;}
    });
    document.getElementById('relief').onclick=()=>{if(!window.MapUI.requireUser())return;if(!hasTerrain){window.MapUI.showPanel('map-layers');window.MapUI.notify(geoData===null?'Vérification du relief indisponible. Réessayez en actualisant la page.':'Relief non préparé : téléchargez les altitudes dans Données locales.');return;}showRelief=!showRelief;document.getElementById('relief').setAttribute('aria-pressed',String(showRelief));document.getElementById('relief').textContent=showRelief?'Masquer le relief':'Afficher le relief';if(map.getLayer('terrain-shade'))map.setLayoutProperty('terrain-shade','visibility',showRelief?'visible':'none');else if(showRelief){const terrain=style(current);map.addSource('terrain',terrain.sources.terrain);map.addLayer(terrain.layers.find(l=>l.id==='terrain-shade'),map.getLayer('water')?'water':undefined);}};
    const params=new URLSearchParams(location.search),lat=Number(params.get('lat')),lon=Number(params.get('lon'));
    if(params.has('lat')&&params.has('lon')&&Number.isFinite(lat)&&Number.isFinite(lon)&&lat>=-85&&lat<=85&&lon>=-180&&lon<180){selectPoint(lat,lon);map.jumpTo({center:[lon,lat],zoom:14});}
    else if(reference){selectPoint(reference.lat,reference.lon);map.jumpTo({center:[reference.lon,reference.lat],zoom:13});}
    if(params.has('choose'))window.MapUI.notify('Cliquez sur la carte pour choisir votre point de départ.');
    if(!hasBasemap)toolStatus.textContent='Aucun fond de carte préparé. Vous pouvez saisir des coordonnées dans Paramètres ; les lieux et le relief téléchargés restent utilisables après connexion.';

    let notebookPoints=[],routeGeometry=null,connectors=[],accessCandidates=[],activeAccess=-1;
    function restorePlanningLayers(){
      if(!map.getLayer('background'))return;
      const data={type:'FeatureCollection',features:notebookPoints.map(p=>({type:'Feature',properties:{id:p.id,title:p.title},geometry:{type:'Point',coordinates:[p.lon,p.lat]}}))};
      if(map.getSource('notebook'))map.getSource('notebook').setData(data);
      else{map.addSource('notebook',{type:'geojson',data});map.addLayer({id:'notebook-points',type:'circle',source:'notebook',paint:{'circle-radius':7,'circle-color':'#245b43','circle-stroke-color':'#ffffff','circle-stroke-width':2}});}
      const route={type:'FeatureCollection',features:routeGeometry?[{type:'Feature',properties:{},geometry:routeGeometry}]:[]};
      if(map.getSource('planned-route'))map.getSource('planned-route').setData(route);
      else{map.addSource('planned-route',{type:'geojson',data:route});map.addLayer({id:'planned-route-line',type:'line',source:'planned-route',paint:{'line-color':'#ae5428','line-width':5}},'notebook-points');}
    }
    function restoreAccessLayers(){
      if(!map.getLayer('background'))return;
      const lines={type:'FeatureCollection',features:connectors.map(c=>({type:'Feature',properties:{},geometry:c.geometry}))};
      if(map.getSource('route-connectors'))map.getSource('route-connectors').setData(lines);
      else{map.addSource('route-connectors',{type:'geojson',data:lines});map.addLayer({id:'route-connectors',type:'line',source:'route-connectors',paint:{'line-color':'#9b6b30','line-width':3,'line-dasharray':[2,2]}});}
      const candidates={type:'FeatureCollection',features:accessCandidates.map((c,i)=>({type:'Feature',properties:{index:i,label:String(i+1),active:i===activeAccess},geometry:{type:'Point',coordinates:[c.lon,c.lat]}}))};
      if(map.getSource('accesses'))map.getSource('accesses').setData(candidates);
      else{
        map.addSource('accesses',{type:'geojson',data:candidates});
        map.addLayer({id:'accesses',type:'circle',source:'accesses',paint:{'circle-radius':14,'circle-color':['case',['get','active'],'#ae5428','#275e47'],'circle-stroke-color':'#fff','circle-stroke-width':3}});
        map.addLayer({id:'access-numbers',type:'symbol',source:'accesses',layout:{'text-field':['get','label'],'text-font':['Noto Sans Regular'],'text-size':13,'text-allow-overlap':true},paint:{'text-color':'#fff'}});
      }
    }
    map.on('style.load',restoreAccessLayers);
    map.on('click','accesses',event=>window.dispatchEvent(new CustomEvent('survie-access-selected',{detail:Number(event.features[0].properties.index)})));
    map.on('style.load',restorePlanningLayers);
    map.once('idle',restorePlanningLayers);
    map.on('click','notebook-points',event=>{const feature=event.features[0],p=notebookPoints.find(p=>p.id===feature.properties.id);if(p){selectPoint(p.lat,p.lon);new maplibregl.Popup().setLngLat([p.lon,p.lat]).setText(p.title).addTo(map);window.dispatchEvent(new CustomEvent('survie-saved-point',{detail:p}));}});
    window.SurvieMap={
      point:()=>point,
      pickPoint:()=>{window.MapUI.notify('Touchez ou cliquez sur la carte à l’endroit à enregistrer.');map.getCanvas().style.cursor='crosshair';},
      finishPick:()=>{map.getCanvas().style.cursor='';},
      selectPoint:(p)=>{selectPoint(p.lat,p.lon);map.flyTo({center:[p.lon,p.lat],zoom:14});},
      points:items=>{notebookPoints=items;restorePlanningLayers();},
      route:(geometry,links=[])=>{routeGeometry=geometry;connectors=links;restorePlanningLayers();restoreAccessLayers();if(geometry){const bounds=new maplibregl.LngLatBounds();for(const p of geometry.coordinates)bounds.extend(p);for(const c of links)for(const p of c.geometry.coordinates)bounds.extend(p);map.fitBounds(bounds,{padding:48,maxZoom:15});}},
      accesses:(items,origin,active=-1,fit=false)=>{accessCandidates=items;activeAccess=active;restoreAccessLayers();if(fit&&items.length){const bounds=new maplibregl.LngLatBounds([origin.lon,origin.lat],[origin.lon,origin.lat]);items.forEach(p=>bounds.extend([p.lon,p.lat]));map.fitBounds(bounds,{padding:64,maxZoom:16});}},
      pickAccess:callback=>{accessPick=callback;map.getCanvas().style.cursor=callback?'crosshair':'';},
      resize:resizeMap
    };
    restorePlanningLayers();window.dispatchEvent(new Event('survie-map-ready'));
    select.disabled = false; home.disabled = false;
  } catch (error) {status.textContent = error.message || 'Impossible d’ouvrir les cartes. Revenez à la bibliothèque et réessayez.';}
})();
