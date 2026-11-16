/* Existing local captions only. Playback never starts inference or a download. */
(() => {
  const panel=element('section');panel.id='next-videos';panel.innerHTML='<h2>Vidéos locales</h2><p class="small muted">Les titres et descriptions se cherchent avec le filtre ci-dessus. La recherche dans les documents retrouve aussi les paroles dont les sous-titres sont indexés.</p><div id="next-videos-admin" class="actions"><button id="next-videos-index" class="secondary">Actualiser les vidéos et leurs sous-titres</button><button id="next-videos-stop" class="secondary" hidden>Arrêter l’inventaire</button><button id="next-videos-report" class="secondary">Télécharger le rapport vidéo</button></div><p id="next-videos-status" class="small" role="status"></p><div id="next-videos-list" class="collections"></div><button id="next-videos-more" class="secondary" hidden>Voir les vidéos suivantes</button>';
  $('next-collections').append(panel);
  const states={french_available:'Sous-titres français présents · à vérifier',french_prepared:'Français préparé localement · relecture à faire',source_only:'Sous-titres dans la langue source',missing:'Sous-titres à préparer',invalid:'Sous-titres présents mais illisibles',unknown:'Langue des sous-titres à identifier'};
  let offset=0,version=0,busy=false,timer=null,latest=null,activeMedia=null;
  async function refresh(append=false){
    if(!S.authReady||!S.user)return;
    const current=++version,q=$('collection-filter').value;
    try{
      const data=await api('/videos?offset='+(append?offset:0)+'&q='+encodeURIComponent(q));if(current!==version)return;
      latest=data;$('next-videos-admin').hidden=S.user.role!=='admin';
      $('next-videos-list').hidden=false;
      const running=data.status.phase==='running';$('next-videos-index').disabled=running||busy;$('next-videos-stop').hidden=!running;
      const phase={not_started:'Actualisez les vidéos pour préparer leur recherche.',running:'Inventaire en cours ; les anciens résultats restent utilisables.',paused:'Inventaire arrêté ; ancien index conservé.',interrupted:'Inventaire interrompu ; relancez-le explicitement.',failed:data.status.error||'Inventaire indisponible.',completed:'Inventaire terminé.'}[data.status.phase]||'';
      $('next-videos-status').textContent=data.total+' vidéo(s) correspondante(s). '+phase+(running?' '+(data.status.videos||0)+' vidéo(s) examinée(s).':'');
      const target=$('next-videos-list');if(!append){target.replaceChildren();offset=0;}
      for(const item of data.videos){
        const card=element('article',undefined,'data-card');card.append(element('h3',item.title),element('p',item.collection||'Vidéo locale','small muted'),element('p',states[item.subtitle_status]||'État inconnu','small'),button('Voir la vidéo →',()=>readSource(item.id),'secondary'));
        card.dataset.videoId=item.id;
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
    try{const report=await api('/admin/videos/report'),url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})),link=element('a');link.href=url;link.download='setupsurvie-videos-'+new Date().toISOString().slice(0,10)+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
    catch(error){$('next-videos-status').textContent=error.message;}
  };
  document.addEventListener('survie:collection-filter',()=>{version++;$('next-videos-list').hidden=true;clearTimeout(timer);timer=setTimeout(()=>refresh(),250);});
  new MutationObserver(()=>{if(!$('next-collections').hidden)refresh();}).observe($('next-collections'),{attributes:true,attributeFilter:['hidden']});
  document.addEventListener('survie:auth',()=>{version++;refresh();});
  document.addEventListener('survie:videos-changed',()=>refresh());
  setInterval(()=>{if(latest?.status.phase==='running'&&!document.hidden&&!$('next-collections').hidden)refresh();},1500);
  document.addEventListener('survie:source',event=>{
    if(activeMedia){activeMedia.pause();activeMedia=null;}
    const source=event.detail;if(source.kind!=='video')return;
    const reader=$('reader'),body=reader.querySelector('.reader-body'),player=element('video');activeMedia=player;
    player.controls=true;player.preload='metadata';player.playsInline=true;player.style.width='100%';player.style.maxHeight='60vh';player.src=source.url;
    const positionKey='survie:video:'+S.user?.id+':'+source.id.split('#t=')[0];let saved=null,lastPositionSave=0;
    try{saved=JSON.parse(localStorage.getItem(positionKey)||'null');}catch(_){}
    function remember(){const now=performance.now();if(now-lastPositionSave<2000&&!player.paused)return;lastPositionSave=now;try{localStorage.setItem(positionKey,JSON.stringify({revision:source.video_revision,seconds:player.currentTime}));}catch(_){}}
    player.addEventListener('timeupdate',remember);player.addEventListener('pause',remember);
    const notice=element('p',source.video_notice,'small catalogue-warning');
    const usable=(source.tracks||[]).filter(t=>t.status==='passed');let defaultChosen=false;
    for(const track of usable){const node=element('track');node.kind='subtitles';node.src=track.url;node.srclang=track.language||'und';node.label=(track.language||'Langue inconnue')+' · '+({automatic:'automatique',provided:'fournie',unknown:'origine inconnue',local_translation:'traduction locale'}[track.origin]||track.origin);node.default=!defaultChosen&&track.language.startsWith('fr');defaultChosen||=node.default;player.append(node);}
    const select=element('select');select.setAttribute('aria-label','Sous-titres de la vidéo');select.append(new Option('Sans sous-titres','off'));
    usable.forEach((track,index)=>select.append(new Option((track.language||'Langue inconnue')+' · '+({automatic:'automatique',provided:'fournie',unknown:'origine inconnue',local_translation:'traduction locale'}[track.origin]||track.origin),String(index))));
    const french=usable.findIndex(track=>track.language.startsWith('fr'));select.value=french>=0?String(french):'off';
    function apply(){for(let i=0;i<player.textTracks.length;i++)player.textTracks[i].mode=select.value===String(i)?'showing':'disabled';}
    select.onchange=apply;player.addEventListener('loadedmetadata',()=>{const duration=player.duration,wanted=source.position_ms?source.position_ms/1000:saved?.revision===source.video_revision&&Number.isFinite(saved.seconds)?saved.seconds:0;if(wanted>0&&Number.isFinite(duration))player.currentTime=Math.min(wanted,Math.max(0,duration-.1));apply();});
    const label=element('label','Sous-titres');label.append(select);
    const problem=element('p',undefined,'small');problem.hidden=true;player.addEventListener('error',()=>{problem.hidden=false;problem.textContent='Ce navigateur ne peut pas lire ce format ou le fichier ne répond pas. Ouvrez le média original avec un lecteur installé. Les sous-titres restent consultables ci-dessous.';});
    reader.insertBefore(player,body);reader.insertBefore(label,body);reader.insertBefore(notice,body);reader.insertBefore(problem,body);
    if(!source.transcription_available)body.replaceChildren(element('p','Aucun sous-titre exploitable pour cet aperçu. Le titre seul ne permet pas à l’assistant de connaître les paroles.'));
    if((source.tracks||[]).some(t=>t.status!=='passed'))reader.insertBefore(element('p','Certaines pistes échouent aux contrôles techniques ; elles ne sont pas proposées en lecture. Consultez le rapport vidéo.','small'),body);
    const original=reader.querySelector('.reader-actions a');if(original){original.textContent='Ouvrir la vidéo originale →';original.href=source.url;}
  });
  new MutationObserver(()=>{if(activeMedia&&($('reader').hidden||$('view-library').hidden)){activeMedia.pause();}}).observe($('view-library'),{subtree:true,attributes:true,attributeFilter:['hidden']});
})();
