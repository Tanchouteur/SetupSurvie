/* Explicit measurements, synthetic trials and local JSON reports. */
(() => {
  const seconds=value=>Number.isFinite(value)?(value/1000).toLocaleString('fr-FR',{maximumFractionDigits:1})+' s':'Non mesuré';
  const modeName=mode=>S.status?.modes?.find(item=>item.id===mode)?.name||mode;
  function download(report,name){const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})),link=element('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  function summaryList(target,rows){const list=element('dl',undefined,'assistant-measures');for(const [label,value] of rows)list.append(element('dt',label),element('dd',value));target.append(list);}

  let jobs=[],owner=null,selectedReport=null;
  const open=button('Voir les durées',()=>{
    const select=$('next-response-measure');select.replaceChildren();
    for(const job of jobs)select.append(new Option(new Date(job.created*1000).toLocaleString('fr-FR')+' · '+modeName(job.mode),job.id));
    dialog.showModal();loadMeasure();
  },'text-button');open.id='next-response-measures-open';open.hidden=true;$('chat-status').parentElement.append(open);
  const dialog=element('dialog',undefined,'assistant-diagnostic-dialog');dialog.id='next-response-measures-dialog';dialog.setAttribute('aria-labelledby','next-response-measures-title');
  dialog.innerHTML='<h2 id="next-response-measures-title">Durées de l’assistant</h2><label>Réponse à examiner<select id="next-response-measure"></select></label><div id="next-response-measures-body"></div><p class="small muted">Ces durées décrivent cet essai. Le rapport ne contient ni votre question, ni la réponse, ni les textes des documents.</p><div class="actions"><button id="next-response-measures-export" class="secondary" disabled>Télécharger le rapport</button><button data-close="next-response-measures-dialog" class="secondary">Fermer</button></div>';
  document.body.append(dialog);
  dialog.querySelector('[data-close]').onclick=()=>dialog.close();
  async function loadMeasure(){
    const id=$('next-response-measure').value,body=$('next-response-measures-body');body.replaceChildren(element('p','Lecture des mesures…'));$('next-response-measures-export').disabled=true;
    try{
      const report=await api('/jobs/'+encodeURIComponent(id)+'/measurements');if($('next-response-measure').value!==id)return;selectedReport=report;body.replaceChildren();
      if(report.simulated)body.append(element('p','Mesures simulées de la recette, sans modèle réel.','small muted'));
      const phases=report.phases_ms||{};
      summaryList(body,[['Temps total',seconds(report.total_ms)],['Dans la file d’attente',seconds(phases.queue)],['Recherche documentaire',seconds(phases.search)],['Lecture des sources',seconds(phases.reading)],['Changement ou reprise du modèle',seconds(phases.model_loading)],['Préparation par le modèle',seconds(phases.model_preparation)],['Reprises automatiques',String(report.model_retries?.length||0)],['Rédaction',seconds(phases.writing)],['Premier texte généré',seconds(report.first_text_ms)]]);
      const loads=(report.model_calls||[]).map(call=>call.load_ms).filter(Number.isFinite),load=loads.length?loads.reduce((sum,value)=>sum+value,0):undefined;
      body.append(element('p','Chargement annoncé par le moteur : '+seconds(load)+'. Il est compris dans les phases ci-dessus.','small muted'));
      const allocated=report.runtime_after?.running?.context_length;
      summaryList(body,[['Modèle',report.model],['Contexte utilisé pour la demande',String(report.context)+' tokens'],['Contexte observé dans le moteur',allocated?allocated+' tokens':'Non mesuré'],['Sources consultées',String(report.sources_read||0)],['Documents choisis',Number.isFinite(report.selected_sources)?String(report.selected_sources):'Non mesuré'],['Documents préparés',Number.isFinite(report.prepared_sources)?String(report.prepared_sources):'Non mesuré'],['Liaisons ajoutées aux sources',Number.isFinite(report.citation_linking?.applied)?String(report.citation_linking.applied):'Non mesuré'],['Temps pour relier les sources',seconds(phases.source_linking)],['Appels au modèle',String(report.model_calls?.length||0)]]);
      if(report.context_limited)body.append(element('p','La limite annoncée par le modèle a réduit le contexte demandé.','small'));
      if(report.failure)body.append(element('p',({context_budget:'La question, les outils et les extraits dépassaient le budget d’entrée.',output_limit:'Le budget de réponse du modèle a été atteint.',no_final_text:'Le modèle n’a pas produit de texte final.',memory_error:'Le moteur a signalé un manque de mémoire.',model_error:'Le moteur a interrompu la réponse.',engine_http_error:'Le moteur a renvoyé une erreur.',time_limit:'Le temps maximal de réponse a été atteint.',engine_unavailable:'Le moteur était indisponible.'})[report.failure]||'La réponse n’a pas pu se terminer.','small catalogue-warning'));
      $('next-response-measures-export').disabled=false;
    }catch(error){body.replaceChildren(element('p',error.message,'error'));}
  }
  $('next-response-measure').onchange=loadMeasure;
  $('next-response-measures-export').onclick=()=>{if(selectedReport)download(selectedReport,'setupsurvie-assistant-'+$('next-response-measure').value+'.json');};
  document.addEventListener('survie:new-conversation',()=>{owner=S.conversation;jobs=[];open.hidden=true;});
  document.addEventListener('survie:conversation',event=>{owner=event.detail.id;jobs=event.detail.measurement_jobs||[];open.hidden=!jobs.length;});
  document.addEventListener('survie:job',event=>{
    if(owner!==S.conversation){owner=S.conversation;jobs=[];}
    const data=event.detail;if(!data.measurements)return;
    jobs=[{id:data.id,mode:data.mode,created:data.created,status:data.status},...jobs.filter(job=>job.id!==data.id)].slice(0,20);open.hidden=false;
  });

  const details=element('details',undefined,'context-trial');details.innerHTML='<summary>Mesurer un contexte adapté à ce PC</summary><p>L’essai utilise uniquement le modèle déjà installé et un texte fictif. Il peut durer jusqu’à une heure. Gardez ce moment pour les mesures ; une nouvelle question ou le mode jeu arrête l’essai. La bibliothèque reste consultable.</p><p class="small muted">Le modèle choisi est chargé puis déchargé pour comparer les essais à froid et à chaud. Le réglage courant reste conservé jusqu’à votre choix.</p><form id="next-calibration-form"><label>Mode à mesurer<select id="next-calibration-mode"></select></label><label>Comparer jusqu’à<select id="next-calibration-limit"><option value="16384">16k tokens</option><option value="32768" selected>32k tokens</option><option value="65536">64k tokens, si le modèle le permet</option></select></label><button id="next-calibration-start" type="submit">Lancer l’essai avec l’IA locale</button></form><p id="next-calibration-status" role="status"></p><div id="next-calibration-results"></div><div class="actions"><button id="next-calibration-stop" class="secondary" hidden>Arrêter l’essai</button><button id="next-calibration-apply" hidden>Utiliser le contexte mesuré</button><button id="next-calibration-rollback" class="secondary" hidden>Revenir au réglage précédent</button><button id="next-calibration-export" class="secondary" hidden>Télécharger le rapport mémoire</button></div>';
  $('next-context-form').closest('article').append(details);
  let calibrationReport=null,busy=false,refreshing=false;
  function fillModes(){
    const select=$('next-calibration-mode');if(select.options.length||!S.status?.modes?.length)return;
    for(const mode of S.status.modes)select.append(new Option(mode.name,mode.id));
  }
  function renderCalibration(report){
    calibrationReport=report;const active=report.status==='running';
    $('next-calibration-start').disabled=active||busy;$('next-calibration-mode').disabled=active;$('next-calibration-limit').disabled=active;
    $('next-calibration-stop').hidden=!active;$('next-calibration-apply').hidden=report.status!=='completed'||!report.recommendation||report.configured_context===report.recommendation;
    $('next-calibration-rollback').hidden=!report.can_rollback;$('next-calibration-export').hidden=report.status==='not_started';
    $('next-calibration-status').textContent=report.message||(report.status==='not_started'?'Aucun essai mémoire enregistré.':'Essai en cours.');
    const result=$('next-calibration-results');result.replaceChildren();
    if(report.model)result.append(element('p',modeName(report.mode)+' · '+report.model,'small muted'));
    if(report.recommendation)result.append(element('p','Contexte retenu par cet essai : '+(report.recommendation/1024)+'k tokens. Cette mesure ne garantit pas la qualité des réponses.','small'));
    if(report.configured_context)result.append(element('p','Réglage courant : '+(report.configured_context/1024)+'k tokens.','small muted'));
    if(report.model_released===false)result.append(element('p','Le déchargement du modèle n’a pas été confirmé. Consultez l’état de l’appareil.','small catalogue-warning'));
    for(const trial of report.trials||[]){const card=element('article',undefined,'context-trial-result');
      card.append(element('strong',(trial.context/1024)+'k · '+({probe:'Mesure du volume de texte',cold:'À froid',warm:'À chaud'}[trial.temperature]||'Mesure')));
      card.append(element('p',({running:'En cours',passed:'Mesure terminée',failed:'Mesure arrêtée',cancelled:'Mesure annulée'}[trial.status]||trial.status)+' · '+seconds(trial.duration_ms),'small'));
      if(trial.first_text_ms!==undefined)card.append(element('p','Premier texte : '+seconds(trial.first_text_ms),'small muted'));
      if(trial.minimum_free)card.append(element('p','Mémoire vive libre minimale observée : '+(trial.minimum_free.ram_available/1024**3).toLocaleString('fr-FR',{maximumFractionDigits:1})+' Go.','small muted'));
      result.append(card);
    }
  }
  async function refresh(){
    fillModes();if(document.hidden||$('view-settings').hidden||S.user?.role!=='admin'||refreshing||busy)return;
    refreshing=true;try{renderCalibration(await api('/admin/assistant/calibration'));}catch(error){$('next-calibration-status').textContent=error.message;}finally{refreshing=false;}
  }
  $('next-calibration-form').onsubmit=async event=>{
    event.preventDefault();if(busy)return;busy=true;$('next-calibration-start').disabled=true;
    try{const report=await api('/admin/assistant/calibration/start',{mode:$('next-calibration-mode').value,max_context:Number($('next-calibration-limit').value)});renderCalibration(report);}
    catch(error){$('next-calibration-status').textContent=error.message;}
    finally{busy=false;$('next-calibration-start').disabled=calibrationReport?.status==='running';}
  };
  for(const [name,action] of [['stop','stop'],['apply','apply'],['rollback','../context/rollback']])$('next-calibration-'+name).onclick=async()=>{
    if(busy)return;busy=true;
    try{
      const path=name==='rollback'?'/admin/assistant/context/rollback':'/admin/assistant/calibration/'+action;
      await api(path,name==='apply'?{id:calibrationReport.id}:name==='rollback'?{model:calibrationReport.model}:{});
      renderCalibration(await api('/admin/assistant/calibration'));if(name==='apply'||name==='rollback')toast('Contexte enregistré pour les prochaines réponses.');
    }catch(error){$('next-calibration-status').textContent=error.message;}finally{busy=false;}
  };
  $('next-calibration-export').onclick=()=>{if(calibrationReport)download(calibrationReport,'setupsurvie-memoire-'+calibrationReport.id+'.json');};
  setInterval(refresh,1500);new MutationObserver(refresh).observe($('view-settings'),{attributes:true,attributeFilter:['hidden']});document.addEventListener('survie:auth',refresh);
})();
