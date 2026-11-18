/* Playback and opening the reader never start subtitle preparation. */
(() => {
  const panel=element('div');panel.id='next-videos';panel.innerHTML='<p class="small muted">Les titres et descriptions se cherchent avec le filtre ci-dessus. La recherche dans les documents retrouve aussi les paroles dont les sous-titres sont indexés.</p><div id="next-videos-admin" class="actions"><button id="next-videos-index" class="secondary">Actualiser les vidéos et leurs sous-titres</button><button id="next-videos-stop" class="secondary" hidden>Arrêter l’inventaire</button><button id="next-videos-report" class="secondary">Télécharger le rapport vidéo</button></div><p id="next-videos-status" class="small" role="status"></p><div id="next-videos-list" class="collections"></div><button id="next-videos-more" class="secondary" hidden>Voir les vidéos suivantes</button>';
  document.querySelector('[data-collection-section="videos"]').append(panel);
  const states={french_available:'Sous-titres français présents · à vérifier',french_prepared:'Français préparé localement · relecture à faire',source_transcribed:'Paroles transcrites localement · relecture à faire',source_only:'Sous-titres dans la langue source',missing:'Sous-titres à préparer',invalid:'Sous-titres présents mais illisibles',unknown:'Langue des sous-titres à identifier'};
  let offset=0,version=0,busy=false,timer=null,latest=null,activeMedia=null;
  let updateReaderTracks=null;
  function languageCode(value){
    const code=(value||'').toLowerCase().split(/[-_]/)[0];
    return ({eng:'en',fra:'fr',fre:'fr',und:''})[code]??code;
  }
  async function refresh(append=false){
    if(!S.authReady||!S.user)return;
    const current=++version,q=$('collection-filter').value;
    try{
      const data=await api('/videos?offset='+(append?offset:0)+'&q='+encodeURIComponent(q));if(current!==version)return;
      const inventoryFinished=data.status.phase==='completed'&&(
        latest?.status.phase!=='completed'||latest.status.finished!==data.status.finished
      );
      latest=data;
      if(inventoryFinished)updateReaderTracks?.();
      $('next-videos-admin').hidden=S.user.role!=='admin';
      $('next-videos-list').hidden=false;
      const running=data.status.phase==='running';$('next-videos-index').disabled=running||busy;$('next-videos-stop').hidden=!running;
      const phase={not_started:'Actualisez les vidéos pour préparer leur recherche.',running:'Inventaire en cours ; les anciens résultats restent utilisables.',paused:'Inventaire arrêté ; ancien index conservé.',interrupted:'Inventaire interrompu ; relancez-le explicitement.',failed:data.status.error||'Inventaire indisponible.',completed:'Inventaire terminé.'}[data.status.phase]||'';
      $('next-videos-status').textContent=data.total+' vidéo(s) correspondante(s). '+phase+(running?' '+(data.status.videos||0)+' vidéo(s) examinée(s).':'');
      const target=$('next-videos-list');if(!append){target.replaceChildren();offset=0;}
      for(const item of data.videos){
        const card=element('article',undefined,'data-card');card.append(element('h3',item.title),element('p',item.collection||'Vidéo locale','small muted'),element('p',states[item.subtitle_status]||'État inconnu','small'),button('Voir la vidéo →',()=>readSource(item.id),'secondary'));
        card.dataset.videoId=item.id;
        if(item.archive_article){const link=element('a','Ouvrir l’article d’origine →','text-button');link.href=originalSourceURL(item.archive_article);link.target='_blank';link.rel='noopener';card.append(link);}
        if(item.available===false){card.querySelector('button').disabled=true;card.append(element('p','Fichier modifié ou absent : actualisez l’inventaire avant de l’ouvrir.','small catalogue-warning'));}
        target.append(card);
      }
      offset+=data.videos.length;$('next-videos-more').hidden=offset>=data.total;
      document.dispatchEvent(new CustomEvent('survie:video-cards',{detail:data.videos}));
    }catch(error){if(current===version)$('next-videos-status').textContent=error.message;}
  }
  async function command(action){
    if(busy)return;busy=true;$('next-videos-index').disabled=true;
    $('next-videos-status').textContent=action==='index'?'Lancement du nouvel inventaire…':'Arrêt de l’inventaire en cours…';
    try{await api('/admin/videos/'+action,{});await refresh();}
    catch(error){$('next-videos-status').textContent=error.message;}
    finally{busy=false;$('next-videos-index').disabled=latest?.status.phase==='running';}
  }
  $('next-videos-index').onclick=()=>command('index');$('next-videos-stop').onclick=()=>command('stop');$('next-videos-more').onclick=()=>refresh(true);
  $('next-videos-report').onclick=async()=>{
    try{const report=await api('/admin/videos/report');downloadReport(report,'videos');}
    catch(error){$('next-videos-status').textContent=error.message;}
  };
  function refreshFilter(){version++;$('next-videos-list').hidden=true;clearTimeout(timer);timer=setTimeout(()=>refresh(),250);}
  document.addEventListener('survie:collection-filter',refreshFilter);
  document.addEventListener('survie:collection-query-restored',refreshFilter);
  new MutationObserver(()=>{if(!$('next-collections').hidden)refresh();}).observe($('next-collections'),{attributes:true,attributeFilter:['hidden']});
  document.addEventListener('survie:auth',()=>{version++;$('video-reader-preparation')?.remove();refresh();});
  document.addEventListener('survie:videos-changed',async()=>{await refresh();updateReaderTracks?.();});
  setInterval(()=>{if(latest?.status.phase==='running'&&!document.hidden&&(!$('next-collections').hidden||activeMedia?.isConnected&&!$('reader').hidden&&!$('view-library').hidden))refresh();},1500);
  document.addEventListener('survie:source',event=>{
    updateReaderTracks=null;
    if(activeMedia){activeMedia.pause();activeMedia=null;}
    const source=event.detail;if(source.kind!=='video')return;
    const reader=$('reader'),body=reader.querySelector('.reader-body'),player=element('video');activeMedia=player;
    player.controls=true;player.preload='metadata';player.playsInline=true;player.style.width='100%';player.style.maxHeight='60vh';player.src=source.url;
    const videoKey=S.user?.id+':'+source.id.split('#t=')[0];
    const positionKey='survie:video:'+videoKey;
    const subtitleKey='survie:video-subtitles:'+videoKey;
    let saved=null,lastPositionSave=0,preference='auto';
    try{preference=localStorage.getItem(subtitleKey)||'auto';}catch(_){}
    try{saved=JSON.parse(localStorage.getItem(positionKey)||'null');}catch(_){}
    function remember(){const now=performance.now();if(now-lastPositionSave<2000&&!player.paused)return;lastPositionSave=now;try{localStorage.setItem(positionKey,JSON.stringify({revision:source.video_revision,seconds:player.currentTime}));}catch(_){}}
    player.addEventListener('timeupdate',remember);player.addEventListener('pause',remember);
    const notice=element('p',undefined,'small catalogue-warning');
    const select=element('select');select.setAttribute('aria-label','Sous-titres de la vidéo');
    const label=element('label','Sous-titres');label.append(select);
    const preparation=element('section');preparation.id='video-reader-preparation';
    preparation.setAttribute('aria-label','Préparation des sous-titres');
    const invalid=element('p','Certaines pistes échouent aux contrôles techniques ; elles ne sont pas proposées en lecture. Consultez le rapport vidéo.','small');
    const problem=element('p',undefined,'small');problem.hidden=true;player.addEventListener('error',()=>{problem.hidden=false;problem.textContent='Ce navigateur ne peut pas lire ce format ou le fichier ne répond pas. Ouvrez le média original avec un lecteur installé. Les sous-titres restent consultables ci-dessous.';});
    for(const node of [player,label,preparation,notice,problem,invalid])reader.insertBefore(node,body);
    const origins={automatic:'automatique',provided:'fournie',unknown:'origine inconnue',local_translation:'traduction locale',local_transcription:'transcription locale'};
    let usable=[],automatic=-1;
    const trackKey=track=>track.preference_key||JSON.stringify([track.language,track.origin,track.id]);
    const selectedIndex=()=>select.value==='auto'?automatic:Number.parseInt(select.value,10);
    function apply(){
      const selected=selectedIndex();
      player.querySelectorAll('track').forEach((track,index)=>{
        track.track.mode=selected===index?'showing':'disabled';
      });
    }
    function renderTracks(){
      usable=(source.tracks||[]).filter(track=>track.status==='passed');
      const audioLanguage=languageCode(source.audio_language);
      automatic=audioLanguage==='fr'?-1:usable.findIndex(track=>languageCode(track.language)==='fr');
      if(automatic<0&&(!audioLanguage||audioLanguage==='en')){
        automatic=usable.findIndex(track=>languageCode(track.language)==='en');
      }
      const remembered=usable.findIndex(track=>trackKey(track)===preference);
      const selected=preference==='off'?-1:remembered>=0?remembered:automatic;
      player.querySelectorAll('track').forEach(track=>track.remove());
      select.replaceChildren(
        new Option('Automatique · '+({fr:'français',en:'anglais'}[languageCode(usable[automatic]?.language)]||'sans sous-titres'),'auto'),
        new Option('Sans sous-titres','off'),
      );
      for(const [index,track] of usable.entries()){
        const node=element('track');node.kind='subtitles';node.src=track.url;node.srclang=track.language||'und';
        node.label=(track.language||'Langue inconnue')+' · '+(origins[track.origin]||track.origin);
        node.default=index===selected;
        node.addEventListener('load',apply,{once:true});
        player.append(node);select.append(new Option(node.label,String(index)));
      }
      select.value=preference==='off'?'off':remembered>=0?String(remembered):'auto';
      apply();
      notice.textContent=[source.video_notice,...new Set((source.tracks||[]).flatMap(track=>[track.transcription_notice,track.acquisition_notice]).filter(Boolean))].join(' ');
      invalid.hidden=!(source.tracks||[]).some(track=>track.status!=='passed');
      body.replaceChildren();
      if(source.transcription_available)renderDocument(body,source);
      else body.append(element('p','Aucun sous-titre exploitable pour cet aperçu. Le titre seul ne permet pas à l’assistant de connaître les paroles.'));
      if(preparation.isConnected&&S.user?.role==='admin')document.dispatchEvent(new CustomEvent('survie:video-reader',{detail:{item:source,host:preparation}}));
    }
    select.onchange=()=>{
      const track=usable[Number.parseInt(select.value,10)];
      preference=track?trackKey(track):select.value;
      try{
        if(preference==='auto')localStorage.removeItem(subtitleKey);
        else localStorage.setItem(subtitleKey,preference);
      }catch(_){}
      apply();
    };
    player.addEventListener('loadedmetadata',()=>{const duration=player.duration,wanted=source.position_ms?source.position_ms/1000:saved?.revision===source.video_revision&&Number.isFinite(saved.seconds)?saved.seconds:0;if(wanted>0&&Number.isFinite(duration))player.currentTime=Math.min(wanted,Math.max(0,duration-.1));apply();});
    if(S.user?.role!=='admin')preparation.remove();
    renderTracks();
    let loadingTracks=false;
    const profile=S.user?.id;
    updateReaderTracks=async()=>{
      if(loadingTracks||!player.isConnected||reader.hidden||$('view-library').hidden||S.user?.id!==profile)return;
      loadingTracks=true;
      try{
        const updated=await api('/source?id='+encodeURIComponent(source.id));
        if(!player.isConnected||S.user?.id!==profile||updated.video_revision===source.video_revision)return;
        Object.assign(source,updated);
        renderTracks();
      }catch(_){
        // Keep the current player usable during an inventory or a network error.
      }finally{loadingTracks=false;}
    };
    const original=reader.querySelector('.reader-actions a');if(original){original.textContent='Ouvrir la vidéo originale →';original.href=source.url;}
  });
  new MutationObserver(()=>{if(activeMedia&&($('reader').hidden||$('view-library').hidden)){activeMedia.pause();}}).observe($('view-library'),{subtree:true,attributes:true,attributeFilter:['hidden']});
})();
