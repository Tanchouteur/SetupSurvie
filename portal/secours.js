(() => {
  const $=id=>document.getElementById(id),kiwix=new URL(location.href);kiwix.port=location.protocol==='https:'?'8445':'8081';kiwix.pathname='/';kiwix.search='';kiwix.hash='';$('emergency-kiwix').href=kiwix.href;
  let documents=[];
  function render(){
    const query=$('emergency-query').value.trim().toLocaleLowerCase(),list=$('emergency-documents');list.replaceChildren();
    const found=documents.filter(d=>String(d.title).toLocaleLowerCase().includes(query));
    for(const item of found.slice(0,200)){const li=document.createElement('li'),a=document.createElement('a');a.textContent=item.title;a.href=item.url;a.target='_blank';a.rel='noopener';li.append(a);list.append(li);}
    $('emergency-status').textContent=found.length+' document(s) dans la dernière liste locale, jusqu’à 200 affichés (affinez le filtre au besoin). Ce filtre porte sur les titres ; la recherche dans le contenu nécessite le pilote.';
  }
  async function load(){
    for(const endpoint of ['/guides/_setupsurvie-index.json','/catalog/guides.json']){
      try{
        const response=await fetch(endpoint);if(!response.ok)continue;
        const data=await response.json();if(!Array.isArray(data.documents))continue;
        documents=data.documents.map(d=>({title:String(d.title||d.path||'Document'),url:d.url||('/guides/'+String(d.path).split('/').map(encodeURIComponent).join('/'))})).filter(d=>{
          try{const u=new URL(d.url,location.href);return u.origin===location.origin&&u.pathname.startsWith('/guides/')&&!u.pathname.includes('..');}catch(_){return false;}
        });render();return;
      }catch(_){/* Fall back to the installer's previous static catalogue. */}
    }
    $('emergency-status').textContent='La liste locale n’est pas disponible. Kiwix reste accessible par le lien ci-dessus. Conservez les données et consultez le guide de reprise.';
  }
  $('emergency-query').oninput=render;load();
})();
