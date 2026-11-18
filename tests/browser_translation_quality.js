// Fixture only: numbers are deliberately altered by the fake inference server.
async page => {
  const base='http://10.0.3.2:8769';
  await page.unrouteAll({behavior:'wait'});await page.goto('about:blank');
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.goto(base);await page.waitForFunction(()=>S.user?.id==='browser');
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
  if(bad.status!=='error'||bad.done!==0||bad.parts[0].candidate.indexOf('100 mg')<0||bad.publication.source_id)throw Error('Bad number accepted');
  await page.getByText('Passage refusé par les contrôles.',{exact:true}).waitFor();
  const source=page.locator('.translation-comparison');await source.locator('summary').click();
  if(!(await source.locator('pre').innerText()).includes('10 mg'))throw Error('Original text missing');
  await page.getByText('Voir la proposition refusée · ne pas utiliser',{exact:true}).click();
  await page.getByText('Utilisez 100 mg. Ne dépassez pas la limite.',{exact:true}).waitFor();
  for(const [width,height] of [[1366,900],[390,844],[320,568]]){
    await page.setViewportSize({width,height});await page.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth&&document.getElementById('send-question').getBoundingClientRect().bottom<=innerHeight);
  }
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
  if(gaps.parts[0].quality.version!==6)throw Error('The translation quality report has an unexpected version');
  await page.getByText('À relire : anomalie possible.',{exact:true}).waitFor();
  if(!(await page.locator('#translation-parts').textContent()).includes('touches dessinées'))throw Error('Source gaps warning not visible');
  return {badNumberBlocked:true,rejectedCandidateVisible:true,sourceComparison:true,warningInPrivateExportAndSharedDocument:true,mobileComposerAccessible:true,missingSourceKeysVisible:true};
}
