/* Family profile: add YouTube videos from a list; the server PC downloads them. */
(() => {
  const area=element('details');area.id='next-youtube';
  area.innerHTML='<summary>Ajouter des vidéos depuis YouTube</summary>'
    +'<p class="small">Collez les adresses des vidéos, une par ligne, ou choisissez un fichier texte. Une ligne <code>[Thème]</code> range les vidéos suivantes dans un dossier de ce nom. Le PC serveur télécharge les vidéos avec Internet, puis elles apparaissent toutes seules dans la bibliothèque, avec les pistes récupérées ou préparées automatiquement.</p>'
    +'<label for="next-youtube-file">Fichier de la liste (facultatif)</label><input id="next-youtube-file" type="file" accept=".txt,text/plain">'
    +'<label for="next-youtube-text">Adresses des vidéos</label><textarea id="next-youtube-text" rows="6" spellcheck="false" placeholder="https://www.youtube.com/watch?v=…&#10;[Eau]&#10;https://youtu.be/…"></textarea>'
    +'<label for="next-youtube-quality">Qualité</label><select id="next-youtube-quality"><option value="480">Normale (480p, conseillée)</option><option value="360">Petite (360p, prend moins de place)</option><option value="720">Bonne (720p, gestes plus visibles)</option></select>'
    +'<div class="actions"><button id="next-youtube-check" class="secondary">Vérifier la liste</button><button id="next-youtube-start">Télécharger les vidéos</button><button id="next-youtube-pause" class="secondary" hidden>Mettre en pause</button><button id="next-youtube-resume" class="secondary" hidden>Reprendre</button></div>'
    +'<p class="small"><a href="#/file" data-route="file">Suivre les téléchargements et sous-titres dans la file</a></p>'
    +'<p id="next-youtube-message" class="small" role="status"></p><ul id="next-youtube-refused" class="small" hidden></ul>'
    +'<p id="next-youtube-connection" class="small work-queue-preview-notice" role="status" hidden></p>'
    +'<div id="next-youtube-progress" hidden><progress id="next-youtube-bar" max="1" value="0" style="width:100%" aria-label="Avancement du téléchargement"></progress><p id="next-youtube-status" class="small" role="status"></p><ul id="next-youtube-items" class="small"></ul></div>'
    +'<p class="small muted">Les vidéos restent la propriété de leurs auteurs : usage privé, sans redistribution. Aucun compte YouTube n’est utilisé et aucun blocage n’est contourné.</p>';
  // Moved into Mon appareil → Bibliothèque et préparations by settings-layout.js.
  area.className='settings-advanced';$('next-videos').append(area);
  const shortcut=element('p',undefined,'small');shortcut.id='next-youtube-shortcut';const go=element('a','Ajouter des vidéos depuis une liste YouTube →');go.href='#/appareil/bibliotheque';shortcut.append(go);$('next-videos').querySelector('#next-videos-admin').after(shortcut);
  let latest=null,busy=false,loading=false,generation=0,finished=false;
  const running=phase=>['starting','planning','downloading','refreshing'].includes(phase);
  const icons={downloaded:'✓',skipped:'•',refused:'✗',error:'✗'};
  function showRefused(list){
    const target=$('next-youtube-refused');target.replaceChildren();target.hidden=!list.length;
    for(const item of list.slice(0,30))target.append(element('li','Ligne '+item.line+' : '+item.message+(item.text?' — '+item.text:'')));
    if(list.length>30)target.append(element('li',(list.length-30)+' autre(s) ligne(s) écartée(s).'));
  }
  function commandButtons(){
    $('next-youtube-start').disabled=busy;
    $('next-youtube-check').disabled=busy;
    $('next-youtube-file').disabled=busy;
  }
  function trackingUnavailable(){
    const note=$('next-youtube-connection');
    note.textContent=latest?'Suivi du PC serveur indisponible. Dernier état connu.':'Suivi du PC serveur indisponible. Nouvelle tentative automatique.';
    note.hidden=false;
    $('next-youtube-pause').disabled=$('next-youtube-resume').disabled=true;
  }
  function render(value){
    if(value.available===false||value.phase==='unknown'){trackingUnavailable();return;}
    $('next-youtube-connection').hidden=true;
    $('next-youtube-pause').disabled=$('next-youtube-resume').disabled=false;
    latest=value;const progress=value.progress||{},counts=progress.counts||{},phase=value.phase;
    const admin=S.user?.role==='admin';area.hidden=!admin;
    commandButtons();
    $('next-youtube-pause').hidden=!running(phase)||value.pause_requested;$('next-youtube-resume').hidden=!value.resumable;
    const shown=value.options&&phase&&!['idle','busy','unknown'].includes(phase);$('next-youtube-progress').hidden=!shown;
    if(!shown){if(value.message&&!$('next-youtube-message').textContent)$('next-youtube-message').textContent=value.message;return;}
    const total=progress.videos??value.options.videos??0;
    const processed=Number.isInteger(progress.done)&&Number.isInteger(progress.total)
      ?progress.done-(progress.total-total)
      :(counts.downloaded||0)+(counts.skipped||0)+(counts.error||0);
    $('next-youtube-bar').max=Math.max(1,total);$('next-youtube-bar').value=Math.max(0,Math.min(total,processed));
    const current=progress.current&&running(phase)?' En cours : vidéo '+progress.current.index+' sur '+total+(progress.current.percent==null?'':', fichier '+Math.round(progress.current.percent)+' %')+'.':'';
    $('next-youtube-status').textContent=(value.message||'')+current;
    const items=$('next-youtube-items');items.replaceChildren();
    for(const item of (progress.items||[]).slice(-12).reverse()){
      const text=(icons[item.status]||'')+' Ligne '+item.line+' : '+(item.status==='downloaded'?(item.title||item.path||'vidéo')+' — ajoutée'+(item.subtitles_skipped?' sans piste YouTube ; préparation automatique dans la file':''):item.message||item.status);
      items.append(element('li',text));
    }
    if(phase==='completed'&&!finished){finished=true;document.dispatchEvent(new Event('survie:videos-changed'));}
    if(running(phase))finished=false;
  }
  async function refresh(){
    if(!S.authReady||S.user?.role!=='admin'||loading||document.hidden)return;
    loading=true;const current=++generation,profile=S.user.id;
    try{const value=await api('/admin/youtube-downloads');if(current===generation&&profile===S.user?.id)render(value);}
    catch{if(current===generation)trackingUnavailable();}
    finally{loading=false;}
  }
  function list(){return $('next-youtube-text').value;}
  async function check(text=list()){
    if(!text.trim()){$('next-youtube-message').textContent='Collez au moins une adresse de vidéo YouTube.';return null;}
    const value=await api('/admin/youtube-downloads/check',{text,max_height:Number($('next-youtube-quality').value)});
    $('next-youtube-message').textContent=value.videos.length+' vidéo(s) prête(s) à télécharger'+(value.refused.length?', '+value.refused.length+' ligne(s) écartée(s) :':'.');
    showRefused(value.refused);return value;
  }
  async function command(work){
    if(busy)return;busy=true;commandButtons();const profile=S.user?.id;
    try{await work();}
    catch(error){if(S.user?.id===profile)$('next-youtube-message').textContent=error.message;}
    finally{busy=false;commandButtons();}
    await refresh();
  }
  function decodeList(bytes){
    if(bytes[0]===255&&bytes[1]===254)return new TextDecoder('utf-16le').decode(bytes);
    if(bytes[0]===254&&bytes[1]===255)return new TextDecoder('utf-16be').decode(bytes);
    // Some Windows editors omit the BOM. Plain-text URLs in UTF-16 still
    // have a zero byte after or before each ASCII character.
    const sample=bytes.subarray(0,128);
    const zeros=[0,0];
    sample.forEach((value,index)=>{if(value===0)zeros[index%2]++;});
    if(zeros[0]>sample.length/5&&zeros[1]===0)return new TextDecoder('utf-16be').decode(bytes);
    if(zeros[1]>sample.length/5&&zeros[0]===0)return new TextDecoder('utf-16le').decode(bytes);
    try{return new TextDecoder('utf-8',{fatal:true}).decode(bytes);}
    catch{return new TextDecoder('windows-1252').decode(bytes);}
  }
  $('next-youtube-file').addEventListener('change',event=>command(async()=>{
    const file=event.target.files?.[0];if(!file)return;
    event.target.value='';
    $('next-youtube-text').value='';
    showRefused([]);
    if(file.size>300000)throw Error('Fichier trop grand : divisez-le en plusieurs listes.');
    $('next-youtube-message').textContent='Lecture du fichier…';
    let text;
    try{text=decodeList(new Uint8Array(await file.arrayBuffer()));}
    catch{throw Error('Impossible de lire ce fichier. Enregistrez la liste au format texte (.txt).');}
    if(!text.trim()||text.includes('\0'))throw Error('Le fichier est vide ou son format texte n’est pas reconnu.');
    $('next-youtube-text').value=text;
    await check();
  }));
  $('next-youtube-check').onclick=()=>command(()=>check());
  $('next-youtube-start').onclick=()=>command(async()=>{
    const text=list(),max_height=Number($('next-youtube-quality').value);
    const checked=await check(text);if(!checked||!checked.videos.length)return;
    await api('/admin/youtube-downloads',{text,max_height});
    $('next-youtube-message').textContent='Liste ajoutée à la file. Vous pouvez fermer cette page.';finished=false;
  });
  $('next-youtube-pause').onclick=()=>command(async()=>{await api('/admin/youtube-downloads/pause',{});$('next-youtube-message').textContent='Pause demandée : la vidéo en cours reprendra au même endroit.';});
  $('next-youtube-resume').onclick=()=>command(async()=>{await api('/admin/youtube-downloads/resume',{});$('next-youtube-message').textContent='Reprise demandée.';finished=false;});
  document.addEventListener('survie:auth',()=>{generation++;latest=null;area.hidden=S.user?.role!=='admin';shortcut.hidden=area.hidden;if(area.open)refresh();});
  area.addEventListener('toggle',()=>{if(area.open)refresh();});
  setInterval(()=>{if(area.offsetParent&&(area.open||running(latest?.phase)))refresh();},2000);
  area.hidden=true;shortcut.hidden=true;
})();
