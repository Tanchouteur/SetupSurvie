/* Explicit server-side campaign. Opening this panel performs read-only requests. */
(() => {
  const panel=element('article',undefined,'panel');panel.id='next-performance';
  panel.innerHTML='<h2>Comprendre les lenteurs</h2><p>Un seul essai pour mesurer la recherche, puis l’assistant : CPU, disque, mémoire et temps de chaque étape.</p><p class="small muted">Prévoyez plusieurs minutes, jusqu’à une heure. Le test continue si vous quittez cette page. Démarrez l’assistant avant le test pour inclure l’IA ; un moteur en pause reste en pause. Évitez les autres travaux lourds pendant les mesures.</p><label>Mode de l’assistant à tester<select id="next-performance-mode"></select></label><div class="actions"><button id="next-performance-start">Lancer le diagnostic complet</button><button id="next-performance-stop" class="secondary" hidden>Arrêter le test</button><button id="next-performance-export" class="secondary" disabled>Télécharger le rapport</button></div><p id="next-performance-status" role="status" aria-live="polite">Aucun essai lancé.</p><div id="next-performance-results"></div><p class="small muted">Le rapport contient les mesures et les erreurs, sans vos conversations ni le texte des documents. Une ressource très occupée ne suffit pas à prouver qu’elle cause la lenteur.</p>';
  $('view-settings').append(panel);
  const names={classical:'Recherche sans IA',generation:'Rédaction sans documents',documentary:'Recherche, lecture et réponse IA',selected_documentary:'Réponse avec les documents trouvés déjà choisis'};
  const states={running:'en cours',completed:'terminé',failed:'échec',not_run:'non effectué',interrupted:'interrompu'};
  const phases={baseline:'Mesure du PC au repos',idle:'Mesure du PC au repos',classical:'Recherche documentaire',generation:'Rédaction sans documents',documentary:'Réponse documentaire',search:'Recherche des documents',reading:'Lecture des sources',loading:'Chargement du modèle',preparing:'Préparation du modèle',writing:'Rédaction'};
  const reasons={paused:'assistant en pause',engine_unavailable:'assistant arrêté ou indisponible',model_not_installed:'modèle local absent',other_activity:'une autre demande a pris la priorité',memory_error:'mémoire insuffisante signalée par le moteur',timeout:'délai maximal de cette étape atteint',incomplete_output:'réponse incomplète',measurement_failed:'mesure indisponible'};
  let report=null,busy=false,refreshing=false,owner=null;
  const seconds=value=>Number.isFinite(value)?(value/1000).toLocaleString('fr-FR',{maximumFractionDigits:1})+' s':'';
  function modes(){
    const select=$('next-performance-mode'),previous=select.value,available=S.status?.modes||[];
    if(available.length&&[...select.options].map(o=>o.value).join('|')!==available.map(o=>o.id).join('|')){
      select.replaceChildren(...available.map(m=>new Option(m.name,m.id)));
      if(available.some(m=>m.id===previous))select.value=previous;
    }
  }
  function render(value){
    report=value;const running=value.status==='running';
    $('next-performance-start').disabled=busy||running||!$('next-performance-mode').options.length;
    $('next-performance-mode').disabled=running||busy;$('next-performance-stop').hidden=!running;
    $('next-performance-export').disabled=busy||value.status==='not_started';
    $('next-performance-status').textContent=(value.message||'Aucun essai lancé.')+(running?' '+(phases[value.current_phase]||'Mesures en cours')+' · '+(value.steps||[]).filter(r=>r.status!=='running').length+'/'+(value.planned_steps||11)+' étapes terminées.':'');
    const target=$('next-performance-results');target.replaceChildren();
    for(const row of value.steps||[]){
      const item=element('p',(names[row.kind]||'Mesure')+' · passage '+row.repeat+' : '+(states[row.status]||row.status)+' '+seconds(row.elapsed_ms),'small');
      if(row.query)item.append(document.createTextNode(' · « '+row.query+' »'));
      if(row.reason)item.append(document.createTextNode(' · '+(reasons[row.reason]||'voir le rapport')));
      if(row.coverage_limit==='no_sources_read')item.append(document.createTextNode(' · aucun document effectivement lu'));
      target.append(item);
    }
    if(value.status!=='not_started'&&value.sample_count===0)target.append(element('p','Aucune mesure matérielle encore reçue. Le rapport précise les compteurs indisponibles.','small muted'));
    else if(value.sample_count>0&&value.host_sample_count===0)target.append(element('p','Les compteurs matériels ne sont pas disponibles. Les durées restent mesurées ; le rapport expliquera cette limite.','small catalogue-warning'));
    if(value.status!=='running'&&value.status!=='not_started')target.append(element('p','Téléchargez le fichier JSON et transmettez-le pour l’analyse des lenteurs.','small'));
  }
  async function refresh(){
    modes();if(owner!==S.user?.id){owner=S.user?.id;report=null;render({status:'not_started'});}
    panel.hidden=S.user?.role!=='admin';if(panel.hidden||document.hidden||$('view-settings').hidden||refreshing||busy)return;
    refreshing=true;try{const id=S.user.id,value=await api('/admin/performance');if(S.user?.id===id)render(value);}catch(error){$('next-performance-status').textContent=error.message;}finally{refreshing=false;}
  }
  async function action(name){
    if(busy)return;busy=true;if(report)render(report);const id=S.user?.id;
    let failure='';try{const value=await api('/admin/performance/'+name,name==='start'?{mode:$('next-performance-mode').value}:{});if(id===S.user?.id)render(value);}
    catch(error){failure=error.message;}
    finally{busy=false;if(report)render(report);else $('next-performance-start').disabled=false;if(failure&&id===S.user?.id)$('next-performance-status').textContent=failure;}
  }
  $('next-performance-start').onclick=()=>action('start');$('next-performance-stop').onclick=()=>action('stop');
  $('next-performance-export').onclick=async()=>{
    if(busy)return;busy=true;const id=S.user?.id;
    try{const value=await api('/admin/performance/report');if(id!==S.user?.id)return;
      downloadReport(value,'performances-'+value.mode);
    }catch(error){$('next-performance-status').textContent=error.message;}finally{busy=false;}
  };
  setInterval(refresh,2000);new MutationObserver(refresh).observe($('view-settings'),{attributes:true,attributeFilter:['hidden']});document.addEventListener('survie:auth',refresh);refresh();
})();
