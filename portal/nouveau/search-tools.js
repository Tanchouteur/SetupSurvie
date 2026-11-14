/* Optional preparation runs on the server; closing this page never stops a job. */
(() => {
  let models=[],loaded=false,busy=false,indexLoaded=false,indexReport=null;
  async function refresh(){
    if(document.hidden||$('view-settings').hidden||S.user?.role!=='admin'||busy)return;
    busy=true;
    try{
      const data=await api('/admin/library'),index=data.search_index||{},queue=data.index_queue||{};
      indexReport={version:S.status?.version,created:new Date().toISOString(),phase:data.phase,message:data.message,index_reader_ready:data.index_reader_ready,reader_probe:data.reader_probe||index.reader_probe,index_queue:queue,index};
      const reasons={source_changed:'Une archive a changé après vérification ; contrôlez-la avant la préparation automatique.',user:'Indexation en pause à votre demande.',interrupted:'Indexation interrompue : choisissez Reprendre.',error:'Indexation à vérifier avant reprise.',disabled:'Préparation automatique désactivée.',gaming:'Préparation différée pendant le mode jeu.',schedule:'En attente du créneau horaire choisi.',missing_reader:'Préparez d’abord l’outil pour rendre ces archives recherchables.',selection_pending:'Une sélection de téléchargement attend votre choix.',other_operation:'Une autre préparation est en cours.',insufficient_storage:'Espace disponible ou limite du laboratoire à vérifier.',operation_busy:'En attente de la fin d’une opération sur les documents.'};
      $('next-index-status').textContent=(data.message||'')+' · Index : '+(index.completed||0)+' / '+(index.archives||0)+' archives examinées · '+(index.articles||0)+' articles indexés.'+(queue.pending?' '+queue.pending+' archive(s) en attente.':'')+(queue.waiting_reason?' '+(reasons[queue.waiting_reason]||'Préparation en attente.'):'');
      if(Array.isArray(index.results)){
        const native=index.results.filter(row=>row.status==='kiwix_index').length,ready=index.results.filter(row=>row.status==='ready').length,failed=index.results.filter(row=>row.status==='error').length;
        $('next-index-status').textContent+=' '+native+' archive(s) utilisent leur index intégré · '+ready+' index local(aux) prêts'+(failed?' · '+failed+' archive(s) en erreur. Téléchargez le rapport d’indexation pour leur diagnostic.':'.');
      }
      if(index.error_summary){const names={storage_reserve:'réserve d’espace libre insuffisante',storage_full:'disque plein',source_changed:'archive modifiée pendant le traitement',source_missing:'archive absente',permission_denied:'accès au fichier refusé',reader_import:'lecteur impossible à charger',sqlite_error:'erreur de l’index local',archive_error:'archive non lisible par l’outil'};
        const problems=Object.entries(index.error_summary).filter(([reason,count])=>names[reason]&&Number.isInteger(count)&&count>0).map(([reason,count])=>count+' · '+names[reason]);if(problems.length)$('next-index-status').textContent+=' Causes : '+problems.join(' ; ')+'.';
      }
      if(!indexLoaded&&queue.settings){const opts=queue.settings;$('next-index-auto').checked=opts.enabled;$('next-index-from').value=String(opts.start_hour);$('next-index-until').value=String(opts.end_hour);$('next-index-workers').value=String(opts.workers);indexLoaded=true;}
      $('next-index-start').disabled=!data.index_reader_ready; $('next-index-prepare').disabled=['starting','planning','downloading','refreshing'].includes(data.phase);$('next-index-prepare').textContent=data.index_reader_ready?'Vérifier / réparer l’outil':'Préparer l’outil · Internet requis';
      $('next-index-pause').disabled=!['starting','planning','downloading'].includes(data.phase);
      if(!loaded){
        models=(await api('/admin/context')).models;const select=$('next-context-model');select.replaceChildren();for(const row of models)select.append(new Option(row.model,row.model));
        $('next-context-size').value=String(models[0]?.tokens||16384);loaded=true;
      }
    }catch(error){$('next-index-status').textContent=error.message;}
    finally{busy=false;}
  }
  for(let hour=0;hour<24;hour++)for(const id of ['next-index-from','next-index-until'])$(id).append(new Option(String(hour).padStart(2,'0')+' h',String(hour)));
  $('next-index-settings').onsubmit=async event=>{
    event.preventDefault();try{await api('/admin/library/index-settings',{enabled:$('next-index-auto').checked,start_hour:Number($('next-index-from').value),end_hour:Number($('next-index-until').value),workers:Number($('next-index-workers').value)});$('next-index-settings-status').textContent='Préparation automatique enregistrée.';await refresh();}
    catch(error){$('next-index-settings-status').textContent=error.message;}
  };
  $('next-index-export').onclick=()=>{
    if(!indexReport)return;const url=URL.createObjectURL(new Blob([JSON.stringify(indexReport,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='setupsurvie-indexation-'+new Date().toISOString().slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
  for(const [id,action] of [['prepare','prepare'],['start','start'],['pause','pause']])$('next-index-'+id).onclick=async()=>{
    try{await api('/admin/library/index/'+action,{});$('next-index-status').textContent='Commande transmise au PC serveur.';await refresh();}
    catch(error){$('next-index-status').textContent=error.message;}
  };
  $('next-context-model').onchange=()=>{$('next-context-size').value=String(models.find(m=>m.model===$('next-context-model').value)?.tokens||16384);};
  $('next-context-form').onsubmit=async event=>{
    event.preventDefault();try{const row=await api('/admin/context',{model:$('next-context-model').value,tokens:Number($('next-context-size').value)});const previous=models.find(m=>m.model===row.model);if(previous)previous.tokens=row.tokens;$('next-context-status').textContent='Contexte enregistré pour les prochaines réponses.';}
    catch(error){$('next-context-status').textContent=error.message;}
  };
  setInterval(refresh,5000);new MutationObserver(refresh).observe($('view-settings'),{attributes:true,attributeFilter:['hidden']});
})();
