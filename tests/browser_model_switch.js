// Visible loading/recovery states, simulated jobs only; no model is contacted.
async page => {
  const base='http://10.0.3.2:8769',checks=[],errors=[];
  const check=(value,label)=>{if(!value)throw Error(label);checks.push(label);};
  page.on('pageerror',e=>errors.push(e.message));
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.goto(base+'/#/assistant');await page.waitForFunction(()=>S.authReady&&S.user&&!S.loadingConversation);
  await page.locator('#chat-reset').click();await page.waitForFunction(()=>!S.conversation);
  const id='f'.repeat(32);let stage='switching',done=false;
  await page.route('**/api/jobs/'+id,route=>route.fulfill({json:{id,mode:'rapide',status:done?'done':'running',created:Date.now()/1000,sources:[],answer:done?'Réponse fictive, une seule question.':'',progress:{stage}}}));
  await page.evaluate(job=>watch(job),id);
  for(const [value,label] of [['switching','Changement de modèle en cours'],['loading','Chargement du modèle'],['retrying','Reprise automatique']]){
    stage=value;await page.waitForFunction(text=>document.getElementById('chat-status').textContent.includes(text),label);
    check((await page.locator('#chat-status').textContent()).includes(label),label+' visible');
    check(await page.locator('#send-question').isDisabled(),'Question en cours, aucun second envoi requis : '+value);
    check(await page.locator('#cancel-job').isVisible(),'Annulation disponible : '+value);
    check(await page.locator('.message-assistant').count()===1,'Un seul message assistant pendant '+value);
  }
  for(const width of [1366,390,320]){
    await page.setViewportSize({width,height:844});
    check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Attente lisible sans débordement à '+width);
  }
  done=true;await page.waitForFunction(()=>S.job===null);
  check((await page.locator('.message-assistant').textContent()).includes('Réponse fictive'),'Réponse finale reçue après la reprise');
  check(await page.locator('.message-assistant').count()===1,'Aucun doublon après reprise');
  check(await page.locator('#send-question').isEnabled(),'Envoi rendu disponible à la fin');
  check(await page.locator('#cancel-job').isHidden(),'Annulation masquée à la fin');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks,real_model:false};
}
