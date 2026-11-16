/* Original illustrations only. Selection uses captions; pixels are not interpreted. */
(()=>{
  'use strict';
  const urls=new Map(),tasks=new Set();let queue=Promise.resolve(),pdfLibrary=null,worker=null,departing=false;
  function addURL(img,blob){const url=URL.createObjectURL(blob);urls.set(img,url);img.src=url;}
  new MutationObserver(records=>{for(const record of records)for(const node of record.removedNodes)if(node.nodeType===1&&!node.isConnected){if(node.matches('.source-figure'))observer.unobserve(node);for(const figure of node.querySelectorAll('.source-figure'))observer.unobserve(figure);}for(const [img,url] of urls)if(!img.isConnected){URL.revokeObjectURL(url);urls.delete(img);}}).observe($('chat-messages'),{childList:true,subtree:true});
  const observer=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting&&!departing){observer.unobserve(entry.target);const run=entry.target.loadOriginal;if(run)queue=queue.then(()=>!departing&&entry.target.isConnected?run():undefined).catch(()=>{});}},{rootMargin:'200px'});
  function validated(item,source){
    if(!item||typeof item.id!=='string'||item.id.length>2000||typeof source.id!=='string'||!/^(guide|zim):/.test(source.id))return false;
    if(item.kind==='pdf_page')return /^guide:.+\.pdf#page=[1-9]\d{0,3}$/i.test(item.id)&&item.id.split('#page=')[0]===source.id.split('#page=')[0]&&Number(item.id.split('#page=')[1])<=1200;
    if(item.kind==='image')return item.id.startsWith('zim:')&&source.id.startsWith('zim:')&&item.id.split('/')[0]===source.id.split('/')[0]&&!/[%\\?#\x00-\x1f]/.test(item.id)&&!item.id.slice(4).split('/').some(p=>!p||p==='.'||p==='..');
    return false;
  }
  async function pdfImage(item,img,status){
    const query='?id='+encodeURIComponent(item.id)+'&revision='+encodeURIComponent(item.revision||'');
    const checked=await api('/illustrations/document'+query);
    if(departing||!img.isConnected)return;
    if(!pdfLibrary)pdfLibrary=await import('/vendor/pdfjs/pdf.mjs');
    if(departing||!img.isConnected)return;
    if(!worker){pdfLibrary.GlobalWorkerOptions.workerSrc='/vendor/pdfjs/pdf.worker.mjs';worker=new pdfLibrary.PDFWorker();}
    let task=null,canvas=null;
    try{
      task=pdfLibrary.getDocument({url:checked.url,worker,cMapUrl:'/vendor/pdfjs/cmaps/',cMapPacked:true,standardFontDataUrl:'/vendor/pdfjs/standard_fonts/',wasmUrl:'/vendor/pdfjs/wasm/',isEvalSupported:false,disableAutoFetch:true,disableStream:true,enableXfa:false});
      tasks.add(task);
      const document=await task.promise,page=await document.getPage(checked.page),initial=page.getViewport({scale:1});
      const scale=Math.min(900/initial.width,1200/initial.height,Math.sqrt(1_000_000/(initial.width*initial.height))),viewport=page.getViewport({scale});
      if(departing||!img.isConnected)return;
      canvas=window.document.createElement('canvas');canvas.width=Math.ceil(viewport.width);canvas.height=Math.ceil(viewport.height);
      await page.render({canvasContext:canvas.getContext('2d'),viewport}).promise;
      await api('/illustrations/document'+query); // Refuse a changed source, including during rendering.
      const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
      if(!blob)throw Error('Aperçu PDF indisponible.');
      if(!departing&&img.isConnected){addURL(img,blob);status.textContent=checked.version_checked?'Page originale · ouvrir le PDF pour agrandir.':'Page originale · version du fichier non vérifiable.';}
    }finally{if(canvas)canvas.width=canvas.height=0;if(task){tasks.delete(task);await task.destroy();}}
  }
  function card(item,source){
    const figure=element('figure',undefined,'source-figure'),img=element('img'),status=element('p','Chargement de l’original…','small muted');
    img.alt=item.alt||item.caption||'Illustration du document';img.loading='lazy';img.decoding='async';
    const caption=element('figcaption');caption.append(element('strong','['+source.number+'] '+source.title),element('p',item.caption||item.alt||'Sans légende enregistrée.'));
    caption.append(element('p',sourceDates(source),'small muted'));
    if(source.provenance)caption.append(element('p',source.provenance,'small muted'));
    if(source.licence)caption.append(element('p',source.licence,'small muted'));
    const actions=element('div',undefined,'source-figure-actions');actions.append(button(item.kind==='pdf_page'?'Consulter cette page':'Consulter le document source',()=>readSource(item.kind==='pdf_page'?item.id:source.id),'text-button'));
    const original=element('a','Ouvrir l’original en grand','secondary-link');original.href=item.kind==='pdf_page'?'/pdf.html?id='+encodeURIComponent(item.id):'/api/media?id='+encodeURIComponent(item.id)+'&source_id='+encodeURIComponent(source.id)+'&revision='+encodeURIComponent(item.revision||'');original.target='_blank';original.rel='noopener';actions.append(original);caption.append(actions);
    img.onerror=()=>{img.hidden=true;status.textContent='Ce visuel est indisponible ou son document a changé. Consultez le document source.';};
    figure.loadOriginal=async()=>{
      try{
        if(item.kind==='pdf_page')await pdfImage(item,img,status);
        else{img.onload=()=>{status.textContent='Illustration originale · sélection d’après la légende.';};img.src=original.href;}
      }catch(error){img.hidden=true;status.textContent=error.status?error.message:'L’aperçu ne peut pas être affiché. Ouvrez le document source.';}
    };
    const preview=element('a');preview.href=original.href;preview.target='_blank';preview.rel='noopener';preview.append(img);figure.append(preview,status,caption);observer.observe(figure);return figure;
  }
  function show(node,sources){
    if(!node||!Array.isArray(sources))return;
    const relevant=sources.filter(source=>source.figure_status),chosen=[];
    for(const source of relevant)for(const item of (Array.isArray(source.figures)?source.figures:[]).slice(0,4))if(validated(item,source))chosen.push({item,source});
    if(!relevant.length&&!chosen.length)return;
    const key=JSON.stringify(relevant.map(source=>[source.id,source.figure_status,source.figures]));
    if(node.figureKey===key)return;node.figureKey=key;
    const old=node.querySelector('.source-figures'),details=element('details',undefined,'source-figures');details.open=old?old.open:chosen.length>0;
    details.append(element('summary',chosen.length?'Illustrations originales · '+Math.min(4,chosen.length)+' visuel(s)':'Illustrations des documents'));
    details.append(element('p',chosen.length?'Sélection à partir des légendes et des textes consultés. Les images ne sont pas interprétées par l’IA. Ouvrez l’original pour lire les détails et les avertissements.':relevant.some(source=>source.figure_status==='unavailable')?'La sélection d’illustrations n’a pas abouti. Les documents sources restent consultables.':'Aucun visuel retenu pour cette demande ; cela ne prouve pas une absence d’illustrations dans la bibliothèque.','small muted'));
    const grid=element('div',undefined,'source-figure-grid');for(const entry of chosen.slice(0,4))grid.append(card(entry.item,entry.source));details.append(grid);
    if(old)old.replaceWith(details);else node.append(details);
  }
  document.addEventListener('survie:message',event=>show(event.detail.node,event.detail.sources));
  document.addEventListener('survie:job',event=>{if(['done','incomplete','failed','cancelled','interrupted'].includes(event.detail.status))show($('chat-messages').lastElementChild,event.detail.sources);});
  for(const node of $('chat-messages').children)show(node,node.sourceReferences);
  window.addEventListener('pagehide',()=>{departing=true;observer.disconnect();for(const url of urls.values())URL.revokeObjectURL(url);urls.clear();for(const task of tasks)task.destroy().catch(()=>{});worker?.destroy();});
})();
