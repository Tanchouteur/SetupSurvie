// Playwright MCP recipe; serve portal/ on the fixture address before running.
// All route responses and map APIs below are synthetic and local.
async (page) => {
  const base='http://10.0.3.2:8766',errors=[],external=[],calls=[];
  let role='admin',failCalculation=false,delayCalculation=false,index=0;
  const book={lists:[],points:[],routes:[]},saved=new Map(),drafts=new Map();
  const id=()=>String(++index).padStart(32,'0');
  await page.unroute('**/*');await page.unroute('**/api/**');
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',async route=>{
    const req=route.request(),url=new URL(req.url()),path=url.pathname;
    if(url.origin!==base){external.push(req.url());return route.abort();}
    if(!path.startsWith('/api/'))return route.continue();
    calls.push(path);let data={},status=200;
    if(path==='/api/maps')data={maps:[]};
    else if(path==='/api/profiles/current')data={id:'browser',name:'Test',role};
    else if(path==='/api/settings')data={home:null,departure:null};
    else if(path==='/api/geography/status')data={datasets:[]};
    else if(path==='/api/geography/elevation')data={elevation_m:null};
    else if(path==='/api/map-notebook')data=book;
    else if(path==='/api/routing')data={prepared:true,note:'Réseau de test préparé',coverage:{created:'2026-11-12'}};
    else if(path==='/api/admin/map-notebook/lists'&&req.method()==='POST'){
      data={id:id(),title:req.postDataJSON().title};book.lists.push(data);
    }else if(path.startsWith('/api/admin/map-notebook/lists/')&&req.method()==='DELETE'){
      data={detail:'Cette liste contient des points ou trajets.'};status=409;
    }else if(path==='/api/admin/map-notebook/points'&&req.method()==='POST'){
      data={id:id(),...req.postDataJSON()};book.points.push(data);
    }else if(path==='/api/admin/map-notebook/calculate'){
      if(delayCalculation)await new Promise(resolve=>setTimeout(resolve,500));
      if(failCalculation){status=422;data={detail:'Aucun trajet dans cette zone.'};}
      else{const body=req.postDataJSON(),draft_id=id();data={...body,draft_id,distance_m:8000,duration_s:Math.round(8000/body.speed_kmh*3.6),geometry:{type:'LineString',coordinates:body.points.map(p=>[p.lon,p.lat])},segments:[{name:'Chemin fictif',distance_m:8000}],note:'Trajet fictif de test. Sans GPS.'};drafts.set(draft_id,data);}
    }else if(path==='/api/admin/map-notebook/routes'){
      const body=req.postDataJSON(),source=drafts.get(body.draft_id);data={id:id()};saved.set(data.id,{...source,...body,...data});book.routes.push({...source,...body,...data});
    }else if(path.startsWith('/api/map-notebook/routes/'))data=saved.get(path.split('/').pop());
    await route.fulfill({status,json:data});
  });
  await page.setViewportSize({width:1366,height:950});
  await page.goto(base+'/cartes.html');
  await page.waitForFunction(()=>window.SurvieMap&&document.querySelector('#planning-panel').hidden===false);
  await page.locator('[data-panel=map-notebook]').click();
  await page.locator('#new-map-list').click();await page.locator('#map-list-title').fill('Eau et lieux de repli');await page.locator('#map-list-form button[type=submit]').click();
  await page.waitForFunction(()=>document.querySelector('#new-map-point').disabled===false);
  for(const [title,lat,lon] of [['Départ familial',43.1,6.1],['Point d’eau à vérifier',43.11,6.11]]){
    await page.locator('#begin-map-point').click();
    await page.evaluate(p=>window.SurvieMap.selectPoint(p),{lat,lon});
await page.locator('#point-title').fill(title);await page.locator('#point-kind').selectOption('water');await page.locator('#point-notes').fill('Repère fictif. Vérifier l’accès avant utilisation.');await page.locator('#map-point-form button[type=submit]').click();
    await page.waitForFunction(count=>document.querySelectorAll('#route-stops select option').length>=count,book.points.length*2+2);
  }
  await page.locator('[data-panel=planning-panel]').click();
  await page.locator('#route-stops select').nth(0).selectOption(book.points[0].id);await page.locator('#route-stops select').nth(1).selectOption(book.points[1].id);
  if(await page.locator('#route-speed').inputValue()!=='4')throw new Error('La marche doit être proposée à 4 km/h.');
  await page.locator('#route-calculate').click();await page.locator('#route-save-form').waitFor({state:'visible'});
  if(!(await page.locator('#selected-route-distance').innerText()).includes('8 km'))throw new Error('Kilomètres manquants.');
  if(!(await page.locator('#selected-route-duration').innerText()).includes('2 h 00'))throw new Error('Durée incorrecte à 4 km/h.');
  await page.locator('#route-title').fill('Vers le point d’eau');await page.locator('#route-save-form button').click();
  await page.waitForFunction(()=>document.querySelector('#selected-route-title').textContent==='Vers le point d’eau');
  await page.locator('#route-mode').selectOption('motorcycle');
  if(await page.locator('#route-speed').inputValue()!=='40')throw new Error('Vitesse moto non réglable.');
  failCalculation=true;await page.locator('#route-calculate').click();await page.waitForFunction(()=>document.querySelector('#planning-message').textContent.includes('Aucun trajet'));
  if(await page.locator('#route-save-form').isVisible())throw new Error('Un échec a laissé un trajet enregistrable.');
  failCalculation=false;delayCalculation=true;
  await page.locator('#route-calculate').click();await page.locator('#route-mode').selectOption('car');
  await page.waitForFunction(()=>document.querySelector('#route-calculate').disabled===false);
  if(await page.locator('#route-save-form').isVisible())throw new Error('Une réponse périmée a été affichée.');
  role='user';calls.length=0;await page.waitForLoadState('networkidle');await page.reload();
  await page.waitForFunction(()=>document.querySelector('#notebook-list').options.length===1);
  const layouts=[];
  for(const [width,height] of [[1366,900],[768,900],[390,844],[375,667],[320,568],[844,390]]){
    await page.setViewportSize({width,height});
    if(width<=760)await page.locator('#open-map-panel').click();
    await page.locator('[data-panel=map-notebook]').click();
    await page.getByRole('button',{name:'Vers le point d’eau',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('#selected-route-title').textContent==='Vers le point d’eau');
    if(await page.locator('#planning-panel').isVisible())throw new Error('Édition visible chez un lecteur.');
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw new Error('Débordement '+width);
    if(await page.locator('#map').evaluate(el=>el.getBoundingClientRect().height)<200)throw new Error('Carte trop petite '+width);
    layouts.push({width,height,no_overflow:true,read_only:true});
    if(width===390)await page.screenshot({path:'/artifacts/setupsurvie-routes-mobile.png',fullPage:true});
  }
  if(calls.some(p=>p.startsWith('/api/admin/')))throw new Error('Un lecteur a demandé une opération administrateur.');
  role='admin';await page.setViewportSize({width:390,height:844});await page.waitForLoadState('networkidle');await page.reload();await page.waitForFunction(()=>window.SurvieMap);
  if(await page.locator('#planning-panel').isVisible())throw new Error('Le téléphone doit privilégier la consultation, même administrateur.');
  if(await page.locator('#locate').count())throw new Error('Le parcours ne doit pas demander le GPS.');
  if(errors.length||external.length)throw new Error(JSON.stringify({errors,external}));
  return {passed:true,layouts,no_external_requests:true,routing_simulated:true,physical_phone:false};
}
