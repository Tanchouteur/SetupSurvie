// Playwright MCP recipe. All map/account/OSRM responses are tiny local fixtures.
async (page) => {
  const base='http://10.0.3.2:8766',errors=[],external=[],calls=[];
  let role=null,available=false,failSearch=false,searches=0,index=0;
  const book={lists:[],points:[],routes:[]},id=()=>String(++index).padStart(32,'0');
  await page.unroute('**/*');await page.unroute('**/api/**');
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',async route=>{
    const req=route.request(),url=new URL(req.url()),path=url.pathname;
    if(url.origin!==base){external.push(req.url());return route.abort();}
    if(!path.startsWith('/api/'))return route.continue();calls.push(path);
    let data={},status=200;
    if(path==='/api/auth/login'){role='admin';data={id:'test',name:'Administration',role};}
    else if(path==='/api/auth/me'){if(role)data={id:'test',name:'Administration',role};else{status=401;data={detail:'Connexion requise'};}}
    else if(path==='/api/maps')data={maps:[]};
    else if(!role){status=401;data={detail:'Connexion requise'};}
    else if(path==='/api/settings')data={home:null,departure:null};
    else if(path==='/api/map-notebook')data=book;
    else if(path==='/api/routing')data={prepared:false,note:'Réseau de routes non préparé.'};
    else if(path==='/api/geography/status')data={datasets:available?[{terrain:false}]:[]};
    else if(path==='/api/geography/elevation')data={elevation_m:null};
    else if(path==='/api/geography/nearby'){
      searches++;await new Promise(resolve=>setTimeout(resolve,350));
      if(failSearch){status=503;data={detail:'Le service local ne répond pas.'};}
      else data={results:[{id:'water1',label:'Source de démonstration',lat:43.1,lon:6.1,distance_m:120}],coverage:[{}],note:'Repère fictif, eau non vérifiée.'};
    }else if(path==='/api/admin/map-notebook/lists'){
      data={id:id(),title:req.postDataJSON().title};book.lists.push(data);
    }else if(path==='/api/admin/map-notebook/points'){
      data={id:id(),...req.postDataJSON()};book.points.push(data);
    }
    await route.fulfill({status,json:data});
  });
  await page.setViewportSize({width:1440,height:900});
  await page.goto(base+'/cartes.html');await page.waitForFunction(()=>window.SurvieMap);
  if(await page.locator('#map').evaluate(e=>e.clientHeight)<700)throw new Error('Les panneaux mangent la carte sur ordinateur.');
  await page.locator('#map-nearby button').click();await page.locator('#map-login-dialog').waitFor({state:'visible'});
  if(searches!==0)throw new Error('La recherche privée ne doit pas partir sans connexion.');
  if(calls.some(path=>path==='/api/geography/status'||path==='/api/settings'))throw new Error('Appels privés inutiles sans session.');
  await page.locator('#map-login-form [name=email]').fill('admin');await page.locator('#map-login-form [name=password]').fill('fixture-password');
  await page.locator('#map-login-form button[type=submit]').click();await page.waitForFunction(()=>window.SurvieMap&&document.body.dataset.mapRole==='admin');
  await page.locator('#map-nearby button').click();await page.waitForFunction(()=>document.querySelector('#search-help').hidden===false);
  if(searches!==0)throw new Error('Requête inutile alors que les lieux ne sont pas préparés.');
  if(!(await page.locator('#geo-tool-status').innerText()).includes('pas encore téléchargés'))throw new Error('Données absentes non expliquées.');
  await page.locator('[data-panel=map-layers]').click();await page.locator('#relief').click();
  if(await page.locator('#relief').isDisabled())throw new Error('Le relief manquant doit être explicable par une action.');
  if(!(await page.locator('#relief-help').innerText()).includes('Aucune altitude'))throw new Error('Relief absent non expliqué.');
  await page.locator('#begin-map-point').click();await page.keyboard.press('Escape');
  if(!(await page.locator('#map-notice').innerText()).includes('annulé'))throw new Error('Le choix du point ne peut pas être annulé.');
  await page.locator('#begin-map-point').click();const bounds=await page.locator('#map').boundingBox();await page.mouse.click(bounds.x+120,bounds.y+220);
  await page.locator('#map-point-dialog').waitFor({state:'visible'});
  if(await page.locator('#point-list').inputValue()!=='__new__')throw new Error('Le premier point doit permettre de créer sa liste.');
  await page.locator('#point-title').fill('Réserve familiale');await page.locator('#point-new-list-title').fill('Nos ressources');
  await page.locator('#map-point-form button[type=submit]').click();await page.waitForFunction(()=>document.querySelector('#notebook-points').textContent.includes('Réserve familiale'));
  if(book.lists.length!==1||book.points.length!==1||book.points[0].list_id!==book.lists[0].id)throw new Error('Création de liste/point incorrecte.');
  available=true;await page.waitForLoadState('networkidle');await page.reload();await page.waitForFunction(()=>window.SurvieMap);await page.locator('#map-nearby button').click();
  if(!(await page.locator('#map-nearby button').innerText()).includes('Recherche'))throw new Error('Pas d’état de chargement.');
  await page.getByRole('button',{name:'Source de démonstration',exact:true}).waitFor();
  await page.getByRole('button',{name:'Source de démonstration',exact:true}).click();
  if(!(await page.locator('#selected-point-title').innerText()).includes('Source'))throw new Error('Le résultat ne sélectionne pas le point.');
  failSearch=true;await page.locator('#map-nearby button').click();await page.waitForFunction(()=>document.querySelector('#geo-tool-status').textContent.includes('ne répond pas'));
  if(await page.locator('#map-results button').count())throw new Error('Résultats périmés après une erreur.');
  if(await page.locator('#map-nearby button').isDisabled())throw new Error('Le bouton reste bloqué après erreur.');
  await page.locator('[data-panel=map-notebook]').click();await page.screenshot({path:'/artifacts/map-redesign-admin-desktop.png',fullPage:true});
  const layouts=[];role='user';calls.length=0;
  for(const [width,height] of [[1440,900],[1024,768],[768,900],[390,844],[375,667],[320,568],[844,390]]){
    await page.setViewportSize({width,height});await page.waitForLoadState('networkidle');await page.reload();await page.waitForFunction(()=>window.SurvieMap&&document.body.dataset.mapRole==='user');
    if(width<=760)await page.locator('#open-map-panel').click();
    await page.locator('[data-panel=map-notebook]').click();
    await page.getByRole('button',{name:'Réserve familiale',exact:true}).click();
    if(width<=760)await page.locator('#close-map-panel').click();
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw new Error('Débordement '+width);
    const mapBox=await page.locator('#map').boundingBox();if(mapBox.height<height-115)throw new Error('Carte trop petite '+width);
    if(await page.locator('#planning-panel').isVisible())throw new Error('Édition chez lecteur.');
    layouts.push({width,height,mapHeight:mapBox.height});
    if(width===390)await page.screenshot({path:'/artifacts/map-redesign-reader-mobile.png',fullPage:true});
  }
  if(calls.some(p=>p.startsWith('/api/admin/')))throw new Error('Un lecteur a demandé une mutation.');
  role=null;await page.setViewportSize({width:390,height:844});await page.waitForLoadState('networkidle');await page.reload();await page.waitForFunction(()=>window.SurvieMap);await page.locator('#open-map-panel').click();
  await page.screenshot({path:'/artifacts/map-redesign-guest-mobile.png',fullPage:true});
  await page.locator('#map-nearby button').click();await page.locator('#map-login-dialog').waitFor({state:'visible'});
  if(errors.length||external.length)throw new Error(JSON.stringify({errors,external}));
  return {passed:true,layouts,first_point_creates_list:true,inline_login:true,empty_data_explained:true,search_loading_and_error:true,physical_phone:false};
}
