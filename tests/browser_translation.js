// Playwright MCP recipe, paired with browser_translation_server.py only.
async (page) => {
  const base='http://10.0.3.2:8769';
  const documents=async()=>{const pane=page.locator('#assistant-documents');if(await pane.count()&&!await pane.isVisible())await page.locator('[data-assistant-zone=documents]').click();};
  await page.unrouteAll({behavior:'wait'});
  await page.goto('about:blank');
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  const result=await page.request.post(base+'/api/questions',{data:{message:'Explique ce document',source_id:'guide:shelter.en.txt'},headers:{Origin:base}});
  if(!result.ok())throw Error(await result.text());
  const item=await result.json();
  await page.goto(base);await page.waitForFunction(()=>S.user?.id==='browser');
  await page.evaluate(id=>openConversation(id),item.conversation_id);
  await page.locator('#chat-source').waitFor({state:'visible'});
  await page.reload();await page.waitForFunction(()=>S.conversation!==null);
  if(await page.locator('#chat-source').isHidden())throw Error('Association perdue');
  await page.locator('#chat-input').fill('traduit moi ce guide en francais');await page.locator('#send-question').click();
  await page.waitForFunction(()=>Number(document.querySelector('#translation-progress').value)>=1);
  await page.locator('#translation-pause').click();await page.locator('#translation-resume').waitFor({state:'visible'});
  const id=await page.evaluate(()=>S.translation);
  const before=await(await page.request.get(base+'/api/translations/'+id)).json();
  const layouts=[];
  for(const [width,height] of [[1366,900],[768,900],[390,844],[320,568]]){
    await page.setViewportSize({width,height});
    await page.locator('#send-question').waitFor({state:'visible'});
    try{await page.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth&&document.getElementById('send-question').getBoundingClientRect().bottom<=innerHeight);}
    catch(error){throw Error('Disposition incorrecte '+width+'x'+height+' '+JSON.stringify(await page.evaluate(()=>({width:innerWidth,height:innerHeight,scroll:document.documentElement.scrollWidth,send:document.getElementById('send-question').getBoundingClientRect().toJSON(),chat:document.getElementById('view-chat').getBoundingClientRect().toJSON(),viewport:visualViewport?.height}))));}
    const valid=await page.evaluate(()=>({horizontal:document.documentElement.scrollWidth<=innerWidth,composer:document.getElementById('send-question').getBoundingClientRect().bottom<=innerHeight}));
    if(!valid.horizontal||!valid.composer)throw Error('Disposition incorrecte '+width+'x'+height);
    await page.locator('#assistant-discussion #translation-resume').waitFor({state:'visible'});
    layouts.push({width,height,...valid});
  }
  await page.reload();await page.waitForFunction(()=>S.translation!==null);
  await page.locator('#translation-panel').evaluate(e=>e.open=true);
  await page.locator('#chat-mode').selectOption('moyenne');await page.locator('#translation-resume').click();
  await page.waitForFunction(done=>Number(document.querySelector('#translation-progress').value)>done,before.done);
  await page.locator('#translation-pause').click();await page.locator('#translation-resume').waitFor({state:'visible'});
  const after=await(await page.request.get(base+'/api/translations/'+id)).json();
  if(after.parts[0].translated!==before.parts[0].translated)throw Error('Passage terminé modifié');
  const output=await(await page.request.get(base+'/api/translations/'+id+'/export')).text();
  if(!output.includes('Construction d’un abri'))throw Error('Export sans texte français');
  await documents();await page.locator('#chat-source button').filter({hasText:'Retirer'}).click();
  await page.reload();await page.waitForFunction(()=>S.conversation!==null);
  await documents();
  if(!await page.locator('#chat-source').isHidden())throw Error('Retrait non conservé');
  await page.locator('[data-close-panel=documents]').click();
  await page.locator('#chat-messages #translation-parts .translation-text').first().waitFor();
  await page.evaluate(()=>readSource('guide:shelter.en.pdf'));
  await page.getByRole('button',{name:'Poser une question sur ce document',exact:true}).click();
  await page.locator('#translation-panel').evaluate(e=>e.open=true);
  await page.locator('#translation-first').fill('3');await page.locator('#translation-first').press('Tab');
  await page.locator('#translation-last').fill('5');await page.locator('#translation-last').press('Tab');
  if(await page.locator('#translation-first').inputValue()!=='3'||await page.locator('#translation-last').inputValue()!=='5')throw Error('Plage PDF modifiée avant envoi');
  const created=page.waitForResponse(response=>response.url()===base+'/api/translations'&&response.request().method()==='POST');
  await page.locator('#translation-start').click();
  const response=await created;if(!response.ok())throw Error('Création PDF refusée : '+response.status());
  const requested=await response.json();
  const range=response.request().postDataJSON();
  if(range.first_page!==3||range.last_page!==5)throw Error('Plage PDF envoyée incorrecte : '+JSON.stringify(range));
  await page.waitForFunction(id=>S.translation===id&&Number(document.querySelector('#translation-progress').value)>=1,requested.id);
  await page.locator('#translation-pause').click();await page.locator('#translation-resume').waitFor({state:'visible'});
  const pdfID=await page.evaluate(()=>S.translation);
  const pdf=await(await page.request.get(base+'/api/translations/'+pdfID)).json();
  if(pdf.pages!==3||pdf.parts.some(p=>p.page<3||p.page>5))throw Error('Plage PDF incorrecte : '+JSON.stringify({expected:requested.id,id:pdfID,source:pdf.source_id,pages:pdf.pages,partPages:pdf.parts.map(p=>p.page)}));
  return {associationRestored:true,pauseResumeReload:true,exported:true,chatTranslationRouted:true,before:before.done,after:after.done,pdfPages:pdf.pages,layouts};
}
