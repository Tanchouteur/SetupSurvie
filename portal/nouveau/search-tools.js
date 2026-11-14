/* Optional preparation runs on the server; closing this page never stops a job. */
(() => {
  let models=[],loaded=false,busy=false;
  async function refresh(){
    if(document.hidden||$('view-settings').hidden||S.user?.role!=='admin'||busy)return;
    busy=true;
    try{
      const data=await api('/admin/library'),index=data.search_index||{};
      $('next-index-status').textContent=(data.message||'')+' · Index : '+(index.completed||0)+' / '+(index.archives||0)+' archives examinées · '+(index.articles||0)+' articles indexés.';
      $('next-index-start').disabled=!data.index_reader_ready; $('next-index-prepare').disabled=!!data.index_reader_ready;
      $('next-index-pause').disabled=!['starting','planning','downloading'].includes(data.phase);
      if(!loaded){
        models=(await api('/admin/context')).models;const select=$('next-context-model');select.replaceChildren();for(const row of models)select.append(new Option(row.model,row.model));
        $('next-context-size').value=String(models[0]?.tokens||16384);loaded=true;
      }
    }catch(error){$('next-index-status').textContent=error.message;}
    finally{busy=false;}
  }
  for(const [id,action] of [['prepare','prepare'],['start','start'],['pause','pause']])$('next-index-'+id).onclick=async()=>{
    try{await api('/admin/library/index/'+action,{});$('next-index-status').textContent='Commande transmise au PC serveur.';await refresh();}
    catch(error){$('next-index-status').textContent=error.message;}
  };
  $('next-context-model').onchange=()=>{$('next-context-size').value=String(models.find(m=>m.model===$('next-context-model').value)?.tokens||16384);};
  $('next-context-form').onsubmit=async event=>{
    event.preventDefault();try{const row=await api('/admin/context',{model:$('next-context-model').value,tokens:Number($('next-context-size').value)});const previous=models.find(m=>m.model===row.model);if(previous)previous.tokens=row.tokens;$('next-context-status').textContent='Contexte enregistré pour les prochaines réponses.';}
    catch(error){$('next-context-status').textContent=error.message;}
  };
  setInterval(refresh,5000);new MutationObserver(refresh).observe($('view-settings'),{attributes:true,attributeFilter:['hidden']});
})();
