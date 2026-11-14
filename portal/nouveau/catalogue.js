/* Human metadata lives on the local server. No edits to books or archive paths. */
(() => {
  const types={unknown:'Type à vérifier',overview:'Présentation générale',explanation:'Explication',procedure:'Procédure',exercise:'Exercice',manual:'Notice technique'};
  const domains={resilience:'Autonomie et résilience',culture:'Savoirs et culture'};
  function description(info){
    if(!info)return 'Type à vérifier';
    const type=types[info.document_type]||types.unknown;
    return type+(info.method==='human'?' · '+(info.status==='reviewed'?'classement examiné':'classement corrigé'):info.document_type!=='unknown'?' · à vérifier':'');
  }
  document.addEventListener('survie:results',event=>{
    for(const result of event.detail){
      const card=[...$('search-results').querySelectorAll('.result')].find(node=>node.dataset.source===result.id);
      if(card&&result.classification){const label=element('p',description(result.classification),'small muted catalogue-type');card.querySelector('h3').after(label);}
    }
  });

  document.addEventListener('survie:source',event=>{
    const source=event.detail,info=source.classification;if(!info)return;
    const reader=$('reader'),summary=element('p',description(info),'small muted');
    reader.querySelector('h2').after(summary);
    if(info.status==='source_changed')reader.append(element('p','La source a changé depuis sa correction. Le classement automatique est utilisé jusqu’à une nouvelle vérification.','catalogue-warning small'));
    if(S.user?.role!=='admin')return;
    const details=element('details',undefined,'catalogue-editor'),heading=element('summary','Corriger le classement');details.append(heading);
    details.append(element('p','Ce classement aide à retrouver le document. Il ne certifie ni son exactitude ni la sécurité d’une procédure.','small muted'));
    const form=element('form'),field=element('fieldset'),legend=element('legend','Où retrouver ce document ?');field.append(legend);
    for(const [key,label] of Object.entries(domains)){const row=element('label'),input=element('input');input.type='checkbox';input.name='domain';input.value=key;input.checked=info.domains.includes(key);row.append(input,document.createTextNode(' '+label));field.append(row);}
    field.append(element('p','Sans espace choisi, le document reste dans Toute la bibliothèque.','small muted'));
    const label=element('label','Ce document contient surtout…'),select=element('select');select.name='document_type';for(const [key,text] of Object.entries(types))select.append(new Option(text,key));select.value=info.document_type;label.append(select);
    const reviewedLabel=element('label'),reviewed=element('input');reviewed.type='checkbox';reviewed.checked=info.status==='reviewed';reviewedLabel.append(reviewed,document.createTextNode(' J’ai examiné le contenu pour ce classement.'));
    const status=element('p',undefined,'small');status.setAttribute('role','status');
    const save=element('button','Enregistrer le classement');save.type='submit';save.disabled=!info.revision;
    const actions=element('div',undefined,'actions');actions.append(save);
    if(info.has_correction)actions.append(button('Revenir au classement automatique',async()=>{
      try{await api('/admin/library/metadata?'+new URLSearchParams({source_id:source.id}),undefined,{method:'DELETE'});if(S.reader===source.id)await readSource(source.id);}catch(error){status.textContent=error.message;}
    },'secondary'));
    form.append(field,label,reviewedLabel,actions,status);details.append(form);reader.append(details);
    form.onsubmit=async event=>{
      event.preventDefault();save.disabled=true;
      try{
        await api('/admin/library/classification',{source_id:source.id,revision:info.revision,domains:[...form.querySelectorAll('[name="domain"]:checked')].map(input=>input.value),document_type:select.value,reviewed:reviewed.checked},{method:'PUT'});
        if(S.reader===source.id)await readSource(source.id);
        toast('Classement conservé. Il sera utilisé lors de la prochaine recherche.');
      }catch(error){status.textContent=error.message;}finally{save.disabled=!info.revision;}
    };
  });

  function editCollection(item){
    const old=document.getElementById('catalogue-collection-dialog');old?.remove();
    const dialog=element('dialog',undefined,'catalogue-dialog');dialog.id='catalogue-collection-dialog';dialog.setAttribute('aria-labelledby','catalogue-collection-title');
    const title=element('h2','Nommer cette collection');title.id='catalogue-collection-title';
    dialog.append(title,element('p','Les fichiers et leurs liens restent les mêmes. Donnez le même nom de groupe aux collections que vous souhaitez réunir.','small muted'));
    const form=element('form'),familyLabel=element('label','Groupe ou source'),family=element('input');family.name='family';family.maxLength=80;family.required=true;family.value=item.family;familyLabel.append(family);
    const variantLabel=element('label','Sujet ou titre de cette collection'),variant=element('input');variant.name='variant';variant.maxLength=120;variant.required=true;variant.value=item.variant;variantLabel.append(variant);
    const reference=element('details'),referenceTitle=element('summary','Référence d’origine');reference.append(referenceTitle,element('p',item.archive_name,'small'),element('p',item.title,'small'));
    const status=element('p',undefined,'small');status.setAttribute('role','status');
    const save=element('button','Enregistrer les noms');save.type='submit';
    const close=button('Fermer',()=>dialog.close(),'secondary'),actions=element('div',undefined,'actions');actions.append(save,close);
    if(item.labels_corrected)actions.append(button('Revenir aux noms automatiques',async()=>{
      try{await api('/admin/library/metadata?'+new URLSearchParams({source_id:'collection:'+item.id}),undefined,{method:'DELETE'});dialog.close();await loadData();}catch(error){status.textContent=error.message;}
    },'secondary'));
    if(item.labels_status==='source_changed')form.append(element('p','Le fichier a changé ; les anciens noms corrigés doivent être revus.','small catalogue-warning'));
    form.append(familyLabel,variantLabel,reference,actions,status);dialog.append(form);document.body.append(dialog);
    form.onsubmit=async event=>{
      event.preventDefault();save.disabled=true;
      try{await api('/admin/library/collection-labels',{collection_id:item.id,revision:item.labels_revision,family:family.value,variant:variant.value},{method:'PUT'});dialog.close();await loadData();toast('Noms conservés sur cet appareil.');}
      catch(error){status.textContent=error.message;}finally{save.disabled=false;}
    };
    dialog.addEventListener('close',()=>dialog.remove(),{once:true});dialog.showModal();
  }

  let lastInventory=null;
  function decorateInventory(data){
    document.querySelectorAll('#data-books .catalogue-label-control').forEach(node=>node.remove());
    if(S.user?.role!=='admin')return;
    const cards=[...$('data-books').querySelectorAll('.data-card')];
    for(const [index,item] of (data.books||[]).entries()){
      const card=cards.find(node=>node.dataset.collectionId===item.id)||cards[index];
      if(card&&item.labels_revision){card.append(button('Modifier les noms',()=>editCollection(item),'text-button catalogue-label-control'));if(item.labels_status==='source_changed')card.append(element('p','Noms corrigés à revoir : fichier modifié.','small catalogue-warning catalogue-label-control'));}
    }
  }
  document.addEventListener('survie:inventory',event=>{lastInventory=event.detail;decorateInventory(lastInventory);});
  document.addEventListener('survie:auth',()=>{if(lastInventory)decorateInventory(lastInventory);});

  const settings=$('view-settings'),panel=element('article',undefined,'panel');panel.append(element('h2','Classements et noms corrigés'),element('p','Conservez les corrections apportées aux documents et collections. Cet export contient leurs références et classements, sans leur texte ni les conversations.','small muted'));
  const status=element('p',undefined,'small');status.setAttribute('role','status');
  panel.append(button('Exporter les métadonnées',async()=>{
    try{const report=await api('/admin/library/metadata-export'),url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})),link=element('a');link.href=url;link.download='setupsurvie-classements.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status.textContent='Métadonnées exportées.';}
    catch(error){status.textContent=error.message;}
  },'secondary'),status);settings.append(panel);
})();
