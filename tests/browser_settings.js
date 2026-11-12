// Run with the Playwright MCP's browser_run_code_unsafe after serving portal/.
// API jobs, positions and altitudes are simulated; no external requests are needed.
async (page) => {
  const base='http://10.0.3.2:8766',errors=[],external=[];
  const state={home:null,departure:null},job={phase:'idle',themes:[],available:true};
  page.on('pageerror',e=>errors.push(e.message));
  await page.unroute('**/*');await page.unroute('**/api/**');
  await page.route('**/*',async route=>{
    const req=route.request(),url=new URL(req.url()),path=url.pathname;
    if(url.origin!==base){external.push(req.url());await route.abort();return;}
    if(!path.startsWith('/api/')){await route.continue();return;}
    let data={};
    if(path==='/api/auth/me')data={id:'test',role:'admin',name:'Test',recovery_ready:true};
    else if(path==='/api/status')data={version:'0.1.10',modes:[],books:[],guides:0};
    else if(path==='/api/conversations')data={conversations:[]};
    else if(path==='/api/inference')data={online:false,control_available:true,message:'Moteur arrêté',models:[],gpus:[],memory:{},disk:{},jobs:{}};
    else if(path==='/api/settings')data=state;
    else if(path==='/api/admin/users')data={users:[]};
    else if(path==='/api/admin/feedback')data={feedback:[]};
    else if(path==='/api/assistant-context')data={system:'Contexte de test'};
    else if(path==='/api/geography/status')data={datasets:[{terrain:false,center:[6.1,43.1],radius_km:5,places:1,addresses:1,created:'fixture'}]};
    else if(path==='/api/map-notebook')data={lists:[],points:[],routes:[]};
    else if(path==='/api/routing')data={prepared:false,note:'Test'};
    else if(path==='/api/inventory')data={books:[],guides:[],models:[],note:'Test'};
    else if(path==='/api/admin/library')data=job;
    else if(path==='/api/geography/addresses')data={results:[{id:'a'.repeat(32),label:'12 Rue des Écoles, Test',lat:43.1,lon:6.1,source:'OpenStreetMap local'}],note:'Résultat local'};
    else if(path.startsWith('/api/admin/settings/')){
      const body=req.postDataJSON(),target=path.split('/').pop();state[target]=req.method()==='DELETE'?null:{label:body.candidate?'12 Rue des Écoles, Test':body.label,lat:body.lat||43.1,lon:body.lon||6.1};data=state[target]||{ok:true};
    }else if(path==='/api/admin/library/geography'){
      Object.assign(job,{phase:'downloading',options:req.postDataJSON(),message:'Préparation géographique…'});data={accepted:true};
    }else if(path==='/api/maps')data={maps:[]};
    else if(path==='/api/geography/elevation')data={elevation_m:123};
    else if(path==='/api/geography/nearby')data={results:[{label:'Source locale',lat:43.1001,lon:6.1001,distance_m:12}],note:'Repères datés'};
    await route.fulfill({json:data});
  });
  await page.goto(base+'/#settings');await page.reload();
  await page.locator('#location-query').fill('12 rue ecoles');
  await page.getByRole('button',{name:'Rechercher l’adresse',exact:true}).click();
  await page.getByRole('button',{name:'Confirmer ce lieu'}).click();
  await page.waitForFunction(()=>document.querySelector('#location-summary').textContent.includes('12 Rue'));
  await page.locator('#location-target').selectOption('departure');
  await page.locator('#location-coordinates').evaluate(e=>e.closest('details').open=true);
  await page.locator('#location-label').fill('Camp');await page.locator('#location-lat').fill('43.2');await page.locator('#location-lon').fill('6.2');
  await page.getByRole('button',{name:'Enregistrer ce point'}).click();
  await page.waitForFunction(()=>document.querySelector('#location-summary').textContent.includes('Camp'));
  if(!state.home.label.includes('Écoles')||state.departure.label!=='Camp')throw new Error('Le départ a écrasé le domicile.');
  const layouts=[];
  for(const width of [1366,768,390,320]){
    await page.setViewportSize({width,height:900});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw new Error('Débordement Paramètres '+width);
    layouts.push({view:'settings',width});
  }
  await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:'/artifacts/setupsurvie-settings-mobile.png',fullPage:true});
  await page.evaluate(()=>view('data'));await page.locator('#geo-use-location').click();
  await page.waitForFunction(()=>document.querySelector('#geo-lat').value==='43.2');
  await page.locator('#geo-download').click();await page.waitForFunction(()=>document.querySelector('#geo-message').textContent.includes('Préparation'));
  await page.goto(base+'/cartes.html?choose=1');await page.waitForFunction(()=>document.querySelector('#area').disabled===false);
  if(await page.locator('#open-map-panel').isVisible())await page.locator('#open-map-panel').click();
  await page.locator('#map-query').fill('Rue des Écoles');await page.locator('#map-search button').click();
  await page.getByRole('button',{name:'12 Rue des Écoles, Test',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#map-point').textContent.includes('123'));
  if(await page.locator('#open-map-panel').isVisible())await page.locator('#open-map-panel').click();
  await page.locator('#map-nearby button').click();await page.getByRole('button',{name:'Source locale',exact:true}).waitFor();
  for(const width of [1366,768,390,320]){
    await page.setViewportSize({width,height:850});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw new Error('Débordement Cartes '+width);
    layouts.push({view:'maps',width});
  }
  if(!(await page.locator('#save-point').getAttribute('href')).includes('target=departure'))throw new Error('Le point manuel doit proposer le départ.');
  await page.screenshot({path:'/artifacts/setupsurvie-maps-tools-mobile.png',fullPage:true});
  if(errors.length||external.length)throw new Error(JSON.stringify({errors,external}));
  return {passed:true,layouts,jobs_simulated:true,physical_iphone:false};
}
