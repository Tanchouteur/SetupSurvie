/* Shared interface primitives. No inference, job creation or data migration. */
(() => {
  function help(label, text) {
    const root=document.createElement('span');root.className='ux-help';
    const trigger=document.createElement('button');trigger.type='button';trigger.className='ux-help-trigger';
    trigger.textContent='i';trigger.setAttribute('aria-label',label);trigger.setAttribute('aria-expanded','false');
    const content=document.createElement('span');content.className='ux-help-content';content.hidden=true;
    content.id='ux-help-'+(++help.count);content.textContent=text;trigger.setAttribute('aria-controls',content.id);
    trigger.setAttribute('aria-describedby',content.id);
    let dismissed=false,pinned=false;
    const show=()=>{if(dismissed)return;content.hidden=false;trigger.setAttribute('aria-expanded','true');};
    const hide=()=>{content.hidden=true;trigger.setAttribute('aria-expanded','false');};
    trigger.addEventListener('click',()=>{dismissed=false;pinned=!pinned;if(pinned)show();else hide();});
    root.addEventListener('pointerenter',event=>{if(event.pointerType==='mouse'){dismissed=false;show();}});
    root.addEventListener('pointerleave',()=>{if(!pinned&&!root.contains(document.activeElement))hide();dismissed=false;});
    trigger.addEventListener('focus',show);
    root.addEventListener('focusout',event=>{if(!root.contains(event.relatedTarget)){pinned=false;hide();}});
    document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!content.hidden){pinned=false;hide();dismissed=true;}});
    document.addEventListener('pointerdown',event=>{if(!root.contains(event.target)){pinned=false;hide();}});
    root.append(trigger,content);return root;
  }
  help.count=0;
  window.SurvieUI=Object.freeze({help});
  document.addEventListener('DOMContentLoaded',()=>{
    const title=document.querySelector('#view-library h1');if(title)title.textContent='Bibliothèque';
    const welcome=document.querySelector('#view-home h1');if(welcome)welcome.textContent='Que souhaitez-vous faire ?';
    const mode=document.querySelector('label[for="chat-mode"]');
    if(mode){mode.textContent='Mode de réponse';mode.append(help('Comprendre les modes de réponse','Rapide, moyenne et approfondie règlent le travail de l’assistant. Le délai dépend aussi du document et du PC. Les modèles de comparaison servent aux essais.'));}
    const domain=document.querySelector('#next-domain-controls');
    if(domain){domain.append(help('Comprendre les espaces documentaires','Les espaces orientent la recherche. Choisissez Toute la bibliothèque pour inclure aussi les documents non classés.'));}
    const label=document.querySelector('label[for="collection-filter"]');
    if(label){label.textContent='Filtrer les collections';label.append(help('Comprendre le filtre des collections','Ce champ cherche dans les titres et descriptions. Pour chercher un sujet dans les articles et les livres, utilisez Rechercher.'));}
  });
  // Opened content takes priority over the search form, especially on phones.
  document.addEventListener('survie:source',()=>{
    const reader=document.getElementById('reader'),heading=reader?.querySelector('h2');
    if(!heading)return;heading.tabIndex=-1;
    requestAnimationFrame(()=>{heading.focus({preventScroll:true});reader.scrollIntoView({block:'start',behavior:'instant'});});
  });
})();
