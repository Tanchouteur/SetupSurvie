// Explicitly failed graphics driver, no real map data and no engine.
async page=>{
 const base='http://10.0.3.2:8769',checks=[],errors=[],writes=[];
 const check=(ok,name)=>{if(!ok)throw Error(name);checks.push(name);};
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(['POST','PUT','PATCH','DELETE'].includes(r.method()))writes.push(r.url());});
 await page.route('**/vendor/maps/maplibre-gl.js',r=>r.fulfill({contentType:'text/javascript',body:'window.maplibregl={addProtocol(){},Map:class{constructor(){throw Error("PRIVATE_DRIVER_DETAILS");}}};'}));
 await page.setViewportSize({width:1366,height:900});await page.goto(base+'/cartes.html?interface=nouveau');
 await page.locator('.map-renderer-fallback').waitFor({state:'visible'});
 check((await page.locator('.map-renderer-fallback').textContent()).includes('Les lieux et trajets enregistrés sont conservés'),'Panne graphique distincte de données perdues');
 check(!(await page.locator('body').textContent()).includes('PRIVATE_DRIVER_DETAILS'),'Détails techniques remplacés par une explication compréhensible');
 check(await page.locator('#home').isDisabled()&&await page.locator('#print').isDisabled(),'Commandes graphiques indisponibles désactivées');
 for(const width of [1366,390,320]){await page.setViewportSize({width,height:844});check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Message et retour sans débordement à '+width);}
 await page.getByRole('link',{name:'Revenir à la bibliothèque',exact:true}).click();await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.view==='library');
 check(true,'Sortie vers la bibliothèque sans dépendre du moteur de carte');
 check(!writes.length,'Aucune commande de téléchargement ou de modification des lieux');check(!errors.length,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length};
}
