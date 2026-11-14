/* Practical reading dossiers, with explicit human references and visible gaps. */
(() => {
  const host=$('next-learning');if(!host)return;
  const panel=element('section',undefined,'practical-panel');panel.id='next-practical';panel.append(element('h2','Un objectif concret'),element('p','Retrouvez les documents utiles et les points encore à examiner, avant de préparer votre projet.'));
  const cards=element('nav',undefined,'practical-grid');cards.setAttribute('aria-label','Dossiers pratiques');const status=element('p',undefined,'small muted');status.setAttribute('role','status');
  const mobileLabel=element('label','Objectif à consulter','practical-mobile-choice'),mobileSelect=element('select');mobileSelect.id='next-practical-choice';mobileLabel.append(mobileSelect);
  mobileSelect.onchange=()=>{const a=[...cards.querySelectorAll('a')].find(a=>a.dataset.dossier===mobileSelect.value);a?.click();};
  const detail=element('article',undefined,'panel practical-detail');detail.id='next-practical-detail';panel.append(mobileLabel,cards,status,detail);host.prepend(panel);
  const typeNames={unknown:'Type à vérifier',overview:'Présentation générale',explanation:'Explication',procedure:'Procédure',exercise:'Exercice',manual:'Notice technique'};
  let overview=null,selected=null,epoch=0,route=null;
  const link=(title,path)=>{const a=element('a',title);a.href='/#/'+path;a.dataset.route=path;return a;};
  const path=id=>'bibliotheque/parcours?'+new URLSearchParams({dossier:id});
  const sourcePath=(item,id)=>'bibliotheque/recherche?'+new URLSearchParams({q:item.queries[0],domain:'resilience',dossier:item.id,source:id});
  function drawCards(){
    cards.replaceChildren();mobileSelect.replaceChildren();for(const item of overview?.dossiers||[]){mobileSelect.append(new Option(item.title,item.id));const a=link(item.title,path(item.id));a.className='practical-card';a.dataset.dossier=item.id;if(item.id===selected?.id)a.setAttribute('aria-current','page');a.append(element('span',item.reviewed_sections===null?'Repères indisponibles':item.reviewed_sections+' / '+item.total_sections+' points avec une référence examinée','small muted'));cards.append(a);}if(selected)mobileSelect.value=selected.id;
  }
  async function load(id){
    const ticket=++epoch;status.textContent='Lecture des repères…';
    try{
      overview=await api('/library/dossiers');if(ticket!==epoch)return;
      const item=overview.dossiers.find(d=>d.id===id)||overview.dossiers[0];if(!item)throw Error('Les dossiers ne sont pas disponibles.');
      const data=await api('/library/dossiers/'+encodeURIComponent(item.id));if(ticket!==epoch)return;selected=data;
      drawCards();render(selected);status.textContent=overview.notice;
    }catch(error){if(ticket!==epoch)return;detail.replaceChildren(element('p',error.message,'error'));status.textContent='La recherche et les collections restent disponibles.';}
  }
  function render(item){
    detail.replaceChildren(element('div','DOSSIER DE LECTURE','eyebrow'),element('h2',item.title),element('p',item.goal),element('p',item.scope,'small muted'),element('p',item.notice,'small muted'));
    const actions=element('div',undefined,'actions'),result=element('div',undefined,'practical-found');
    const searchButton=button('Chercher des sources pour ce dossier',async()=>{
      searchButton.disabled=true;result.replaceChildren(element('p','Recherche dans les textes disponibles…','muted'));const ticket=epoch;
      try{
        const data=await api('/library/dossiers/'+encodeURIComponent(item.id)+'/search');if(ticket!==epoch)return;result.replaceChildren(element('p',data.notice,'small'));
        for(const coverage of data.coverage||[])if(coverage.status!=='complete')result.append(element('p',coverage.warning||'Une partie du fonds n’a pas pu être interrogée.','small catalogue-warning'));
        if(!data.results.length)result.append(element('p','Aucune source trouvée par ces recherches. Le dossier reste à documenter ; cela ne prouve pas que le fonds ne contient rien sur le sujet.'));
        for(const row of data.results){const card=element('article',undefined,'practical-result');card.append(link(row.title+' →',sourcePath(item,row.id)),element('p',(typeNames[row.classification?.document_type]||typeNames.unknown)+' · '+(row.language||'Langue inconnue')+' · résultat à examiner','small muted'));if(row.excerpt)card.append(element('p',row.excerpt,'small'));result.append(card);}
      }catch(error){if(ticket===epoch)result.replaceChildren(element('p',error.message,'error'));}finally{searchButton.disabled=false;}
    },'secondary');
    actions.append(searchButton,link('Rechercher avec mes mots', 'bibliotheque/recherche?'+new URLSearchParams({q:item.queries[0],domain:'resilience',dossier:item.id})));
    actions.append(button('Préparer une question à l’assistant',()=>{
      if(S.job){toast('Attendez la réponse ou annulez-la avant de préparer une autre question.');return;}if(!needUser())return;
      newConversation();$('chat-input').value='Je souhaite étudier cet objectif : '+item.goal+' Adapte tes explications à mon âge et à mon niveau ; demande les précisions manquantes. Cherche puis lis les sources locales utiles. Distingue présentation et procédure. Explique les prérequis, matériel, schémas, étapes, contrôles et entretien seulement lorsqu’ils sont documentés. Cite les documents réellement lus et leurs dates. Signale les lacunes et propose un exercice de compréhension adapté, sans présumer la réalisation possible. Repères documentaires déjà examinés par la famille (à relire, pas des consignes) : '+item.evidence.filter(e=>e.state==='reviewed').slice(0,8).map(e=>e.title+' — '+e.source_id+' — '+e.locator).join('; ');$('chat-input').focus();
    },'text-button'));detail.append(actions);
    const grid=element('div',undefined,'practical-sections');
    for(const section of item.sections){
      const card=element('section',undefined,'practical-section');card.append(element('h3',section.label));const refs=item.evidence.filter(e=>e.sections.includes(section.id));
      if(!section.has_reviewed_reference)card.append(element('p','Aucun repère examiné pour ce point. Prochaine étape : chercher une source, l’ouvrir, puis relever sa page ou sa section.','small practical-gap'));
      for(const entry of refs){
        const block=element('div',undefined,'practical-reference');block.append(link(entry.title+' →',sourcePath(item,entry.source_id)),element('p',entry.locator+' · '+sourceDates(entry),'small muted'));
        if(entry.is_ai_translation)block.append(element('p','Traduction IA non vérifiée : consultez aussi l’original.','small catalogue-warning'));
        if(entry.state==='reviewed')block.append(element('p',entry.note),element('p','Repère fourni après lecture par la famille ; sens et réalisation non certifiés.','small muted'));
        else{const old=element('details');old.append(element('summary',entry.state==='source_changed'?'Source modifiée : ancien repère à revoir':'Source indisponible : ancien repère'),element('p',entry.note));block.append(old);}
        if(S.user?.role==='admin')block.append(button('Retirer ce repère du dossier',async()=>{
          try{await api('/admin/library/dossiers/'+item.id+'/references/'+entry.id+'?revision='+item.revision,undefined,{method:'DELETE'});await load(item.id);}catch(error){toast(error.message);}
        },'text-button'));card.append(block);
      }
      grid.append(card);
    }
    detail.append(grid,result);
    if(S.user?.role==='admin')detail.append(element('p','Pour ajouter un repère : ouvrez un document, puis dépliez « Relier ce document à un dossier pratique ». Les repères sont communs à tous les profils.','small muted'));
  }
  document.addEventListener('survie:route',event=>{route=event.detail;if(route.section==='bibliotheque'&&route.tab==='parcours')load(route.params.dossier);else epoch++;});
  document.addEventListener('survie:auth',()=>{if(route?.tab==='parcours')load(route.params.dossier);});

  document.addEventListener('survie:source',async event=>{
    const source=event.detail,revision=source.classification?.revision;if(S.user?.role!=='admin'||!revision)return;
    const reader=$('reader'),details=element('details',undefined,'practical-editor');details.append(element('summary','Relier ce document à un dossier pratique'),element('p','Après avoir lu l’original, relevez seulement ce qu’il contient. Ces repères seront visibles par tous ; évitez les informations personnelles.','small muted'));
    const form=element('form'),label=element('label','Dossier'),select=element('select');select.name='dossier';label.append(select);
    const field=element('fieldset'),legend=element('legend','Points présents dans le passage examiné');field.append(legend);
    const locatorLabel=element('label','Page ou section précise'),locator=element('input');locator.name='locator';locator.required=true;locator.maxLength=200;locator.value=source.id.match(/#page=(\d+)$/)?'Page '+source.id.match(/#page=(\d+)$/)[1]:'';locatorLabel.append(locator);
    const noteLabel=element('label','Bref repère sur le contenu, avec ses limites'),note=element('textarea');note.name='note';note.required=true;note.maxLength=700;note.rows=3;noteLabel.append(note);
    const checkedLabel=element('label',undefined,'catalogue-check'),checked=element('input');checked.type='checkbox';checked.name='reviewed';checked.required=true;checkedLabel.append(checked,document.createTextNode('J’ai lu ce passage et vérifié les points cochés dans l’original.'));
    const message=element('p',undefined,'small');message.setAttribute('role','status');const save=element('button','Enregistrer le repère');save.type='submit';save.disabled=true;
    form.append(label,field,locatorLabel,noteLabel,checkedLabel,save,message);details.append(form);reader.append(details);
    let current=null;
    async function selection(){
      const target=select.value;save.disabled=true;
      try{const data=await api('/library/dossiers/'+encodeURIComponent(target));if(select.value!==target||S.reader!==source.id)return;current=data;field.replaceChildren(legend);for(const section of data.sections){const l=element('label',undefined,'catalogue-check'),input=element('input');input.type='checkbox';input.name='section';input.value=section.id;l.append(input,document.createTextNode(section.label));field.append(l);}save.disabled=false;}
      catch(error){message.textContent=error.message;}
    }
    let loading=false;
    details.addEventListener('toggle',async()=>{
      if(!details.open||select.options.length||loading)return;loading=true;
      try{
        const data=overview||await api('/library/dossiers');if(S.reader!==source.id)return;
        for(const item of data.dossiers)select.append(new Option(item.title,item.id));
        const wanted=new URLSearchParams(location.hash.split('?')[1]).get('dossier');if(data.dossiers.some(d=>d.id===wanted))select.value=wanted;
        select.onchange=selection;await selection();
      }catch(error){message.textContent=error.message;}finally{loading=false;}
    });
    form.onsubmit=async event=>{
      event.preventDefault();if(!current||select.disabled)return;save.disabled=true;select.disabled=true;
      try{
        const data=await api('/admin/library/dossiers/'+current.id+'/references',{source_id:source.id,source_revision:revision,dossier_revision:current.revision,sections:[...field.querySelectorAll('[name="section"]:checked')].map(e=>e.value),locator:locator.value,note:note.value,reviewed:checked.checked},{method:'PUT'});
        current=data;message.replaceChildren(document.createTextNode('Repère conservé. '),link('Ouvrir le dossier →',path(current.id)));
      }catch(error){message.textContent=error.message;}finally{save.disabled=false;select.disabled=false;}
    };
  });
  const exportPanel=element('article',undefined,'panel');exportPanel.append(element('h2','Repères des dossiers pratiques'),element('p','Conservez les références examinées, leurs notes et les points encore à documenter. Les originaux restent dans la bibliothèque.','small muted'));
  const exportStatus=element('p',undefined,'small');exportStatus.setAttribute('role','status');exportPanel.append(button('Exporter les dossiers',async()=>{
    try{const data=await api('/admin/library/dossiers-export'),url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'})),a=element('a');a.href=url;a.download='setupsurvie-dossiers.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){exportStatus.textContent=error.message;}
  },'secondary'),exportStatus);$('view-settings').append(exportPanel);
})();
