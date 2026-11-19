/* Playback and opening the reader never start subtitle preparation. */
(() => {
  const panel=element('div');panel.id='next-videos';
  panel.innerHTML=`<div class="video-library-status"><p id="next-videos-count" role="status"></p><p id="next-videos-feedback" class="small" role="status"></p></div>
    <div id="next-videos-list" class="video-library-list"></div>
    <button id="next-videos-more" class="secondary" hidden>Voir la suite</button>
    <div id="video-library-tools">
      <details id="next-video-management" class="video-disclosure">
        <summary>Gestion de la vidéothèque</summary>
        <div id="next-videos-admin" class="video-actions" hidden>
          <button id="next-videos-index" class="secondary">Actualiser les vidéos et leurs sous-titres</button>
          <button id="next-videos-stop" class="secondary" hidden>Arrêter l’inventaire</button>
          <button id="next-videos-report" class="text-button">Télécharger le rapport vidéo</button>
        </div>
        <p id="next-videos-status" class="small" role="status"></p>
      </details>
    </div>`;
  document.querySelector('[data-collection-section="videos"]').append(panel);
  const states={french_available:'Sous-titres français',french_prepared:'Sous-titres français · à relire',source_transcribed:'Paroles transcrites · à relire',source_only:'Sous-titres en langue d’origine',missing:'Sous-titres à préparer',invalid:'Pistes illisibles',unknown:'Langue des pistes inconnue'};
  let offset=0,version=0,busy=false,timer=null,latest=null,activeMedia=null;
  let renderedQuery=null;
  let updateReaderTracks=null;
  function languageCode(value){
    const code=(value||'').toLowerCase().split(/[-_]/)[0];
    return ({eng:'en',fra:'fr',fre:'fr',und:''})[code]??code;
  }
  async function refresh(append=false){
    if(!S.authReady||!S.user)return;
    const current=++version,q=$('collection-filter').value;
    try{
      const data=await api('/videos?'+new URLSearchParams({grouped:'true',offset:append?offset:0,q}));
      if(current!==version)return;
      const same=!append&&renderedQuery===q&&offset>0&&latest?.status.finished===data.status.finished&&latest.total===data.total;
      const inventoryFinished=data.status.phase==='completed'&&(
        latest?.status.phase!=='completed'||latest.status.finished!==data.status.finished
      );
      latest=data;
      if(inventoryFinished)updateReaderTracks?.();
      $('next-videos-admin').hidden=S.user.role!=='admin';
      $('next-videos-list').hidden=false;
      const running=data.status.phase==='running';$('next-videos-index').disabled=running||busy;$('next-videos-stop').hidden=!running;
      const phase={not_started:'Actualisez les vidéos pour préparer leur recherche.',running:'Inventaire en cours ; les anciens résultats restent utilisables.',paused:'Inventaire arrêté ; ancien index conservé.',interrupted:'Inventaire interrompu ; relancez-le explicitement.',failed:data.status.error||'Inventaire indisponible.',completed:'Inventaire terminé.'}[data.status.phase]||'';
      $('next-videos-count').textContent=data.total?data.total+(data.total===1?' vidéo':' vidéos'):(q?'Aucune vidéo ne correspond à ce filtre.':'Aucune vidéo répertoriée.');
      $('next-videos-feedback').textContent=running?'Inventaire en cours…':data.status.phase==='failed'?'Inventaire indisponible.':'';
      $('next-videos-status').textContent=phase+(running?' Vidéos examinées : '+(data.status.videos||0)+'.':'');
      if(same)return;
      const target=$('next-videos-list');
      if(!append){target.replaceChildren();offset=0;renderedQuery=q;}
      for(const group of data.groups.filter(group=>!group.video))target.append(collectionCard(group,q,data.group_total===1));
      renderCards(target,data.groups.filter(group=>group.video).map(group=>group.video));
      offset+=data.groups.length;$('next-videos-more').hidden=offset>=data.group_total;
    }catch(error){if(current===version)$('next-videos-feedback').textContent=error.message;}
  }
  function collectionCard(group,q,onlyGroup){
    const details=window.CollectionsFilter.createGroup('video:'+group.id,group.name,group.count+' vidéos');
    details.classList.add('video-collection-group');
    const children=element('div',undefined,'data-grid video-library-list');
    const notice=element('p',undefined,'small video-collection-notice');notice.setAttribute('role','status');
    let loaded=0,loading=false;
    const more=button('Voir les vidéos suivantes',load,'secondary video-collection-more');more.hidden=true;
    details.append(children,notice,more);
    async function load(){
      if(loading)return;
      loading=true;more.disabled=true;notice.textContent='Chargement des vidéos…';
      try{
        const data=await api('/videos?'+new URLSearchParams({group:group.id,q,offset:loaded}));
        if(!details.isConnected||q!==$('collection-filter').value)return;
        renderCards(children,data.videos);
        loaded+=data.videos.length;more.hidden=loaded>=data.total;more.textContent='Voir les vidéos suivantes';notice.textContent='';
      }catch(error){notice.textContent=error.message;more.hidden=false;more.textContent='Réessayer';}
      finally{loading=false;more.disabled=false;}
    }
    details.addEventListener('toggle',()=>{if(details.open&&!loaded)load();});
    if(q.trim()&&onlyGroup)details.open=true;
    return details;
  }
  function renderCards(target,items){
      for(const item of items){
        const card=element('article',undefined,'data-card video-library-card');
        const head=element('div',undefined,'video-card-heading');
        const info=element('div',undefined,'video-card-info');
        const play=button('Voir la vidéo →',()=>readSource(item.id),'secondary video-card-play');
        const mark=element('span',undefined,'video-card-mark');mark.setAttribute('aria-hidden','true');
        info.append(element('h3',item.title));
        const language=({fr:'Français',en:'Anglais'})[languageCode(item.audio_language||item.language)];
        const metadata=[item.collection,language].filter(Boolean).join(' · ');
        if(metadata)info.append(element('p',metadata,'video-card-meta'));
        const hasNamedTrack=item.tracks.some(track=>track.status==='passed'&&track.language);
        const trackStatus=item.subtitle_status==='unknown'&&hasNamedTrack?'Sous-titres disponibles':states[item.subtitle_status];
        info.append(element('p',trackStatus||'Sous-titres à vérifier','video-card-track'));
        head.append(mark,info,play);card.append(head);
        card.dataset.videoId=item.id;
        if(item.archive_article){
          const link=element('a','Ouvrir l’article d’origine →','video-card-origin');link.href=originalSourceURL(item.archive_article);link.target='_blank';link.rel='noopener';card.append(link);
        }
        if(item.available===false){
          play.disabled=true;card.append(element('p','Fichier modifié ou absent. Actualisez la vidéothèque.','small catalogue-warning'));
        }
        target.append(card);
      }
      document.dispatchEvent(new CustomEvent('survie:video-cards',{detail:items}));
      for(const card of target.querySelectorAll('.video-library-card:not(:has(.video-card-tools))')){
        const controls=card.querySelectorAll(':scope > details:not(.video-card-tools)');
        if(!controls.length)continue;
        const options=element('details',undefined,'video-card-tools video-disclosure');
        options.append(element('summary','Options de sous-titrage'),...controls);
        card.append(options);
      }
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
  document.addEventListener('survie:auth',()=>{version++;renderedQuery=null;$('video-reader-preparation')?.remove();refresh();});
  document.addEventListener('survie:videos-changed',async()=>{renderedQuery=null;await refresh();updateReaderTracks?.();});
  setInterval(()=>{if(latest?.status.phase==='running'&&!document.hidden&&(!$('next-collections').hidden||activeMedia?.isConnected&&!$('reader').hidden&&!$('view-library').hidden))refresh();},1500);
  document.addEventListener('survie:source',event=>{
    updateReaderTracks=null;
    if(activeMedia){activeMedia.pause();activeMedia=null;}
    const source=event.detail;if(source.kind!=='video')return;
    const reader=$('reader'),body=reader.querySelector('.reader-body'),player=element('video');activeMedia=player;
    const actions=reader.querySelector('.reader-actions');
    const ask=actions.querySelector('button:nth-child(2)');
    if(ask)ask.textContent='Question sur la vidéo';
    const original=actions.querySelector('a.secondary-link');
    if(original){original.textContent='Ouvrir le fichier vidéo →';original.href=source.url;}
    const more=element('details',undefined,'video-disclosure video-player-more');
    const moreActions=element('div',undefined,'video-actions');
    moreActions.append(...[...actions.children].slice(2));
    more.append(element('summary','Plus d’options'),moreActions);
    const origin=reader.querySelector('.source-details');
    const sourceDate=reader.querySelector('.source-dates');
    if(origin){
      origin.querySelector('summary').textContent='Origine de la vidéo';
      if(source.document_date)origin.append(sourceDate);
    }
    if(!source.document_date)sourceDate?.remove();
    const preview=body.nextElementSibling;
    if(source.preview&&preview?.matches('p.muted.small'))preview.remove();
    player.controls=true;player.preload='metadata';player.playsInline=true;player.src=source.url;
    const videoKey=S.user?.id+':'+source.id.split('#t=')[0];
    const positionKey='survie:video:'+videoKey;
    const subtitleKey='survie:video-subtitles:'+videoKey;
    let saved=null,lastPositionSave=0,preference='auto';
    try{preference=localStorage.getItem(subtitleKey)||'auto';}catch(_){}
    try{saved=JSON.parse(localStorage.getItem(positionKey)||'null');}catch(_){}
    function remember(){const now=performance.now();if(now-lastPositionSave<2000&&!player.paused)return;lastPositionSave=now;try{localStorage.setItem(positionKey,JSON.stringify({revision:source.video_revision,seconds:player.currentTime}));}catch(_){}}
    player.addEventListener('timeupdate',remember);player.addEventListener('pause',remember);
    const stage=element('div',undefined,'video-player-stage');stage.append(player);
    const captions=element('section',undefined,'video-player-captions');
    captions.setAttribute('aria-label','Sous-titres');
    const notice=element('p',undefined,'small catalogue-warning');
    const limits=element('details',undefined,'video-disclosure video-player-limits');
    limits.append(element('summary','Qualité des sous-titres'),notice);
    const transcript=element('details',undefined,'video-disclosure video-player-transcript');
    transcript.append(element('summary','Lire la transcription'));
    if(source.preview)transcript.append(element('p','Extrait des paroles à partir du passage ouvert.','small muted'));
    const select=element('select');select.setAttribute('aria-label','Sous-titres de la vidéo');
    const label=element('label','Sous-titres');label.append(select);
    const preparation=element('section');preparation.id='video-reader-preparation';
    preparation.setAttribute('aria-label','Préparation des sous-titres');
    const invalid=element('p','Certaines pistes échouent aux contrôles techniques ; elles ne sont pas proposées en lecture. Consultez le rapport vidéo.','small');
    const problem=element('p',undefined,'small');problem.hidden=true;player.addEventListener('error',()=>{problem.hidden=false;problem.textContent='Ce navigateur ne peut pas lire ce format ou le fichier ne répond pas. Ouvrez le média original avec un lecteur installé. Les sous-titres restent consultables ci-dessous.';});
    captions.append(label,preparation,limits);
    limits.append(invalid);
    body.before(stage,problem,captions,transcript);
    transcript.append(body);
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
      limits.hidden=!source.tracks?.length;
      invalid.hidden=!(source.tracks||[]).some(track=>track.status!=='passed');
      body.replaceChildren();
      transcript.hidden=!source.transcription_available;
      if(source.transcription_available)renderDocument(body,source);
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
    transcript.after(more);
    if(origin)more.after(origin);
  });
  new MutationObserver(()=>{if(activeMedia&&($('reader').hidden||$('view-library').hidden)){activeMedia.pause();}}).observe($('view-library'),{subtree:true,attributes:true,attributeFilter:['hidden']});
})();
