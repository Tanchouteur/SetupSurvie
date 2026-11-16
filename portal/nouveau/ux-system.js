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
  const resumeBox=element('section',undefined,'ux-resume');resumeBox.setAttribute('aria-label','Reprendre une activité');
  const home=document.getElementById('view-home');home.querySelector('.welcome').after(resumeBox);
  function recentReading(){if(!S.user)return null;try{const saved=JSON.parse(localStorage.getItem('survie-next-v1:'+S.user.id+':last-document'));return saved&&Date.now()-saved.at<7*86400000?saved:null;}catch(_){return null;}}
  function drawResume(){resumeBox.replaceChildren();if(!S.user)return;const document=recentReading(),conversation=readingState().selected;
    if(document)resumeBox.append(button('Reprendre la lecture : '+document.title,()=>readSource(document.id),'secondary'));
    if(conversation)resumeBox.append(button('Reprendre la discussion',()=>openConversation(conversation),'secondary'));
    resumeBox.hidden=!resumeBox.children.length;
  }
  document.addEventListener('survie:source',event=>{if(S.user)try{localStorage.setItem('survie-next-v1:'+S.user.id+':last-document',JSON.stringify({id:event.detail.id,title:event.detail.title,at:Date.now()}));}catch(_){}drawResume();});
  document.addEventListener('survie:conversation',drawResume);document.addEventListener('survie:auth',drawResume);
  const work=element('section',undefined,'ux-personal-work');work.setAttribute('aria-label','Vos travaux de lecture');
  const workTitle=element('h2','Vos traductions et synthèses'),workList=element('div'),workRefresh=button('Actualiser vos travaux',refreshWork,'secondary');const observed=element('p','','small muted');work.append(workTitle,workRefresh,observed,workList);document.getElementById('view-activity').append(work);
  let workVersion=0;
  async function refreshWork(){const owner=S.user?.id,own=++workVersion;if(!owner)return;try{const data=await api('/my-work');if(owner!==S.user?.id||own!==workVersion)return;workList.replaceChildren();observed.textContent='Actualisé à '+new Intl.DateTimeFormat('fr-FR',{hour:'2-digit',minute:'2-digit'}).format(new Date());
    for(const [kind,items] of [['translation',data.translations],['summary',data.summaries]])for(const item of items){
      const row=element('article',undefined,'ux-work-row'),states={running:'En cours',queued:'En attente',preparing:'Préparation',paused:'En pause',error:'À reprendre',stopped:'Arrêté',completed:'Terminé',incomplete:'Incomplet'};
      const link=element('a',item.title);link.href='#/assistant?conversation='+encodeURIComponent(item.conversation_id);link.dataset.route='assistant?conversation='+encodeURIComponent(item.conversation_id);
      row.append(link,element('p',(kind==='translation'?'Traduction':'Synthèse')+' · '+(states[item.status]||item.status),'small muted'));workList.append(row);
    }
    if(!workList.children.length)workList.append(element('p','Aucun travail de lecture enregistré pour ce profil.','small muted'));
  }catch(e){if(own===workVersion)workList.textContent=e.message;}}
  document.addEventListener('survie:route',event=>{if(event.detail.section==='appareil'&&event.detail.tab==='activite')refreshWork();if(event.detail.section==='accueil')drawResume();});
  document.addEventListener('survie:auth',()=>{workVersion++;workList.replaceChildren();});
  // Opened content takes priority over the search form, especially on phones.
  document.addEventListener('survie:source',()=>{
    const reader=document.getElementById('reader'),heading=reader?.querySelector('h2');
    if(!heading)return;heading.tabIndex=-1;
    requestAnimationFrame(()=>{heading.focus({preventScroll:true});reader.scrollIntoView({block:'start',behavior:'instant'});});
  });
})();
