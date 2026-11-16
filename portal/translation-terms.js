/* Optional personal vocabulary, frozen when each translation starts. */
(() => {
  const area=element('details');area.id='translation-terms';
  const summary=element('summary','Mots à traduire de la même façon (facultatif)'),intro=element('p','Indiquez vos choix de vocabulaire. Ils seront repris pour les prochaines traductions de ce profil. Un travail déjà lancé conserve les mots choisis à son départ.','small');
  const current=element('p',undefined,'small'),fixed=element('ul',undefined,'small'),rows=element('div'),actions=element('div',undefined,'translation-actions'),message=element('p',undefined,'small');
  current.id='translation-terms-current';rows.id='translation-terms-rows';message.id='translation-terms-message';message.setAttribute('role','status');
  const add=button('Ajouter un mot',()=>append(),'secondary'),save=button('Enregistrer ces mots',persist,'secondary');
  actions.append(add,save);area.append(summary,intro,current,fixed,rows,actions,message);$('translation-range').before(area);
  let owner=null,loaded=false,busy=false,dirty=false,generation=0;
  function inputsDisabled(value){for(const node of area.querySelectorAll('input,button'))node.disabled=value;}
  function changed(){dirty=true;message.textContent='Modifications non enregistrées : elles ne seront pas utilisées avant « Enregistrer ces mots ».';}
  function append(value={source:'',french:''},editing=true){
    if(rows.children.length>=40){message.textContent='La liste contient déjà 40 termes. Retirez-en un avant d’en ajouter.';return;}
    const row=element('div',undefined,'translation-term-row');
    for(const [key,title,example] of [['source','Dans le texte original','Exemple : bearing'],['french','En français','Exemple : roulement']]){
      const label=element('label',title),input=element('input');input.type='text';input.maxLength=100;input.value=value[key]||'';input.placeholder=example;input.dataset.term=key;input.addEventListener('input',changed);label.append(input);row.append(label);
    }
    row.append(button('Retirer ce mot',()=>{row.remove();changed();},'secondary'));rows.append(row);if(editing)changed();
  }
  async function refresh(){
    if(!S.user||busy||loaded&&owner===S.user.id)return;
    const profile=S.user.id,version=++generation;busy=true;inputsDisabled(true);message.textContent='Chargement du vocabulaire…';
    try{
      const data=await api('/translation-terms');if(S.user?.id!==profile||generation!==version)return;
      rows.replaceChildren();for(const value of data.terms)append(value,false);owner=profile;loaded=true;dirty=false;message.textContent=data.terms.length?'Vocabulaire enregistré pour les prochaines traductions.':'Aucun mot imposé. Vous pouvez traduire sans remplir cette liste.';
    }catch(error){if(generation===version)message.textContent=error.message;}
    finally{busy=false;inputsDisabled(!loaded||S.user?.id!==owner);if(area.open&&S.user&&S.user.id!==profile)refresh();}
  }
  async function persist(){
    if(busy||!loaded||owner!==S.user?.id)return;
    const profile=S.user.id,version=generation;busy=true;inputsDisabled(true);message.textContent='Enregistrement…';
    try{
      const terms=[...rows.children].map(row=>Object.fromEntries([...row.querySelectorAll('input')].map(input=>[input.dataset.term,input.value])));
      const data=await api('/translation-terms',{terms},{method:'PUT'});if(profile!==S.user?.id||generation!==version)return;
      dirty=false;message.textContent=data.terms.length+' mot(s) enregistré(s) pour les prochaines traductions. Les travaux existants restent inchangés.';
    }catch(error){if(generation===version)message.textContent=error.message;}
    finally{busy=false;inputsDisabled(!loaded||S.user?.id!==owner);if(area.open&&S.user&&S.user.id!==profile)refresh();}
  }
  area.addEventListener('toggle',()=>{if(area.open)refresh();});
  document.addEventListener('survie:auth',()=>{generation++;owner=null;loaded=false;dirty=false;rows.replaceChildren();current.textContent='';fixed.replaceChildren();message.textContent='';if(area.open)refresh();else inputsDisabled(true);});
  document.addEventListener('survie:translation',event=>{const data=event.detail;current.textContent=data.guidance?.version?'Ce travail conserve '+data.guidance.terms.length+' terme(s) de son départ. Le passage précédent sert seulement de repère de cohérence ; sa fidélité reste à vérifier.':'Ce travail ancien n’avait pas de vocabulaire enregistré. Une reprise conserve ce fonctionnement.';fixed.replaceChildren(...(data.guidance?.terms||[]).map(row=>element('li',row.source+' → '+row.french)));});
  document.addEventListener('survie:translation-clear',()=>{current.textContent='';fixed.replaceChildren();});
  $('translation-start').addEventListener('click',event=>{if(dirty){event.preventDefault();event.stopImmediatePropagation();area.open=true;message.textContent='Enregistrez vos mots avant de lancer la traduction, ou rechargez la page pour les abandonner.';}},true);
  inputsDisabled(true);
})();
