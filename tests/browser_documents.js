// UI, real PDF rendering and deliberately broken optional features; fixture only.
async (page) => {
  const base='http://10.0.3.2:8769';
  await page.unrouteAll({behavior:'wait'});
  await page.goto('about:blank');
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.request.delete(base+'/api/favorites?source_id='+encodeURIComponent('guide:shelter.en.pdf'),{headers:{Origin:base}});
  await page.goto(base);await page.waitForFunction(()=>S.user?.id==='browser');
  await page.evaluate(()=>search('Shelter'));
  const pdfResult=page.locator('.result[data-source="guide:shelter.en.pdf#page=6"]');
  await pdfResult.waitFor({state:'visible'});
  await pdfResult.locator('.favorite-toggle').click();
  await page.waitForFunction(()=>document.querySelector('.result[data-source="guide:shelter.en.pdf#page=6"] .favorite-toggle').getAttribute('aria-pressed')==='true');
  await page.locator('[data-library-scope=favorites]').click();
  await page.locator('#library-query').fill('calibration');await page.locator('#library-search').evaluate(f=>f.requestSubmit());
  await page.waitForFunction(()=>[...document.querySelectorAll('.result')].some(n=>n.dataset.source==='guide:shelter.en.pdf#page=6'));
  await page.reload();await page.waitForFunction(()=>S.user?.id==='browser');
  const saved=await(await page.request.get(base+'/api/favorites')).json();
  if(!saved.results.some(r=>r.id==='guide:shelter.en.pdf'))throw Error('Favorite lost after reload');

  const created=await page.request.post(base+'/api/translations',{data:{source_id:'guide:shelter.en.pdf',mode:'rapide',first_page:6,last_page:6},headers:{Origin:base}});
  if(!created.ok())throw Error(await created.text());
  const item=await created.json();
  const translated=await page.evaluate(async id=>{
    const deadline=performance.now()+30000;
    while(performance.now()<deadline){const r=await fetch('/api/translations/'+id);const t=await r.json();if(t.publication?.source_id)return t;await new Promise(resolve=>setTimeout(resolve,100));}
    throw Error('Translation publication timed out');
  },item.id);
  const shared=translated.publication.source_id;
  await page.evaluate(()=>view('library'));await page.locator('[data-library-scope=translations]').click();
  await page.locator('#library-query').fill('');await page.locator('#library-search').evaluate(f=>f.requestSubmit());
  await page.waitForFunction(id=>[...document.querySelectorAll('.result')].some(n=>n.dataset.source===id),shared);
  await page.locator('.result').filter({hasText:'Traduction IA'}).first().locator('.favorite-toggle').click();
  const deleted=await page.request.delete(base+'/api/conversations/'+item.conversation_id,{headers:{Origin:base}});
  if(!deleted.ok())throw Error('Published document blocked conversation deletion: '+await deleted.text());
  const retained=await page.request.get(base+'/api/source?id='+encodeURIComponent(shared));
  if(!retained.ok()||!(await retained.json()).is_ai_translation)throw Error('Published translation lost with conversation');

  // A new page exercises the actual renderer, not a mocked canvas or API.
  const pdf=await page.context().newPage();const pdfErrors=[];pdf.on('pageerror',error=>pdfErrors.push(String(error)));
  const external=[];pdf.on('request',request=>{if(!request.url().startsWith(base)&&!request.url().startsWith('blob:')&&!request.url().startsWith('data:'))external.push(request.url());});
  await pdf.goto(base+'/pdf.html?id='+encodeURIComponent('guide:shelter.en.pdf#page=3'));
  await pdf.waitForFunction(()=>document.querySelectorAll('canvas').length>0&&document.querySelector('#pdf-page').value==='3');
  await pdf.locator('#pdf-next').click();await pdf.waitForFunction(()=>document.querySelector('#pdf-page').value==='4');
  const layouts=[];
  for(const [width,height] of [[1366,900],[390,844],[320,568]]){
    await pdf.setViewportSize({width,height});
    await pdf.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth&&document.querySelector('#pdf-container').getBoundingClientRect().height>100);
    layouts.push({width,height});
  }
  await pdf.locator('#pdf-query').fill('Shelter');await pdf.locator('#pdf-find').click();
  await pdf.waitForFunction(()=>document.querySelector('#pdf-status').textContent.includes('résultat'));
  await pdf.route('**/api/**',route=>route.fulfill({status:503,contentType:'application/json',body:'{"detail":"fixture API unavailable"}'}));
  await pdf.reload();await pdf.waitForFunction(()=>document.querySelectorAll('canvas').length>0);
  await pdf.route('**/vendor/pdfjs/pdf.mjs',route=>route.fulfill({status:503,body:'fixture renderer unavailable'}));
  await pdf.reload();await pdf.waitForFunction(()=>document.querySelector('#pdf-status').textContent.includes('ne peut pas afficher'));
  const original=await pdf.locator('#pdf-emergency').getAttribute('href');
  if(!(await pdf.request.get(base+original)).ok())throw Error('Static original inaccessible after optional failures');
  await pdf.goto(base+'/secours.html');await pdf.waitForFunction(()=>document.querySelectorAll('#emergency-documents a').length>0);
  if(pdfErrors.length)throw Error(pdfErrors.join('\n'));if(external.length)throw Error('Remote PDF assets: '+external.join(','));
  await pdf.close();

  // A JavaScript error in the optional module must leave the old search alive.
  const fallback=await page.context().newPage();const expected=[];fallback.on('pageerror',error=>expected.push(String(error)));
  await fallback.route('**/documents.js*',route=>route.fulfill({contentType:'text/javascript',body:'throw new Error("fixture optional module failure");'}));
  await fallback.goto(base+'/index.html#library');await fallback.locator('#library-query').fill('Shelter');await fallback.locator('#library-search').evaluate(f=>f.requestSubmit());
  await fallback.waitForFunction(()=>document.querySelectorAll('.result').length>0);
  if(!expected.some(e=>e.includes('fixture optional module failure'))||expected.some(e=>!e.includes('fixture optional module failure')))throw Error('Core failure after optional module crash: '+expected.join('\n'));
  await fallback.close();
  return {favoritesPersisted:true,fullPageFavoriteSearch:true,publishedAndRetained:true,pdfRendered:true,worksWithoutPilot:true,originalFallback:true,optionalModuleIsolation:true,layouts};
}
