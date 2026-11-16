/* Read existing published French text locally; never start an inference. */
(()=>{
  'use strict';
  const node=(tag,text,cls)=>{const value=document.createElement(tag);if(text!==undefined)value.textContent=text;if(cls)value.className=cls;return value;};
  const button=(text,action)=>{const value=node('button',text);value.type='button';value.onclick=action;return value;};
  const requests=new Set();let departing=false;
  window.addEventListener('beforeunload',()=>{for(const controller of requests)controller.abort();});
  window.addEventListener('pagehide',()=>{departing=true;for(const controller of requests)controller.abort();});
  window.addEventListener('pageshow',event=>{if(event.persisted)departing=false;});
  async function get(path){
    if(departing)throw new DOMException('Page quittée','AbortError');
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),15000);requests.add(controller);
    try{const response=await fetch('/api/library/'+path,{signal:controller.signal,cache:'no-store'});if(!response.ok)throw Error('La version française ne peut pas être ouverte pour le moment.');return await response.json();}
    finally{clearTimeout(timer);requests.delete(controller);}
  }
  function mount(original,host,trigger,modeChanged,pdf=false,synchronize=false){
    const panel=node('section',undefined,'french-reading');panel.hidden=true;panel.setAttribute('aria-label','Lecture en français');host.append(panel);
    const actions=node('div',undefined,'french-reading-actions'),back=button(synchronize?'Voir le PDF original':'Voir l’original',()=>showOriginal());actions.append(back);
    const versions=node('select');versions.setAttribute('aria-label','Version française à lire');const versionLabel=node('label','Version française ');versionLabel.append(versions);actions.append(versionLabel);
    const pageControls=node('div',undefined,'french-reading-pages'),previous=button('←',()=>adjacent(-1)),next=button('→',()=>adjacent(1)),pageInput=node('input');
    pageInput.type='number';pageInput.min='1';pageInput.max='1200';pageInput.value=String(Number(original.split('#page=')[1])||1);const pageLabel=node('label','Page originale ');pageLabel.append(pageInput);
    previous.setAttribute('aria-label','Page traduite précédente');next.setAttribute('aria-label','Page traduite suivante');pageControls.append(previous,pageLabel,next);pageControls.hidden=!pdf;
    const notice=node('p','Traduction IA non vérifiée. Les illustrations restent dans l’original.','french-reading-notice'),status=node('p',undefined,'french-reading-status');status.setAttribute('role','status');
    const body=node('div',undefined,'french-reading-text');panel.append(actions,pageControls,notice,status,body);
    const base=original.replace(/#page=\d+$/,''),key='survie-french-reading:'+((typeof S!=='undefined'&&S.user?.id)||'reader')+':'+base;
    let choices=[],active=null,reading=false,confirmed=null,requestNumber=0,lastRequest=null;
    function remember(mode){try{localStorage.setItem(key,JSON.stringify({mode,translation:active?.id}));}catch(_){}}
    function showOriginal(){reading=false;requestNumber++;lastRequest=null;panel.hidden=true;modeChanged(false,Number(pageInput.value));trigger.setAttribute('aria-pressed','false');remember('original');}
    function adjacent(direction){const page=Number(pageInput.value),pages=active?.pages||[],target=direction<0?[...pages].reverse().find(value=>value<page):pages.find(value=>value>page);if(target)go(target);}
    function go(page){if(!Number.isInteger(page)||page<1||page>1200)return;pageInput.value=String(page);if(synchronize){document.documentElement.dataset.frenchReaderPage=String(page);window.dispatchEvent(new CustomEvent('survie:pdf-go',{detail:{page}}));}if(reading)load();}
    pageInput.onchange=()=>go(Number(pageInput.value));
    versions.onchange=()=>{active=choices.find(row=>row.id===versions.value);confirmed=null;lastRequest=null;load();};
    async function load(){
      if(departing||!active||!panel.isConnected)return;
      panel.hidden=false;reading=true;modeChanged(true);trigger.setAttribute('aria-pressed','true');
      const page=Number(pageInput.value)||1,request=active.id+':'+page;
      if(request===lastRequest)return;lastRequest=request;const own=++requestNumber;body.replaceChildren();
      previous.disabled=!(active.pages||[]).some(value=>value<page);next.disabled=!(active.pages||[]).some(value=>value>page);
      if(active.freshness!=='unchanged'&&confirmed!==active.id){
        status.textContent=active.freshness==='changed'?'L’original a changé depuis cette traduction. Cette version peut ne plus correspondre.':'La correspondance avec la version actuelle de l’original n’a pas été enregistrée.';
        body.append(button('Lire cette version en gardant cette limite',()=>{confirmed=active.id;lastRequest=null;load();}));return;
      }
      status.textContent='Ouverture du texte français…';
      try{
        const data=await get('french-page?'+new URLSearchParams({id:active.id,original_id:base,page:String(page)}));
        if(departing||own!==requestNumber||!panel.isConnected||!reading)return;
        if(Array.isArray(data.pages)){active.pages=data.pages;previous.disabled=!data.pages.some(value=>value<page);next.disabled=!data.pages.some(value=>value>page);}
        notice.textContent=data.notice||notice.textContent;
        if(!data.available){status.textContent='Cette page n’est pas dans la plage traduite. Pages disponibles : '+active.pages.join(', ')+'.';if(active.pages.length)body.append(button('Ouvrir la première page traduite',()=>go(active.pages[0])));return;}
        status.textContent=data.freshness==='changed'?'L’original a changé depuis la traduction : comparez les deux versions.':data.freshness==='unknown'?'Correspondance des éditions à vérifier.':'Page/section '+data.page+' · texte français enregistré. Les contrôles automatiques ne valident pas le sens.';
        for(const warning of data.warnings||[])body.append(node('p',warning,'french-reading-notice'));
        for(const text of data.parts||[])body.append(node('p',text,'french-reading-part'));
        remember('french');
      }catch(error){if(error.name==='AbortError'&&departing){lastRequest=null;return;}if(!departing&&own===requestNumber&&panel.isConnected){status.textContent='Le texte français est indisponible. Vous pouvez revenir à l’original.';lastRequest=null;body.append(button('Réessayer',()=>load()));}}
    }
    trigger.onclick=()=>{if(reading){showOriginal();return;}if(!active)active=choices[0];versions.value=active?.id||'';load();};
    trigger.setAttribute('aria-pressed','false');
    if(synchronize)window.addEventListener('survie:pdf-page',event=>{if(panel.isConnected){pageInput.value=String(event.detail.page);if(reading)load();}});
    function discover(){get('french-reading?'+new URLSearchParams({original_id:base})).then(data=>{
      if(departing||!panel.isConnected)return;choices=Array.isArray(data.translations)?data.translations:[];
      if(!choices.length){panel.remove();return;}
      versions.replaceChildren();for(const choice of choices){const option=node('option',new Date(choice.published_at*1000).toLocaleDateString('fr-FR')+' · '+(choice.original_edition||'édition inconnue')+(choice.freshness==='changed'?' · original modifié':choice.freshness==='unknown'?' · à comparer':''));option.value=choice.id;versions.append(option);}
      versionLabel.hidden=choices.length<2;active=choices[0];trigger.hidden=false;notice.textContent=data.notice||notice.textContent;
      try{const saved=JSON.parse(localStorage.getItem(key)||'null');const found=choices.find(row=>row.id===saved?.translation);if(found)active=found;versions.value=active.id;if(saved?.mode==='french'&&active.freshness==='unchanged')load();}catch(_){}
    }).catch(error=>{if(error.name!=='AbortError'||!departing)panel.remove();});}
    discover();window.addEventListener('pageshow',event=>{if(event.persisted&&panel.isConnected){lastRequest=null;discover();}});
    return panel;
  }
  document.addEventListener('survie:source',event=>{
    const source=event.detail;if(source.is_ai_translation||!source.id?.startsWith('guide:')&&!source.id?.startsWith('zim:'))return;
    const reader=document.getElementById('reader'),actions=reader?.querySelector('.reader-actions'),body=reader?.querySelector('.reader-body');if(!body||!actions)return;
    const trigger=button('Lire en français',()=>{});trigger.className='secondary';trigger.hidden=true;actions.append(trigger);
    const originalParts=[body,...reader.querySelectorAll('.reader-images')];
    const pdf=source.id.split('#page=')[0].toLowerCase().endsWith('.pdf');
    const panel=mount(source.id,reader,trigger,(french,page)=>{for(const item of originalParts)item.hidden=french;if(!french&&pdf&&page!==(Number(source.id.split('#page=')[1])||1))readSource(source.id.split('#page=')[0]+'#page='+page);},pdf);
    body.before(panel);
  });
  const trigger=document.getElementById('pdf-french'),host=document.getElementById('pdf-reading-area');
  if(trigger&&host){const original=new URLSearchParams(location.search).get('id')||'';if(/^guide:.+\.pdf(?:#page=\d+)?$/i.test(original))mount(original,host,trigger,french=>{document.getElementById('pdf-container').hidden=french;document.querySelector('.pdf-controls').hidden=french;window.dispatchEvent(new CustomEvent('survie:pdf-view',{detail:{original:!french}}));},true,true);}
})();
