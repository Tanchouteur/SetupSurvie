/* Explicit read-only checks on the real library, available from Windows/Linux. */
(() => {
  const open=document.getElementById('next-search-check-open'),dialog=document.getElementById('next-search-check-dialog');
  if(!open||!dialog)return;
  const status=document.getElementById('next-search-check-status'),results=document.getElementById('next-search-check-results'),meter=document.getElementById('next-search-check-progress'),cancel=document.getElementById('next-search-check-cancel'),download=document.getElementById('next-search-check-export');
  const cases=[{query:'allumer un feu'},{query:'faire du feu'},{query:'techniques de production de feu',collection:'wikipedia'},{query:'fabriquer un générateur à pédales'},{query:'rendre eau potable'},{query:'toit abri'},{query:'réparer un vélo'},{query:'conserver les graines'}];
  let controller=null,report=null;
  cancel.onclick=()=>controller?.abort();dialog.addEventListener('close',()=>controller?.abort());
  async function read(path){
    const request=new AbortController(),parent=controller.signal;let timedOut=false;
    const stop=()=>request.abort();parent.addEventListener('abort',stop,{once:true});
    if(parent.aborted)stop();const timeout=setTimeout(()=>{timedOut=true;request.abort();},20000);
    try{return await api(path,undefined,{signal:request.signal});}
    catch(error){if(timedOut&&!parent.aborted)throw Error('Le service n’a pas répondu sous 20 secondes.');throw error;}
    finally{clearTimeout(timeout);parent.removeEventListener('abort',stop);}
  }
  open.onclick=async()=>{
    if(controller)return;
    report={created:new Date().toISOString(),version:null,status:'running',cases:[]};controller=new AbortController();open.disabled=true;results.replaceChildren();meter.value=0;meter.max=cases.length;download.hidden=true;cancel.hidden=false;
    if(!dialog.open)dialog.showModal();
    try{
      try{report.version=(await read('/health')).version;}catch(error){if(error.name==='AbortError')throw error;}
      for(const [index,item] of cases.entries()){
        if(controller.signal.aborted)break;
        status.textContent=(index+1)+' / '+cases.length+' — '+item.query;
        const started=performance.now(),record={...item},article=element('article',undefined,'search-check-case');article.append(element('h3',item.query+(item.collection?' · Wikipédia':'')));results.append(article);
        try{
          const params=new URLSearchParams({q:item.query,language:'',limit:'5',collection:item.collection||''});
          const data=await read('/search?'+params);record.elapsed_ms=Math.round(performance.now()-started);record.coverage=data.coverage||null;
          record.results=(data.results||[]).slice(0,5).map(row=>({id:row.id,title:row.title,language:row.language,collection:row.collection,match:row.match,url:row.url}));
          article.append(element('p',record.results.length+' document(s) affiché(s) · '+(record.elapsed_ms/1000).toLocaleString('fr-FR',{maximumFractionDigits:1})+' s.','small muted'));
          if(record.coverage?.warning)article.append(element('p',record.coverage.warning,'small'));
          if(!record.results.length)article.append(element('p','Aucun résultat trouvé par cette recherche. Vérifiez les limites indiquées ; cela ne prouve pas que le sujet est absent.'));
          const list=element('ol');
          for(const row of record.results){const li=element('li'),link=element('a',row.title+' ↗');link.href='/#/bibliotheque/recherche?'+new URLSearchParams({q:item.query,collection:item.collection||'',source:row.id});link.target='_blank';link.rel='noopener';li.append(link);list.append(li);}article.append(list);
        }catch(error){if(error.name==='AbortError')break;record.elapsed_ms=Math.round(performance.now()-started);record.error=error.message||'Cette recherche n’a pas abouti.';article.append(element('p',record.error,'error'));}
        report.cases.push(record);meter.value=report.cases.length;
      }
      report.status=controller.signal.aborted?'cancelled':'measured';status.textContent=report.status==='cancelled'?'Vérification arrêtée. Les résultats déjà reçus sont conservés.':report.cases.length+' recherches terminées'+(report.cases.some(row=>row.error)?' · '+report.cases.filter(row=>row.error).length+' en erreur':'')+'. Ouvrez les documents pour juger de leur utilité.';
    }catch(error){report.status=error.name==='AbortError'?'cancelled':'error';status.textContent=error.name==='AbortError'?'Vérification arrêtée.':error.message;}
    finally{controller=null;open.disabled=false;cancel.hidden=true;download.hidden=!report;}
  };
  download.onclick=()=>{if(!report)return;const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='setupsurvie-recherche-'+report.created.slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
})();
