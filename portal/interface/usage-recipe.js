/* Read-only acceptance recipe. Human observations never become automatic proof. */
(() => {
  const dialog=$('next-usage-dialog');if(!dialog)return;
  const manual=[
    ['original','Lire un résultat et son original','Ouvrez un résultat dans la bibliothèque, puis son original illustré. Vérifiez que le texte et les images attendus sont lisibles.'],
    ['pdf','Lire un PDF','Ouvrez un guide PDF, changez de page et revenez à la bibliothèque. Si aucun PDF n’est essayé, laissez Non effectué.'],
    ['history','Revenir en arrière et en avant','Après une recherche filtrée, ouvrez un document puis utilisez les flèches du navigateur. La recherche, ses filtres et la lecture doivent correspondre.'],
    ['reload','Recharger la recherche','Actualisez une recherche avec ses filtres. Vérifiez les filtres restaurés et les documents trouvés.'],
    ['tabs','Utiliser deux onglets','Ouvrez deux recherches différentes dans deux onglets. Chacun doit conserver sa propre demande.'],
    ['profiles','Retrouver ses données après un changement de profil','Changez de profil puis revenez à celui de cet essai. Vérifiez vos conversations et favoris ; ne recopiez pas leur contenu dans le rapport.'],
    ['draft','Retrouver un brouillon','Écrivez un brouillon, changez de page puis revenez. Son texte doit être conservé.'],
    ['screen','Lire confortablement sur cet appareil','À un zoom normal, vérifiez les boutons, le clavier et le défilement. Sur téléphone, essayez une recherche et une lecture.'],
    ['rescue','Lire les documents de secours','Ouvrez Documents de secours et une collection depuis cette page.'],
    ['restart','Retrouver l’usage après un redémarrage normal','Après un redémarrage normal déjà prévu du serveur, refaites une recherche et retrouvez vos données. Cet outil ne redémarre rien.'],
    ['index_resume','Reprendre une indexation mise en pause','Si une préparation est en cours, utilisez sa pause puis sa reprise explicite et vérifiez les index terminés. Sinon laissez Non effectué.'],
    ['update','Conserver ses données après une mise à jour','Après une mise à jour déjà prévue, vérifiez profils, conversations, favoris et sources. Cet outil ne lance pas de mise à jour.'],
    ['restore','Restaurer une copie d’essai','Sur une installation d’essai séparée seulement, restaurez une sauvegarde puis retrouvez une recherche et les données attendues.'],
    ['faults','Vérifier les pannes sur une copie jetable','Réservé à une recette technique séparée : catalogue absent, index ancien ou illisible, espace insuffisant et interruption. Ne provoquez pas ces pannes ici.']
  ];
  const choices={unperformed:'Non effectué',passed:'Essai réussi',failed:'Problème rencontré',not_applicable:'Ne s’applique pas à cet essai'};
  const labels={health:'Portail local',health_after:'Version à la fin du contrôle',engine_before:'État de l’IA avant',diagnostic:'Accès documentaire',all:'Recherche dans toute la bibliothèque',resilience:'Recherche Autonomie et résilience',source:'Lecture d’un aperçu',engine_after:'État de l’IA après',rescue:'Page de secours'};
  const network=$('next-usage-network'),device=$('next-usage-device'),note=$('next-usage-note'),status=$('next-usage-status'),results=$('next-usage-results');
  let report=null,owner=null,controller=null,epoch=0,storageProblem=false;
  const version=()=>typeof S.status?.version==='string'?S.status.version.slice(0,64):null;
  const key=()=>owner&&report?.version?'survie-usage-v1:'+owner+':'+report.version:null;
  const fresh=()=>({schema:1,kind:'usage_recipe',reference:'2026-11-14.1',created:new Date().toISOString(),version:version(),status:'draft',context:{network:'unknown',device:'unknown',internet_evidence:'operator_declaration'},manual:manual.map(([id])=>({id,state:'unperformed'})),note:'',measurements:[]});
  function persist(){try{const name=key();if(name)localStorage.setItem(name,JSON.stringify({schema:1,created:report.created,version:report.version,context:report.context,manual:report.manual,note:report.note}));storageProblem=false;}catch(_){storageProblem=true;conclusion();}}
  function lockedContext(){return !!report&&(report.measurements.length>0||report.manual.some(row=>row.state!=='unperformed'));}
  function controls(){const busy=!!controller;network.disabled=device.disabled=busy||lockedContext();$('next-usage-run').disabled=$('next-usage-new').disabled=busy;$('next-usage-cancel').hidden=!busy;$('next-usage-export').disabled=busy;for(const select of dialog.querySelectorAll('[data-usage-step]'))select.disabled=busy;}
  function conclusion(restored=false){
    const message=({running:'Contrôles locaux en cours…',measured:'Contrôles terminés ; les étapes humaines restent à effectuer.',cancelled:'Contrôles arrêtés ; mesures reçues conservées.',timed_out:'Limite de 90 secondes atteinte ; mesures reçues conservées.',version_changed:'La version du serveur a changé. Actualisez le site avant de poursuivre.',error:'Le contrôle a été interrompu ; les mesures reçues sont conservées.'})[report.status];
    status.textContent=(message||(restored?'Étapes précédentes retrouvées. Relancez les contrôles pour obtenir des mesures après ce chargement.':'Choisissez les conditions de cet essai, puis lancez les contrôles. Les étapes humaines restent à vérifier.'))+(report.context.network==='disconnected'?' Internet coupé est votre déclaration, pas une détection automatique.':' Cet essai ne démontre pas un usage sans Internet.')+(storageProblem?' La mémoire de ce navigateur est indisponible ; téléchargez le rapport avant de partir.':'');
  }
  function load(){
    epoch++;controller?.abort();controller=null;
    owner=S.user?.id;report=fresh();let restored=false;
    try{const saved=JSON.parse(localStorage.getItem(key()));
      if(saved?.schema===1&&saved.version===report.version&&typeof saved.created==='string'&&Number.isFinite(Date.parse(saved.created))){
        report.created=saved.created;
        for(const [name,select] of [['network',network],['device',device]])if([...select.options].some(option=>option.value===saved.context?.[name]))report.context[name]=saved.context[name];
        for(const row of report.manual){const previous=Array.isArray(saved.manual)&&saved.manual.find(value=>value?.id===row.id);if(previous&&Object.hasOwn(choices,previous.state)){row.state=previous.state;if(typeof previous.at==='string'&&Number.isFinite(Date.parse(previous.at)))row.at=previous.at;}}
        report.note=typeof saved.note==='string'?saved.note.slice(0,600):'';restored=true;
      }
    }catch(_){}
    network.value=report.context.network;device.value=report.context.device;note.value=report.note;results.replaceChildren();
    $('next-usage-manual').replaceChildren();$('next-usage-maintenance').replaceChildren();
    const loaded=report;
    for(const [index,[id,title,text]] of manual.entries()){const label=element('label',undefined,'usage-step'),heading=element('strong',title),description=element('span',text,'small muted'),select=element('select');select.dataset.usageStep=id;select.setAttribute('aria-label',title);for(const [value,caption] of Object.entries(choices))select.append(new Option(caption,value));select.value=report.manual.find(row=>row.id===id).state;select.onchange=()=>{if(owner!==S.user?.id||report!==loaded)return;const row=report.manual.find(row=>row.id===id);row.state=select.value;row.at=new Date().toISOString();persist();controls();};label.append(heading,description,select);$(index<9?'next-usage-manual':'next-usage-maintenance').append(label);}
    conclusion(restored);controls();
  }
  for(const select of [network,device])select.onchange=()=>{if(!report||owner!==S.user?.id)return;report.context.network=network.value;report.context.device=device.value;persist();conclusion();};
  note.oninput=()=>{if(report&&owner===S.user?.id){report.note=note.value.slice(0,600);persist();}};
  $('next-usage-open').onclick=()=>{if(S.user?.role!=='admin')return;if(!report||owner!==S.user.id||version()&&report.version!==version()){persist();load();}if(!dialog.open)dialog.showModal();};
  $('next-usage-new').onclick=()=>{if(controller)return;try{localStorage.removeItem(key());}catch(_){}load();};
  $('next-usage-cancel').onclick=()=>controller?.abort();dialog.addEventListener('close',()=>{if(!dialog.open){controller?.abort();persist();}});
  document.addEventListener('survie:auth',()=>{if(report&&(owner!==S.user?.id||S.user?.role!=='admin')){epoch++;controller?.abort();persist();dialog.close();report=null;owner=null;controller=null;}});
  window.addEventListener('pagehide',()=>{controller?.abort();persist();});
  async function read(path,signal,staticPage=false){
    const request=new AbortController(),stop=()=>request.abort();let expired=false;signal.addEventListener('abort',stop,{once:true});if(signal.aborted)stop();
    const timer=setTimeout(()=>{expired=true;request.abort();},15000);
    try{
      if(!staticPage)return await api(path,undefined,{signal:request.signal,cache:'no-store'});
      const response=await fetch(path,{signal:request.signal,cache:'no-store',credentials:'same-origin'});if(!response.ok)throw Error('http');return await response.text();
    }catch(error){if(signal.aborted)throw new DOMException('Stopped','AbortError');throw Error(expired?'timeout':'unavailable');}
    finally{clearTimeout(timer);signal.removeEventListener('abort',stop);}
  }
  const engineState=value=>({control_available:value?.control_available===true,online:typeof value?.online==='boolean'?value.online:null,paused:value?.paused===true});
  const off=value=>value.control_available&&value.online===false;
  const finite=value=>Number.isFinite(value)?value:null;
  const text=(value,max=180)=>typeof value==='string'?value.slice(0,max):'';
  const sourceId=value=>typeof value==='string'&&value.length<=2000&&!!originalSourceURL(value);
  function render(row){const article=element('article',undefined,'usage-measure');article.dataset.usageMeasure=row.id;article.append(element('strong',labels[row.id]||row.id),element('p',row.message));if(row.source_id){const link=element('a','Ouvrir ce document ↗');link.href='/#/bibliotheque/recherche?'+new URLSearchParams({q:'faire du feu',domain:row.domain,source:row.source_id});link.target='_blank';link.rel='noopener';article.append(link);}results.append(article);}
  $('next-usage-run').onclick=async()=>{
    if(controller||!report||owner!==S.user?.id||S.user?.role!=='admin')return;
    const token=++epoch,active=report,runController=new AbortController();controller=runController;const signal=runController.signal;let deadline=false;
    const timer=setTimeout(()=>{deadline=true;runController.abort();},90000),candidates=[];
    active.status='running';active.measurements=[];active.started=new Date().toISOString();results.replaceChildren();controls();status.textContent='Contrôles locaux en cours…';
    async function measure(id,fn){
      if(signal.aborted)throw new DOMException('Stopped','AbortError');
      const started=performance.now();let row;
      try{row={id,...await fn()};}catch(error){if(signal.aborted)throw error;row={id,state:'failed',error:['timeout','format'].includes(error.message)?error.message:'unavailable',message:error.message==='timeout'?'Le contrôle a dépassé 15 secondes.':'Ce contrôle n’a pas abouti ; les autres résultats sont conservés.'};}
      if(signal.aborted||token!==epoch)throw new DOMException('Stopped','AbortError');row.elapsed_ms=Math.round(performance.now()-started);active.measurements.push(row);render(row);
      if(row.error==='version_changed')throw Error('version_changed');
    }
    async function health(){
      const value=await read('/health',signal);if(!value?.ok||typeof value.version!=='string'||!value.version||value.version.length>64)throw Error('format');
      if(active.version&&active.version!==value.version)return {state:'failed',error:'version_changed',observed_version:value.version,message:'La version du serveur a changé ; ces mesures ne constituent pas un essai de la même version.'};
      active.version=value.version;return {state:'passed',message:'Le portail local répond en version '+value.version+'.'};
    }
    try{
      await measure('health',health);
      await measure('engine_before',async()=>{const value=engineState(await read('/inference',signal));return {...value,state:off(value)?'passed':'unverified',message:off(value)?'L’arrêt du moteur est confirmé par le contrôleur.':'L’arrêt du moteur n’est pas confirmé ; cet essai ne prouve pas son fonctionnement IA arrêtée.'};});
      await measure('diagnostic',async()=>{const value=await read('/library/search-diagnostic',signal),data={kiwix_state:['reachable','unavailable'].includes(value.kiwix?.state)?value.kiwix.state:'unknown',catalog_state:text(value.catalog?.state,30),collections:finite(value.catalog?.collections),guides_indexed:finite(value.guides?.indexed),index_phase:text(value.archive_index?.phase,30)};return {...data,state:data.kiwix_state==='reachable'&&data.catalog_state==='live'?'passed':'unverified',message:data.kiwix_state==='reachable'?'Le serveur des collections répond ; état du catalogue : '+data.catalog_state+'.':'L’accès aux collections n’est pas confirmé. Une recherche partielle ne prouve pas l’absence du document.'};});
      for(const domain of ['all','resilience'])await measure(domain,async()=>{
        const value=await read('/search?'+new URLSearchParams({q:'faire du feu',domain,language:'',limit:'5'}),signal);if(!Array.isArray(value.results))throw Error('format');
        const rows=value.results.slice(0,5).filter(row=>sourceId(row.id)).map(row=>({id:row.id,title:text(row.title),language:text(row.language,12),kind:text(row.kind,20)}));
        for(const row of rows)if(candidates.length<2&&!candidates.some(item=>item.id===row.id))candidates.push({...row,domain});
        const coverage=['complete','partial','unavailable'].includes(value.coverage?.status)?value.coverage.status:'unknown';
        return {state:rows.length&&coverage==='complete'?'passed':'unverified',query:'faire du feu',domain,coverage,results:rows,message:rows.length+' résultat(s) à lire · couverture '+({complete:'complète annoncée',partial:'partielle',unavailable:'indisponible',unknown:'non précisée'}[coverage])+'. Leur pertinence reste à vérifier.'};
      });
      for(const candidate of candidates)await measure('source',async()=>{const value=await read('/source?'+new URLSearchParams({id:candidate.id}),signal);if(value?.id!==candidate.id||typeof value.text!=='string')throw Error('format');return {state:value.text.trim()?'passed':'unverified',source_id:candidate.id,domain:candidate.domain,title:candidate.title,characters:value.text.length,preview:value.preview===true,message:value.text.trim()?'Un aperçu textuel est lisible. Ouvrez l’original pour vérifier son utilité et ses illustrations.':'Aucun texte dans cet aperçu ; vérifiez l’original.'};});
      await measure('engine_after',async()=>{const value=engineState(await read('/inference',signal));return {...value,state:off(value)?'passed':'unverified',message:off(value)?'L’arrêt du moteur reste confirmé après les lectures.':'L’arrêt du moteur n’est pas confirmé à la fin de l’essai.'};});
      await measure('rescue',async()=>{const html=await read('/secours.html',signal,true);if(!/<html[\s>]/i.test(html))throw Error('format');return {state:'passed',message:'La page statique de secours répond. Son accès aux documents reste à vérifier en l’ouvrant.'};});
      await measure('health_after',health);
      if(token===epoch)active.status=deadline?'timed_out':signal.aborted?'cancelled':'measured';
    }catch(error){if(token===epoch)active.status=error.message==='version_changed'?'version_changed':deadline?'timed_out':signal.aborted?'cancelled':'error';}
    finally{
      clearTimeout(timer);if(token!==epoch)return;active.finished=new Date().toISOString();controller=null;
      conclusion();persist();controls();
    }
  };
  $('next-usage-export').onclick=()=>{
    if(!report||controller)return;
    const reviewed=report.manual.filter(row=>['passed','failed'].includes(row.state)).length;
    const data={...report,summary:{automatic_measured:report.measurements.length,automatic_failed:report.measurements.filter(row=>row.state==='failed').length,human_reviewed:reviewed,human_failed:report.manual.filter(row=>row.state==='failed').length,human_not_applicable:report.manual.filter(row=>row.state==='not_applicable').length,human_unperformed:report.manual.filter(row=>row.state==='unperformed').length,human_total:manual.length},notice:'Mesures techniques et observations humaines distinctes. Ni validation automatique du contenu ni preuve de coupure Internet. Les conversations et textes des documents sont exclus ; votre observation est incluse.'};
    downloadReport(data,'usage');
  };
})();
