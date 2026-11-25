// Espace disque : carte de la vue d'ensemble et analyse détaillée, sur une analyse simulée.
async page=>{
 let stage='carte';
 try{
 const base='http://10.0.3.2:8769',checks=[],errors=[];
 const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
 page.on('pageerror',error=>errors.push(error.message));
 await page.request.post(base+'/api/profiles/select',{data:{id:'local-family'},headers:{Origin:base}});
 await page.setViewportSize({width:1440,height:1000});
 await page.goto(base+'/#/appareil/ensemble');await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.user);
 const card=page.locator('#storage-summary');
 await card.locator('.storage-disk').first().waitFor();
 const text=await card.innerText();
 check(text.includes('Espace disque')&&text.includes('SetupSurvie occupe 820 Go')&&/1\s020 Go libres/.test(text),'Phrase d’état avant les mesures : '+text.split('\n').slice(0,3).join(' / '));
 const parts=await card.locator('.storage-segment').evaluateAll(nodes=>nodes.map(n=>n.dataset.part));
 check(parts.join(',')==='survie,backups,other','Segments SetupSurvie, copies de sécurité et autres fichiers');
 const legend=await card.locator('.storage-legend li').allInnerTexts();
 check(legend.some(t=>t.includes('Autres fichiers du PC')&&t.includes('30 Go'))&&legend.some(t=>t.startsWith('Libre')),'Légende chiffrée, autres fichiers = utilisé − SetupSurvie − copies');
 const layout=await page.evaluate(()=>{const c=document.getElementById('storage-summary').getBoundingClientRect(),v=document.getElementById('view-monitor').getBoundingClientRect(),m=document.getElementById('settings-server-metrics');return {full:c.width>v.width*0.9,after:m.compareDocumentPosition(document.getElementById('storage-summary'))&Node.DOCUMENT_POSITION_FOLLOWING};});
 check(layout.full&&layout.after,'Carte pleine largeur, placée après la mémoire');
 stage='ouverture';
 await card.click();
 await page.waitForFunction(()=>location.hash==='#/appareil/stockage');
 const analysis=page.locator('#storage-analysis');
 await analysis.locator('.storage-category').first().waitFor();
 check(await analysis.locator('.storage-category').count()===4,'Une ligne par catégorie');
 check((await analysis.locator('.storage-category').first().innerText()).includes('Bibliothèque'),'Catégories triées par taille');
 check((await analysis.innerText()).includes('Dernière analyse il y a 2 h'),'Date de la dernière analyse');
 check(await page.locator('#storage-analysis button',{hasText:'Analyser à nouveau'}).isVisible(),'Famille peut relancer l’analyse');
 await analysis.locator('.storage-category > summary').first().click();
 await analysis.locator('.storage-item > summary').first().click();
 const detail=await analysis.locator('.storage-item').first().innerText();
 check(detail.includes('khanacademy_fr_fixture.zim')&&detail.includes('183 fichiers'),'Plus gros fichiers d’un élément');
 check((await analysis.innerText()).includes('reconstructible'),'Les index reconstructibles sont signalés');
 stage='téléphone';
 for(const width of [320,390,760]){
   await page.setViewportSize({width,height:900});
   check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Analyse sans débordement à '+width);
   const target=await analysis.locator('.storage-category > summary').first().evaluate(n=>n.getBoundingClientRect().height);
   check(target>=40,'Cible tactile des catégories à '+width+' : '+target);
 }
 await page.goto(base+'/#/appareil/ensemble');await card.locator('.storage-disk').first().waitFor();
 check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Carte sans débordement sur téléphone');
 check(!errors.length,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks};
 }catch(error){throw Error(stage+' : '+error.message);}
}
