/* Voluntary long translation; reading this panel never runs inference. */
(() => {
  const panel=element('article',undefined,'panel');panel.id='next-translation-benchmark';panel.innerHTML='<h2>Traduire un document de 40 pages pour mesurer le PC</h2><p>Un PDF fictif d’environ 9 600 mots est préparé sur le serveur, puis traduit par le moteur habituel. Il ne rejoint pas votre bibliothèque.</p><p class="small muted">Prévoyez un moment disponible : la durée dépend du modèle. Le suivi continue sans cet onglet. Une pause conserve les passages terminés ; une nouvelle question ou le mode jeu prend la priorité.</p><label>Modèle à mesurer<select id="next-translation-benchmark-mode"></select></label><div class="actions"><button id="next-translation-benchmark-start">Lancer le test de 40 pages</button><button id="next-translation-benchmark-pause" class="secondary" hidden>Mettre en pause</button><button id="next-translation-benchmark-resume" hidden>Reprendre le test</button><button id="next-translation-benchmark-export" class="secondary" disabled>Télécharger le rapport</button></div><p id="next-translation-benchmark-status" role="status"></p><div id="next-translation-benchmark-result"></div><p class="small muted">Le rapport mesure les durées et ressources. Il ne certifie pas la fidélité de la traduction. Aucun texte de vos documents ni conversation n’est utilisé.</p>';
  $('view-settings').append(panel);
  let report=null,busy=false,loading=false,owner=null;
  function modes(){const select=$('next-translation-benchmark-mode');if(!select.options.length)for(const mode of S.status?.modes||[])select.append(new Option(mode.name,mode.id));}
  function render(value){
    report=value;const active=value.status==='running',resume=['paused','failed'].includes(value.status);
    $('next-translation-benchmark-start').disabled=active||busy||!$('next-translation-benchmark-mode').options.length;
    $('next-translation-benchmark-mode').disabled=active;$('next-translation-benchmark-pause').hidden=!active;$('next-translation-benchmark-resume').hidden=!resume;
    $('next-translation-benchmark-export').disabled=value.status==='not_started';
    $('next-translation-benchmark-status').textContent=value.message||'Aucun test lancé.';
    const target=$('next-translation-benchmark-result');target.replaceChildren();if(value.status==='not_started')return;
    target.append(element('p',(value.pages_done||0)+' / 40 pages terminées · '+(value.parts_done||0)+' passage(s) traduit(s).'));
    if(value.current_page)target.append(element('p','Page en cours : '+value.current_page,'small'));
    if(value.fixture)target.append(element('p',value.fixture.source_words.toLocaleString('fr-FR')+' mots source · '+value.fixture.parts+' passages · PDF préparé et texte extrait.','small muted'));
    if(Number.isFinite(value.active_elapsed_ms))target.append(element('p','Temps de travail cumulé : '+(value.active_elapsed_ms/60000).toLocaleString('fr-FR',{maximumFractionDigits:1})+' min. Les pauses sont exclues.','small'));
    if(value.source_words_per_minute)target.append(element('p',value.source_words_per_minute.toLocaleString('fr-FR',{maximumFractionDigits:1})+' mots source traduits par minute de travail.','small'));
    if(value.sample_count&&!value.host_sample_count)target.append(element('p','Mesures matérielles indisponibles ; les durées et tokens restent dans le rapport.','small catalogue-warning'));
    if(resume)target.append(element('p','Reprendre conserve les passages terminés. Lancer un nouveau test crée une autre mesure.','small'));
  }
  async function refresh(){
    modes();if(S.user?.role!=='admin'||$('view-settings').hidden||document.hidden||loading||busy)return;
    if(owner!==S.user.id){owner=S.user.id;render({status:'not_started'});}
    loading=true;const id=S.user.id;
    try{const value=await api('/admin/translation-benchmark');if(S.user?.id===id)render(value);}
    catch(error){$('next-translation-benchmark-status').textContent=error.message;}finally{loading=false;}
  }
  async function action(name){
    if(busy)return;busy=true;const id=S.user?.id;if(report)render(report);
    try{const value=await api('/admin/translation-benchmark/'+name,name==='pause'?{}:{mode:$('next-translation-benchmark-mode').value||'rapide'});if(S.user?.id===id)render(value);}
    catch(error){$('next-translation-benchmark-status').textContent=error.message;}finally{busy=false;if(report){const message=$('next-translation-benchmark-status').textContent;render(report);$('next-translation-benchmark-status').textContent=message;}}
  }
  for(const name of ['start','pause','resume'])$('next-translation-benchmark-'+name).onclick=()=>action(name);
  $('next-translation-benchmark-export').onclick=async()=>{
    try{const id=S.user?.id,value=await api('/admin/translation-benchmark/report');if(S.user?.id!==id)return;
      const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'})),link=element('a');link.href=url;link.download='setupsurvie-traduction-40-pages-'+value.id+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    }catch(error){$('next-translation-benchmark-status').textContent=error.message;}
  };
  setInterval(refresh,2000);document.addEventListener('survie:auth',refresh);document.addEventListener('survie:route',refresh);new MutationObserver(refresh).observe($('view-settings'),{attributes:true,attributeFilter:['hidden']});
})();
