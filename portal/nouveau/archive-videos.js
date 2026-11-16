/* Explicit preparation of videos inside collections, independent of the AI. */
(() => {
  const area=element('details');area.id='next-archive-videos';area.innerHTML='<summary>Vidéos dans les collections</summary><p class="small">Les collections peuvent contenir des vidéos et leurs sous-titres. Examinez-les une fois pour les retrouver avec les autres vidéos. Cette préparation ne télécharge rien et ne lance pas l’IA. Une vidéo externe liée à un article n’est pas forcément incluse sur cet appareil.</p><p id="next-archive-videos-status" class="small" role="status"></p><div id="next-archive-videos-actions" class="actions"><button id="next-archive-videos-start" class="secondary">Examiner ou reprendre les collections</button><button id="next-archive-videos-pause" class="secondary" hidden>Mettre l’examen en pause</button><button id="next-archive-videos-refresh" class="secondary" hidden>Actualiser le lecteur vidéo</button><button id="next-archive-videos-report" class="secondary">Télécharger le rapport des collections</button></div><p id="next-archive-videos-message" class="small" role="status"></p>';
  $('next-videos').append(area);let latest=null,busy=false,loading=false,generation=0;
  const states={not_started:'Les vidéos des collections n’ont pas encore été examinées.',preparing:'Lancement de l’examen sur le PC serveur…',running:'Examen en cours. Les résultats déjà prêts restent utilisables.',paused:'Examen en pause. Reprenez-le à votre demande.',error:'L’examen s’est interrompu ; les anciens inventaires restent conservés.',partial:'Examen incomplet : certaines collections restent à vérifier.',completed:'Examen terminé. La qualité des paroles et leur synchronisation restent à vérifier.'};
  async function refresh(){
    if(!S.authReady||!S.user||loading||busy||document.hidden)return;
    loading=true;const current=++generation,profile=S.user.id;
    try{
      const value=await api('/zim-videos');if(current!==generation||profile!==S.user?.id)return;
      const becameReady=value.reader_ready&&!latest?.reader_ready;latest=value;
      const results=value.results||[],media=results.reduce((sum,row)=>sum+(row.video_resources||0),0),tracks=results.reduce((sum,row)=>sum+(row.usable_tracks||0),0);
      $('next-archive-videos-status').textContent=(states[value.phase]||'État de l’examen à vérifier.')+(!['not_started','preparing'].includes(value.phase)?' '+value.completed+' / '+value.archives+' collection(s) examinée(s) · '+media+' fichier(s) vidéo · '+tracks+' piste(s) lisible(s).':'')+(value.reader_updating?' Mise à jour du lecteur et de la recherche…':'')+(value.control_notice?' '+value.control_notice:'');
      $('next-archive-videos-actions').hidden=S.user.role!=='admin';$('next-archive-videos-start').disabled=['preparing','running'].includes(value.phase)||value.reader_updating;
      $('next-archive-videos-pause').hidden=!['preparing','running'].includes(value.phase);$('next-archive-videos-refresh').hidden=!['completed','partial'].includes(value.phase)||value.reader_ready||value.reader_updating;
      if(becameReady)document.dispatchEvent(new Event('survie:videos-changed'));
    }catch(error){if(current===generation)$('next-archive-videos-message').textContent=error.message;}
    finally{loading=false;}
  }
  async function command(action){
    if(busy)return;busy=true;const profile=S.user?.id;
    $('next-archive-videos-message').textContent='Commande en cours…';
    try{await api(action==='refresh'?'/admin/videos/index':'/admin/zim-videos/'+action,{});if(S.user?.id===profile)$('next-archive-videos-message').textContent='Commande reçue. Les inventaires terminés sont conservés.';}
    catch(error){if(S.user?.id===profile)$('next-archive-videos-message').textContent=error.message;}
    finally{busy=false;}
    await refresh();
  }
  $('next-archive-videos-start').onclick=()=>command('start');$('next-archive-videos-pause').onclick=()=>command('pause');$('next-archive-videos-refresh').onclick=()=>command('refresh');
  $('next-archive-videos-report').onclick=async()=>{try{const profile=S.user?.id,report=await api('/admin/zim-videos/report');if(profile===S.user?.id)downloadReport(report,'videos-collections');}catch(error){$('next-archive-videos-message').textContent=error.message;}};
  document.addEventListener('survie:auth',()=>{generation++;latest=null;if(area.open)refresh();});
  area.addEventListener('toggle',()=>{if(area.open)refresh();});
  setInterval(()=>{if(!$('next-collections').hidden&&(area.open||['preparing','running'].includes(latest?.phase)||latest?.reader_updating))refresh();},2000);
})();
