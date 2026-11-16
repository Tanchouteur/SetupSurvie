// Actual 40-page PDF extraction and resumable queue; model output is simulated.
async page=>{
  const base='http://10.0.3.2:8769',checks=[],commands=[],errors=[],headers={Origin:base};let memoryRequests=0;
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',r=>{if(r.method()==='POST'&&r.url().includes('/admin/translation-benchmark/'))commands.push(r.url().split('/').pop());});
  page.on('request',r=>{if(new URL(r.url()).pathname==='/api/admin/assistant/calibration')memoryRequests++;});
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers});
  await page.goto(base+'/#/appareil/reglages');await page.waitForFunction(()=>S.authReady&&S.user);
  await page.locator('#settings-reglages a[href="#/appareil/tests"]').click();await page.waitForURL('**/#/appareil/tests');
  check(await page.locator('#settings-tests').isVisible(),'Tests et diagnostics accessible depuis les paramètres');
  check(await page.locator('#settings-tests > details').count()===5,'Cinq tests rangés dans des rubriques dépliables');
  check(commands.length===0,'Ouvrir les tests ne lance aucune traduction');
  await page.goto(base+'/#/appareil/tests?test=translation');await page.waitForFunction(()=>document.getElementById('next-translation-benchmark-mode').options.length>0);
  check(await page.locator('#settings-test-translation').evaluate(d=>d.open),'Le lien direct ouvre le test demandé');
  await page.locator('#next-translation-benchmark-start').click();await page.locator('#next-translation-benchmark-pause').waitFor({state:'visible'});
  check(await page.locator('#next-translation-benchmark-start').isDisabled(),'Double lancement désactivé');
  await page.waitForFunction(()=>document.getElementById('next-translation-benchmark-result').textContent.includes('PDF préparé'));
  await page.waitForTimeout(900);await page.locator('#next-translation-benchmark-pause').click();
  await page.locator('#next-translation-benchmark-resume').waitFor({state:'visible'});
  const paused=await(await page.request.get(base+'/api/admin/translation-benchmark/report')).json();
  check(paused.status==='paused'&&paused.parts_done>0&&paused.parts_done<40,'Pause conserve les passages terminés et les mesures');
  await page.reload();await page.waitForFunction(()=>S.authReady&&S.user);await page.locator('#next-translation-benchmark-resume').waitFor({state:'visible'});
  check(commands.filter(name=>name==='start').length===1,'Rechargement sans relancement du test');
  await page.locator('#next-translation-benchmark-resume').click();
  await page.waitForFunction(()=>document.getElementById('next-translation-benchmark-status').textContent.includes('40 pages sont traduites'),null,{timeout:45000});
  check((await page.locator('#next-translation-benchmark-result').textContent()).includes('40 / 40'),'Quarante pages terminées affichées');
  check((await page.locator('#next-translation-benchmark-result').textContent()).includes('9 600')||(await page.locator('#next-translation-benchmark-result').textContent()).includes('9 600'),'Volume réel du PDF affiché');
  const downloadEvent=page.waitForEvent('download');await page.locator('#next-translation-benchmark-export').click();
  const download=await downloadEvent,chunks=[];for await(const chunk of await download.createReadStream())chunks.push(chunk);const report=JSON.parse(Buffer.concat(chunks).toString());
  check(report.pages_done===40&&report.page_timings.length===40&&report.sessions.length===2,'Rapport par page et deux sessions de travail');
  check(report.parts.some(row=>row.metrics?.runtime_after?.running?.context_length===16384),'Contexte observé inclus dans le rapport');
  check(report.samples.length>0&&report.fixture.source_words===9600,'Échantillons matériels et volume source conservés');
  check(!JSON.stringify(report).includes('The narrator')&&!('translated' in report),'Aucun texte de traduction dans le rapport numérique');
  check(memoryRequests===0,'La rubrique traduction ne consulte pas un essai mémoire replié');
  await page.goto(base+'/#/appareil/tests?test=memory');check(await page.locator('#next-calibration-form').isVisible(),'Essai mémoire dans le même sous-menu');
  await page.goBack();await page.waitForURL('**/#/appareil/tests?test=translation');check(await page.locator('#settings-test-translation').isVisible(),'Retour navigateur retrouve le test de traduction');
  for(const width of [1366,390,320]){await page.setViewportSize({width,height:900});check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Test lisible à '+width);}
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks,real_inference:false};
}
