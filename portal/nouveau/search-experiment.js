/* Optional human-reviewed comparison; ordinary searches never call this module. */
(() => {
  const host=$('next-search-check-open')?.closest('article');if(!host)return;
  const details=element('details',undefined,'search-experiment');details.id='next-search-experiment';
  details.innerHTML='<summary>Comparer une aide IA à la recherche · essai facultatif</summary><p>Compare la recherche actuelle, deux reformulations française et anglaise, puis un reclassement des résultats par l’IA locale. Cet essai ne change pas la recherche habituelle.</p><p class="small muted">Le modèle installé sera chargé. Réservez un moment disponible : jusqu’à une heure, arrêt possible. Une question ou le mode jeu prend la priorité. Les caches ne sont pas vidés ; ce n’est pas une mesure à froid.</p><form id="next-experiment-form"><label>Modèle à essayer<select id="next-experiment-mode"></select></label><label>Demandes à comparer<select id="next-experiment-suite"><option value="verification">8 demandes de vérification</option><option value="all">32 demandes, réglage et vérification séparés</option></select></label><label>Attente maximale souhaitée par recherche<select id="next-experiment-budget"><option value="5">5 secondes</option><option value="15" selected>15 secondes</option><option value="30">30 secondes</option><option value="60">60 secondes</option></select></label><button id="next-experiment-start">Lancer le comparatif avec l’IA locale</button></form><p id="next-experiment-status" role="status"></p><div id="next-experiment-summary"></div><div class="actions"><button id="next-experiment-stop" class="secondary" hidden>Arrêter le comparatif</button><button id="next-experiment-export" class="secondary" hidden>Télécharger le comparatif</button></div><p class="small muted">Le rapport contient les demandes de test, les titres, de courts extraits et vos avis. Il ne contient pas les conversations. Une proposition ne sera jamais activée automatiquement.</p><div id="next-experiment-cases"></div>';
  host.append(details);
  const names={baseline:'Actuelle',rewritten:'Reformulée',reranked:'Reclassée'},seconds=ms=>Number.isFinite(ms)?(ms/1000).toLocaleString('fr-FR',{maximumFractionDigits:1})+' s':'Non mesuré';
  let report=null,busy=false,refreshing=false,epoch=0;
  function modes(){const select=$('next-experiment-mode');if(!select.options.length)for(const mode of S.status?.modes||[])select.append(new Option(mode.name,mode.id));}
  function summary(){
    const body=$('next-experiment-summary');body.replaceChildren();const data=report?.summary;if(!data)return;
    body.append(element('p',({needs_measurements:'Les mesures sont incomplètes : aucune conclusion.',needs_review:'La comparaison attend votre lecture des documents. Un avis manquant reste inconnu.',needs_coverage:'La couverture de recherche reste partielle : ce rapport ne permet pas de valider l’aide IA.',no_demonstrated_gain:'Aucun gain répondant aux critères n’a été démontré. L’aide reste désactivée.',candidate_to_confirm:'Une amélioration respecte les critères de cet essai. Une seconde mesure sur le PC reste nécessaire avant de décider.'})[data.decision]||'Comparaison à examiner.'));
    for(const [split,methods] of Object.entries(data.splits||{})){
      if(!Object.values(methods).some(m=>m.measured))continue;
      const section=element('div',undefined,'experiment-summary');section.append(element('strong',split==='verification'?'Vérification réservée':'Cas de réglage'));
      for(const [method,m] of Object.entries(methods))section.append(element('p',names[method]+' : '+m.hit5+' besoin(s) avec un résultat utile dans les cinq premiers · '+m.fully_judged+' cas entièrement relus · '+m.unrelated_results+' résultat(s) jugé(s) hors sujet sur '+m.judged_results+' examinés · médiane '+seconds(m.median_ms)+' · cas lent (95 %) '+seconds(m.p95_ms)+(m.errors?' · '+m.errors+' erreur(s)':''),'small'));
      body.append(section);
    }
  }
  function render(data){
    report=data;const active=data.status==='running';
    $('next-experiment-start').disabled=active||busy;for(const field of ['mode','suite','budget'])$('next-experiment-'+field).disabled=active;
    $('next-experiment-stop').hidden=!active;$('next-experiment-export').hidden=data.status==='not_started';
    $('next-experiment-status').textContent=data.status==='not_started'?'Aucun comparatif enregistré.':(data.message||'Comparatif en cours.')+' '+(data.cases?.length||0)+' / '+(data.planned_cases||0)+' demandes commencées.';
    summary();const body=$('next-experiment-cases');body.replaceChildren();
    for(const item of data.cases||[]){
      const card=element('details',undefined,'experiment-case');card.append(element('summary',item.query),element('p',item.need,'small'));
      if(!item.coverage_complete)card.append(element('p','Recherche partielle : cette demande ne peut pas valider l’option. Le détail des limites figure dans le rapport.','small catalogue-warning'));
      for(const [method,arm] of Object.entries(item.methods||{}))card.append(element('p',names[method]+' · '+seconds(arm.elapsed_ms)+(arm.error?' · Essai interrompu, résultats précédents conservés.':''),'small muted'));
      if(!item.candidates.length)card.append(element('p','Aucun candidat trouvé. Cela ne prouve pas que le sujet est absent de la bibliothèque.','small'));
      const list=element('ul',undefined,'experiment-candidates');
      for(const row of item.candidates){
        const li=element('li'),link=element('a',row.title+' ↗');link.href='/#/bibliotheque/recherche?'+new URLSearchParams({q:item.query,collection:item.collection||'',domain:item.domain,source:row.id});link.target='_blank';link.rel='noopener';li.append(link);
        li.append(element('p',Object.entries(names).map(([method,name])=>{const i=item.methods?.[method]?.ids?.indexOf(row.id)??-1;return name+' : '+(i<0?'absent des cinq premiers':i+1);}).join(' · '),'small muted'));
        const label=element('label','Après lecture de ce document'),select=element('select');select.append(new Option('À vérifier','uncertain'),new Option('Utile pour cette demande','useful'),new Option('Ne répond pas à cette demande','unrelated'));
        select.value=item.judgments?.[row.id]||'uncertain';select.disabled=active;
        select.onchange=async()=>{
          if(busy){select.value=report?.cases?.find(c=>c.id===item.id)?.judgments?.[row.id]||'uncertain';return;}busy=true;epoch++;select.disabled=true;
          try{report=await api('/admin/search-experiment/review',{id:data.id,case_id:item.id,judgments:{[row.id]:select.value}});summary();}
          catch(error){$('next-experiment-status').textContent=error.message;select.value=report?.cases?.find(c=>c.id===item.id)?.judgments?.[row.id]||'uncertain';}
          finally{busy=false;select.disabled=false;}
        };
        label.append(select);li.append(label);list.append(li);
      }
      card.append(list);body.append(card);
    }
  }
  async function refresh(force=false){
    modes();if(!details.open||document.hidden||$('view-settings').hidden||S.user?.role!=='admin'||refreshing||busy||(!force&&report?.status!=='running'))return;
    refreshing=true;const ticket=epoch;try{const data=await api('/admin/search-experiment');if(ticket===epoch&&S.user?.role==='admin')render(data);}catch(error){if(ticket===epoch)$('next-experiment-status').textContent=error.message;}finally{refreshing=false;}
  }
  details.addEventListener('toggle',()=>{if(details.open)refresh(true);});document.addEventListener('survie:auth',()=>refresh(true));setInterval(()=>refresh(),1500);
  $('next-experiment-form').onsubmit=async event=>{
    event.preventDefault();if(busy)return;busy=true;epoch++;$('next-experiment-start').disabled=true;
    try{render(await api('/admin/search-experiment/start',{mode:$('next-experiment-mode').value,suite:$('next-experiment-suite').value,latency_budget_seconds:Number($('next-experiment-budget').value)}));}
    catch(error){$('next-experiment-status').textContent=error.message;}finally{busy=false;$('next-experiment-start').disabled=report?.status==='running';}
  };
  $('next-experiment-stop').onclick=async()=>{if(busy)return;busy=true;epoch++;try{render(await api('/admin/search-experiment/stop',{}));}catch(error){$('next-experiment-status').textContent=error.message;}finally{busy=false;}};
  $('next-experiment-export').onclick=()=>{if(!report)return;const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})),a=element('a');a.href=url;a.download='setupsurvie-comparatif-'+report.id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
})();
