/* Translation belongs to the original reader. Jobs and publication use existing APIs. */
(() => {
  let destroy=null;
  const portal=typeof S!=='undefined',session=portal?S:{user:null,status:null};
  const get=id=>document.getElementById(id);
  const setText=(n,text)=>{if(n.textContent!==text)n.textContent=text;};
  const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  const action=(text,fn,cls='secondary')=>{const b=node('button',text,cls);b.type='button';b.addEventListener('click',fn);return b;};
  const request=portal?api:async(path,body,options={})=>{
    // Identity discovery must read the cookie's current profile, even when the
    // reader belongs to an older one. Data and commands keep the ownership guard.
    const headers=path==='/profiles/current'?{}:{'X-Survie-Profile':session.user?.id||''},config={credentials:'same-origin',...options,headers};
    if(body!==undefined){config.method=options.method||'POST';headers['Content-Type']='application/json';config.body=JSON.stringify(body);}
    const response=await fetch('/api'+path,config),data=await response.json();
    if(!response.ok){const error=Error(typeof data.detail==='string'?data.detail:'Le service est momentanément indisponible.');error.status=response.status;throw error;}return data;
  };
  const originalURL=portal?originalSourceURL:id=>'/pdf.html?'+new URLSearchParams({id,interface:'nouveau'});

  const canonical=id=>id.replace(/#page=\d+$/,'');
  async function mount(source,host,actions){
    destroy?.();
    if(source.is_ai_translation||source.language==='fr'||source.kind==='video'||!source.id?.match(/^(guide|zim):/))return;
    const owner=session.user?.id;if(!owner)return;
    const root=node('section',undefined,'reader-work');root.id='reader-work';root.hidden=true;
    root.setAttribute('aria-label','Traduction du document');
    const heading=node('h3','Traduire en français'),select=node('select');select.id='reader-work-choice';select.setAttribute('aria-label','Travail de traduction');
    const config=node('div',undefined,'reader-work-config');
    const first=node('input'),last=node('input');first.type=last.type='number';first.min=last.min='1';first.max=last.max='1200';first.value='1';last.placeholder='Jusqu’à la fin';
    const firstLabel=node('label','Première page du PDF'),lastLabel=node('label','Dernière page (facultatif)');firstLabel.append(first);lastLabel.append(last);
    const modes=node('select');modes.setAttribute('aria-label','Mode de traduction');
    for(const mode of session.status?.modes||[])modes.append(new Option(mode.name,mode.id));modes.value=get('chat-mode')?.value||'rapide';
    const modeLabel=node('label','Mode de traduction');modeLabel.append(modes);
    const advanced=node('details');advanced.append(node('summary','Options de traduction'),modeLabel);
    const glossary=node('details');glossary.append(node('summary','Mots à traduire de la même façon (facultatif)'));
    const termsRows=node('div'),termsStatus=node('p');termsStatus.setAttribute('role','status');
    let termsLoaded=false,termsDirty=false;
    const row=(source='',french='')=>{const line=node('div',undefined,'reader-work-term'),a=node('input'),b=node('input');a.value=source;b.value=french;a.maxLength=b.maxLength=120;a.setAttribute('aria-label','Terme original');b.setAttribute('aria-label','Forme française');
      for(const input of [a,b])input.oninput=()=>{termsDirty=true;};
      line.append(a,b,action('Retirer',()=>{line.remove();termsDirty=true;},'text-button'));termsRows.append(line);};
    const addTerm=action('Ajouter un mot',()=>{if(termsRows.children.length<40){row();termsDirty=true;}});
    const saveTerms=action('Enregistrer ces mots',async()=>{saveTerms.disabled=true;try{await request('/translation-terms',{terms:[...termsRows.children].map(n=>{const [a,b]=n.querySelectorAll('input');return {source:a.value.trim(),french:b.value.trim()};})},{method:'PUT'});termsDirty=false;termsStatus.textContent='Mots enregistrés pour les prochains travaux.';}catch(e){termsStatus.textContent=e.message;}finally{saveTerms.disabled=false;}});
    addTerm.disabled=saveTerms.disabled=true;
    glossary.append(node('p','Ces préférences seront copiées au lancement. Les modifier ensuite ne change pas un travail déjà commencé.','small muted'),termsRows,addTerm,saveTerms,termsStatus);advanced.append(glossary);
    glossary.addEventListener('toggle',async()=>{if(!glossary.open||termsLoaded)return;try{const data=await request('/translation-terms');if(!root.isConnected)return;termsRows.replaceChildren();for(const term of data.terms)row(term.source,term.french);termsLoaded=true;addTerm.disabled=saveTerms.disabled=false;}catch(e){termsStatus.textContent=e.message;}});
    config.append(firstLabel,lastLabel,advanced);const pdf=canonical(source.id).toLowerCase().endsWith('.pdf');firstLabel.hidden=lastLabel.hidden=!pdf;
    const notice=node('p','Une nouvelle traduction terminée sera partagée dans la bibliothèque locale. Les images restent dans l’original. Les contrôles automatiques ne valident pas le sens.','reader-work-notice small');
    const state=node('p');state.id='reader-work-status';state.setAttribute('role','status');state.setAttribute('aria-live','polite');
    const progress=node('progress');progress.hidden=true;progress.setAttribute('aria-label','Passages réellement traduits');
    const controls=node('div',undefined,'reader-work-actions');
    const parts=node('div');parts.id='reader-work-parts';
    const explanation=node('p','Vous pouvez quitter ce document et retrouver le travail ici. Après un arrêt du serveur, la reprise est volontaire.','small muted');
    const start=action('Démarrer la traduction',()=>command('start')),pause=action('Mettre en pause',()=>command('pause'),'secondary'),resume=action('Reprendre',()=>command('resume'),'secondary'),stop=action('Arrêter',()=>command('stop'),'secondary'),remove=action('Supprimer ce travail',()=>command('delete'),'text-button');
    const download=node('a','Télécharger le texte français');download.className='secondary-link';
    const conversation=node('a','Ouvrir la conversation associée'),shared=node('a','Lire le document partagé'),publicationNotice=node('p',undefined,'small muted');
    const publish=action('Réessayer l’ajout à la bibliothèque',()=>command('publish'),'secondary');
    controls.append(start,pause,resume,stop,download,publish,remove,conversation,shared);
    const navigation=node('div',undefined,'reader-work-actions');
    const previous=action('Passages précédents',()=>load(job,Math.max(0,offset-10)),'secondary'),next=action('Passages suivants',()=>load(job,offset+10),'secondary');
    const latest=action('Lire les derniers passages traduits',()=>{if(Number.isInteger(lastDone)){load(job,Math.floor(lastDone/10)*10);parts.scrollIntoView({block:'start'});}},'secondary');
    const reading=node('p',undefined,'small muted');
    navigation.append(previous,next,latest);
    root.append(heading,select,config,notice,state,progress,controls,explanation,reading,parts,navigation);host.querySelector('.reader-body').before(root);
    const trigger=actions.querySelector('[data-document-action=translate]')||action('Traduire en français',()=>{},'secondary');
    trigger.dataset.documentAction='translate';trigger.disabled=true;if(!trigger.isConnected)actions.append(trigger);
    let job=null,offset=0,timer=null,version=0,busy=false,items=[],disposed=false,modeForJob=null,renderedJob=null,lastDone=null;
    const valid=()=>!disposed&&root.isConnected&&session.user?.id===owner;
    const updateQueue=({detail})=>{
      const queue=window.WorkQueuePreview;
      queue?.translationLabels(queue.aiBusy(detail),start,resume,'Démarrer la traduction',resume.dataset.deferred==='true'?'Reprendre les passages à vérifier':'Reprendre');
    };
    const checkQueue=()=>{
      if(portal||document.hidden||root.hidden||!valid())return;
      request('/work-queue').then(detail=>{if(valid()&&window.WorkQueuePreview?.isSnapshot(detail))updateQueue({detail});}).catch(()=>{});
    };
    updateQueue({detail:window.WorkQueuePreview?.current?.()});
    document.addEventListener('survie:work-queue',updateQueue);
    controls.after(publicationNotice);
    const queueTimer=portal?null:setInterval(checkQueue,3500);
    const resumePolling=()=>{if(!document.hidden&&!root.hidden&&valid()&&job)load(job,offset);};
    document.addEventListener('visibilitychange',resumePolling);
    destroy=()=>{disposed=true;version++;clearTimeout(timer);clearInterval(queueTimer);document.removeEventListener('survie:work-queue',updateQueue);document.removeEventListener('visibilitychange',resumePolling);};
    const labels={queued:'En attente du moteur',running:'Traduction en cours',paused:'En pause',stopped:'Arrêtée',error:'Passage à reprendre',completed:'Traitement terminé'};
    function pending(){start.hidden=!!job;pause.hidden=resume.hidden=stop.hidden=remove.hidden=download.hidden=conversation.hidden=publish.hidden=shared.hidden=true;previous.hidden=next.hidden=latest.hidden=true;setText(publicationNotice,'');config.hidden=false;firstLabel.hidden=lastLabel.hidden=!!job||!pdf;}
    function choose(){select.replaceChildren(new Option('Nouvelle traduction',''));for(const item of items)select.append(new Option((labels[item.status]||item.status)+' · '+new Date(item.created*1000).toLocaleDateString('fr-FR'),item.id));select.value=job||'';}
    async function discover(){try{const data=await request('/document-work?'+new URLSearchParams({source_id:canonical(source.id)}));if(!valid())return;items=data.translations;choose();if(items.length){trigger.textContent='Traduction : ouvrir ou reprendre';}}catch(e){if(valid())state.textContent=e.message;}finally{if(valid())trigger.disabled=false;}}
    function newWork(){clearTimeout(timer);version++;job=null;renderedJob=null;lastDone=null;offset=0;parts.replaceChildren();setText(reading,'');state.textContent='Choisissez la plage puis démarrez volontairement la traduction.';progress.hidden=true;pending();select.value='';}
    trigger.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();root.hidden=!root.hidden;
      if(!root.hidden){checkQueue();if(!job&&items.length){job=items[0].id;select.value=job;}if(job)load(job,offset);root.scrollIntoView({block:'start'});}else{clearTimeout(timer);version++;}},true);
    select.onchange=()=>{if(select.value)load(select.value);else newWork();};
    function render(data){
      const keyed=new Map([...parts.children].map(n=>[n.dataset.position,n]));
      for(const part of data.parts){let row=keyed.get(String(part.position));const snapshot=JSON.stringify(part);if(row?.dataset.snapshot===snapshot){keyed.delete(String(part.position));continue;}
        const n=node('article',undefined,'translation-part');n.dataset.position=part.position;n.dataset.snapshot=snapshot;n.append(node('h4','Page/section '+part.page+' · passage '+(part.position+1)));
        if(part.status==='done'){const text=node('div',undefined,'translation-text');if(window.SurvieTranslationText)window.SurvieTranslationText.render(text,part.translated);else text.textContent=part.translated||'';n.append(text);}
        else n.append(node('p',part.status==='unreadable'?'Page sans texte extractible. Consultez les illustrations originales.':'Passage encore à traduire.'));
        if(part.model)n.append(node('p',part.model,'small muted'));
        n.append(node('p',({checked:'Contrôles limités : le sens reste à vérifier.',warning:'À relire : anomalie possible.',unchecked:'Aucun contrôle enregistré.'}[part.quality?.status]||''),'small muted'));
        for(const issue of part.quality?.issues||[])n.append(node('p',issue.message,'reader-work-notice'));
        if(part.quality?.status==='blocked')n.append(node('p','Proposition refusée : elle ne compte pas comme traduction et n’est pas publiée.','reader-work-notice'));
        if(part.source_text){const compare=node('details');compare.append(node('summary','Comparer avec le texte original'),node('pre',part.source_text));n.append(compare);}
        if(part.candidate){const candidate=node('details');candidate.append(node('summary','Proposition refusée · ne pas utiliser'),node('p',part.candidate));n.append(candidate);}
        const original=node('a','Consulter la page originale');original.href=originalURL(canonical(data.source_id)+(pdf?'#page='+part.page:''));original.target='_blank';original.rel='noopener';n.append(original);
        if(row){const opened=[...row.querySelectorAll('details')].map(d=>d.open);n.querySelectorAll('details').forEach((d,i)=>d.open=opened[i]);row.replaceWith(n);keyed.delete(String(part.position));}else parts.append(n);
      }
      for(const n of keyed.values())n.remove();
    }
    async function load(id,position=0){clearTimeout(timer);job=id;offset=position;const own=++version;if(renderedJob!==id)pending();
      try{const data=await request('/translations/'+encodeURIComponent(id)+'?offset='+position);if(!valid()||own!==version)return;
        if(position>=data.total&&position)return load(id,Math.max(0,Math.floor((data.total-1)/10)*10));
        if(modeForJob!==id){modeForJob=id;if([...modes.options].some(o=>o.value===data.mode))modes.value=data.mode;}
        renderedJob=id;select.value=id;const option=[...select.options].find(o=>o.value===id);if(option)setText(option,(window.WorkQueuePreview?.workLabel(data,labels[data.status])||labels[data.status]||'État inconnu')+' · '+new Date(data.created*1000).toLocaleDateString('fr-FR'));const active=['queued','running'].includes(data.status);
        setText(state,(data.status==='completed'&&data.done<data.total?'Traduction incomplète':window.WorkQueuePreview?.workLabel(data,labels[data.status])||labels[data.status]||'État inconnu')+' · '+(data.deferred?data.deferred+' passage(s) à reprendre. L’original reste consultable. ':'')+data.done+'/'+data.total+' passages traduits. '+(Number.isInteger(data.pages_done)?data.pages_done+'/'+data.pages+' pages ou sections entièrement traduites. ':'')+(data.error||data.notice||''));
        const end=Math.min(position+data.parts.length,data.total);setText(reading,(Number.isInteger(data.current_page)?'Page/section en cours : '+data.current_page+'. ':'')+(data.total?'Passages affichés : '+(position+1)+' à '+end+' sur '+data.total+'.':'Aucun passage à afficher.'));
        lastDone=data.last_done_position;latest.hidden=!Number.isInteger(lastDone)||Math.floor(lastDone/10)*10===position;
        progress.hidden=false;progress.max=Math.max(1,data.total);progress.value=data.done;
        pause.hidden=!active;resume.hidden=active||(data.status==='completed'&&!data.deferred);resume.dataset.deferred=String(data.status==='completed'&&!!data.deferred);resume.textContent=resume.dataset.deferred==='true'?'Reprendre les passages à vérifier':'Reprendre';stop.hidden=data.status==='completed'||data.status==='stopped';remove.hidden=false;download.hidden=false;conversation.hidden=false;
        download.href='/api/translations/'+encodeURIComponent(id)+'/export';conversation.href=(portal?'':'/nouveau/')+'#/assistant?conversation='+encodeURIComponent(data.conversation_id);conversation.dataset.route='assistant?conversation='+encodeURIComponent(data.conversation_id);
        const publication=data.publication||{};
        const publishing=data.status==='completed'&&data.done>0&&publication.pending&&!publication.error;
        publish.hidden=data.status!=='completed'||!data.done||publishing||!!(publication.source_id&&!publication.error);
        shared.hidden=!publication.url;
        if(!shared.hidden){
          shared.textContent=publication.partial?'Lire la traduction partielle partagée':'Lire le document partagé';
          shared.href=publication.url;
        }
        setText(publicationNotice,publication.error||(publishing?'Actualisation des documents locaux en cours…':data.status==='completed'&&!data.done?'Aucun passage français à partager.':''));
        previous.hidden=position===0;next.hidden=position+data.parts.length>=data.total;
        render(data);if((active||publishing)&&!document.hidden&&!root.hidden)timer=setTimeout(()=>load(id,position),2000);
      }catch(e){if(valid()&&own===version){state.textContent=e.message;if(e.status!==404)timer=setTimeout(()=>load(id,position),5000);}}
    }
    async function command(action){if(!valid()||busy)return;
      if(action==='delete'&&!confirm('Supprimer les passages privés et le suivi de ce travail ? Le document original, la conversation et toute traduction déjà partagée sont conservés.'))return;
      busy=true;for(const b of controls.querySelectorAll('button'))b.disabled=true;
      try{let data;
        if(action==='start'){
          if(termsDirty)throw Error('Enregistrez les mots choisis avant de lancer la traduction.');
          const a=pdf?Number(first.value):1,b=pdf&&last.value?Number(last.value):null;
          if(!Number.isInteger(a)||a<1||a>1200||b!==null&&(!Number.isInteger(b)||b<a||b>1200))throw Error('Vérifiez les pages à traduire.');
          data=await request('/translations',{source_id:canonical(source.id),conversation_id:null,mode:modes.value||'rapide',first_page:a,last_page:b});
        }else if(action==='delete'){await request('/translations/'+encodeURIComponent(job),undefined,{method:'DELETE'});newWork();await discover();return;}
        else data=await request('/translations/'+encodeURIComponent(job)+'/'+action,action==='resume'?{mode:modes.value||'rapide'}:{});
        if(!valid())return;
        if(['start','resume','pause','stop'].includes(action)){
          if(portal)document.dispatchEvent(new CustomEvent('survie:translation-command',{detail:{action,id:data.id}}));
          else checkQueue();
        }
        job=data.id||job;await discover();await load(job,action==='start'?0:offset);
      }catch(e){if(valid())state.textContent=e.message;}finally{busy=false;if(valid())for(const b of controls.querySelectorAll('button'))b.disabled=false;}
    }
    pending();await discover();
  }
  if(!portal){
    const id=new URLSearchParams(location.search).get('id')||'',nav=document.querySelector('header nav');
    if(/^guide:.+\.pdf(?:#page=\d+)?$/i.test(id)&&nav){
      const open=action('Traduire ce PDF',()=>{},'secondary');open.disabled=true;nav.append(open);
      const dialog=node('dialog');dialog.id='pdf-translation-work';dialog.setAttribute('aria-label','Traduction du PDF');
      const close=action('Revenir au PDF',()=>dialog.close());const placeholder=node('div',undefined,'reader-body');dialog.append(close,placeholder);document.body.append(dialog);
      open.onclick=()=>dialog.showModal();
      const ready=Promise.all([request('/profiles/current'),request('/status')]).then(async([profile,status])=>{
        session.user=profile;session.status=status;
        const source=await request('/source?id='+encodeURIComponent(canonical(id)));
        if(source.language==='fr'||source.is_ai_translation){open.hidden=true;return;}
        await mount(source,dialog,nav);
        const trigger=nav.querySelector('[data-document-action=translate]');
        if(trigger){trigger.hidden=true;open.disabled=false;open.onclick=()=>{dialog.showModal();const panel=get('reader-work');if(panel.hidden)trigger.click();};}
      }).catch(()=>{open.disabled=true;open.textContent='Traduction indisponible';});
      window.addEventListener('focus',async()=>{try{
        // An initial focus is not a profile change. Compare only once the
        // reference profile and controls are initialized, including slow loads.
        await ready;if(!session.user)return;
        const current=await request('/profiles/current');if(current.id!==session.user.id){destroy?.();dialog.close();open.disabled=true;open.textContent='Profil modifié : rechargez le lecteur';}
      }catch(_){}});
    }
    return;
  }
  document.addEventListener('survie:source',event=>{const host=get('reader');mount(event.detail,host,host.querySelector('.reader-actions'));});
  document.addEventListener('survie:auth',()=>destroy?.());
  document.addEventListener('survie:route',event=>{if(event.detail.section!=='bibliotheque'||!event.detail.params.source){destroy?.();get('reader').hidden=true;}});
})();
