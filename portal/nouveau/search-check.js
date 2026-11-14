/* Explicit read-only checks on the real library, available from Windows/Linux. */
(() => {
  const open=document.getElementById('next-search-check-open'),dialog=document.getElementById('next-search-check-dialog');
  if(!open||!dialog)return;
  const status=document.getElementById('next-search-check-status'),results=document.getElementById('next-search-check-results'),meter=document.getElementById('next-search-check-progress'),cancel=document.getElementById('next-search-check-cancel'),download=document.getElementById('next-search-check-export'),suite=document.getElementById('next-search-check-suite');
  const shortCases=[{query:'allumer un feu'},{query:'faire du feu'},{query:'techniques de production de feu',collection:'wikipedia'},{query:'fabriquer un générateur à pédales'},{query:'rendre eau potable'},{query:'toit abri'},{query:'réparer un vélo'},{query:'conserver les graines'},{query:'faire du feux',domain:'all'},{query:'faire du feux',domain:'resilience'}];
  let controller=null,report=null;
  cancel.onclick=()=>controller?.abort();dialog.addEventListener('close',()=>controller?.abort());

  async function read(path,staticFile=false){
    const request=new AbortController(),parent=controller.signal;let timedOut=false;
    const stop=()=>request.abort();parent.addEventListener('abort',stop,{once:true});
    if(parent.aborted)stop();const timeout=setTimeout(()=>{timedOut=true;request.abort();},20000);
    try{
      if(!staticFile)return await api(path,undefined,{signal:request.signal});
      const response=await fetch(path,{signal:request.signal});
      if(!response.ok)throw Error('La liste des recherches de test est indisponible.');
      return await response.json();
    }catch(error){if(timedOut&&!parent.aborted)throw Error('Le service n’a pas répondu sous 20 secondes.');throw error;}
    finally{clearTimeout(timeout);parent.removeEventListener('abort',stop);}
  }

  async function casesFor(selection){
    if(selection!=='extended')return shortCases;
    const reference=await read('/nouveau/search-reference.json?v=0.5.0',true);
    const valid=reference&&reference.schema===1&&typeof reference.version==='string'&&Array.isArray(reference.cases)&&reference.cases.length>0&&reference.cases.length<=60&&reference.cases.every(item=>item&&typeof item.id==='string'&&typeof item.query==='string'&&item.query.length>0&&item.query.length<=200&&['all','resilience','culture'].includes(item.domain)&&typeof item.need==='string');
    if(!valid||new Set(reference.cases.map(item=>item.id)).size!==reference.cases.length)throw Error('La liste des recherches de test doit être mise à jour.');
    report.reference={version:reference.version,notice:reference.notice};
    return reference.cases;
  }

  function reviewControl(record,article){
    if(!record.results)return;
    const label=element('label','Après lecture, quel résultat est utile ?','search-check-review'),select=element('select');
    select.append(new Option('À vérifier','unreviewed'));
    record.results.forEach((row,index)=>select.append(new Option((index+1)+' · '+row.title,String(index))));
    select.append(new Option('Aucun de ces résultats ne répond au besoin','no_useful'),new Option('Je ne peux pas encore juger','uncertain'));
    select.onchange=()=>{
      const index=Number(select.value),row=/^\d+$/.test(select.value)?record.results[index]:null;
      record.review=row?{state:'useful',source_id:row.id,rank:index+1}:{state:select.value};
    };
    label.append(select);article.append(label);
  }

  open.onclick=async()=>{
    if(controller)return;
    const selected=suite.value;
    report={schema:2,created:new Date().toISOString(),version:null,suite:selected,status:'running',cases:[]};controller=new AbortController();open.disabled=true;suite.disabled=true;results.replaceChildren();meter.value=0;download.hidden=true;cancel.hidden=false;
    if(!dialog.open)dialog.showModal();
    try{
      status.textContent='Préparation des recherches de test…';
      const cases=await casesFor(selected);meter.max=cases.length;
      status.textContent='Vérification des services documentaires…';
      try{report.version=(await read('/health')).version;}catch(error){if(error.name==='AbortError')throw error;}
      try{report.diagnostic=await read('/library/search-diagnostic');}catch(error){if(error.name==='AbortError')throw error;report.diagnostic={error:error.message};}
      for(const [index,item] of cases.entries()){
        if(controller.signal.aborted)break;
        status.textContent=(index+1)+' / '+cases.length+' — '+item.query;
        const started=performance.now(),record={...item,review:{state:'unreviewed'}},article=element('article',undefined,'search-check-case');article.append(element('h3',item.query+(item.domain==='resilience'?' · Autonomie et résilience':'')));results.append(article);
        if(item.need)article.append(element('p',item.need,'small'));
        try{
          const params=new URLSearchParams({q:item.query,language:'',limit:'5',collection:item.collection||'',domain:item.domain||'all',diagnostic:'true'});
          const data=await read('/search?'+params);record.elapsed_ms=Math.round(performance.now()-started);record.coverage=data.coverage||null;
          record.results=(data.results||[]).slice(0,5).map(row=>({id:row.id,title:row.title,language:row.language,collection:row.collection,match:row.match,url:row.url,excerpt:row.excerpt,domains:row.domains}));
          article.append(element('p',record.results.length+' document(s) affiché(s) · '+(record.elapsed_ms/1000).toLocaleString('fr-FR',{maximumFractionDigits:1})+' s.','small muted'));
          if(record.coverage?.warning)article.append(element('p',record.coverage.warning,'small'));
          if(!record.results.length)article.append(element('p','Aucun résultat trouvé par cette recherche. Vérifiez les limites indiquées ; cela ne prouve pas que le sujet est absent.'));
          const list=element('ol');
          for(const row of record.results){
            const li=element('li'),link=element('a',row.title+' ↗');
            link.href='/#/bibliotheque/recherche?'+new URLSearchParams({q:item.query,collection:item.collection||'',domain:item.domain||'all',source:row.id});link.target='_blank';link.rel='noopener';li.append(link);list.append(li);
          }
          article.append(list);reviewControl(record,article);
        }catch(error){if(error.name==='AbortError')break;record.elapsed_ms=Math.round(performance.now()-started);record.error=error.message||'Cette recherche n’a pas abouti.';article.append(element('p',record.error,'error'));}
        report.cases.push(record);meter.value=report.cases.length;
      }
      report.status=controller.signal.aborted?'cancelled':'measured';status.textContent=report.status==='cancelled'?'Vérification arrêtée. Les résultats déjà reçus sont conservés.':report.cases.length+' recherches terminées'+(report.cases.some(row=>row.error)?' · '+report.cases.filter(row=>row.error).length+' en erreur':'')+'. Ouvrez les documents pour juger de leur utilité.';
    }catch(error){report.status=error.name==='AbortError'?'cancelled':'error';status.textContent=error.name==='AbortError'?'Vérification arrêtée.':error.message;}
    finally{controller=null;open.disabled=false;suite.disabled=false;cancel.hidden=true;download.hidden=!report;}
  };

  download.onclick=()=>{
    if(!report)return;
    report.review_summary={reviewed:report.cases.filter(row=>row.review.state!=='unreviewed').length,useful:report.cases.filter(row=>row.review.state==='useful').length,total:report.cases.length};
    const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='setupsurvie-recherche-'+report.created.slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
})();
