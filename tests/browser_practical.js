// Human reading references on tiny files, no model or real practical instructions.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],errors=[],inferences=[],searches=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));page.on('request',r=>{if(/\/api\/(questions|admin\/inference)/.test(r.url()))inferences.push(r.url());if(r.url().includes('/api/library/dossiers/')&&r.url().endsWith('/search'))searches.push(r.url());});
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.setViewportSize({width:1366,height:900});await page.goto(base+'/#/bibliotheque/parcours?dossier=generateur-pedales');
  await page.waitForFunction(()=>document.querySelector('#next-practical-detail h2')?.textContent.includes('générateur'));
  check(await page.locator('.practical-card').count()===6,'Six objectifs pratiques visibles');
  check(searches.length===0,'Ouvrir un dossier ne lance pas de recherche lourde');
  check(await page.locator('.practical-gap').count()===6,'Points sans référence explicitement à examiner');
  await page.locator('.practical-card').filter({hasText:'Préparer un projet d’abri'}).click();await page.waitForFunction(()=>document.querySelector('#next-practical-detail h2')?.textContent.includes('abri'));
  await page.goBack();await page.waitForFunction(()=>document.querySelector('#next-practical-detail h2')?.textContent.includes('générateur'));await page.goForward();await page.waitForFunction(()=>document.querySelector('#next-practical-detail h2')?.textContent.includes('abri'));
  check(page.url().includes('dossier=abri'),'Précédent et Suivant conservent le dossier');
  await page.locator('#next-practical-detail').getByRole('button',{name:'Chercher des sources pour ce dossier',exact:true}).click();await page.locator('.practical-result').first().waitFor();
  check((await page.locator('.practical-found').textContent()).includes('à ouvrir et examiner'),'Résultats proposés distincts des repères examinés');
  const target=page.locator('.practical-result a').filter({hasText:'Shelter fixture'}).first();await target.click();await page.locator('.practical-editor').waitFor();await page.locator('.practical-editor > summary').click();
  const form=page.locator('.practical-editor form');await page.waitForFunction(()=>document.querySelector('.practical-editor button')?.disabled===false);
  check(await form.locator('[name="dossier"]').inputValue()==='abri','Lecteur conserve le dossier d’origine');
  await form.locator('[name="section"][value="steps"]').check();await form.locator('[name="section"][value="materials"]').check();await form.locator('[name="locator"]').fill('Section fixture');await form.locator('[name="note"]').fill('Ce document fictif mentionne des dimensions et avertissements, sans validation pratique.');await form.locator('[name="reviewed"]').check();
  await form.getByRole('button',{name:'Enregistrer le repère',exact:true}).click();await form.getByRole('link',{name:'Ouvrir le dossier →',exact:true}).waitFor();await form.getByRole('link',{name:'Ouvrir le dossier →',exact:true}).click();
  await page.waitForFunction(()=>document.querySelectorAll('.practical-reference').length===2);
  check(await page.locator('.practical-gap').count()===4,'Seuls les points examinés reçoivent une référence');
  check((await page.locator('#next-practical-detail').textContent()).includes('2010-05'),'Page, repère et date du document conservés');
  await page.reload();await page.waitForFunction(()=>document.querySelectorAll('.practical-reference').length===2);
  check(page.url().includes('dossier=abri'),'Dossier et références retrouvés au rechargement');
  for(const width of [1366,390,320]){await page.setViewportSize({width,height:844});check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Dossier lisible sans débordement à '+width);}
  await page.locator('#next-practical-choice').selectOption('velo');await page.waitForFunction(()=>document.querySelector('#next-practical-detail h2')?.textContent.includes('crevaison'));await page.locator('#next-practical-choice').selectOption('abri');await page.waitForFunction(()=>document.querySelectorAll('.practical-reference').length===2);
  check(page.url().includes('dossier=abri'),'Sélecteur mobile compact conserve le dossier dans l’adresse');
  await page.setViewportSize({width:1366,height:900});await page.locator('#next-practical-detail').getByRole('button',{name:'Préparer une question à l’assistant',exact:true}).click();await page.locator('#chat-input').waitFor({state:'visible'});
  check((await page.locator('#chat-input').inputValue()).includes('sources locales')&&(await page.locator('#chat-input').inputValue()).includes('exercice de compréhension'),'Question pédagogique préparée avec sources et limites');
  check(inferences.length===0,'Aucune inférence lancée par la préparation ou la consultation');
  await page.goto(base+'/#/appareil/entretien');await page.waitForFunction(()=>S.authReady&&S.user);if(!await page.locator('#settings-exports').evaluate(node=>node.open))await page.locator('#settings-exports > summary').click();const pending=page.waitForEvent('download');await page.getByRole('button',{name:'Exporter les dossiers',exact:true}).click();const file=await pending,parts=[];for await(const c of await file.createReadStream())parts.push(c);const data=JSON.parse(Buffer.concat(parts).toString());
  check(data.dossiers.find(d=>d.id==='abri').reviewed_sections===2&&!('conversations' in data),'Export des repères et lacunes, sans conversation');
  await page.goto(base+'/#/bibliotheque/parcours?dossier=abri');await page.waitForFunction(()=>document.querySelectorAll('.practical-reference').length===2);await page.locator('.practical-reference').first().getByRole('button',{name:'Retirer ce repère du dossier',exact:true}).click();await page.waitForFunction(()=>document.querySelectorAll('.practical-gap').length===6);
  check((await page.request.get(base+'/api/source?id=guide%3Ashelter.en.txt')).ok(),'Retirer un repère conserve le document original');
  const delayedData=await(await page.request.get(base+'/api/library/dossiers/abri')).json();
  await page.goto(base+'/#/bibliotheque/recherche?domain=all&dossier=abri&source=guide%3Ashelter.en.txt');await page.locator('.practical-editor').waitFor();
  await page.route('**/api/library/dossiers/abri',async r=>{await new Promise(resolve=>setTimeout(resolve,300));await r.fulfill({json:delayedData}).catch(()=>{});});
  const delayed=page.waitForRequest(r=>r.url().endsWith('/api/library/dossiers/abri'));await page.locator('.practical-editor > summary').click();await delayed;await page.reload();await page.locator('.practical-editor').waitFor();await page.waitForTimeout(400);
  check(!await page.locator('.practical-editor').evaluate(e=>e.open),'Rechargement pendant la lecture des repères sans requête tardive');await page.unroute('**/api/library/dossiers/abri');
  await page.goto(base+'/#/bibliotheque/parcours?dossier=abri');await page.waitForFunction(()=>document.querySelector('.practical-gap'));
  await page.route('**/api/library/dossiers',r=>r.fulfill({status:503,json:{detail:'Dossiers indisponibles pour cette recette.'}}));await page.reload();await page.waitForFunction(()=>document.querySelector('#next-practical-detail')?.textContent.includes('indisponibles'));
  await page.locator('.next-tabs [data-route="bibliotheque/recherche"]').click();check(await page.locator('#library-query').isEnabled(),'Module de dossiers indisponible sans bloquer la recherche');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks};
}
