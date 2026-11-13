// Read-only catalogue and tiny fixture documents; preparing a question never runs a model.
async(page)=>{
  const base='http://10.0.3.2:8769';
  await page.unrouteAll({behavior:'wait'});await page.goto(base+'/#library');
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.reload();await page.waitForFunction(()=>S.user?.id==='browser');
  await page.evaluate(()=>view('library'));
  await page.locator('#learning-browser').evaluate(e=>e.open=true);
  await page.waitForFunction(()=>document.querySelectorAll('#learning-domain option').length===14);
  const domains=await page.locator('#learning-domain option').evaluateAll(items=>items.map(e=>e.value));
  if(!domains.includes('sciences')||!domains.includes('organisation'))throw Error('Parcours manquants');
  await page.locator('#learning-domain').selectOption('textile');
  await page.locator('#learning-search').click();
  await page.waitForFunction(()=>document.querySelector('#search-results')?.textContent.includes('Sewing'));
  if(await page.locator('#library-query').inputValue()!=='couture')throw Error('Recherche du sujet incorrecte');
  const questions=[];const listener=request=>{if(request.url().endsWith('/api/questions'))questions.push(request.url());};page.on('request',listener);
  await page.locator('#learning-level').selectOption('local');await page.locator('#learning-ask').click();
  await page.locator('#chat-input').waitFor({state:'visible'});
  const prompt=await page.locator('#chat-input').inputValue();
  if(!prompt.includes('consommables industriels')||!prompt.includes('Couture')||!prompt.includes('sources et leurs dates')||!prompt.includes('exercices'))throw Error('Question pédagogique incomplète');
  if(questions.length)throw Error('Question envoyée sans validation');page.off('request',listener);
  await page.evaluate(()=>view('library'));
  const layouts=[];
  for(const width of [1366,768,390,320]){
    await page.setViewportSize({width,height:900});
    for(const domain of ['sciences','sante','organisation','histoire-techniques']){
      await page.locator('#learning-domain').selectOption(domain);
      try{
        await page.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth);
      }catch(error){
        const measure=await page.evaluate(()=>({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,body:document.body.scrollWidth,
          overflow:[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth&&!e.closest('[hidden]')).slice(0,12)
            .map(e=>({tag:e.tagName,id:e.id,class:e.className,width:e.getBoundingClientRect().width,right:e.getBoundingClientRect().right}))}));
        throw Error('Overflow '+width+' '+domain+' '+JSON.stringify(measure));
      }
      if(await page.locator('#learning-subject option').count()<4)throw Error('Sujets manquants '+domain);
    }
    layouts.push({width,scrollWidth:await page.evaluate(()=>document.documentElement.scrollWidth),noHorizontalOverflow:true});
  }
  await page.route('**/api/library/learning',route=>route.fulfill({status:503,contentType:'application/json',body:'{"detail":"fixture unavailable"}'}));
  await page.reload();await page.evaluate(()=>view('library'));
  await page.waitForFunction(()=>document.getElementById('learning-notice').textContent.includes('pas disponibles'));
  if(!await page.locator('#library-query').isEnabled())throw Error('Recherche bloquée par les parcours');
  await page.unroute('**/api/library/learning');
  await page.evaluate(()=>view('data'));
  await page.locator('#content-manager').evaluate(e=>e.open=true);
  await page.waitForFunction(()=>document.querySelectorAll('#content-themes input').length===38);
  await page.locator('#content-learning').waitFor({state:'visible'});await page.locator('#content-learning').evaluate(e=>e.open=true);
  if(!(await page.locator('#content-learning-list').textContent()).includes('Algèbre'))throw Error('Besoins à examiner absents');
  return {domains:domains.length,themes:38,bilingualSearch:true,questionPreparedWithoutInference:true,missingCatalogueFallback:true,reviewGrid:true,layouts};
}
