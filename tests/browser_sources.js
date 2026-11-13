// Playwright MCP recipe against the tiny local fixture API only.
async (page) => {
  const base='http://10.0.3.2:8769';
  await page.unrouteAll({behavior:'wait'});
  await page.goto(base);
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.reload();await page.waitForFunction(()=>S.user?.id==='browser');
  await page.evaluate(()=>readSource('guide:shelter.en.txt'));
  await page.locator('#reader .source-dates').waitFor({state:'visible'});
  const date=await page.locator('#reader .source-dates').textContent();
  if(!date.includes('Document : 2010-05')||!date.includes('Collecte locale : 2026-11-12'))throw Error('Dates confondues '+date);
  await page.getByRole('button',{name:'Poser une question sur ce document',exact:true}).click();
  await page.locator('#chat-input').fill('Explique ce document et cite sa date.');await page.locator('#send-question').click();
  await page.locator('.source-chips').waitFor({state:'visible'});
  if(!(await page.locator('.source-chips').textContent()).includes('2010-05'))throw Error('Citation sans date');
  await page.reload();await page.waitForFunction(()=>S.conversation!==null);
  if(!(await page.locator('.source-chips').textContent()).includes('Deuxième édition'))throw Error('Métadonnées perdues après rechargement');
  await page.locator('.source-chips button').first().click();
  await page.locator('#reader .source-dates').waitFor({state:'visible'});
  await page.evaluate(()=>view('settings'));
  await page.waitForFunction(()=>document.getElementById('assistant-policy').textContent.includes('Je ne sais pas'));
  const form=page.locator('#upload-form');await form.locator('..').evaluate(e=>e.open=true);
  await form.locator('[name="title"]').fill('Notice fictive sans date');
  await form.locator('[name="file"]').setInputFiles({name:'notice.txt',mimeType:'text/plain',buffer:Buffer.from('Notice fictive. Trois compartiments.')});
  const edition='<img src=x onerror=alert(1)> '+'E'.repeat(240);
  await form.locator('[name="edition"]').fill(edition);
  await form.locator('[name="document_date"]').fill('2026-02-30');
  await form.locator('button[type=submit]').click();
  await page.waitForFunction(()=>document.getElementById('upload-status').textContent.includes('Date du document'));
  await form.locator('[name="document_date"]').fill('');await form.locator('button[type=submit]').click();
  await page.waitForFunction(()=>document.getElementById('upload-status').textContent.includes('Guide ajouté'));
  const results=await(await page.request.get(base+'/api/search?q=compartiments')).json();
  if(!results.results.length)throw Error('Document ajouté introuvable');
  await page.evaluate(id=>readSource(id),results.results[0].id);
  await page.locator('#reader .source-dates').waitFor({state:'visible'});
  if(!(await page.locator('#reader .source-dates').textContent()).includes('Date du document inconnue'))throw Error('Date inventée');
  if(await page.locator('#reader .source-dates img').count())throw Error('Métadonnées interprétées comme HTML');
  await page.evaluate(edition=>{view('chat');message('assistant','Ancienne citation [1].',[{id:'guide:shelter.en.txt',number:1,title:'Ancienne citation'}]);message('assistant','Citation longue [2].',[{id:'guide:shelter.en.txt',number:2,title:'Notice',edition}]);},edition);
  if(!(await page.locator('.source-chips').allTextContents()).some(t=>t.includes('Date du document inconnue')))throw Error('Ancien historique sans indication de date');
  const layouts=[];
  for(const width of [1366,768,390,320]){
    await page.setViewportSize({width,height:900});
    await page.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth);
    layouts.push({width,noHorizontalOverflow:true});
  }
  return {datedReader:true,datedSavedCitation:true,uploadDatesValidated:true,unknownDate:true,textOnlyMetadata:true,layouts};
}
