// Fixture only: numbers are deliberately altered by the fake inference server.
async page => {
  const base='http://10.0.3.2:8769';
  await page.setViewportSize({width:1366,height:900});await page.unrouteAll({behavior:'wait'});await page.goto('about:blank');
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.goto(base+'/#/bibliotheque/recherche');await page.waitForFunction(()=>S.user?.id==='browser');
  async function begin(source){
    const r=await page.request.post(base+'/api/translations',{data:{source_id:source,mode:'rapide'},headers:{Origin:base}});
    if(!r.ok())throw Error(await r.text());const t=await r.json();
    const done=await page.evaluate(async id=>{
      const end=performance.now()+30000;
      while(performance.now()<end){const t=await(await fetch('/api/translations/'+id)).json();if(['completed','error'].includes(t.status))return t;await new Promise(r=>setTimeout(r,100));}
      throw Error('Quality fixture timed out');
    },t.id);
    await page.evaluate(id=>openConversation(id),done.conversation_id);
    await page.waitForFunction(id=>S.translation===id,done.id);
    await page.locator('#translation-panel').evaluate(n=>n.open=true);
    return done;
  }
  const bad=await begin('guide:quality-bad.en.txt');
  if(bad.status!=='completed'||bad.done!==0||bad.deferred!==1||bad.parts[0].candidate.indexOf('100 mg')<0||bad.publication.source_id)throw Error('Bad number accepted');
  await page.getByText('Passage refusé par les contrôles.',{exact:true}).waitFor();
  const source=page.locator('.translation-comparison');await source.locator('summary').click();
  if(!(await source.locator('pre').innerText()).includes('10 mg'))throw Error('Original text missing');
  await page.getByText('Voir la proposition refusée · ne pas utiliser',{exact:true}).click();
  await page.getByText('Utilisez 100 mg. Ne dépassez pas la limite.',{exact:true}).waitFor();
  for(const [width,height] of [[1366,900],[390,844],[320,568]]){
    await page.setViewportSize({width,height});await page.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth&&document.getElementById('send-question').getBoundingClientRect().bottom<=innerHeight);
  }
  const partial=await begin('guide:quality-partial.en.pdf');
  if(partial.status!=='completed'||partial.done!==2||partial.deferred!==1)throw Error('The later section did not finish');
  const retry=page.getByRole('button',{name:'Reprendre les passages à vérifier'});
  await retry.waitFor();await page.getByText('Le dernier chapitre est bref.',{exact:true}).waitFor();
  const publication=page.getByRole('button',{name:'Lire la traduction partielle partagée'});
  await publication.waitFor();
  const shared=await page.evaluate(async id=>(await(await fetch('/api/translations/'+id)).json()).publication,partial.id);
  const sharedUrl=base+'/guides/'+shared.source_id.slice(6);
  const before=await(await page.request.get(sharedUrl)).text();
  if(!before.includes('Traduction partielle')||!before.includes('Passage non traduit')||!before.includes('Consulter l’original')||before.includes('100 mg'))throw Error('Public gaps or rejected candidate incorrect');
  if(!before.includes('/pdf.html?id=guide%3Aquality-partial.en.pdf%23page%3D2'))throw Error('The gap does not link to its original PDF page');
  await page.locator('#chat-mode').evaluate(node=>{node.value='moyenne';node.dispatchEvent(new Event('change',{bubbles:true}));});
  await retry.click();
  await page.getByRole('button',{name:'Lire le document partagé',exact:true}).waitFor();
  const after=await(await page.request.get(sharedUrl)).text();
  if(!after.includes('pèse 10 mg')||after.includes('Passage non traduit'))throw Error('The original public link was not updated');
  const warning=await begin('guide:quality-short.en.txt');
  if(warning.status!=='completed'||warning.quality.warnings!==1)throw Error('Warning not retained');
  await page.getByText('À relire : anomalie possible.',{exact:true}).waitFor();
  const exportResult=await page.request.get(base+'/api/translations/'+warning.id+'/export');
  if(!(await exportResult.text()).includes('beaucoup plus courte'))throw Error('Export lost warning');
  const published=await page.evaluate(async id=>{
    const end=performance.now()+30000;
    while(performance.now()<end){const t=await(await fetch('/api/translations/'+id)).json();if(t.publication.source_id)return t.publication.source_id;await new Promise(r=>setTimeout(r,100));}
    throw Error('Warning publication timed out');
  },warning.id);
  const publicFile=await page.request.get(base+'/guides/'+published.slice(6));
  if(!(await publicFile.text()).includes('À relire'))throw Error('Shared copy lost warning');
  const gaps=await begin('guide:quality-gaps.en.txt');
  if(gaps.status!=='completed'||!gaps.parts[0].quality.issues.some(row=>row.code==='source_gaps'))throw Error('Missing source keys were not identified');
  const version=gaps.parts[0].quality.version;
  if(!Number.isInteger(version)||version<1)throw Error('The translation quality report is missing its version');
  await page.getByText('À relire : anomalie possible.',{exact:true}).waitFor();
  if(!(await page.locator('#translation-parts').textContent()).includes('touches dessinées'))throw Error('Source gaps warning not visible');
  return {badNumberBlocked:true,rejectedCandidateVisible:true,sourceComparison:true,warningInPrivateExportAndSharedDocument:true,mobileComposerAccessible:true,missingSourceKeysVisible:true,partialPublishedAndUpdated:true};
}
